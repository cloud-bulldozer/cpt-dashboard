FROM node:18-buster-slim AS builder

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
COPY --chown=nginx:nginx --from=builder /usr/src/cpt-dashboard/dist /usr/share/nginx/html
RUN touch /tmp/nginx.pid
# RUN chown -R nginx:nginx /tmp/nginx.pid /usr/share/nginx/html /var/cache/nginx /var/log/nginx /etc/nginx/conf.d
USER nginx
EXPOSE 8080

ENTRYPOINT ["nginx"]
CMD ["-g", "daemon off;"]
