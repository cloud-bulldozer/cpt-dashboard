import {
  Button,
  Menu,
  MenuContent,
  MenuItem,
  MenuList,
  Title,
} from "@patternfly/react-core";

import PropTypes from "prop-types";
import { fetchMultiGraphData } from "@/actions/ilabActions.js";
import { uid } from "@/utils/helper";
import { useDispatch } from "react-redux";
import { useState } from "react";

const IlabCompareComponent = (props) => {
  const { data } = props;

  const dispatch = useDispatch();
  const [selectedItems, setSelectedItems] = useState([]);
  const onSelect = (_event, itemId) => {
    const item = itemId;
    if (selectedItems.includes(item)) {
      setSelectedItems(selectedItems.filter((id) => id !== item));
    } else {
      setSelectedItems([...selectedItems, item]);
    }
  };
  return (
    <div className="comparison-container">
      <div className="metrics-container">
        <Title headingLevel="h3" className="title">
          Metrics
        </Title>
        <Button
          className="compare-btn"
          isDisabled={selectedItems.length < 2}
          isBlock
          onClick={() => dispatch(fetchMultiGraphData(selectedItems))}
        >
          Comapre
        </Button>
        {/* <List isPlain isBordered>
          {data.map((item) => {
            return (
              // <ListItem ></ListItem>
              <Checkbox
                key={uid()}
                isLabelWrapped
                label={item.primary_metrics[0]}
              />
            );
          })}
          
        </List> */}
        <Menu onSelect={onSelect} selected={selectedItems}>
          <MenuContent>
            <MenuList>
              {data.map((item) => {
                return (
                  <MenuItem
                    key={uid()}
                    hasCheckbox
                    itemId={item.id}
                    isSelected={selectedItems.includes(item.id)}
                  >
                    {item.primary_metrics[0]}
                  </MenuItem>
                );
              })}
            </MenuList>
          </MenuContent>
        </Menu>
      </div>

      <Title headingLevel="h3" className="title">
        Chart
      </Title>
    </div>
  );
};

IlabCompareComponent.propTypes = {
  data: PropTypes.array,
};
export default IlabCompareComponent;
