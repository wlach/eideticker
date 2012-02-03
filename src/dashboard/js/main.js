function parseDate(datestr) {
  var parsed = datestr.split("-");
  var year = parsed[0];
  var month = parsed[1] - 1; //Javascript months index from 0 instead of 1
  var day = parsed[2];

  return Date.UTC(year, month, day);
}

$(function() {
  $('#content').html(ich.graph({'title': 'Checkerboarding percents'}));
  $.getJSON('checkerboard.json', function(data) {
    var graphdata = Object.keys(data).sort().map(function(type) {
      var series = {};
      series.label = type;
      series.data = Object.keys(data[type]).map(function(datestr) {
        console.log(datestr);
        return [ parseDate(datestr), data[type][datestr]["duration"] ];
      }).sort();

      return series;
    });

    console.log(graphdata);
    $.plot($("#graph-container"), graphdata, {
      xaxis: {
        mode: "time",
        timeformat: "%y-%0m-%0d"

      },
      yaxis: {
        axisLabel: 'Time spent checkerboarding (seconds)',
        min: 0
      },
      series: {
        lines: { show: true, steps: false },
        points: { show: true }
      }
    });
  });

/*
  var router = Router({
    '/': {
      on: function() {
        $('#main-content').html(ich.index());
      }
    },
    '/irc-chatter': {
      on: function() {
        $('#main-content').html(ich.graph({'title': 'IRC Chatter'}));
        $.ajax({
        type: "GET",
          url: 'irc-chatter.json',
          dataType: "json",
          success: function(data) {
            var graphdata = Object.keys(data).sort().map(function(type) {
              var series = {};
              series.label = type;
              series.data = Object.keys(data[type]).map(function(datestr) {
                return [ parseDate(datestr), data[type][datestr] ];
              }).sort();

              return series;
            });

            $.plot($("#graph-container"), graphdata, {
              xaxis: {
                mode: "time",
              },
              yaxis: {
                axisLabel: 'Number of Messages',
                min: 0
              },
              series: {
                stack: true,
                lines: { show: true, fill: true, steps: false },
                points: { show: false }
              },
              legend: {
                container: "#legend"
              }
            });
          }
        });
      }
    },
    'blogposts': {
      on: function() {
        $('#main-content').html(ich.graph({'title': 'IRC Chatter'}));
        $.ajax({
        type: "GET",
          url: 'blogposts.json',
          dataType: "json",
          success: function(data) {
            
          }
        });
      }
    }
  }).init('/');
*/
});
