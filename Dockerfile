FROM node:20-alpine
WORKDIR /app
COPY package.json ./
COPY server.js ./
EXPOSE 8088
ENV PORT=8088
CMD ["node", "server.js"]
