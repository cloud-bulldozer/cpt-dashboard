
# Openshift Performance Dashbaord

## Dashboard directory structure

### [`src`](src/)

The CPT Dashboard Javascript source plus additional CSS/LESS and artifacts.

#### [`src/assets`](src/assets/)

Assets placed in the `src/assets/images` directory are only referenced within component or layout definitions and are packaged in the generated `***.js` file during the build process.

#### [`src/modules`](src/modules/)

`modules` directory has all containers (patent layouts) and components (react components).

#### [`src/utils`](src/utils/)

The `utils` directory has all helper/utility scripts.

#### [`src/reducers`](src/reducers)

Contains functions that manage store via actions 

## Cloning and Running the Application Locally 

- Install [Node.js](https://nodejs.org) 
- Clone the [CPT Dashboard code](https://github.com/cloud-bulldozer/cpt-dashboard) to a local file system
- Install all the npm packages

Type the following command to install all npm packages 

```bash
$ npm install
```

In order to run the application use the following command 

```bash
$ npm run dev
```

The application runs on http://localhost:3000 in the default browser.

## Build

To build the application run the following command

```bash
$ npm run build
```
This will generate the `build` folder in the root directory, which contains packaged files such as `***.js`, `***.css`, and `index.html`.

Then, copy the `build` folder to the proper place on the server for deployment.

## Test

### Component Tests

#### Requirements
- Starting directory is the project root
- NodeJS 22+

Install JavaScript dependencies.

```shell
npm --prefix frontend install
```

Execute Cypress tests of React Components.

```shell
npm --prefix frontend run cypress:cp
```


### E2E Tests

#### Requirements
- Three shell terminals
- Starting directory is the project root
- Podman, Docker
- NodeJS 22+

Start CPT-Dashboard backend data service end-to-end test dependency.
```shell
./backend/e2e_backend.sh
```

Start frontend GUI server and execute end-to-end tests.
```shell
npm --prefix frontend run cypress:run:ci
```

#### Interactive E2E Test Execution

Start CPT-Dashboard backend data service end-to-end test dependency.
```shell
./backend/e2e_backend.sh
```

Start CPT-Dashboard frontend GUI.
```shell
npm --prefix frontend run dev
```

[Open Cypress](https://docs.cypress.io/app/core-concepts/open-mode) GUI to view test execution.
```shell
npm --prefix frontend run cypress:open
```
Click `E2E Testing`.

Choose a browser (Chrome is recommended), and click `Start E2E Testing in {your browser}`.

In the newly opened web browser under the directory `cypress/e2e` select a test file. Each individual `.cy.js` file is a `spec` file. I recommend clicking `home.cy.js`, or `ocp.cy.js`.


## Template

This application is based on v5 of PatternFly which is a production-ready UI solution for admin interfaces. For more information regarding the foundation and template of the application, please visit [PatternFly](https://www.patternfly.org/get-started/develop) 

## Resources

- [Vite](https://vitejs.dev/guide/)   

- [ReactJS](https://reactjs.org/) 

- [React-Redux](https://github.com/reduxjs/react-redux)
