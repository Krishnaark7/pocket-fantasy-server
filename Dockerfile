FROM python:3.11-slim

WORKDIR /app

# Install sqlite3 support (included in standard python:3.11-slim)
COPY data/ ./data/
COPY server.py ./

EXPOSE 8088
ENV PORT=8088

# Run unbuffered for real-time cloud logging
CMD ["python", "-u", "server.py"]
