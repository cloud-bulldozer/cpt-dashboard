export const uid = () => {
  const head = Date.now().toString(36);
  const tail = Math.random().toString(36).substring(2);

  return head + tail;
};

export const isEmptyObject = (obj) => {
  return (
    obj &&
    Object.keys(obj).length === 0 &&
    Object.getPrototypeOf(obj) === Object.prototype
  );
};

/**
 * Convert a date string into Locale Date String with seconds and milli seconds removed *
 * @function
 * @param {string} dateTimeStamp - Date in string format
 * @return {string} - Locale Date string
 */

export const formatDateTime = (dateTimeStamp) => {
  if (!dateTimeStamp) {
    return "N/A";
  }

  try {
    const dateObj = new Date(dateTimeStamp);
    if (isNaN(dateObj.getTime())) {
      console.error("Invalid dateTimeStamp received:", dateTimeStamp);
      return "Invalid Date";
    }
    return new Intl.DateTimeFormat("en-US", {
      dateStyle: "medium",
      timeStyle: "short",
    }).format(dateObj);
  } catch (error) {
    console.error("Error formatting date:", error);
    console.error("Original input was:", dateTimeStamp);
    return "Formatting Error";
  }
};

/**
 * Build the url with query params*
 * @function
 * @param {Object} queryObj - Query
 * @param {string} toPage - new page to be navigated
 * @return {string} - update the url with the query string
 */

export const appendQueryString = (queryObj, navigate, toPage) => {
  const validQueryObj = Object.fromEntries(
    Object.entries(queryObj).filter(
      // eslint-disable-next-line no-unused-vars
      ([_, value]) => value !== null && value !== undefined && value !== ""
    )
  );

  const queryString = new URLSearchParams(validQueryObj).toString();

  navigate({
    pathname: toPage ? toPage : window.location.pathname,
    search: `?${queryString}`,
  });
};

export const formatDate = (input) => {
  const d = new Date(input);
  if (isNaN(d)) throw new Error(`Invalid date: ${input}`);
  const year = d.getUTCFullYear();
  const month = String(d.getUTCMonth() + 1).padStart(2, "0");
  const day = String(d.getUTCDate()).padStart(2, "0");
  return `${year}-${month}-${day}`;
};

export const appendDateFilter = (startDate, endDate) => {
  const searchParams = new URLSearchParams(window.location.search);
  if (!searchParams.has("start_date") || !searchParams.has("end_date")) {
    searchParams.set("start_date", startDate);
    searchParams.set("end_date", endDate);
    window.history.pushState({}, "", `?${searchParams.toString()}`);
  }
};
