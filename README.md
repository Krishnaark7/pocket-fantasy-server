# 🎮 Pocket Fantasy — 24/7 Global Multiplayer Cloud Server

[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy?repo=https://github.com/Krishnaark7/pocket-fantasy-server)

Dedicated high-performance backend server for **Pocket Fantasy**, backed by authentic 70-table SQLite `Bag.db` and persistent `server.db`.

---

## ⚡ 1-Click Cloud Deployment

### Option A: Render (Singapore Region — Ultra-Low Latency in Asia)
Click the button above or:
1. Go to [dashboard.render.com](https://dashboard.render.com/) > **New +** > **Blueprint**.
2. Connect repository: **`Krishnaark7/pocket-fantasy-server`**.
3. Render will read `render.yaml` automatically and configure:
   - **Environment**: Docker
   - **Plan**: Free
   - **Region**: Singapore (lowest latency for India and Southeast Asia)
4. Click **Apply**.
5. Your permanent public server URL will be ready in under 60 seconds (e.g. `https://pocket-fantasy-server.onrender.com`)!

---

### Option B: Koyeb (Mumbai, India Region — 10ms Ping)
1. Go to [app.koyeb.com](https://app.koyeb.com/) > **Create Service**.
2. Select **GitHub** > `Krishnaark7/pocket-fantasy-server`.
3. Choose **Dockerfile** deployment.
4. Select region: **Mumbai (bom)**.
5. Click **Deploy**.

---

## 📡 Live Health Check Endpoint
Once deployed, verify your cloud server anytime at:
`https://<your-service-name>.onrender.com/api/status`

Outputs:
```json
{
  "status": "online",
  "service": "Pocket Fantasy Dedicated Server",
  "version": "1.0.0",
  "registered_accounts": 1,
  "active_characters": 1,
  "active_pvp_rooms": 0
}
```
