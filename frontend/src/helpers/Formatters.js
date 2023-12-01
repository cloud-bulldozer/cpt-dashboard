export function formatTime(time) {
    // Hours, minutes and seconds
    var hrs = ~~(time / 3600);
    var mins = ~~((time % 3600) / 60);
    var secs = ~~time % 60;

    // Output like "1:01" or "4:03:59" or "123:03:59"
    var ret = "";
    if (hrs > 0) {
        ret += "" + hrs + ":" + (mins < 10 ? "0" : "");
    }
    ret += "" + mins + ":" + (secs < 10 ? "0" : "");
    ret += "" + secs;
    return ret;
}

export function getFormattedDate(date) {
    let d = new Date();
    if (typeof date === 'string' || date instanceof String)
        d = new Date(date);
    else
        d = new Date(date.props.value);

    var year = d.getFullYear();
    var month = ("0" + (d.getMonth() + 1)).slice(-2);
    var day  = ("0" + (d.getDate())).slice(-2);
    var hour =  ("0" + (d.getHours())).slice(-2);
    var min =  ("0" + (d.getMinutes())).slice(-2);
    var sec = ("0" + (d.getSeconds())).slice(-2);
    return year + "-" + month + "-" + day + " " + hour + ":" +  min + ":" + sec;
}
