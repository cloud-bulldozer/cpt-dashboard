# Error Handling Improvements

## Overview

This document describes the improvements made to centralize and enhance error handling in the CPT Dashboard application, specifically in the axios interceptor layer.

## Problem Statement

The original error handling had several limitations:
1. Only handled specific error formats (`{"detail": {"message": "..."}}`)
2. Limited status code handling (only 400 and 404)
3. No fallback for malformed JSON responses
4. No differentiation between network errors and server errors
5. Generic error messages that didn't provide useful information to users

## Solution

### Enhanced Axios Interceptor

The `axiosInstance.js` file has been updated with a comprehensive error handling system that:

1. **Handles Multiple Error Response Formats**:
   - `{"detail": {"message": "..."}}` - HTTPException with message object
   - `{"detail": {"error": "..."}}` - HTTPException with error object  
   - `{"detail": "..."}` - HTTPException with string detail (FastAPI unhandled exceptions)
   - `{"error": "..."}` - Direct error key format
   - `{"message": "..."}` - Generic message format

2. **Robust JSON Parsing**:
   - Safe error message extraction with try-catch
   - Fallback messages when JSON parsing fails
   - Console warnings for debugging malformed responses

3. **Comprehensive Status Code Handling**:
   - Specific titles for common HTTP status codes (400, 401, 403, 404, 422, 500, 502, 503)
   - Differentiated messaging for client errors (4xx) vs server errors (5xx)

4. **Network Error Handling**:
   - Separate handling for network connectivity issues
   - Clear messaging when requests fail to reach the server

5. **Improved User Experience**:
   - More descriptive error titles based on status codes
   - Context-aware error messages
   - Consistent toast notification system

### Key Functions

#### `extractErrorMessage(data)`
Safely extracts error messages from various response formats with fallback handling.

#### `getStatusCodeErrorTitle(status)`
Returns appropriate error titles based on HTTP status codes.

### Error Handling Flow

```
Request Error
    ↓
Has Response?
    ├─ Yes → Extract error message → Show specific toast
    └─ No → Network error? → Show network error toast
```

## Testing

### Temporary Test Infrastructure

**⚠️ IMPORTANT: The following files contain temporary test code that should be REMOVED after testing:**

1. **Backend Test Endpoints** (`backend/app/api/v1/endpoints/ocp/ocpJobs.py`):
   - `/api/v1/ocp/test-errors/format1` - Tests `{"detail": {"message": "..."}}`
   - `/api/v1/ocp/test-errors/format2` - Tests `{"detail": {"error": "..."}}`
   - `/api/v1/ocp/test-errors/format3` - Tests `{"detail": "..."}`
   - `/api/v1/ocp/test-errors/format4` - Tests `{"error": "..."}`
   - `/api/v1/ocp/test-errors/malformed` - Tests non-JSON responses
   - `/api/v1/ocp/test-errors/network` - Tests network timeouts

2. **Frontend Test Page** (`frontend/src/components/templates/ErrorTestPage/index.jsx`):
   - Interactive test interface with buttons for each error type
   - Console logging for debugging
   - Instructions for testing

3. **Routing Changes**:
   - `frontend/src/utils/routeConstants.js` - Added `ERROR_TEST` route
   - `frontend/src/App.jsx` - Added ErrorTestPage route
   - `frontend/src/assets/constants/SidemenuConstants.js` - Added navigation constant
   - `frontend/src/components/molecules/SideMenuOptions/index.jsx` - Added menu item

### Testing Instructions

1. Start the application (both backend and frontend)
2. Navigate to the "🧪 Error Test" page in the side menu
3. Click each test button to verify different error formats are handled correctly
4. Check that:
   - Appropriate toast notifications appear
   - Error messages are descriptive and user-friendly
   - UI remains operational after errors
   - Console logs show detailed error information

### Cleanup After Testing

**REMOVE the following after testing is complete:**

#### Backend Files:
- Remove test endpoints from `backend/app/api/v1/endpoints/ocp/ocpJobs.py` (lines marked with "TEMPORARY")

#### Frontend Files:
- Delete `frontend/src/components/templates/ErrorTestPage/`
- Remove ERROR_TEST references from:
  - `frontend/src/utils/routeConstants.js`
  - `frontend/src/App.jsx`
  - `frontend/src/assets/constants/SidemenuConstants.js`
  - `frontend/src/components/molecules/SideMenuOptions/index.jsx`

#### Documentation:
- Delete this file: `ERROR_HANDLING_IMPROVEMENTS.md`

## Benefits

1. **Centralized Error Handling**: All HTTP errors are handled consistently in one place
2. **Better User Experience**: More informative error messages and appropriate status-based titles
3. **Robust Parsing**: Handles malformed responses gracefully
4. **Network Awareness**: Distinguishes between network and server errors
5. **Maintainability**: Clear separation of concerns and well-documented code
6. **Debugging Support**: Console logging for development troubleshooting

## Future Improvements

1. **Backend Consistency**: Standardize error response formats across all endpoints
2. **Error Categorization**: Add error codes for programmatic handling
3. **Retry Logic**: Implement automatic retry for transient network errors
4. **User Feedback**: Add options for users to report persistent errors
5. **Monitoring**: Integrate with error tracking services for production monitoring

