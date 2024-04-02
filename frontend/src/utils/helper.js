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
