import socket
import pickle
from threading import Thread
import queue
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
        Thread(target=self.start_accept, daemon=True).start()#todo в клиенте исправить daemon = True
        Thread(target=self.distribution, daemon=True).start()


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
                pass
            elif data[0] == 'ping':
                pass

            # conn.send(b'1234')
            # conn.close()

def chat(conn, address,):
    # conn, address = server_socket.accept() # accept new connection
    print("Connection from: " + str(address))
    while True:
        # receive data stream. it won't accept data packet greater than 1024 bytes
        data = conn.recv(1024).decode()
        if not data:
            # if data is not received break
            break
        print("from connected user: " + str(data))
        data = input(' -> ')
        conn.send(data.encode()) # send data to the client
    conn.close() # close the connection


if __name__ == '__main__':
    ServerSocket()