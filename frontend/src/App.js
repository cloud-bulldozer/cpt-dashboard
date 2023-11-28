import React, {useEffect} from 'react';
import '@patternfly/react-core/dist/styles/base.css';

import {
    Page,
    PageSection,
    PageSectionVariants,
} from '@patternfly/react-core';
import {fetchOCPJobsData, fetchCPTJobsData} from "./store/Actions/ActionCreator";
import {useDispatch} from "react-redux";
import {Route, Switch, BrowserRouter as Router} from "react-router-dom";
import {NavBar} from "./components/NavBar/NavBar";
import {HomeView} from "./components/Home/HomeView";
import {OCPHome} from './components/OCP/OCPHome';


export const App = () => {
    const dispatch = useDispatch()

    useEffect(() => {
          const fetchData = async () =>{
              await dispatch(fetchOCPJobsData())
              await dispatch(fetchCPTJobsData())
          }
          fetchData()
    }, [dispatch])




  return (
      <Router>
        <Page
          header={<NavBar />}
          groupProps={{
            stickyOnBreakpoint: { default: 'top' },
            sticky: 'top'
          }}
        >
          <PageSection variant={PageSectionVariants.light} hasOverflowScroll={true} aria-label={"overflow false"}>
              <Switch>
                  <Route path="/"><HomeView /></Route>
                  <Route path="/home"><HomeView /></Route>
                  <Route path="/ocp"><OCPHome /></Route>
              </Switch>
          </PageSection>
        </Page>
      </Router>
  );
};

export default App
