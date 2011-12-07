var Eideticker = function () {
  var startTime;

  return {
    loadTest: function(testurl) {
      setTimeout(function() {
        window.location.href = testurl;
      }, 5000);
    },
    start: function() {
      startTime = new Date();
    },
    elapsed: function() {
      var now = new Date();
      return now - startTime;
    },
    finish: function() {
      window.location.href = "/finish.html";
    }
  }
}();
