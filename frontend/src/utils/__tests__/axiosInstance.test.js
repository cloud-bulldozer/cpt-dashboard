import { describe, it, expect, test } from "vitest";

import {
  extractErrorMessage,
} from "../errorUtils";

// Test the error priority logic that would be used in axios interceptor
const mockErrorPrioritization = (axiosMessage, responseData, status = 500) => {
  const responseMessage = extractErrorMessage(responseData, status);
  
  // Enhanced messages (from status codes 500, 502, 503, 504) are always preferred
  const enhancedMessages = [
    'A backend service is temporarily unavailable.',
    'Unable to connect to backend service. Please try again in a moment.',
    'The service is temporarily overloaded or under maintenance. Please try again later.',
    'The request timed out while connecting to external services. Please try again.'
  ];
  
  if (responseMessage && enhancedMessages.includes(responseMessage)) {
    return { message: responseMessage, source: 'Response data extraction' };
  } else if (responseMessage && typeof responseData === 'object') {
    return { message: responseMessage, source: 'Response data extraction' };
  } else if (axiosMessage && axiosMessage !== 'Network Error' && !axiosMessage.startsWith('timeout')) {
    return { message: axiosMessage, source: 'Axios error message' };
  } else if (responseMessage) {
    return { message: responseMessage, source: 'Response data extraction' };
  }
  
  return { message: null, source: 'none' };
};

describe("extractErrorMessage", () => {
  // Status code based enhanced messages (any text gets enhanced for these status codes)
  test.each([
    ["Internal Server Error", 500, "A backend service is temporarily unavailable."],
    ["Erreur interne du serveur", 500, "A backend service is temporarily unavailable."], // French
    ["Custom 500 error", 500, "A backend service is temporarily unavailable."],
    ["Bad Gateway", 502, "Unable to connect to backend service. Please try again in a moment."],
    ["Proxy Error", 502, "Unable to connect to backend service. Please try again in a moment."],
    ["Service Unavailable", 503, "The service is temporarily overloaded or under maintenance. Please try again later."],
    ["Temporarily Unavailable", 503, "The service is temporarily overloaded or under maintenance. Please try again later."],
    ["Gateway Timeout", 504, "The request timed out while connecting to external services. Please try again."],
    ["Request Timeout", 504, "The request timed out while connecting to external services. Please try again."]
  ])('enhances any plain text for status %d: "%s" -> enhanced message', (input, status, expected) => {
    expect(extractErrorMessage(input, status)).toBe(expected);
  });

  // Non-enhanced status codes return original text
  test.each([
    ["Custom server error", 400, "Custom server error"],
    ["Not Found", 404, "Not Found"],
    ["Unauthorized", 401, "Unauthorized"],
    ["  Whitespace trimmed  ", 422, "Whitespace trimmed"]
  ])('returns original text for non-enhanced status %d: "%s"', (input, status, expected) => {
    expect(extractErrorMessage(input, status)).toBe(expected);
  });

  // FastAPI error formats
  test.each([
    [{ detail: { message: "Custom error message" } }, 400, "Custom error message"],
    [{ detail: { error: "Error object format" } }, 422, "Error object format"],
    [{ detail: "String detail format" }, 400, "String detail format"],
    [{ error: "Direct error key format" }, 400, "Direct error key format"],
    [{ message: "Generic message field" }, 400, "Generic message field"]
  ])('extracts from various JSON formats', (input, status, expected) => {
    expect(extractErrorMessage(input, status)).toBe(expected);
  });

  // Null/invalid inputs
  test.each([
    [null], [undefined], [{}], [123], [[]], [""], ["   "], [{ detail: [] }]
  ])('returns null for unparseable data: %s', (input) => {
    expect(extractErrorMessage(input, 500)).toBeNull();
  });

  it("handles validation errors with field paths", () => {
    const result = extractErrorMessage({
      detail: [
        { msg: "Field required", loc: ["query", "start_date"] },
        { msg: "ensure this value is greater than 0", loc: ["query", "size"] },
      ],
    }, 422);
    expect(result).toContain("Multiple validation errors");
    expect(result).toContain("Field required");
    expect(result).toContain("greater than 0");
  });

  it("handles single validation error with nested path", () => {
    const result = extractErrorMessage({
      detail: [{ msg: "Field is required", loc: ["query", "start_date", "nested"] }],
    }, 422);
    expect(result).toBe("Field is required (start_date.nested)");
  });
});


describe("Error Prioritization Logic", () => {
  test.each([
    ["Request failed with status code 500", { detail: { message: "Database connection timeout" } }, "Database connection timeout", "Response data extraction"],
    ["Request failed with status code 500", "Internal Server Error", "A backend service is temporarily unavailable.", "Response data extraction"],
    ["Network Error", "Internal Server Error", "A backend service is temporarily unavailable.", "Response data extraction"],
    ["Connection refused to database server", "Internal Server Error", "A backend service is temporarily unavailable.", "Response data extraction"],
    ["timeout of 5000ms exceeded", "Internal Server Error", "A backend service is temporarily unavailable.", "Response data extraction"],
    [null, { detail: { message: "Specific error" } }, "Specific error", "Response data extraction"],
    [undefined, "Internal Server Error", "A backend service is temporarily unavailable.", "Response data extraction"],
    ["Network Error", { random: "data" }, null, "none"],
    ["", "Internal Server Error", "A backend service is temporarily unavailable.", "Response data extraction"]
  ])('prioritization: axios="%s" response=%j -> message="%s" source="%s"', (axiosMessage, responseData, expectedMessage, expectedSource) => {
    const result = mockErrorPrioritization(axiosMessage, responseData);
    expect(result.message).toBe(expectedMessage);
    expect(result.source).toBe(expectedSource);
  });

  it("prefers validation errors over axios messages", () => {
    const result = mockErrorPrioritization(
      "Request failed with status code 422",
      { detail: [{ msg: "Field required", loc: ["query", "start_date"] }] },
      422
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
    
    const responseMessage = extractErrorMessage(data, status);
    
    // Enhanced messages (from status codes 500, 502, 503, 504) are always preferred
    const enhancedMessages = [
      'A backend service is temporarily unavailable.',
      'Unable to connect to backend service. Please try again in a moment.',
      'The service is temporarily overloaded or under maintenance. Please try again later.',
      'The request timed out while connecting to external services. Please try again.'
    ];
    
    if (responseMessage && enhancedMessages.includes(responseMessage)) {
      extractedMessage = responseMessage;
      messageSource = 'Response data extraction';
    } else if (responseMessage && typeof data === 'object') {
      extractedMessage = responseMessage;
      messageSource = 'Response data extraction';
    } else if (axiosMessage && axiosMessage !== 'Network Error' && !axiosMessage.startsWith('timeout')) {
      extractedMessage = axiosMessage;
      messageSource = 'Axios error message';
    } else if (responseMessage) {
      extractedMessage = responseMessage;
      messageSource = 'Response data extraction';
    }
    
    return {
      showToast: true, // Now shows for all HTTP errors
      message: extractedMessage,
      source: messageSource
    };
  };

  test.each([
    [500, "Internal Server Error", "/api/v1/telco/filters", "Request failed with status code 500", "A backend service is temporarily unavailable.", "Response data extraction"],
    [422, { detail: [{ msg: "Field required", loc: ["query", "start_date"] }] }, "/api/v1/ocp/jobs", "Request failed with status code 422", "Field required (start_date)", "Response data extraction"],
    [400, { detail: { message: "Invalid date range" } }, "/api/v1/quay/jobs", "Request failed with status code 400", "Invalid date range", "Response data extraction"],
    [404, { detail: "Not found" }, "/api/v1/ocp/jobs", "Request failed with status code 404", "Not found", "Response data extraction"]
  ])('status %d with %j -> message="%s" source="%s"', (status, data, url, axiosMessage, expectedMessage, expectedSource) => {
    const result = mockFullErrorHandling(status, data, url, axiosMessage);
    
    expect(result).toEqual({
      showToast: true,
      message: expectedMessage,
      source: expectedSource
    });
  });

  it("handles enhanced error messages", () => {
    const result = mockFullErrorHandling(
      504,
      "Gateway Timeout",
      "/api/v1/ols/jobs",
      "timeout of 30000ms exceeded"
    );
    
    expect(result.message).toBe("The request timed out while connecting to external services. Please try again.");
  });
});
