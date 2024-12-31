import subprocess
from asyncio import timeout
from time import sleep
import win32gui, win32process
from  interface_for_var_acc import get_num_acc
import os
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
import snoop

class Steam:
    def __init__(self, login:str, password:str, id_game:int):
        self.app = self.run_steam(login, password, id_game)
        self.guard = self.login(login, password)



    def run_steam(self, login:str, password:str, id_game:int):
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Valve\Steam")
        path_steam, regtype = winreg.QueryValueEx(key, "SteamExe")
        path_steam += f' -login {login} -password {password} -applaunch {id_game}'
        app = Application(backend="uia").start(path_steam)

        while True and app.is_process_running():
            try:
                app = Application(backend="uia").connect(title="Войти в Steam")
                break
            except:
                pass

        return app

    @snoop
    def login(self, login, password):
        window = self.app.top_window()
        f = False
        while True:
            try:
                window.child_window(control_type="Edit", found_index=0).wait(wait_for="active", timeout=5)
                break
            except:
                enter = window.child_window(title="Вход...").window_text()
                if enter != "Вход...":
                    if f:
                        raise Exception("Не удалось найти поле ввода логина")
                    else:
                        f = True


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

        print(text_wait)#todo Ошибка При входе в аккаунт произошла ошибка. Повторите попытку позже. Повторить Код ошибки: e87
        if 'Введите код' in text_wait:
            return True
        else:
            return False

    def guard_input(self, guard_code:str):
        window = self.app.top_window()
        for i in range(5):
           window.child_window(control_type="Edit", found_index=i).set_text(guard_code[i])




steam = Steam("fabiooo12345", "qsxcgyujm1590.", 730)
if steam.guard:
    a = input()
    steam.guard_input(a)
