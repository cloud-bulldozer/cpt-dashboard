import React, {useEffect} from 'react';
import '@patternfly/react-core/dist/styles/base.css';

import {
    Page,
    PageSection,
    PageSectionVariants,
} from '@patternfly/react-core';
import {fetchJobsData} from "./store/Actions/ActionCreator";
import {useDispatch} from "react-redux";
import HomeView from "./components/HomeView";
import {Route, Switch, BrowserRouter as Router} from "react-router-dom";
import {NavBar} from "./components/NavBar/NavBar";


export const App = () => {
    const dispatch = useDispatch()

    useEffect(() => {
          const fetchData = async () =>{
              await dispatch(fetchJobsData())
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
              </Switch>
          </PageSection>
        </Page>
      </Router>
  );
};

export default App
