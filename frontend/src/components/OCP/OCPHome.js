

import '../css/PlatformView.css';
import "@patternfly/react-core/dist/styles/base.css";
import React from 'react';
import {
    Page,
    PageSection,
    PageSectionVariants,
    PageSidebar,
    PageSidebarBody
} from "@patternfly/react-core";
import {DataDisplayView} from "./DataDisplayView";
import {TopView} from "./TopView";
import {SidePaneView} from "./SidePaneView";


export function OCPHome() {

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
