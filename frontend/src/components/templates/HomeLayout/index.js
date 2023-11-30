import '../../css/PlatformView.css';
import "@patternfly/react-core/dist/styles/base.css";
import React from 'react';
import {
    Page,
    PageSection,
    PageSectionVariants,
    PageSidebar,
    PageSidebarBody
} from "@patternfly/react-core";
import {TopLayout} from "./TopLayout";
import {SidebarLayout} from "./SidebarLayout";
import {DisplayTableDataLayout} from "./DisplayTableDataLayout";

export function HomeLayout({topHeadersData, sidebarComponents, initialState, tableData, tableMetaData,
                               addExpandableRows=false, expandableComponent}) {

    const sidebar = (
        <PageSidebar theme={"light"}>
          <PageSidebarBody><SidebarLayout  sidebarComponents={sidebarComponents}/></PageSidebarBody>
        </PageSidebar>
  );

  return (
        <Page
            sidebar={sidebar}
            isManagedSidebar
            breadcrumb={<TopLayout topHeadersData={topHeadersData} />}
            isBreadcrumbGrouped
            groupProps={{
            stickyOnBreakpoint: { default: 'top' },
            sticky: 'top'
          }}
        >
            <PageSection aria-label={"overflow false"} hasOverflowScroll={true} variant={PageSectionVariants.light} >
                <DisplayTableDataLayout tableMetaData={tableMetaData}
                                        initialState={initialState}
                                        tableData={tableData}
                                        expandableComponent={expandableComponent}
                                        addExpandableRows={addExpandableRows}
                />
            </PageSection>
        </Page>
  );
}
