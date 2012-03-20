function displayFrameDiffs(captureId, minFrameNum, maxFrameNum, threshold) {
  resourceCache.get('api/captures/' + captureId, function(captureSummary) {
    resourceCache.get('api/captures/' + captureId + '/framediff', function(frameDiffs) {
      var i = 1;
      var groups = [ { start: 1 } ];
      var lastUnique = false;
      var visibleLength = 1;
      frameDiffs.forEach(function(diff) {
        if (diff > threshold) {
          lastUnique = true;
          visibleLength++;

          if (visibleLength > 5) {
            groups[groups.length] = { start: i };
            visibleLength = 1;
          }
        } else if (lastUnique) {
          visibleLength++;
          lastUnique = false;
        }

        // Update end
        if (groups.length > 0) {
          groups[groups.length-1].end = (i+1);
        }
        i++;
      });

      if (minFrameNum === 0 && maxFrameNum === 0) {
        minFrameNum = groups[0].start;
        maxFrameNum = groups[0].end;
      }

      var visibleGroups = [];
      var somePreviousInvisible = false;
      var someNextInvisible = false;
      var previous = null;
      var next = null;
      for (i=0; i<groups.length; i++) {
        var group = groups[i]
        if (group.start >= minFrameNum && group.end <= maxFrameNum) {

          // previous next
          if (i>0) {
            previous = groups[(i-1)].start + "-" + groups[(i-1)].end;
          }
          if (i < (groups.length-1)) {
            next = groups[(i+1)].start + "-" + groups[(i+1)].end;
          }
          if ((i-2) > 0) {
            somePreviousInvisible = true;
          }
          // elements before current
          for (var j=(i-1); (j>=0 && j>=(i-2)); j--) {
            visibleGroups.unshift(groups[j]);
          }

          // current element
          visibleGroups.push(group);
        } else if (group.end > maxFrameNum) {

          // elements after current
          visibleGroups.push(group);
        }

        // max # of elements visible at a time
        if (visibleGroups.length > 5) {
          break;
        }
      }
      if (i < (groups.length-1)) {
        someNextInvisible = true;
      }

      var frameViews = [];
      var frame1_num=minFrameNum;
      var frame2_num=minFrameNum;
      for (i=minFrameNum; i<maxFrameNum; i++) {
        var frameIndex = (i-1);
        var frameDiff = frameDiffs[frameIndex];
        if (frameDiff <= threshold) {
          frame2_num=i;
        } else {
          if (frame1_num !== frame2_num) {
            // push an identity frame view
            frameViews.push({
              frame1_num: frame1_num,
              frame2_num: frame2_num,
              frame1_thumb_url: getCaptureThumbnailImageURL(captureId, captureSummary, frame1_num, {}),
              frame1_url: getCaptureImageURL(captureId, frame1_num, {})
            });
          }
          // push a framediff View
          frameViews.push({
            frame1_num: i,
            frame2_num: i+1,
            frame1_thumb_url: getCaptureThumbnailImageURL(captureId, captureSummary, i, {}),
            frame1_url: getCaptureImageURL(captureId, i, {}),
            frame2_thumb_url: getCaptureThumbnailImageURL(captureId, captureSummary, i+1, {}),
            frame2_url: getCaptureImageURL(captureId, i+1, {}),
            framediff_thumb_url: getFrameDiffThumbnailImageURL(captureId, captureSummary, i, i+1),
            framediff_url: getFrameDiffImageURL(captureId, i, i+1, {}),
            framediff: frameDiff
          });

          frame1_num=frame2_num=(i+1);
        }
      }
      if (frame1_num !== frame2_num) {
        // push an identity frame view
        frameViews.push({
          frame1_num: frame1_num,
          frame2_num: frame2_num,
          frame1_thumb_url: getCaptureThumbnailImageURL(captureId, captureSummary, frame1_num, 
                                                        {}),
          frame1_url: getCaptureImageURL(captureId, frame1_num, {})
        });
      }

      $("#framediff-viz").html(ich.framediff_viz({
        captureid: captureId,
        threshold: threshold,
        frameviews: frameViews,
        visiblegroups: visibleGroups,
        somepreviousinvisible: somePreviousInvisible,
        somenextinvisible: someNextInvisible,
        previous: previous,
        next: next
      }));
      $("#" + minFrameNum + "-" + maxFrameNum).addClass("active");
    });
  });
}

function getFrameDiffGroups(captureSummary, frameDiffs, threshold, groupSize) {
  var i = 1;
  var groups = [ { start: 1 } ];
  var lastUnique = false;
  var visibleLength = 1;
  frameDiffs.forEach(function(diff) {
    if (diff > threshold) {
      lastUnique = true;
      visibleLength++;

      if (groupSize && visibleLength > groupSize) {
        groups[groups.length] = { start: i };
        visibleLength = 1;
      }
    } else if (lastUnique) {
      visibleLength++;
      lastUnique = false;
    }

    // Update end
    if (groups.length > 0) {
      groups[groups.length-1].end = (i+1);
    }
    i++;
  });

  return groups;
}

function getFrameViews(captureId, captureSummary, frameDiffs, minFrameNum, maxFrameNum) {
}

function displayCheckerboard(captureId, captureSummary) {
  resourceCache.get('api/captures/' + captureId + '/checkerboard', function(checkerboardSummary) {
    resourceCache.get('api/captures/' + captureId + '/framediff', function(frameDiffs) {

      $("#maincontent").html(ich.checkerboard_summary({
        checkerboardAreaDuration: checkerboardSummary.areaDuration,
        numCheckerboards: checkerboardSummary.numCheckerboards,
        numFrames: checkerboardSummary.numFrames
      }));

      //var frameDiffGroup = getFrameDiffGroups(captureSummary, frameDiffs, 2500, 0)[0];
      var frameViews = [];
      var frame1_num = 1;
      var frame2_num = 1;
      var minFrameNum = 1;
      var maxFrameNum = captureSummary.numFrames+1;

      for (i=minFrameNum; i<maxFrameNum; i++) {
        var frameIndex = (i-1);
        var frameDiff = frameDiffs[frameIndex];
        if (frameDiff <= 2500) {
          frame2_num=i;
        } else {
          if (frame1_num !== frame2_num) {
            frameViews.push({
              title: "Frames " + frame1_num + " - " + frame2_num,
              images: [
                { url: getCaptureImageURL(captureId, frame1_num, {}),
                  thumb_url: getCaptureThumbnailImageURL(captureId, captureSummary, frame1_num,
                                                         {})
                },
                { url: getCheckerboardImageURL(captureId, captureSummary, i, {}),
                  thumb_url: getCheckerboardThumbnailImageURL(captureId, captureSummary, i)
                }
              ],
              extra_info: null
            });
          }
          // push a single frame view
          frameViews.push({
            title: "Frame " + frame1_num,
            images: [
              { url: getCaptureImageURL(captureId, frame1_num, {}),
                thumb_url: getCaptureThumbnailImageURL(captureId, captureSummary, frame1_num,
                                                       {})
              },
              { url: getCheckerboardImageURL(captureId, captureSummary, i, {}),
                thumb_url: getCheckerboardThumbnailImageURL(captureId, captureSummary, i)
              }
            ],
            extra_info: null
          });

          frame1_num=frame2_num=(i+1);
        }
      }
      if (frame1_num !== frame2_num) {
        // push an identity frame view
        frameViews.push({
          title: "Frames " + frame1_num + " - " + frame2_num,
          images: [
            { url: getCaptureImageURL(captureId, frame1_num, {}),
              thumb_url: getCaptureThumbnailImageURL(captureId, captureSummary, frame1_num,
                                                     {})
            },
            { url: getCheckerboardImageURL(captureId, captureSummary, i, {}),
              thumb_url: getCheckerboardThumbnailImageURL(captureId, captureSummary, i)
            }
          ],
          extra_info: null
        });
      }

      $("#checkerboard-viz").html(ich.checkerboard_viz({
        captureid: captureId,
        frameviews: frameViews
      }));
    });
  });
}

$(function() {
  var router = Router({
    '/([^\/]*)': {
      on: function(captureId) {
        resourceCache.get('api/captures/' + captureId, function(captureSummary) {
          $('#header').html(ich.capture_header( {
            captureId: captureId,
            title: captureSummary.name
          }));
        });
      },
      '/summary': {
        on: function(captureId) {
          resourceCache.get('api/captures/' + captureId, function(captureSummary) {
            $('#summary-tab').addClass('active');
            $("#maincontent").html(ich.capture_summary({}));
            if (captureSummary.numFrames > 0) {
              var dimensions = getScaledCaptureImageDimensions(captureSummary, 400);
              $('#capture-video').html(ich.capture_video({
                url: 'api/captures/' + captureId + '/video/',
                width: dimensions.width,
                height: dimensions.height
              }));
            }
            $('#capture-detail').html(ich.capture_detail({
              date: captureSummary.date,
              num_frames: captureSummary.numFrames,
              device: captureSummary.device,
              length_str: getTimeStr(captureSummary.length)
            }));
          });
        }
      },
      '/framediff-\([0-9]+\)': {
        on: function(captureId, threshold) {
          resourceCache.get('api/captures/' + captureId, function(captureSummary) {
            $('#framediff-tab').addClass('active');

            $("#maincontent").html(ich.loading_screen({}));
            $("#loading_element").spin();

            resourceCache.get('api/captures/' + captureId + '/framediff', function(framediffs) {
              $("#maincontent").html(ich.framediff_summary({}));
              var uniqueFrames = framediffs.reduce(function(prev, curr, i, a) {
                if (curr > threshold ) {
                  return prev+1;
                }
                return prev;
              }, 0);
              var minFPS = (uniqueFrames / captureSummary.numFrames)*60.0;

              $("#framediff-analysis-results").html(ich.framediff_analysis_results({
                unique: uniqueFrames,
                total: captureSummary.numFrames,
                minfps: minFPS
              }));

              $("#rgb-diff-threshold").val(threshold);
              $("#rgb-diff-threshold").change(function() {
                window.location.hash = '/'+captureId+'/framediff-'+$("#rgb-diff-threshold").val();
              });
            });

            displayFrameDiffs(captureId, 0, 0, threshold);
          });
        },
        '/([0-9]+)-([0-9]+)': {
          on: function(captureId, threshold, minFrameNum, maxFrameNum) {
            displayFrameDiffs(captureId, parseInt(minFrameNum), parseInt(maxFrameNum), threshold);
          }
        }
      },
      '/checkerboard': {
        on: function(captureId, threshold) {
          resourceCache.get('api/captures/' + captureId, function(captureSummary) {
            $('#checkerboard-tab').addClass('active');

            $("#maincontent").html(ich.loading_screen({}));
            $("#loading_element").spin();

            displayCheckerboard(captureId, captureSummary);
          });
        }
      }
    }
  }).use({ recurse: 'forward' }).init();
});
