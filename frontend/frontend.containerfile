FROM node:14.15.3-alpine3.12 AS build

RUN mkdir /app
WORKDIR /app

COPY package.json yarn.lock /app
COPY src/ /app/src
COPY public/ /app/public

RUN yarn install
RUN yarn build

FROM nginx:1.19.6
COPY ./nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/build /usr/share/nginx/html