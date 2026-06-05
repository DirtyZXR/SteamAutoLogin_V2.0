import ctypes
import socket
import threading
from time import sleep

from loguru import logger

from server.account_manager import PING_TIMEOUT, AccountManager
from server.handlers import MessageHandler
from server.network import TCPServer
from server.sda_automation import SDAAutomation
from shared.config import Settings
from shared.logger import setup_logger


def main():
    config = Settings.load_server_config()
    setup_logger("file_server.log", config.telegram.params)

    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(("8.8.8.8", 80))
    host_ip = s.getsockname()[0]
    s.close()

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
    handler = MessageHandler(tcp_server, account_manager, sda)

    tcp_server.set_handler(handler.handle)

    threading.Thread(target=account_manager._load_backup, daemon=False).start()
    threading.Thread(target=_offline_check_loop, args=[account_manager], daemon=False).start()

    tcp_server.start()


def _offline_check_loop(account_manager: AccountManager):
    while True:
        sleep(PING_TIMEOUT)
        account_manager.check_offline_cycle()


if __name__ == "__main__":
    main()
