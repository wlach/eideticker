"use strict";

$(function() {
  function getParameterByName(name) {
    var match = RegExp('[?&]' + name + '=([^&]*)').exec(window.location.search);
    if (!match)
      return null;

    return decodeURIComponent(match[1].replace(/\+/g, ' ')).replace(
        /[\"\']/g, ' ');
  }

  function render(diffsums, actions) {
    var seriesList = [];
    var currentSeries = null;
    var lastSeries = null;
    var currentAction = null;
    var colors = [ '#f00', '#a00', '#aaa' ];
    var actionColorIndex = 0;
    var i = 0.0;
    var actionCount = {};

    diffsums.forEach(function(diffsum) {
      // if we have a current action, check to make sure
      // we're still within it
      if (currentAction && i > currentAction.end) {
        currentAction = null;
        seriesList.push(currentSeries);
        lastSeries = currentSeries;
        currentSeries = null;
      }
      // if we don't have a current action (or just went
      // out of one) see if there's any left in the log
      // and if so, whether we're now inside one
      if (!currentAction && actions && actions.length > 0 &&
          i > actions[0].start && i < actions[0].end) {
        if (actions[0].type === "sleep") {
          // just skip sleep events as they're not very interesting
          actions.shift();
        } else {
          if (currentSeries) {
            seriesList.push(currentSeries);
            lastSeries = currentSeries;
          }
          currentAction = actions.shift();
          if (actionCount[currentAction.type] === undefined) {
            actionCount[currentAction.type] = 1;
          } else {
            actionCount[currentAction.type]++;
          }
          currentSeries = { data: [], color: colors[actionColorIndex],
                            label: currentAction.type + " " +
                            actionCount[currentAction.type] + " (time: " +
                            currentAction.start.toFixed(4) + "s - " +
                            currentAction.end.toFixed(4) +
                            "s)" };
          actionColorIndex = actionColorIndex ? 0 : 1;
        }
      }
      // if we're not in action and we have no currentSeries, create a
      // "null" grey series indicating a dead space before/between/after
      // actions
      if (currentSeries === null) {
        currentSeries = { data: [], color: colors[2] }
      }

      if (lastSeries) {
        // we keep track of the last series so the graph looks continuous
        lastSeries.data.push([ i, diffsum ]);
        lastSeries = null;
      }
      currentSeries.data.push([ i, diffsum ]);
      i+=(1.0/60.0);
    });

    if (currentSeries)
      seriesList.push(currentSeries);

    var graphContainer = $("#graph-container");
    var plot = $.plot(graphContainer, seriesList, {
      xaxis: {
        axisLabel: "Time (seconds)"
      },
      yaxis: {
        axisLabel: "Pixel difference from previous frame",
        min: 0
      },
      legend: { show: false },
      grid: { clickable: true, hoverable: true, mouseActiveRadius: 1000 },
      pan: { interactive: true }
    });

    graphContainer.bind("plotclick", function (event, pos, item) {
      var video = $("#frameview").get(0);
      video.currentTime = item.datapoint[0];
    });

    var previousPoint = null;
    graphContainer.bind("plothover", function (event, pos, item) {
      var video = $("#frameview").get(0);
      video.currentTime = item.datapoint[0];

      if (item) {
	var t = item.datapoint[0].toFixed(8);
        $("#datapoint").html(ich.graphDatapoint({ 'time': t,
                                                  'framediff': item.datapoint[1],
                                                  'eventName': item.series.label }));
      }
    });
  }


  $('#header').html(ich.pageHeader({ 'title': getParameterByName('title') }));
  $('#maincontent').html(ich.pageContent({ 'videoPath': getParameterByName('video') }));

  $.getJSON(getParameterByName('framediff'), function(framediff) {
    if (getParameterByName('actionlog')) {
      $.getJSON(getParameterByName('actionlog'), function(actionLog) {
        render(framediff.diffsums, actionLog.actions);
      });
    } else {
      render(framediff.diffsums, null);
    }
  });
});
