(function(w, d) {

    var script = document.currentScript || document.querySelector('script[src*="widget-loader.js"]')
    var baseUrl = script.src.replace("/static/widget-loader.js", "");

    var containers = [];
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
         initIframeWidget(elements.item(i), i);
      }
    }

    function initIframeWidget(element, index) {
      var customId = getWidgetData(element, 'id');
      var customWidgetData = null;
      var src = null;
      var resize = true;
      var minHeight = "400";
      var maxHeight = "Infinity";
      var width = "100%";
      var googleTagManager = false;

      if (customId != null) {
        var url = baseUrl + "/api/v1/custom-widgets/" + customId;

        customWidgetData = loadJSON(url);
        var settings = customWidgetData.settings;
        src = baseUrl + "/static/widget/" + customWidgetData.widget_type + ".html";

        if (settings.hasOwnProperty('iFrameAutoResize') && settings.iFrameAutoResize != null) {
          resize = settings.iFrameAutoResize;
        }

        if (settings.hasOwnProperty('iFrameHeight') && settings.iFrameHeight != null) {
          minHeight = settings.iFrameHeight;
          maxHeight = settings.iFrameHeight;
        }

        if (settings.hasOwnProperty('iFrameMinHeight') && settings.iFrameMinHeight != null) {
          minHeight = settings.iFrameMinHeight;
        }

        if (settings.hasOwnProperty('iFrameMaxHeight') && settings.iFrameMaxHeight != null) {
          maxHeight = settings.iFrameMaxHeight;
        }

        if (settings.hasOwnProperty('googleTagManager') && settings.googleTagManager != null) {
          googleTagManager = settings.googleTagManager;
        }
      } else {
        width = getWidgetData(element, 'width', '100%');
        minHeight = getWidgetData(element, 'height', '400px');
        resize = getWidgetBoolData(element, 'resize', false);
        googleTagManager = getWidgetBoolData(element, 'google-tag-manager', false);

        var shortName = getWidgetData(element, 'short-name');
        var src = baseUrl + "/" + shortName + "/widget/eventdates?";
        src = addParamToQuery(element, src, 'event-list', 'event_list_id');
        src = addParamToQuery(element, src, 'font', 's_ft');
        src = addParamToQuery(element, src, 'background', 's_bg');
        src = addParamToQuery(element, src, 'primary', 's_pr');
        src = addParamToQuery(element, src, 'link', 's_li');
      }

      var style = "border: none; width:" + width + ";height:" + minHeight + ";";
      if (resize || customWidgetData != null) {
        style += "min-width:100%;max-width:100%;";
      }

      var iFrame = d.createElement("iframe");
      iFrame.id = "oveda-widget-iframe-" + index;
      iFrame.class = "oveda-widget-iframe";
      iFrame.src = src;
      iFrame.style = style;
      iFrame.frameborder = "0";
      iFrame.allowtransparency = "true";

      if (resize || googleTagManager || customWidgetData != null) {
        needsResizer = true;
      }

      var container = {
        element: element,
        iFrame: iFrame,
        minHeight: minHeight,
        maxHeight: maxHeight,
        resize: resize,
        googleTagManager: googleTagManager,
        customWidgetData: customWidgetData,
        resizer: null,
        iFrameLoaded: false
      };
      containers.push(container);

      iFrame.onload = function() {
        container.iFrameLoaded = true;
        startIframeResizer(container, index);
      }

      element.appendChild(iFrame);
    }

    function addParamToQuery(element, url, attr, param)
    {
      var value = getWidgetData(element, attr);

      if (value != null) {
        url += param + "=" + encodeURIComponent(value) + "&";
      }

      return url;
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
      addScript("https://cdnjs.cloudflare.com/ajax/libs/iframe-resizer/4.3.2/iframeResizer.min.js", onIframeResizerScriptLoaded);
    }

    function onIframeResizerScriptLoaded() {
      for (var i = 0; i < containers.length; i++) {
        var container = containers[i];
        startIframeResizer(container, i);
      }
    };

    function startIframeResizer(container, index) {
      if (container.resizer == null && container.iFrameLoaded && (container.resize || container.googleTagManager || container.customWidgetData != null)) {
        var config = { };
        config.autoResize = container.resize;
        config.scrolling = "omit";
        config.id = "iFrameResizer" + index;

        config.onMessage = function(messageData) {
          onIframeMessage(messageData, container.googleTagManager);
        }

        if (container.customWidgetData == null) {
          if (container.resize) {
            config.minHeight = container.minHeight;
            config.maxHeight = container.maxHeight;
          } else {
            config.sizeHeight = false;
            config.sizeWidth = false;
          }
        } else {
          config.minHeight = container.minHeight;
          config.maxHeight = container.maxHeight;

          (function(data) {
            config.onInit = function (iFrame) {
              iFrame.iFrameResizer.sendMessage({'type': 'OVEDA_WIDGET_SETTINGS_UPDATE_EVENT', 'data': data});
            }
          })(container.customWidgetData.settings);
        }

        var resizers = iFrameResize(config, container.iFrame);
        container.resizer = resizers[0];
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

    function loadJSON(url) {
      var json = loadUrlSync(url, "application/json");
      return JSON.parse(json);
    }

    function loadUrlSync(url, mimeType)
    {
      var xmlhttp=new XMLHttpRequest();
      xmlhttp.open("GET", url, false);
      if (mimeType != null && xmlhttp.overrideMimeType) {
        xmlhttp.overrideMimeType(mimeType);
      }

      xmlhttp.send();
      return xmlhttp.responseText;
    }

  })(window, document);