import { showFailureToast, showToast } from "@/actions/toastActions";

import { BASE_URL } from "./apiConstants";
import axios from "axios";
import store from "@/store/store";

const axiosInstance = axios.create({
  baseURL: BASE_URL,
  responseType: "json",
});

axiosInstance.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response) {
      const {
        response: {
          data: { detail },
          status,
        },
      } = error;
      if (status === 400 || status === 404) {
        store.dispatch(showToast("danger", "Error", detail.message));
      } else {
        store.dispatch(
          showToast("danger", "Something went wrong", "Please Try again later")
        );
      }
    } else {
      store.dispatch(showFailureToast());
    }
    return Promise.reject(error);
  }
);

export default axiosInstance;
