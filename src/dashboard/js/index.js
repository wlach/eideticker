"use strict";

var serverPrefix = ""; // set this to e.g. `http://eideticker.mozilla.org/` to serve remote data to a local server
function getResourceURL(path) {
  if (!path)
    return null;

  return serverPrefix + path;
}

function updateContent(testInfo, deviceId, testId, measureId) {
  $.getJSON(getResourceURL(deviceId + '/' + testId + '.json'), function(dict) {
    if (!dict || !dict['testdata']) {
      $('#data-view').html("<p><b>No data for that device/test combination. :(</b></p>");
      return;
    }

    var testData = dict['testdata'];

    // figure out which measures could apply to this graph
    var availableMeasures = [];
    Object.keys(testData).forEach(function(type) {
      Object.keys(testData[type]).forEach(function(datestr) {
        testData[type][datestr].forEach(function(sample) {
          Object.keys(measures).forEach(function(measure) {
            if (jQuery.inArray(measure, Object.keys(sample)) !== -1 &&
                jQuery.inArray(measure, availableMeasures) === -1) {
              availableMeasures.push(measure);
            }
          });
        });
      });
    });

    $('#data-view').html(ich.graph({'title': testInfo.shortDesc,
                                  'measureDescription': measures[measureId].longDesc,
                                  'measures': availableMeasures.map(
                                    function(measureId) {
                                      return { 'id': measureId,
                                               'desc': measures[measureId].shortDesc
                                             };
                                    })
                                 }));

    // update graph
    updateGraph(testInfo.shortDesc, testData, measureId);

    $('#measure-'+measureId).attr("selected", "true");
    $('#measure').change(function() {
      var newMeasure = $(this).val();
      window.location.hash = '/' + [ deviceId, testId, newMeasure ].join('/');
    });

  });
}

function updateFooter() {
  $("#footer").css('margin-top', Math.max($("#chooser").height(),
                                          ($("#data-view").height() +
                                           $("#graph-main").height())));
}

function updateGraph(title, rawdata, measure) {
  // show individual data points
  var graphdata = [];
  var color = 0;
  var uuidHash = {};

  var seriesIndex = 0;

  // get global maximum date (for baselining)
  var globalMaxDate = 0;
  Object.keys(rawdata).forEach(function(type) {
    var dates = Object.keys(rawdata[type]).map(parseDate);
    globalMaxDate = Math.max(globalMaxDate, Math.max.apply(null, dates));
  });

  Object.keys(rawdata).sort().forEach(function(type) {
    uuidHash[seriesIndex] = [];

    // point graph
    var series1 = {
      label: type,
      points: { show: true },
      color: color,
      data: []
    };

    Object.keys(rawdata[type]).sort().forEach(function(datestr) {
      rawdata[type][datestr].forEach(function(sample) {
        if (measure in sample) {
          series1.data.push([ parseDate(datestr), sample[measure] ]);
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
      hoverLabel: "Average per day for " + type,
      lines: { show: true },
      color: color,
      data: [],
      clickable: false,
      hoverable: false
    };

    var lastSample;
    var lastData;
    Object.keys(rawdata[type]).sort().forEach(function(datestr) {
      var numSamples = 0;
      var total = 0;
      rawdata[type][datestr].forEach(function(sample) {
        lastSample = sample;
        if (sample[measure]) {
          total += sample[measure];
          numSamples++;
        }
      });
      lastData = [parseDate(datestr), total/numSamples];
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
        $('#datapoint-info').html(ich.graphDatapoint({ 'uuid': uuid,
                                                       'videoURL': metadata.video,
                                                       'profileURL': metadata.profile,
                                                       'frameDiff': metadata.frameDiff ? true : false,
                                                       'httpLog': metadata.httpLog ? true : false,
                                                       'measureName': measureName,
                                                       'date': getDateStr(date),
                                                       'appDate': metadata.appdate,
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
      var prevDateStr = null;
      Object.keys(rawdata[series.label]).sort().forEach(function(dateStr) {
        if (parseDate(dateStr) < date) {
          // potential candidate
          prevDateStr = dateStr;
        }
      });

      if (prevDateStr) {
        var prevDayData = rawdata[series.label][prevDateStr];
        $.getJSON(getResourceURL('metadata/' + prevDayData[0].uuid + '.json'), function(prevMetadata) {
          updateDataPoint(prevMetadata.revision)
        });
      } else {
        updateDataPoint(null);
      }
    });
  }

  function updateGraphDisplay() {
    var plot = $.plot($("#graph-container"), graphdata, {
      xaxis: {
        mode: "time",
        timeformat: "%m-%d"
      },
      yaxis: {
        axisLabel: measures[measure].shortDesc,
        min: 0
      },
      legend: {
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
        updateDataPointDisplay(uuid, item.datapoint[0], measure, item.series);
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
    var deviceIds = Object.keys(devices);

    $.when.apply($, deviceIds.map(function(deviceId) {
      return $.getJSON(getResourceURL([deviceId, 'tests.json'].join('/')),
                       function(testData) {
                         var tests = testData['tests'];
                         devices[deviceId]['tests'] = tests;
                       });
    })).done(function() {

      // initialize device chooser
      deviceIds.forEach(function(deviceId) {
        var tests = devices[deviceId].tests;
        var firstTestKey = Object.keys(tests).sort()[0];
        var defaultMeasure = tests[firstTestKey].defaultMeasure;

        var deviceURL = "#/" + [ deviceId, firstTestKey, defaultMeasure ].join('/');
        $('<a href="' + deviceURL + '" id="device-' + deviceId + '" deviceid= ' + deviceId + ' class="list-group-item">' + devices[deviceId].name+'</a></li>').appendTo(
            $('#device-chooser'));
      });

      var routes = {
        '/:deviceId/:testId/:measureId': {
          on: function(deviceId, testId, measure) {
            if (!devices[deviceId] || !devices[deviceId]['tests'][testId]) {
              $('#data-view').html("<p><b>That device/test/measure combination does not seem to exist. Maybe you're using an expired link? <a href=''>Reload page</a>?</b></p>");
              return;
            }

            // update device chooser
            $('#device-chooser').children('a').removeClass("active");
            $('#device-chooser').children('#device-'+deviceId).addClass("active");

            // update list of tests to be consistent with those of this
            // particular device (in case it changed)
            $('#test-chooser').empty();

            var tests = devices[deviceId].tests;
            var testKeys = Object.keys(tests).sort();
            testKeys.forEach(function(testKey) {
              $('<a id="' + testKey + '" class="list-group-item">' + testKey + '</a>').appendTo($('#test-chooser'));
            });

            // update all test links to be relative to the new test or device
            $('#test-chooser').children('a').removeClass("active");
            $('#test-chooser').children('#'+testId).addClass("active");

            $('#test-chooser').children('a').each(function() {
              var testIdAttr = $(this).attr('id');
              if (testIdAttr) {
                var defaultMeasure = tests[testIdAttr].defaultMeasure;
                $(this).attr('href', '#/' +
                             [ deviceId, testIdAttr,
                               defaultMeasure ].join('/'));
              }
            });

            var testInfo = tests[testId];
            updateFooter();
            updateContent(testInfo, deviceId, testId, measure);
          }
        }
      };

      var defaultDeviceId = deviceIds[0];
      var initialTestKey = Object.keys(devices[defaultDeviceId]['tests'])[0];
      var initialTest = devices[defaultDeviceId]['tests'][initialTestKey]

      var router = Router(routes).init('/' + [ defaultDeviceId,
                                               initialTestKey,
                                               initialTest.defaultMeasure ].join('/'));
    });
  });
});
