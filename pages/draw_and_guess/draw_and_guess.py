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
        encode_socket_data, decode_socket_data,
        handle_websocket_message,
        C_R, C_G, C_B, C_E
)

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



connected_sockets = {} # <int: id> to <socket.socket: client>
connected_sockets["count"] = 0

socket_id_to_user_name = {}
user_name_to_user_uuid = {}
user_uuid_to_room_name = {}
room_name_to_user_list = {}
user_uuid_to_socket_id = {}

def default_data_handler(socket_id, o):
    return ""

data_handlers = {}

running = True

def close(socket_id=None):
    if socket_id == None:
        global running
        running = False
        for id, s in list(connected_sockets.items()):
            if id == "count": continue
            s.close()
            del connected_sockets[id]
            print(f"socket#{id} closed successfully")
    elif socket_id in socket_id_to_user_name:
        user_name = socket_id_to_user_name[socket_id]
        user_uuid = user_name_to_user_uuid[user_name]
        room_name = user_uuid_to_room_name[user_uuid]
        user_list = room_name_to_user_list[room_name]
        assert user_uuid_to_socket_id[user_uuid] == socket_id

        del socket_id_to_user_name[socket_id]
        del user_name_to_user_uuid[user_name]
        del user_uuid_to_room_name[user_uuid]
        del user_uuid_to_socket_id[user_uuid]

        if len(user_list) == 1:
            assert user_list[0] == user_uuid
            del room_name_to_user_list[room_name]
        else:
            user_list.remove(user_uuid)

        s = connected_sockets[socket_id]

        for uuid in user_list:
            if uuid == user_uuid:
                # send stop signal
                s
            else:
                leave_room_message = encode_socket_data(json.dumps({
                        "request": "leave_room",
                        "server": True,
                        "room_name": room_name,
                        "user_uuid": user_uuid,
                        "user_name": user_name,
                        "uuid": uuid,
                }, separators=(",", ":")))
                connected_sockets[user_uuid_to_socket_id[
                        uuid]].sendall(leave_room_message)

        s.close()
        del connected_sockets[socket_id]
        print(f"socket#{C_G}{socket_id}{C_E} closed successfully")

    elif socket_id in connected_sockets:
        s = connected_sockets[socket_id]
        s.close()
        del connected_sockets[socket_id]
        print(f"socket#{C_G}{socket_id}{C_E} closed successfully")
    else:
        print(f"socket#{C_G}{socket_id}{C_E} closed already")

def initializeDrawAndGuessApplication():
    def req_room_list(socket_id, o):
        o["room_list"] = [(n, len(l))
                for n, l in room_name_to_user_list.items()]
        return o
    
    def join_or_create_room(socket_id, o):
        room_name, user_name = o["room_name"], o["user_name"]
        
        o["status"] = False

        if not user_name:
            o["message"] = "invalid user name"
            return o
        elif user_name in user_name_to_user_uuid:
            o["message"] = "user name already exists"
            return o

        user_uuid = o["user_uuid"] if "user_uuid" in o else str(uuid.uuid4())

        if not room_name:
            o["message"] = "invalid room name"
            return o
        elif user_uuid in user_uuid_to_room_name:
            o["message"] = "user already joined a room"
            return o
        elif o["request"] == "create_room":
            if room_name in room_name_to_user_list:
                o["message"] = "room name already exists"
                return o
        elif o["request"] == "join_room":
            if room_name not in room_name_to_user_list:
                o["message"] = "cannot find the room"
                return o

        o["status"] = True

        socket_id_to_user_name[socket_id] = user_name
        user_name_to_user_uuid[user_name] = user_uuid
        user_uuid_to_room_name[user_uuid] = room_name
        user_uuid_to_socket_id[user_uuid] = socket_id

        if o["request"] == "create_room":
            room_name_to_user_list[room_name] = [user_uuid]
        elif o["request"] == "join_room":
            room_name_to_user_list[room_name].append(user_uuid)


        o["user_uuid"] = user_uuid
        o["user_list"] = room_name_to_user_list[room_name]

        return o

    
    data_handlers.update({
        "room_list": req_room_list,
        "create_room": join_or_create_room,
        "join_room": join_or_create_room,
    })



def main():
    initializeDrawAndGuessApplication()
    def handle_socket(client, address):
        connected_sockets["count"] += 1
        socket_id = connected_sockets["count"]
        connected_sockets[socket_id] = client

        d = client.recv(1024).strip()
        print(f"socket#{C_G}{socket_id}{C_E} handshake")

        
        # print("HANDSHAKE HEADERS")
        # for line in data.split(b"\r\n"):
        #     print(line.decode("utf-8"))

        client.sendall(resolve_socket_handshake(d))

        d, r = None, b""

        while socket_id in connected_sockets:
            if d:
                r = d + r
            else:
                r += client.recv(8192)
            d, r = decode_socket_data(r)
            # if not d: continue
            if d.encode("utf-8") == b'\x03\xc3\xa9' or not d:
                print("socket#" + str(socket_id) +
                        " terminate singal received? exiting...")
                break
            print("RESOLVED DATA:", d)
            o = json.loads(d)
            o = data_handlers.get(o["request"],
                    default_data_handler)(socket_id, o)
            if o and isinstance(o, dict):
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
            
        print(f"attempt to close socket#{C_G}{socket_id}{C_E}")
        close(socket_id)
    
    global PORT
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


