"use strict";

$(function() {
  function getParameterByName(name) {
    var match = RegExp('[?&]' + name + '=([^&]*)').exec(window.location.search);
    if (!match)
      return null;

    return match && decodeURIComponent(match[1].replace(/\+/g, ' '));
  }

  console.log(getParameterByName('video'));
  console.log(getParameterByName('framediff'));

  $('#header').html(ich.pageHeader({ 'title': getParameterByName('title') }));
  $('#maincontent').html(ich.pageContent({ 'videoPath': getParameterByName('video') }));

  $.getJSON(getParameterByName('framediff'), function(dict) {

    var series = {
      data: []
    }

    var i = 0.0;
    dict.diffsums.forEach(function(diffsum) {
      series.data.push([ i, diffsum ]);
      i+=(1.0/60.0);
    });

    var plot = $.plot($("#graph-container"), [ series ], {
      xaxis: {
        axisLabel: "Time (seconds)"
      },
      yaxis: {
        axisLabel: "Pixel difference from previous frame",
        min: 0
      },
      grid: { clickable: true, hoverable: true, mouseActiveRadius:1000 },
      zoom: { interactive: true },
      pan: { interactive: true }
    });

    // add zoom out button
    $('<div class="button" style="right:20px;top:20px">zoom out</div>').appendTo($("#graph-container")).click(function (e) {
      e.preventDefault();
      plot.zoomOut();
    });

    $("#graph-container").bind("plotclick", function (event, pos, item) {
      console.log("Data index: " + item.dataIndex);
      var video = $("#frameview").get(0);
      console.log(video);
      video.currentTime = item.dataIndex/60.0;
    });

  });
});