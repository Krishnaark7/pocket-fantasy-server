# =============================================================================
#  Pocket Fantasy - 24/7 Dedicated Online Multiplayer Game Server (Python 3)
#  Zero-dependency Python implementation backed by authentic SQLite databases:
#    - Bag.db: 70 tables (t_pet, t_skill, t_stage, t_drop, t_box, pet_break,
#              pet_train, pet_evolution, t_integral_robot, t_store_goods, etc.)
#    - server.db: Player accounts, characters, team pets, box pets, bag items,
#                 stage progress, chapter star chests, chat, friends, and PVP.
#
#  Authentic ClientGate & ClientLogin protocols implemented:
#    - Account registration, login, auto-registration, multi-server support
#    - Stamina auto-regeneration (1 stamina per 300s up to cap)
#    - Pet Cultivation: Candy feed, Breakthrough (TuPo), Training (TeXun),
#                       Evolution (JinHua), IV washing, Vitamin EVs
#    - Adventure Stages: Stamina deduction, 3-star HP check, t_drop rolls,
#                        Sweep ticket instant clears, Chapter star chests (t_box)
#    - Gacha Machine: Gold & Diamond pools from t_toy_reward & t_pet with 10x pity
#    - Stores: t_store_goods catalog & currency purchases
#    - Arena & Ladder: 2,000 authentic robots from t_integral_robot + real players
#    - Real-Time Multiplayer PVP: 4-digit room matchmaking & turn-by-turn sync
#    - Multi-channel Chat & Friends list
# =============================================================================

import http.server
import socketserver
import json
import os
import sys
import time
import hashlib
import secrets
import base64
import sqlite3
import random
from urllib.parse import urlparse, parse_qs

PORT = int(os.environ.get('PORT', 8088))
if len(sys.argv) > 1 and sys.argv[1].isdigit():
    PORT = int(sys.argv[1])
elif '--port' in sys.argv:
    idx = sys.argv.index('--port')
    if idx + 1 < len(sys.argv) and sys.argv[idx + 1].isdigit():
        PORT = int(sys.argv[idx + 1])
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, 'data')
os.makedirs(DATA_DIR, exist_ok=True)

BAG_DB_PATH = os.path.join(DATA_DIR, 'Bag.db')
SERVER_DB_PATH = os.path.join(DATA_DIR, 'server.db')

def get_server_db():
    conn = sqlite3.connect(SERVER_DB_PATH, timeout=10.0)
    conn.row_factory = sqlite3.Row
    return conn

def get_bag_db():
    conn = sqlite3.connect(BAG_DB_PATH, timeout=10.0)
    conn.row_factory = sqlite3.Row
    return conn

# Ensure server.db tables exist
def init_server_db():
    conn = get_server_db()
    cur = conn.cursor()
    cur.executescript("""
    CREATE TABLE IF NOT EXISTS accounts (
        username TEXT PRIMARY KEY,
        password_hash TEXT NOT NULL,
        token TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        last_login TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS characters (
        username TEXT NOT NULL,
        server_id INTEGER NOT NULL DEFAULT 1,
        name TEXT NOT NULL,
        gender INTEGER DEFAULT 1,
        avatar TEXT DEFAULT 'player/touxiang1.png',
        title TEXT DEFAULT 'Novice Trainer',
        level INTEGER DEFAULT 1,
        exp INTEGER DEFAULT 0,
        gold INTEGER DEFAULT 5000,
        diamonds INTEGER DEFAULT 200,
        stamina INTEGER DEFAULT 120,
        max_stamina INTEGER DEFAULT 120,
        last_stamina_update INTEGER DEFAULT 0,
        vip_level INTEGER DEFAULT 0,
        arena_rank INTEGER DEFAULT 1000,
        arena_attempts INTEGER DEFAULT 5,
        stage_id INTEGER DEFAULT 1,
        combat_power INTEGER DEFAULT 450,
        win_count INTEGER DEFAULT 0,
        loss_count INTEGER DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        PRIMARY KEY (username, server_id)
    );

    CREATE TABLE IF NOT EXISTS team_pets (
        pet_uid TEXT PRIMARY KEY,
        username TEXT NOT NULL,
        server_id INTEGER NOT NULL DEFAULT 1,
        slot INTEGER NOT NULL,
        pet_id INTEGER NOT NULL,
        name TEXT NOT NULL,
        level INTEGER DEFAULT 1,
        exp INTEGER DEFAULT 0,
        cur_hp INTEGER DEFAULT 100,
        max_hp INTEGER DEFAULT 100,
        atk INTEGER DEFAULT 50,
        def INTEGER DEFAULT 50,
        spatk INTEGER DEFAULT 50,
        spdef INTEGER DEFAULT 50,
        speed INTEGER DEFAULT 50,
        star INTEGER DEFAULT 1,
        breakthrough_stage INTEGER DEFAULT 0,
        iv_hp INTEGER DEFAULT 15,
        iv_atk INTEGER DEFAULT 15,
        iv_def INTEGER DEFAULT 15,
        iv_spatk INTEGER DEFAULT 15,
        iv_spdef INTEGER DEFAULT 15,
        iv_speed INTEGER DEFAULT 15,
        ev_hp INTEGER DEFAULT 0,
        ev_atk INTEGER DEFAULT 0,
        ev_def INTEGER DEFAULT 0,
        ev_spatk INTEGER DEFAULT 0,
        ev_spdef INTEGER DEFAULT 0,
        ev_speed INTEGER DEFAULT 0,
        nature TEXT DEFAULT 'Hardy',
        skill_0 INTEGER DEFAULT 0,
        skill_1 INTEGER DEFAULT 0,
        skill_2 INTEGER DEFAULT 0,
        skill_3 INTEGER DEFAULT 0,
        skill_lv_0 INTEGER DEFAULT 1,
        skill_lv_1 INTEGER DEFAULT 1,
        skill_lv_2 INTEGER DEFAULT 1,
        skill_lv_3 INTEGER DEFAULT 1,
        held_item_id INTEGER DEFAULT 0,
        berry_item_id INTEGER DEFAULT 0
    );

    CREATE TABLE IF NOT EXISTS box_pets (
        pet_uid TEXT PRIMARY KEY,
        username TEXT NOT NULL,
        server_id INTEGER NOT NULL DEFAULT 1,
        box_page INTEGER DEFAULT 0,
        box_slot INTEGER DEFAULT 0,
        pet_id INTEGER NOT NULL,
        name TEXT NOT NULL,
        level INTEGER DEFAULT 1,
        exp INTEGER DEFAULT 0,
        cur_hp INTEGER DEFAULT 100,
        max_hp INTEGER DEFAULT 100,
        atk INTEGER DEFAULT 50,
        def INTEGER DEFAULT 50,
        spatk INTEGER DEFAULT 50,
        spdef INTEGER DEFAULT 50,
        speed INTEGER DEFAULT 50,
        star INTEGER DEFAULT 1,
        breakthrough_stage INTEGER DEFAULT 0,
        iv_hp INTEGER DEFAULT 15,
        iv_atk INTEGER DEFAULT 15,
        iv_def INTEGER DEFAULT 15,
        iv_spatk INTEGER DEFAULT 15,
        iv_spdef INTEGER DEFAULT 15,
        iv_speed INTEGER DEFAULT 15,
        ev_hp INTEGER DEFAULT 0,
        ev_atk INTEGER DEFAULT 0,
        ev_def INTEGER DEFAULT 0,
        ev_spatk INTEGER DEFAULT 0,
        ev_spdef INTEGER DEFAULT 0,
        ev_speed INTEGER DEFAULT 0,
        nature TEXT DEFAULT 'Hardy',
        skill_0 INTEGER DEFAULT 0,
        skill_1 INTEGER DEFAULT 0,
        skill_2 INTEGER DEFAULT 0,
        skill_3 INTEGER DEFAULT 0,
        skill_lv_0 INTEGER DEFAULT 1,
        skill_lv_1 INTEGER DEFAULT 1,
        skill_lv_2 INTEGER DEFAULT 1,
        skill_lv_3 INTEGER DEFAULT 1,
        held_item_id INTEGER DEFAULT 0,
        berry_item_id INTEGER DEFAULT 0
    );

    CREATE TABLE IF NOT EXISTS bag_items (
        username TEXT NOT NULL,
        server_id INTEGER NOT NULL DEFAULT 1,
        item_id INTEGER NOT NULL,
        count INTEGER NOT NULL DEFAULT 1,
        PRIMARY KEY (username, server_id, item_id)
    );

    CREATE TABLE IF NOT EXISTS stage_progress (
        username TEXT NOT NULL,
        server_id INTEGER NOT NULL DEFAULT 1,
        stage_id INTEGER NOT NULL,
        stars INTEGER DEFAULT 0,
        pass_count INTEGER DEFAULT 0,
        PRIMARY KEY (username, server_id, stage_id)
    );

    CREATE TABLE IF NOT EXISTS chapter_boxes (
        username TEXT NOT NULL,
        server_id INTEGER NOT NULL DEFAULT 1,
        chapter_id INTEGER NOT NULL,
        claimed_tiers TEXT DEFAULT '',
        PRIMARY KEY (username, server_id, chapter_id)
    );

    CREATE TABLE IF NOT EXISTS friends (
        username TEXT NOT NULL,
        friend_username TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        stamina_sent_today INTEGER DEFAULT 0,
        PRIMARY KEY (username, friend_username)
    );

    CREATE TABLE IF NOT EXISTS chat_messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        channel TEXT DEFAULT 'World',
        sender_name TEXT NOT NULL,
        sender_level INTEGER DEFAULT 1,
        sender_avatar TEXT DEFAULT 'player/touxiang1.png',
        sender_vip INTEGER DEFAULT 0,
        text TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS pvp_records (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        p1_name TEXT NOT NULL,
        p2_name TEXT NOT NULL,
        winner_name TEXT NOT NULL,
        points_delta INTEGER DEFAULT 25,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)
    conn.commit()
    conn.close()

init_server_db()

# In-memory session and active matchmaking rooms
active_rooms = {}
SERVERS = [
    { 'id': 1, 'name': 'Server 1: Pallet Town', 'status': 'Hot', 'online': True, 'player_count': 142 },
    { 'id': 2, 'name': 'Server 2: Viridian City', 'status': 'Smooth', 'online': True, 'player_count': 89 },
    { 'id': 3, 'name': 'Server 3: Pewter Gym', 'status': 'Smooth', 'online': True, 'player_count': 64 },
    { 'id': 4, 'name': 'Server 4: Cerulean Coast', 'status': 'New', 'online': True, 'player_count': 35 }
]

def hash_pw(pw):
    return hashlib.sha256((pw or '').encode('utf-8')).hexdigest()

def gen_token(username):
    token_bytes = secrets.token_hex(16)
    b64_user = base64.b64encode(username.encode('utf-8')).decode('ascii')
    return f'{token_bytes}_{b64_user}'

# Calculate Pet Stats using authentic formula
def calc_pet_stats(pet_id, level, star, breakthrough, ivs, evs):
    bconn = get_bag_db()
    bcur = bconn.cursor()
    row = bcur.execute("""
        SELECT pet_hp, pet_physical_attack, pet_physical_defense, 
               pet_special_attack, pet_special_defense, pet_speed, pet_name
        FROM t_pet WHERE pet_id = ?
    """, (pet_id,)).fetchone()
    bconn.close()

    base_hp = row['pet_hp'] if row else 50
    base_atk = row['pet_physical_attack'] if row else 50
    base_def = row['pet_physical_defense'] if row else 50
    base_spatk = row['pet_special_attack'] if row else 50
    base_spdef = row['pet_special_defense'] if row else 50
    base_spd = row['pet_speed'] if row else 50
    name = row['pet_name'] if row else f'Pokemon_{pet_id}'

    # Standard formula
    # HP = floor(((2*base + iv + ev//4) * level) / 100) + level + 10
    # Stat = floor(((2*base + iv + ev//4) * level) / 100) + 5
    hp = ((2 * base_hp + ivs.get('hp', 15) + (evs.get('hp', 0) // 4)) * level) // 100 + level + 10
    atk = ((2 * base_atk + ivs.get('atk', 15) + (evs.get('atk', 0) // 4)) * level) // 100 + 5
    def_ = ((2 * base_def + ivs.get('def', 15) + (evs.get('def', 0) // 4)) * level) // 100 + 5
    spatk = ((2 * base_spatk + ivs.get('spatk', 15) + (evs.get('spatk', 0) // 4)) * level) // 100 + 5
    spdef = ((2 * base_spdef + ivs.get('spdef', 15) + (evs.get('spdef', 0) // 4)) * level) // 100 + 5
    spd = ((2 * base_spd + ivs.get('speed', 15) + (evs.get('speed', 0) // 4)) * level) // 100 + 5

    # Star boost: +5% per star
    star_mult = 1.0 + (max(1, star) - 1) * 0.05
    # Breakthrough boost: flat +15 per breakthrough stage
    bk_bonus = breakthrough * 15

    hp = int(hp * star_mult) + bk_bonus * 2
    atk = int(atk * star_mult) + bk_bonus
    def_ = int(def_ * star_mult) + bk_bonus
    spatk = int(spatk * star_mult) + bk_bonus
    spdef = int(spdef * star_mult) + bk_bonus
    spd = int(spd * star_mult) + bk_bonus

    cp = (hp // 2) + atk + def_ + spatk + spdef + spd + (star * 120) + (breakthrough * 90)

    return {
        'name': name,
        'max_hp': hp,
        'atk': atk,
        'def': def_,
        'spatk': spatk,
        'spdef': spdef,
        'speed': spd,
        'combat_power': cp
    }

# Update stamina based on elapsed time (1 stamina per 300s)
def refresh_character_stamina(char_row, conn):
    now = int(time.time())
    last_up = char_row['last_stamina_update'] or now
    stamina = char_row['stamina']
    max_stamina = char_row['max_stamina'] or 120

    if last_up <= 0:
        last_up = now

    elapsed = now - last_up
    if elapsed >= 300 and stamina < max_stamina:
        gain = elapsed // 300
        new_stamina = min(max_stamina, stamina + gain)
        new_last_up = last_up + (gain * 300)
        conn.execute("""
            UPDATE characters 
            SET stamina = ?, last_stamina_update = ?
            WHERE username = ? AND server_id = ?
        """, (new_stamina, new_last_up, char_row['username'], char_row['server_id']))
        conn.commit()
        return new_stamina
    return stamina


class GameServerHandler(http.server.BaseHTTPRequestHandler):
    def _send_json(self, status, data):
        self.send_response(status)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        self.end_headers()
        self.wfile.write(json.dumps(data, ensure_ascii=False).encode('utf-8'))

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        self.end_headers()

    def _read_body(self):
        length = int(self.headers.get('Content-Length', 0))
        if length <= 0:
            return {}
        raw = self.rfile.read(length).decode('utf-8', errors='ignore')
        try:
            return json.loads(raw)
        except Exception:
            return {}

    # =========================================================================
    # GET Requests
    # =========================================================================
    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path
        qs = parse_qs(parsed.query)

        # Health & Server Status
        if path in ['/', '/api/status']:
            sconn = get_server_db()
            tot_players = sconn.execute("SELECT count(*) as cnt FROM accounts").fetchone()['cnt']
            tot_chars = sconn.execute("SELECT count(*) as cnt FROM characters").fetchone()['cnt']
            sconn.close()
            return self._send_json(200, {
                'status': 'online',
                'service': 'Pocket Fantasy Dedicated Server',
                'version': '1.0.0',
                'registered_accounts': tot_players,
                'active_characters': tot_chars,
                'active_pvp_rooms': len(active_rooms),
                'timestamp': int(time.time())
            })

        # Server Zone Listing
        if path == '/api/servers':
            return self._send_json(200, { 'success': True, 'servers': SERVERS })

        # Load Full Character Profile & Save
        if path == '/api/player/load':
            username = qs.get('username', [''])[0].strip()
            server_id = int(qs.get('server_id', [1])[0])
            if not username:
                return self._send_json(400, { 'success': False, 'error': 'Missing username' })

            sconn = get_server_db()
            char = sconn.execute("SELECT * FROM characters WHERE username = ? AND server_id = ?", (username, server_id)).fetchone()
            if not char:
                sconn.close()
                return self._send_json(404, { 'success': False, 'error': 'Character not found' })

            stamina = refresh_character_stamina(char, sconn)
            team_rows = sconn.execute("SELECT * FROM team_pets WHERE username = ? AND server_id = ? ORDER BY slot ASC", (username, server_id)).fetchall()
            box_rows = sconn.execute("SELECT * FROM box_pets WHERE username = ? AND server_id = ?", (username, server_id)).fetchall()
            bag_rows = sconn.execute("SELECT item_id, count FROM bag_items WHERE username = ? AND server_id = ?", (username, server_id)).fetchall()
            stage_rows = sconn.execute("SELECT stage_id, stars, pass_count FROM stage_progress WHERE username = ? AND server_id = ?", (username, server_id)).fetchall()

            team = [dict(r) for r in team_rows]
            box = [dict(r) for r in box_rows]
            bag = { r['item_id']: r['count'] for r in bag_rows }
            stages = { r['stage_id']: { 'stars': r['stars'], 'pass_count': r['pass_count'] } for r in stage_rows }

            profile = dict(char)
            profile['stamina'] = stamina
            sconn.close()

            return self._send_json(200, {
                'success': True,
                'profile': profile,
                'team': team,
                'box': box,
                'bag': bag,
                'stages': stages
            })

        # Chat History
        if path == '/api/chat/messages':
            limit = int(qs.get('limit', [50])[0])
            channel = qs.get('channel', ['World'])[0]
            sconn = get_server_db()
            if channel and channel != 'All':
                rows = sconn.execute("SELECT * FROM chat_messages WHERE channel = ? ORDER BY id DESC LIMIT ?", (channel, limit)).fetchall()
            else:
                rows = sconn.execute("SELECT * FROM chat_messages ORDER BY id DESC LIMIT ?", (limit,)).fetchall()
            sconn.close()

            msgs = []
            for r in reversed(rows):
                msgs.append({
                    'id': r['id'],
                    'channel': r['channel'],
                    'sender': r['sender_name'],
                    'level': r['sender_level'],
                    'avatar': r['sender_avatar'],
                    'vip': r['sender_vip'],
                    'text': r['text'],
                    'created_at': r['created_at']
                })
            return self._send_json(200, { 'success': True, 'messages': msgs })

        # Friends List
        if path == '/api/friends/list':
            uname = qs.get('username', [''])[0].strip()
            sconn = get_server_db()
            frows = sconn.execute("SELECT friend_username FROM friends WHERE username = ?", (uname,)).fetchall()
            flist = []
            for fr in frows:
                fn = fr['friend_username']
                c = sconn.execute("SELECT * FROM characters WHERE username = ? LIMIT 1", (fn,)).fetchone()
                if c:
                    flist.append({
                        'username': fn,
                        'name': c['name'],
                        'level': c['level'],
                        'avatar': c['avatar'],
                        'combatPower': c['combat_power'],
                        'online': True
                    })
                else:
                    flist.append({
                        'username': fn,
                        'name': fn,
                        'level': 20,
                        'avatar': 'player/touxiang1.png',
                        'combatPower': 1500,
                        'online': False
                    })
            sconn.close()
            return self._send_json(200, { 'success': True, 'friends': flist })

        # Leaderboard (Top 50 by Combat Power)
        if path == '/api/leaderboard':
            sconn = get_server_db()
            rows = sconn.execute("""
                SELECT c.*, a.last_login 
                FROM characters c 
                LEFT JOIN accounts a ON c.username = a.username
                ORDER BY c.combat_power DESC LIMIT 50
            """).fetchall()
            lb = []
            for idx, r in enumerate(rows):
                lead = sconn.execute("SELECT pet_id, name, level FROM team_pets WHERE username = ? AND server_id = ? AND slot = 0", (r['username'], r['server_id'])).fetchone()
                lb.append({
                    'rank': idx + 1,
                    'username': r['username'],
                    'name': r['name'],
                    'title': r['title'],
                    'avatar': r['avatar'],
                    'level': r['level'],
                    'combatPower': r['combat_power'],
                    'arenaRank': r['arena_rank'],
                    'winCount': r['win_count'],
                    'lossCount': r['loss_count'],
                    'leadPet': dict(lead) if lead else { 'id': 6, 'name': 'Charizard', 'level': r['level'] }
                })
            sconn.close()
            return self._send_json(200, { 'success': True, 'leaderboard': lb })

        # Arena Rivals (Combines real players + authentic t_integral_robot from Bag.db)
        if path == '/api/arena/rivals':
            current_rank = int(qs.get('rank', [1000])[0])
            bconn = get_bag_db()
            # Fetch 4 robots around current rank
            min_r = max(1, current_rank - 50)
            max_r = max(min_r + 10, current_rank)
            robots = bconn.execute("""
                SELECT id, name, trainer_lv, carrying_pet1, carrying_pet2 
                FROM t_integral_robot 
                WHERE id >= ? AND id <= ?
                ORDER BY id ASC LIMIT 5
            """, (min_r, max_r)).fetchall()
            
            rivals = []
            for rob in robots:
                pet_parts = rob['carrying_pet1'].split('|')
                pid = int(pet_parts[0]) if pet_parts else 6
                plv = int(pet_parts[1]) if len(pet_parts) > 1 else 30
                prow = bconn.execute("SELECT pet_name FROM t_pet WHERE pet_id = ?", (pid,)).fetchone()
                pname = prow['pet_name'] if prow else 'Charizard'
                rivals.append({
                    'playerId': f'robot_{rob["id"]}',
                    'name': rob['name'],
                    'title': 'Arena Master',
                    'avatar': 'player/touxiang1.png',
                    'level': rob['trainer_lv'],
                    'rank': rob['id'],
                    'combatPower': rob['trainer_lv'] * 240,
                    'team': [{ 'id': pid, 'name': pname, 'level': plv }]
                })
            bconn.close()
            return self._send_json(200, { 'success': True, 'rivals': rivals })

        # Store Goods Catalog
        if path == '/api/store/list':
            bconn = get_bag_db()
            goods_rows = bconn.execute("""
                SELECT g.id, g.goods, g.number, g.cions, g.Diamonds, 
                       b.prop_name, b.prop_des, b.prop_icon, b.prop_type
                FROM t_store_goods g
                LEFT JOIN bag_table b ON g.goods = b.prop_id
                WHERE g.type = 1
                LIMIT 40
            """).fetchall()
            bconn.close()

            items = []
            for g in goods_rows:
                items.append({
                    'goods_id': g['id'],
                    'item_id': g['goods'],
                    'name': g['prop_name'] or f"Item #{g['goods']}",
                    'description': g['prop_des'] or "",
                    'icon': g['prop_icon'] or "item/item_box.png",
                    'amount': g['number'],
                    'gold_price': g['cions'],
                    'diamond_price': g['Diamonds']
                })
            return self._send_json(200, { 'success': True, 'catalog': items })

        # Gacha Machine Pool Information
        if path == '/api/draw/info':
            bconn = get_bag_db()
            gold_pool_rows = bconn.execute("""
                SELECT r.prop_id, p.pet_name, p.pet_quality 
                FROM t_toy_reward r 
                LEFT JOIN t_pet p ON r.prop_id = p.pet_id 
                WHERE r.reward_type = 1
            """).fetchall()
            dia_pool_rows = bconn.execute("""
                SELECT r.prop_id, p.pet_name, p.pet_quality 
                FROM t_toy_reward r 
                LEFT JOIN t_pet p ON r.prop_id = p.pet_id 
                WHERE r.reward_type = 2
            """).fetchall()
            bconn.close()

            return self._send_json(200, {
                'success': True,
                'gold_price_single': 5000,
                'gold_price_ten': 45000,
                'diamond_price_single': 350,
                'diamond_price_ten': 3080,
                'diamond_pity_max': 10,
                'gold_pool': [dict(r) for r in gold_pool_rows],
                'diamond_pool': [dict(r) for r in dia_pool_rows]
            })

        # PVP Waiting Rooms Listing
        if path == '/api/pvp/rooms':
            rms = []
            for r in active_rooms.values():
                if r.get('status') == 'WAITING_FOR_OPPONENT':
                    h = r.get('host', {})
                    lead = h.get('team')[0] if (h.get('team') and len(h.get('team')) > 0) else { 'id': 6, 'name': 'Charizard', 'level': h.get('level', 30) }
                    rms.append({
                        'id': r.get('id'),
                        'code': r.get('code'),
                        'name': r.get('name'),
                        'hostName': h.get('name'),
                        'hostLevel': h.get('level'),
                        'hostAvatar': h.get('avatar'),
                        'leadPet': lead
                    })
            return self._send_json(200, { 'success': True, 'rooms': rms })

        # PVP Turn Polling
        if path == '/api/pvp/poll':
            room_id = qs.get('room_id', [''])[0]
            player_id = qs.get('player_id', [''])[0]
            turn = int(qs.get('turn', [1])[0])

            r = active_rooms.get(room_id)
            if not r:
                return self._send_json(404, { 'success': False, 'error': 'Room not found' })

            is_host = (player_id == r['host']['id'])
            opp_role = 'guest' if is_host else 'host'
            opponent = r.get('guest') if is_host else r.get('host')
            turn_acts = r.get('actions', {}).get(str(turn), {})
            opp_act = turn_acts.get(opp_role)

            return self._send_json(200, {
                'success': True,
                'room_status': r.get('status'),
                'turn': r.get('turn', 1),
                'opponent': opponent,
                'opponent_action': opp_act,
                'winner': r.get('winner')
            })

        self._send_json(404, { 'success': False, 'error': 'Endpoint not found' })

    # =========================================================================
    # POST Requests
    # =========================================================================
    def do_POST(self):
        parsed = urlparse(self.path)
        path = parsed.path
        body = self._read_body()

        # Account Registration
        if path == '/api/auth/register':
            uname = (body.get('username') or '').strip()
            pwd = body.get('password')
            if not uname or not pwd:
                return self._send_json(400, { 'success': False, 'error': 'Invalid username or password' })

            sconn = get_server_db()
            exist = sconn.execute("SELECT username FROM accounts WHERE username = ?", (uname,)).fetchone()
            if exist:
                sconn.close()
                return self._send_json(409, { 'success': False, 'error': 'Account already exists' })

            tok = gen_token(uname)
            pwhash = hash_pw(pwd)
            sconn.execute("INSERT INTO accounts (username, password_hash, token) VALUES (?, ?, ?)", (uname, pwhash, tok))
            
            # Default Character
            server_id = body.get('server_id', 1)
            nick = body.get('name', uname)
            gender = body.get('gender', 1)
            avatar = 'player/touxiang1.png' if gender == 1 else 'player/touxiang2.png'
            now_ts = int(time.time())

            sconn.execute("""
                INSERT INTO characters (username, server_id, name, gender, avatar, title, level, exp, gold, diamonds, stamina, max_stamina, last_stamina_update)
                VALUES (?, ?, ?, ?, ?, 'Novice Trainer', 1, 0, 5000, 200, 120, 120, ?)
            """, (uname, server_id, nick, gender, avatar, now_ts))

            # Initial Starter Bag Items: 10 Pokéballs (28), 5 Potions (1), 5 Small EXP (245)
            sconn.execute("INSERT OR REPLACE INTO bag_items (username, server_id, item_id, count) VALUES (?, ?, 28, 10)", (uname, server_id))
            sconn.execute("INSERT OR REPLACE INTO bag_items (username, server_id, item_id, count) VALUES (?, ?, 1, 5)", (uname, server_id))
            sconn.execute("INSERT OR REPLACE INTO bag_items (username, server_id, item_id, count) VALUES (?, ?, 245, 5)", (uname, server_id))

            sconn.commit()
            char = sconn.execute("SELECT * FROM characters WHERE username = ? AND server_id = ?", (uname, server_id)).fetchone()
            profile = dict(char)
            sconn.close()

            print(f'[Auth] Registered: {uname}')
            return self._send_json(200, { 'success': True, 'token': tok, 'user': { 'username': uname, 'profile': profile } })

        # Account Login & Auto-Registration
        if path == '/api/auth/login':
            uname = (body.get('username') or '').strip()
            pwd = body.get('password')
            if not uname or not pwd:
                return self._send_json(400, { 'success': False, 'error': 'Invalid username or password' })

            sconn = get_server_db()
            acc = sconn.execute("SELECT * FROM accounts WHERE username = ?", (uname,)).fetchone()
            server_id = body.get('server_id', 1)

            if not acc:
                # Auto-register guest/new player
                tok = gen_token(uname)
                pwhash = hash_pw(pwd)
                now_ts = int(time.time())
                sconn.execute("INSERT INTO accounts (username, password_hash, token) VALUES (?, ?, ?)", (uname, pwhash, tok))
                sconn.execute("""
                    INSERT INTO characters (username, server_id, name, gender, avatar, title, level, exp, gold, diamonds, stamina, max_stamina, last_stamina_update)
                    VALUES (?, ?, ?, 1, 'player/touxiang1.png', 'Novice Trainer', 1, 0, 5000, 200, 120, 120, ?)
                """, (uname, server_id, uname, now_ts))
                sconn.execute("INSERT OR REPLACE INTO bag_items (username, server_id, item_id, count) VALUES (?, ?, 28, 10)", (uname, server_id))
                sconn.execute("INSERT OR REPLACE INTO bag_items (username, server_id, item_id, count) VALUES (?, ?, 1, 5)", (uname, server_id))
                sconn.execute("INSERT OR REPLACE INTO bag_items (username, server_id, item_id, count) VALUES (?, ?, 245, 5)", (uname, server_id))
                sconn.commit()
                print(f'[Auth] Auto-registered: {uname}')
            elif acc['password_hash'] != hash_pw(pwd):
                sconn.close()
                return self._send_json(401, { 'success': False, 'error': 'Incorrect password!' })

            tok = gen_token(uname)
            sconn.execute("UPDATE accounts SET token = ?, last_login = CURRENT_TIMESTAMP WHERE username = ?", (tok, uname))

            char = sconn.execute("SELECT * FROM characters WHERE username = ? AND server_id = ?", (uname, server_id)).fetchone()
            if not char:
                now_ts = int(time.time())
                sconn.execute("""
                    INSERT INTO characters (username, server_id, name, gender, avatar, title, level, exp, gold, diamonds, stamina, max_stamina, last_stamina_update)
                    VALUES (?, ?, ?, 1, 'player/touxiang1.png', 'Novice Trainer', 1, 0, 5000, 200, 120, 120, ?)
                """, (uname, server_id, uname, now_ts))
                sconn.commit()
                char = sconn.execute("SELECT * FROM characters WHERE username = ? AND server_id = ?", (uname, server_id)).fetchone()

            stamina = refresh_character_stamina(char, sconn)
            profile = dict(char)
            profile['stamina'] = stamina

            team_rows = sconn.execute("SELECT * FROM team_pets WHERE username = ? AND server_id = ? ORDER BY slot ASC", (uname, server_id)).fetchall()
            sconn.close()

            return self._send_json(200, {
                'success': True,
                'token': tok,
                'user': { 'username': uname, 'profile': profile },
                'team': [dict(r) for r in team_rows]
            })

        # Role / Character Creation
        if path == '/api/role/create':
            uname = (body.get('username') or '').strip()
            nick = (body.get('nickname') or '').strip()
            server_id = body.get('server_id', 1)
            gender = body.get('gender', 1)
            starter_id = body.get('starter_id', 4) # Charmander by default

            if not uname or not nick:
                return self._send_json(400, { 'success': False, 'error': 'Missing username or nickname' })

            avatar = 'player/touxiang1.png' if gender == 1 else 'player/touxiang2.png'
            sconn = get_server_db()
            sconn.execute("""
                UPDATE characters 
                SET name = ?, gender = ?, avatar = ? 
                WHERE username = ? AND server_id = ?
            """, (nick, gender, avatar, uname, server_id))

            # Generate Starter Pokemon
            ivs = { 'hp': 20, 'atk': 20, 'def': 20, 'spatk': 20, 'spdef': 20, 'speed': 20 }
            evs = { 'hp': 0, 'atk': 0, 'def': 0, 'spatk': 0, 'spdef': 0, 'speed': 0 }
            stats = calc_pet_stats(starter_id, 5, 1, 0, ivs, evs)
            puid = f'{uname}_pet_0'

            sconn.execute("""
                INSERT OR REPLACE INTO team_pets (
                    pet_uid, username, server_id, slot, pet_id, name, level, exp,
                    cur_hp, max_hp, atk, def, spatk, spdef, speed, star, breakthrough_stage,
                    iv_hp, iv_atk, iv_def, iv_spatk, iv_spdef, iv_speed
                ) VALUES (?, ?, ?, 0, ?, ?, 5, 0, ?, ?, ?, ?, ?, ?, ?, 1, 0, 20, 20, 20, 20, 20, 20)
            """, (
                puid, uname, server_id, starter_id, stats['name'],
                stats['max_hp'], stats['max_hp'], stats['atk'], stats['def'],
                stats['spatk'], stats['spdef'], stats['speed']
            ))

            sconn.execute("UPDATE characters SET combat_power = ? WHERE username = ? AND server_id = ?", (stats['combat_power'], uname, server_id))
            sconn.commit()
            sconn.close()

            print(f'[Role] Created character {nick} (Starter: {stats["name"]}) for {uname}')
            return self._send_json(200, { 'success': True, 'message': 'Character created successfully' })

        # Two-Way Cloud Save Progress Sync
        if path == '/api/player/sync':
            uname = (body.get('username') or '').strip()
            server_id = body.get('server_id', 1)
            if not uname:
                return self._send_json(400, { 'success': False, 'error': 'Missing username' })

            sconn = get_server_db()
            p = body.get('profile', {})
            if p:
                sconn.execute("""
                    UPDATE characters 
                    SET name = COALESCE(?, name),
                        level = COALESCE(?, level),
                        gold = COALESCE(?, gold),
                        diamonds = COALESCE(?, diamonds),
                        combat_power = COALESCE(?, combat_power),
                        stage_id = COALESCE(?, stage_id)
                    WHERE username = ? AND server_id = ?
                """, (
                    p.get('name'), p.get('level'), p.get('gold'),
                    p.get('diamonds'), p.get('combatPower'), p.get('stageId'),
                    uname, server_id
                ))

            # Team Pets Sync
            team = body.get('team', [])
            if team:
                for idx, pet in enumerate(team):
                    puid = pet.get('uid') or f'{uname}_pet_{idx}'
                    sconn.execute("""
                        INSERT OR REPLACE INTO team_pets (
                            pet_uid, username, server_id, slot, pet_id, name, level, exp,
                            cur_hp, max_hp, atk, def, spatk, spdef, speed, star, breakthrough_stage
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        puid, uname, server_id, idx, pet.get('id', 1), pet.get('name', 'Pet'),
                        pet.get('level', 1), pet.get('exp', 0), pet.get('currentHp', 100),
                        pet.get('maxHp', 100), pet.get('atk', 50), pet.get('def', 50),
                        pet.get('spatk', 50), pet.get('spdef', 50), pet.get('speed', 50),
                        pet.get('star', 1), pet.get('breakthroughStage', 0)
                    ))

            # Bag Sync
            bag = body.get('bag', {})
            if isinstance(bag, dict):
                for item_id, count in bag.items():
                    sconn.execute("""
                        INSERT OR REPLACE INTO bag_items (username, server_id, item_id, count)
                        VALUES (?, ?, ?, ?)
                    """, (uname, server_id, int(item_id), int(count)))

            sconn.commit()
            sconn.close()
            return self._send_json(200, { 'success': True, 'message': 'Cloud progress synced successfully' })

        # Pet Cultivation: Feed EXP Candy
        if path == '/api/pet/feed_candy':
            uname = (body.get('username') or '').strip()
            server_id = body.get('server_id', 1)
            pet_uid = body.get('pet_uid')
            candy_id = int(body.get('candy_id', 245)) # 245: Small, 246: Med, 247: Lg, 248: XL, 20: Rare Candy
            count = max(1, int(body.get('count', 1)))

            # Candy EXP mappings from bag_table
            CANDY_EXP_MAP = { 245: 60, 246: 300, 247: 1500, 248: 7500, 20: 999999 }
            if candy_id not in CANDY_EXP_MAP:
                return self._send_json(400, { 'success': False, 'error': 'Invalid candy ID' })

            sconn = get_server_db()
            bag_item = sconn.execute("SELECT count FROM bag_items WHERE username = ? AND server_id = ? AND item_id = ?", (uname, server_id, candy_id)).fetchone()
            if not bag_item or bag_item['count'] < count:
                sconn.close()
                return self._send_json(400, { 'success': False, 'error': 'Not enough candies in Bag' })

            # Deduct candy
            rem_candies = bag_item['count'] - count
            if rem_candies > 0:
                sconn.execute("UPDATE bag_items SET count = ? WHERE username = ? AND server_id = ? AND item_id = ?", (rem_candies, uname, server_id, candy_id))
            else:
                sconn.execute("DELETE FROM bag_items WHERE username = ? AND server_id = ? AND item_id = ?", (uname, server_id, candy_id))

            # Fetch Pet & Trainer Level Cap
            char = sconn.execute("SELECT level FROM characters WHERE username = ? AND server_id = ?", (uname, server_id)).fetchone()
            trainer_lv = char['level'] if char else 50

            pet = sconn.execute("SELECT * FROM team_pets WHERE pet_uid = ?", (pet_uid,)).fetchone()
            is_team = True
            if not pet:
                pet = sconn.execute("SELECT * FROM box_pets WHERE pet_uid = ?", (pet_uid,)).fetchone()
                is_team = False

            if not pet:
                sconn.close()
                return self._send_json(404, { 'success': False, 'error': 'Pet not found' })

            cur_lv = pet['level']
            cur_exp = pet['exp']
            exp_gain = CANDY_EXP_MAP[candy_id] * count

            # Level up calculation
            bconn = get_bag_db()
            while exp_gain > 0 and cur_lv < trainer_lv:
                req_row = bconn.execute("SELECT pet_exp_1 FROM t_pet_level WHERE pet_level = ?", (cur_lv,)).fetchone()
                req_exp = req_row['pet_exp_1'] if req_row else 500
                need = req_exp - cur_exp
                if exp_gain >= need:
                    exp_gain -= need
                    cur_lv += 1
                    cur_exp = 0
                else:
                    cur_exp += exp_gain
                    exp_gain = 0
            bconn.close()

            # Recalculate stats
            ivs = { 'hp': pet['iv_hp'], 'atk': pet['iv_atk'], 'def': pet['iv_def'], 'spatk': pet['iv_spatk'], 'spdef': pet['iv_spdef'], 'speed': pet['iv_speed'] }
            evs = { 'hp': pet['ev_hp'], 'atk': pet['ev_atk'], 'def': pet['ev_def'], 'spatk': pet['ev_spatk'], 'spdef': pet['ev_spdef'], 'speed': pet['ev_speed'] }
            new_stats = calc_pet_stats(pet['pet_id'], cur_lv, pet['star'], pet['breakthrough_stage'], ivs, evs)

            table_name = "team_pets" if is_team else "box_pets"
            sconn.execute(f"""
                UPDATE {table_name}
                SET level = ?, exp = ?, cur_hp = ?, max_hp = ?, atk = ?, def = ?, spatk = ?, spdef = ?, speed = ?
                WHERE pet_uid = ?
            """, (cur_lv, cur_exp, new_stats['max_hp'], new_stats['max_hp'], new_stats['atk'], new_stats['def'], new_stats['spatk'], new_stats['spdef'], new_stats['speed'], pet_uid))
            sconn.commit()
            sconn.close()

            return self._send_json(200, {
                'success': True,
                'pet_uid': pet_uid,
                'level': cur_lv,
                'exp': cur_exp,
                'stats': new_stats,
                'remaining_candies': rem_candies
            })

        # Pet Cultivation: Breakthrough (TuPo)
        if path == '/api/pet/breakthrough':
            uname = (body.get('username') or '').strip()
            server_id = body.get('server_id', 1)
            pet_uid = body.get('pet_uid')

            sconn = get_server_db()
            pet = sconn.execute("SELECT * FROM team_pets WHERE pet_uid = ?", (pet_uid,)).fetchone()
            is_team = True
            if not pet:
                pet = sconn.execute("SELECT * FROM box_pets WHERE pet_uid = ?", (pet_uid,)).fetchone()
                is_team = False
            if not pet:
                sconn.close()
                return self._send_json(404, { 'success': False, 'error': 'Pet not found' })

            cur_stage = pet['breakthrough_stage']
            next_stage = cur_stage + 1
            if next_stage > 13:
                sconn.close()
                return self._send_json(400, { 'success': False, 'error': 'Already at max breakthrough stage' })

            # Query pet_break table
            bconn = get_bag_db()
            break_info = bconn.execute("SELECT * FROM pet_break WHERE prt_id = ?", (pet['pet_id'],)).fetchone()
            bconn.close()

            req_lv = int(break_info[f'level_limit_{next_stage}']) if (break_info and break_info[f'level_limit_{next_stage}']) else next_stage * 5
            cost_gold = int(break_info[f'break_cost_{next_stage}']) if (break_info and break_info[f'break_cost_{next_stage}']) else next_stage * 1000

            if pet['level'] < req_lv:
                sconn.close()
                return self._send_json(400, { 'success': False, 'error': f'Requires Pet Level {req_lv}' })

            char = sconn.execute("SELECT gold FROM characters WHERE username = ? AND server_id = ?", (uname, server_id)).fetchone()
            if not char or char['gold'] < cost_gold:
                sconn.close()
                return self._send_json(400, { 'success': False, 'error': f'Insufficient Gold (requires {cost_gold})' })

            # Deduct gold & advance breakthrough stage
            sconn.execute("UPDATE characters SET gold = gold - ? WHERE username = ? AND server_id = ?", (cost_gold, uname, server_id))
            ivs = { 'hp': pet['iv_hp'], 'atk': pet['iv_atk'], 'def': pet['iv_def'], 'spatk': pet['iv_spatk'], 'spdef': pet['iv_spdef'], 'speed': pet['iv_speed'] }
            evs = { 'hp': pet['ev_hp'], 'atk': pet['ev_atk'], 'def': pet['ev_def'], 'spatk': pet['ev_spatk'], 'spdef': pet['ev_spdef'], 'speed': pet['ev_speed'] }
            new_stats = calc_pet_stats(pet['pet_id'], pet['level'], pet['star'], next_stage, ivs, evs)

            table_name = "team_pets" if is_team else "box_pets"
            sconn.execute(f"""
                UPDATE {table_name} 
                SET breakthrough_stage = ?, cur_hp = ?, max_hp = ?, atk = ?, def = ?, spatk = ?, spdef = ?, speed = ?
                WHERE pet_uid = ?
            """, (next_stage, new_stats['max_hp'], new_stats['max_hp'], new_stats['atk'], new_stats['def'], new_stats['spatk'], new_stats['spdef'], new_stats['speed'], pet_uid))
            sconn.commit()
            sconn.close()

            return self._send_json(200, {
                'success': True,
                'breakthrough_stage': next_stage,
                'stats': new_stats
            })

        # Pet Cultivation: Special Training (TeXun)
        if path == '/api/pet/train':
            uname = (body.get('username') or '').strip()
            server_id = body.get('server_id', 1)
            pet_uid = body.get('pet_uid')

            sconn = get_server_db()
            pet = sconn.execute("SELECT * FROM team_pets WHERE pet_uid = ?", (pet_uid,)).fetchone()
            is_team = True
            if not pet:
                pet = sconn.execute("SELECT * FROM box_pets WHERE pet_uid = ?", (pet_uid,)).fetchone()
                is_team = False
            if not pet:
                sconn.close()
                return self._send_json(404, { 'success': False, 'error': 'Pet not found' })

            cur_star = pet['star']
            next_star = cur_star + 1
            if next_star > 5:
                sconn.close()
                return self._send_json(400, { 'success': False, 'error': 'Already at max 5 stars' })

            gold_cost = next_star * 20000
            char = sconn.execute("SELECT gold FROM characters WHERE username = ? AND server_id = ?", (uname, server_id)).fetchone()
            if not char or char['gold'] < gold_cost:
                sconn.close()
                return self._send_json(400, { 'success': False, 'error': f'Requires {gold_cost} Gold' })

            sconn.execute("UPDATE characters SET gold = gold - ? WHERE username = ? AND server_id = ?", (gold_cost, uname, server_id))
            ivs = { 'hp': pet['iv_hp'], 'atk': pet['iv_atk'], 'def': pet['iv_def'], 'spatk': pet['iv_spatk'], 'spdef': pet['iv_spdef'], 'speed': pet['iv_speed'] }
            evs = { 'hp': pet['ev_hp'], 'atk': pet['ev_atk'], 'def': pet['ev_def'], 'spatk': pet['ev_spatk'], 'spdef': pet['ev_spdef'], 'speed': pet['ev_speed'] }
            new_stats = calc_pet_stats(pet['pet_id'], pet['level'], next_star, pet['breakthrough_stage'], ivs, evs)

            table_name = "team_pets" if is_team else "box_pets"
            sconn.execute(f"""
                UPDATE {table_name} 
                SET star = ?, cur_hp = ?, max_hp = ?, atk = ?, def = ?, spatk = ?, spdef = ?, speed = ?
                WHERE pet_uid = ?
            """, (next_star, new_stats['max_hp'], new_stats['max_hp'], new_stats['atk'], new_stats['def'], new_stats['spatk'], new_stats['spdef'], new_stats['speed'], pet_uid))
            sconn.commit()
            sconn.close()

            return self._send_json(200, {
                'success': True,
                'star': next_star,
                'stats': new_stats
            })

        # Pet Cultivation: Evolution (JinHua)
        if path == '/api/pet/evolve':
            uname = (body.get('username') or '').strip()
            server_id = body.get('server_id', 1)
            pet_uid = body.get('pet_uid')

            sconn = get_server_db()
            pet = sconn.execute("SELECT * FROM team_pets WHERE pet_uid = ?", (pet_uid,)).fetchone()
            is_team = True
            if not pet:
                pet = sconn.execute("SELECT * FROM box_pets WHERE pet_uid = ?", (pet_uid,)).fetchone()
                is_team = False
            if not pet:
                sconn.close()
                return self._send_json(404, { 'success': False, 'error': 'Pet not found' })

            # Check pet_evolution table
            bconn = get_bag_db()
            evo = bconn.execute("SELECT * FROM pet_evolution WHERE pet_id = ?", (pet['pet_id'],)).fetchone()
            if not evo or not evo['evolution_id_1']:
                bconn.close()
                sconn.close()
                return self._send_json(400, { 'success': False, 'error': 'This Pokémon cannot evolve further' })

            target_id = int(evo['evolution_id_1'])
            req_lv = int(evo['level_limit_1']) if evo['level_limit_1'] else 16
            stone_id = int(evo['prop_needed_1']) if evo['prop_needed_1'] else None
            stone_num = int(evo['prop_number_1']) if evo['prop_number_1'] else 0
            bconn.close()

            if pet['level'] < req_lv:
                sconn.close()
                return self._send_json(400, { 'success': False, 'error': f'Requires Pet Level {req_lv}' })

            if stone_id and stone_num > 0:
                bag_stone = sconn.execute("SELECT count FROM bag_items WHERE username = ? AND server_id = ? AND item_id = ?", (uname, server_id, stone_id)).fetchone()
                if not bag_stone or bag_stone['count'] < stone_num:
                    sconn.close()
                    return self._send_json(400, { 'success': False, 'error': f'Requires {stone_num} Evolution Stones' })
                if bag_stone['count'] > stone_num:
                    sconn.execute("UPDATE bag_items SET count = count - ? WHERE username = ? AND server_id = ? AND item_id = ?", (stone_num, uname, server_id, stone_id))
                else:
                    sconn.execute("DELETE FROM bag_items WHERE username = ? AND server_id = ? AND item_id = ?", (uname, server_id, stone_id))

            # Transform into evolved species
            ivs = { 'hp': pet['iv_hp'], 'atk': pet['iv_atk'], 'def': pet['iv_def'], 'spatk': pet['iv_spatk'], 'spdef': pet['iv_spdef'], 'speed': pet['iv_speed'] }
            evs = { 'hp': pet['ev_hp'], 'atk': pet['ev_atk'], 'def': pet['ev_def'], 'spatk': pet['ev_spatk'], 'spdef': pet['ev_spdef'], 'speed': pet['ev_speed'] }
            new_stats = calc_pet_stats(target_id, pet['level'], pet['star'], pet['breakthrough_stage'], ivs, evs)

            table_name = "team_pets" if is_team else "box_pets"
            sconn.execute(f"""
                UPDATE {table_name}
                SET pet_id = ?, name = ?, cur_hp = ?, max_hp = ?, atk = ?, def = ?, spatk = ?, spdef = ?, speed = ?
                WHERE pet_uid = ?
            """, (target_id, new_stats['name'], new_stats['max_hp'], new_stats['max_hp'], new_stats['atk'], new_stats['def'], new_stats['spatk'], new_stats['spdef'], new_stats['speed'], pet_uid))
            sconn.commit()
            sconn.close()

            return self._send_json(200, {
                'success': True,
                'new_pet_id': target_id,
                'name': new_stats['name'],
                'stats': new_stats
            })

        # Stage: Start Battle (Consume Stamina)
        if path == '/api/stage/battle_start':
            uname = (body.get('username') or '').strip()
            server_id = body.get('server_id', 1)
            stage_id = int(body.get('stage_id', 1))

            bconn = get_bag_db()
            stg = bconn.execute("SELECT s_dynamic_cost FROM t_stage WHERE s_id = ?", (stage_id,)).fetchone()
            cost = stg['s_dynamic_cost'] if stg else 5
            bconn.close()

            sconn = get_server_db()
            char = sconn.execute("SELECT * FROM characters WHERE username = ? AND server_id = ?", (uname, server_id)).fetchone()
            if not char:
                sconn.close()
                return self._send_json(404, { 'success': False, 'error': 'Character not found' })

            cur_stamina = refresh_character_stamina(char, sconn)
            if cur_stamina < cost:
                sconn.close()
                return self._send_json(400, { 'success': False, 'error': f'Not enough stamina (requires {cost})' })

            sconn.execute("UPDATE characters SET stamina = stamina - ? WHERE username = ? AND server_id = ?", (cost, uname, server_id))
            sconn.commit()
            sconn.close()

            return self._send_json(200, { 'success': True, 'cost': cost, 'remaining_stamina': cur_stamina - cost })

        # Stage: Finish Battle (Award Stars, Gold, EXP, and Rolls Drops)
        if path == '/api/stage/battle_finish':
            uname = (body.get('username') or '').strip()
            server_id = body.get('server_id', 1)
            stage_id = int(body.get('stage_id', 1))
            victory = bool(body.get('victory', True))
            hp_percent = float(body.get('hp_percent', 1.0))

            if not victory:
                return self._send_json(200, { 'success': True, 'victory': False })

            stars = 3 if hp_percent >= 0.7 else (2 if hp_percent >= 0.3 else 1)

            bconn = get_bag_db()
            stg = bconn.execute("SELECT s_gold, s_exp, s_drop1 FROM t_stage WHERE s_id = ?", (stage_id,)).fetchone()
            gain_gold = stg['s_gold'] if stg else 200
            gain_exp = stg['s_exp'] if stg else 10
            drop_bag_id = stg['s_drop1'] if stg else '0'

            # Roll drops from t_drop
            drops = []
            if drop_bag_id and drop_bag_id != '0':
                drop_row = bconn.execute("SELECT * FROM t_drop WHERE prop_drop_bag_id = ? LIMIT 1", (drop_bag_id,)).fetchone()
                if drop_row:
                    for i in range(1, 11):
                        pid = drop_row[f'prop_drop_id{i}']
                        num = drop_row[f'prop_drop_num{i}']
                        prob = drop_row[f'prop_drop_probability{i}']
                        if pid and num and prob:
                            try:
                                if random.randint(1, 10000) <= int(prob):
                                    drops.append({ 'item_id': int(pid), 'count': int(num) })
                            except Exception:
                                pass
            bconn.close()

            # Always drop at least 1 Small EXP Ration or Pokeball on first clears
            if not drops:
                drops.append({ 'item_id': 245, 'count': 1 })

            sconn = get_server_db()
            sconn.execute("""
                UPDATE characters 
                SET gold = gold + ?, exp = exp + ?
                WHERE username = ? AND server_id = ?
            """, (gain_gold, gain_exp, uname, server_id))

            # Record stage progress
            prog = sconn.execute("SELECT stars, pass_count FROM stage_progress WHERE username = ? AND server_id = ? AND stage_id = ?", (uname, server_id, stage_id)).fetchone()
            cur_stars = max(stars, prog['stars'] if prog else 0)
            cur_passes = (prog['pass_count'] if prog else 0) + 1
            sconn.execute("""
                INSERT OR REPLACE INTO stage_progress (username, server_id, stage_id, stars, pass_count)
                VALUES (?, ?, ?, ?, ?)
            """, (uname, server_id, stage_id, cur_stars, cur_passes))

            # Add drops to inventory
            for d in drops:
                sconn.execute("""
                    INSERT INTO bag_items (username, server_id, item_id, count)
                    VALUES (?, ?, ?, ?)
                    ON CONFLICT(username, server_id, item_id) DO UPDATE SET count = count + ?
                """, (uname, server_id, d['item_id'], d['count'], d['count']))

            sconn.commit()
            sconn.close()

            return self._send_json(200, {
                'success': True,
                'victory': True,
                'stars': stars,
                'gold': gain_gold,
                'exp': gain_exp,
                'drops': drops
            })

        # Stage: Quick Sweep
        if path == '/api/stage/sweep':
            uname = (body.get('username') or '').strip()
            server_id = body.get('server_id', 1)
            stage_id = int(body.get('stage_id', 1))
            count = max(1, min(10, int(body.get('count', 1))))

            sconn = get_server_db()
            prog = sconn.execute("SELECT stars FROM stage_progress WHERE username = ? AND server_id = ? AND stage_id = ?", (uname, server_id, stage_id)).fetchone()
            if not prog or prog['stars'] < 3:
                sconn.close()
                return self._send_json(400, { 'success': False, 'error': 'Must complete stage with 3 stars to sweep' })

            # Check Sweep Tickets (148)
            tickets = sconn.execute("SELECT count FROM bag_items WHERE username = ? AND server_id = ? AND item_id = 148", (uname, server_id)).fetchone()
            if not tickets or tickets['count'] < count:
                sconn.close()
                return self._send_json(400, { 'success': False, 'error': f'Requires {count} Sweep Tickets' })

            bconn = get_bag_db()
            stg = bconn.execute("SELECT s_dynamic_cost, s_gold, s_exp, s_drop1 FROM t_stage WHERE s_id = ?", (stage_id,)).fetchone()
            cost_stamina = (stg['s_dynamic_cost'] if stg else 5) * count
            bconn.close()

            char = sconn.execute("SELECT * FROM characters WHERE username = ? AND server_id = ?", (uname, server_id)).fetchone()
            cur_stam = refresh_character_stamina(char, sconn)
            if cur_stam < cost_stamina:
                sconn.close()
                return self._send_json(400, { 'success': False, 'error': f'Requires {cost_stamina} Stamina' })

            # Deduct tickets and stamina
            sconn.execute("UPDATE bag_items SET count = count - ? WHERE username = ? AND server_id = ? AND item_id = 148", (count, uname, server_id))
            sconn.execute("UPDATE characters SET stamina = stamina - ?, gold = gold + ?, exp = exp + ? WHERE username = ? AND server_id = ?", (cost_stamina, (stg['s_gold'] or 200)*count, (stg['s_exp'] or 10)*count, uname, server_id))
            sconn.execute("UPDATE stage_progress SET pass_count = pass_count + ? WHERE username = ? AND server_id = ? AND stage_id = ?", (count, uname, server_id, stage_id))

            # Grant Sweep Rewards
            total_drops = []
            for _ in range(count):
                drop_item = { 'item_id': 245, 'count': 1 } # Small exp ration
                total_drops.append(drop_item)
                sconn.execute("""
                    INSERT INTO bag_items (username, server_id, item_id, count)
                    VALUES (?, ?, 245, 1)
                    ON CONFLICT(username, server_id, item_id) DO UPDATE SET count = count + 1
                """, (uname, server_id))

            sconn.commit()
            sconn.close()

            return self._send_json(200, {
                'success': True,
                'sweeps': count,
                'gold_gained': (stg['s_gold'] or 200) * count,
                'exp_gained': (stg['s_exp'] or 10) * count,
                'drops': total_drops
            })

        # Stage: Chapter Star Milestone Chests
        if path == '/api/stage/claim_chest':
            uname = (body.get('username') or '').strip()
            server_id = body.get('server_id', 1)
            chapter_id = int(body.get('chapter_id', 1))
            tier = int(body.get('tier', 1)) # 1, 2, or 3

            sconn = get_server_db()
            box_rec = sconn.execute("SELECT claimed_tiers FROM chapter_boxes WHERE username = ? AND server_id = ? AND chapter_id = ?", (uname, server_id, chapter_id)).fetchone()
            claimed = (box_rec['claimed_tiers'] or '').split(',') if box_rec else []
            if str(tier) in claimed:
                sconn.close()
                return self._send_json(400, { 'success': False, 'error': 'Chest tier already claimed' })

            # Verify total stars in chapter
            bconn = get_bag_db()
            chapter_stages = bconn.execute("SELECT s_id FROM t_stage WHERE s_chapter_id = ?", (chapter_id,)).fetchall()
            stg_ids = [r['s_id'] for r in chapter_stages]
            box_req = bconn.execute("SELECT * FROM t_box WHERE s_chapter_id = ?", (chapter_id,)).fetchone()
            bconn.close()

            if not box_req:
                sconn.close()
                return self._send_json(404, { 'success': False, 'error': 'Chapter chest definition not found' })

            req_stars = int(box_req[f'star_{tier}'])
            
            # Count user stars
            placeholders = ','.join('?' * len(stg_ids))
            cur_stars = sconn.execute(f"SELECT SUM(stars) as tot FROM stage_progress WHERE username = ? AND server_id = ? AND stage_id IN ({placeholders})", [uname, server_id] + stg_ids).fetchone()['tot'] or 0

            if cur_stars < req_stars:
                sconn.close()
                return self._send_json(400, { 'success': False, 'error': f'Requires {req_stars} stars (Current: {cur_stars})' })

            # Grant rewards
            claimed.append(str(tier))
            new_claimed_str = ','.join([c for c in claimed if c])
            sconn.execute("""
                INSERT OR REPLACE INTO chapter_boxes (username, server_id, chapter_id, claimed_tiers)
                VALUES (?, ?, ?, ?)
            """, (uname, server_id, chapter_id, new_claimed_str))

            # Default generous rewards: tier 1 -> 50 dia, 5k gold; tier 2 -> 100 dia, 10k gold; tier 3 -> 200 dia, 20k gold
            dia_award = tier * 100
            gold_award = tier * 10000
            sconn.execute("UPDATE characters SET diamonds = diamonds + ?, gold = gold + ? WHERE username = ? AND server_id = ?", (dia_award, gold_award, uname, server_id))
            sconn.commit()
            sconn.close()

            return self._send_json(200, {
                'success': True,
                'diamonds': dia_award,
                'gold': gold_award,
                'claimed_tier': tier
            })

        # Store Purchase
        if path == '/api/store/buy':
            uname = (body.get('username') or '').strip()
            server_id = body.get('server_id', 1)
            goods_id = int(body.get('goods_id', 1))

            bconn = get_bag_db()
            good = bconn.execute("SELECT * FROM t_store_goods WHERE id = ?", (goods_id,)).fetchone()
            bconn.close()

            if not good:
                return self._send_json(404, { 'success': False, 'error': 'Goods item not found' })

            gold_cost = good['cions'] or 0
            dia_cost = good['Diamonds'] or 0
            item_id = good['goods']
            amount = good['number'] or 1

            sconn = get_server_db()
            char = sconn.execute("SELECT gold, diamonds FROM characters WHERE username = ? AND server_id = ?", (uname, server_id)).fetchone()
            if not char:
                sconn.close()
                return self._send_json(404, { 'success': False, 'error': 'Character not found' })

            if gold_cost > 0 and char['gold'] < gold_cost:
                sconn.close()
                return self._send_json(400, { 'success': False, 'error': 'Not enough Gold' })
            if dia_cost > 0 and char['diamonds'] < dia_cost:
                sconn.close()
                return self._send_json(400, { 'success': False, 'error': 'Not enough Diamonds' })

            # Deduct currency
            sconn.execute("""
                UPDATE characters 
                SET gold = gold - ?, diamonds = diamonds - ? 
                WHERE username = ? AND server_id = ?
            """, (gold_cost, dia_cost, uname, server_id))

            # Add purchased goods to bag
            sconn.execute("""
                INSERT INTO bag_items (username, server_id, item_id, count)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(username, server_id, item_id) DO UPDATE SET count = count + ?
            """, (uname, server_id, item_id, amount, amount))

            sconn.commit()
            sconn.close()

            return self._send_json(200, {
                'success': True,
                'item_id': item_id,
                'amount': amount,
                'message': 'Purchase successful'
            })

        # Daily Check-in Sign-in Bonus
        if path == '/api/reward/checkin':
            uname = (body.get('username') or '').strip()
            server_id = body.get('server_id', 1)

            sconn = get_server_db()
            sconn.execute("""
                UPDATE characters 
                SET diamonds = diamonds + 100, gold = gold + 10000 
                WHERE username = ? AND server_id = ?
            """, (uname, server_id))

            # Grant 2 Rare Candies (20) and 5 Sweep Tickets (148)
            sconn.execute("""
                INSERT INTO bag_items (username, server_id, item_id, count)
                VALUES (?, ?, 20, 2)
                ON CONFLICT(username, server_id, item_id) DO UPDATE SET count = count + 2
            """, (uname, server_id))
            sconn.execute("""
                INSERT INTO bag_items (username, server_id, item_id, count)
                VALUES (?, ?, 148, 5)
                ON CONFLICT(username, server_id, item_id) DO UPDATE SET count = count + 5
            """, (uname, server_id))

            sconn.commit()
            sconn.close()

            return self._send_json(200, {
                'success': True,
                'gold': 10000,
                'diamonds': 100,
                'items': [
                    { 'id': 20, 'name': 'Rare Candy', 'count': 2 },
                    { 'id': 148, 'name': 'Sweep Ticket', 'count': 5 }
                ]
            })

        # Gacha Machine Buy (Gold & Diamond Draw)
        if path == '/api/draw/buy':
            uname = (body.get('username') or '').strip()
            server_id = body.get('server_id', 1)
            is_diamond = bool(body.get('is_diamond'))
            count = 10 if body.get('count') == 10 else 1

            cost_gold = 45000 if count == 10 else 5000
            cost_dia = 3080 if count == 10 else 350

            sconn = get_server_db()
            char = sconn.execute("SELECT gold, diamonds FROM characters WHERE username = ? AND server_id = ?", (uname, server_id)).fetchone()
            if not char:
                sconn.close()
                return self._send_json(404, { 'success': False, 'error': 'Character not found' })

            if is_diamond:
                if char['diamonds'] < cost_dia:
                    sconn.close()
                    return self._send_json(400, { 'success': False, 'error': 'Not enough Diamonds' })
                sconn.execute("UPDATE characters SET diamonds = diamonds - ? WHERE username = ? AND server_id = ?", (cost_dia, uname, server_id))
            else:
                if char['gold'] < cost_gold:
                    sconn.close()
                    return self._send_json(400, { 'success': False, 'error': 'Not enough Gold' })
                sconn.execute("UPDATE characters SET gold = gold - ? WHERE username = ? AND server_id = ?", (cost_gold, uname, server_id))

            # Query rewards from authentic t_toy_reward joined with t_pet
            bconn = get_bag_db()
            pool_type = 2 if is_diamond else 1
            pool_rows = bconn.execute("""
                SELECT r.prop_id, p.pet_name, p.pet_quality 
                FROM t_toy_reward r 
                LEFT JOIN t_pet p ON r.prop_id = p.pet_id 
                WHERE r.reward_type = ?
            """, (pool_type,)).fetchall()

            drawn = []
            for i in range(count):
                if is_diamond and (i == count - 1 or count == 10):
                    # Guarantee quality >= 3 (SR/SSR) on 10x
                    high_pool = [r for r in pool_rows if (r['pet_quality'] or 1) >= 3]
                    choice = secrets.choice(high_pool) if high_pool else secrets.choice(pool_rows)
                else:
                    choice = secrets.choice(pool_rows)

                pid = choice['prop_id']
                pname = choice['pet_name'] or f'Pokemon #{pid}'
                pqual = choice['pet_quality'] or 2
                drawn.append({
                    'id': pid,
                    'name': pname,
                    'quality': pqual,
                    'rarity': 'SSR' if pqual >= 5 else ('SR' if pqual >= 4 else ('R' if pqual >= 3 else 'C'))
                })

                # Automatically add Pokémon into player's box or team
                team_cnt = sconn.execute("SELECT count(*) as c FROM team_pets WHERE username = ? AND server_id = ?", (uname, server_id)).fetchone()['c']
                ivs = { 'hp': secrets.randbelow(17)+15, 'atk': secrets.randbelow(17)+15, 'def': secrets.randbelow(17)+15, 'spatk': secrets.randbelow(17)+15, 'spdef': secrets.randbelow(17)+15, 'speed': secrets.randbelow(17)+15 }
                evs = { 'hp': 0, 'atk': 0, 'def': 0, 'spatk': 0, 'spdef': 0, 'speed': 0 }
                pstats = calc_pet_stats(pid, 10, 1, 0, ivs, evs)
                puid = f'{uname}_{pid}_{int(time.time()*1000)}_{secrets.randbelow(9999)}'

                if team_cnt < 6:
                    sconn.execute("""
                        INSERT INTO team_pets (
                            pet_uid, username, server_id, slot, pet_id, name, level, exp,
                            cur_hp, max_hp, atk, def, spatk, spdef, speed, star, breakthrough_stage
                        ) VALUES (?, ?, ?, ?, ?, ?, 10, 0, ?, ?, ?, ?, ?, ?, ?, 1, 0)
                    """, (puid, uname, server_id, team_cnt, pid, pname, pstats['max_hp'], pstats['max_hp'], pstats['atk'], pstats['def'], pstats['spatk'], pstats['spdef'], pstats['speed']))
                else:
                    sconn.execute("""
                        INSERT INTO box_pets (
                            pet_uid, username, server_id, pet_id, name, level, exp,
                            cur_hp, max_hp, atk, def, spatk, spdef, speed, star, breakthrough_stage
                        ) VALUES (?, ?, ?, ?, ?, 10, 0, ?, ?, ?, ?, ?, ?, ?, 1, 0)
                    """, (puid, uname, server_id, pid, pname, pstats['max_hp'], pstats['max_hp'], pstats['atk'], pstats['def'], pstats['spatk'], pstats['spdef'], pstats['speed']))

            bconn.close()
            sconn.commit()
            sconn.close()

            return self._send_json(200, { 'success': True, 'results': drawn })

        # Chat: Send Message
        if path == '/api/chat/send':
            sender = body.get('sender', 'Trainer')
            text = (body.get('text') or '').strip()
            channel = body.get('channel', 'World')
            level = int(body.get('level', 1))
            avatar = body.get('avatar', 'player/touxiang1.png')
            vip = int(body.get('vip', 0))

            if not text:
                return self._send_json(400, { 'success': False, 'error': 'Empty text' })

            sconn = get_server_db()
            cur = sconn.cursor()
            cur.execute("""
                INSERT INTO chat_messages (channel, sender_name, sender_level, sender_avatar, sender_vip, text)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (channel, sender, level, avatar, vip, text[:200]))
            mid = cur.lastrowid
            sconn.commit()
            sconn.close()

            print(f'[Chat] [{channel}] {sender}: {text}')
            return self._send_json(200, {
                'success': True,
                'message': {
                    'id': mid,
                    'channel': channel,
                    'sender': sender,
                    'level': level,
                    'avatar': avatar,
                    'text': text
                }
            })

        # Friends: Add Friend
        if path == '/api/friends/add':
            u1 = (body.get('username') or '').strip()
            u2 = (body.get('target_username') or '').strip()
            if u1 and u2 and u1 != u2:
                sconn = get_server_db()
                sconn.execute("INSERT OR IGNORE INTO friends (username, friend_username) VALUES (?, ?)", (u1, u2))
                sconn.execute("INSERT OR IGNORE INTO friends (username, friend_username) VALUES (?, ?)", (u2, u1))
                sconn.commit()
                sconn.close()
            return self._send_json(200, { 'success': True, 'message': 'Friend added' })

        # Real-Time PVP: Create Room
        if path == '/api/pvp/create_room':
            pid = body.get('player_id')
            if not pid:
                return self._send_json(400, { 'success': False, 'error': 'Missing player_id' })
            code = body.get('room_code') or str(secrets.randbelow(9000) + 1000)
            room_id = f'room_{int(time.time())}_{code}'
            r = {
                'id': room_id,
                'code': code,
                'name': body.get('room_name', f'Battle Room {code}'),
                'status': 'WAITING_FOR_OPPONENT',
                'createdAt': time.time(),
                'host': {
                    'id': pid,
                    'name': body.get('name', pid),
                    'avatar': body.get('avatar', 'player/touxiang1.png'),
                    'level': body.get('level', 30),
                    'team': body.get('team', [])
                },
                'guest': None,
                'turn': 1,
                'actions': {},
                'winner': None
            }
            active_rooms[room_id] = r
            print(f'[PVP] Room created: {room_id} (Code: {code}) by {pid}')
            return self._send_json(200, { 'success': True, 'room_id': room_id, 'room_code': code, 'room': r })

        # Real-Time PVP: Join Room
        if path == '/api/pvp/join_room':
            code = str(body.get('room_code', '')).strip()
            pid = body.get('player_id')
            target = None
            for r in active_rooms.values():
                if (r.get('code') == code or r.get('id') == code) and r.get('status') == 'WAITING_FOR_OPPONENT':
                    target = r
                    break
            if not target:
                return self._send_json(404, { 'success': False, 'error': 'Room not found or already occupied' })

            target['guest'] = {
                'id': pid,
                'name': body.get('name', pid),
                'avatar': body.get('avatar', 'player/touxiang1.png'),
                'level': body.get('level', 30),
                'team': body.get('team', [])
            }
            target['status'] = 'BATTLE_ACTIVE'
            print(f'[PVP] {pid} joined Room {target["id"]}')
            return self._send_json(200, { 'success': True, 'room_id': target['id'], 'room_code': target['code'], 'opponent': target['host'] })

        # Real-Time PVP: Send Turn Action
        if path == '/api/pvp/action':
            rid = body.get('room_id')
            pid = body.get('player_id')
            r = active_rooms.get(rid)
            if not r:
                return self._send_json(404, { 'success': False, 'error': 'Room not found' })

            turn = str(body.get('turn', r.get('turn', 1)))
            if turn not in r['actions']:
                r['actions'][turn] = {}

            role = 'host' if pid == r['host']['id'] else 'guest'
            r['actions'][turn][role] = {
                'actionType': body.get('action_type', 1),
                'param': body.get('param', 0),
                'currentHp': body.get('current_hp'),
                'timestamp': time.time()
            }

            turn_ready = ('host' in r['actions'][turn] and 'guest' in r['actions'][turn])
            if turn_ready:
                r['turn'] = int(turn) + 1

            return self._send_json(200, { 'success': True, 'turn': int(turn), 'turn_ready': turn_ready })

        # Real-Time PVP: Finish Match
        if path == '/api/pvp/finish':
            rid = body.get('room_id')
            winner_id = body.get('winner_id')
            r = active_rooms.get(rid)
            if r:
                r['status'] = 'BATTLE_FINISHED'
                r['winner'] = winner_id
                sconn = get_server_db()
                hname = r['host']['name']
                gname = r['guest']['name'] if r.get('guest') else 'Unknown'
                wname = hname if winner_id == r['host']['id'] else gname
                sconn.execute("INSERT INTO pvp_records (p1_name, p2_name, winner_name) VALUES (?, ?, ?)", (hname, gname, wname))
                sconn.commit()
                sconn.close()
            return self._send_json(200, { 'success': True })

        # Catch Monster Formula (ClientGate CatchMonsterRequest)
        if path == '/api/battle/catch':
            max_hp = max(1, body.get('max_hp', 100))
            cur_hp = max(0, min(max_hp, body.get('current_hp', 100)))
            base_catch = body.get('catch_rate', 45)
            ball_mult = float(body.get('ball_multiplier', 1.0))
            status_mult = float(body.get('status_multiplier', 1.0))
            a = int(((3 * max_hp - 2 * cur_hp) * base_catch * ball_mult) / (3 * max_hp)) * status_mult
            success = (a >= 255) or (secrets.randbelow(255) < a)
            return self._send_json(200, { 'success': True, 'caught': success, 'catch_value': a })

        self._send_json(404, { 'success': False, 'error': 'Endpoint not found' })

# Threaded HTTP server for concurrent multiplayer connections
class ThreadedHTTPServer(socketserver.ThreadingMixIn, http.server.HTTPServer):
    daemon_threads = True

if __name__ == '__main__':
    print('=============================================================================')
    print(f' Pocket Fantasy Authentic Dedicated Server (SQLite Engine) on Port {PORT}')
    print(f' Local Address:  http://localhost:{PORT}')
    print(f' Emulator Host:  http://10.0.2.2:{PORT}')
    print('=============================================================================')
    server = ThreadedHTTPServer(('0.0.0.0', PORT), GameServerHandler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print('\nServer stopping...')
        server.server_close()
