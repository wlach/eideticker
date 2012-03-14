"use strict";

function parseDate(datestr) {
  var parsed = datestr.split("-");
  var year = parsed[0];
  var month = parsed[1] - 1; //Javascript months index from 0 instead of 1
  var day = parsed[2];

  return Date.UTC(year, month, day);
}

function drawGraph(rawdata, measure, ylabel) {
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
        metadataHash[seriesIndex].push({'videoURL': sample.video, 'dateStr': datestr});
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

  var plot = $.plot($("#graph-container"), graphdata, {
    xaxis: {
      mode: "time",
      timeformat: "%0m-%0d"
    },
    yaxis: {
      axisLabel: ylabel,
      min: 0
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
  var router = Router({
    '/checkerboarding': {
      on: function() {
        $('#functions').children('li').removeClass("active");
        $('#functions').children('#checkerboard-li').addClass("active");

        $('#content').html(ich.graph({'title': 'Checkerboarding percents'}));
        $('#graph-container').append("<p>Workin' on it! ;)</p>");
      }
    },
    '/canvas': {
      on: function() {
        $('#functions').children('li').removeClass("active");
        $('#functions').children('#canvas-li').addClass("active");

        $('#content').html(ich.graph({'title': 'Canvas Framerate'}));
        $.getJSON('data.json', function(rawdata) {
          drawGraph(rawdata['src/tests/canvas/clock.html'], "fps", "Frames per second");
        });
      }
    }
  }).init('/checkerboarding');
});
