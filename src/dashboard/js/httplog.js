"use strict";

$(function() {
  $.getJSON('metadata/' + getParameterByName('id') + '.json', function(metadata) {
    var title = "HTTP Log";
    if (metadata.label)
      title = "HTTP Log for " + metadata.label;

    console.log(metadata);
    $('.container').html(ich.httpLog({ 'title': title,
                                       'log': metadata.httpLog }));
  });
});