import time

import psutil
from loguru import logger
from pywinauto import Application
from pywinauto.clipboard import clipboard


class SDAAutomation:
    def __init__(self, path_to_sda: str):
        if not path_to_sda:
            raise ValueError("Путь к SDA не указан")
        self.path_to_sda = path_to_sda
        self.app: Application | None = None
        self.window = None
        self.filter_label = None
        self.acc_list = None
        self.copy_button = None
        self._launch()

    def _launch(self):
        self._kill_existing()
        logger.info("Запуск SDA")
        self.app = Application(backend="uia").start(self.path_to_sda)
        time.sleep(2)

        window = self.app.top_window()
        try:
            window.child_window(title="ОК").click()
            time.sleep(2)
        except Exception:
            pass

        window = self.app.top_window()
        try:
            window.child_window(title="ОК").click()
            time.sleep(1)
        except Exception:
            pass

        self.window = self.app.top_window()
        self.filter_label = self.window.child_window(
            auto_id="txtAccSearch", control_type="Edit"
        )
        self.acc_list = self.window.child_window(
            auto_id="listAccounts", control_type="List"
        )
        self.copy_button = (
            self.window.child_window(
                title="Login Token", auto_id="groupBox1", control_type="Group"
            )
            .child_window(title="Copy", auto_id="btnCopy", control_type="Button")
        )
        self.window.minimize()
        logger.info("SDA инициализирован")

    def _kill_existing(self):
        for process in psutil.process_iter():
            if process.name() == "Steam Desktop Authenticator.exe":
                process.terminate()
                break

    def get_guard(self, account_name: str) -> str:
        logger.info(f"Получение guard для {account_name}")
        self.window.set_focus()
        self.filter_label.set_text(account_name)
        self.acc_list.child_window(title=account_name).select()
        self.copy_button.click()
        self.window.minimize()
        return clipboard.GetData()
