from time import sleep
import win32gui, win32process
from snoop import snoop

from loger_data import params
from  interface_for_var_acc import get_num_acc
import mysql.connector
from threading import Thread
from data_all import host_ip, login_db, pass_db, name_db
import argparse
import ctypes
import pynput
import winreg
import psutil
from client import ClientSocket
from loguru import logger
# from notifiers.logging import NotificationHandler
from My_Exeptions import *
from into_steam import Steam


def create_connection(host_name, user_name, user_password, db_name):
    try:

        connection = mysql.connector.connect(
            host=host_name,
            user=user_name,
            passwd=user_password,
            database=db_name
        )
    except Exception as e:
        logger.error("Не смог инициадизировать подключение к БД | {host}", host=socket_code.hostname)
        raise ConnectedError('Не смог инициализировать подключение к БД')

    return connection

# @snoop
def get_acc(appid):
    connection = create_connection(host_ip, login_db, pass_db, name_db)
    acc = """
    SELECT id, login_steam, pass_steam, auth_mail, game
    FROM users
    WHERE online = FALSE and active = TRUE
    """
    try:
        with connection.cursor() as cursor:
            cursor.execute(acc)
            accounts = cursor.fetchall()
            accounts_appid = []
            for account in accounts:
                appid_all = account[-1].split('-')
                if appid in appid_all:
                    accounts_appid.append(account)
            if len(accounts_appid) != 0:
                num = get_num_acc(accounts_appid)
                if num == -1:
                    account = (0, 0, 0, 0, -1)
                else:
                    account = accounts_appid[num]
                    # query = f"UPDATE users SET online = 1 WHERE id = {account[0]}"#todo это сделать на сервере
                    # cursor.execute(query)
                    # connection.commit()
                    pass
            else:
                account = (0, 0, 0, 0, 0)

            cursor.close()

        connection.close()
        logger.info(f"Получил данные аккаунта. {account[1]}")
    except Exception as e:
        cursor.close()
        connection.close()
        logger.error("Ошибка подключения к БД| {e} | {host}", host=socket_code.hostname, e=e)
        raise ConnectedError('Ошибка подключения к БД')
    return account

# @snoop
def wait_close_steam(id_, username):
    key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Valve\Steam\ActiveProcess")
    pid, regtype = winreg.QueryValueEx(key, "pid")
    pid_old = pid
    logger.info(f'Начал пинговать аккаунт {username}')
    while True:
        sleep(10)
        socket_code.ping_acc(id_, username)
        pid, regtype = winreg.QueryValueEx(key, "pid")
        if pid != pid_old:
            break
    logger.info(f'Закончил пинговать аккаунт {username}')

def stop_timer(mouse: pynput.mouse.Listener, key: pynput.mouse.Listener):
    logger.info("Start timers")
    sleep(30)
    mouse.stop()
    key.stop()
    logger.info("Stop timers")

# @snoop
def main():
    global socket_code
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Valve\Steam\ActiveProcess")
        pid, regtype = winreg.QueryValueEx(key, "pid")

        if pid == 0 or not psutil.pid_exists(pid):

            try:
                parser = argparse.ArgumentParser(description='Run Steam')
                parser.add_argument('appid', type=str, help='Id game in steam')
                args = parser.parse_args()
                appid = args.appid
            except:
                logger.warning('Не удалось получить аргументы')
                raise Exception('Не удалось получить аргументы')

            try:
                socket_code = ClientSocket()
                suc = socket_code.host_ping()
            except Exception as e:
                logger.error(e)
                logger.error("Не смог подключиться к хосту")
                suc = False

            if suc:
                try:
                    acc = get_acc(appid)
                    id_, login_steam, pass_steam, auth_mail, ap = acc
                    # id_, login_steam, pass_steam, auth_mail, ap = (0, "fabiooo12345", "qsxcgyujm1590.", 1, 730)
                    logger.info(f"Получил аккаунт {login_steam}")

                except Exception as e:
                    logger.error(e)
                    raise ConnectedError(e)

                if ap != -1:
                    if ap == 0:
                        ctypes.windll.user32.MessageBoxW(0, "Сейчас нет доступных аккаутов для это игры. Попробуйте позже.",
                                                         "Нет доступных аккаунтов", 1)
                    else:

                        keyboard_listener = pynput.keyboard.Listener(suppress=True)
                        mouse_listener = pynput.mouse.Listener(suppress=True)
                        keyboard_listener.start()
                        mouse_listener.start()
                        logger.info("Запустил слушатели клавиатуры и мыши")
                        Thread(target=stop_timer, args=(mouse_listener, keyboard_listener)).start()
                        try:
                            logger.info("Запускаю стим")
                            steam = Steam(login_steam,pass_steam, appid)
                            Thread(target=wait_close_steam, args=[id_, login_steam], daemon=False).start()
                            if steam.guard:
                                try:
                                    guard = socket_code.get_guard(id_, login_steam)
                                    logger.info('Получил гвард')
                                except Exception as e:
                                    logger.error(e)
                                    print(e)
                                    raise Exception('Не смог получить гвард от аккаунта')
                                try:
                                    suc = steam.guard_input(keyboard_listener, guard)
                                    if suc:
                                        logger.info('Ввел гвард')
                                    else:
                                        logger.warning("Не удалось ввести гвард")
                                except Exception as e:
                                    logger.error(e)
                                    print(e)
                                    raise Exception('Не смог ввести от аккаунта')

                            else:
                                logger.info('Вход произведен')
                        except:
                            pass
                        finally:
                            keyboard_listener.stop()
                            mouse_listener.stop()
                            logger.info("Остановил слушатели клавиатуры и мыши")
            else:
                ctypes.windll.user32.MessageBoxW(0, "Не удалось подключиться к серверу. Обратитесь к администратору", "Ошибка", 1)

        else:
            ctypes.windll.user32.MessageBoxW(0, "Стим запущен. Сначала закройте стим.", "Ошибка", 1)

    except ConnectedError as e:
        logger.warning(e)

    except Exception as e:
        logger.error(e)


logger.add("./file_client.log", format="{time:DD.MM.YYYY at HH:mm:ss} | {name}:{function}:{line} | {level} | {message}", level="INFO", rotation="100MB")
# handler = NotificationHandler("telegram", defaults=params)
# logger.add(handler, level="ERROR")

main()