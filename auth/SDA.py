from pywinauto import Application, clipboard
import psutil

path_to_SDA = "C:\\Users\Denis-PC\Desktop\SDA.1.0.15\Steam Desktop Authenticator.exe"

class SDA:
    def __init__(self):
        self.__get_all_items()

    def __get_top_window(self):
        process_name = "Steam Desktop Authenticator.exe"

        for process in psutil.process_iter():
            if process.name() == process_name:
                process.terminate()
                break

        self.app = Application(backend="uia").start(path_to_SDA)
        window = self.app.top_window()
        window.child_window(title="ОК").click()
        self.window = self.app.top_window()

    def __get_all_items(self):
        self.__get_top_window()
        self.window = self.app.top_window()
        self.filter_label = self.window.child_window(auto_id="txtAccSearch", control_type="Edit")
        self.acc_list = self.window.child_window(auto_id="listAccounts", control_type="List")
        self.copy_button = (self.window.child_window(title="Login Token", auto_id="groupBox1", control_type="Group")
                            .child_window(title="Copy", auto_id="btnCopy", control_type="Button"))
        self.window.minimize()


    def get_guard(self, acc_name: str) -> str:
        self.window.restore()
        self.filter_label.set_text(acc_name)
        self.acc_list.child_window(title=acc_name).select()
        self.copy_button.click()
        self.window.minimize()

        return clipboard.GetData()
