"use strict";

function parseDate(datestr) {
  var parsed = datestr.split("-");
  var year = parsed[0];
  var month = parsed[1] - 1; //Javascript months index from 0 instead of 1
  var day = parsed[2];

  return Date.UTC(year, month, day);
}

function updateContent(graphTitle, testName, measure) {

  var measureDescription;
  if (measure === "checkerboard") {
    measureDescription = 'The measure is the sum of the percentages of frames that are checkerboarded over the entire capture. Lower values are better.';
  } else if (measure === "fps") {
    measureDescription = 'The measure is a calculation of the average number of UNIQUE frames per second of capture. The theoretical maximum is 60 fps (which is what we are capturing), but note that if there periods where the page being captured is unchanging this number may be aritifically low.';
  } else {
    measureDescription = 'The measure is a calculation of the total number of UNIQUE frames in the capture. Higher values generally indicate more fluid animations.';
  }

  $('#content').html(ich.graph({'title': graphTitle,
                                'measureDescription': measureDescription
                               }));
  $('#measure-'+measure).attr("selected", "true");
  $('#measure').change(function() {
    var newMeasure = $(this).val();
    window.location.hash = '/' + [ testName, newMeasure ].join('/');
  });
}

function updateGraph(rawdata, measure) {
  // show individual data points
  var graphdata = [];
  var color = 0;
  var metadataHash = {};

  var seriesIndex = 0;
  Object.keys(rawdata).sort().forEach(function(type) {
    metadataHash[seriesIndex] = [];
    // point graph
    var series1 = {
      label: type,
      points: { show: true },
      color: color,
      data: []
    };

    Object.keys(rawdata[type]).sort().forEach(function(datestr) {
      rawdata[type][datestr].forEach(function(sample) {
        series1.data.push([ parseDate(datestr), sample[measure] ]);
        metadataHash[seriesIndex].push({'videoURL': sample.video, 'dateStr': datestr, 'appDate': sample.appdate, 'revision': sample.revision, 'buildId': sample.buildid });
      });
    });
    graphdata.push(series1);

    // line graph (aggregate average per day)
    var series2 = {
      lines: { show: true },
      color: color,
      data: [],
      clickable: false
    };
    Object.keys(rawdata[type]).forEach(function(datestr) {
      var numSamples = 0;
      var total = 0;
      rawdata[type][datestr].forEach(function(sample) {
        total += sample[measure];
        numSamples++;
      });

      series2.data.push([parseDate(datestr), total/numSamples]);
    });
    series2.data.sort();
    graphdata.push(series2);

    color++;
    seriesIndex += 2;
  });

  var axisLabel;
  if (measure == "checkerboard") {
    axisLabel = "Checkerboard";
  } else if (measure === "uniqueframes") {
    axisLabel = "Unique frames";
  } else {
    axisLabel = "Frames per second";
  }

  var plot = $.plot($("#graph-container"), graphdata, {
    xaxis: {
      mode: "time",
      timeformat: "%0m-%0d"
    },
    yaxis: {
      axisLabel: axisLabel,
      min: 0
    },
    legend: {
      container: $("#legend"),
    },
    grid: { clickable: true, hoverable: true },
  });

  $("#graph-container").bind("plotclick", function (event, pos, item) {
    plot.unhighlight();
    if (item) {
      var metadata = metadataHash[item.seriesIndex][item.dataIndex];
      $('#datapoint-info').html(ich.graphDatapoint({ 'videoURL': metadata.videoURL,
                                                     'measureName': measure,
                                                     'date': metadata.dateStr,
                                                     'appDate': metadata.appDate,
                                                     'revision': metadata.revision,
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
  var testInfoDict = {
    'taskjs-scrolling': {
      'key': 'taskjs',
      'graphTitle': 'Scrolling on taskjs.org'
    },
    'nightly-zooming': {
      'key': 'nightly',
      'graphTitle': 'Mozilla Nightly Zooming Test'
    },
    'nytimes-scrolling': {
      'key': 'nytimes-scroll',
      'graphTitle': 'New York Times Scrolling Test'
    },
    'nytimes-zooming': {
      'key': 'nytimes-zoom',
      'graphTitle': 'New York Times Zooming Test'
    },
    'cnn': {
      'key': 'cnn',
      'graphTitle': 'CNN.com Test'
    },
    'canvas-clock': {
      'key': 'clock',
      'graphTitle': 'Canvas Clock Test'
    },
    'reddit': {
      'key': 'reddit',
      'graphTitle': 'Reddit test'
    },
    'imgur': {
      'key': 'imgur',
      'graphTitle': 'imgur test'
    },
    'wikipedia': {
      'key': 'wikipedia',
      'graphTitle': 'wikipedia test'
    }
  }

  var baseRoute = "/(" + Object.keys(testInfoDict).join("|") + ")";
  var tmp = {};
  tmp[baseRoute] = {
    '/(checkerboard|fps|uniqueframes)': {
      on: function(test, measure) {
        $('#functions').children('li').removeClass("active");
        $('#functions').children('#'+test+'-li').addClass("active");

        var testInfo = testInfoDict[test];
        updateContent(testInfo.graphTitle, test, measure);

        $.getJSON('data.json', function(rawData) {
          updateGraph(rawData[testInfo.key], measure);
        });
      }
    }
  };
  var router = Router(tmp).init('/taskjs-scrolling/checkerboard');

});
