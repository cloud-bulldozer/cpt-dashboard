import { Nav, NavItem, NavList } from "@patternfly/react-core";

import React from "react";

const sideMenuOptions = [
  {
    id: 0,
    key: "home",
    displayName: "Home",
  },
  {
    id: 1,
    key: "ocp",
    displayName: "OCP",
  },
  {
    id: 2,
    key: "quay",
    displayName: "Quay",
  },
];

const MenuOptions = () => {
  const [activeItem, setActiveItem] = React.useState(0);
  const onSelect = (_event, itemId) => {
    const item = itemId;
    setActiveItem(item);
  };

  return (
    <>
      <Nav onSelect={onSelect}>
        <NavList>
          {sideMenuOptions.map((option) => {
            return (
              <NavItem
                key={option.key}
                itemId={option.id}
                isActive={activeItem === option.id}
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
