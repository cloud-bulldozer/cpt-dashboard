import {
  Alert,
  AlertActionCloseButton,
  AlertGroup,
  AlertVariant,
} from "@patternfly/react-core";
import { useDispatch, useSelector } from "react-redux";

import { hideToast } from "@/actions/toastActions";
import "./index.less";

const ToastComponent = () => {
  const { alerts } = useSelector((state) => state.toast);
  const dispatch = useDispatch();

  const removeToast = (key) => {
    dispatch(hideToast(key));
  };

  // Different timeout durations based on alert type
  const getTimeoutDuration = (variant) => {
    switch (variant) {
      case 'success':
        return 2500; // Success messages can disappear quickly
      case 'info':
        return 3000; // Info messages - standard duration
      case 'warning':
        return 4000; // Warnings need a bit more time
      case 'danger':
        return 4500; // Error messages need more time to read
      default:
        return 3000; // Default fallback
    }
  };
  return (
    <AlertGroup isToast className="fast-fade-toast-group">
      {alerts.map((item) => (
        <Alert
          variant={AlertVariant[item.variant]}
          title={item.title}
          key={item.key}
          timeout={getTimeoutDuration(item.variant)}
          onTimeout={() => removeToast(item.key)}
          className="fast-fade-toast"
          actionClose={
            <AlertActionCloseButton
              title={item.title}
              variantLabel={`${item.variant} alert`}
              onClose={() => removeToast(item.key)}
            />
          }
        >
          {item?.message &&
            item?.message.split("\n").map((i) => {
              return <p key={i}>{i}</p>;
            })}
        </Alert>
      ))}
    </AlertGroup>
  );
};

export default ToastComponent;
