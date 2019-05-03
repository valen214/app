#!/bin/python


import importlib
import json
import os
import threading
import socket
import socketserver
import ssl
import uuid

# import pages.util
# importlib.reload(pages.util)
from pages.util import (
        content_type,
        encode_socket_data, decode_socket_data,
        get_next_websocket_message, handle_socket_handshake,
        R, G, B, E
)

HOST, PORT = "0.0.0.0", 8001

def main_html(env, start_res):
    threading.Thread(target=main).start()

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
    print(f"{B}close signal received by draw_and_guess.py{E}")
    if socket_id == None:
        global running
        running = False
        for id, s in connected_sockets.items():
            if id == "count":
                continue
            elif id == "active":
                s.close()
                continue
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
                        "type": "leave_room",
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
        print(f"socket#{G}{socket_id}{E} closed successfully")

    elif socket_id in connected_sockets:
        s = connected_sockets[socket_id]
        s.close()
        del connected_sockets[socket_id]
        print(f"socket#{G}{socket_id}{E} closed successfully")
    else:
        print(f"socket#{G}{socket_id}{E} closed already")

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
        elif o["type"] == "create_room":
            if room_name in room_name_to_user_list:
                o["message"] = "room name already exists"
                return o
        elif o["type"] == "join_room":
            if room_name not in room_name_to_user_list:
                o["message"] = "cannot find the room"
                return o

        o["status"] = True

        socket_id_to_user_name[socket_id] = user_name
        user_name_to_user_uuid[user_name] = user_uuid
        user_uuid_to_room_name[user_uuid] = room_name
        user_uuid_to_socket_id[user_uuid] = socket_id

        if o["type"] == "create_room":
            room_name_to_user_list[room_name] = [user_uuid]
        elif o["type"] == "join_room":
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


        
        # print("HANDSHAKE HEADERS")
        # for line in data.split(b"\r\n"):
        #     print(line.decode("utf-8"))

        print(f"{' '*8}draw_and_guess.py:",
                f"socket#{G}{socket_id}{E} handshake")
        handle_socket_handshake(client)

        while socket_id in connected_sockets:
            d = get_next_websocket_message(client)
            if not d:
                print(f"socket#{G}{socket_id}{E}" +
                        " terminate singal received? exiting...")
                break
            try:
                o = json.loads(d)
                o = data_handlers.get(o["type"],
                        default_data_handler)(socket_id, o)
                if o and isinstance(o, dict): # returned value
                    client.sendall(encode_socket_data(
                            json.dumps(o, separators=(",", ":"))))
            except json.decoder.JSONDecodeError:
                print(f"{' '*8}draw_and_guess.py:",
                        f"socket#{G}{socket_id}{E}:",
                        f"data not in json format: {d}")

        print(f"attempt to close socket#{G}{socket_id}{E}")
        close(socket_id)
    
    global PORT
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        valid = False
        while (not valid) and PORT <= 8200:
            try:
                sock.bind((HOST, PORT))
                valid = True
            except OSError:
                PORT += 1
            else:
                print(f"{G}draw_and_guess.py: using PORT {PORT}{E}")
        if not valid:
            close()
            raise Exception("invalid port range, socket creation failed")
        sock.listen(5)

        context = ssl.SSLContext(ssl._ssl.PROTOCOL_TLS_SERVER)
        context.load_cert_chain('./data/cert_key.pem')
        with context.wrap_socket(sock, server_side=True) as ssock:
            while running:
                connected_sockets["active"] = ssock
                c, addr = ssock.accept()
                print(f"{' '*8}{G}draw_and_guess.py:",
                        f"new connection at {addr}{E}")
                # print(f"{' '*8}{G}draw_and_guess.py: type(c): {c}{E}")
                # c.settimeout(60)
                threading.Thread(target=handle_socket, args=(c, addr)).start()

    close()



def initialize(wsgi_application_handler):
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

