

import './css/PlatformView.css';
import "@patternfly/react-core/dist/styles/base.css";
import React from 'react';
import {
    Page,
    PageSection,
    PageSectionVariants,
    PageSidebar,
    PageSidebarBody
} from "@patternfly/react-core";
import {DataDisplayView} from "./OCP/DataDisplayView";
import {TopView} from "./OCP/TopView";
import {SidePaneView} from "./OCP/SidePaneView";


export default function HomeView() {

    const sidebar = (
    <PageSidebar theme={"light"}>
      <PageSidebarBody><SidePaneView /></PageSidebarBody>
    </PageSidebar>
  );

  return (
        <Page
            sidebar={sidebar}
            isManagedSidebar
            breadcrumb={<TopView />}
            isBreadcrumbGrouped
            groupProps={{
            stickyOnBreakpoint: { default: 'top' },
            sticky: 'top'
          }}
        >
            <PageSection aria-label={"overflow false"} hasOverflowScroll={true} variant={PageSectionVariants.light} >
             <DataDisplayView />
            </PageSection>
        </Page>
  );
}
