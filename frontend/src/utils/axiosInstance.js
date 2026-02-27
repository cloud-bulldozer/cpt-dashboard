import { showFailureToast, showToast } from "@/actions/toastActions";

import { BASE_URL } from "./apiConstants";
import { extractErrorMessage } from "./errorUtils";
import axios from "axios";
import store from "@/store/store";

const axiosInstance = axios.create({
  baseURL: BASE_URL,
  responseType: "json",
});

// Show toasts for all HTTP error status codes (400-599)
const getStatusCodeErrorTitle = (status) => {
  switch (status) {
    case 400:
      return "Bad Request";
    case 401:
      return "Unauthorized";
    case 402:
      return "Payment Required";
    case 403:
      return "Forbidden";
    case 404:
      return "Not Found";
    case 405:
      return "Method Not Allowed";
    case 406:
      return "Not Acceptable";
    case 408:
      return "Request Timeout";
    case 409:
      return "Conflict";
    case 410:
      return "Gone";
    case 413:
      return "Payload Too Large";
    case 415:
      return "Unsupported Media Type";
    case 422:
      return "Validation Error";
    case 429:
      return "Too Many Requests";
    case 500:
      return "Internal Server Error";
    case 501:
      return "Not Implemented";
    case 502:
      return "Bad Gateway";
    case 503:
      return "Service Unavailable";
    case 504:
      return "Gateway Timeout";
    case 505:
      return "HTTP Version Not Supported";
    default:
      return status >= 400 && status < 500 ? "Client Error" : "Server Error";
  }
};

axiosInstance.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response) {
      const { data, status } = error.response;
      let extractedMessage = null;
      
      const responseMessage = extractErrorMessage(data, status);
      // Use the response message if available, otherwise fall back to axios message
      extractedMessage = responseMessage || error.message;
      
      
      //Display error message or fallback
      if (extractedMessage) {
        const title = getStatusCodeErrorTitle(status);
        store.dispatch(showToast("danger", title, extractedMessage));
      } else {
        const title = status >= 500 ? "Server Error" : "Request Error";
        const message = status >= 500 
          ? "The server encountered an error. Please try again later."
          : "There was an issue with your request. Please check your input and try again.";
        store.dispatch(showToast("danger", title, message));
      }
    } else if (error.request) {
      //For errors with no response data
      store.dispatch(showToast(
        "danger", 
        "Network Error", 
        "Unable to connect to the server. Please check your internet connection and try again."
      ));
    } else {
      // Something else went wrong
      store.dispatch(showFailureToast());
    }
    
    return Promise.reject(error);
  }
);

export default axiosInstance;
