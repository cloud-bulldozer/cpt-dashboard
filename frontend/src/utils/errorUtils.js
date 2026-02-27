/**
 * Extract user-friendly error message from various API error response formats.
 * @param {string|object|null} data - Response body (string or parsed JSON)
 * @param {number} status - HTTP status code
 * @returns {string|null} Extracted message or null if unparseable
 */
export const extractErrorMessage = (data, status) => {
  try {
    // Enhanced error messages based on HTTP status codes for generic responses
    const statusErrorMap = {
      500: 'A backend service is temporarily unavailable.',
      502: 'Unable to connect to backend service. Please try again in a moment.',
      503: 'The service is temporarily overloaded or under maintenance. Please try again later.',
      504: 'The request timed out while connecting to external services. Please try again.'
    };

    // Handling for plain text response
    if (typeof data === 'string' && data.trim()) {
      const errorText = data.trim();
      if (statusErrorMap[status]) {
        return statusErrorMap[status];
      }
      // Return original text for unrecognized status codes
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

