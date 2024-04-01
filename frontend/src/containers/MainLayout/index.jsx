import "./index.less";

import { Outlet, useNavigate } from "react-router-dom";
import { Page, PageSection, PageSectionVariants } from "@patternfly/react-core";

import Header from "@/components/organisms/Header";
import LoadingComponent from "@/components/organisms/LoadingComponent";
import SideMenu from "@/components/organisms/SideMenu";

const MainLayout = () => {
  const navigate = useNavigate();

  return (
    <>
      <Page header={<Header />} sidebar={<SideMenu />}>
        <PageSection variant={PageSectionVariants.light} isCenterAligned>
          <LoadingComponent>
            <Outlet context={navigate} />
          </LoadingComponent>
        </PageSection>
      </Page>
    </>
  );
};

export default MainLayout;
