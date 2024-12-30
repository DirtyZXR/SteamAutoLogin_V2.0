import socket
from copyreg import pickle
import configparser
import pickle
import snoop
from loguru import logger
# from notifiers.logging import NotificationHandler
from loger_data import params

logger.add("../file.log", format="{time:DD.MM.YYYY at HH:mm:ss} | {name}:{function}:{line} | {level} | {message}", level="INFO", rotation="100MB")
# handler = NotificationHandler("telegram", defaults=params)
# logger.add(handler, level="ERROR")

class ClientSocket:
    def __init__(self):
        self.hostname = socket.gethostname()
        self.ip = self.__get_ip()
        self.port = 5000
        self.socket = socket.socket()

        config = configparser.ConfigParser()
        logger.info("Reading config")
        try:
            config.read("config.ini")
            self.server_ip = config.get("Settings",'server_ip')
            self.server_port = int(config.get("Settings",'port'))
            logger.info("Хост - {ip}", ip=self.server_ip)
        except:
            logger.error('Не смог прочитать конфиг файл. {host}', host = self.hostname)


        self.can_connected = None
        self.host_ping()



    def connection_usage(self):   #todo: Попробовать сделать поиск сервера по локальной сети(функция не используется)
        str_ip = "192.168.88."
        ip = None
        name = socket.gethostname()
        for i in range(255):
            test_ip = str_ip + str(i + 1)
            test_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            test_connection = test_socket.connect(test_ip, 5000)
            if test_connection == 10061:
                continue
            else:
                test_socket.send(name)


    def __get_ip(self):

        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        logger.info("Connected 8.8.8.8. My ip = {ip}", ip=ip)
        return ip


    def host_ping(self) -> bool:
        if self.can_connected is None:
            server_connection = self.socket.connect_ex((self.server_ip, self.server_port))
        else:
            self.socket.close()
            self.socket = socket.socket()
            server_connection = self.socket.connect_ex((self.server_ip, self.server_port))

        if server_connection == 10061:
            logger.warning("Хост не доступен.")
            self.can_connected = None
            return False
        else:
            logger.info("Подключился к хосту")
            self.can_connected = True
            return True


    def ping_acc(self, username: str): #todo сделать отправку в БД самостоятельно
        data = pickle.dumps(("ping", username, self.hostname,))
        try:
            self.socket.sendall(data)
        except:
            logger.warning("Не смог отправить пинг хосту")


    def get_guard(self, username: str):
        data = pickle.dumps(("guard", username, self.hostname,))
        try:
            self.socket.sendall(data)
        except:
            logger.warning("Не смог отправить запрос о гварде хосту")
            return "ERROR"

        try:
            chunk = self.socket.recv(1024)
        except:
            logger.warning("Не смог получить ответ гварда от  хоста")
            return "ERROR"

        # data = b''
        # data += chunk
        # guard = data.decode('utf-8')
        data = pickle.loads(chunk)
        return data

        # return guard


if __name__ == '__main__':
    client_soket = ClientSocket()
    f = client_soket.get_guard("fabiooo12345")
    print(f)