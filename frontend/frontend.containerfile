FROM node:18-bookworm-slim AS builder

WORKDIR /usr/src/cpt-dashboard
COPY public/ public/
COPY src/ src/
COPY index.html index.html
COPY vite.config.js vite.config.js
COPY jsconfig.json jsconfig.json
ADD package*.json ./
RUN npm clean-install
RUN npm run build

FROM nginxinc/nginx-unprivileged:1.27-alpine

RUN \
    # 1) remove any stale PID so NGINX can create a fresh one at startup \
    rm -f /var/cache/nginx/nginx.pid && \
    # 2) force the cache dir to be owned by nginx:root (GID 0) \
    chown -R nginx:0 /var/cache/nginx && \
    # 3) grant group-write so any UID in GID 0 can create/delete files \
    chmod -R g+w /var/cache/nginx && \
    # 4) setgid so new files inherit GID 0 (root) \
    chmod g+s /var/cache/nginx

USER root
RUN touch /var/cache/nginx/nginx.pid && \
  chown nginx:root /var/cache/nginx/nginx.pid && \
  chmod 664 /var/cache/nginx/nginx.pid

USER nginx
COPY --chown=nginx:root --from=builder /usr/src/cpt-dashboard/dist/ /usr/share/nginx/html/
COPY --chown=nginx:root nginx.conf /etc/nginx/nginx.conf
# RUN touch /tmp/nginx.pid 


# RUN touch /var/cache/nginx/nginx.pid
EXPOSE 3000

ENTRYPOINT ["nginx"]
CMD ["-g", "daemon off;"]
