import { describe, it, expect } from "vitest";

import { formatDate } from "../helper";

describe("formatDate", () => {
  it("month string and day string are length 1", () => {
    expect(formatDate("1000-9-7")).toBe("1000-09-07");
  });
  it("ensure day is not off by one", () => {
    expect(formatDate("1000-09-08")).toBe("1000-09-08");
  });
  it("error on invalid date string", () => {
    const invalidDate = "dee-doo-doo";
    expect(() => formatDate(invalidDate))
      .toThrowError(`Invalid date: ${invalidDate}`);
  });
});
