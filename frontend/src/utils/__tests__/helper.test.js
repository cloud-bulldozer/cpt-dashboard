import { describe, it, expect } from "vitest";

import { formatDate } from "../helper";

describe("formatDate", () => {
  it("month and day strings each have length 2", () => {
    expect(formatDate("1000-10-10")).toBe("1000-10-10");
  });
  it("month string is length 1", () => {
    expect(formatDate("1000-9-10")).toBe("1000-09-10");
  });
  it("day string is length 1", () => {
    expect(formatDate("1000-10-9")).toBe("1000-10-09");
  });
  it("year string is length 2", () => {
    expect(formatDate("01-10-09")).toBe("2009-01-10");
  });
  it("error on invalid date string", () => {
    const invalidDate = "dee-doo-doo";
    expect(() => formatDate(invalidDate))
      .toThrowError(`Invalid date: ${invalidDate}`);
  });
});