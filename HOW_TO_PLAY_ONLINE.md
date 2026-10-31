# 🎮 Pocket Fantasy — 24/7 Dedicated Online Multiplayer Game Server

Welcome to the **Pocket Fantasy Dedicated Online Multiplayer Game Server**!
This server provides a complete, persistent backend directly backed by the game's authentic SQLite databases (`Bag.db` with 70 tables and `server.db`).

It runs **24/7 in the background** on your computer with automatic startup on boot, allowing you and your friends to play online continuously, level up, catch Pokémon, cultivate and evolve monsters, sweep stages, and duel in real-time PvP!

---

## ⚡ 1. 24/7 Persistent Server Service

The server is configured to run silently in the background with zero terminal windows required:

- **Installed Background Startup Script**:
  `%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup\PocketFantasyServer247.vbs`
  *(Automatically boots and resumes 24/7 whenever your PC turns on)*

- **Check Server Status Anytime**:
  Double-click `check_server_status.py` or run:
  ```powershell
  python check_server_status.py
  ```
  Outputs live latency, online status, registered accounts, active characters, and PVP rooms.

- **To Stop the Server**:
  Double-click `stop_server.bat` (finds and kills the port 8088 process cleanly).

- **To Reinstall / Restart 24/7 Service**:
  Double-click `install_autostart_task.bat`.

---

## 📱 2. How Friends Connect & Play Online

### Step 1: Share the Android Game APK
The signed, production-ready Android APK is located at:
`C:\Users\rajbh\Desktop\POCKET_FANTASY_RESEARCH\08_android_release\PocketFantasy_v1.0.0_Android.apk`

- Send this APK to your friends via Telegram, WhatsApp, Google Drive, or USB.
- Friends install it on their Android smartphones or emulators (LDPlayer, BlueStacks, Nox).

---

### Step 2: Connect to Your 24/7 Server

#### 🌐 Method A: Same Wi-Fi or Mobile Hotspot (Fastest & Zero Lag)
- Your PC's Local Network IP is: **`10.76.68.252`**
- When opening the game on Android or PC:
  1. At the **Login Screen**, tap the server pill at the top right: **`● Server: Online`** (or Offline).
  2. In the **Online Server Configuration** popup, enter:
     ```
     http://10.76.68.252:8088
     ```
  3. Tap **Save & Connect**. The indicator turns green: **`● Online: 15ms`**!

#### 🌍 Method B: Anywhere in the World (Cellular 4G/5G / Remote Internet)
1. In `pocket_fantasy_server`, double-click **`start_tunnel.bat`**.
2. It gives you a public HTTPS address (e.g. `https://pocketfantasy-live.loca.lt`).
3. Share this address with friends anywhere in the world. They paste it into the **Server Configuration** popup in their game.
4. You and your friends can now play together across cities or cellular networks!

---

## ⚔️ 3. How to Battle Friends in Real-Time PvP

1. Both players log in with their own accounts.
2. Go to **Duel (精灵对决)** from the Home City menu.
3. Tap **Practice Match (练习赛)**:
   - **Host (Player 1)**:
     - Tap **Create Room**.
     - A 4-digit room code (e.g., `5829`) is generated and shown.
     - Tell your friend the code.
   - **Challenger (Player 2)**:
     - Open Practice Match. Your friend's room appears in the room lobby with their name and lead Pokémon!
     - Tap **Join** (or enter the 4-digit code).
4. **Live Turn-by-Turn Combat**:
   - Both players enter real-time battle.
   - Every attack, skill choice, switch, and damage calculation is synchronized between both devices in real time.
   - The winner earns ranking points, gold, and climbs the global leaderboard!

---

## 🏛️ 4. Full Authentic Game Systems Implemented

| System | Database Tables Used | Functionality |
| :--- | :--- | :--- |
| **Authentication & Accounts** | `accounts`, `characters` | Username/password registration, auto-guest registration, cloud profiles. |
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
| **World & Legion Chat** | `chat_messages` | Live cross-player chat with avatars, titles, and VIP levels. |
