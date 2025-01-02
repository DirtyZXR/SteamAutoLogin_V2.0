import ctypes
import socket
import pickle
import queue
import json
import mysql.connector

from threading import Thread, Lock
from loguru import logger
from notifiers.logging import NotificationHandler
from snoop import snoop

from data_all import host_ip, login_db, pass_db, name_db
from loger_data import params
from os import path
from time import sleep
from SDA import SDA



class ServerSocket:

    def __init__(self):
        # self.host = socket.gethostname()
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        self.host = ip
        self.port = 5000
        self.wait_guard = queue.Queue()
        self.wait_ping = queue.Queue()
        self.wait_distribution = queue.Queue()
        self.lock = Lock()
        self.backup = {}
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
            Thread(target=self.__update_acc, daemon=False).start()
            Thread(target=self.guard, daemon=False).start()
            self.start_accept()
        else:
            ctypes.windll.user32.MessageBoxW(0, f"Проблема при открытии SDA. Проверьте путь до SDA в конфиг-файле",
                                             "SDA",1)

    def start_accept(self,):
        while True:
            conn, address = self.socket.accept()
            Thread(target=self.distribution, args=[conn, address], daemon=False).start()

    # @snoop
    def distribution(self, conn, address):
        while True:
            try:
                chunk = conn.recv(1024)
                data = pickle.loads(chunk)
            except:
                break

            if data[0] == 'guard':
                self.wait_guard.put((data, conn))
            elif data[0] == 'ping':
                self.wait_ping.put(data[1])


    def __update_acc(self,):

        if path.exists('backup.json'):
            try:
                self.backup = json.loads('backup.json')
            except json.JSONDecodeError:
                self.backup = {}
        else:
            with open('backup.json', 'w+'):
                pass


        Thread(target=self.__get_ping_acc, daemon=False).start()
        while True:
            sleep(30)
            for id_ in list(self.backup):
                if self.backup[id_] == 0:
                    with self.lock:
                        self.backup.pop(id_)
                    self.set_acc_ofline(id_)
                else:
                    self.backup[id_] = 0
            with open('backup.json', 'w') as file:
                json.dump(self.backup, file)


    def __get_ping_acc(self):
        while True:
            id_ = self.wait_ping.get()
            with self.lock:
                self.backup[id_] = 1
            # print(self.backup)

    # @snoop
    def guard(self,):
        while True:
            data, conn = self.wait_guard.get()

            id_ = data[1]
            username = data[2]
            hostname = data[3]

            guard = self.sda.get_guard(username)

            self.wait_ping.put(id_)

            try:
                conn.sendall(pickle.dumps(guard))
                logger.info('Отправил гвард')
            except Exception as e:
                ctypes.windll.user32.MessageBoxW(0, f"Не смог отправить guard на {hostname}",
                                                 "Steam Guard",1)
                logger.warning(f'Не смог отправить гвард на {hostname}. Ошибка {e}')


    def create_connection(self, host_name, user_name, user_password, db_name):
        connection = None
        try:

            connection = mysql.connector.connect(
                host=host_name,
                user=user_name,
                passwd=user_password,
                database=db_name
            )
            return connection
        except Exception as e:
            logger.error("Error connecting to BD")
            return False


    def set_acc_ofline(self, id_):
        query = f"UPDATE users SET online = FALSE WHERE id = {id_}"
        try:

            connection = mysql.connector.connect(
                host=host_ip,
                user=login_db,
                passwd=pass_db,
                database=name_db
            )
        except Exception as e:
            logger.error('Сервер не смог подключиться к БД')
            return False

        try:
            cursor = connection.cursor()
            cursor.execute(query)
            connection.commit()
            cursor.close()
            connection.close()
            logger.info('Отправил аккаунт в офлайн')
            return True
        except:
            logger.error("Не смог обновить данные аккаунта")
            return False

if __name__ == '__main__':
    logger.add("./file_server.log", format="{time:DD.MM.YYYY at HH:mm:ss} | {name}:{function}:{line} | {level} | {message}", level="INFO", rotation="100MB")
    handler = NotificationHandler("telegram", defaults=params)
    logger.add(handler, level="ERROR")
    ServerSocket()