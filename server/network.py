import socket
import threading

from loguru import logger

from shared.protocol import GuardResponse, Message, recv_message, serialize_message


class TCPServer:
    def __init__(self, host: str, port: int):
        self.host = host
        self.port = port
        self.socket = socket.socket()
        self.socket.bind((host, port))
        self.socket.listen(25)
        self._handler = None

    def set_handler(self, handler):
        self._handler = handler

    def start(self):
        logger.info(f"Сервер слушает {self.host}:{self.port}")
        while True:
            conn, address = self.socket.accept()
            logger.info(f"Подключение от {address[0]}")
            threading.Thread(
                target=self._handle_connection, args=[conn], daemon=False
            ).start()

    def _handle_connection(self, conn: socket.socket):
        while True:
            try:
                msg = recv_message(conn)
                if msg is None:
                    break
                if self._handler and isinstance(msg, Message):
                    self._handler(msg, conn)
            except Exception:
                break

    @staticmethod
    def send_guard_response(conn: socket.socket, guard_code: str):
        response = GuardResponse(guard_code=guard_code)
        conn.sendall(serialize_message(response))
