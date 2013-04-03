var Eideticker = function () {
  var startTime;

  return {
    getParameterByName: function(name) {
      var match = RegExp('[?&]' + name + '=([^&]*)').exec(window.location.search);
      if (!match)
        return null;

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
    },
    onload: window.onload
  }
}();

// bit of a hack, we determine whether or not this is a test by looking for
// the "testpath" variable, which we assume is only set on the start.html
// "green screen" page
if (Eideticker.getParameterByName('testpath') === null) {
  window.onload = function() {
    // Run the test, after a brief timeout to make sure the page is *really* loaded and stable
    setTimeout(function() {
      if (Eideticker.onload) {
        Eideticker.onload();
      }

      var params = "commands=" + Eideticker.getTestType();
      var http = new XMLHttpRequest();
      http.open("POST", '/api/captures/input', true);
      http.setRequestHeader("Content-type", "application/x-www-form-urlencoded");
      http.setRequestHeader("Content-length", params.length);
      http.onreadystatechange = function () {
        if (this.readyState === 4 && this.status === 200) Eideticker.finish();
      };
      http.send(params);
    }, 1000);
  };
}
