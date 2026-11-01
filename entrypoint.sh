#!/bin/bash
set -e

echo "[Entrypoint] Starting Mythical Elves Dedicated Game Server..."
python -u server.py &
SERVER_PID=$!

echo "[Entrypoint] Waiting for server sockets to initialize..."
sleep 3

echo "[Entrypoint] Starting bore public tunnels to bore.pub..."
(while true; do
    echo "[Bore-9911] Connecting..."
    bore local 9911 --to bore.pub --port 9911 || true
    echo "[Bore-9911] Disconnected. Reconnecting in 3s..."
    sleep 3
done) &

(while true; do
    echo "[Bore-8088] Connecting..."
    bore local 8088 --to bore.pub --port 8088 || true
    echo "[Bore-8088] Disconnected. Reconnecting in 3s..."
    sleep 3
done) &

echo "[Entrypoint] All background services active. Waiting on server process..."
wait $SERVER_PID
