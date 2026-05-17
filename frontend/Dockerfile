FROM node:22-alpine

WORKDIR /app

COPY package.json package-lock.json* ./
RUN npm ci

COPY . .

EXPOSE 5173

# --host binds to 0.0.0.0 so the port is reachable from outside the container.
# BACKEND_URL is injected by docker-compose for the Vite proxy target.
CMD ["npm", "run", "dev", "--", "--host"]
