function Eideticker() {
}

Eideticker.prototype = {
  toString: function() { return "[Eideticker]"; },
  pageLoaded: function() {
    sendAsyncMessage('Eideticker.PageLoaded', { });
  },
  animationFinished: function() {
    sendAsyncMessage('Eideticker.AnimationFinished', { });
  },
  __exposedProps__: {
    'toString': 'r',
    'pageLoaded': 'r',
    'animationFinished': 'r'
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
addMessageListener("Eideticker.StartAnimation", function(obj) {
  if (content.wrappedJSObject.startAnimation) {
    content.wrappedJSObject.startAnimation();
  }
});
