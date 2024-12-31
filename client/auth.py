from time import sleep
import win32gui, win32process
from snoop import snoop

from loger_data import params
from  interface_for_var_acc import get_num_acc
import queue
import mysql.connector
from pywinauto import Application
from threading import Thread, Event
from psutil import pid_exists
from data_all import host_ip, login_db, pass_db, name_db
import webbrowser
import argparse
import ctypes
import pynput
import winreg
import psutil
from client import ClientSocket
from loguru import logger
from notifiers.logging import NotificationHandler
from My_Exeptions import *



def get_window_pid():
    key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\Valve\Steam")
    pid, regtype = winreg.QueryValueEx(key, "SteamPID")
    while pid == 0:
        pid, regtype = winreg.QueryValueEx(key, "SteamPID")

    sleep(2)
    parent = psutil.Process(pid)
    children = parent.children()
    while len(children) == 0:
        children = parent.children()
    # all child pids can be accessed using the pid attribute
    child_pids = [p.pid for p in children]
    pid = child_pids[0]

    # print(pid)
    return pid


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
                    query = f"UPDATE users SET online = 1 WHERE id = {account[0]}"
                    cursor.execute(query)
                    connection.commit()
            else:
                account = (0, 0, 0, 0, 0)

            cursor.close()

        connection.close()
        logger.info(f"Получил данные аккаунта. {account[1]}")
    except Exception as e:
        cursor.close()
        connection.close()
        logger.error("Ошибка подключения к БД | {host}", host=socket_code.hostname)
        raise ConnectedError('Ошибка подключения к БД')
    return account


@snoop
def check_add_account(window, pid, q):
    f = pid_exists(pid)
    while f and not event_succes.is_set():
        try:
            window.child_window(title='Добавить аккаунт', control_type='Group').wait(wait_for="active", timeout=5)
            event_succes.set()
        except:
            f = pid_exists(pid)
        else:
            q.put_nowait('yes add')


@snoop
def check_login(window, pid, q):
    f = pid_exists(pid)
    while f and not event_succes.is_set():
        try:
            window.child_window(control_type="Edit", found_index=0).wait(wait_for="active", timeout=5)
            event_succes.set()
        except:
            f = pid_exists(pid)
        else:
            q.put_nowait('yes login')
    if not f:
        q.put_nowait('close steam')


@snoop
def login(window, username, password):
    username_pane = window.child_window(control_type="Edit", found_index=0)
    password_pane = window.child_window(control_type="Edit", found_index=1)

    username_pane.set_text(username)
    password_pane.set_text(password)

    signin_button = window.child_window(title="Войти")
    signin_button.click()


def wait_close_steam(username):
    while True:
        sleep(10)
        socket_code.ping_acc(username)

@snoop
def add_acc_login(window, username, password):
    add_account = window.child_window(title='Добавить аккаунт', control_type='Group')
    im = add_account.child_window(control_type='Image')
    im.invoke()

    window.child_window(control_type="Edit", found_index=0).wait(wait_for="active", timeout=10)

    login(window, username, password)


@snoop
def auth_steam(id_, login_steam, password_steam, auth_mail, appid, need_wait):
    # Запуск Steam

    webbrowser.open(f'steam://rungameid/{appid}')
    if need_wait:
        sleep(1.5)
    pid = get_window_pid()

    if pid != 'close':
        Thread(target=wait_close_steam, args=[login_steam], daemon=True).start()
        flag = False
        while not flag:
            try:
                app = Application(backend="uia").connect(process=pid)
                try:
                    window = app.window(title="Войти в Steam")
                    flag = True
                except:
                    try:
                        window = app.window(title="Вход в Steam")
                        flag = True
                    except:
                        pass
            except:
                pass

        q = queue.Queue()
        Thread(target=check_add_account, args=[window, pid, q]).start()
        Thread(target=check_login, args=[window, pid, q]).start()
        f = True
        s = q.get()

        if s == 'yes login':
            try:
                login(window, login_steam, password_steam)
            except:
                f = False
        elif s == 'yes add':
            try:
                add_acc_login(window, login_steam, password_steam)
            except:
                f = False
        else:
            f = False

        if f:
            mouse_listener.start()
            keyboard_listener.start()
            sleep(1.5)
            text_wait = 'Создайте бесплатный аккаунт'
            try:
                while 'Создайте бесплатный аккаунт' in text_wait or len(text_wait) == 13:
                    text_wait = window.child_window(control_type="Document", found_index=0).wait(wait_for='active', timeout=10)
                    text_wait = text_wait.window_text()


                if 'Введите код' in text_wait:
                    need_guard = True
                else:
                    need_guard = False
                    mouse_listener.stop()
                    keyboard_listener.stop()

            except Exception as e:
                need_guard = False
                mouse_listener.stop()
                keyboard_listener.stop()
                logger.warning('Exception - {e}', e=e)



            if need_guard:
                try:
                    place_for_symbol = [0, 0, 0, 0, 0]
                    try:
                        for i in range(5):
                            place_for_symbol[i] = window.child_window(control_type="Edit", found_index=i)
                        if auth_mail:
                            logger.info('Потребовался Гвард на аккаунт - {login_steam}', login_steam=login_steam)
                            steam_code = socket_code.get_guard(login_steam)
                            if steam_code == 'ERROR':
                                auth_mail = False
                                logger.error('Не смог получить гвард от аккаунта - {login_steam} | {host}', login_steam=login_steam, host=socket_code.hostname)

                    except Exception as e:
                        mouse_listener.stop()
                        keyboard_listener.stop()
                        ctypes.windll.user32.MessageBoxW(0, "Автоматически ввести Steam Guard не удалось. Попросите администратора",
                                                         "Steam Guard",1)
                        ctypes.windll.user32.MessageBoxW(0, f"Автоматически ввести Steam Guard не удалось. Попросите администратора",
                                                         "Steam Guard",1)
                        logger.error("Не смог получить гвард. Ошибка - {e} | {host}", e=e, host=socket_code.hostname)
                        # raise SteamError('Не смог получить или ввести гвард')

                    try:
                        if auth_mail:
                            for i in range(5):
                                place_for_symbol[i].set_text(steam_code[i])

                    except Exception as e:
                        logger.error("Не смог ввести гвард. Ошибка - {e} | {host}", e=e, host=socket_code.hostname)
                        mouse_listener.stop()
                        keyboard_listener.stop()

                except Exception as e:
                    logger.error("Необработанная ошибка. Ошибка - {e} | {host}", e=e, host=socket_code.hostname)
                    event.set()

                finally:
                    mouse_listener.stop()
                    keyboard_listener.stop()

                    if not auth_mail:
                        ctypes.windll.user32.MessageBoxW(0, "Автоматически ввести Steam Guard не удалось. Попросите администратора",
                                                         "Steam Guard", 1)

    else:
        event.set()


logger.add("./file_client.log", format="{time:DD.MM.YYYY at HH:mm:ss} | {name}:{function}:{line} | {level} | {message}", level="INFO", rotation="100MB")
handler = NotificationHandler("telegram", defaults=params)
logger.add(handler, level="ERROR")

try:
    key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\Valve\Steam")
    pid, regtype = winreg.QueryValueEx(key, "SteamPID")
    need_wait = False
    mouse_listener = pynput.mouse.Listener(suppress=True)
    keyboard_listener = pynput.keyboard.Listener(suppress=True)


    if not psutil.pid_exists(pid):
        pid = 0
        need_wait = True

    if pid == 0:
        event = Event()
        event_succes = Event()
        try:
            parser = argparse.ArgumentParser(description='Run Steam')
            parser.add_argument('appid', type=str, help='Id game in steam')
            args = parser.parse_args()
            appid = args.appid
        except:
            logger.warning('Не удалось получить аргументы')
            raise Exception('Не удалось получить аргументы')

        try:

            acc = get_acc(appid)
            id_, login_steam, pass_steam, auth_mail, ap = acc
            # id_, login_steam, pass_steam, auth_mail, ap = (0, "fabiooo12345", "qsxcgyujm1590.", 1, 730)
            suc = True

        except Exception as e:
            logger.warning(e)
            ap = 0
            suc = False

        if ap != -1:
            if ap == 0 and suc:
                if suc:
                    ctypes.windll.user32.MessageBoxW(0, "Сейчас нет доступных аккаутов для это игры. Попробуйте позже.",
                                                     "Нет доступных аккаунтов", 1)
                else:
                    ctypes.windll.user32.MessageBoxW(0, "Возникла неизвестная ошибка. Обратитесь к администратору.", "Ошибка",
                                                     1)
            else:
                socket_code = ClientSocket()
                auth_steam(id_, login_steam, pass_steam, auth_mail, ap, need_wait)

    else:
        ctypes.windll.user32.MessageBoxW(0, "Стим запущен. Сначала закройте стим.", "Ошибка", 1)
except Exception as e:
    logger.warning(e)
    ctypes.windll.user32.MessageBoxW(0, "Возникла неизвестная ошибка. Обратитесь к администратору",
                                     "Ошибка", 1)
