function Eideticker() {
}

Eideticker.prototype = {
  toString: function() { return "[Eideticker]"; },
  pageLoaded: function() {
    sendAsyncMessage('Eideticker.Ready', { });
  },
  finished: function() {
    sendAsyncMessage('Eideticker.Finished', { });
  },
  __exposedProps__: {
    'toString': 'r',
    'pageLoaded': 'r',
    'finished': 'r'
  }
};

// This is a frame script, so it may be running in a content process.
// In any event, it is targeted at a specific "tab", so we listen for
// the DOMWindowCreated event to be notified about content windows
// being created in this context.

function EidetickerManager() {
  addEventListener("DOMWindowCreated", this, false);
}

EidetickerManager.prototype = {
  handleEvent: function handleEvent(aEvent) {
    var window = aEvent.target.defaultView;
    window.wrappedJSObject.Eideticker = new Eideticker(window);
  }
};

var eidetickerControllerManager = new EidetickerManager();

// Register for any messages our API needs us to handle
addMessageListener("Eideticker.StartedRecording", function(obj) {
  if (content.wrappedJSObject.startedRecording) {
    content.wrappedJSObject.startedRecording();
  }
});
