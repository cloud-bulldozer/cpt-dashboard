import { showFailureToast, showToast } from "@/actions/toastActions";

import { BASE_URL } from "./apiConstants";
import axios from "axios";
import store from "@/store/store";

const axiosInstance = axios.create({
  baseURL: BASE_URL,
  responseType: "json",
});

/**
 * Enhanced error handler for different FastAPI error response formats:
 * 1. {"detail": [{"type": "...", "loc": [...], "msg": "..."}]} - FastAPI validation errors (422)
 * 2. {"detail": {"message": "..."}} - explicit HTTPException with message object
 * 3. {"detail": {"error": "..."}} - explicit HTTPException with error object
 * 4. {"detail": "..."} - FastAPI unhandled exceptions or HTTPException with string detail
 * 5. {"error": "..."} - some response formats
 * 6. Non-JSON responses or malformed responses
 */
const extractErrorMessage = (data) => {
  try {
    // Handle different error response formats
    if (data && typeof data === 'object') {
      // Case 1: FastAPI validation errors - {"detail": [{"type": "...", "loc": [...], "msg": "..."}]}
      if (data.detail && Array.isArray(data.detail) && data.detail.length > 0) {
        const validationErrors = data.detail.map(error => {
          if (error.msg) {
            // Include field location if available for better context
            const fieldPath = error.loc && Array.isArray(error.loc) && error.loc.length > 1 
              ? ` (${error.loc.slice(1).join('.')})` // Skip first element which is usually 'query' or 'body'
              : '';
            return `${error.msg}${fieldPath}`;
          }
          return 'Validation error';
        });
        
        // Combine multiple validation errors into a readable message
        if (validationErrors.length === 1) {
          return validationErrors[0];
        } else {
          return `Multiple validation errors: ${validationErrors.join(', ')}`;
        }
      }
      
      // Case 2: {"detail": {"message": "..."}}
      if (data.detail && typeof data.detail === 'object' && !Array.isArray(data.detail) && data.detail.message) {
        return data.detail.message;
      }
      
      // Case 3: {"detail": {"error": "..."}}
      if (data.detail && typeof data.detail === 'object' && !Array.isArray(data.detail) && data.detail.error) {
        return data.detail.error;
      }
      
      // Case 4: {"detail": "..."} - string detail
      if (data.detail && typeof data.detail === 'string') {
        return data.detail;
      }
      
      // Case 4: {"error": "..."} - direct error key
      if (data.error && typeof data.error === 'string') {
        return data.error;
      }
      
      // Case 5: Try to find any message-like field
      if (data.message && typeof data.message === 'string') {
        return data.message;
      }
    }
    
    // If we can't extract a message, return null to use fallback
    return null;
  } catch (e) {
    // If any parsing fails, return null to use fallback
    console.warn('Error parsing error response:', e);
    return null;
  }
};

const getStatusCodeErrorTitle = (status) => {
  switch (status) {
    case 400:
      return "Bad Request";
    case 401:
      return "Unauthorized";
    case 403:
      return "Forbidden";
    case 404:
      return "Not Found :(";
    case 422:
      return "Validation Error";
    case 500:
      return "Internal Server Error";
    case 502:
      return "Bad Gateway";
    case 503:
      return "Service Unavailable";
    default:
      return "Error";
  }
};

axiosInstance.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response) {
      const { data, status } = error.response;
      
      // Try to extract error message from response
      const extractedMessage = extractErrorMessage(data);
      
      if (extractedMessage) {
        // We successfully extracted an error message
        const title = getStatusCodeErrorTitle(status);
        store.dispatch(showToast("danger", title, extractedMessage));
      } else {
        // Fallback for when we can't parse the error message
        const title = status >= 500 ? "Server Error" : "Request Error";
        const message = status >= 500 
          ? "The server encountered an error. Please try again later."
          : "There was an issue with your request. Please check your input and try again.";
        store.dispatch(showToast("danger", title, message));
      }
    } else if (error.request) {
      // Network error (request was made but no response received)
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
