import "@patternfly/react-core/dist/styles/base.css";
import "./index.css";

import App from "./App.jsx";
import { Provider } from "react-redux";
import ReactDOM from "react-dom/client";
import store from "./store/store";

ReactDOM.createRoot(document.getElementById("root")).render(
  <Provider store={store}>
    <App />
  </Provider>
);
