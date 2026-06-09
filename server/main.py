import ctypes
import threading
from time import sleep

from loguru import logger

from server.account_manager import PING_TIMEOUT, AccountManager
from server.handlers import MessageHandler
from server.network import TCPServer
from server.sda_automation import SDAAutomation
from shared.config import Settings
from shared.logger import setup_logger
from shared.netutil import get_local_ip


def main():
    config = Settings.load_server_config()
    setup_logger("file_server.log", config.telegram.params)

    if not config.auth_token:
        logger.warning(
            "AUTH_TOKEN не задан — сервер принимает guard-запросы без аутентификации. "
            "Задайте AUTH_TOKEN в .env на сервере и клиентах."
        )

    host_ip = get_local_ip()

    try:
        sda = SDAAutomation(config.sda.path)
        logger.info("SDA запущен")
    except Exception:
        ctypes.windll.user32.MessageBoxW(
            0,
            "Проблема при открытии SDA. Проверьте путь до SDA в конфиг-файле",
            "SDA",
            1,
        )
        return

    account_manager = AccountManager(config.db)
    tcp_server = TCPServer(host_ip, config.server.port)
    handler = MessageHandler(tcp_server, account_manager, sda, auth_token=config.auth_token)

    tcp_server.set_handler(handler.handle)

    threading.Thread(target=_offline_check_loop, args=[account_manager], daemon=True).start()

    tcp_server.start()


def _offline_check_loop(account_manager: AccountManager):
    while True:
        sleep(PING_TIMEOUT)
        account_manager.check_offline_cycle()


if __name__ == "__main__":
    main()
