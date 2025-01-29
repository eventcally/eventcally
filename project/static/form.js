$.datepicker.setDefaults($.datepicker.regional["de"]);
$.fn.select2.defaults.set("language", "de");

function processSelect2Ajax($el) {
  var multiple = $el.attr("data-multiple") == "1";

  var opts = {
    width: "100%",
    theme: "bootstrap4",
    minimumInputLength: $el.attr("data-minimum-input-length"),
    placeholder: "data-placeholder",
    allowClear: false,
    ajax: {
      url: $el.attr("data-url"),
      headers: { "X-Backend-For-Frontend": "ajax_lookup" },
      dataType: "json",
      delay: 250,
      cache: true,
      data: function (params) {
        return {
          term: params.term,
          per_page: 5,
          page: params.page || 1,
        };
      },
      processResults: function (data) {
        return {
          results: data.items.map((p) => ({ id: p[0], text: p[1] })),
          pagination: {
            more: data.has_next,
          },
        };
      },
    },
    initSelection: function (element, callback) {
      $el = $(element);
      var result = [];

      if ($el.attr("data-json")) {
        var value = JSON.parse($el.attr("data-json"));

        if (value) {
          if (multiple) {
            for (var k in value) {
              var v = value[k];
              result.push({ id: v[0], text: v[1] });
            }

            callback(result);
          } else {
            result = { id: value[0], text: value[1] };
          }
        }
      }

      callback(result);
    },
  };

  if ($el.attr("data-allow-blank")) opts["allowClear"] = true;

  opts["multiple"] = multiple;

  $el.select2(opts);
}

$(function () {
  $("select[data-role=select2-ajax]").each(function () {
    var $el = $(this);
    processSelect2Ajax($el);
  });

  $(".autocomplete").select2({
    width: "100%",
    theme: "bootstrap4",
  });
  $(".autocomplete-multi").select2({
    width: "100%",
  });
});
