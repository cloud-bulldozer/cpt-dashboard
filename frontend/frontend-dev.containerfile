FROM node:14.15.3-alpine3.12

WORKDIR /app

COPY package.json yarn.lock /app
COPY src/ /app/src
COPY public/ /app/public

ARG FRONTEND_ENV=dev

ENV REACT_APP_ENV=${FRONTEND_ENV}

RUN yarn install

CMD ["yarn", "start"]

