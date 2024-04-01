import { Pagination, PaginationVariant } from "@patternfly/react-core";

const RenderPagination = (props) => {
  return (
    <Pagination
      itemCount={props?.items}
      widgetId="pagination"
      perPage={props.perPage}
      page={props.page}
      variant={PaginationVariant.bottom}
      perPageOptions={props.perPageOptions}
      onSetPage={props.onSetPage}
      onPerPageSelect={props.onPerPageSelect}
    />
  );
};

export default RenderPagination;
