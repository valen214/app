#/bin/python


import importlib
import json
import os
import threading
import socket
# import ssl
import time
import uuid
HOST, PORT = "0.0.0.0", 8001

# import pages.util
# importlib.reload(pages.util)
from pages.util import (
        content_type, resolve_socket_handshake,
        decode_socket_data, encode_socket_data,
        handle_websocket_message,
        C_R, C_G, C_B, C_E
)

    
CLOSEABLE = set()
initialized = False
running = True
server_socket = None

def close():
    global running, server_socket
    running = False
    server_socket = None
    for c in CLOSEABLE:
        c.close()

def main():
    def socket_signal(data, c):
        try:
            data = data.decode("utf-8")
            if not data:
                return
            o = json.loads(data, encoding="utf-8")
        except json.decoder.JSONDecodeError:
            print("\n" * 2 + "#" * 80)
            print("data not in json format:", data.hex())
            """
            b'\x88\x82\xea\xdd\xd5\x99\xe94'
            b'\x88\x82M\x86K\xe7No'
            b"\x88\x82$\xafF\xf0'F"
            b'\x88\x82\xe9Qp\xee\xea\xb8'
            
            b'\x88\x805\xb3\x9a6'
            b'\x88\x80\x89\xb8#\xc3'
            """
            print(f"socket#{C_B}{c.no}{C_E} not handled")
            print("#" * 80)
            return
        
        # print(f"\nsocket_signal: {json.dumps(o)}\n")
        if o["type"] == "create_peer":
            assert o["uuid"]
            c.setUUID(o["uuid"])
            c.sendObj({
                "type": "peer_created",
                "uuid": c.uuid,
            })
        elif o["type"] == "create_offer":
            print(f"create_offer {o['offerer_uuid']} => {o['receiver_uuid']}")
            assert c.uuid == o["offerer_uuid"]
            print(f"client#{c.no} created offer")
            o["type"] = "receive_offer"
            try:
                ClientSocket.getByUUID(o["receiver_uuid"]).sendObj(o)
            except KeyError as ke:
                print(ke)
                c.sendObj({
                    "status": False,
                    "response": "server"
                })
        elif o["type"] == "created_answer":
            assert c.uuid == o["receiver_uuid"]
            print(f"client#{c.no} created answer")
            o["type"] = "receive_answer"
            try:
                ClientSocket.getByUUID(o["offerer_uuid"]).sendObj(o)
            except KeyError as ke:
                print(ke)
                c.sendObj({
                    "status": False,
                    "response": "server"
                })
        elif o["type"] == "ice_candidate":
            try:
                ClientSocket.getByUUID(o["remote_uuid"]).sendObj(o)
            except KeyError as ke:
                print(ke)
                c.sendObj({
                    "status": False,
                    "response": "server"
                })

        return False



    class ClientSocket:  # socket wrapper
        count = 0
        ADDRESS_TO_CLIENT = {}
        UUID_TO_CLIENT = {}

        def __init__(self, client, address):
            ClientSocket.count + 1

            self.client = client
            self.address = None
            self.uuid = None
            self.setAddress(address)
            # self.setUUID(str(uuid.uuid4()))
            self.no = ClientSocket.count
            self.alive = True


        def handle_handshake(self):
            # initial data for js WebSocket handshake
            data = self.client.recv(1024)
            print(f"socket#{C_B}{self.no}{C_E} handshake")
            self.client.sendall(resolve_socket_handshake(data))
        
        def sendObj(self, obj):
            self.client.sendall(encode_socket_data(
                    json.dumps(obj, separators=(",", ":"))))

        def close(self):
            if self.alive:
                self.alive = False
                try:
                    self.deleteByAddress(self.address)
                except Exception as e:
                    print(f"error in closing socket#{self.no}: {e}")
            else:
                print(f"socket#{C_B}{self.no}{C_E} already closed")
        
        # getter and setter of address and uuid
        def setAddress(self, address, retry=True):
            if address in ClientSocket.ADDRESS_TO_CLIENT:
                try:
                    ClientSocket.deleteByAddress(address)
                except KeyError:
                    raise KeyError("FATAL!")
            self.address = address
            ClientSocket.ADDRESS_TO_CLIENT[address] = self
        def setUUID(self, uuid):
            if uuid in ClientSocket.UUID_TO_CLIENT:
                try:
                    ClientSocket.deleteByUUID(uuid)
                except KeyError:
                    raise KeyError("FATAL!")
            self.uuid = uuid
            ClientSocket.UUID_TO_CLIENT[uuid] = self
        
        @classmethod
        def getByAddress(cls, address, retry=True):
            assert cls == ClientSocket
            if retry and address not in cls.ADDRESS_TO_CLIENT:
                time.sleep(5.0)
            if address in cls.ADDRESS_TO_CLIENT:
                return cls.ADDRESS_TO_CLIENT[address]
            else:
                raise KeyError(f"cannot find client with address: {address}")
                
        @classmethod
        def getByUUID(cls, uuid, retry=True):
            if retry and uuid not in cls.UUID_TO_CLIENT:
                time.sleep(5.0)
            if uuid in cls.UUID_TO_CLIENT:
                return cls.UUID_TO_CLIENT[uuid]
            else:
                raise KeyError("cannot find client with uuid: " + uuid)
        
        # only one need to be called
        @classmethod
        def deleteByAddress(cls, address):
            self = cls.getByAddress(address, False)
            self.alive = False
            del cls.ADDRESS_TO_CLIENT[address]
            if self.uuid:
                del cls.UUID_TO_CLIENT[self.uuid]
        @classmethod
        def deleteByUUID(cls, uuid):
            self = cls.getByUUID(uuid, False)
            self.alive = False
            del cls.UUID_TO_CLIENT[uuid]
            if self.address:
                del cls.ADDRESS_TO_CLIENT[self.address]

    def handle_socket(client, address):
        c = ClientSocket(client, address) # socket wrapper
        CLOSEABLE.add(c)
        c.handle_handshake() # js WebSocket handshake

        try:
            while c.alive:
                # handler of web rtc protocol
                handle_websocket_message(client, socket_signal, c)
        except OSError as ose:
            print(repr(ose))
            print(str(ose) == "OSError(9, 'Bad file descriptor')")
        print(f"socket#{C_B}{c.no}{C_E} closing...")
        c.close()
    
    global PORT, server_socket
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    valid = False
    while (not valid) and PORT <= 8200:
        try:
            server_socket.bind((HOST, PORT))
            valid = True
        except OSError:
            PORT += 1
    if valid:
        CLOSEABLE.add(server_socket)
        socket.setdefaulttimeout(None)
        server_socket.listen()
        while running:
            c, addr = server_socket.accept()
            print(f"{' '*8}new connection at {addr}")
            CLOSEABLE.add(c)
            # c.settimeout(60)
            threading.Thread(target=handle_socket, args=(c, addr)).start()
        close()
    else:
        close()
        raise Exception("invalid port range, socket creation failed")





def initialize(wsgi_application_handler):
    global initialized
    if initialized:
        raise Exception("<module " + __name__ + "> already initialized")
    else:
        initialized = True


    threading.Thread(target=main).start()


    webrtc_js_path = "pages/webrtc/webrtc.js"
    webrtc_js_last_modified = os.stat(webrtc_js_path).st_mtime
    webrtc_js_cache = None
    def webrtc_js(env, start_res):
        nonlocal webrtc_js_cache
        # print("HELO")
        if (not webrtc_js_cache) or (
                webrtc_js_last_modified < os.stat(webrtc_js_path).st_mtime):
            with open(webrtc_js_path, "r") as f:
                webrtc_js_cache = f.read()
        content = webrtc_js_cache.replace("<? PORT ?>", str(PORT))
        start_res("200 OK", [
                ("Content-Type", content_type("webrtc.js")),
                ("Content-Length", str(len(content)))
        ])
        return content
    
    for regex, func in {
            "/(webrtc/)?webrtc(_peer)?(.js?)?": webrtc_js,
    }.items():
        wsgi_application_handler.add("GET", regex, func)
