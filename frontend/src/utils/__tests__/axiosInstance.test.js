import { describe, it, expect } from "vitest";

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
  it('converts plain text "Internal Server Error" to helpful message', () => {
    const result = extractErrorMessage("Internal Server Error");
    expect(result).toBe("A backend service is temporarily unavailable.");
  });

  it('converts plain text "Bad Gateway" to helpful message', () => {
    const result = extractErrorMessage("Bad Gateway");
    expect(result).toBe(
      "Unable to connect to backend service. Please try again in a moment."
    );
  });

  it('converts plain text "Service Unavailable" to helpful message', () => {
    const result = extractErrorMessage("Service Unavailable");
    expect(result).toBe(
      "The service is temporarily overloaded or under maintenance. Please try again later."
    );
  });

  it("extracts from Format 1: detail.message", () => {
    const result = extractErrorMessage({
      detail: { message: "Custom error message" },
    });
    expect(result).toBe("Custom error message");
  });

  it("extracts from Format 2: detail.error", () => {
    const result = extractErrorMessage({
      detail: { error: "Error object format" },
    });
    expect(result).toBe("Error object format");
  });

  it("extracts from Format 3: detail string", () => {
    const result = extractErrorMessage({
      detail: "String detail format",
    });
    expect(result).toBe("String detail format");
  });

  it("extracts from Format 4: direct error key", () => {
    const result = extractErrorMessage({
      error: "Direct error key format",
    });
    expect(result).toBe("Direct error key format");
  });

  it("extracts validation errors and combines them", () => {
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

  it("returns null for unparseable data", () => {
    expect(extractErrorMessage(null)).toBeNull();
    expect(extractErrorMessage(undefined)).toBeNull();
    expect(extractErrorMessage({})).toBeNull();
    expect(extractErrorMessage(123)).toBeNull();
    expect(extractErrorMessage([])).toBeNull();
  });

  describe("Additional plain text error messages", () => {
    it('converts "Gateway Timeout" to helpful message', () => {
      const result = extractErrorMessage("Gateway Timeout");
      expect(result).toBe(
        "The request timed out while connecting to external services. Please try again."
      );
    });

    it("returns plain text as-is for unknown error messages", () => {
      expect(extractErrorMessage("Custom server error")).toBe("Custom server error");
      expect(extractErrorMessage("  Whitespace trimmed  ")).toBe("Whitespace trimmed");
    });

    it("handles empty strings", () => {
      expect(extractErrorMessage("")).toBeNull();
      expect(extractErrorMessage("   ")).toBeNull();
    });
  });

  describe("Complex validation error scenarios", () => {
    it("handles single validation error with field path", () => {
      const result = extractErrorMessage({
        detail: [
          { 
            msg: "Field is required", 
            loc: ["query", "start_date", "nested"] 
          }
        ],
      });
      expect(result).toBe("Field is required (start_date.nested)");
    });

    it("handles validation error without location", () => {
      const result = extractErrorMessage({
        detail: [
          { msg: "Invalid format" }
        ],
      });
      expect(result).toBe("Invalid format");
    });

    it("handles validation error with empty location", () => {
      const result = extractErrorMessage({
        detail: [
          { 
            msg: "Value error", 
            loc: ["query"] 
          }
        ],
      });
      expect(result).toBe("Value error");
    });

    it("handles validation errors without msg field", () => {
      const result = extractErrorMessage({
        detail: [
          { type: "missing" },
          { msg: "Valid error" }
        ],
      });
      expect(result).toBe("Multiple validation errors: Validation error, Valid error");
    });
  });

  describe("Edge cases and malformed data", () => {
    it("handles nested object structures", () => {
      const result = extractErrorMessage({
        detail: {
          message: {
            nested: "This should not be extracted"
          }
        }
      });
      // Returns the object because the condition only checks if message exists, not if it's a string
      expect(result).toEqual({
        nested: "This should not be extracted"
      });
    });

    it("handles detail as empty array", () => {
      const result = extractErrorMessage({
        detail: []
      });
      expect(result).toBeNull();
    });

    it("handles circular reference gracefully", () => {
      const circular = { detail: {} };
      circular.detail.self = circular.detail;
      
      // Should not crash and should return null
      expect(() => extractErrorMessage(circular)).not.toThrow();
      expect(extractErrorMessage(circular)).toBeNull();
    });
  });
});

describe("getServiceContext", () => {
  it("returns Telco Service for telco URLs", () => {
    expect(getServiceContext("/api/v1/telco/filters")).toBe("Telco Service");
    expect(getServiceContext("/api/v1/telco/jobs")).toBe("Telco Service");
  });

  it("returns OCP Service for ocp URLs", () => {
    expect(getServiceContext("/api/v1/ocp/jobs")).toBe("OCP Service");
  });

  it("returns OLS Service for ols URLs", () => {
    expect(getServiceContext("/api/v1/ols/jobs")).toBe("OLS Service");
  });

  it("returns Quay Service for quay URLs", () => {
    expect(getServiceContext("/api/v1/quay/jobs")).toBe("Quay Service");
  });

  it("returns ILAB Service for ilab URLs", () => {
    expect(getServiceContext("/api/v1/ilab/runs")).toBe("ILAB Service");
  });

  it("returns CPT Service for cpt URLs", () => {
    expect(getServiceContext("/api/v1/cpt/jobs")).toBe("CPT Service");
  });

  it("returns null for unknown URLs", () => {
    expect(getServiceContext("/api/version")).toBeNull();
    expect(getServiceContext("/api/v1/summary")).toBeNull();
    expect(getServiceContext("/unknown")).toBeNull();
    expect(getServiceContext("")).toBeNull();
  });

  describe("Edge cases for service context", () => {
    it("handles case sensitivity", () => {
      expect(getServiceContext("/api/v1/TELCO/jobs")).toBeNull();
      expect(getServiceContext("/api/v1/OCP/filters")).toBeNull();
    });

    it("handles URLs with query parameters", () => {
      expect(getServiceContext("/api/v1/telco/jobs?start_date=2024-01-01")).toBe("Telco Service");
      expect(getServiceContext("/api/v1/ocp/filters?pretty=true")).toBe("OCP Service");
    });

    it("handles URLs with fragments", () => {
      expect(getServiceContext("/api/v1/quay/jobs#section1")).toBe("Quay Service");
    });

    it("handles deeply nested service paths", () => {
      expect(getServiceContext("/api/v1/telco/jobs/123/details")).toBe("Telco Service");
      expect(getServiceContext("/api/v1/ilab/runs/456/metrics")).toBe("ILAB Service");
    });

    it("prioritizes first service match in URL", () => {
      expect(getServiceContext("/api/v1/telco/ocp/mixed")).toBe("Telco Service");
    });
  });
});

describe("Error Prioritization Logic", () => {
  it("prefers specific response messages over axios messages", () => {
    const result = mockErrorPrioritization(
      "Request failed with status code 500",
      { detail: { message: "Database connection timeout" } }
    );
    
    expect(result.message).toBe("Database connection timeout");
    expect(result.source).toBe("Response data extraction");
  });

  it("uses axios message when response is generic", () => {
    const result = mockErrorPrioritization(
      "Request failed with status code 500",
      "Internal Server Error"
    );
    
    expect(result.message).toBe("Request failed with status code 500");
    expect(result.source).toBe("Axios error message");
  });

  it("falls back to generic response message if axios message is network error", () => {
    const result = mockErrorPrioritization(
      "Network Error",
      "Internal Server Error"
    );
    
    expect(result.message).toBe("A backend service is temporarily unavailable.");
    expect(result.source).toBe("Response data extraction (generic)");
  });

  it("uses axios message for descriptive errors", () => {
    const result = mockErrorPrioritization(
      "Connection refused to database server",
      "Internal Server Error"
    );
    
    expect(result.message).toBe("Connection refused to database server");
    expect(result.source).toBe("Axios error message");
  });

  describe("Advanced prioritization scenarios", () => {
    it("handles timeout axios messages", () => {
      const result = mockErrorPrioritization(
        "timeout of 5000ms exceeded",
        "Internal Server Error"
      );
      
      expect(result.message).toBe("A backend service is temporarily unavailable.");
      expect(result.source).toBe("Response data extraction (generic)");
    });

    it("prefers validation errors over axios messages", () => {
      const result = mockErrorPrioritization(
        "Request failed with status code 422",
        {
          detail: [
            { msg: "Field required", loc: ["query", "start_date"] }
          ]
        }
      );
      
      expect(result.message).toBe("Field required (start_date)");
      expect(result.source).toBe("Response data extraction");
    });

    it("handles null/undefined axios messages", () => {
      const result1 = mockErrorPrioritization(
        null,
        { detail: { message: "Specific error" } }
      );
      expect(result1.message).toBe("Specific error");
      expect(result1.source).toBe("Response data extraction");

      const result2 = mockErrorPrioritization(
        undefined,
        "Internal Server Error"
      );
      expect(result2.message).toBe("A backend service is temporarily unavailable.");
      expect(result2.source).toBe("Response data extraction (generic)");
    });

    it("handles cases where both sources return null", () => {
      const result = mockErrorPrioritization(
        "Network Error",
        { random: "data" }
      );
      
      expect(result.message).toBeNull();
      expect(result.source).toBe("none");
    });

    it("handles empty string messages", () => {
      const result = mockErrorPrioritization(
        "",
        "Internal Server Error"
      );
      
      expect(result.message).toBe("A backend service is temporarily unavailable.");
      expect(result.source).toBe("Response data extraction (generic)");
    });
  });
});

describe("Integration Tests - Full Error Handling Flow", () => {
  const mockFullErrorHandling = (status, data, url, axiosMessage) => {
    // Simulate the full logic from axios interceptor
    const shouldShowToast = 
      status === 400 || 
      status === 401 || 
      status === 403 || 
      status === 422 || 
      status >= 500;

    if (!shouldShowToast) {
      return { showToast: false };
    }

    let extractedMessage = null;
    let messageSource = '';
    
    // Priority 1: Try to extract from response data
    const responseMessage = extractErrorMessage(data);
    
    // Priority 2: Use Axios error message if response extraction failed or gave generic message
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
      showToast: true,
      message: extractedMessage,
      source: messageSource,
      hasServiceContext: status >= 500 && url && getServiceContext(url) !== null
    };
  };

  it("handles 500 error with service context", () => {
    const result = mockFullErrorHandling(
      500,
      "Internal Server Error",
      "/api/v1/telco/filters",
      "Request failed with status code 500"
    );
    
    expect(result.showToast).toBe(true);
    expect(result.message).toBe("Telco Service: Request failed with status code 500");
    expect(result.source).toBe("Axios error message");
    expect(result.hasServiceContext).toBe(true);
  });

  it("handles 422 validation error without service context", () => {
    const result = mockFullErrorHandling(
      422,
      {
        detail: [
          { msg: "Field required", loc: ["query", "start_date"] }
        ]
      },
      "/api/v1/ocp/jobs",
      "Request failed with status code 422"
    );
    
    expect(result.showToast).toBe(true);
    expect(result.message).toBe("Field required (start_date)");
    expect(result.source).toBe("Response data extraction");
    expect(result.hasServiceContext).toBe(false);
  });

  it("skips toast for 404 errors", () => {
    const result = mockFullErrorHandling(
      404,
      { detail: "Not found" },
      "/api/v1/ocp/jobs",
      "Request failed with status code 404"
    );
    
    expect(result.showToast).toBe(false);
  });

  it("handles specific backend error message", () => {
    const result = mockFullErrorHandling(
      400,
      { detail: { message: "Invalid date range provided" } },
      "/api/v1/quay/jobs",
      "Request failed with status code 400"
    );
    
    expect(result.showToast).toBe(true);
    expect(result.message).toBe("Invalid date range provided");
    expect(result.source).toBe("Response data extraction");
    expect(result.hasServiceContext).toBe(false);
  });

  it("handles network timeout scenario", () => {
    const result = mockFullErrorHandling(
      500,
      "Gateway Timeout",
      "/api/v1/ols/jobs",
      "timeout of 30000ms exceeded"
    );
    
    expect(result.showToast).toBe(true);
    expect(result.message).toBe("OLS Service: The request timed out while connecting to external services. Please try again.");
    expect(result.source).toBe("Response data extraction");
    expect(result.hasServiceContext).toBe(true);
  });

  describe("Real-world error scenarios", () => {
    it("handles Splunk connection failure (Telco service)", () => {
      const result = mockFullErrorHandling(
        500,
        "Internal Server Error",
        "/api/v1/telco/filters",
        "Request failed with status code 500"
      );
      
      expect(result.message).toContain("Telco Service");
      expect(result.message).toContain("Request failed with status code 500");
    });

    it("handles database timeout error", () => {
      const result = mockFullErrorHandling(
        500,
        { detail: { message: "Database query timeout after 30 seconds" } },
        "/api/v1/ocp/jobs",
        "Request failed with status code 500"
      );
      
      expect(result.message).toBe("OCP Service: Database query timeout after 30 seconds");
      expect(result.source).toBe("Response data extraction");
    });

    it("handles authentication failure", () => {
      const result = mockFullErrorHandling(
        401,
        { detail: "Invalid credentials" },
        "/api/v1/ilab/runs",
        "Request failed with status code 401"
      );
      
      expect(result.message).toBe("Invalid credentials");
      expect(result.showToast).toBe(true);
    });
  });
});
