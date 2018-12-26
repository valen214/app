
import socket
import ssl
import threading

def socket_listener(c, addr):
    data = c.recv(4096)
    while data:
        print(data.decode("utf-8"))
        print("="*80)
        data = c.recv(4096)
        
        
def socket_sender(c, addr):
    line = input()
    while line:
        c.sendall(line)
        line = input()

def start_server():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        context = ssl.SSLContext(ssl._ssl.PROTOCOL_TLS_SERVER)
        context.load_cert_chain("cert_key.pem")
        sock.bind(("", 8000))
        sock.listen(5)
        with context.wrap_socket(sock, server_side=True) as ssock:
            while True:
                c, addr = ssock.accept()
                print("new socket!")
                threading.Thread(target=socket_listener, args=(c, addr)).start()
                threading.Thread(target=socket_sender, args=(c, addr)).start()
                
                
                
def start_client():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        context = ssl.SSLContext()
        context.verify_mode = ssl.CERT_NONE
        context.load_default_certs()
        with context.wrap_socket(sock, server_hostname="localhost") as ssock:
            ssock.connect(("localhost", 8000))
            print("new socket created!")
            threading.Thread(target=socket_listener, args=(ssock, None)).start()
            threading.Thread(target=socket_sender, args=(ssock, None)).start()
