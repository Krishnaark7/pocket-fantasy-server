# 🎮 Pocket Fantasy — 24/7 Dedicated Online Multiplayer Game Server

Welcome to the **Pocket Fantasy Dedicated Online Multiplayer Game Server**!
This server provides a complete, persistent backend directly backed by the game's authentic SQLite databases (`Bag.db` with 70 tables and `server.db`), complete with both **Native Google Protobuf TCP Gateway (Port 9911)** and **HTTP REST APIs (Port 8088)**.

The server runs **24/7 silently in the background** on your computer with automatic startup on boot, allowing you and your friends to play online continuously, level up, catch Pokémon, cultivate and evolve monsters, sweep stages, and duel in real-time PvP!

---

## ⚡ 1. 24/7 Persistent Server Status

The server is currently running in the background.

- **Check Server Status Anytime**:
  Double-click `check_server_status.py` or run in terminal:
  ```powershell
  python C:\Users\rajbh\Desktop\POCKET_FANTASY_RESEARCH\pocket_fantasy_server\check_server_status.py
  ```
  **Live Status Output**:
  - `[+] HTTP REST API (Port 8088)`: **ONLINE**
  - `[+] Protobuf TCP Gateway (Port 9911)`: **ONLINE**
  - `[+] GameUpdater API (Port 8088)`: **ONLINE**
  - `[+] Notice Webview (Port 8082)`: **ONLINE**

- **To Stop the Server**:
  Double-click `stop_server.bat` (kills the background process cleanly).

- **To Reinstall / Restart 24/7 Service**:
  Double-click `install_autostart_task.bat`.

---

## 📱 2. Choose Your Android Game APK

Two production-ready, zipaligned and cryptographically signed APKs are ready in:
`C:\Users\rajbh\Desktop\POCKET_FANTASY_RESEARCH\08_android_release\`

### 🌟 Option A: 100% Authentic Original Commercial Game APK (Recommended!)
**File**: `PocketFantasy_Authentic_English_Online.apk` (665.8 MB)
- **What it is**: The exact untouched original English commercial game (`Pokemon EN` v1.3.0, build 16238).
- **Features**: 100% authentic cutscenes, voices, sound effects, Master League tournament brackets, full battle animations, and original menus.
- **Connection**: Zero-shift binary patched to connect directly to your local PC (`10.76.68.252`) and port `9911` over the native Protobuf TCP socket!
- **How to play**: Just install and open! It connects directly to your 24/7 server with zero configuration required.

### 🛠️ Option B: Reconstructed Client APK (with In-Game Server Switcher)
**File**: `PocketFantasy_v1.0.1_Online.apk` (657.0 MB)
- **Features**: Includes the live in-game Server Switcher popup on the login screen. You can enter any IP or public Cloudflare/tunnel URL directly from your phone.
- **Connection**: Connects via HTTP REST on port 8088.

---

## 🌐 3. How Friends Connect & Play Online

### Method 1: Same Wi-Fi or Hotspot (Zero Lag)
- PC Local IP: **`10.76.68.252`**
- Send `PocketFantasy_Authentic_English_Online.apk` to any Android phone on the same Wi-Fi.
- Open the game — it connects to your PC instantly!

### Method 2: Play Anywhere in the World (4G/5G Cellular / Remote Friends)
1. In `pocket_fantasy_server`, double-click **`start_tunnel.bat`**.
2. It generates a public URL (or uses Cloudflare tunnel).
3. Friends using `PocketFantasy_v1.0.1_Online.apk` can tap the **Server Indicator** pill on their login screen and paste the URL.

---

## ⚔️ 4. Full Authentic Game Systems Implemented

| System | Protocol & Database Tables Used | Functionality |
| :--- | :--- | :--- |
| **Authentication & Accounts** | `ClientLogin.proto` (`50001`), `accounts` | Username/password registration, auto-guest registration, cloud profiles. |
| **Server Gateway** | `Protocol.proto` (`10001`, `9911`) | Multi-server routing, server status, latency reporting. |
| **Character State** | `ClientGate.proto` (`50011`, `50012`) | Gold, diamonds, stamina, level, exp, VIP level 10, party Pokémon. |
| **Stamina System** | `characters` | Authentic auto-regeneration (+1 stamina every 300 seconds up to 120 cap). |
| **Pet Cultivation (Level)** | `t_pet_level`, `bag_table` | Feed Small/Medium/Large/XL Exp Rations (245-248) and Rare Candies (20). |
| **Breakthrough (TuPo)** | `pet_break`, `bag_table` | 13 breakthrough stages, level checks, gold and doll material deductions. |
| **Special Training (TeXun)** | `pet_train` | 1 to 5 stars promotion with +5% stat boosts per star. |
| **Species Evolution** | `pet_evolution`, `t_pet` | Level requirements, elemental stones (Fire, Water, Thunder, Leaf), stat metamorphosis. |
| **Adventure Stages & Dungeons** | `t_stage`, `t_drop`, `stage_progress` | Stamina cost, 3-star HP rating, drop rolls, gold/exp awards. |
| **Stage Sweep** | `t_stage`, `bag_items` | Instant multi-clears consuming Sweep Tickets (148) and stamina. |
| **Chapter Star Chests** | `t_box`, `chapter_boxes` | Star threshold checks, milestone diamond and gold rewards. |
| **In-Game Stores** | `t_store_goods`, `bag_table` | 40+ authentic items, potions, balls, candies with coins/diamonds. |
| **Capsule Gacha Machine** | `t_toy_reward`, `t_pet` | Gold and Diamond pulls, 10x SR/SSR pity guarantee, automatic party deposit. |
| **Arena & Rankings** | `t_integral_robot` | 2,000 authentic arena robots + live player leaderboard. |
| **Real-Time Multiplayer PVP** | `active_rooms`, `pvp_matches` | 4-digit room code matchmaking, turn-by-turn synchronization. |
