var Eideticker = function () {
  var startTime;

  return {
    getParameterByName: function(name) {
      var match = RegExp('[?&]' + name + '=([^&]*)').exec(window.location.search);

      return match && decodeURIComponent(match[1].replace(/\+/g, ' '));
    },
    getTestType: function() {
       var testType = this.getParameterByName('testtype');
       if (!testType) {
          return "default";
       }

       return testType;
    },
    loadTest: function(testurl) {
      setTimeout(function() {
        window.location.href = testurl;
      }, 2000);
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

