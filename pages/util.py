#!/bin/python

import base64
import hashlib
import struct

def content_type(path, default="text/plain"):
    ctype = default
    if isinstance(path, str):
        for ext, t in content_type.EXT_DICT.items():
            if path.endswith(ext):
                ctype = t
                break
    if ctype.startswith("text/"):
        ctype += "; charset=utf-8"
    return ctype

content_type.EXT_DICT = {
    ".htm": "text/html",
    ".html": "text/html",
    ".js": "application/javascript",
    ".css": "text/css",
    ".png": "image/png"
}



# return str
def decode_socket_data(data):
    # https://tools.ietf.org/html/rfc6455#page-28
    # https://gist.github.com/rich20bb/4190781

    # https://developer.mozilla.org/en-US/docs/
    # Web/API/WebSockets_API/Writing_WebSocket_servers
    
    if data[0] == 0x81:
        pass # content is text
    else:
        print(f"{C_R}util.py:",
                f"data[0] == {data[0]} != 0x81, data is not text{C_E}")
    payload_len = data[1] & 127
    
    index_first_mask = 2
    if payload_len == 126:
        index_first_mask = 4
        payload_len = (data[2] << 8) + data[3]
    elif payload_len == 127:
        index_first_mask = 10

    masks = list(data[index_first_mask:index_first_mask+4])
    index_first_data_byte = index_first_mask + 4

    decoded_chars = []
    i = index_first_data_byte
    j = 0
    
    last_index = payload_len + index_first_data_byte
    # last_index = min(last_index, len(data))
    while i < last_index:
        decoded_chars.append(chr(data[i] ^ masks[j]))
        i += 1
        j = (j+1) % 4
    
    return "".join(decoded_chars), data[last_index:]

def handle_websocket_message(socket, handler, *args):
    """https://tools.ietf.org/html/rfc6455#page-28
    """
    return_code = True
    while return_code:
        data = socket.recv(2)
        FIN_RSV123 = 0xf0 & data[0]
        OPCODE = 0x0f & data[0]
        MASKED = data[1] & 0x80
        LENGTH = data[1] & 0x7f
        
        if FIN_RSV123 != 0x80:
            print("util.py: get_next_socket_message():",
                    f"unexpected frame starting bits({bin(FIN_RSV123)})")
        if not MASKED:
            print(f"{' '*8}{C_R}util.py: get_next_socket_message():",
                    f"client-to-server message should be masked{C_E}")

        if LENGTH == 126:
            data = socket.recv(2)
            LENGTH = struct.unpack("!H", data)
        elif LENGTH == 127:
            data = socket.recv(8)
            LENGTH = struct.unpack("!Q", data)


        if OPCODE == 0: pass # continuation frame
        elif OPCODE == 1: pass # text frame
        elif OPCODE == 2: pass # binary frame
        elif OPCODE == 8: # connection close
            pass
        elif OPCODE == 9: # ping
            if LENGTH >= 126:
                print(f"{' '*8}{C_R}util.py: get_next_socekt_message():",
                        f"invalid ping frame payload length{C_E}")
            data = socket.recv()
            pong = bytearray([0x8a, MASKED+LENGTH, data])
            socket.sendall(pong)

            print(f"{' ' *8}{C_R}util.py: ping received,",
                    f"payload: {pong.decode('utf-8')}{C_E}")
            continue
        elif OPCODE == 10: # pong
            pass
        else: # reserved further control frames
            pass


        masks = socket.recv(4)
        i = 0
        data = bytearray()
        for b in socket.recv(LENGTH):
            data.append(b ^ masks[i])
            i = (i + 1) % 4

        print(f"{' '*8}{C_R}util.py: received data, decoded:\n" +
                f"{' '*8}{data.decode('utf-8')}{C_E}")
        
        
        # bytes.fromhex(
        return_code = handler(data, *args)



# return bytes
def encode_socket_data(message):
    TEXT = 0x01
    
    return_value = b""
    payload = None

    b1 = 0x80

    if type(message) == str:
        b1 |= TEXT
        payload = message.encode("utf-8")
    elif type(message) == bytes:
        b1 |= TEXT
        payload = message
    
    return_value += bytes([b1])

    b2 = 0
    length = len(payload)
    if length < 126:
        b2 |= length
        return_value += bytes([b2])
    elif length < (2 ** 16) -1:
        b2 |= 126
        return_value += bytes([b2])
        return_value += struct.pack(">H", length)
    else:
        b2 |= 127
        return_value += bytes([b2])
        return_value += struct.pack(">Q", length)
    
    # print("\n"*5 + "#"*20 + " payload " + "#"*20)
    # print(payload.decode("utf-8"))
    # print("#"*20 + " return value " + "#"*20)
    # print(repr(return_value))
    # print("#" * 50 + "\n"*2)
    # return_value += payload
    return return_value + payload




# data in bytes, return bytes
def resolve_socket_handshake(data):
    sec_websocket_key = None
    # print("="*80)
    for line in data.split(b"\r\n"):
        # print(line.decode("utf-8"))
        if line.startswith(b"Sec-WebSocket-Key:"):
            sec_websocket_key = line[19:].strip()
            break
    # print("="*80)

    h = hashlib.sha1()
    h.update(sec_websocket_key)
    h.update(resolve_socket_handshake.magic.encode("utf-8"))
    h = h.digest()
    sec_websocket_accept = base64.b64encode(h).decode("utf-8")
    # print("Sec-WebSocket-Key:", sec_websocket_key.decode("utf-8"))
    # print("Sec-WebSocket-Accept:", sec_websocket_accept)

    return resolve_socket_handshake.handshake.format(
            sec_websocket_accept).encode("utf-8")


resolve_socket_handshake.magic = "258EAFA5-E914-47DA-95CA-C5AB0DC85B11"

resolve_socket_handshake.handshake = (
        "HTTP/1.1 101 Switching Protocols\r\n"
        "Upgrade: WebSocket\r\n"
        "Connection: Upgrade\r\n"
        "Sec-WebSocket-Accept: {}\r\n"
        "Server: TestTest\r\n"
        "Access-Control-Allow-Oripin: *\r\n"
        "Access-Control-Allow-Credentials: true\r\n"
        "\r\n"
)




def C(foreground, background=None):
    """
https://stackoverflow.com/questions/287871/print-in-terminal-with-colors

a;bb;ccm

open tag \033 == \x1b

a is probably text style
bb foreground, cc background

1; is brighter
4; is underlined

    """
    return "\33[1;34;40m" + "HI" + "\33[0m"

C_R = C_RED    = "\33[1;31;40m"
C_G = C_GREEN  = "\33[1;32;40m"
C_Y = C_YELLOW = "\33[1;33;40m"
C_B = C_BLUE   = "\33[1;34;40m"
C_P = C_PURPLE = "\33[1;35;40m"
C_E = C_END    = "\33[0m"