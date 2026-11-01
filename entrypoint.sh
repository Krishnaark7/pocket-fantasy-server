#!/bin/bash
echo "[Entrypoint] Starting bore public TCP tunnels to bore.pub..."
bore local 9911 --to bore.pub --port 9911 &
bore local 8088 --to bore.pub --port 8088 &
echo "[Entrypoint] Starting Mythical Elves Game Server..."
exec python -u server.py
