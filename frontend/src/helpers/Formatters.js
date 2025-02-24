export function formatTime(time) {
  // Hours, minutes and seconds
  let hrs = ~~(time / 3600);
  let mins = ~~((time % 3600) / 60);
  let secs = ~~time % 60;

  // Output like "1:01" or "4:03:59" or "123:03:59"
  let ret = "";
  if (hrs > 0) {
    ret += "" + hrs + ":" + (mins < 10 ? "0" : "");
  }
  ret += "" + mins + ":" + (secs < 10 ? "0" : "");
  ret += "" + secs;
  return ret;
}

export function getFormattedDate(date) {
  let d = new Date();
  if (typeof date === "string" || date instanceof String) d = new Date(date);
  else d = new Date(date.props.value);

  let year = d.getFullYear();
  let month = ("0" + (d.getMonth() + 1)).slice(-2);
  let day = ("0" + d.getDate()).slice(-2);
  let hour = ("0" + d.getHours()).slice(-2);
  let min = ("0" + d.getMinutes()).slice(-2);
  let sec = ("0" + d.getSeconds()).slice(-2);
  return year + "-" + month + "-" + day + " " + hour + ":" + min + ":" + sec;
}
