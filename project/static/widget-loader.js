(function(w, d) {

    var script = document.currentScript || document.querySelector('script[src*="widget-loader.js"]')
    var baseUrl = script.src.replace("/static/widget-loader.js", "");

    var iFrameElements = [];
    var needsResizer = false;

    w.onload = function() {
      initWidgets()

      if (needsResizer) {
        addIframeResizerScript();
      }
    };

    function initWidgets() {
      var elements = d.getElementsByClassName("oveda-widget");
      for (var i = 0; i < elements.length; i++) {
         initIframeWidget(elements.item(i));
      }
    }

    function initIframeWidget(element) {
      var shortName = getWidgetData(element, 'short-name');
      var width = getWidgetData(element, 'width', '100%');
      var height = getWidgetData(element, 'height', '400px');
      var resize = getWidgetBoolData(element, 'resize', false);
      var googleTagManager = getWidgetBoolData(element, 'google-tag-manager', false);

      var style = "border: none; width:" + width + ";height:" + height + ";";
      if (resize) {
        style += "min-width:100%;max-width:100%;";
      }

      var iFrame = d.createElement("iframe");
      iFrame.class = "oveda-widget-iframe";
      iFrame.src = baseUrl + "/" + shortName + "/widget/eventdates";
      iFrame.style = style;
      iFrame.frameborder = "0";
      iFrame.allowtransparency = "true";
      element.appendChild(iFrame);

      if (resize || googleTagManager) {
        needsResizer = true;
      }

      iFrameElements.push(element);
    }

    function getWidgetData(element, name, defaultValue = null) {
      var attribute = 'data-widget-' + name;

      if (!element.hasAttribute(attribute)) {
        return defaultValue;
      }

      return element.getAttribute(attribute);
    }

    function getWidgetBoolData(element, name, defaultValue = false) {
      return getWidgetData(element, name, defaultValue) !== "false";
    }

    function addIframeResizerScript() {
      addScript("https://cdnjs.cloudflare.com/ajax/libs/iframe-resizer/4.3.2/iframeResizer.min.js", startIframeResizer);
    }

    function startIframeResizer() {
      for (var i = 0; i < iFrameElements.length; i++) {
        var element = iFrameElements[i];
        var iFrame = element.getElementsByTagName("iframe")[0];
        var height = getWidgetData(element, 'height', '400px');
        var resize = getWidgetBoolData(element, 'resize', false);
        var googleTagManager = getWidgetBoolData(element, 'google-tag-manager', false);

        if (resize || googleTagManager) {
          var config = { autoResize: resize };

          if (resize) {
            config.minHeight = height;
          } else {
            config.scrolling = "omit";
            config.sizeHeight = false;
            config.sizeWidth = false;
          }

          config.onMessage = function(messageData) {
              onIframeMessage(messageData, googleTagManager);
          }

          iFrameResize(config, iFrame);
        }
      }
    };

    function onIframeMessage(messageData, googleTagManager) {
      var message = messageData.message;

      if (message.type == "OVEDA_ANALYTICS_EVENT") {
        trackAnalyticsEvent(message.data, googleTagManager);
      }
    }

    function trackAnalyticsEvent(data, googleTagManager) {
      if (googleTagManager) {
        data.event = "ovedaWidget." + data.event;

        if (window.dataLayer !== null && window.dataLayer !== undefined) {
          window.dataLayer.push(data);
        }
      }
    }

    function addScript(src, callback) {
      var script = d.createElement("script");
      script.src = src;
      script.onreadystatechange = callback;
      script.onload = callback;

      addScriptElement(script)
    }

    function addScriptElement(element) {
      var p = d.getElementsByTagName("script")[0];
      p.parentNode.insertBefore(element, p);
    }

  })(window, document);