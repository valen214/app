#!/bin/python


import importlib
import json
import os
import threading
import socket
import socketserver
# import ssl
import uuid

# import pages.util
# importlib.reload(pages.util)
# from pages.util import (
#     content_type, resolve_socket_handshake,
#     encode_socket_data, decode_socket_data)

from pages.util import (
    content_type, resolve_socket_handshake,
    encode_socket_data, decode_socket_data)

HOST, PORT = "0.0.0.0", 8001

def main_html(env, start_res):
    with open("pages/draw_and_guess/draw_and_guess.htm", "r") as f, \
            open("pages/draw_and_guess/draw_and_guess.css", "r") as c:
        content = f.read().replace("<? PORT ?>", str(PORT))
        content = content.replace('<link rel="stylesheet" ' +
                'href="draw_and_guess/draw_and_guess.css" />',
                "<style>" + c.read() + "</style>")
        start_res("200 OK", [
                ("Content-Type", content_type(".htm")),
                ("Content-Length", str(len(content)))
        ])
        return content

def static_file(name):
    def file_handler(env, start_res):
        # print("HELO")
        with open(name, "r") as f:
            content = f.read()
            start_res("200 OK", [
                    ("Content-Type", content_type(name)),
                    ("Content-Length", str(len(content)))
            ])
            return content
    return file_handler

running = True
s = None

connected_sockets = {
    "client_id": (lambda: 0)()
}

def close():
    global running, s
    if running:
        running = False
        if isinstance(s, socket.socket):
            s.close()
        elif isinstance(s, socketserver.TCPServer):
            s.server_close()
        
        for k, c in connected_sockets.items():
            if k != "client_id":
                c.close()

class DrawAndGuessRoom:
    def __init__(self, name, owner):
        self.name = name
        self.owner = owner
        self.uuid = str(uuid.uuid4())
        self.users = {
            owner.uuid: owner
        }

    def add(self, user):
        assert isinstance(user, DrawAndGuessUser)
        self.users[user.uuid] = user
        user.room = self
    
    def remove(self, user):
        user_uuid = None
        if isinstance(user, DrawAndGuessUser):
            user_uuid = user.uuid
            user.room = None
        elif isinstance(user, str):
            user_uuid = user
        
        if user_uuid in self.users:
            del self.users[user_uuid]





class DrawAndGuessUser:
    INSTANCES_BY_CLIENT_ID = {}

    def __init__(self, client_id, name, user_uuid=None):
        self.client_id = client_id
        self.client = connected_sockets[client_id]
        self.name = name
        self.room = None

        self.uuid = user_uuid or str(uuid.uuid4())

        DrawAndGuessUser.INSTANCES_BY_CLIENT_ID[client_id] = self
    
    @staticmethod
    def getInstance(a):
        return DrawAndGuessUser.INSTANCES_BY_CLIENT_ID[a]
    
    @staticmethod
    def removeInstance(a):
        del DrawAndGuessUser.INSTANCES_BY_CLIENT_ID[a]

class DrawAndGuessApplication:
    def __init__(self):
        # use uuid as keys
        self.users = {}
        self.rooms = {}

    def getUserByName(self, user_name):
        for user in self.users.values():
            if user.name == user_name:
                return user
        return None

    def getRoomByName(self, room_name):
        for room in self.rooms.values():
            if room.name == room_name:
                return room
        return None

    def room_list(self):
        l = []
        r = {
            "request": "room_list",
            "response": "server",
            "status": True,
            "room_list": l,
        }
        for id, room in iter(self.rooms.items()):
            if len(room.users):
                l.append([id, room.name, len(room.users)])
            else:
                del self.rooms[id]
        return r


    def create_user(self, client_id, user_name, user_uuid=None):
        invalid_name = False
        user_exists = self.getUserByName(user_name)

        if not user_name:
            invalid_name = True
        
        if invalid_name or user_exists:
            return {
                "request": "create_user",
                "response": "server",
                "status": False,
                "message": ("invalid user name"
                        if invalid_name else "user name already exists")
            }
        else:
            user = DrawAndGuessUser(client_id, user_name, user_uuid)
            self.users[user.uuid] = user
            return {
                "request": "create_user",
                "response": "server",
                "status": True,
                "user_uuid": user.uuid
            }

    def remove_user(self, user):
        user_uuid = None
        if isinstance(user, DrawAndGuessUser):
            user_uuid = user.uuid
            user.room = None
        elif isinstance(user, str):
            user_uuid = user
        
        if user_uuid in self.users:
            del self.users[user_uuid]

    def create_room(self, client_id, o):
        # if user already in a room
        msg = self.create_user(client_id, o["user_name"])
        if ("status" not in msg) or (
                not msg["status"]):
            msg["request"] = "create_room"
            msg["callback"] = o["callback"]
            return msg
        
        user = self.getUserByName(o["user_name"])
        assert user.client_id == client_id

        invalid_name = not o["room_name"]
        room_exists = self.getRoomByName(o["room_name"])
        if invalid_name or room_exists:
            msg["message"] = ("invalid room name"
                    if invalid_name else "room already exists")
            self.remove_user(user)
            return msg
        
        room = DrawAndGuessRoom(o["room_name"], user)
        self.rooms[room.uuid] = room

        room_users = list(room.users.keys())
        assert room_users[0] == user.uuid

        print(f"user_uuid: {user.uuid}; user_name: {user.name}")

        o["status"] = True
        o["room_uuid"] = room.uuid
        o["user_uuid"] = user.uuid
        o["user_list"] = room_users
        return o

    def join_room(self, client_id, o):
        room_name = o["room_name"]
        room_uuid, room = None, None
        for id, r in self.rooms.items():
            if (room_name == id) or (room_name == r.name):
                room_uuid, room = id, r
                break
        else:
            o["status"] = False
            o["message"] = "room not found"
            return o

        msg = self.create_user(client_id, o["user_name"])
        if ("status" not in msg) or (not msg["status"]):
            o["status"] = False
            o["message"] = msg["message"]
            return o
        
        user = self.users[msg["user_uuid"]]
        

        print(f"join_room: user'{o['user_name']}' joins room({room_uuid}) ")

        if user and room_uuid and room.owner.client_id in connected_sockets:
            room.add(user)

            print("user_list:", " ".join(room.users.keys()))

            o["status"] = True
            o["response"] = "server"
            o["user_uuid"] = user.uuid
            o["user_list"] = list(room.users.keys())
            o["room_uuid"] = room_uuid
            # o["room_name"] # already here
            return o
        else:
            return {
                "request": "join_room",
                "response": "server",
                "status": False,
                "message": "room not found",
                "callback": o["callback"]
            }

    def leave_room(self, client_id, room_uuid, user_uuid):
        room = self.rooms[room_uuid] if room_uuid in self.rooms else None
        user = self.users[user_uuid]
        assert user.client_id == client_id
        if room:
            print("LEAVE ROOM SUCESSFUALLY")
            room.remove(user)



    def handle_socket(self, client_id, data):
        o = {}
        try:
            o = json.loads(data, encoding="utf-8")
        except json.JSONDecodeError:
            print("socket data not in json format:", data)
            print(data.encode("utf-8"))
        
        request = o["request"] if "request" in o else None
        if request == "room_list":
            return self.room_list()
        elif request == "create_room":
            return self.create_room(client_id, o)
        elif request == "join_room":
            return self.join_room(client_id, o)
        else:
            print(f"{' '*8}invalid request: {data}")
        
    def socket_close(self, client_id):
        try:
            c = DrawAndGuessUser.getInstance(client_id)
            assert c.client == connected_sockets[client_id]
            self.leave_room(client_id, c.room, c.uuid)
        except:
            print("socket probably closed")


def main():
    app = DrawAndGuessApplication()
    def handle_socket(client, address):
        connected_sockets["client_id"] += 1
        client_id = connected_sockets["client_id"]
        connected_sockets[client_id] = client

        data = client.recv(1024).strip()
        print("socket#" + str(client_id) + " handshake")

        
        # print("HANDSHAKE HEADERS")
        # for line in data.split(b"\r\n"):
        #     print(line.decode("utf-8"))

        client.sendall(resolve_socket_handshake(data))

        d, r = None, b""

        while client_id in connected_sockets:
            if d:
                r = d + r
            else:
                r += client.recv(8192)
            d, r = decode_socket_data(r)
            # if not d: continue
            if d.encode("utf-8") == b'\x03\xc3\xa9' or not d:
                print("socket#" + str(client_id) +
                        " terminate singal received? exiting...")
                break
            o = app.handle_socket(client_id, d)
            if o and isinstance(o, object):
                client.sendall(encode_socket_data(
                        json.dumps(o, separators=(",", ":"))))
            try:
                a, b = decode_socket_data(r)
            except IndexError as ie:
                if str(ie) == "index out of range":
                    d = None
            else:
                d = a
                r = b
            
        
        app.socket_close(client_id)
        client.close()
        del connected_sockets[client_id]
    
    global PORT, s
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    valid = False
    while (not valid) and PORT <= 8200:
        try:
            sock.bind((HOST, PORT))
            valid = True
        except OSError:
            PORT += 1
    sock.listen(5)
    while running:
        c, addr = sock.accept()
        # c.settimeout(60)
        threading.Thread(target=handle_socket, args=(c, addr)).start()

    close()



def initialize(wsgi_application_handler):

    threading.Thread(target=main).start()

    for regex, func in {
            "/(draw_and_guess/)?draw_and_guess(.html?)?": main_html,
            # "/(draw_and_guess/)?draw_and_guess\.css":
            #         static_file("pages/draw_and_guess/draw_and_guess.css"),
            "/(draw_and_guess/)?canvas.js":
                    static_file("pages/draw_and_guess/canvas.js"),
            "/(draw_and_guess/)?util.js":
                    static_file("pages/draw_and_guess/util.js"),
            "/(draw_and_guess/)?p2p.js":
                    static_file("pages/draw_and_guess/p2p.js"),
    }.items():
        wsgi_application_handler.add("GET", regex, func)

    for abs_path in [
            # "/draw_and_guess", "/draw_and_guess/draw_and_guess.htm",
            "/draw_and_guess/canvas.js", "/draw_and_guess/util.js",
            "/draw_and_guess/p2p.js"]:
        wsgi_application_handler.exclude_log(abs_path)


