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
            logger.info("SDA started")
        except:
            # logger.error("Failed to initialize SDA")
            self.sda = None

        if self.sda is not None:
            # Thread(target=self.start_accept, daemon=False).start()
            Thread(target=self.__update_acc, daemon=False).start()
            Thread(target=self.guard, daemon=False).start()
            self.start_accept()
        else:
            ctypes.windll.user32.MessageBoxW(0, f"Проблема при открытии SDA. Проверьте путь до SDA в конфиг-файле",
                                             "SDA",1)

    def start_accept(self,):
        logger.info("Start accept connection")
        while True:
            conn, address = self.socket.accept()
            logger.info("Start accept connection on address " + address[0])
            Thread(target=self.distribution, args=[conn, address], daemon=False).start()

    # @snoop
    def distribution(self, conn, address):
        while True:
            try:
                chunk = conn.recv(1024)
                data = pickle.loads(chunk)
            except:
                break

            # print(f"Connection {data[3]}, account - {data[2]}, task - {data[0]}")
            logger.info(f"Connection {data[3]}, account - {data[2]}, task - {data[0]}")
            if data[0] == 'guard':
                self.wait_guard.put((data, conn))
            elif data[0] == 'ping':
                self.wait_ping.put(data[1])


    def __update_acc(self,):
        logger.info("Запустил обновление аккаунтов")
        if path.exists('backup.json'):
            try:
                with open('backup.json', 'r') as file:
                    self.backup = json.load(file)
                logger.info(f'Прочитал файл backup.json - {self.backup}')
            except json.JSONDecodeError:
                self.backup = {}
                logger.error('Не смог прочитать файл backup.json. Создаю новый файл')
        else:
            logger.info('Не нашел файл backup.json. Создаю новый файл')
            with open('backup.json', 'w+'):
                pass



        Thread(target=self.__get_ping_acc, daemon=False).start()
        while True:
            sleep(30)
            for id_ in list(self.backup):
                logger.info(f"{id_}, status, {self.backup[id_]}")
                if self.backup[id_] == 0:
                    can_offline = self.set_acc_status(id_)
                    if can_offline:
                        logger.info(f"Send offline {id_}")
                        with self.lock:
                            self.backup.pop(id_)
                else:
                    self.backup[id_] = 0
            with open('backup.json', 'w+') as file:
                json.dump(self.backup, file, indent=4)


    def __get_ping_acc(self):
        while True:
            id_ = self.wait_ping.get()
            id_ = str(id_)
            if id_ in self.backup:
                with self.lock:
                    self.backup[id_] = 1
            else:
                suc = self.set_acc_status(id_, status=True)
                if suc:
                    with self.lock:
                        self.backup[id_] = 1
            # print(f'')

    # @snoop
    def guard(self,):
        while True:
            data, conn = self.wait_guard.get()

            id_ = data[1]
            username = data[2]
            hostname = data[3]
            # print(f'Get request from {hostname}, account {username}, id = {id_}')
            logger.info(f'Get request from {hostname}, account {username}, id = {id_}')

            guard = self.sda.get_guard(username)
            logger.info(f'guard for {username} - {guard}')

            self.wait_ping.put(id_)

            try:
                conn.sendall(pickle.dumps(guard))
                logger.info(f'Send guard to {hostname}, account {username}')
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


    def set_acc_status(self, id_, status=False):
        if status:
            query = f"UPDATE users SET online = TRUE WHERE id = {id_}"
            status = 'online'
        else:
            query = f"UPDATE users SET online = FALSE WHERE id = {id_}"
            status = 'offline'
        try:

            connection = mysql.connector.connect(
                host=host_ip,
                user=login_db,
                passwd=pass_db,
                database=name_db
            )
            logger.info(f'Подключился к БД, чтобы отправить аккаунт {id_} в {status}')
        except Exception as e:
            logger.error(f'Сервер не смог подключиться к БД, чтобы отправить аккаунт {id_} в {status}')
            print(f'Error connecting to BD for offline {id_}')
            return False

        try:
            cursor = connection.cursor()
            cursor.execute(query)
            connection.commit()
            cursor.close()
            connection.close()
            # print(f"Account offline: {id_}")
            logger.info(f'Отправил аккаунт {id_} в {status}')
            return True
        except:
            # print(f"Error updating account {id_}")
            logger.error(f"Не смог отправить аккаунта {id_} в {status}")
            return False

if __name__ == '__main__':
    logger.add("./file_server.log", format="{time:DD.MM.YYYY at HH:mm:ss} | {name}:{function}:{line} | {level} | {message}", level="INFO", rotation="100MB")
    handler = NotificationHandler("telegram", defaults=params)
    logger.add(handler, level="ERROR")
    ServerSocket()

#todo сделать проверку свободных хостов в гизмо и все акки в оффлайн