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

FROM docker.io/nginxinc/nginx-unprivileged:1.27-alpine
COPY --chown=nginx:nginx --from=builder /usr/src/cpt-dashboard/dist/ /usr/share/nginx/html/
COPY --chown=nginx:nginx nginx.conf /etc/nginx/nginx.conf
RUN touch /tmp/nginx.pid

USER nginx
EXPOSE 3000

ENTRYPOINT ["nginx"]
CMD ["-g", "daemon off;"]
