import HomeReducer from "./homeReducer";
import LoadingReducer from "./loadingReducer";
import SideMenuReducer from "./sideMenuReducer";
import ToastReducer from "./toastReducer";
import { combineReducers } from "redux";

export default combineReducers({
  loading: LoadingReducer,
  toast: ToastReducer,
  sidemenu: SideMenuReducer,
  cpt: HomeReducer,
});
