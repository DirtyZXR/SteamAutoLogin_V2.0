import time

import pyperclip
import pynput
from loguru import logger
from pywinauto import Application, keyboard
from pywinauto.clipboard import clipboard
import winreg


class SteamAutomation:
    def __init__(self, login: str, password: str, appid: int):
        self.login = login
        self.password = password
        self.appid = appid
        self.app: Application | None = None
        self._launch_and_connect()

    def _launch_and_connect(self):
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Valve\Steam")
        path_steam, _ = winreg.QueryValueEx(key, "SteamExe")
        cmd = f'{path_steam} -language "russian" -login {self.login} -password {self.password} -applaunch {self.appid}'
        logger.info("Запуск Steam")
        self.app = Application(backend="uia").start(cmd)

        while self.app.is_process_running():
            try:
                self.app = Application(backend="uia").connect(title="Войти в Steam")
                logger.info("Подключился к окну входа Steam")
                break
            except Exception:
                pass

    def login(self, attempt: int = 0) -> bool:
        window = self.app.top_window()
        retries = 0
        while True:
            try:
                window.child_window(control_type="Edit", found_index=0).wait(
                    wait_for="active", timeout=5
                )
                logger.info("Найдено окно логина Steam")
                break
            except Exception:
                retries += 1
                try:
                    enter_text = window.child_window(title="Вход...").window_text()
                    if enter_text != "Вход..." and retries > 5:
                        raise RuntimeError("Не удалось найти поле ввода логина")
                except Exception:
                    pass

        try:
            window.child_window(control_type="Edit", found_index=0).set_text(self.login)
            window.child_window(control_type="Edit", found_index=1).set_text(self.password)
            window.child_window(title="Войти").click()
            logger.info(f"Нажата кнопка входа для {self.login}")

            text_wait = "Создайте бесплатный аккаунт"
            try:
                while (
                    "Создайте бесплатный аккаунт" in text_wait
                    or len(text_wait) == 13
                ):
                    elem = window.child_window(
                        control_type="Document", found_index=0
                    ).wait(wait_for="active", timeout=10)
                    text_wait = elem.window_text()
            except Exception:
                pass

            if "Введите код" in text_wait:
                logger.info(f"Аккаунт {self.login} требует код guard")
                return True
            elif "Ошибка" in text_wait:
                window.child_window(title="Повторить").click()
                attempt += 1
                if attempt >= 3:
                    raise RuntimeError("Слишком много попыток входа")
                return self.login(attempt)
            else:
                return False
        except RuntimeError:
            raise
        except Exception as e:
            raise RuntimeError(f"Ошибка при входе в аккаунт: {e}") from e

    def input_guard_code(
        self, keyboard_listener: pynput.keyboard.Listener, guard_code: str
    ) -> bool:
        logger.info("Ввод кода guard")
        window = self.app.top_window()
        window.set_focus()
        doc = window.child_window(control_type="Document")
        text = doc.window_text()
        logger.info(f"Текст окна: {text}")

        pyperclip.copy(guard_code)
        logger.info(f"Скопирован код {guard_code} в буфер обмена")
        keyboard_listener.stop()
        logger.info("Остановлен слушатель клавиатуры")

        for _ in range(5):
            if self._try_send_code(doc, guard_code):
                return True
            time.sleep(1)
            try:
                text = doc.window_text()
            except Exception:
                text = ""
            if self._is_login_success(text):
                return True

        keyboard.send_keys("^v")
        logger.info("Вставлен код из буфера обмена")

        try:
            text = doc.window_text()
        except Exception:
            text = ""
        return self._is_login_success(text)

    def _try_send_code(self, doc, guard_code: str) -> bool:
        keyboard.send_keys(guard_code, pause=0.1, turn_off_numlock=True)
        logger.info("Введён код в окно")
        time.sleep(2)
        try:
            text = doc.window_text()
        except Exception:
            text = ""
        return self._is_login_success(text)

    @staticmethod
    def _is_login_success(text: str) -> bool:
        return (
            text == "Загрузка данных пользователя..."
            or "Введите код из мобильного приложения Steam" not in text
        )
