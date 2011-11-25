$(function() {
  var router = Router({
    '/captures': {
      on: function() {
        $.getJSON('api/captures/', function(data) {
          if (data.length > 0) {
            $('#capture-list').html(ich.capture_list({captures: data}));
            $('.capture-row').click(function() {
              $('.capture-row').removeClass('blue');
              $(this).addClass('blue');

              window.location.hash = '/captures/' + $(this).attr('id');
            });
          } else {
            $('#capture-list').html("<p>No captures found on this machine. Create some?</p>");
          }
        });
      },
      '/([^\/]*)': {
        on: function(capture_id) {
          $.getJSON('api/captures/' + capture_id, function(data) {
            var num_frames = data['num_frames'];
            var image_url = "";
            if (num_frames > 0) {
              var im_w = parseInt(240);
              var im_h = parseInt((im_w / data['width']) * data['height']);
              image_url = "api/captures/" + capture_id + "/images/" + parseInt(num_frames/2) + "?width= " + im_w + "&height=" + im_h;
            }
            $('#capture-detail').html(ich.capture_detail({
              date: data['date'],
              num_frames: num_frames,
              device: data['device'],
              length_str: getTimeStr(data['length']),
              image_url: image_url
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
