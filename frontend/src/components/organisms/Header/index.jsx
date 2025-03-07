import "./index.less";

import {
  Brand,
  Masthead,
  MastheadBrand,
  MastheadContent,
  MastheadMain,
  MastheadToggle,
  PageToggleButton,
} from "@patternfly/react-core";
import { useDispatch, useSelector } from "react-redux";

import { BarsIcon } from "@patternfly/react-icons";
import logo from "@/assets//logo.png";
import { toggleSideMenu } from "@/actions/sideMenuActions";

const Header = () => {
  const isSideMenuOpen = useSelector((state) => state.sidemenu.isSideMenuOpen);
  const updatedTime = useSelector((state) => state.header.updatedTime);
  const dispatch = useDispatch();
  const onSidebarToggle = () => {
    dispatch(toggleSideMenu(!isSideMenuOpen));
  };

  return (
    <Masthead>
      <MastheadToggle>
        <PageToggleButton
          variant="plain"
          aria-label="Global navigation"
          isSidebarOpen={isSideMenuOpen}
          onSidebarToggle={onSidebarToggle}
          id="nav-toggle"
        >
          <BarsIcon />
        </PageToggleButton>
      </MastheadToggle>
      <MastheadMain>
        <MastheadBrand href="/">
          <Brand src={logo} className="header-logo" alt="ocp Logo" />
        </MastheadBrand>
      </MastheadMain>
      <MastheadContent>
        CPT Dashboard
        <div className="last-updated-box">
          {updatedTime && <div>Last Updated: {updatedTime}</div>}
        </div>
      </MastheadContent>
    </Masthead>
  );
};

export default Header;
