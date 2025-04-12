import time
from time import sleep
from loguru import logger

import pyperclip
from pywinauto import Application
from pywinauto import keyboard
from pywinauto import clipboard
import pynput
import winreg

from snoop import snoop


class Steam:
    def __init__(self, login:str, password:str, id_game:int):
        self.app = self.run_steam(login, password, id_game)
        self.guard = self.login(login, password)



    def run_steam(self, login:str, password:str, id_game:int):
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Valve\Steam")
        path_steam, regtype = winreg.QueryValueEx(key, "SteamExe")
        path_steam += f' -language "russian" -login {login} -password {password} -applaunch {id_game}'
        logger.info('Запустил стим')
        app = Application(backend="uia").start(path_steam)

        while True and app.is_process_running():
            try:
                app = Application(backend="uia").connect(title="Войти в Steam")
                logger.info('Подключился к окну входа в стим')
                break
            except:
                pass

        return app

    # @snoop
    def login(self, login, password, try_number = 0) -> bool:
        window = self.app.top_window()
        f = 0
        while True:
            try:
                window.child_window(control_type="Edit", found_index=0).wait(wait_for="active", timeout=5)
                logger.info("Нашел окно логина в стим")
                break
            except:
                f += 1
                try:
                    enter = window.child_window(title="Вход...").window_text()
                    if enter != "Вход...":
                        if f > 5:
                            logger.warning("Не удалось найти поле ввода логина")
                            raise Exception("Не удалось найти поле ввода логина")
                        else:
                            f = True
                except:
                    pass

        try:

            window.child_window(control_type="Edit", found_index=0).set_text(login)
            window.child_window(control_type="Edit", found_index=1).set_text(password)
            window.child_window(title="Войти").click()
            logger.info(f"Нажал кнопку входа в стим в {login}")

            text_wait = 'Создайте бесплатный аккаунт'
            try:
                while 'Создайте бесплатный аккаунт' in text_wait or len(text_wait) == 13:
                    text_wait = window.child_window(control_type="Document", found_index=0).wait(wait_for='active', timeout=10)
                    text_wait = text_wait.window_text()
            except:
                pass


            if 'Введите код' in text_wait:
                logger.info(f"Аккаунт {login} требует ввода кода")
                return True
            elif 'Ошибка' in text_wait:
                window.child_window(title='Повторить').click()
                try_number += 1
                if try_number >= 3:
                    logger.info("Слишком много попыток входа в аккаунт")
                    raise Exception('У стима ошибка')#todo вывести на экран
                else:
                    return self.login(login, password, try_number)
            else:
                return False
        except Exception as e:
            raise Exception(f"Ошибка при входе в аккаунт - {e}")


    # @snoop
    def guard_input(self, key: pynput.keyboard.Listener, guard_code:str):
        logger.info("Вводим код гварда")
        window = self.app.top_window()
        logger.info("Установил окно стима")
        window.set_focus()
        logger.info("Установил фокус на окно ввода кода")
        window = window.child_window(control_type="Document")
        logger.info("Установил фокус на документ")
        s = window.window_text()
        logger.info(f'Получил текст окна - {s}')
        pyperclip.copy(guard_code)
        logger.info(f"Скопировал код {guard_code} в буфер обмена")
        key.stop()
        logger.info("Остановил слушатель клавиатуры")
        i = 0
        while 'Введите код из мобильного приложения Steam' in s and i < 5:
            sleep(1)
            keyboard.send_keys(guard_code, pause=0.1, turn_off_numlock=True)
            logger.info("Вписал код в окно")
            sleep(2)
            i += 1
            try:
                s = window.window_text()
                logger.info(f'Получил текст окна - {s}')
            except Exception as e:
                logger.warning(e)
                s = ''
                logger.info("Не смог получить текст окна")

            if s == 'Загрузка данных пользователя...' or 'Введите код из мобильного приложения Steam' not in s:
                logger.info("Вход удачен")
                return True

        keyboard.send_keys('^v')
        logger.info("Вставил код из буфера обмена")

        try:
            s = window.window_text()
            logger.info(f'Получил текст окна - {s}')
        except Exception as e:
            logger.warning(e)
            s = ''
            logger.info("Не смог получить текст окна")

        if s == 'Загрузка данных пользователя...' or 'Введите код из мобильного приложения Steam' not in s:
            logger.info("Вход удачен")
            return True

        logger.info("Не удалось ввести код")
        return False
