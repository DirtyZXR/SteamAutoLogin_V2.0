import socket
import pickle
from threading import Thread
import queue
from loguru import logger
from notifiers.logging import NotificationHandler
from loger_data import params
import json
from os import path
from time import sleep

from SDA import SDA
# import snoop

logger.add("../file_server.log", format="{time:DD.MM.YYYY at HH:mm:ss} | {name}:{function}:{line} | {level} | {message}", level="INFO", rotation="100MB")
handler = NotificationHandler("telegram", defaults=params)
logger.add(handler, level="ERROR")

class ServerSocket:

    def __init__(self):
        self.host = socket.gethostname()
        self.port = 5000
        self.wait_distribution = queue.Queue()
        self.wait_guard = queue.Queue()
        self.wait_ping = queue.Queue()
        self.socket = socket.socket()
        self.socket.bind((self.host, self.port))
        self.socket.listen(25)
        try:
            self.sda = SDA()
        except:
            # logger.error("Failed to initialize SDA")
            self.sda = None

        if self.sda is not None:
            Thread(target=self.start_accept, daemon=False).start()
            Thread(target=self.distribution, daemon=False).start()
            self.start_accept()
        else:
            pass#todo вывести уведомление о sda

    def start_accept(self,):
        while True:
            conn, address = self.socket.accept()
            self.wait_distribution.put((conn, address))


    def distribution(self):
        while True:
            conn, address = self.wait_distribution.get()
            chunk = conn.recv(1024)#todo try-except
            data = b'' + chunk
            data = pickle.loads(data)
            if data[0] == 'guard':
                self.guard(data, conn)
            elif data[0] == 'ping':
                self.wait_ping.put(data[1])

            # conn.send(b'1234')
            # conn.close()

    def __update_acc(self,):
        if path.exists('backup.json'):
            self.backup = json.loads('backup.json')
        else:
            with open('backup.json', 'w+'):
                pass
        Thread(target=self.__get_ping_acc, daemon=False).start()

        while True:
            sleep(30)
            for username in self.backup:
                if self.backup[username] == 0:
                    self.backup.pop(username)
                    #todo отправка в бд аккаунта в офлайн
                else:
                    self.backup[username] = 0
            with open('backup.json', 'w') as file:
                json.dump(self.backup, file)

    def __get_ping_acc(self):
        while True:
            username = self.wait_ping.get()
            self.backup[username] = 1

    def guard(self, data, conn):
        username = data[1]
        hostname = data[2]
        guard = self.sda.get_guard(username)

        self.update_acc(username, hostname)

        try:
            conn.sendall(pickle.dumps(guard))
        except:
            pass#todo логер и ошибку



if __name__ == '__main__':
    ServerSocket()