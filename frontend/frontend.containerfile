# pull official base image
FROM docker.io/library/node:16.20.2-alpine3.18

RUN mkdir /app


COPY . /app
WORKDIR /app

RUN yarn install
RUN yarn add react-scripts
ENV PATH="${PATH}:/app/node_modules/.bin/react-scripts"

EXPOSE 3000

RUN chown -R node /app
USER node

# start app
CMD ["yarn", "run", "start"]
