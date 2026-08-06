# ---- Stage 1: Build ----
FROM node:20-alpine AS builder

WORKDIR /app

COPY package.json ./
RUN npm install

COPY . .
RUN npm run build

# ---- Stage 2: Serve ----
FROM nginx:alpine-slim

# TODO [BACKEND/DEPLOY]: Add an nginx config with `try_files $uri /index.html`
# for BrowserRouter and a narrowly scoped /api reverse proxy. Do not cache booking
# responses; immutable hashed assets may be cached long-term.
COPY --from=builder /app/dist /usr/share/nginx/html

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
