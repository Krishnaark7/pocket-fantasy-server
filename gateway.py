# =============================================================================
#  Pocket Fantasy - Authentic Protobuf TCP Gateway Server (Port 9911)
#  Implements authentic ClientGate & ClientLogin binary Protobuf protocols
#  connecting directly with the original untouched English APK (Pokemon EN 1.3.0)
# =============================================================================

import socket
import threading
import struct
import os
import sys
import time
import sqlite3
import random
from google.protobuf import descriptor_pb2, descriptor_pool, message_factory

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DESC_DIR = os.path.join(BASE_DIR, 'descriptors')
DATA_DIR = os.path.join(BASE_DIR, 'data')
SERVER_DB_PATH = os.path.join(DATA_DIR, 'server.db')
LOG_PATH = os.path.join(BASE_DIR, 'gateway.log')

def log(msg):
    ts = time.strftime('%Y-%m-%d %H:%M:%S')
    line = f"[{ts}] {msg}\n"
    try:
        with open(LOG_PATH, 'a', encoding='utf-8') as f:
            f.write(line)
    except Exception:
        pass
    print(line, end='')

# Initialize Protobuf Pool from extracted authentic descriptors
pool = descriptor_pool.DescriptorPool()

with open(os.path.join(DESC_DIR, 'Packet.desc'), 'rb') as f:
    fd_packet = descriptor_pb2.FileDescriptorProto()
    fd_packet.ParseFromString(f.read())
pool.Add(fd_packet)

with open(os.path.join(DESC_DIR, 'ClientLogin.desc'), 'rb') as f:
    fd_login = descriptor_pb2.FileDescriptorProto()
    fd_login.ParseFromString(f.read())
pool.Add(fd_login)

PacketClass = message_factory.GetMessageClass(pool.FindMessageTypeByName('PB.Packet'))
LoginRequestClass = message_factory.GetMessageClass(pool.FindMessageTypeByName('ClientLogin.LoginRequest'))
LoginResponseClass = message_factory.GetMessageClass(pool.FindMessageTypeByName('ClientLogin.LoginResponse'))
ServerInfoClass = message_factory.GetMessageClass(pool.FindMessageTypeByName('ClientLogin.ServerInfo'))
LoginServerRequestClass = message_factory.GetMessageClass(pool.FindMessageTypeByName('ClientLogin.LoginServerRequest'))
LoginServerResponseClass = message_factory.GetMessageClass(pool.FindMessageTypeByName('ClientLogin.LoginServerResponse'))

def encode_varint(n):
    buf = bytearray()
    while True:
        b = n & 0x7f
        n >>= 7
        if n:
            buf.append(b | 0x80)
        else:
            buf.append(b)
            break
    return bytes(buf)

def encode_field(tag, wire_type, val):
    header = encode_varint((tag << 3) | wire_type)
    if wire_type == 0:
        return header + encode_varint(val)
    elif wire_type == 2:
        if isinstance(val, str):
            val = val.encode('utf-8')
        return header + encode_varint(len(val)) + val
    elif wire_type == 5:
        return header + struct.pack('<I', val)
    return b''

def build_role_info(uuid, nick, level=50, exp=1000, head_id=1, party_ids=[1, 4, 7]):
    data = bytearray()
    data += encode_field(1, 2, uuid)
    data += encode_field(2, 2, nick)
    data += encode_field(4, 0, level)
    data += encode_field(5, 0, exp)
    data += encode_field(6, 0, head_id)
    data += encode_field(7, 0, 1)
    data += encode_field(8, 0, int(time.time()))
    data += encode_field(11, 0, 10)
    for pid in party_ids:
        data += encode_field(13, 0, pid)
    return bytes(data)

def build_pm_user_basic_info(uuid, nick, stamina=120, money=500000, diamond=5000, level=50, party_ids=[1, 4, 7]):
    data = bytearray()
    data += encode_field(1, 2, uuid)
    data += encode_field(2, 0, stamina)
    data += encode_field(3, 0, money)
    data += encode_field(4, 0, diamond)
    role_bytes = build_role_info(uuid, nick, level=level, party_ids=party_ids)
    data += encode_field(5, 2, role_bytes)
    data += encode_field(6, 2, "Kanto Global 1")
    data += encode_field(18, 0, 10)
    return bytes(data)

def build_login2gameserver_response(uuid, nick, stamina=120, money=500000, diamond=5000, level=50, party_ids=[1, 4, 7]):
    data = bytearray()
    data += encode_field(1, 0, 0)
    basic_info = build_pm_user_basic_info(uuid, nick, stamina=stamina, money=money, diamond=diamond, level=level, party_ids=party_ids)
    data += encode_field(2, 2, basic_info)
    return bytes(data)

def send_tcp_packet(sock, cmd, serialized=b''):
    pkt = PacketClass()
    pkt.command = cmd
    pkt.serialized = serialized
    data = pkt.SerializeToString()
    header = struct.pack('<I', len(data))
    sock.sendall(header + data)

def recv_tcp_packet(sock):
    try:
        hdr = sock.recv(4)
        if not hdr or len(hdr) < 4:
            return None
        sz = struct.unpack('<I', hdr)[0]
        if sz > 1000000:
            sz = struct.unpack('>I', hdr)[0]
        if sz == 0 or sz > 5000000:
            return None
        buf = bytearray()
        while len(buf) < sz:
            chunk = sock.recv(sz - len(buf))
            if not chunk:
                break
            buf.extend(chunk)
        if len(buf) < sz:
            return None
        pkt = PacketClass()
        pkt.ParseFromString(bytes(buf))
        return pkt
    except Exception:
        return None

def get_or_create_character(account):
    conn = sqlite3.connect(SERVER_DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    acc = c.execute("SELECT * FROM accounts WHERE LOWER(username) = LOWER(?)", (account,)).fetchone()
    if not acc:
        c.execute("INSERT INTO accounts (username, password_hash, token) VALUES (?, 'guest_hash', ?)", (account, f"tok_{account}"))
        conn.commit()

    char = c.execute("SELECT * FROM characters WHERE LOWER(username) = LOWER(?) AND server_id = 1", (account,)).fetchone()
    if not char:
        c.execute("""INSERT INTO characters (username, server_id, name, gender, avatar, title, level, exp, gold, diamonds, stamina, max_stamina, vip_level, arena_rank, combat_power)
                     VALUES (?, 1, ?, 'male', 'avatar_01.png', 'Novice Trainer', 50, 1000, 500000, 5000, 120, 120, 10, 1500, 12500)""",
                  (account, account))
        conn.commit()
        char = c.execute("SELECT * FROM characters WHERE LOWER(username) = LOWER(?) AND server_id = 1", (account,)).fetchone()

    team = c.execute("SELECT pet_id FROM team_pets WHERE LOWER(username) = LOWER(?) AND server_id = 1 ORDER BY slot ASC", (account,)).fetchall()
    party_ids = [row['pet_id'] for row in team] if team else [150, 10150, 1, 4, 7]
    conn.close()
    return char, party_ids

def handle_client_connection(sock, addr, server_ip=None):
    if not server_ip or server_ip == "0.0.0.0":
        server_ip = os.environ.get("GATEWAY_IP", "bore.pub")
    log(f"New client connection from {addr}")
    current_account = None
    try:
        while True:
            pkt = recv_tcp_packet(sock)
            if pkt is None:
                break
            cmd = pkt.command
            
            # Opcode 1: HEART_BEAT
            if cmd == 1:
                send_tcp_packet(sock, 1, b'')
                
            # Opcode 50001 / 100001: CLIENT_LOGIN_REQUEST / CL_LOGIN_REQUEST
            elif cmd in [50001, 100001]:
                req = LoginRequestClass()
                try:
                    req.ParseFromString(pkt.serialized)
                    current_account = req.account if req.account else f"trainer_{random.randint(1000, 9999)}"
                except Exception:
                    current_account = f"trainer_{random.randint(1000, 9999)}"
                    
                log(f"Opcode {cmd} (LOGIN_REQUEST): Account='{current_account}'")
                resp = LoginResponseClass()
                resp.result = 0  # enumResultSucc = 0
                s = resp.servers.add()
                s.id = 1
                s.name = "Server 1: Kanto Global"
                s.register_count = 100
                s.has_acc = True
                s.is_new = True
                resp.last_server_id = 1
                resp.account = current_account
                resp_cmd = 100002 if cmd == 100001 else 50002
                send_tcp_packet(sock, resp_cmd, resp.SerializeToString())
                log(f"Sent Opcode {resp_cmd} (LOGIN_RESPONSE) for '{current_account}'")
                
            # Opcode 10001 / 100003: LOGIN_SERVER_REQUEST / CL_SEVER_DETAIL_REQUEST
            elif cmd in [10001, 100003]:
                log(f"Opcode {cmd} (SERVER_DETAIL_REQUEST) from '{current_account}'")
                srv_resp = LoginServerResponseClass()
                srv_resp.ip = server_ip
                srv_resp.port = "9911"
                srv_resp.uuid = current_account if current_account else "trainer_001"
                srv_resp.locked_register = False
                resp_cmd = 100004 if cmd == 100003 else 10002
                send_tcp_packet(sock, resp_cmd, srv_resp.SerializeToString())
                log(f"Sent Opcode {resp_cmd} (SERVER_DETAIL_RESPONSE)")
                
            # Opcode 50011 / 200001: CLIENT_ENTER_GAME / CG_LOGIN_REQUEST
            elif cmd in [50011, 200001]:
                log(f"Opcode {cmd} (ENTER_GAME_REQUEST) for '{current_account}'")
                char, party_ids = get_or_create_character(current_account if current_account else "trainer_001")
                enter_resp = build_login2gameserver_response(
                    uuid=current_account if current_account else "trainer_001",
                    nick=char['name'],
                    stamina=char['stamina'],
                    money=char['gold'],
                    diamond=char['diamonds'],
                    level=char['level'],
                    party_ids=party_ids
                )
                resp_cmd = 200002 if cmd == 200001 else 50012
                send_tcp_packet(sock, resp_cmd, enter_resp)
                log(f"Sent Opcode {resp_cmd} (ENTER_GAME_RESPONSE) for '{char['name']}' (Lv.{char['level']})")
                
            # Opcode 50014: CLIENT_GET_TASKS_REQUEST
            elif cmd in [50014, 50015]:
                send_tcp_packet(sock, cmd + 1, b'')
                
            # Opcode 50111: CLIENT_GET_MAIL
            elif cmd in [50111, 50112]:
                send_tcp_packet(sock, cmd + 1, b'')
                
            # Opcode 300001: MONSTER_BACKPACK_REQUEST
            elif cmd == 300001:
                log(f"Opcode 300001 (MONSTER_BACKPACK_REQUEST) for '{current_account}'")
                send_tcp_packet(sock, 300002, b'')
                
            else:
                log(f"Received unhandled command: {cmd}")
                send_tcp_packet(sock, cmd + 1, b'')

    except Exception as e:
        log(f"Error handling client {addr}: {e}")
    finally:
        sock.close()
        log(f"Client {addr} disconnected cleanly.")

def run_tcp_gateway_server(host='0.0.0.0', port=9911, server_ip=None):
    if not server_ip or server_ip == "0.0.0.0":
        server_ip = os.environ.get("GATEWAY_IP", "bore.pub")
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind((host, port))
        s.listen(50)
        log(f"Listening on {host}:{port} (Announcing server IP: {server_ip})")
        while True:
            try:
                conn, addr = s.accept()
                t = threading.Thread(target=handle_client_connection, args=(conn, addr, server_ip), daemon=True)
                t.start()
            except Exception as e:
                log(f"Accept error: {e}")
                break
    except Exception as e:
        log(f"FATAL: Bind error on {host}:{port}: {e}")

if __name__ == '__main__':
    run_tcp_gateway_server()
