FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy authentic databases, binary protobuf descriptors, and server logic
COPY data/ ./data/
COPY descriptors/ ./descriptors/
COPY gateway.py ./
COPY gm.html ./
COPY server.py ./

# Expose HTTP port (10000 / 8088) and Protobuf Gateway port (9911)
EXPOSE 8088 10000 9911
ENV PORT=10000
ENV PYTHONUNBUFFERED=1

# Run unbuffered for real-time cloud logging
CMD ["python", "-u", "server.py"]
