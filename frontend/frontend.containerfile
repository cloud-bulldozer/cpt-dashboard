# pull official base image
FROM node:alpine

RUN mkdir /app
WORKDIR /app



COPY . /app


RUN yarn install
EXPOSE 3000

RUN chown node /app
USER node

# start app
CMD ["yarn", "run", "start"]