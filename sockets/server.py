import socket
import pickle
from threading import Thread
import queue

from snoop import snoop

from auth.SDA import SDA
# import snoop


class ServerSocket:

    def __init__(self):
        self.host = socket.gethostname()
        self.port = 5000
        self.wait_distribution = queue.Queue()
        self.wait_guard = queue.Queue()
        self.socket = socket.socket()
        self.socket.bind((self.host, self.port))
        self.socket.listen(25)
        self.sda = SDA()
        Thread(target=self.start_accept, daemon=False).start()
        Thread(target=self.distribution, daemon=False).start()
        self.start_accept()

    def start_accept(self,):
        while True:
            conn, address = self.socket.accept()
            print(address)
            self.wait_distribution.put((conn, address))


    def distribution(self):
        while True:
            conn, address = self.wait_distribution.get()
            chunk = conn.recv(1024)#todo try-except
            data = b'' + chunk
            data = pickle.loads(data)
            if data[0] == 'guard':
                guard = self.sda.get_guard(data[1])
                try:
                    conn.sendall(pickle.dumps(guard))
                except:
                    pass
            elif data[0] == 'ping':
                pass

            # conn.send(b'1234')
            # conn.close()

if __name__ == '__main__':
    ServerSocket()