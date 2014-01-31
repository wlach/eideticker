"use strict";

var availableMeasures = [];

function updateContent(title, measure) {

  var measureDescription = measures[measure].longDesc;

  $('#content').html(ich.graph({'title': title,
                                'measureDescription': measureDescription,
                                'measures': availableMeasures.map(
                                  function(measureId) {
                                    return { 'id': measureId,
                                             'desc': measures[measureId].shortDesc
                                           };
                                  })
                               }));
  $('#measure-'+measure).attr("selected", "true");
  $('#measure').change(function() {
    var newMeasure = $(this).val();
    window.location.hash = '/' + newMeasure;
  });
}

function updateGraph(rawdata, measure) {
  // show individual data points
  var graphdata = [];
  var colorCounter = 0;
  var metadataHash = {};

  var seriesIndex = 0;
  var barPosition = 1;
  Object.keys(rawdata).sort().forEach(function(appname) {
    metadataHash[seriesIndex] = [];

    var label;
    var color = colorCounter;
    if (appname === "com.android.chrome") {
      label = "Chrome for Android";
    } else if (appname === "com.google.android.browser") {
      label = "ICS Stock Browser";
    } else if (appname === "com.opera.browser") {
      label = "Opera Browser";
    } else if (appname === "mobi.mgeek.TunnyBrowser") {
      label = "Dolphin";
    } else if (appname === "org.mozilla.firefox") {
      label = "Old Firefox Mobile";
    } else if (appname === "org.mozilla.firefox_beta") {
      label = "New Firefox Mobile Beta";
      color = "#e8780a";
    } else {
      label = appname;
    }
    // point graph
    var series = {
      label: label,
      bars: { show: true },
      color: color,
      data: []
    };
    rawdata[appname].forEach(function(sample) {
      series.data.push([ barPosition, sample[measure] ]);

      metadataHash[seriesIndex].push({'videoURL': sample.video, 'appDate': sample.appdate, 'revision': sample.revision, 'buildId': sample.buildid, 'frameDiff': sample.frameDiff, 'fps': sample.captureFPS, 'generatedVideoFPS': sample.generatedVideoFPS });
      barPosition++;
    });
    graphdata.push(series);

    colorCounter++;
    seriesIndex++;
    barPosition++; // space between apps
  });

  var axisLabel;
  if (measure == "checkerboard") {
    axisLabel = "Checkerboard (lower is better)";
  } else if (measure === "uniqueframes") {
    axisLabel = "Unique frames (higher is better)";
  } else {
    axisLabel = "Frames per second (higher is better)";
  }

  var plot = $.plot($("#graph-container"), graphdata, {
    xaxis: { show: false },
    yaxis: {
      axisLabel: axisLabel
    },
    legend: {
      container: $("#legend"),
    },
    grid: { clickable: true, hoverable: true }
  });

  $("#graph-container").bind("plotclick", function (event, pos, item) {
    plot.unhighlight();
    if (item) {
      var metadata = metadataHash[item.seriesIndex][item.dataIndex];
      $('#datapoint-info').html(ich.graphDatapoint({ 'date': null,
                                                     'videoURL': metadata.videoURL,
                                                     'measureName': measure,
                                                     'appDate': metadata.appDate,
                                                     'revision': metadata.revision,
                                                     'buildId': metadata.buildId,
                                                     'measureValue': Math.round(100.0*item.datapoint[1])/100.0,
                                                     'frameDiff': metadata.frameDiff,
                                                     'fps': metadata.fps,
                                                     'generatedVideoFPS': metadata.generatedVideoFPS
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

  var dataFilename = getParameterByName('data');
  if (!dataFilename)
    dataFilename = 'metric.json';

  $.getJSON(dataFilename, function(data) {
    // figure out which measures could apply to this graph
    Object.keys(data['data']).forEach(function(appname) {
      data['data'][appname].forEach(function(sample) {
        Object.keys(sample).forEach(function(potentialMeasure) {
          if (jQuery.inArray(potentialMeasure, Object.keys(measures)) !== -1 &&
              jQuery.inArray(potentialMeasure, availableMeasures) === -1) {
            availableMeasures.push(potentialMeasure);
          }
        });
      });
    });

    var defaultMeasure = availableMeasures[0];

    var router = Router({ '/:measureId': {
      on: function(measureId) {
        updateContent(data['title'], measureId);
        updateGraph(data['data'], measureId);
      }
    } }).init('/' + defaultMeasure);
  });
});
