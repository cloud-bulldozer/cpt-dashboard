# ─────────────────────────────────────────────────────────────────────────────
# Stage 1: build your React/Vite app
# ─────────────────────────────────────────────────────────────────────────────
FROM node:18-bookworm-slim AS builder

WORKDIR /usr/src/cpt-dashboard

# Install dependencies first so we can leverage Docker cache
COPY package*.json ./
RUN npm clean-install

# Copy source and build
COPY public/ public/
COPY src/    src/
COPY index.html vite.config.js jsconfig.json ./
RUN npm run build


# ─────────────────────────────────────────────────────────────────────────────
# Stage 2: runtime with unprivileged NGINX
# ─────────────────────────────────────────────────────────────────────────────
FROM docker.io/nginxinc/nginx-unprivileged:1.27-alpine

# 1) Become root so we can fix ownership and create the PID file
USER root

RUN \
  # On OpenShift’s Restricted SCC the container runs as an arbitrary UID in GID=0,  \
  # and under Podman it runs as nginx UID=101—so ensure the cache dir and PID file \
  # are owned by nginx user and root group with group-write/setgid for both cases. \
  mkdir -p  /var/cache/nginx && \
  chown -R nginx:root  /var/cache/nginx && \
  chmod -R g+w  /var/cache/nginx && \
  chmod g+s  /var/cache/nginx && \
  \
  # remove any stale PID and pre-create a group-writable PID file owned by nginx:root, \
  # ensuring Podman’s nginx user and OpenShift’s arbitrary UID (in GID=0) can write \
  rm -f  /var/cache/nginx/nginx.pid && \
  touch  /var/cache/nginx/nginx.pid && \
  chown nginx:root  /var/cache/nginx/nginx.pid && \
  chmod u=rw,g=rw,o=r  /var/cache/nginx/nginx.pid

# 2) Copy in your custom config and the built assets, with nginx ownership
COPY --chown=nginx:root nginx.conf /etc/nginx/nginx.conf
COPY --chown=nginx:root --from=builder /usr/src/cpt-dashboard/dist/ /usr/share/nginx/html/

# 3) Drop back to the unprivileged user
USER nginx

EXPOSE 3000
ENTRYPOINT ["nginx"]
CMD ["-g", "daemon off;"]
