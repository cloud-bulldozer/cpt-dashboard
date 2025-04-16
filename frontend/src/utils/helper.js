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
  const dateObj = new Date(dateTimeStamp);
  return new Intl.DateTimeFormat("en-US", {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(dateObj);
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

export const formatDate = (date) => {
  let d = new Date(date),
    month = "" + (d.getMonth() + 1),
    day = "" + d.getDate(),
    year = d.getFullYear();

  if (month.length < 2) month = "0" + month;
  if (day.length < 2) day = "0" + day;

  return [year, month, day].join("-");
};

export const appendDateFilter = (startDate, endDate) => {
  const searchParams = new URLSearchParams(window.location.search);
  if (!searchParams.has("start_date") || !searchParams.has("end_date")) {
    searchParams.set("start_date", startDate);
    searchParams.set("end_date", endDate);
    window.history.pushState({}, "", `?${searchParams.toString()}`);
  }
};
