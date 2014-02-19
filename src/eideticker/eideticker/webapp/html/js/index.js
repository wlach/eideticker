$(function() {
  var router = Router({
    '/captures': {
      on: function() {
        $.getJSON('api/captures/', function(data) {
          if (data.length > 0) {
            $('#capture-list').html(ich.capture_list({captures: data}));
            $('.capture-row').click(function() {
              window.location.hash = '/captures/' + $(this).attr('id');
            });
          } else {
            $('#capture-list').html("<p>No captures found on this machine. Create some?</p>");
          }
        });
      },
      '/([^\/]*)': {
        on: function(capture_id) {
          $.getJSON('api/captures/' + capture_id, function(captureSummary) {
            $("#"+capture_id.replace(/(:|\.)/g,'\\$1')).addClass('blue');

            var num_frames = captureSummary.numFrames;
            var image_url = "";
            if (num_frames > 0) {
              var im_w = parseInt(240);
              var im_h = parseInt((im_w / captureSummary.frameDimensions[0]) * captureSummary.frameDimensions[1]);
              image_url = "api/captures/" + capture_id + "/images/" + parseInt(num_frames/2) + "?width= " + im_w + "&height=" + im_h;
            }
            $('#capture-detail').html(ich.capture_detail({
              image_url: image_url,
              date: captureSummary.date,
              num_frames: captureSummary.numFrames,
              device: captureSummary.device,
              application: captureSummary.app,
              length_str: getTimeStr(captureSummary.length),
              filename: captureSummary.filename
            }));

            $('#open-capture').click(function() {
              window.open('capture.html#/'+capture_id+'/summary');
            });
          });
        }
      }
    }
  }).use({ recurse: 'forward' }).init('/captures');
});
