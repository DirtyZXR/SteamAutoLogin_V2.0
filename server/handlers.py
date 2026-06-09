import threading

from loguru import logger

from server.account_manager import AccountManager
from server.network import TCPServer
from server.sda_automation import SDAAutomation
from shared.auth import is_authorized
from shared.protocol import MessageAction


class MessageHandler:
    def __init__(
        self,
        tcp_server: TCPServer,
        account_manager: AccountManager,
        sda: SDAAutomation,
        auth_token: str = "",
    ):
        self.tcp_server = tcp_server
        self.account_manager = account_manager
        self.sda = sda
        self.auth_token = auth_token

        self._guard_queue = []
        self._guard_event = threading.Event()
        threading.Thread(target=self._process_guard_queue, daemon=False).start()

    def handle(self, msg, conn):
        if not is_authorized(msg.token, self.auth_token):
            logger.warning(
                f"Отклонён неавторизованный запрос от {msg.hostname}, аккаунт {msg.username}"
            )
            return

        logger.info(
            f"Сообщение от {msg.hostname}, аккаунт {msg.username}, "
            f"действие {msg.action.value}"
        )
        if msg.action == MessageAction.GUARD:
            self._guard_queue.append((msg, conn))
            self._guard_event.set()
        elif msg.action == MessageAction.PING:
            self.account_manager.mark_online(msg.account_id)

    def _process_guard_queue(self):
        while True:
            self._guard_event.wait()
            self._guard_event.clear()

            while self._guard_queue:
                msg, conn = self._guard_queue.pop(0)
                logger.info(
                    f"Обработка guard: {msg.hostname}, аккаунт {msg.username}"
                )
                try:
                    guard = self.sda.get_guard(msg.username)
                    logger.info(f"Guard для {msg.username}: {guard}")
                    self.account_manager.mark_online(msg.account_id)
                    self.tcp_server.send_guard_response(conn, guard)
                    logger.info(f"Guard отправлен на {msg.hostname}")
                except Exception as e:
                    logger.error(f"Ошибка при получении guard: {e}")
