import json
import socket
import struct
import threading
from time import sleep

from shared.protocol import (
    GuardResponse,
    Message,
    MessageAction,
    deserialize_message,
    recv_message,
    serialize_message,
)


class TestMessage:
    def test_to_dict(self):
        msg = Message(
            action=MessageAction.GUARD,
            account_id=42,
            username="testuser",
            hostname="PC-01",
        )
        d = msg.to_dict()
        assert d == {
            "action": "guard",
            "account_id": 42,
            "username": "testuser",
            "hostname": "PC-01",
            "token": "",
        }

    def test_token_roundtrip(self):
        msg = Message(
            action=MessageAction.GUARD,
            account_id=1,
            username="u",
            hostname="h",
            token="secret-123",
        )
        restored = Message.from_dict(msg.to_dict())
        assert restored.token == "secret-123"

    def test_from_dict_without_token_defaults_empty(self):
        msg = Message.from_dict(
            {"action": "ping", "account_id": 1, "username": "u", "hostname": "h"}
        )
        assert msg.token == ""

    def test_from_dict(self):
        data = {
            "action": "ping",
            "account_id": 7,
            "username": "player",
            "hostname": "PC-02",
        }
        msg = Message.from_dict(data)
        assert msg.action == MessageAction.PING
        assert msg.account_id == 7
        assert msg.username == "player"
        assert msg.hostname == "PC-02"

    def test_roundtrip(self):
        original = Message(
            action=MessageAction.GUARD,
            account_id=99,
            username="аккаунт_тест",
            hostname="мой-пк",
        )
        restored = Message.from_dict(original.to_dict())
        assert restored.action == original.action
        assert restored.account_id == original.account_id
        assert restored.username == original.username
        assert restored.hostname == original.hostname


class TestGuardResponse:
    def test_to_dict(self):
        resp = GuardResponse(guard_code="ABC12")
        assert resp.to_dict() == {"action": "guard_response", "guard_code": "ABC12"}

    def test_from_dict(self):
        resp = GuardResponse.from_dict({"action": "guard_response", "guard_code": "XYZ99"})
        assert resp.guard_code == "XYZ99"

    def test_roundtrip(self):
        original = GuardResponse(guard_code="Р43Х5")
        restored = GuardResponse.from_dict(original.to_dict())
        assert restored.guard_code == original.guard_code


class TestSerialization:
    def test_serialize_deserialize_message(self):
        msg = Message(
            action=MessageAction.PING,
            account_id=1,
            username="user",
            hostname="host",
        )
        raw = serialize_message(msg)
        assert isinstance(raw, bytes)

        length = struct.unpack("!I", raw[:4])[0]
        payload = raw[4:]
        assert len(payload) == length

        restored = deserialize_message(payload)
        assert isinstance(restored, Message)
        assert restored.action == msg.action
        assert restored.account_id == msg.account_id

    def test_serialize_deserialize_guard_response(self):
        resp = GuardResponse(guard_code="12345")
        raw = serialize_message(resp)
        payload = raw[4:]
        data = json.loads(payload)
        assert data["action"] == "guard_response"
        assert data["guard_code"] == "12345"

    def test_unicode_roundtrip(self):
        msg = Message(
            action=MessageAction.GUARD,
            account_id=5,
            username="пользователь",
            hostname="компьютер",
        )
        raw = serialize_message(msg)
        payload = raw[4:]
        restored = deserialize_message(payload)
        assert restored.username == "пользователь"
        assert restored.hostname == "компьютер"


class TestRecvMessage:
    def test_recv_message_over_socket(self):
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.bind(("127.0.0.1", 0))
        server.listen(1)
        port = server.getsockname()[1]

        msg = Message(
            action=MessageAction.GUARD,
            account_id=10,
            username="test",
            hostname="host",
        )

        def client_thread():
            c = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            c.connect(("127.0.0.1", port))
            c.sendall(serialize_message(msg))
            c.close()

        t = threading.Thread(target=client_thread)
        t.start()
        conn, _ = server.accept()
        result = recv_message(conn)
        conn.close()
        server.close()
        t.join()

        assert result is not None
        assert result.action == MessageAction.GUARD
        assert result.account_id == 10
        assert result.username == "test"

    def test_recv_message_returns_none_on_empty(self):
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.bind(("127.0.0.1", 0))
        server.listen(1)
        port = server.getsockname()[1]

        def client_close():
            c = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            c.connect(("127.0.0.1", port))
            c.close()

        t = threading.Thread(target=client_close)
        t.start()
        conn, _ = server.accept()
        sleep(0.1)
        result = recv_message(conn)
        conn.close()
        server.close()
        t.join()

        assert result is None

    def test_recv_guard_response(self):
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.bind(("127.0.0.1", 0))
        server.listen(1)
        port = server.getsockname()[1]

        resp = GuardResponse(guard_code="G42X9")

        def client_thread():
            c = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            c.connect(("127.0.0.1", port))
            c.sendall(serialize_message(resp))
            c.close()

        t = threading.Thread(target=client_thread)
        t.start()
        conn, _ = server.accept()
        result = recv_message(conn)
        conn.close()
        server.close()
        t.join()

        assert isinstance(result, GuardResponse)
        assert result.guard_code == "G42X9"
