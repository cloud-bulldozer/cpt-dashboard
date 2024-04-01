import "./index.less";

import { Spinner } from "@patternfly/react-core";

const LoadingComponent = ({ children }) => {
  // const parentClass = isLoading ? "main-with-spinner" : "";
  const isLoading = false;
  const parentClass = "";
  return (
    <div className={`main-page-container ${parentClass}`}>
      {children}
      {isLoading && (
        <div className="spinner-container">
          <Spinner size="md" isSVG className="spinner" />
        </div>
      )}
    </div>
  );
};

export default LoadingComponent;
