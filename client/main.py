import argparse
import ctypes
import sys
import threading
from time import sleep
from pathlib import Path

import psutil
import winreg
from loguru import logger

from shared.config import Settings
from shared.db import get_free_accounts
from shared.exceptions import ConnectedError
from shared.logger import setup_logger
from client.gui import select_account
from client.input_guard import InputGuard
from client.network import NetworkClient
from client.steam_automation import SteamAutomation


def wait_for_steam_close(account_id: int, username: str, client: NetworkClient):
    key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Valve\Steam\ActiveProcess")
    pid_old, _ = winreg.QueryValueEx(key, "pid")
    logger.info(f"Начинаю пинговать аккаунт {username}")
    while True:
        sleep(10)
        client.ping_account(account_id, username)
        pid, _ = winreg.QueryValueEx(key, "pid")
        if pid != pid_old:
            break
    logger.info(f"Закончил пинговать аккаунт {username}")


def pick_account(accounts: list[tuple]) -> tuple:
    if len(accounts) == 1:
        return accounts[0]
    idx = select_account(accounts)
    if idx == -1:
        return (0, 0, 0, 0, -1)
    return accounts[idx]


def main():
    config = Settings.load_client_config()
    setup_logger("file_client.log", config.telegram.params)

    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Valve\Steam\ActiveProcess")
        pid, _ = winreg.QueryValueEx(key, "pid")
        if pid != 0 and psutil.pid_exists(pid):
            ctypes.windll.user32.MessageBoxW(
                0, "Steam запущен. Сначала закройте Steam.", "Ошибка", 1
            )
            return
    except OSError:
        pass

    parser = argparse.ArgumentParser(description="SteamAutoLogin Client")
    parser.add_argument("appid", type=str, help="ID игры в Steam")
    args = parser.parse_args()
    appid = args.appid

    client = NetworkClient(config.server)

    try:
        accounts = get_free_accounts(config.db, appid)
    except Exception as e:
        logger.error(f"Ошибка получения аккаунтов: {e}")
        raise ConnectedError(e)

    if not accounts:
        ctypes.windll.user32.MessageBoxW(
            0, "Нет доступных аккаунтов для этой игры. Попробуйте позже.",
            "Нет доступных аккаунтов", 1,
        )
        return

    account = pick_account(accounts)
    account_id, login_steam, pass_steam, auth_mail, ap = account

    if ap == -1:
        return
    if ap == 0:
        ctypes.windll.user32.MessageBoxW(
            0, "Нет доступных аккаунтов для этой игры. Попробуйте позже.",
            "Нет доступных аккаунтов", 1,
        )
        return

    input_guard = InputGuard()
    input_guard.block()
    threading.Thread(target=input_guard.auto_unblock, daemon=True).start()

    try:
        steam = SteamAutomation(login_steam, pass_steam, appid)
        threading.Thread(
            target=wait_for_steam_close, args=[account_id, login_steam, client], daemon=False
        ).start()

        if steam.login():
            guard = client.get_guard(account_id, login_steam)
            if guard == "ERROR":
                raise RuntimeError("Не удалось получить guard")
            success = steam.input_guard_code(input_guard.keyboard_listener, guard)
            if not success:
                logger.warning("Не удалось ввести guard")
        else:
            logger.info("Вход выполнен без guard")
    except Exception as e:
        logger.error(f"Ошибка при входе: {e}")
    finally:
        input_guard.unblock()


if __name__ == "__main__":
    main()
