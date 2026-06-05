import json
import struct
from dataclasses import dataclass
from enum import Enum
from typing import Any


class MessageAction(Enum):
    GUARD = "guard"
    PING = "ping"


@dataclass
class Message:
    action: MessageAction
    account_id: int
    username: str
    hostname: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "action": self.action.value,
            "account_id": self.account_id,
            "username": self.username,
            "hostname": self.hostname,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Message":
        return cls(
            action=MessageAction(data["action"]),
            account_id=int(data["account_id"]),
            username=str(data["username"]),
            hostname=str(data["hostname"]),
        )


def serialize_message(msg: Message) -> bytes:
    payload = json.dumps(msg.to_dict(), ensure_ascii=False).encode("utf-8")
    length = struct.pack("!I", len(payload))
    return length + payload


def deserialize_message(data: bytes) -> Message:
    return Message.from_dict(json.loads(data.decode("utf-8")))


def recv_message(sock, bufsize: int = 4096) -> Message | None:
    raw_length = _recv_exact(sock, 4)
    if raw_length is None:
        return None
    length = struct.unpack("!I", raw_length)[0]
    raw_data = _recv_exact(sock, length)
    if raw_data is None:
        return None
    return deserialize_message(raw_data)


def _recv_exact(sock, n: int) -> bytes | None:
    buf = b""
    while len(buf) < n:
        chunk = sock.recv(n - len(buf))
        if not chunk:
            return None
        buf += chunk
    return buf
