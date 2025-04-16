import "./index.less";

import { Card, CardFooter, CardTitle } from "@patternfly/react-core";

import PropTypes from "prop-types";

const MetricCard = (props) => {
  return (
    <Card
      ouiaId={props.title}
      className="card-class"
      onClick={() => props.clickHandler()}
    >
      <CardTitle className="title">{props.title}</CardTitle>
      <CardFooter>{props.footer}</CardFooter>
    </Card>
  );
};

MetricCard.propTypes = {
  title: PropTypes.string,
  footer: PropTypes.number,
  clickHandler: PropTypes.func,
};
export default MetricCard;
