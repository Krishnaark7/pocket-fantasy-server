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
LAST_ACTIVE_ACCOUNT = "Rk"

def log(msg):
    ts = time.strftime('%Y-%m-%d %H:%M:%S')
    line = f"[{ts}] {msg}\n"
    try:
        with open(LOG_PATH, 'a', encoding='utf-8') as f:
            f.write(line)
    except Exception:
        pass
    print(line, end='', flush=True)

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
    if val is None:
        if wire_type == 2:
            val = b''
        elif wire_type in (0, 5, 1):
            val = 0
    header = encode_varint((tag << 3) | wire_type)
    if wire_type == 0:
        return header + encode_varint(int(val))
    elif wire_type == 2:
        if isinstance(val, str):
            val = val.encode('utf-8')
        elif not isinstance(val, (bytes, bytearray)):
            val = str(val).encode('utf-8')
        return header + encode_varint(len(val)) + val
    elif wire_type == 5:
        return header + struct.pack('<I', int(val))
    return b''

def parse_uuid(data):
    if not data:
        return None
    try:
        idx = 0
        while idx < len(data):
            tag_byte = data[idx]
            wire = tag_byte & 0x07
            field_num = tag_byte >> 3
            idx += 1
            if field_num == 1 and wire == 2:
                length = 0
                shift = 0
                while idx < len(data):
                    b = data[idx]
                    idx += 1
                    length |= (b & 0x7f) << shift
                    if not (b & 0x80):
                        break
                    shift += 7
                if idx + length <= len(data):
                    val = data[idx:idx+length].decode('utf-8', errors='ignore')
                    if val:
                        return val
                break
            elif wire == 0:
                while idx < len(data) and (data[idx] & 0x80):
                    idx += 1
                idx += 1
            elif wire == 2:
                length = 0
                shift = 0
                while idx < len(data):
                    b = data[idx]
                    idx += 1
                    length |= (b & 0x7f) << shift
                    if not (b & 0x80):
                        break
                    shift += 7
                idx += length
            elif wire == 5:
                idx += 4
            elif wire == 1:
                idx += 8
            else:
                break
    except Exception:
        pass
    return None

def build_skills_bytes(skill_ids):
    sl = bytearray()
    for s_id in skill_ids:
        s = encode_field(1, 0, s_id) + encode_field(6, 0, 30)
        sl += encode_field(1, 2, s)
    return bytes(sl)

def build_monster_bytes(uuid, pet_id, nick, level=100, breakthrough=13):
    if not uuid:
        uuid = f"pet_{pet_id}_{random.randint(100, 999)}"
    if not nick:
        nick = "Mewtwo (Shiny)" if pet_id == 10150 else "Mewtwo"
    m = bytearray()
    m += encode_field(2, 2, uuid)
    m += encode_field(3, 0, 9999)   # hp
    m += encode_field(4, 0, 9999)   # max_hp
    m += encode_field(5, 0, 100000) # exp
    m += encode_field(9, 2, nick)
    m += encode_field(10, 0, level)
    m += encode_field(16, 0, 2500)  # att
    m += encode_field(17, 0, 2000)  # def
    m += encode_field(18, 0, 3000)  # int
    m += encode_field(19, 0, 2000)  # res
    m += encode_field(20, 0, 2800)  # spd
    if pet_id == 150:
        skills = [93, 50, 94, 219] # Confusion, Disable, Psychic, Safeguard
    elif pet_id == 10150:
        skills = [231, 242, 182, 284]
    else:
        skills = [1, 2, 3, 4]
    m += encode_field(21, 2, build_skills_bytes(skills))
    m += encode_field(31, 0, breakthrough)
    m += encode_field(32, 0, 10)    # train_lev
    m += encode_field(33, 0, pet_id)
    m += encode_field(64, 0, 1)     # is_inbag = true
    return bytes(m)

def build_monster_list_bytes(pets):
    ml = bytearray()
    for idx, p in enumerate(pets):
        p_uid = p.get('pet_uid') or f"pet_{p.get('pet_id', 150)}_{idx+1}"
        p_id = p.get('pet_id') or 150
        p_nick = p.get('name') or ('Mewtwo (Shiny)' if p_id == 10150 else 'Mewtwo')
        p_lev = p.get('level') or 100
        p_bt = p.get('breakthrough_stage') or 13
        m_bytes = build_monster_bytes(p_uid, p_id, p_nick, p_lev, p_bt)
        ml += encode_field(1, 2, m_bytes)
    return bytes(ml)

def build_role_info(uuid, nick, level=100, exp=1000, head_id=1, party_ids=[150, 10150]):
    data = bytearray()
    data += encode_field(1, 2, uuid)
    data += encode_field(2, 2, nick)
    data += encode_field(3, 0, 1)   # gender = male
    data += encode_field(4, 0, level)
    data += encode_field(5, 0, exp)
    data += encode_field(6, 0, head_id) # 1 = player01 Ash/Red avatar
    data += encode_field(7, 0, 1)   # trainer_id
    data += encode_field(8, 0, int(time.time()))
    data += encode_field(11, 0, 15) # VIP level 15
    for pid in party_ids:
        data += encode_field(13, 0, pid)
        data += encode_field(14, 0, pid)
    data += encode_field(23, 0, 6)  # battle_monster_size = 6
    return bytes(data)

def build_pm_user_basic_info(uuid, nick, stamina=120, money=10000000, diamond=100000, level=100, party_ids=[150, 10150]):
    data = bytearray()
    data += encode_field(1, 2, uuid)
    data += encode_field(2, 0, stamina)
    data += encode_field(3, 0, money)
    data += encode_field(4, 0, diamond)
    role_bytes = build_role_info(uuid, nick, level=level, party_ids=party_ids)
    data += encode_field(5, 2, role_bytes)
    data += encode_field(6, 2, "Server 1: Kanto Global")
    data += encode_field(16, 2, "guide_complete") # guide = "guide_complete"
    data += encode_field(17, 0, 4)                # first_select_pet = 4 (Charmander chosen)
    data += encode_field(18, 0, 15)               # vip_lev
    return bytes(data)

def build_login2gameserver_response(uuid, nick, stamina=120, money=10000000, diamond=100000, level=100, pets=[], party_ids=[150, 10150]):
    data = bytearray()
    data += encode_field(1, 0, 0) # result = 0 (enumResultSucc)
    basic_info = build_pm_user_basic_info(uuid, nick, stamina=stamina, money=money, diamond=diamond, level=level, party_ids=party_ids)
    data += encode_field(2, 2, basic_info)
    if pets:
        monsters_bytes = build_monster_list_bytes(pets)
        data += encode_field(3, 2, monsters_bytes)
    # Note: tutorial (tag 4) and tutorial_drawcard (tag 6) are omitted completely to prevent engine null pointer crash
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
                     VALUES (?, 1, ?, 'male', 'avatar_01.png', 'Grandmaster Trainer', 100, 1000, 10000000, 100000, 120, 120, 15, 1, 99999)""",
                  (account, account))
        conn.commit()
        # Seed Mewtwo and Shiny Mewtwo for the new account
        c.execute("""INSERT INTO team_pets (pet_uid, username, server_id, slot, pet_id, name, level, breakthrough_stage)
                     VALUES (?, ?, 1, 1, 150, 'Mewtwo', 100, 13)""", (f"pet_{account}_01", account))
        c.execute("""INSERT INTO team_pets (pet_uid, username, server_id, slot, pet_id, name, level, breakthrough_stage)
                     VALUES (?, ?, 1, 2, 10150, 'Mewtwo (Shiny)', 100, 13)""", (f"pet_{account}_02", account))
        conn.commit()
        char = c.execute("SELECT * FROM characters WHERE LOWER(username) = LOWER(?) AND server_id = 1", (account,)).fetchone()

    team = c.execute("SELECT pet_uid, pet_id, name, level, breakthrough_stage FROM team_pets WHERE LOWER(username) = LOWER(?) AND server_id = 1 ORDER BY slot ASC", (account,)).fetchall()
    pets = [dict(row) for row in team] if team else [
        {'pet_uid': f"pet_{account}_01", 'pet_id': 150, 'name': 'Mewtwo', 'level': 100, 'breakthrough_stage': 13},
        {'pet_uid': f"pet_{account}_02", 'pet_id': 10150, 'name': 'Mewtwo (Shiny)', 'level': 100, 'breakthrough_stage': 13}
    ]
    party_ids = [p['pet_id'] for p in pets]
    conn.close()
    return char, pets, party_ids

def handle_client_connection(sock, addr, server_ip=None):
    global LAST_ACTIVE_ACCOUNT
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
                LAST_ACTIVE_ACCOUNT = current_account
                    
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
                if not current_account:
                    current_account = LAST_ACTIVE_ACCOUNT
                log(f"Opcode {cmd} (SERVER_DETAIL_REQUEST) from '{current_account}'")
                srv_resp = LoginServerResponseClass()
                srv_resp.ip = server_ip
                srv_resp.port = "9911"
                srv_resp.uuid = current_account if current_account else "Rk"
                srv_resp.locked_register = False
                resp_cmd = 100004 if cmd == 100003 else 10002
                send_tcp_packet(sock, resp_cmd, srv_resp.SerializeToString())
                log(f"Sent Opcode {resp_cmd} (SERVER_DETAIL_RESPONSE) -> {server_ip}:9911, uuid='{srv_resp.uuid}'")
                
            # Opcode 50011 / 200001: CLIENT_ENTER_GAME / CG_LOGIN_REQUEST
            elif cmd in [50011, 200001]:
                req_uuid = parse_uuid(pkt.serialized)
                if req_uuid:
                    current_account = req_uuid
                    LAST_ACTIVE_ACCOUNT = req_uuid
                elif not current_account:
                    current_account = LAST_ACTIVE_ACCOUNT
                log(f"Opcode {cmd} (ENTER_GAME_REQUEST) for '{current_account}'")
                char, pets, party_ids = get_or_create_character(current_account if current_account else "Rk")
                enter_resp = build_login2gameserver_response(
                    uuid=char['username'],
                    nick=char['name'],
                    stamina=char['stamina'],
                    money=char['gold'],
                    diamond=char['diamonds'],
                    level=char['level'],
                    pets=pets,
                    party_ids=party_ids
                )
                resp_cmd = 200002 if cmd == 200001 else 50012
                send_tcp_packet(sock, resp_cmd, enter_resp)
                log(f"Sent Opcode {resp_cmd} (ENTER_GAME_RESPONSE) for '{char['name']}' (Lv.{char['level']}) with {len(pets)} pets")
                
            # Opcode 430700: ACTIVITY_OPEN_STATUS_REQUEST
            elif cmd == 430700:
                log(f"Opcode 430700 (ACTIVITY_OPEN_STATUS_REQUEST)")
                send_tcp_packet(sock, 430701, b'')
                log(f"Sent Opcode 430701 (ACTIVITY_OPEN_STATUS_RESPONSE) -> safe empty")

            # Opcode 430100: RED_POINTS_STATUES_REQUEST
            elif cmd == 430100:
                log(f"Opcode 430100 (RED_POINTS_STATUES_REQUEST)")
                send_tcp_packet(sock, 430101, b'')
                log(f"Sent Opcode 430101 (RED_POINTS_STATUES_RESPONSE) -> safe empty")

            # Opcode 310001: OPERA_DATA_REQUEST (Stage / chapter progress)
            elif cmd == 310001:
                log(f"Opcode 310001 (OPERA_DATA_REQUEST)")
                rec_bytes = bytearray()
                for stage_idx in range(1, 10):
                    rec = encode_field(1, 0, 1) + encode_field(2, 0, stage_idx) + encode_field(3, 0, 3)
                    rec_bytes += encode_field(1, 2, rec)
                send_tcp_packet(sock, 310002, bytes(rec_bytes))
                log(f"Sent Opcode 310002 (OPERA_DATA_RESPONSE)")

            # Opcode 420001: DRAW_INFO_REQUEST (Gacha info)
            elif cmd == 420001:
                log(f"Opcode 420001 (DRAW_INFO_REQUEST)")
                send_tcp_packet(sock, 420002, b'')
                log(f"Sent Opcode 420002 (DRAW_INFO_RESPONSE)")

            # Opcode 300001: MONSTER_BACKPACK_REQUEST
            elif cmd == 300001:
                log(f"Opcode 300001 (MONSTER_BACKPACK_REQUEST)")
                target_acc = current_account if current_account else LAST_ACTIVE_ACCOUNT
                char, pets, party_ids = get_or_create_character(target_acc if target_acc else "Rk")
                monsters_bytes = build_monster_list_bytes(pets)
                mb_resp = bytearray()
                mb_resp += encode_field(1, 2, monsters_bytes)
                mb_resp += encode_field(2, 0, 100)
                mb_resp += encode_field(3, 0, 1)
                send_tcp_packet(sock, 300002, bytes(mb_resp))
                log(f"Sent Opcode 300002 (MONSTER_BACKPACK_RESPONSE)")

            # Opcode 430200: GROWN_UP_INFO_REQUEST
            elif cmd == 430200:
                log(f"Opcode 430200 (GROWN_UP_INFO_REQUEST)")
                # GrownUpInfoResponse: required bool has_bought = 1
                gu_data = encode_field(1, 0, 1)
                send_tcp_packet(sock, 430201, gu_data)
                log(f"Sent Opcode 430201 (GROWN_UP_INFO_RESPONSE)")

            # Opcode 430300: DOUBLE_DROP_INFO_REQUEST
            elif cmd == 430300:
                log(f"Opcode 430300 (DOUBLE_DROP_INFO_REQUEST)")
                # DoubleDropResponse: required bool open = 1
                dd_data = encode_field(1, 0, 0)
                send_tcp_packet(sock, 430301, dd_data)
                log(f"Sent Opcode 430301 (DOUBLE_DROP_INFO_RESPONSE)")

            # Opcode 90000: BACKPACK_REQUEST
            elif cmd == 90000:
                log(f"Opcode 90000 (BACKPACK_REQUEST)")
                send_tcp_packet(sock, 90001, b'')
                log(f"Sent Opcode 90001 (BACKPACK_RESPONSE)")

            # Opcode 50014: CLIENT_GET_TASKS_REQUEST
            elif cmd in [50014, 50015]:
                send_tcp_packet(sock, 50015, b'')
                
            # Opcode 50111: CLIENT_GET_MAIL
            elif cmd in [50111, 50112]:
                send_tcp_packet(sock, 50112, b'')
                
            else:
                log(f"Received command: {cmd} (acknowledged safely without sending invalid data)")

    except Exception as e:
        log(f"Error handling client {addr}: {e}")
    finally:
        sock.close()
        log(f"Client {addr} disconnected cleanly.")

def run_tcp_gateway_server(host='0.0.0.0', port=9911, server_ip=None):
    if not server_ip or server_ip == "0.0.0.0":
        server_ip = os.environ.get("GATEWAY_IP", "bore.pub")
    log(f"Listening on {host}:{port} (Announcing server IP: {server_ip})")
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((host, port))
    server.listen(10)
    try:
        while True:
            conn, addr = server.accept()
            t = threading.Thread(target=handle_client_connection, args=(conn, addr, server_ip), daemon=True)
            t.start()
    except Exception as e:
        log(f"TCP Gateway server fatal error: {e}")
    finally:
        server.close()

if __name__ == '__main__':
    run_tcp_gateway_server()
