import time

from pywinauto import Application, clipboard
import psutil
from loguru import logger
import configparser

from snoop import snoop


class SDA:
    def __init__(self):
        logger.info('Начал инициализацию')
        self.__get_logger_info()
        self.__get_all_items()
        logger.info("Инициализировал SDA")

    logger.info('Смотрю процеесы')
    def __get_top_window(self):
        process_name = "Steam Desktop Authenticator.exe"

        for process in psutil.process_iter():
            if process.name() == process_name:
                process.terminate()
                break
        logger.info('Просмотрел процессы')

        self.app = Application(backend="uia").start(self.path_to_sda)
        time.sleep(2)
        window = self.app.top_window()
        window.child_window(title="ОК").click()
        time.sleep(2)
        self.window = self.app.top_window()
        try:
            self.window.child_window(title="ОК").click()
            self.window = self.app.top_window()
            logger.info("Закрыл обновления")
        except:
            logger.info('Не нашел окно с обновлениями')

    # @snoop
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
        logger.info(f'Получаю guard для {acc_name}')
        self.window.set_focus()
        logger.info('Установил фокус на окно SDA')
        self.filter_label.set_text(acc_name)
        logger.info(f'Задал фильтр {acc_name}')
        self.acc_list.child_window(title=acc_name).select()
        logger.info(f'Выбрал аккаунт {acc_name}')
        self.copy_button.click()
        logger.info('Нажал кнопку копирования')
        self.window.minimize()
        logger.info('Свернул окно SDA')

        return clipboard.GetData()