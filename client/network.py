import socket

from loguru import logger

from shared.config import ServerConfig
from shared.protocol import GuardResponse, Message, MessageAction, recv_message, serialize_message


class NetworkClient:
    def __init__(self, config: ServerConfig, token: str = ""):
        self.hostname = socket.gethostname()
        self.port = config.port
        self.server_ip = config.ip
        self.token = token
        self.socket = socket.socket()
        self.can_connected: bool | None = None
        self._connect()

    def _connect(self) -> bool:
        if self.can_connected is not None:
            self.socket.close()
            self.socket = socket.socket()

        try:
            result = self.socket.connect_ex((self.server_ip, self.port))
        except OSError as e:
            logger.warning(f"Ошибка подключения к серверу: {e}")
            self.can_connected = None
            return False

        if result != 0:
            logger.warning(f"Сервер недоступен (код {result})")
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
            token=self.token,
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
            token=self.token,
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
