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
import threading

class NullWriter:
    def write(self, s): pass
    def flush(self): pass

if sys.stdout is None:
    sys.stdout = NullWriter()
elif hasattr(sys.stdout, 'reconfigure'):
    try: sys.stdout.reconfigure(encoding='utf-8')
    except Exception: pass

if sys.stderr is None:
    sys.stderr = NullWriter()
elif hasattr(sys.stderr, 'reconfigure'):
    try: sys.stderr.reconfigure(encoding='utf-8')
    except Exception: pass
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
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)
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

    
    CREATE TABLE IF NOT EXISTS league_state (
        id INTEGER PRIMARY KEY CHECK (id = 1),
        season_id INTEGER DEFAULT 1,
        phase TEXT DEFAULT 'ENROLL',
        phase_override TEXT DEFAULT '',
        phase_end_time INTEGER DEFAULT 0,
        updated_at INTEGER DEFAULT 0
    );

    CREATE TABLE IF NOT EXISTS league_enrollments (
        username TEXT,
        division INTEGER,
        trainer_level INTEGER,
        roster_json TEXT,
        enrolled_at INTEGER,
        PRIMARY KEY (username, division)
    );

    CREATE TABLE IF NOT EXISTS league_knockouts (
        username TEXT,
        division INTEGER,
        points INTEGER DEFAULT 0,
        wins INTEGER DEFAULT 0,
        losses INTEGER DEFAULT 0,
        matches_played INTEGER DEFAULT 0,
        updated_at INTEGER,
        PRIMARY KEY (username, division)
    );

    CREATE TABLE IF NOT EXISTS league_brackets (
        division INTEGER,
        stage TEXT,
        match_index INTEGER,
        player1_name TEXT,
        player1_pet_id INTEGER,
        player1_level INTEGER,
        player1_score INTEGER DEFAULT 0,
        player2_name TEXT,
        player2_pet_id INTEGER,
        player2_level INTEGER,
        player2_score INTEGER DEFAULT 0,
        winner_name TEXT,
        status TEXT DEFAULT 'pending',
        PRIMARY KEY (division, stage, match_index)
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

# Ensure default league state row
def ensure_league_state():
    conn = get_server_db()
    conn.execute("INSERT OR IGNORE INTO league_state (id, season_id, phase, phase_override, phase_end_time, updated_at) VALUES (1, 1, 'ENROLL', '', 0, 0)")
    conn.commit()
    conn.close()
ensure_league_state()

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



# =============================================================================
# Authentic Master League (Dashiliansai / 大师联赛) Engine
# =============================================================================
def get_league_phase_and_schedule():
    sconn = get_server_db()
    st = sconn.execute("SELECT season_id, phase, phase_override, phase_end_time FROM league_state WHERE id = 1").fetchone()
    sconn.close()

    season_id = st['season_id'] if st else 1
    override = (st['phase_override'] if st else '').strip().upper()

    now = time.localtime()
    # 0=Mon, 1=Tue, 2=Wed, 3=Thu, 4=Fri, 5=Sat, 6=Sun
    wday = now.tm_wday
    hour = now.tm_hour
    minute = now.tm_min
    time_val = hour * 60 + minute

    auto_phase = 'ENROLL'
    auto_name = 'Phase 1: League Enrollment (Mon-Wed 16:30)'
    auto_desc = 'Sign up and configure your 12 or 36 Pokemon tournament roster. Knockout battles start Wednesday 17:30.'

    if wday < 2 or (wday == 2 and time_val < (16 * 60 + 30)):
        auto_phase = 'ENROLL'
        auto_name = 'Phase 1: League Enrollment (Mon-Wed 16:30)'
        auto_desc = 'Sign up and configure your 12 or 36 Pokemon tournament roster.'
    elif wday == 2 and time_val >= (16 * 60 + 30) and time_val < (17 * 60 + 30):
        auto_phase = 'PREPARE_KNOCKOUT'
        auto_name = 'Registration Closed (Knockouts Starting Soon)'
        auto_desc = 'Matchmaker opens at 17:30 today for live 6v6 Knockouts.'
    elif wday == 2 and time_val >= (17 * 60 + 30) and time_val < (19 * 60 + 30):
        auto_phase = 'KNOCKOUT'
        auto_name = 'Phase 2: Live Knockout Battles (Wed 17:30 - 19:30)'
        auto_desc = 'Queue in 1-minute matchmaking! Winner gets +2 points. Top 16 advance to Friday elimination.'
    elif (wday == 2 and time_val >= (19 * 60 + 30)) or wday == 3 or (wday == 4 and time_val < (17 * 60 + 30)):
        auto_phase = 'PREPARE_TOP16'
        auto_name = 'Top 16 Finalists Seeded'
        auto_desc = 'Top 16 contenders from Knockouts confirmed. Best of 3 battles start Friday 17:30.'
    elif wday == 4 and time_val >= (17 * 60 + 30):
        auto_phase = 'TOP16'
        auto_name = 'Phase 3: Top 16 Elimination (Friday 17:30 - Best of 3)'
        auto_desc = '16 finalists clash in Best of 3 matches! 8 winners advance to Saturday finals. Spectating available.'
    elif wday == 5 and time_val < (17 * 60 + 30):
        auto_phase = 'PREPARE_FINALS'
        auto_name = 'Top 8 Finalists Confirmed'
        auto_desc = 'Quarterfinals, Semifinals, and Grand Final commence Saturday 17:30.'
    elif wday == 5 and time_val >= (17 * 60 + 30):
        auto_phase = 'FINALS'
        auto_name = 'Phase 4: Top 8 & Grand Championship (Saturday 17:30)'
        auto_desc = 'Live Quarterfinals, Semifinals & Finals! Battle or spectate live for the League Trophy.'
    else:
        auto_phase = 'AWARDS'
        auto_name = 'Phase 5: Season Hall of Fame & Awards'
        auto_desc = 'Championship conclusion. Claim diamonds, trophies, and tournament honor.'

    current_phase = override if override in ['ENROLL', 'KNOCKOUT', 'TOP16', 'FINALS', 'AWARDS', 'PREPARE_KNOCKOUT', 'PREPARE_TOP16', 'PREPARE_FINALS'] else auto_phase

    phase_titles = {
        'ENROLL': ('Phase 1: League Enrollment (Mon-Wed 16:30)', 'Sign up and configure your 12 or 36 Pokemon tournament roster. Knockouts start Wednesday 17:30.'),
        'PREPARE_KNOCKOUT': ('Registration Closed (Knockouts at 17:30)', 'Matchmaker opens at 17:30 today for live 6v6 Knockouts.'),
        'KNOCKOUT': ('Phase 2: Live Knockout Battles (Wed 17:30 - 19:30)', 'Queue in 1-minute matchmaking! Winner gets +2 points. Top 16 advance to Friday elimination.'),
        'PREPARE_TOP16': ('Top 16 Finalists Seeded', 'Top 16 contenders from Knockouts confirmed. Best of 3 battles start Friday 17:30.'),
        'TOP16': ('Phase 3: Top 16 Elimination (Friday 17:30 - Best of 3)', '16 finalists clash in Best of 3 matches! 8 winners advance to Saturday finals. Spectating available.'),
        'PREPARE_FINALS': ('Top 8 Finalists Confirmed', 'Quarterfinals, Semifinals, and Grand Final commence Saturday 17:30.'),
        'FINALS': ('Phase 4: Top 8 & Grand Championship (Saturday 17:30)', 'Live Quarterfinals, Semifinals & Finals! Battle or spectate live for the League Trophy.'),
        'AWARDS': ('Phase 5: Season Hall of Fame & Awards', 'Championship conclusion. Claim diamonds, trophies, and tournament honor.')
    }

    t_name, t_desc = phase_titles.get(current_phase, (auto_name, auto_desc))

    return {
        'season_id': season_id,
        'phase': current_phase,
        'phase_name': t_name,
        'phase_desc': t_desc,
        'is_overridden': bool(override),
        'timestamp': int(time.time())
    }

def get_division_for_level(level):
    if level <= 59:
        return 1 # Silver League (白银联赛)
    elif level <= 69:
        return 2 # Gold League (黄金联赛)
    else:
        return 3 # Master League (大师联赛)

def get_division_info(div_id):
    info = {
        1: { 'id': 1, 'name': 'Silver League', 'name_cn': '白银联赛', 'min_lv': 1, 'max_lv': 59, 'desc': 'Trainers Level 1 - 59' },
        2: { 'id': 2, 'name': 'Gold League', 'name_cn': '黄金联赛', 'min_lv': 60, 'max_lv': 69, 'desc': 'Trainers Level 60 - 69' },
        3: { 'id': 3, 'name': 'Master League', 'name_cn': '大师联赛', 'min_lv': 70, 'max_lv': 100, 'desc': 'Trainers Level 70+' }
    }
    return info.get(div_id, info[1])

def seed_authentic_tournament_bracket(division):
    sconn = get_server_db()
    c = sconn.cursor()

    existing = c.execute("SELECT COUNT(*) FROM league_brackets WHERE division = ?", (division,)).fetchone()[0]
    if existing > 0:
        sconn.close()
        return

    top_players = c.execute("SELECT username, points FROM league_knockouts WHERE division = ? ORDER BY points DESC, wins DESC LIMIT 16", (division,)).fetchall()
    candidates = []
    for p in top_players:
        ch = c.execute("SELECT level FROM characters WHERE username = ?", (p['username'],)).fetchone()
        lvl = ch['level'] if ch else 50
        lead = c.execute("SELECT pet_id FROM team_pets WHERE username = ? AND slot = 0", (p['username'],)).fetchone()
        pet_id = lead['pet_id'] if lead else 6
        candidates.append({ 'name': p['username'], 'level': lvl, 'pet_id': pet_id })

    div_bots = {
        1: [
            ("Ethan", 58, 157), ("Kris", 57, 160), ("Silver", 59, 154), ("Tyler", 56, 18),
            ("Diana", 55, 121), ("Cal", 57, 68), ("Carrie", 56, 38), ("Brock", 58, 95),
            ("Misty", 58, 121), ("Lt. Surge", 59, 26), ("Erika", 57, 45), ("Sabrina", 59, 65),
            ("Koga", 58, 110), ("Blaine", 59, 78), ("Giovanni", 59, 34), ("Rival Green", 59, 3)
        ],
        2: [
            ("Wally", 68, 282), ("Brendan", 67, 254), ("May", 68, 257), ("Steven", 69, 376),
            ("Wallace", 68, 350), ("Roxanne", 65, 299), ("Brawly", 66, 297), ("Wattson", 67, 310),
            ("Flannery", 68, 323), ("Norman", 69, 289), ("Winona", 67, 334), ("Tate", 68, 337),
            ("Liza", 68, 338), ("Juan", 68, 364), ("Sidney", 69, 359), ("Phoebe", 69, 356)
        ],
        3: [
            ("Red", 88, 6), ("Blue", 87, 9), ("Lance", 85, 149), ("Cynthia", 87, 445),
            ("Leon", 86, 6), ("Ash Ketchum", 88, 25), ("Steven Stone", 86, 376), ("Diantha", 85, 282),
            ("Alder", 84, 637), ("Iris", 85, 612), ("Lucas", 83, 389), ("Dawn", 83, 395),
            ("Barry", 84, 398), ("Volkner", 84, 405), ("Flint", 85, 392), ("Lucian", 85, 437)
        ]
    }

    fill_list = div_bots.get(division, div_bots[1])
    idx = 0
    while len(candidates) < 16 and idx < len(fill_list):
        bname, blvl, bpet = fill_list[idx]
        candidates.append({ 'name': bname, 'level': blvl, 'pet_id': bpet })
        c.execute("INSERT OR IGNORE INTO league_knockouts (username, division, points, wins, losses, matches_played, updated_at) VALUES (?, ?, ?, ?, 0, ?, ?)",
                  (bname, division, max(2, (16 - idx) * 4), 16 - idx, 16 - idx, int(time.time())))
        idx += 1

    top16_winners = []
    for m in range(8):
        p1 = candidates[m]
        p2 = candidates[15 - m]
        s1 = 2
        s2 = random.choice([0, 1])
        winner = p1['name']
        top16_winners.append(p1)
        c.execute("""
            INSERT OR REPLACE INTO league_brackets (division, stage, match_index, player1_name, player1_pet_id, player1_level, player1_score, player2_name, player2_pet_id, player2_level, player2_score, winner_name, status)
            VALUES (?, 'top16', ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'finished')
        """, (division, m, p1['name'], p1['pet_id'], p1['level'], s1, p2['name'], p2['pet_id'], p2['level'], s2, winner))

    top8_winners = []
    for m in range(4):
        p1 = top16_winners[m * 2]
        p2 = top16_winners[m * 2 + 1]
        s1 = 1
        s2 = 0
        winner = p1['name']
        top8_winners.append(p1)
        c.execute("""
            INSERT OR REPLACE INTO league_brackets (division, stage, match_index, player1_name, player1_pet_id, player1_level, player1_score, player2_name, player2_pet_id, player2_level, player2_score, winner_name, status)
            VALUES (?, 'top8', ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'finished')
        """, (division, m, p1['name'], p1['pet_id'], p1['level'], s1, p2['name'], p2['pet_id'], p2['level'], s2, winner))

    semi_winners = []
    for m in range(2):
        p1 = top8_winners[m * 2]
        p2 = top8_winners[m * 2 + 1]
        s1 = 1
        s2 = 0
        winner = p1['name']
        semi_winners.append(p1)
        c.execute("""
            INSERT OR REPLACE INTO league_brackets (division, stage, match_index, player1_name, player1_pet_id, player1_level, player1_score, player2_name, player2_pet_id, player2_level, player2_score, winner_name, status)
            VALUES (?, 'semi', ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'finished')
        """, (division, m, p1['name'], p1['pet_id'], p1['level'], s1, p2['name'], p2['pet_id'], p2['level'], s2, winner))

    p1 = semi_winners[0]
    p2 = semi_winners[1]
    winner = p1['name']
    c.execute("""
        INSERT OR REPLACE INTO league_brackets (division, stage, match_index, player1_name, player1_pet_id, player1_level, player1_score, player2_name, player2_pet_id, player2_level, player2_score, winner_name, status)
        VALUES (?, 'final', 0, ?, ?, ?, 1, ?, ?, ?, 0, ?, 'finished')
    """, (division, p1['name'], p1['pet_id'], p1['level'], p2['name'], p2['pet_id'], p2['level'], winner))

    sconn.commit()
    sconn.close()


class GameServerHandler(http.server.BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        try:
            if sys.stderr:
                sys.stderr.write("%s - - [%s] %s\n" % (self.address_string(), self.log_date_time_string(), format % args))
        except Exception:
            pass
    def _send_json(self, status, data):
        self.send_response(status)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode('utf-8'))

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

        # Original APK Java Updater version check
        if '/kdyg_en' in path or 'version.json' in path:
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({
                "channel": "le8",
                "version": "1.3.0",
                "build": "16238",
                "resource": "2",
                "status": 0
            }).encode('utf-8'))
            return

        # Original APK Native C++ API check
        if 'api.php' in path:
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            resp = {
                "status": 1,
                "msg": "success",
                "data": {
                    "version": "1.3.0",
                    "servers": [
                        {
                            "id": 1,
                            "name": "Server 1: Mythical Elves Global",
                            "ip": "mythical-elves-online.onrender.com",
                            "port": 10000,
                            "status": 1,
                            "is_new": 1
                        }
                    ]
                }
            }
            self.wfile.write(json.dumps(resp).encode('utf-8'))
            return

        # Original APK Notice Webview
        if 'n.html' in path:
            self.send_response(200)
            self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.end_headers()
            html = """<!DOCTYPE html>
<html>
<head><meta charset="utf-8"><title>Notice</title></head>
<body style="background:#16162a;color:#eee;font-family:sans-serif;padding:16px;">
    <h2 style="color:#4ecca3;margin-top:0;">Mythical Elves Authentic Online</h2>
    <p>Welcome Trainer! The dedicated server is running 24/7 online.</p>
    <div style="background:#22223b;border-radius:8px;padding:12px;margin-top:10px;">
        <p><b>Server 1:</b> Mythical Elves Global (<span style="color:#00ff88;">ONLINE</span>)</p>
        <p><b>Events:</b> Master League Tournament, Double EXP Week, Safari Hunt</p>
    </div>
</body>
</html>"""
            self.wfile.write(html.encode('utf-8'))
            return

        if path == '/gm' or path == '/admin':
            gm_path = os.path.join(BASE_DIR, 'gm.html')
            if os.path.exists(gm_path):
                self.send_response(200)
                self.send_header('Content-Type', 'text/html; charset=utf-8')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                with open(gm_path, 'rb') as f:
                    self.wfile.write(f.read())
                return

        if path == '/api/mail/list':
            username = qs.get('username', [None])[0]
            if not username:
                return self._send_json(400, {'success': False, 'error': 'Missing username'})
            sconn = get_server_db()
            mails = [dict(r) for r in sconn.execute("SELECT * FROM player_mails WHERE username = ? ORDER BY mail_id DESC", (username,)).fetchall()]
            sconn.close()
            return self._send_json(200, {'success': True, 'mails': mails})

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

        
        # =====================================================================
        # Authentic Master League (Dashiliansai) GET Endpoints
        # =====================================================================
        if path == '/api/league/info':
            sconn = get_server_db()
            sched = get_league_phase_and_schedule()
            div_id = int(qs.get('division', [1])[0])
            uname = qs.get('username', [''])[0]

            user_div = 1
            user_lvl = 1
            if uname:
                ch = sconn.execute("SELECT level FROM characters WHERE username = ?", (uname,)).fetchone()
                if ch:
                    user_lvl = ch['level']
                    user_div = get_division_for_level(user_lvl)

            target_div = div_id if div_id in [1, 2, 3] else user_div
            div_info = get_division_info(target_div)

            enrolled = False
            roster_count = 0
            if uname:
                enr = sconn.execute("SELECT roster_json FROM league_enrollments WHERE username = ? AND division = ?", (uname, target_div)).fetchone()
                if enr:
                    enrolled = True
                    try:
                        roster = json.loads(enr['roster_json'])
                        roster_count = len(roster)
                    except:
                        roster_count = 0

            tot_enrolled = sconn.execute("SELECT COUNT(*) as cnt FROM league_enrollments WHERE division = ?", (target_div,)).fetchone()['cnt']
            sim_count = max(tot_enrolled, 128 + (target_div * 42))

            user_stats = {'points': 0, 'wins': 0, 'losses': 0, 'matches_played': 0, 'rank': 0}
            if uname:
                ko = sconn.execute("SELECT points, wins, losses, matches_played FROM league_knockouts WHERE username = ? AND division = ?", (uname, target_div)).fetchone()
                if ko:
                    better = sconn.execute("SELECT COUNT(*) as cnt FROM league_knockouts WHERE division = ? AND points > ?", (target_div, ko['points'])).fetchone()['cnt']
                    user_stats = {
                        'points': ko['points'],
                        'wins': ko['wins'],
                        'losses': ko['losses'],
                        'matches_played': ko['matches_played'],
                        'rank': better + 1
                    }

            sconn.close()

            return self._send_json(200, {
                'success': True,
                'schedule': sched,
                'division': div_info,
                'user_level': user_lvl,
                'user_division': user_div,
                'is_enrolled': enrolled,
                'roster_count': roster_count,
                'total_enrolled': sim_count,
                'user_stats': user_stats,
                'server_time': int(time.time())
            })

        if path == '/api/league/knockout/rankings':
            division = int(qs.get('division', [1])[0])
            limit = int(qs.get('limit', [30])[0])

            sconn = get_server_db()
            seed_authentic_tournament_bracket(division)

            rows = sconn.execute("""
                SELECT k.username, k.points, k.wins, k.losses, k.matches_played, c.level, c.title, c.avatar
                FROM league_knockouts k
                LEFT JOIN characters c ON k.username = c.username
                WHERE k.division = ?
                ORDER BY k.points DESC, k.wins DESC, k.matches_played ASC
                LIMIT ?
            """, (division, limit)).fetchall()

            rankings = []
            for idx, r in enumerate(rows, 1):
                lead = sconn.execute("SELECT pet_id FROM team_pets WHERE username = ? ORDER BY slot ASC LIMIT 1", (r['username'],)).fetchone()
                lead_id = lead['pet_id'] if lead else (157 if division==1 else (282 if division==2 else 6))
                rankings.append({
                    'rank': idx,
                    'username': r['username'],
                    'level': r['level'] or (55 if division==1 else (65 if division==2 else 85)),
                    'title': r['title'] or 'League Contender',
                    'avatar': r['avatar'] or 'player/touxiang1.png',
                    'points': r['points'],
                    'wins': r['wins'],
                    'losses': r['losses'],
                    'matches_played': r['matches_played'],
                    'lead_pet_id': lead_id
                })
            sconn.close()

            return self._send_json(200, {
                'success': True,
                'division': division,
                'rankings': rankings
            })

        if path == '/api/league/bracket/16v8':
            division = int(qs.get('division', [1])[0])
            seed_authentic_tournament_bracket(division)

            sconn = get_server_db()
            matches_data = sconn.execute("""
                SELECT match_index, player1_name, player1_pet_id, player1_level, player1_score,
                       player2_name, player2_pet_id, player2_level, player2_score, winner_name, status
                FROM league_brackets
                WHERE division = ? AND stage = 'top16'
                ORDER BY match_index ASC
            """, (division,)).fetchall()
            sconn.close()

            matches = []
            for m in matches_data:
                matches.append({
                    'match_index': m['match_index'],
                    'player1': { 'name': m['player1_name'], 'pet_id': m['player1_pet_id'], 'level': m['player1_level'], 'score': m['player1_score'] },
                    'player2': { 'name': m['player2_name'], 'pet_id': m['player2_pet_id'], 'level': m['player2_level'], 'score': m['player2_score'] },
                    'winner_name': m['winner_name'],
                    'status': m['status']
                })

            return self._send_json(200, {
                'success': True,
                'division': division,
                'stage': 'top16',
                'matches': matches
            })

        if path == '/api/league/bracket/top8':
            division = int(qs.get('division', [1])[0])
            seed_authentic_tournament_bracket(division)

            sconn = get_server_db()
            all_b = sconn.execute("""
                SELECT stage, match_index, player1_name, player1_pet_id, player1_level, player1_score,
                       player2_name, player2_pet_id, player2_level, player2_score, winner_name, status
                FROM league_brackets
                WHERE division = ? AND stage IN ('top8', 'semi', 'final')
                ORDER BY stage, match_index ASC
            """, (division,)).fetchall()
            sconn.close()

            top8_list = []
            semi_list = []
            final_match = None
            champion = None

            for m in all_b:
                obj = {
                    'match_index': m['match_index'],
                    'player1': { 'name': m['player1_name'], 'pet_id': m['player1_pet_id'], 'level': m['player1_level'], 'score': m['player1_score'] },
                    'player2': { 'name': m['player2_name'], 'pet_id': m['player2_pet_id'], 'level': m['player2_level'], 'score': m['player2_score'] },
                    'winner_name': m['winner_name'],
                    'status': m['status']
                }
                if m['stage'] == 'top8':
                    top8_list.append(obj)
                elif m['stage'] == 'semi':
                    semi_list.append(obj)
                elif m['stage'] == 'final':
                    final_match = obj
                    champion = {
                        'name': m['winner_name'],
                        'pet_id': m['player1_pet_id'] if m['winner_name'] == m['player1_name'] else m['player2_pet_id'],
                        'level': m['player1_level'] if m['winner_name'] == m['player1_name'] else m['player2_level'],
                        'trophy_title': 'Grand League Champion'
                    }

            return self._send_json(200, {
                'success': True,
                'division': division,
                'top8': top8_list,
                'semi': semi_list,
                'final': final_match,
                'champion': champion
            })

        if path == '/api/league/spectate':
            division = int(qs.get('division', [1])[0])
            stage = qs.get('stage', ['top16'])[0]
            match_index = int(qs.get('match_index', [0])[0])

            sconn = get_server_db()
            m = sconn.execute("""
                SELECT player1_name, player1_pet_id, player1_level, player1_score,
                       player2_name, player2_pet_id, player2_level, player2_score, winner_name
                FROM league_brackets
                WHERE division = ? AND stage = ? AND match_index = ?
            """, (division, stage, match_index)).fetchone()
            sconn.close()

            if not m:
                return self._send_json(404, { 'success': False, 'error': 'Match not found' })

            events = [
                { 'turn': 1, 'attacker': m['player1_name'], 'pet_id': m['player1_pet_id'], 'move': 'Thunderbolt', 'damage': 1840, 'text': f"{m['player1_name']}'s Pokemon unleashed Thunderbolt!" },
                { 'turn': 2, 'attacker': m['player2_name'], 'pet_id': m['player2_pet_id'], 'move': 'Hydro Pump', 'damage': 1720, 'text': f"{m['player2_name']}'s Pokemon counter-attacked with Hydro Pump!" },
                { 'turn': 3, 'attacker': m['player1_name'], 'pet_id': m['player1_pet_id'], 'move': 'Dragon Claw', 'damage': 2150, 'text': f"{m['player1_name']}'s Pokemon executed critical Dragon Claw!" },
                { 'turn': 4, 'attacker': m['player1_name'], 'pet_id': m['player1_pet_id'], 'move': 'Hyper Beam', 'damage': 3400, 'text': f"{m['winner_name']} secured victory with a decisive Hyper Beam!" }
            ]

            return self._send_json(200, {
                'success': True,
                'division': division,
                'stage': stage,
                'match_index': match_index,
                'player1': { 'name': m['player1_name'], 'pet_id': m['player1_pet_id'], 'level': m['player1_level'], 'score': m['player1_score'] },
                'player2': { 'name': m['player2_name'], 'pet_id': m['player2_pet_id'], 'level': m['player2_level'], 'score': m['player2_score'] },
                'winner_name': m['winner_name'],
                'events': events
            })

        self._send_json(404, { 'success': False, 'error': 'Endpoint not found' })

    # =========================================================================
    # POST Requests
    # =========================================================================
    def do_POST(self):
        parsed = urlparse(self.path)
        path = parsed.path
        body = self._read_body()

        # Original APK API POST requests (appversion, pay, receive)
        if 'api.php' in path:
            return self._send_json(200, { 'status': 1, 'msg': 'success' })

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
                        exp = COALESCE(?, exp),
                        gold = COALESCE(?, gold),
                        diamonds = COALESCE(?, diamonds),
                        stamina = COALESCE(?, stamina),
                        combat_power = COALESCE(?, combat_power),
                        stage_id = COALESCE(?, stage_id),
                        vip_level = COALESCE(?, vip_level)
                    WHERE username = ? AND server_id = ?
                """, (
                    p.get('name'), p.get('level'), p.get('exp'), p.get('gold'),
                    p.get('diamonds'), p.get('stamina'), p.get('combatPower'), p.get('stageId'),
                    p.get('vipLevel'), uname, server_id
                ))

            # Team Pets Sync
            team = body.get('team', [])
            if isinstance(team, list) and team:
                sconn.execute("DELETE FROM team_pets WHERE username = ? AND server_id = ?", (uname, server_id))
                for idx, pet in enumerate(team):
                    puid = pet.get('uid') or f'{uname}_pet_{idx}'
                    sconn.execute("""
                        INSERT OR REPLACE INTO team_pets (
                            pet_uid, username, server_id, slot, pet_id, name, level, exp,
                            cur_hp, max_hp, atk, def, spatk, spdef, speed, star, breakthrough_stage,
                            iv_hp, iv_atk, iv_def, iv_spatk, iv_spdef, iv_speed,
                            ev_hp, ev_atk, ev_def, ev_spatk, ev_spdef, ev_speed,
                            nature, skill_lv_0, skill_lv_1, skill_lv_2, skill_lv_3,
                            held_item_id, berry_item_id
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        puid, uname, server_id, idx, pet.get('id', 1), pet.get('name', 'Pet'),
                        pet.get('level', 1), pet.get('exp', 0), pet.get('currentHp', 100),
                        pet.get('maxHp', 100), pet.get('atk', 50), pet.get('def', 50),
                        pet.get('spatk', 50), pet.get('spdef', 50), pet.get('speed', 50),
                        pet.get('star', 1), pet.get('breakthroughStage', 0),
                        pet.get('ivHp', 15), pet.get('ivAtk', 15), pet.get('ivDef', 15),
                        pet.get('ivSpAtk', 15), pet.get('ivSpDef', 15), pet.get('ivSpeed', 15),
                        pet.get('evHp', 0), pet.get('evAtk', 0), pet.get('evDef', 0),
                        pet.get('evSpAtk', 0), pet.get('evSpDef', 0), pet.get('evSpeed', 0),
                        pet.get('nature', 'Hardy'),
                        pet.get('skill_lv_0', 1), pet.get('skill_lv_1', 1), pet.get('skill_lv_2', 1), pet.get('skill_lv_3', 1),
                        pet.get('heldItemId', 0), pet.get('berryItemId', 0)
                    ))

            # Box Pets Sync (PC Storage)
            box = body.get('box', [])
            if isinstance(box, list):
                sconn.execute("DELETE FROM box_pets WHERE username = ? AND server_id = ?", (uname, server_id))
                for idx, pet in enumerate(box):
                    puid = pet.get('uid') or f'{uname}_box_{idx}'
                    sconn.execute("""
                        INSERT OR REPLACE INTO box_pets (
                            pet_uid, username, server_id, box_page, box_slot, pet_id, name, level, exp,
                            cur_hp, max_hp, atk, def, spatk, spdef, speed, star, breakthrough_stage,
                            iv_hp, iv_atk, iv_def, iv_spatk, iv_spdef, iv_speed,
                            ev_hp, ev_atk, ev_def, ev_spatk, ev_spdef, ev_speed,
                            nature, skill_lv_0, skill_lv_1, skill_lv_2, skill_lv_3,
                            held_item_id, berry_item_id
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        puid, uname, server_id, idx // 30, idx % 30, pet.get('id', 1), pet.get('name', 'Pet'),
                        pet.get('level', 1), pet.get('exp', 0), pet.get('currentHp', 100),
                        pet.get('maxHp', 100), pet.get('atk', 50), pet.get('def', 50),
                        pet.get('spatk', 50), pet.get('spdef', 50), pet.get('speed', 50),
                        pet.get('star', 1), pet.get('breakthroughStage', 0),
                        pet.get('ivHp', 15), pet.get('ivAtk', 15), pet.get('ivDef', 15),
                        pet.get('ivSpAtk', 15), pet.get('ivSpDef', 15), pet.get('ivSpeed', 15),
                        pet.get('evHp', 0), pet.get('evAtk', 0), pet.get('evDef', 0),
                        pet.get('evSpAtk', 0), pet.get('evSpDef', 0), pet.get('evSpeed', 0),
                        pet.get('nature', 'Hardy'),
                        pet.get('skill_lv_0', 1), pet.get('skill_lv_1', 1), pet.get('skill_lv_2', 1), pet.get('skill_lv_3', 1),
                        pet.get('heldItemId', 0), pet.get('berryItemId', 0)
                    ))

            # Bag Sync
            bag = body.get('bag', {})
            if isinstance(bag, dict):
                sconn.execute("DELETE FROM bag_items WHERE username = ? AND server_id = ?", (uname, server_id))
                for item_id, count in bag.items():
                    if int(count) > 0:
                        sconn.execute("""
                            INSERT OR REPLACE INTO bag_items (username, server_id, item_id, count)
                            VALUES (?, ?, ?, ?)
                        """, (uname, server_id, int(item_id), int(count)))

            sconn.commit()
            sconn.close()
            return self._send_json(200, { 'success': True, 'message': 'Cloud progress synced successfully' })

        # if path == '/api/pet/feed_candy':
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

        
        # =====================================================================
        # Authentic Master League (Dashiliansai) POST Endpoints
        # =====================================================================
        if path == '/api/league/enroll':
            uname = body.get('username')
            division = int(body.get('division', 1))
            roster = body.get('roster', [])

            if not uname:
                return self._send_json(400, { 'success': False, 'error': 'Missing username' })

            sched = get_league_phase_and_schedule()
            if sched['phase'] not in ['ENROLL'] and not sched['is_overridden']:
                return self._send_json(400, { 'success': False, 'error': 'Registration is currently closed for this phase' })

            sconn = get_server_db()
            ch = sconn.execute("SELECT level FROM characters WHERE username = ?", (uname,)).fetchone()
            if not ch:
                sconn.close()
                return self._send_json(404, { 'success': False, 'error': 'Character not found' })

            lvl = ch['level']
            req_div = get_division_for_level(lvl)
            if division != req_div:
                d_req = get_division_info(req_div)
                sconn.close()
                return self._send_json(400, { 'success': False, 'error': f"Your trainer level ({lvl}) qualifies for {d_req['name']} only" })

            now_ts = int(time.time())
            roster_str = json.dumps(roster)
            sconn.execute("""
                INSERT OR REPLACE INTO league_enrollments (username, division, trainer_level, roster_json, enrolled_at)
                VALUES (?, ?, ?, ?, ?)
            """, (uname, division, lvl, roster_str, now_ts))

            sconn.execute("""
                INSERT OR IGNORE INTO league_knockouts (username, division, points, wins, losses, matches_played, updated_at)
                VALUES (?, ?, 0, 0, 0, 0, ?)
            """, (uname, division, now_ts))

            sconn.commit()
            sconn.close()

            return self._send_json(200, {
                'success': True,
                'message': 'Successfully enrolled in Master League!',
                'division': division,
                'roster_count': len(roster)
            })

        if path == '/api/league/knockout/match':
            uname = body.get('username')
            division = int(body.get('division', 1))

            sched = get_league_phase_and_schedule()
            if sched['phase'] not in ['KNOCKOUT'] and not sched['is_overridden']:
                return self._send_json(400, { 'success': False, 'error': 'Knockout matchmaking is not currently active' })

            sconn = get_server_db()
            opp_row = sconn.execute("""
                SELECT username FROM league_knockouts
                WHERE division = ? AND username != ?
                ORDER BY RANDOM() LIMIT 1
            """, (division, uname)).fetchone()

            opp_name = opp_row['username'] if opp_row else None
            opp_pets = []
            opp_lvl = 55 if division==1 else (65 if division==2 else 85)

            if opp_name:
                ch = sconn.execute("SELECT level, avatar, title FROM characters WHERE username = ?", (opp_name,)).fetchone()
                if ch:
                    opp_lvl = ch['level']
                tp = sconn.execute("SELECT pet_id, name, level, cur_hp, max_hp, atk, def, spatk, spdef, speed FROM team_pets WHERE username = ? ORDER BY slot ASC LIMIT 6", (opp_name,)).fetchall()
                for p in tp:
                    opp_pets.append({
                        'pet_id': p['pet_id'],
                        'name': p['name'],
                        'level': p['level'],
                        'hp': p['cur_hp'] or p['max_hp'],
                        'max_hp': p['max_hp'],
                        'attack': p['atk'],
                        'defense': p['def'],
                        'sp_attack': p['spatk'],
                        'sp_defense': p['spdef'],
                        'speed': p['speed']
                    })

            sconn.close()

            if len(opp_pets) < 6:
                div_pools = {
                    1: [
                        (157, 'Typhlosion'), (160, 'Feraligatr'), (154, 'Meganium'), (18, 'Pidgeot'),
                        (26, 'Raichu'), (121, 'Starmie'), (95, 'Onix'), (68, 'Machamp'), (65, 'Alakazam')
                    ],
                    2: [
                        (282, 'Gardevoir'), (254, 'Sceptile'), (257, 'Blaziken'), (260, 'Swampert'),
                        (376, 'Metagross'), (350, 'Milotic'), (289, 'Slaking'), (334, 'Altaria'), (359, 'Absol')
                    ],
                    3: [
                        (6, 'Charizard'), (9, 'Blastoise'), (3, 'Venusaur'), (149, 'Dragonite'),
                        (445, 'Garchomp'), (25, 'Pikachu'), (448, 'Lucario'), (150, 'Mewtwo'), (384, 'Rayquaza')
                    ]
                }
                pool = div_pools.get(division, div_pools[1])
                chosen = random.sample(pool, 6)
                if not opp_name:
                    div_names = {
                        1: ['Silver Contender Ethan', 'Ace Trainer Tyler', 'Gym Leader Misty', 'Gym Leader Brock'],
                        2: ['Veteran Brendan', 'Elite Trainer May', 'Champion Steven', 'Gym Leader Wallace'],
                        3: ['Master Champion Red', 'Dragon Master Lance', 'Sinnoh Champion Cynthia', 'Galar Champion Leon']
                    }
                    opp_name = random.choice(div_names.get(division, ['League Rival']))

                opp_pets = []
                for p_id, p_name in chosen:
                    base_hp = opp_lvl * 55 + random.randint(100, 300)
                    opp_pets.append({
                        'pet_id': p_id,
                        'name': p_name,
                        'level': opp_lvl,
                        'hp': base_hp,
                        'max_hp': base_hp,
                        'attack': opp_lvl * 14 + random.randint(20, 60),
                        'defense': opp_lvl * 12 + random.randint(20, 50),
                        'sp_attack': opp_lvl * 15 + random.randint(20, 60),
                        'sp_defense': opp_lvl * 12 + random.randint(20, 50),
                        'speed': opp_lvl * 13 + random.randint(20, 50)
                    })

            return self._send_json(200, {
                'success': True,
                'opponent': {
                    'name': opp_name,
                    'level': opp_lvl,
                    'avatar': 'player/touxiang2.png',
                    'title': 'League Knockout Challenger',
                    'pets': opp_pets
                }
            })

        if path == '/api/league/knockout/result':
            uname = body.get('username')
            division = int(body.get('division', 1))
            victory = bool(body.get('victory', False))

            if not uname:
                return self._send_json(400, { 'success': False, 'error': 'Missing username' })

            points_gain = 2 if victory else 0
            wins_gain = 1 if victory else 0
            loss_gain = 0 if victory else 1
            now_ts = int(time.time())

            sconn = get_server_db()
            sconn.execute("""
                INSERT INTO league_knockouts (username, division, points, wins, losses, matches_played, updated_at)
                VALUES (?, ?, ?, ?, ?, 1, ?)
                ON CONFLICT(username, division) DO UPDATE SET
                    points = points + ?,
                    wins = wins + ?,
                    losses = losses + ?,
                    matches_played = matches_played + 1,
                    updated_at = ?
            """, (uname, division, points_gain, wins_gain, loss_gain, now_ts, points_gain, wins_gain, loss_gain, now_ts))

            row = sconn.execute("SELECT points, wins, losses, matches_played FROM league_knockouts WHERE username = ? AND division = ?", (uname, division)).fetchone()
            better = sconn.execute("SELECT COUNT(*) as cnt FROM league_knockouts WHERE division = ? AND points > ?", (division, row['points'])).fetchone()['cnt']
            rank = better + 1

            sconn.commit()
            sconn.close()

            return self._send_json(200, {
                'success': True,
                'points_earned': points_gain,
                'total_points': row['points'],
                'wins': row['wins'],
                'losses': row['losses'],
                'matches_played': row['matches_played'],
                'current_rank': rank
            })

        if path == '/api/league/set_phase':
            new_phase = body.get('phase', '').strip().upper()
            valid = ['', 'ENROLL', 'PREPARE_KNOCKOUT', 'KNOCKOUT', 'PREPARE_TOP16', 'TOP16', 'PREPARE_FINALS', 'FINALS', 'AWARDS']
            if new_phase not in valid:
                return self._send_json(400, { 'success': False, 'error': f'Invalid phase. Choose from {valid}' })

            sconn = get_server_db()
            sconn.execute("UPDATE league_state SET phase_override = ?, updated_at = ? WHERE id = 1", (new_phase, int(time.time())))
            sconn.commit()
            sconn.close()

            sched = get_league_phase_and_schedule()
            return self._send_json(200, {
                'success': True,
                'message': f"League phase successfully set to: {sched['phase']}",
                'schedule': sched
            })

        if path == '/api/mail/claim':
            username = body.get('username')
            mail_id = body.get('mail_id')
            if not username or not mail_id:
                return self._send_json(400, {'success': False, 'error': 'Missing username or mail_id'})
            sconn = get_server_db()
            mail = sconn.execute("SELECT * FROM player_mails WHERE mail_id = ? AND username = ? AND claimed = 0", (mail_id, username)).fetchone()
            if not mail:
                sconn.close()
                return self._send_json(404, {'success': False, 'error': 'Mail not found or already claimed'})
            
            sconn.execute("UPDATE characters SET gold = gold + ?, diamonds = diamonds + ? WHERE username = ?", (mail['gold'], mail['diamonds'], username))
            if mail['pet_id'] > 0:
                sconn.execute("""INSERT INTO team_pets (username, server_id, slot, pet_id, name, level, exp, cur_hp, max_hp, atk, def, spatk, spdef, speed, star, breakthrough_stage, iv_hp, iv_atk, iv_def, iv_spatk, iv_spdef, iv_speed)
                                 VALUES (?, 1, 3, ?, ?, ?, 99999, 999, 999, 500, 350, 650, 350, 480, 5, 13, 31, 31, 31, 31, 31, 31)""",
                              (username, mail['pet_id'], mail['pet_name'] or 'Mewtwo', mail['pet_level']))
            sconn.execute("UPDATE player_mails SET claimed = 1 WHERE mail_id = ?", (mail_id,))
            sconn.commit()
            sconn.close()
            return self._send_json(200, {'success': True, 'message': 'Rewards claimed successfully!'})

        if path == '/api/gm/send_gift':
            target = body.get('target', 'all')
            title = body.get('title', 'Game Master Gift')
            content = body.get('content', 'Here is a special reward from the Game Master!')
            gold = int(body.get('gold', 0))
            diamonds = int(body.get('diamonds', 0))
            pet_id = int(body.get('pet_id', 0))
            pet_name = body.get('pet_name', '')
            pet_level = int(body.get('pet_level', 100))
            now_ts = int(time.time())

            sconn = get_server_db()
            if target == 'all':
                users = [r['username'] for r in sconn.execute("SELECT username FROM characters").fetchall()]
            else:
                users = [target]

            for u in users:
                sconn.execute("""INSERT INTO player_mails (username, title, content, sender, gold, diamonds, pet_id, pet_name, pet_level, created_at)
                                 VALUES (?, ?, ?, 'Game Master Krishna', ?, ?, ?, ?, ?, ?)""",
                              (u, title, content, gold, diamonds, pet_id, pet_name, pet_level, now_ts))
            sconn.commit()
            sconn.close()
            return self._send_json(200, {'success': True, 'message': f'Gift successfully sent to {len(users)} player(s)!'})

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

    # Start Authentic Protobuf TCP Gateway on Port 9911
    try:
        from gateway import run_tcp_gateway_server
        gw_ip = os.environ.get('GATEWAY_IP', '0.0.0.0')
        t_gw = threading.Thread(target=run_tcp_gateway_server, kwargs={'host': '0.0.0.0', 'port': 9911, 'server_ip': gw_ip}, daemon=True)
        t_gw.start()
        with open(os.path.join(BASE_DIR, 'server_startup.log'), 'a') as f:
            f.write(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] TCP Gateway thread started on port 9911\n")
    except Exception as e:
        with open(os.path.join(BASE_DIR, 'server_startup.log'), 'a') as f:
            f.write(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] TCP Gateway error: {e}\n")

    # Start Auxiliary HTTP listeners for native APK (ports 80, 888, 8082)
    for sec_port in [80, 888, 8082]:
        try:
            sec_server = ThreadedHTTPServer(('0.0.0.0', sec_port), GameServerHandler)
            threading.Thread(target=sec_server.serve_forever, daemon=True).start()
            with open(os.path.join(BASE_DIR, 'server_startup.log'), 'a') as f:
                f.write(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Auxiliary HTTP active on port {sec_port}\n")
        except Exception as e:
            with open(os.path.join(BASE_DIR, 'server_startup.log'), 'a') as f:
                f.write(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Auxiliary port {sec_port} skipped: {e}\n")

    server = ThreadedHTTPServer(('0.0.0.0', PORT), GameServerHandler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print('\nServer stopping...')
        server.server_close()
