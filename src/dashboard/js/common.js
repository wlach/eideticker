// various utility functions used by all eideticker web interface pages

function getParameterByName(name) {
  var match = RegExp('[?&]' + name + '=([^&]*)').exec(window.location.search);
  if (!match)
    return null;
  
  return decodeURIComponent(match[1].replace(/\+/g, ' ')).replace(
      /[\"\']/g, ' ');
}

function parseDate(datestr) {
  var parsed = datestr.split("-");
  var year = parsed[0];
  var month = parsed[1] - 1; //Javascript months index from 0 instead of 1
  var day = parsed[2];

  return Date.UTC(year, month, day);
}

function getDateStr(timestamp) {
  var date = new Date(timestamp);
  var month = (date.getUTCMonth() + 1);
  var day = date.getUTCDate();
  return date.getUTCFullYear() + "-" + ((month < 10) ? "0" : "") + month + '-' + ((day < 10) ? "0" : "") + day;
}

var measures = {
  'checkerboard': { 'shortDesc': 'Checkerboard',
                    'longDesc': 'The measure is the sum of the percentages of frames that are checkerboarded over the entire capture. Lower values are better.' },
  'uniqueframes': { 'shortDesc': 'Unique frames',
                    'longDesc': 'The measure is a calculation of the average number of UNIQUE frames per second of capture. The theoretical maximum is 60 fps (which is what we are capturing), but note that if there periods where the page being captured is unchanging this number may be aritifically low.' },
  'fps': { 'shortDesc': 'Frames per second',
           'longDesc': 'The measure is a calculation of the average number of UNIQUE frames per second of capture. The theoretical maximum is 60 fps (which is what we are capturing), but note that if there periods where the page being captured is unchanging this number may be aritifically low.' },
  'timetostableframe': { 'shortDesc': 'Time to first stable frame (seconds)',
                         'longDesc': 'The time to the first frame of the capture where the image is stable (i.e. mostly unchanging). This is a startup metric that indicates roughly when things have stopped loading. Lower values are better.' },
  'timetoresponse': { 'shortDesc': 'Time to visible response (seconds)',
                      'longDesc': 'Time between event being first sent to device and an observable response. A long pause may indicate that the application is unresponsive.' },
  'overallentropy': { 'shortDesc': 'Overall entropy over length of capture',
                      'longDesc': 'Overall information content in frames of capture. Low values may indicate that some areas of the screen were left blank while the screen was redrawing. Higher values are generally better.' }
}
