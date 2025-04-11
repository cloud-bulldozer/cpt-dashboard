FROM cypress/browsers:22.14.0

WORKDIR /usr/src/cpt-dashboard

# A wildcard is used to ensure both package.json AND package-lock.json are copied
# where available (npm@5+)
COPY package*.json ./

RUN npm install

COPY . .

EXPOSE 3000

CMD ["npm", "run", "cypress:run:ci"]
