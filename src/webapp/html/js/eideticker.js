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

function getScaledCaptureImageDimensions(captureSummary, minWidth) {
  return {
    'width': parseInt(minWidth),
    'height': parseInt((minWidth / captureSummary.width) * captureSummary.height)
  };
}

function getCaptureImageURL(captureId, frameNum, width, height, cropped) {
  return "api/captures/" + captureId + "/images/" + frameNum +
    "?width= " + width + "&height=" + height + "&cropped=" + +cropped;
}

function getCaptureThumbnailImageURL(captureId, captureSummary, frameNum, cropped) {
  var dimensions = getScaledCaptureImageDimensions(captureSummary, 400);
  return getCaptureImageURL(captureId, frameNum, dimensions.width,
                            dimensions.height, cropped);
}

function getFrameDiffImageURL(captureId, frameNum1, frameNum2, width, height) {
  return "api/captures/" + captureId + "/framediff/images/" +
    frameNum1 + '-' + frameNum2 + "?width=" + width + "&height=" + height;
}

function getFrameDiffThumbnailImageURL(captureId, captureSummary, frameNum1, frameNum2) {
  var dimensions = getScaledCaptureImageDimensions(captureSummary, 400);
  return getFrameDiffImageURL(captureId, frameNum1, frameNum2, dimensions.width,
                              dimensions.height);
}