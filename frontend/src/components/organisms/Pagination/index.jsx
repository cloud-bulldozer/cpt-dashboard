import { Pagination, PaginationVariant } from "@patternfly/react-core";
import {
  fetchNextJobs,
  setPage,
  setPageOptions,
  sliceTableRows,
} from "@/actions/paginationActions";

import PropTypes from "prop-types";
import { useCallback } from "react";
import { useDispatch } from "react-redux";

const RenderPagination = (props) => {
  const dispatch = useDispatch();

  const perPageOptions = [
    { title: "10", value: 10 },
    { title: "25", value: 25 },
    { title: "50", value: 50 },
    { title: "100", value: 100 },
  ];

  const onSetPage = useCallback(
    (_evt, newPage, _perPage, startIdx, endIdx) => {
      dispatch(setPage(newPage, props.type));

      dispatch(sliceTableRows(startIdx, endIdx, props.type));
    },
    [dispatch, props.type]
  );
  const onPerPageSelect = useCallback(
    (_evt, newPerPage, newPage, startIdx, endIdx) => {
      dispatch(setPageOptions(newPage, newPerPage, props.type));

      dispatch(sliceTableRows(startIdx, endIdx, props.type));
    },
    [dispatch, props.type]
  );

  const checkAndFetch = (_evt, newPage) => {
    if (props.type === "ilab") {
      dispatch(fetchNextJobs(newPage));
    }
  };
  return (
    <Pagination
      itemCount={props?.items}
      widgetId="pagination"
      perPage={props.perPage}
      page={props.page}
      variant={PaginationVariant.bottom}
      onNextClick={checkAndFetch}
      perPageOptions={perPageOptions}
      onSetPage={onSetPage}
      onPerPageSelect={onPerPageSelect}
      onPageInput={checkAndFetch}
    />
  );
};

RenderPagination.propTypes = {
  page: PropTypes.number,
  perPage: PropTypes.number,
  type: PropTypes.string,
  items: PropTypes.number,
};
export default RenderPagination;
