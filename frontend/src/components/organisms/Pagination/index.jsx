import { Pagination, PaginationVariant } from "@patternfly/react-core";
import {
  checkTableData,
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
    { title: "25", value: 25 },
    { title: "50", value: 50 },
    { title: "100", value: 100 },
  ];

  const onSetPage = useCallback(
    (_evt, newPage, _perPage, startIdx, endIdx) => {
      dispatch(setPage(newPage, props.type));
      dispatch(checkTableData(newPage, props.type));
      dispatch(sliceTableRows(startIdx, endIdx, props.type));
    },
    [dispatch, props.type]
  );
  const onPerPageSelect = useCallback(
    (_evt, newPerPage, newPage, startIdx, endIdx) => {
      dispatch(setPageOptions(newPage, newPerPage, props.type));
      dispatch(checkTableData(newPage, props.type));
      dispatch(sliceTableRows(startIdx, endIdx, props.type));
    },
    [dispatch, props.type]
  );

  const onNextClick = useCallback(
    (_evt, newPage) => {
      dispatch(checkTableData(newPage, props.type));
    },
    [dispatch, props.type]
  );

  return (
    <Pagination
      itemCount={props?.items}
      widgetId="pagination"
      perPage={props.perPage}
      page={props.page}
      variant={PaginationVariant.bottom}
      perPageOptions={perPageOptions}
      onSetPage={onSetPage}
      onPerPageSelect={onPerPageSelect}
      onNextClick={onNextClick}
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
