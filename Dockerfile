FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends wget ca-certificates && \
    wget https://github.com/ekzhang/bore/releases/download/v0.5.1/bore-v0.5.1-x86_64-unknown-linux-musl.tar.gz -O /tmp/bore.tar.gz && \
    tar -xzf /tmp/bore.tar.gz -C /usr/local/bin/ && \
    rm /tmp/bore.tar.gz && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY data/ ./data/
COPY descriptors/ ./descriptors/
COPY gateway.py ./
COPY gm.html ./
COPY server.py ./
COPY entrypoint.sh ./
RUN chmod +x entrypoint.sh

EXPOSE 8088 10000 9911
ENV PORT=10000
ENV PYTHONUNBUFFERED=1

CMD ["./entrypoint.sh"]
