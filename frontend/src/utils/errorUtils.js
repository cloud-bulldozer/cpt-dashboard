/**
 * Pure error extraction utilities for API error responses.
 * Used by axios interceptor - extracted for testability.
 */

/**
 * Extract user-friendly error message from various API error response formats.
 * @param {string|object|null} data - Response body (string or parsed JSON)
 * @returns {string|null} Extracted message or null if unparseable
 */
export const extractErrorMessage = (data) => {
  try {
    // Case: Plain text response (e.g. FastAPI/Starlette default 500, or text/plain errors)
    if (typeof data === 'string' && data.trim()) {
      const errorText = data.trim();

      // Enhance generic server errors with more helpful context
      if (errorText === 'Internal Server Error') {
        return 'A backend service is temporarily unavailable.';
      }

      if (errorText === 'Bad Gateway') {
        return 'Unable to connect to backend service. Please try again in a moment.';
      }

      if (errorText === 'Service Unavailable') {
        return 'The service is temporarily overloaded or under maintenance. Please try again later.';
      }

      if (errorText === 'Gateway Timeout') {
        return 'The request timed out while connecting to external services. Please try again.';
      }

      // For other plain text errors, return as-is
      return errorText;
    }

    // Handle different error response formats
    if (data && typeof data === 'object') {
      // Case 1: FastAPI validation errors - {"detail": [{"type": "...", "loc": [...], "msg": "..."}]}
      if (data.detail && Array.isArray(data.detail) && data.detail.length > 0) {
        const validationErrors = data.detail.map(error => {
          if (error.msg) {
            const fieldPath = error.loc && Array.isArray(error.loc) && error.loc.length > 1
              ? ` (${error.loc.slice(1).join('.')})`
              : '';
            return `${error.msg}${fieldPath}`;
          }
          return 'Validation error';
        });

        if (validationErrors.length === 1) {
          return validationErrors[0];
        }
        return `Multiple validation errors: ${validationErrors.join(', ')}`;
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

      // Case 5: {"error": "..."} - direct error key
      if (data.error && typeof data.error === 'string') {
        return data.error;
      }

      // Case 6: Try to find any message-like field
      if (data.message && typeof data.message === 'string') {
        return data.message;
      }
    }

    return null;
  } catch (e) {
    console.warn('Error parsing error response:', e);
    return null;
  }
};

/**
 * Get service context label from API URL for 500 errors.
 * @param {string} url - Request URL path
 * @returns {string|null} Service name or null
 */
export const getServiceContext = (url) => {
  if (url.includes('/telco/')) {
    return 'Telco Service';
  }
  if (url.includes('/ocp/')) {
    return 'OCP Service';
  }
  if (url.includes('/ols/')) {
    return 'OLS Service';
  }
  if (url.includes('/quay/')) {
    return 'Quay Service';
  }
  if (url.includes('/ilab/')) {
    return 'ILAB Service';
  }
  if (url.includes('/cpt/')) {
    return 'CPT Service';
  }
  return null;
};
