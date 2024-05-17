import { Pagination, PaginationVariant } from "@patternfly/react-core";

const RenderPagination = (props) => {
  const perPageOptions = [
    { title: "25", value: 25 },
    { title: "50", value: 50 },
    { title: "100", value: 100 },
  ];

  return (
    <Pagination
      itemCount={props?.items}
      widgetId="pagination"
      perPage={props.perPage}
      page={props.page}
      variant={PaginationVariant.bottom}
      perPageOptions={perPageOptions}
      onSetPage={props.onSetPage}
      onPerPageSelect={props.onPerPageSelect}
    />
  );
};

export default RenderPagination;
