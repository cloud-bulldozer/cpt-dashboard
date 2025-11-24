import * as CONSTANTS from "@/assets/constants/SidemenuConstants";

import { Nav, NavItem, NavList } from "@patternfly/react-core";
import {
  maintainQueryString,
  setActiveItem,
  setFromSideMenuFlag,
} from "@/actions/sideMenuActions";
import { useDispatch, useSelector } from "react-redux";
import { useLocation, useNavigate } from "react-router-dom";

import { useEffect } from "react";

const sideMenuOptions = [
  {
    id: CONSTANTS.HOME_NAV,
    key: "home",
    displayName: "Home",
    type: "cpt",
  },
  {
    id: CONSTANTS.OCP_NAV,
    key: "ocp",
    displayName: "OCP",
    type: "ocp",
  },
  {
    id: CONSTANTS.TELCO_NAV,
    key: "telco",
    displayName: "Telco",
    type: "telco",
  },
  {
    id: CONSTANTS.OLS_NAV,
    key: "ols",
    displayName: "OLS",
    type: "ols",
  },
  {
    id: CONSTANTS.QUAY_NAV,
    key: "quay",
    displayName: "Quay",
    type: "quay",
  },
  {
    id: CONSTANTS.ILAB_NAV,
    key: "ilab",
    displayName: "ILAB",
    type: "ilab",
  },
  {
    id: CONSTANTS.RHOSO_NAV,
    key: "oso",
    displayName: "RHOSO",
    type: "oso",
  },
];

const MenuOptions = () => {
  const dispatch = useDispatch();
  const navigate = useNavigate();
  const { pathname } = useLocation();
  const activeMenuItem = useSelector((state) => state.sidemenu.activeMenuItem);

  const onSelect = (_event, item) => {
    dispatch(setActiveItem(item.itemId));
  };

  const onSideMenuNavigation = (toPage, type) => {
    dispatch(setFromSideMenuFlag(true));
    dispatch(maintainQueryString(toPage, type, navigate));
  };
  useEffect(() => {
    if (pathname !== "/") {
      const currPath = pathname.replace(/^.*[/]([^/]+)[/]*$/, "$1");

      dispatch(setActiveItem(currPath));
    }
  }, [dispatch, pathname]);

  return (
    <>
      <Nav onSelect={onSelect} ouiaId="side_menu_options">
        <NavList>
          {sideMenuOptions.map((option) => {
            return (
              <NavItem
                key={option.key}
                itemId={option.id}
                isActive={activeMenuItem === option.id}
                onClick={() => onSideMenuNavigation(option.key, option.type)}
              >
                {option.displayName}
              </NavItem>
            );
          })}
        </NavList>
      </Nav>
    </>
  );
};

export default MenuOptions;
