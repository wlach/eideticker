"use strict";

var serverPrefix = ""; // set this to e.g. `http://eideticker.mozilla.org/` to serve remote data to a local server
function getResourceURL(path) {
  if (!path)
    return null;

  return serverPrefix + path;
}

function updateContent(testInfo, deviceId, branchId, testId, measureId) {
  $.getJSON(getResourceURL([deviceId, branchId, testId].join('/') + '.json'), function(dict) {
    if (!dict || !dict['testdata']) {
      $('#data-view').html("<p><b>No data for that device/test combination. :(</b></p>");
      return;
    }

    var testData = dict['testdata'];

    // figure out which measures could apply to this graph
    var availableMeasureIds = [];
    Object.keys(testData).forEach(function(product) {
      Object.keys(testData[product]).forEach(function(timestamp) {
        testData[product][timestamp].forEach(function(sample) {
          var measureIds = getMeasureIdsInSample(sample, overallMeasures);
          measureIds.forEach(function(measureId) {
            if (jQuery.inArray(measureId, availableMeasureIds) === -1) {
              availableMeasureIds.push(measureId);
            }
          });
        });
      });
    });

    $('#data-view').html(ich.graph({'title': testInfo.shortDesc,
                                    'measureDescription': overallMeasures[measureId].longDesc,
                                    'measures': measureDisplayList(availableMeasureIds, overallMeasures)
                                 }));

    // update graph
    updateGraph(testInfo.shortDesc, testData, measureId);

    $('#measure-'+measureId).attr("selected", "true");
    $('#measure').change(function() {
      var newMeasureId = $(this).val();
      window.location.hash = '/' + [ deviceId, branchId, testId, newMeasureId ].join('/');
    });

  });
}

function updateFooter() {
  $("#footer").css('margin-top', Math.max($("#chooser").height(),
                                          ($("#data-view").height() +
                                           $("#graph-main").height())));
}

function updateGraph(title, rawdata, measureId) {
  // show individual data points
  var graphdata = [];
  var color = 0;
  var uuidHash = {};

  var seriesIndex = 0;

  // get global maximum date (for baselining)
  var globalMaxDate = 0;
  Object.keys(rawdata).forEach(function(product) {
    var dates = Object.keys(rawdata[product]).map(parseTimestamp);
    globalMaxDate = Math.max(globalMaxDate, Math.max.apply(null, dates));
  });

  var products = Object.keys(rawdata).sort();

  products.forEach(function(product) {
    uuidHash[seriesIndex] = [];

    // point graph
    var series1 = {
      label: product,
      points: { show: true },
      color: color,
      data: []
    };

    Object.keys(rawdata[product]).sort().forEach(function(timestamp) {
      rawdata[product][timestamp].forEach(function(sample) {
        if (measureId in sample) {
          series1.data.push([ parseTimestamp(timestamp), sample[measureId] ]);
          var sourceRepo = sample.sourceRepo;
          if (!sourceRepo) {
            sourceRepo = "http://hg.mozilla.org/mozilla-central";
          }
          uuidHash[seriesIndex].push(sample.uuid);
        }
      });
    });
    graphdata.push(series1);

    var dates = series1.data.map(function(d) { return d[0]; });

    // line graph (aggregate average per day + baseline results if appropriate)
    var series2 = {
      lines: { show: true },
      color: color,
      data: [],
      clickable: false,
      hoverable: false
    };

    var lastSample;
    var lastData;
    Object.keys(rawdata[product]).sort().forEach(function(timestamp) {
      var numSamples = 0;
      var total = 0;
      rawdata[product][timestamp].forEach(function(sample) {
        lastSample = sample;
        if (sample[measureId]) {
          total += sample[measureId];
          numSamples++;
        }
      });
      lastData = [parseTimestamp(timestamp), total/numSamples];
      series2.data.push(lastData);
    });
    // if last sample was a baseline and there's a great data, extend
    // the baseline of the graph up to today
    if (lastSample.baseline === true && lastData[0] < globalMaxDate) {
      series2.data.push([globalMaxDate, lastData[1]]);
    }
    graphdata.push(series2);

    color++;
    seriesIndex += 2;
  });

  function updateDataPointDisplay(uuid, date, measureName, series) {
    $.getJSON(getResourceURL('metadata/' + uuid + '.json'), function(metadata) {
      function sliceIfExist(str) {
        if (str) {
          return str.slice(0, 12);
        }
        return null;
      }

      function updateDataPoint(prevRevision) {
        var defaultDetailParameter = getDefaultDetailParameter(measureName, metadata);
        $('#datapoint-info').html(ich.graphDatapoint({ 'uuid': uuid,
                                                       'videoURL': metadata.video,
                                                       'profileURL': metadata.profile,
                                                       'defaultDetailParameter': defaultDetailParameter,
                                                       'httpLog': metadata.httpLog ? true : false,
                                                       'measureName': measureName,
                                                       'date': getDateStr(metadata.appdate * 1000),
                                                       'buildRevision': sliceIfExist(metadata.buildRevision),
                                                       'gaiaRevision': sliceIfExist(metadata.gaiaRevision),
                                                       'prevRevision': prevRevision,
                                                       'revision': metadata.revision,
                                                       'sourceRepo': metadata.sourceRepo,
                                                       'buildId': metadata.buildId,
                                                       'measureValue': Math.round(100.0*metadata['metrics'][measureName])/100.0
                                                     }));

        $('#datapoint-info').css('left', $('#graph-main').width() + 20);
        $('#video').css('width', $('#video').parent().width());
        $('#video').css('max-height', $('#graph-container').height());
      }

      // try to find the previous revision
      var prevTimestamp = null;
      Object.keys(rawdata[series.label]).sort().forEach(function(timestamp) {
        if (parseTimestamp(timestamp) < date) {
          // potential candidate
          prevTimestamp = timestamp;
        }
      });

      if (prevTimestamp) {
        var prevDayData = rawdata[series.label][prevTimestamp];
        $.getJSON(getResourceURL('metadata/' + prevDayData[0].uuid + '.json'), function(prevMetadata) {
          updateDataPoint(prevMetadata.revision)
        });
      } else {
        updateDataPoint(null);
      }
    });
  }

  var showGraphLegend = (products.length > 1);

  function updateGraphDisplay() {
    var plot = $.plot($("#graph-container"), graphdata, {
      xaxis: {
        mode: "time",
        timeformat: "%m-%d"
      },
      yaxis: {
        axisLabel: overallMeasures[measureId].shortDesc,
        min: 0
      },
      legend: {
        show: showGraphLegend,
        position: "ne",
      },
      grid: { clickable: true, hoverable: true },
      zoom: { interactive: true },
      pan: { interactive: true }
    });

    updateFooter();

    // add zoom out button
    $('<div class="button" style="left:50px;top:20px">zoom out</div>').appendTo($("#graph-container")).click(function (e) {
      e.preventDefault();
      plot.zoomOut();
    });

    function showTooltip(x, y, contents) {
      $('<div id="tooltip">' + contents + '</div>').css( {
        position: 'absolute',
        display: 'none',
        top: y + 5,
        left: x + 5,
        border: '1px solid #fdd',
        padding: '2px',
        'background-color': '#fee',
        opacity: 0.80
      }).appendTo("body").fadeIn(200);
    }

    // Plot Hover tooltip
    var previousPoint = null;
    $("#graph-container").bind("plothover", function (event, pos, item) {
      if (item) {
        if (previousPoint != item.dataIndex) {
          var toolTip;
          var x = item.datapoint[0].toFixed(2),
          y = item.datapoint[1].toFixed(2);

          if (uuidHash[item.seriesIndex] && uuidHash[item.seriesIndex][item.dataIndex]) {
            toolTip = (item.series.label || item.series.hoverLabel) + " of " + getDateStr(item.datapoint[0]) + " = " + y;
          } else {
            toolTip = (item.series.label || item.series.hoverLabel) + " = " + y;
          }

          previousPoint = item.dataIndex;

          $("#tooltip").remove();
          showTooltip(item.pageX, item.pageY, toolTip);
        }
      } else {
        $("#tooltip").remove();
        previousPoint = null;
      }
    });

    $("#graph-container").bind("plotclick", function (event, pos, item) {
      plot.unhighlight();
      if (item) {
        var uuid = uuidHash[item.seriesIndex][item.dataIndex];
        updateDataPointDisplay(uuid, item.datapoint[0], measureId, item.series);
        plot.highlight(item.series, item.datapoint);
      } else {
        $('#datapoint-info').html(null);
      }
    });
  }

  updateGraphDisplay();
  var redisplayTimeout = null;
  $(window).resize(function() {
    if (redisplayTimeout)
      return;
    redisplayTimeout = window.setTimeout(function() {
      redisplayTimeout = null;
      updateGraphDisplay();
      updateDataPointDisplay();
    }, 200);
  });
}

$(function() {
  var graphData = {};

  $.getJSON(getResourceURL('devices.json'), function(deviceData) {
    var devices = deviceData['devices'];
    var deviceIds = Object.keys(devices).sort();

    var deviceBranchPairs = [];
    deviceIds.forEach(function(deviceId) {
      devices[deviceId].branches.forEach(function(branchId) {
        deviceBranchPairs.push([deviceId, branchId]);
      });
    });
    $.when.apply($, deviceBranchPairs.map(function(pair) {
      var deviceId = pair[0];
      var branchId = pair[1];

      return $.getJSON(getResourceURL([deviceId, branchId, 'tests.json'].join('/')),
                       function(testData) {
                         var tests = testData['tests'];
                         if (!devices[deviceId][branchId]) {
                           devices[deviceId][branchId] = {};
                         }
                         devices[deviceId][branchId]['tests'] = tests;
                       });
    })).done(function() {
      var defaultDeviceId = deviceIds[0];

      function getTestIdForDeviceAndBranch(deviceId, branchId, preferredTest) {
        var device = devices[deviceId];
        var tests = device[branchId].tests;
        var testIds = Object.keys(tests).sort();
        var testId;
        if (preferredTest && testIds.indexOf(preferredTest) >= 0) {
          // this deviceid/branch combo has our preferred test, return it
          return preferredTest;
        } else {
          // this deviceid/branch combo *doesn't* have our preferred test,
          // fall back to the first one
          return testIds[0];
        }
      }

      function updateDeviceChooser(preferredBranchId, preferredTest) {
        $('#device-chooser').empty();

        deviceIds.forEach(function(deviceId) {
          var device = devices[deviceId];

          var branchId;
          if (preferredBranchId && device.branches.indexOf(preferredBranchId) >= 0) {
            branchId = preferredBranchId;
          } else {
            branchId = device.branches.sort()[0];
          }

          var testId = getTestIdForDeviceAndBranch(deviceId, branchId, preferredTest);
          var defaultMeasureId = device[branchId].tests[testId].defaultMeasureId;

          var deviceURL = "#/" + [ deviceId, branchId, testId, defaultMeasureId ].join('/');
          $('<a href="' + deviceURL + '" id="device-' + deviceId + '" deviceid= ' + deviceId + ' class="list-group-item">' + devices[deviceId].name+'</a></li>').appendTo(
            $('#device-chooser'));
        });
      }

      function updateBranchChooser(deviceId, preferredTest) {
        $('#branch-chooser').empty();

        var device = devices[deviceId];
        device.branches.forEach(function(branchId) {
          var testId = getTestIdForDeviceAndBranch(deviceId, branchId, preferredTest);
          var defaultMeasureId = device[branchId].tests[testId].defaultMeasureId;

          var url = "#/" + [ deviceId, branchId, testId, defaultMeasureId ].join('/');
          $('<a href="' + url + '" id="branch-' + branchId + '" class="list-group-item">' + branchId +'</a></li>').appendTo(
            $('#branch-chooser'));
        });
      }

      var currentBranchId = null;
      var currentDeviceId = null;
      var currentTestId = null;

      var routes = {
        '/:deviceId/:branchId/:testId/:measureId': {
          on: function(deviceId, branchId, testId, measureId) {
            if (!devices[deviceId] || !devices[deviceId][branchId] || !devices[deviceId][branchId]['tests'][testId]) {
              $('#data-view').html("<p><b>That device/branch/test/measure combination does not seem to exist. Maybe you're using an expired link? <a href=''>Reload page</a>?</b></p>");
              return;
            }

            updateDeviceChooser(branchId, testId);
            updateBranchChooser(deviceId, testId);

            // update list of tests to be consistent with those of this
            // particular device (in case it changed)
            $('#test-chooser').empty();

            var tests = devices[deviceId][branchId].tests;
            var testKeys = Object.keys(tests).sort();
            testKeys.forEach(function(testKey) {
              $('<a id="' + testKey + '" class="list-group-item">' + testKey + '</a>').appendTo($('#test-chooser'));
            });

            // update all test links to be relative to the new test or device
            $('#test-chooser').children('a').each(function() {
              var testIdAttr = $(this).attr('id');
              if (testIdAttr) {
                var defaultMeasureId = tests[testIdAttr].defaultMeasureId;
                $(this).attr('href', '#/' +
                             [ deviceId, branchId, testIdAttr,
                               defaultMeasureId ].join('/'));
              }
            });

            // highlight chosen selections in choosers
            $('#device-chooser').children('#device-'+deviceId).addClass("active");
            $('#branch-chooser').children('#branch-'+branchId.replace('.', '\\.')).addClass("active");
            $('#test-chooser').children('#'+testId).addClass("active");

            var testInfo = tests[testId];
            updateFooter();
            updateContent(testInfo, deviceId, branchId, testId, measureId);
          }
        }
      };

      var defaultDeviceId = deviceIds[0];
      var defaultBranchId = devices[defaultDeviceId].branches[0];
      var defaultTestId = Object.keys(devices[defaultDeviceId][defaultBranchId].tests)[0];
      var defaultMeasureId = devices[defaultDeviceId][defaultBranchId].tests[defaultTestId].defaultMeasureId;

      var router = Router(routes).init('/' + [ defaultDeviceId,
                                               defaultBranchId,
                                               defaultTestId,
                                               defaultMeasureId ].join('/'));
    });
  });
});
