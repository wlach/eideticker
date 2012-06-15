"use strict";

function getParameterByName(name) {
  var match = RegExp('[?&]' + name + '=([^&]*)').exec(window.location.search);

  return match && decodeURIComponent(match[1].replace(/\+/g, ' '));
}

function updateContent(title, measure) {

  var measureDescription;
  if (measure === "checkerboard") {
    measureDescription = 'The measure is the sum of the percentages of frames that are checkerboarded over the entire capture. Lower values are better.';
  } else if (measure === "fps") {
    measureDescription = 'The measure is a calculation of the average number of UNIQUE frames per second of capture. The theoretical maximum is 60 fps (which is what we are capturing), but note that if there periods where the page being captured is unchanging this number may be artifically low.';
  } else {
    measureDescription = 'The measure is a calculation of the total number of UNIQUE frames in the capture. Higher values generally indicate more fluid animations.';
  }

  $('#content').html(ich.graph({'title': title,
                                'measureDescription': measureDescription
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

      metadataHash[seriesIndex].push({'videoURL': sample.video, 'appDate': sample.appdate, 'revision': sample.revision, 'buildId': sample.buildid });
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
  var router = Router({ '/(checkerboard|fps|uniqueframes)': {
    on: function(measure) {

      var jsonFile = getParameterByName('data');
      $.getJSON(jsonFile, function(data) {
        console.log(data);
        updateContent(data['title'], measure);
        updateGraph(data['data'], measure);
      });
    }
  } }).init('/fps');

});
