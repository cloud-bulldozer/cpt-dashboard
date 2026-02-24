import { describe, it, expect, test } from "vitest";

import {
  extractErrorMessage,
  getServiceContext,
} from "../errorUtils";

// Test the error priority logic that would be used in axios interceptor
const mockErrorPrioritization = (axiosMessage, responseData) => {
  const responseMessage = extractErrorMessage(responseData);
  const isGenericResponseMessage = responseMessage && (
    responseMessage.includes('backend service is temporarily unavailable') ||
    responseMessage === 'Internal Server Error' ||
    responseMessage === 'Bad Gateway' ||
    responseMessage === 'Service Unavailable'
  );
  
  if (responseMessage && !isGenericResponseMessage) {
    return { message: responseMessage, source: 'Response data extraction' };
  } else if (axiosMessage && axiosMessage !== 'Network Error' && !axiosMessage.startsWith('timeout')) {
    return { message: axiosMessage, source: 'Axios error message' };
  } else if (responseMessage) {
    return { message: responseMessage, source: 'Response data extraction (generic)' };
  }
  
  return { message: null, source: 'none' };
};

describe("extractErrorMessage", () => {
  // Plain text error message conversion
  test.each([
    ["Internal Server Error", "A backend service is temporarily unavailable."],
    ["Bad Gateway", "Unable to connect to backend service. Please try again in a moment."],
    ["Service Unavailable", "The service is temporarily overloaded or under maintenance. Please try again later."],
    ["Gateway Timeout", "The request timed out while connecting to external services. Please try again."],
    ["Custom server error", "Custom server error"],
    ["  Whitespace trimmed  ", "Whitespace trimmed"]
  ])('converts plain text "%s" to expected message', (input, expected) => {
    expect(extractErrorMessage(input)).toBe(expected);
  });

  // FastAPI error formats
  test.each([
    [{ detail: { message: "Custom error message" } }, "Custom error message"],
    [{ detail: { error: "Error object format" } }, "Error object format"],
    [{ detail: "String detail format" }, "String detail format"],
    [{ error: "Direct error key format" }, "Direct error key format"],
    [{ message: "Generic message field" }, "Generic message field"]
  ])('extracts from various JSON formats', (input, expected) => {
    expect(extractErrorMessage(input)).toBe(expected);
  });

  // Null/invalid inputs
  test.each([
    [null], [undefined], [{}], [123], [[]], [""], ["   "], [{ detail: [] }]
  ])('returns null for unparseable data: %s', (input) => {
    expect(extractErrorMessage(input)).toBeNull();
  });

  it("handles validation errors with field paths", () => {
    const result = extractErrorMessage({
      detail: [
        { msg: "Field required", loc: ["query", "start_date"] },
        { msg: "ensure this value is greater than 0", loc: ["query", "size"] },
      ],
    });
    expect(result).toContain("Multiple validation errors");
    expect(result).toContain("Field required");
    expect(result).toContain("greater than 0");
  });

  it("handles single validation error with nested path", () => {
    const result = extractErrorMessage({
      detail: [{ msg: "Field is required", loc: ["query", "start_date", "nested"] }],
    });
    expect(result).toBe("Field is required (start_date.nested)");
  });
});

describe("getServiceContext", () => {
  test.each([
    ["/api/v1/telco/filters", "Telco Service"],
    ["/api/v1/telco/jobs", "Telco Service"],
    ["/api/v1/ocp/jobs", "OCP Service"],
    ["/api/v1/ols/jobs", "OLS Service"],
    ["/api/v1/quay/jobs", "Quay Service"],
    ["/api/v1/ilab/runs", "ILAB Service"],
    ["/api/v1/cpt/jobs", "CPT Service"],
    ["/api/version", null],
    ["/api/v1/summary", null],
    ["/unknown", null],
    ["", null],
    ["/api/v1/TELCO/jobs", null], // case sensitive
    ["/api/v1/telco/jobs?start_date=2024-01-01", "Telco Service"], // query params
    ["/api/v1/quay/jobs#section1", "Quay Service"], // fragments
    ["/api/v1/telco/jobs/123/details", "Telco Service"], // nested paths
    ["/api/v1/telco/ocp/mixed", "Telco Service"] // first match wins
  ])('getServiceContext("%s") returns %s', (url, expected) => {
    expect(getServiceContext(url)).toBe(expected);
  });
});

describe("Error Prioritization Logic", () => {
  test.each([
    ["Request failed with status code 500", { detail: { message: "Database connection timeout" } }, "Database connection timeout", "Response data extraction"],
    ["Request failed with status code 500", "Internal Server Error", "Request failed with status code 500", "Axios error message"],
    ["Network Error", "Internal Server Error", "A backend service is temporarily unavailable.", "Response data extraction (generic)"],
    ["Connection refused to database server", "Internal Server Error", "Connection refused to database server", "Axios error message"],
    ["timeout of 5000ms exceeded", "Internal Server Error", "A backend service is temporarily unavailable.", "Response data extraction (generic)"],
    [null, { detail: { message: "Specific error" } }, "Specific error", "Response data extraction"],
    [undefined, "Internal Server Error", "A backend service is temporarily unavailable.", "Response data extraction (generic)"],
    ["Network Error", { random: "data" }, null, "none"],
    ["", "Internal Server Error", "A backend service is temporarily unavailable.", "Response data extraction (generic)"]
  ])('prioritization: axios="%s" response=%j -> message="%s" source="%s"', (axiosMessage, responseData, expectedMessage, expectedSource) => {
    const result = mockErrorPrioritization(axiosMessage, responseData);
    expect(result.message).toBe(expectedMessage);
    expect(result.source).toBe(expectedSource);
  });

  it("prefers validation errors over axios messages", () => {
    const result = mockErrorPrioritization(
      "Request failed with status code 422",
      { detail: [{ msg: "Field required", loc: ["query", "start_date"] }] }
    );
    
    expect(result).toEqual({
      message: "Field required (start_date)",
      source: "Response data extraction"
    });
  });
});

describe("Integration Tests - Full Error Handling Flow", () => {
  const mockFullErrorHandling = (status, data, url, axiosMessage) => {
    // Note: Current implementation shows toasts for ALL status codes (400-599)
    let extractedMessage = null;
    let messageSource = '';
    
    const responseMessage = extractErrorMessage(data);
    const isGenericResponseMessage = responseMessage && (
      responseMessage.includes('backend service is temporarily unavailable') ||
      responseMessage === 'Internal Server Error' ||
      responseMessage === 'Bad Gateway' ||
      responseMessage === 'Service Unavailable'
    );
    
    if (responseMessage && !isGenericResponseMessage) {
      extractedMessage = responseMessage;
      messageSource = 'Response data extraction';
    } else if (axiosMessage && axiosMessage !== 'Network Error' && !axiosMessage.startsWith('timeout')) {
      extractedMessage = axiosMessage;
      messageSource = 'Axios error message';
    } else if (responseMessage) {
      extractedMessage = responseMessage;
      messageSource = 'Response data extraction (generic)';
    }
    
    // Add service context for 500 errors
    if (status >= 500 && extractedMessage && url) {
      const serviceContext = getServiceContext(url);
      if (serviceContext) {
        extractedMessage = `${serviceContext}: ${extractedMessage}`;
      }
    }

    return {
      showToast: true, // Now shows for all HTTP errors
      message: extractedMessage,
      source: messageSource,
      hasServiceContext: status >= 500 && url && getServiceContext(url) !== null
    };
  };

  test.each([
    [500, "Internal Server Error", "/api/v1/telco/filters", "Request failed with status code 500", "Telco Service: Request failed with status code 500", "Axios error message", true],
    [422, { detail: [{ msg: "Field required", loc: ["query", "start_date"] }] }, "/api/v1/ocp/jobs", "Request failed with status code 422", "Field required (start_date)", "Response data extraction", false],
    [400, { detail: { message: "Invalid date range" } }, "/api/v1/quay/jobs", "Request failed with status code 400", "Invalid date range", "Response data extraction", false],
    [404, { detail: "Not found" }, "/api/v1/ocp/jobs", "Request failed with status code 404", "Not found", "Response data extraction", false]
  ])('status %d with %j -> message="%s" hasServiceContext=%s', (status, data, url, axiosMessage, expectedMessage, expectedSource, expectedServiceContext) => {
    const result = mockFullErrorHandling(status, data, url, axiosMessage);
    
    expect(result).toEqual({
      showToast: true,
      message: expectedMessage,
      source: expectedSource,
      hasServiceContext: expectedServiceContext
    });
  });

  it("handles enhanced error messages with service context", () => {
    const result = mockFullErrorHandling(
      500,
      "Gateway Timeout",
      "/api/v1/ols/jobs",
      "timeout of 30000ms exceeded"
    );
    
    expect(result.message).toBe("OLS Service: The request timed out while connecting to external services. Please try again.");
    expect(result.hasServiceContext).toBe(true);
  });
});
