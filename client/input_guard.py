from time import sleep

import pynput
from loguru import logger

INPUT_BLOCK_TIMEOUT = 30


class InputGuard:
    def __init__(self):
        self.keyboard_listener: pynput.keyboard.Listener | None = None
        self.mouse_listener: pynput.mouse.Listener | None = None

    def block(self):
        self.keyboard_listener = pynput.keyboard.Listener(suppress=True)
        self.mouse_listener = pynput.mouse.Listener(suppress=True)
        self.keyboard_listener.start()
        self.mouse_listener.start()
        logger.info("Клавиатура и мышь заблокированы")

    def unblock(self):
        if self.keyboard_listener:
            self.keyboard_listener.stop()
        if self.mouse_listener:
            self.mouse_listener.stop()
        logger.info("Клавиатура и мышь разблокированы")

    def auto_unblock(self):
        sleep(INPUT_BLOCK_TIMEOUT)
        self.unblock()
