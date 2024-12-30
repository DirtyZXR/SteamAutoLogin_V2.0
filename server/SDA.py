from pywinauto import Application, clipboard
import psutil
from loguru import logger
from notifiers.logging import NotificationHandler
from snoop import snoop

from client.loger_data import params
from os import path
import configparser




class SDA:
    def __init__(self):
        self.__get_logger_info()
        self.__get_all_items()

    def __get_top_window(self):
        process_name = "Steam Desktop Authenticator.exe"

        for process in psutil.process_iter():
            if process.name() == process_name:
                process.terminate()
                break

        self.app = Application(backend="uia").start(self.path_to_sda)
        window = self.app.top_window()
        window.child_window(title="ОК").click()
        self.window = self.app.top_window()

    def __get_all_items(self):
        if self.path_to_sda is None:
            raise Exception("Не указан путь к Steam Desktop Authenticator")
        self.__get_top_window()
        self.window = self.app.top_window()
        self.filter_label = self.window.child_window(auto_id="txtAccSearch", control_type="Edit")
        self.acc_list = self.window.child_window(auto_id="listAccounts", control_type="List")
        self.copy_button = (self.window.child_window(title="Login Token", auto_id="groupBox1", control_type="Group")
                            .child_window(title="Copy", auto_id="btnCopy", control_type="Button"))
        self.window.minimize()


    def __get_logger_info(self):
        logger.add("./file_sda.log", format="{time:DD.MM.YYYY at HH:mm:ss} | {name}:{function}:{line} | {level} | {message}", level="INFO", rotation="100MB")
        handler = NotificationHandler("telegram", defaults=params)
        logger.add(handler, level="ERROR")

        config = configparser.ConfigParser()
        logger.info("Reading config")
        try:
            config.read("./config_sda.ini")
            config.items()
            self.path_to_sda = config.get("SDA",'path_to_SDA')
            logger.info("Прочитал конфиг, путь до SDA - {path}", path=self.path_to_sda)
        except:
            logger.error('Не смог прочитать конфиг файл.')
            self.path_to_sda = None

    def get_guard(self, acc_name: str) -> str:
        self.window.restore()
        self.filter_label.set_text(acc_name)
        self.acc_list.child_window(title=acc_name).select()
        self.copy_button.click()
        self.window.minimize()

        return clipboard.GetData()
