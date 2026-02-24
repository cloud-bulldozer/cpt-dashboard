export const extractErrorMessage = (data) => {
  try {
    // Handling for plain text response
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

      return errorText;
    }

    // Handling for different error response formats
    if (data && typeof data === 'object') {
      // FastAPI validation errors - {"detail": [{"type": "...", "loc": [...], "msg": "..."}]}
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

      // {"detail": {"message": "..."}}
      if (data.detail && typeof data.detail === 'object' && !Array.isArray(data.detail) && data.detail.message) {
        return data.detail.message;
      }

      // {"detail": {"error": "..."}}
      if (data.detail && typeof data.detail === 'object' && !Array.isArray(data.detail) && data.detail.error) {
        return data.detail.error;
      }

      // {"detail": "..."} - string detail
      if (data.detail && typeof data.detail === 'string') {
        return data.detail;
      }

      // {"error": "..."} - direct error key
      if (data.error && typeof data.error === 'string') {
        return data.error;
      }

      // Try to find any message-like field
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
