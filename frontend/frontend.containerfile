# pull official base image
FROM docker.io/library/node:15.9.0-alpine3.13

RUN mkdir /app


COPY . /app
WORKDIR /app

RUN yarn install
EXPOSE 3000

RUN chown -R node /app
USER node

# start app
CMD ["yarn", "run", "start"]