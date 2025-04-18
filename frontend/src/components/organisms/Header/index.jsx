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
import { useEffect } from "react";
import { useDispatch, useSelector } from "react-redux";

import { BarsIcon } from "@patternfly/react-icons";
import logo from "@/assets//logo.png";
import { toggleSideMenu } from "@/actions/sideMenuActions";
import VersionWidget from "@/components/atoms/VersionWidget";
import { fetchAggregatorVersion } from "@/actions/headerActions";

const Header = () => {
  const isSideMenuOpen = useSelector((state) => state.sidemenu.isSideMenuOpen);
  const updatedTime = useSelector((state) => state.header.updatedTime);
  const dispatch = useDispatch();
  const onSidebarToggle = () => {
    dispatch(toggleSideMenu(!isSideMenuOpen));
  };

  useEffect(() => {
    dispatch(fetchAggregatorVersion());
  }, [dispatch]);

  return (
    <Masthead>
      <MastheadToggle>
        <PageToggleButton
          variant="plain"
          aria-label="Global navigation"
          isSidebarOpen={isSideMenuOpen}
          onSidebarToggle={onSidebarToggle}
          id="nav-toggle"
          ouiaId="main_layout_toggle"
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
        <div className="meta-items">
          <div className="name">CPT Dashboard</div>
          <div>{updatedTime && <div>Last Updated: {updatedTime}</div>}</div>
          <VersionWidget />
        </div>
      </MastheadContent>
    </Masthead>
  );
};

export default Header;
