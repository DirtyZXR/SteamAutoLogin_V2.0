import json
import struct
from dataclasses import dataclass
from enum import Enum
from typing import Any


class MessageAction(Enum):
    GUARD = "guard"
    PING = "ping"
    GUARD_RESPONSE = "guard_response"


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


@dataclass
class GuardResponse:
    guard_code: str

    def to_dict(self) -> dict[str, Any]:
        return {"action": MessageAction.GUARD_RESPONSE.value, "guard_code": self.guard_code}

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "GuardResponse":
        return cls(guard_code=str(data["guard_code"]))


AnyMessage = Message | GuardResponse


def _parse_dict(data: dict[str, Any]) -> AnyMessage:
    action = data.get("action", "")
    if action == MessageAction.GUARD_RESPONSE.value:
        return GuardResponse.from_dict(data)
    return Message.from_dict(data)


def serialize_message(msg: AnyMessage) -> bytes:
    payload = json.dumps(msg.to_dict(), ensure_ascii=False).encode("utf-8")
    length = struct.pack("!I", len(payload))
    return length + payload


def deserialize_message(data: bytes) -> AnyMessage:
    parsed = json.loads(data.decode("utf-8"))
    return _parse_dict(parsed)


def recv_message(sock) -> AnyMessage | None:
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
