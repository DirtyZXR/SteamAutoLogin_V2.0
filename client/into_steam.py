import time
from venv import logger

from pywinauto import Application
import pynput
import winreg


class Steam:
    def __init__(self, login:str, password:str, id_game:int):
        self.app = self.run_steam(login, password, id_game)
        self.guard = self.login(login, password)



    def run_steam(self, login:str, password:str, id_game:int):
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Valve\Steam")
        path_steam, regtype = winreg.QueryValueEx(key, "SteamExe")
        path_steam += f'-language "russian" -login {login} -password {password} -applaunch {id_game}'
        app = Application(backend="uia").start(path_steam)

        while True and app.is_process_running():
            try:
                app = Application(backend="uia").connect(title="Войти в Steam")
                break
            except:
                pass

        return app

    def login(self, login, password, try_number = 0) -> bool:
        window = self.app.top_window()
        f = 0
        while True:
            try:
                window.child_window(control_type="Edit", found_index=0).wait(wait_for="active", timeout=5)
                break
            except:
                f += 1
                try:
                    enter = window.child_window(title="Вход...").window_text()
                    if enter != "Вход...":
                        if f > 5:
                            raise Exception("Не удалось найти поле ввода логина")
                        else:
                            f = True
                except:
                    pass

        try:

            window.child_window(control_type="Edit", found_index=0).set_text(login)
            window.child_window(control_type="Edit", found_index=1).set_text(password)
            window.child_window(title="Войти").click()

            text_wait = 'Создайте бесплатный аккаунт'
            try:
                while 'Создайте бесплатный аккаунт' in text_wait or len(text_wait) == 13:
                    text_wait = window.child_window(control_type="Document", found_index=0).wait(wait_for='active', timeout=10)
                    text_wait = text_wait.window_text()
            except:
                pass


            # print(text_wait)#Ошибка При входе в аккаунт произошла ошибка. Повторите попытку позже. Повторить Код ошибки: e87
            if 'Введите код' in text_wait:
                return True
            elif 'Ошибка' in text_wait:
                window.child_window(title='Повторить').click()
                try_number += 1
                if try_number >= 3:
                    raise Exception('У стима ошибка')#todo вывести на экран
                else:
                    return self.login(login, password, try_number)
            else:
                return False
        except Exception as e:
            raise Exception(f"Ошибка при входе в аккаунт - {e}")



    def guard_input(self, guard_code:str):
        try_number = 0
        window = self.app.top_window()
        while try_number < 5:
            try:
                for i in range(5):
                   window.child_window(control_type="Edit", found_index=i).set_text(guard_code[i])
                break
            except:
                try_number += 1
                time.sleep(3)