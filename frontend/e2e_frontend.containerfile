FROM docker.io/cypress/browsers:22.14.0

WORKDIR /usr/src/cpt-dashboard

# A wildcard is used to ensure both package.json AND package-lock.json are copied
# where available (npm@5+)
COPY package*.json ./

RUN npm install

COPY . .

ENTRYPOINT ["npm"]

CMD ["run", "cypress:run:ci"]
