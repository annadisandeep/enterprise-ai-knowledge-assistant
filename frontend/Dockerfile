# ============================================================================
# Frontend container — Enterprise AI Knowledge Assistant (Vite + React + TS)
# ----------------------------------------------------------------------------
# Build context is the `frontend/` directory:
#   docker build -t knowledge-frontend ./frontend
#
# Two stages:
#   1) node:20-alpine  -> install deps and produce the static `dist/` bundle.
#   2) nginx:1.27-alpine -> serve that bundle as a tiny static web server.
#
# VITE_API_BASE_URL is a BUILD-TIME value (Vite inlines it into the JS bundle).
# Default "/api" assumes the frontend is served behind a proxy/host that routes
# /api to the backend. For Cloud Run (separate services) pass the backend URL,
# e.g. --build-arg VITE_API_BASE_URL=https://backend-xxxx.run.app/api
# ============================================================================

# ---- Stage 1: build the static bundle ----
FROM node:20-alpine AS build
WORKDIR /app

# Install dependencies first (cached unless package manifests change).
COPY package*.json ./
RUN npm ci

# Copy the rest of the source and build.
COPY . .

# Inject the API base URL into the build. Must be set BEFORE `npm run build`
# because Vite reads VITE_* variables at build time and inlines them.
ARG VITE_API_BASE_URL=/api
ENV VITE_API_BASE_URL=${VITE_API_BASE_URL}
RUN npm run build

# ---- Stage 2: serve with nginx ----
FROM nginx:1.27-alpine AS runtime

# Replace the default server block with our SPA-aware config (listens on 8080,
# falls back to index.html for client-side routing, adds security headers).
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Ship only the compiled static assets (no node_modules, no source).
COPY --from=build /app/dist /usr/share/nginx/html

# Cloud Run expects the container to listen on $PORT (8080). nginx.conf listens
# on 8080 to match. (The stock nginx image listens on 80 — we override it.)
EXPOSE 8080

# Simple health check: the root document should return 200.
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD wget --quiet --tries=1 --spider http://localhost:8080/ || exit 1

# NOTE on non-root: running nginx fully as non-root requires rewriting pid/temp
# paths and granting write access to several dirs, which is fiddly. For a
# portfolio/static server we keep the stock entrypoint (master as root, workers
# drop to the unprivileged `nginx` user). To go fully rootless, switch to the
# `nginxinc/nginx-unprivileged:1.27-alpine` image (already listens on 8080).
CMD ["nginx", "-g", "daemon off;"]
