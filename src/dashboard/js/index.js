function parseDate(datestr) {
  var parsed = datestr.split("-");
  var year = parsed[0];
  var month = parsed[1] - 1; //Javascript months index from 0 instead of 1
  var day = parsed[2];

  return Date.UTC(year, month, day);
}

function drawGraph(rawdata, ylabel) {
  // show individual data points
  var graphdata = [];
  var color = 0;
  Object.keys(rawdata).sort().forEach(function(type) {
    var series1 = {
      label: type,
      points: { show: true },
      color: color,
      data: []
    };

    Object.keys(rawdata[type]).forEach(function(datestr) {
      rawdata[type][datestr].forEach(function(sample) {
        series1.data.push([parseDate(datestr), sample["fps"] ]);
      });
    });
    series1.data.sort();
    graphdata.push(series1);

    var series2 = {
      lines: { show: true },
      color: color,
      data: []
    };
    Object.keys(rawdata[type]).forEach(function(datestr) {
      var numSamples = 0;
      var total = 0;
      rawdata[type][datestr].forEach(function(sample) {
        total += sample["fps"];
        numSamples++;
      });

      series2.data.push([parseDate(datestr), total/numSamples]);
    });
    series2.data.sort();
    graphdata.push(series2);

    color++;
  });

  $.plot($("#graph-container"), graphdata, {
    xaxis: {
      mode: "time",
      timeformat: "%y-%0m-%0d",
      minTickSize: [1, "day"]

    },
    yaxis: {
      axisLabel: ylabel,
      min: 0
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
          drawGraph(rawdata['src/tests/canvas/clock.html'], "Frames per second");
        });
      }
    }
  }).init('/checkerboarding');
});
