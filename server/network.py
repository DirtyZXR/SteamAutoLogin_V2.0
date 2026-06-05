import socket
import threading
from loguru import logger

from shared.protocol import recv_message, serialize_message, Message


class TCPServer:
    def __init__(self, host: str, port: int):
        self.host = host
        self.port = port
        self.socket = socket.socket()
        self.socket.bind((host, port))
        self.socket.listen(25)
        self.on_message = None

    def set_handler(self, handler):
        self.on_message = handler

    def start(self):
        logger.info(f"Сервер слушает {self.host}:{self.port}")
        while True:
            conn, address = self.socket.accept()
            logger.info(f"Подключение от {address[0]}")
            threading.Thread(
                target=self._handle_connection, args=[conn, address], daemon=False
            ).start()

    def _handle_connection(self, conn: socket.socket, address):
        while True:
            try:
                msg = recv_message(conn)
                if msg is None:
                    break
                if self.on_message:
                    self.on_message(msg, conn)
            except Exception:
                break

    @staticmethod
    def send_response(conn: socket.socket, data: str):
        response = Message(
            action=Message.PING,
            account_id=0,
            username=data,
            hostname="server",
        )
        conn.sendall(serialize_message(response))
