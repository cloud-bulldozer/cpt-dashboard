import { PageSidebar, PageSidebarBody } from "@patternfly/react-core";

import MenuOptions from "@/components/molecules/SideMenuOptions/index";
import { useSelector } from "react-redux";

const SideMenu = () => {
  const isSideMenuOpen = useSelector((state) => state.sidemenu.isSideMenuOpen);

  return (
    <PageSidebar isSidebarOpen={isSideMenuOpen} id="vertical-sidebar"      
    >
      <PageSidebarBody>
        <MenuOptions />
      </PageSidebarBody>
    </PageSidebar>
  );
};

export default SideMenu;
