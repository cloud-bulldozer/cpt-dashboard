import { PageSidebar, PageSidebarBody } from "@patternfly/react-core";

import MenuOptions from "@/components/molecules/SideMenuOptions/index";
import { useSelector } from "react-redux";

const SideMenu = () => {
  const isSideMenuOpen = true;
  return (
    <PageSidebar isSidebarOpen={isSideMenuOpen} id="vertical-sidebar">
      <PageSidebarBody>
        <MenuOptions />
      </PageSidebarBody>
    </PageSidebar>
  );
};

export default SideMenu;
