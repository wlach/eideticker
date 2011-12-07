// this crude "class" allows us to avoid fetching the same resource over and over
var resourceCache = {
  get: function(resourceURL, cb) {
    if (this.urlCache[resourceURL]) {
      cb(this.urlCache[resourceURL]);
    } else {
      if (!this.cbs[resourceURL]) { // first
        this.cbs[resourceURL] = [cb];
        var that = this;

        $.getJSON(resourceURL, function(data) {
          that.urlCache[resourceURL] = data;
          that.cbs[resourceURL].forEach(function(cb) {
            cb(data);
          });

          that.cbs[resourceURL] = [];
        });
      } else {
        this.cbs[resourceURL][this.cbs[resourceURL].length] = cb;
      }
    }
  },
  urlCache: {},
  cbs: {}
};

function getTimeStr(seconds) {
  var minutes = Math.floor(seconds / 60);
  var seconds = (seconds - (minutes * 60)).toFixed(2);

  var timeStr = "";
  if (minutes > 0) {
    timeStr += (minutes + "min ");
  }
  return timeStr + seconds + " sec";
}

function getParamStr(paramdict) {
  return Object.keys(paramdict).map(function(key) {
    return key + "=" + +(paramdict[key]);
  }).join("&");
}

function getScaledCaptureImageDimensions(captureSummary, minWidth) {
  return {
    width: parseInt(minWidth),
    height: parseInt((minWidth / captureSummary.width) * captureSummary.height)
  };
}

function getCaptureImageURL(captureId, frameNum, params) {
  return "api/captures/" + captureId + "/images/" + frameNum +
    "?" + getParamStr(params);
}

function getCaptureThumbnailImageURL(captureId, captureSummary, frameNum, params) {
  var params = jQuery.extend({}, params,
                             getScaledCaptureImageDimensions(captureSummary,
                                                             400));
  return getCaptureImageURL(captureId, frameNum, params);
}

function getFrameDiffImageURL(captureId, frameNum1, frameNum2, params) {
  return "api/captures/" + captureId + "/framediff/images/" +
    frameNum1 + '-' + frameNum2 + "?" + getParamStr(params);
}

function getFrameDiffThumbnailImageURL(captureId, captureSummary, frameNum1, frameNum2) {
  var params = getScaledCaptureImageDimensions(captureSummary, 400);

  return getFrameDiffImageURL(captureId, frameNum1, frameNum2, params);
}