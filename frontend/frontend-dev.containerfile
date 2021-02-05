FROM node:14.15.4-alpine3.12

RUN mkdir /app
WORKDIR /app

COPY package.json /app
COPY src/ /app/src
COPY public/ /app/public

ARG FRONTEND_ENV=dev

ENV REACT_APP_ENV=${FRONTEND_ENV}

RUN yarn install

CMD ["yarn", "start"]

