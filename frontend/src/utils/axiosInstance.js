import { showFailureToast, showToast } from "@/actions/toastActions";

import { BASE_URL } from "./apiConstants";
import { extractErrorMessage, getServiceContext } from "./errorUtils";
import axios from "axios";
import store from "@/store/store";

const axiosInstance = axios.create({
  baseURL: BASE_URL,
  responseType: "json",
});


const getStatusCodeErrorTitle = (status) => {
  switch (status) {
    case 400:
      return "Bad Request";
    case 401:
      return "Unauthorized";
    case 403:
      return "Forbidden";
    case 404:
      return "Not Found";
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
    // Check if this request should suppress toast notifications
    const suppressToast = error.config?.suppressToast;
    
    // 🐛 DEBUG: Print exact backend API response details to console
    if (error.response) {
      const { data, status, headers } = error.response;
      const requestUrl = error.config?.url || 'unknown';
      const method = error.config?.method?.toUpperCase() || 'GET';
      const fullUrl = error.config?.baseURL ? `${error.config.baseURL}${requestUrl}` : requestUrl;
      
      console.group(`🚨 API Error: ${method} ${requestUrl}`);
      console.log('📍 Full URL:', fullUrl);
      console.log('📊 Status Code:', status);
      console.log('📋 Response Headers:', {
        'content-type': headers?.['content-type'] || 'unknown',
        'content-length': headers?.['content-length'] || 'unknown'
      });
      console.log('📄 Raw Response Body:');
      console.log(data);
      console.log('📝 Response Type:', typeof data);
      
      // Show what both extraction methods produced
      const responseExtracted = extractErrorMessage(data);
      const axiosMessage = error.message;
      console.log('🔧 Response Data Extracted:', responseExtracted || '(none)');
      console.log('🔧 Axios Error Message:', axiosMessage || '(none)');
      
      // Show service context if applicable
      const serviceContext = getServiceContext(requestUrl);
      if (serviceContext) {
        console.log('🏷️  Service Context:', serviceContext);
      }
      
      console.groupEnd();
    } else if (error.request) {
      console.group('🌐 Network Error');
      console.log('📡 Request made but no response received');
      console.log('🔗 Request URL:', error.config?.url || 'unknown');
      console.log('❌ Error:', error.message);
      console.groupEnd();
    } else {
      console.group('⚠️  Request Setup Error');
      console.log('❌ Error:', error.message);
      console.groupEnd();
    }
    
    if (!suppressToast && error.response) {
      const { data, status } = error.response;
      const requestUrl = error.config?.url || '';
      
      // Only show toasts for certain error conditions:
      // - 4xx errors that are user-actionable (400, 401, 403, 422)
      // - 5xx server errors (always show these)
      // - Skip 404 errors for background data fetching (common for optional data)
      const shouldShowToast = 
        status === 400 || // Bad Request - user needs to fix input
        status === 401 || // Unauthorized - user needs to login
        status === 403 || // Forbidden - user doesn't have access
        status === 422 || // Validation Error - user needs to fix input
        status >= 500;    // Server errors - always show
      
      if (shouldShowToast) {
        let extractedMessage = null;
        let messageSource = '';
        
        // Priority 1: Try to extract from response data using existing logic
        const responseMessage = extractErrorMessage(data);
        
        // Priority 2: Use Axios error message if response extraction failed or gave generic message
        const axiosMessage = error.message;
        const isGenericResponseMessage = responseMessage && (
          responseMessage.includes('backend service is temporarily unavailable') ||
          responseMessage === 'Internal Server Error' ||
          responseMessage === 'Bad Gateway' ||
          responseMessage === 'Service Unavailable'
        );
        
        if (responseMessage && !isGenericResponseMessage) {
          // Use the extracted response message if it's specific
          extractedMessage = responseMessage;
          messageSource = 'Response data extraction';
        } else if (axiosMessage && axiosMessage !== 'Network Error' && !axiosMessage.startsWith('timeout')) {
          // Use Axios error message as it might be more descriptive
          extractedMessage = axiosMessage;
          messageSource = 'Axios error message';
        } else if (responseMessage) {
          // Fall back to response message even if generic
          extractedMessage = responseMessage;
          messageSource = 'Response data extraction (generic)';
        }
        
        // Add context about which service failed for 500 errors
        if (status >= 500 && extractedMessage && requestUrl) {
          const serviceContext = getServiceContext(requestUrl);
          if (serviceContext) {
            extractedMessage = `${serviceContext}: ${extractedMessage}`;
          }
        }
        
        if (extractedMessage) {
          // We successfully extracted an error message
          const title = getStatusCodeErrorTitle(status);
          store.dispatch(showToast("danger", title, extractedMessage));
          
          // Log which method was used for extracting the message
          console.log('🔧 Message Source:', messageSource);
        } else {
          // Final fallback for when we can't parse any error message
          const title = status >= 500 ? "Server Error" : "Request Error";
          const message = status >= 500 
            ? "The server encountered an error. Please try again later."
            : "There was an issue with your request. Please check your input and try again.";
          store.dispatch(showToast("danger", title, message));
          console.log('🔧 Message Source: Final fallback (no extractable message)');
        }
      }
    } else if (!suppressToast && error.request) {
      // Network error (request was made but no response received)
      store.dispatch(showToast(
        "danger", 
        "Network Error", 
        "Unable to connect to the server. Please check your internet connection and try again."
      ));
    } else if (!suppressToast && !error.request) {
      // Something else went wrong
      store.dispatch(showFailureToast());
    }
    
    return Promise.reject(error);
  }
);

// Helper methods for making requests with suppressed error toasts
axiosInstance.silent = {
  get: (url, config = {}) => axiosInstance.get(url, { ...config, suppressToast: true }),
  post: (url, data, config = {}) => axiosInstance.post(url, data, { ...config, suppressToast: true }),
  put: (url, data, config = {}) => axiosInstance.put(url, data, { ...config, suppressToast: true }),
  delete: (url, config = {}) => axiosInstance.delete(url, { ...config, suppressToast: true }),
  patch: (url, data, config = {}) => axiosInstance.patch(url, data, { ...config, suppressToast: true }),
};

// Helper method to suppress toasts for any request
axiosInstance.suppressToast = (config = {}) => ({ ...config, suppressToast: true });

export default axiosInstance;
