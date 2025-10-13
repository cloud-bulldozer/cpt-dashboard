import "react-date-picker/dist/DatePicker.css";
import "react-calendar/dist/Calendar.css";

import {
  Toolbar,
  ToolbarContent,
  ToolbarItem,
  Button,
} from "@patternfly/react-core";
import { useState } from "react";
import DatePicker from "react-date-picker";
import PropTypes from "prop-types";
import { formatDate } from "@/utils/helper";

const KPIDateFilter = ({ startDate, endDate, onDateChange, onApply }) => {
  const [localStartDate, setLocalStartDate] = useState(
    startDate ? new Date(startDate) : null,
  );
  const [localEndDate, setLocalEndDate] = useState(
    endDate ? new Date(endDate) : null,
  );

  const handleStartDateChange = (date) => {
    setLocalStartDate(date);
    if (onDateChange) {
      onDateChange(
        date ? formatDate(date) : null,
        localEndDate ? formatDate(localEndDate) : null,
      );
    }
  };

  const handleEndDateChange = (date) => {
    setLocalEndDate(date);
    if (onDateChange) {
      onDateChange(
        localStartDate ? formatDate(localStartDate) : null,
        date ? formatDate(date) : null,
      );
    }
  };

  const handleApply = () => {
    if (onApply) {
      onApply(
        localStartDate ? formatDate(localStartDate) : null,
        localEndDate ? formatDate(localEndDate) : null,
      );
    }
  };

  const handleClear = () => {
    setLocalStartDate(null);
    setLocalEndDate(null);
    if (onDateChange) {
      onDateChange(null, null);
    }
    if (onApply) {
      onApply(null, null);
    }
  };

  return (
    <Toolbar id="kpi-date-filter-toolbar" ouiaId="kpi_date_filter">
      <ToolbarContent className="date-filter">
        <ToolbarItem variant="label">Date Range:</ToolbarItem>
        <ToolbarItem>
          <DatePicker
            onChange={handleStartDateChange}
            clearIcon={null}
            value={localStartDate}
            placeholder="Start Date"
          />
        </ToolbarItem>
        <ToolbarItem variant="label" className="to-text">
          to
        </ToolbarItem>
        <ToolbarItem>
          <DatePicker
            onChange={handleEndDateChange}
            minDate={localStartDate}
            clearIcon={null}
            value={localEndDate}
            placeholder="End Date"
          />
        </ToolbarItem>
        <ToolbarItem>
          <Button variant="primary" onClick={handleApply}>
            Apply
          </Button>
        </ToolbarItem>
        <ToolbarItem>
          <Button variant="secondary" onClick={handleClear}>
            Clear
          </Button>
        </ToolbarItem>
      </ToolbarContent>
    </Toolbar>
  );
};

KPIDateFilter.propTypes = {
  startDate: PropTypes.string,
  endDate: PropTypes.string,
  onDateChange: PropTypes.func,
  onApply: PropTypes.func.isRequired,
};

export default KPIDateFilter;
