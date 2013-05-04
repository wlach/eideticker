"use strict";

function parseDate(datestr) {
  var parsed = datestr.split("-");
  var year = parsed[0];
  var month = parsed[1] - 1; //Javascript months index from 0 instead of 1
  var day = parsed[2];

  return Date.UTC(year, month, day);
}

var measures = {
  'checkerboard': { 'shortDesc': 'Checkerboard',
                    'longDesc': 'The measure is the sum of the percentages of frames that are checkerboarded over the entire capture. Lower values are better.' },
  'uniqueframes': { 'shortDesc': 'Unique frames',
                    'longDesc': 'The measure is a calculation of the average number of UNIQUE frames per second of capture. The theoretical maximum is 60 fps (which is what we are capturing), but note that if there periods where the page being captured is unchanging this number may be aritifically low.' },
  'fps': { 'shortDesc': 'Frames per second',
           'longDesc': 'The measure is a calculation of the average number of UNIQUE frames per second of capture. The theoretical maximum is 60 fps (which is what we are capturing), but note that if there periods where the page being captured is unchanging this number may be aritifically low.' },
  'timetostableframe': { 'shortDesc': 'Time to first stable frame (seconds)',
                         'longDesc': 'The time to the first frame of the capture where the image is stable (i.e. mostly unchanging). This is a startup metric that indicates roughly when things have stopped loading. Lower values are better.' }
}

function updateContent(testInfo, deviceId, testId, measureId) {
  $.getJSON(deviceId + '/' + testId + '.json', function(dict) {
    if (!dict || !dict['testdata']) {
      $('#content').html("<p><b>No data for that device/test combination. :(</b></p>");
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

    $('#content').html(ich.graph({'title': testInfo.shortDesc,
                                  'measureDescription': measures[measureId].longDesc,
                                  'measures': availableMeasures.map(
                                    function(measureId) {
                                      return { 'id': measureId,
                                               'desc': measures[measureId].shortDesc
                                             };
                                    })
                                 }));

    // update graph
    updateGraph(testData, measureId);

    $('#measure-'+measureId).attr("selected", "true");
    $('#measure').change(function() {
      var newMeasure = $(this).val();
      window.location.hash = '/' + [ deviceId, testId, newMeasure ].join('/');
    });

  });
}

function updateGraph(rawdata, measure) {
  // show individual data points
  var graphdata = [];
  var color = 0;
  var metadataHash = {};

  var seriesIndex = 0;

  // get global maximum date (for baselining)
  var globalMaxDate = 0;
  Object.keys(rawdata).forEach(function(type) {
    var dates = Object.keys(rawdata[type]).map(parseDate);
    globalMaxDate = Math.max(globalMaxDate, Math.max.apply(null, dates));
  });

  Object.keys(rawdata).sort().forEach(function(type) {
    metadataHash[seriesIndex] = [];

    // point graph
    var series1 = {
      label: type,
      points: { show: true },
      color: color,
      data: []
    };

    var prevRevision = null;
    Object.keys(rawdata[type]).sort().forEach(function(datestr) {
      rawdata[type][datestr].forEach(function(sample) {
        if (measure in sample) {
          series1.data.push([ parseDate(datestr), sample[measure] ]);
          metadataHash[seriesIndex].push({
            'videoURL': sample.video,
            'dateStr': datestr,
            'appDate': sample.appdate,
            'revision': sample.revision,
            'gaiaRevision': sample.gaiaRevision,
            'prevRevision': prevRevision,
            'buildId': sample.buildid,
            'profileURL': sample.profile
          });
        }
      });
      prevRevision = rawdata[type][datestr][0].revision;
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
      container: $("#legend"),
    },
    grid: { clickable: true, hoverable: true },
    zoom: { interactive: true },
    pan: { interactive: true }
  });

    // add zoom out button
  $('<div class="button" style="right:20px;top:20px">zoom out</div>').appendTo($("#graph-container")).click(function (e) {
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

        if (metadataHash[item.seriesIndex] && metadataHash[item.seriesIndex][item.dataIndex]) {
          var metadata = metadataHash[item.seriesIndex][item.dataIndex];
          toolTip = (item.series.label || item.series.hoverLabel) + " of " + (metadata.appDate || "'Unknown Date'") + " = " + y;
        } else {
          console.log(JSON.stringify(item.series));
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
      var metadata = metadataHash[item.seriesIndex][item.dataIndex];
      $('#datapoint-info').html(ich.graphDatapoint({ 'videoURL': metadata.videoURL,
                                                     'profileURL': metadata.profileURL,
                                                     'measureName': measure,
                                                     'date': metadata.dateStr,
                                                     'appDate': metadata.appDate,
                                                     'gaiaRevision': metadata.gaiaRevision.slice(0, 8),
                                                     'revision': metadata.revision,
                                                     'prevRevision': metadata.prevRevision,
                                                     'buildId': metadata.buildId,
                                                     'measureValue': Math.round(100.0*item.datapoint[1])/100.0
                                                   }));
      $('#video').css('width', $('#video').parent().width());
      $('#video').css('max-height', $('#graph-container').height());

      plot.highlight(item.series, item.datapoint);
    } else {
      $('#datapoint-info').html(null);
    }
  });
}

$(function() {
  var graphData = {};
  $.getJSON('devices.json', function(deviceData) {
    var devices = deviceData['devices'];
    var deviceIds = Object.keys(devices);

    deviceIds.forEach(function(deviceId) {
      $('<li id="device-' + deviceId + '-li" deviceid= ' + deviceId + '><a>'+devices[deviceId].name+'</a></li>').appendTo($('#device-chooser'));

      $.getJSON([deviceId, 'tests.json'].join('/'), function(testData) {
        var tests = testData['tests'];
        devices[deviceId]['tests'] = tests;
      });

    });

    // FIXME: should probably have some kind of maximum timeout here...
    function setupRoutes() {
      deviceIds.forEach(function(deviceId) {
        // not ready, call again shortly
        if (!devices[deviceId]['tests']) {
          setTimeout(setupRoutes, 100);
          return;
        }
      });

      var routes = {
        '/:deviceId/:testId/:measureId': {
          on: function(deviceId, testId, measure) {
            if (!devices[deviceId] || !devices[deviceId]['tests'][testId]) {
              $('#content').html("<p><b>That device/test/measure combination does not seem to exist. Maybe you're using an expired link? <a href=''>Reload page</a>?</b></p>");
              return;
            }

            // update list of tests to be consistent with those of this
            // particular device (in case it changed)
            $('#test-chooser').empty();

            var tests = devices[deviceId]['tests'];
            var testKeys = Object.keys(tests).sort();
            testKeys.forEach(function(testKey) {
              $('<li id="' + testKey + '-li" testid = ' + testKey + '><a>' + testKey + '</a></li>').appendTo($('#test-chooser'));
            });

            // update all links to be relative to the new test or device
            $('#device-chooser').children('li').removeClass("active");
            $('#device-chooser').children('#device-'+deviceId+'-li').addClass("active");
            $('#device-chooser').children('li').each(function() {
              var defaultMeasure = devices[deviceId]['tests'][testKeys[0]].defaultMeasure;
              $(this).children('a').attr('href', '#/' + [ $(this).attr('deviceid'),
                                                          testKeys[0],
                                                          defaultMeasure ].join('/'));
            });

            $('#test-chooser').children('li').removeClass("active");
            $('#test-chooser').children('#'+testId+'-li').addClass("active");

            $('#test-chooser').children('li').each(function() {
              var testIdAttr = $(this).attr('testid');
              if (testIdAttr) {
                var defaultMeasure = tests[testIdAttr].defaultMeasure;
                $(this).children('a').attr('href', '#/' +
                                           [ deviceId, testIdAttr,
                                             defaultMeasure ].join('/'));
              }
            });

            var testInfo = tests[testId];
            updateContent(testInfo, deviceId, testId, measure);
          }
        }
      };

      var defaultDeviceId = deviceIds[0];
      var initialTestKey = Object.keys(devices[defaultDeviceId]['tests']);
      var initialTest = devices[defaultDeviceId]['tests'][initialTestKey]

      var router = Router(routes).init('/' + [ defaultDeviceId,
                                               initialTestKey,
                                               initialTest.defaultMeasure ].join('/'));
    }

    setTimeout(setupRoutes, 100);
  });
});
