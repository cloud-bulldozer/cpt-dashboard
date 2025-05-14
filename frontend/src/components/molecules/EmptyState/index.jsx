import {
  EmptyState,
  EmptyStateBody,
  EmptyStateHeader,
  EmptyStateIcon,
} from "@patternfly/react-core";

import PropTypes from "prop-types";
import SearchIcon from "@patternfly/react-icons/dist/esm/icons/search-icon";

const msgToShow = {
  noData: "No data found for the selected date range.",
  noFilterData: "No results match the filter criteria.",
};
const CustomEmptyState = ({ type }) => (
  <EmptyState ouiaId="custom_empty_state">
    <EmptyStateHeader
      titleText="No results found"
      headingLevel="h4"
      icon={<EmptyStateIcon icon={SearchIcon} />}
    />
    <EmptyStateBody>{msgToShow[type]}</EmptyStateBody>
  </EmptyState>
);

CustomEmptyState.propTypes = {
  type: PropTypes.string,
};

export default CustomEmptyState;
