import socket

from loguru import logger

from shared.config import ServerConfig
from shared.protocol import GuardResponse, Message, MessageAction, recv_message, serialize_message


class NetworkClient:
    def __init__(self, config: ServerConfig):
        self.hostname = socket.gethostname()
        self.port = config.port
        self.server_ip = config.ip
        self.socket = socket.socket()
        self.can_connected: bool | None = None
        self._connect()

    def _get_local_ip(self) -> str:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        logger.info("Определён локальный IP: {ip}", ip=ip)
        return ip

    def _connect(self) -> bool:
        if self.can_connected is not None:
            self.socket.close()
            self.socket = socket.socket()

        result = self.socket.connect_ex((self.server_ip, self.port))
        if result == 10061:
            logger.warning("Сервер недоступен")
            self.can_connected = None
            return False

        logger.info("Подключился к серверу")
        self.can_connected = True
        return True

    def ping_account(self, account_id: int, username: str, retry: bool = True) -> None:
        msg = Message(
            action=MessageAction.PING,
            account_id=account_id,
            username=username,
            hostname=self.hostname,
        )
        try:
            self.socket.sendall(serialize_message(msg))
            logger.info(f"Пинг: аккаунт {username}")
        except OSError:
            if retry:
                logger.warning("Не удалось отправить пинг, переподключение")
                self._connect()
                self.ping_account(account_id, username, retry=False)
            else:
                logger.warning("Переподключение не помогло")

    def get_guard(self, account_id: int, username: str) -> str:
        msg = Message(
            action=MessageAction.GUARD,
            account_id=account_id,
            username=username,
            hostname=self.hostname,
        )
        try:
            self.socket.sendall(serialize_message(msg))
            logger.info(f"Запрос guard для {username}")
        except OSError:
            logger.warning(f"Не удалось отправить запрос guard для {username}")
            return "ERROR"

        try:
            response = recv_message(self.socket)
            if response is None:
                logger.warning("Пустой ответ guard от сервера")
                return "ERROR"
            if isinstance(response, GuardResponse):
                logger.info(f"Получен guard для {username}")
                return response.guard_code
            logger.warning("Неожиданный тип ответа от сервера")
            return "ERROR"
        except Exception:
            logger.warning("Не удалось получить guard от сервера")
            return "ERROR"

    def close(self):
        self.socket.close()
