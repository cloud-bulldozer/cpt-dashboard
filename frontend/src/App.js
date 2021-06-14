import React from "react";
import {
  BrowserRouter as Router,
  Switch,
  Route,
  Link
} from "react-router-dom";
import PlatformView from './components/Platform/PlatformView';
import { Nav, NavItem, NavList, PageHeader } from '@patternfly/react-core';
import {
  Page,
  PageHeaderTools,
  PageSection,
  PageSectionVariants
} from '@patternfly/react-core';

export default function App() {
  const logoProps = {
    href: 'https://patternfly.org',
    onClick: () => console.log('clicked logo'),
    target: '_blank'
  };

  const PerfNav = (

    <Nav variant="horizontal">
      <NavList>
        <NavItem>
          <Link to="/">Home</Link>
        </NavItem>
        <NavItem>
          <Link to="/platform">Platform</Link>
        </NavItem>
        <NavItem>
          <Link to="/releases">Releases</Link>
        </NavItem>
      </NavList>
    </Nav>

  );

  const Header = (
    <PageHeader className="OCPPerformance-header"
      logo={<img className="OCPPerformance-logo" src="logo.png" alt="Openshift Logo" />}
      logoProps={logoProps}
      headerTools={<PageHeaderTools>Openshift Performance and Scale</PageHeaderTools>}
      topNav={PerfNav}
    />

  );
  return (
    <>
      <Router>
        <Page header={Header}>
          <PageSection variant={PageSectionVariants.light}>
            <Switch>
              <Route path="/releases">
                <About />
              </Route>
              <Route path="/platform">
                <PlatformView />
              </Route>
              <Route path="/">
                <Home />
              </Route>
            </Switch>

          </PageSection>
        </Page>
      </Router>
    </>
  );
}

function Home() {
  return <h2>Home</h2>;
}

function About() {
  return <h2>About</h2>;
}

