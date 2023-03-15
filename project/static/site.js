moment.locale("de");

function get_moment_with_time_from_fields(date_field, time_field) {
  var date_time_string = $(date_field).val();
  var time_string = $(time_field).val();

  if (time_string != undefined && time_string != "") {
    date_time_string += " " + time_string;
  }

  return moment(date_time_string);
}

function get_moment_with_time(field_id) {
  var date_field = $(field_id);
  var time_field = $(field_id + "-time");
  return get_moment_with_time_from_fields(date_field, time_field)
}

function set_date_bounds(picker) {
  var data_range_to_attr = picker.attr("data-range-to");
  var data_allday_attr = picker.attr("data-allday");

  if (data_range_to_attr) {
    var hidden_field_id = picker.attr("id").replace("-user", "");
    var from_moment = get_moment_with_time("#" + hidden_field_id);
    $(data_range_to_attr + "-user").datepicker(
      "option",
      "minDate",
      from_moment.toDate()
    );

    var end_val = $(data_range_to_attr).val();
    if (end_val != "") {
      var end_moment = get_moment_with_time(data_range_to_attr);

      if (data_allday_attr && $(data_allday_attr).is(':checked')) {
        end_moment = end_moment.endOf('day');
        set_picker_date($(data_range_to_attr), end_moment.toDate());
      } else if (end_moment < from_moment) {
        set_picker_date($(data_range_to_attr), from_moment.toDate());
      }
    }

    var data_range_max_attr = picker.attr("data-range-max-days");
    if (data_range_max_attr) {
      from_moment.add(data_range_max_attr, "days");
      $(data_range_to_attr + "-user").datepicker(
        "option",
        "maxDate",
        from_moment.toDate()
      );
    }
  }

  var data_range_from_attr = picker.attr("data-range-from");
  if (data_range_from_attr) {
    var hidden_field_id = picker.attr("id").replace("-user", "");
    var to_moment = get_moment_with_time("#" + hidden_field_id);

    var start_val = $(data_range_from_attr).val();
    if (start_val != "") {
      var start_moment = get_moment_with_time(data_range_from_attr);
      if (start_moment > to_moment) {
        set_picker_date($(data_range_from_attr), to_moment.toDate());
      }
    }
  }
}

function set_picker_date(picker, date, timeout = -1) {
  picker.datepicker("setDate", date);

  var hidden_field_id = picker.attr("id").replace("-user", "");
  $("#" + hidden_field_id + "-time").timepicker("setTime", date);

  if (timeout < 0) {
    set_date_bounds(picker);
  } else {
    window.setTimeout(function () {
      set_date_bounds(picker);
    }, timeout);
  }
}

function onAlldayChecked(checkbox, hidden_field_id) {
  var picker = $("#" + hidden_field_id + "-user");
  var data_range_to_attr = picker.attr("data-range-to");
  var start_moment = get_moment_with_time("#" + hidden_field_id).startOf('day');

  if (checkbox.checked) {
    set_picker_date(picker, start_moment.toDate());
  } else {
    var next_hour = moment().add(1, 'hour').startOf('hour');
    start_moment = start_moment.set({"hour": next_hour.hour(), "minute": next_hour.minute()});
    set_picker_date(picker, start_moment.toDate());

    if (data_range_to_attr) {
      var end_moment = get_moment_with_time(data_range_to_attr);
      end_moment = end_moment.startOf('day').set({"hour": next_hour.hour(), "minute": next_hour.minute()});
      set_picker_date($(data_range_to_attr), end_moment.add(3, 'hours').toDate());
    }
  }
}

function start_datepicker(input) {
  if (input.data('picker') !== undefined) {
    return;
  }

  var hidden_field = input;
  var hidden_field_id = hidden_field.attr("id");

  var user_field = hidden_field.clone();
  user_field.removeAttr("name");
  user_field.removeClass("datepicker");
  user_field.attr("id", hidden_field_id + "-user");
  user_field.attr("autocomplete", "off");

  var picker = user_field.datepicker({
    dateFormat: "D, dd.mm.yy",
    altField: hidden_field,
    altFormat: "yy-mm-dd",
    onSelect: function (date) {
      hidden_field.change();
    },
  });

  hidden_field.data("picker", picker);
  hidden_field.hide();

  var hidden_value = hidden_field.val();
  if (hidden_value) {
    set_picker_date(
      picker,
      get_moment_with_time("#" + hidden_field_id).toDate(),
      100
    );
  }

  hidden_field.after(user_field);

  var data_range_to_attr = picker.attr("data-range-to");
  if (data_range_to_attr) {
    $(data_range_to_attr).attr("data-range-from", "#" + hidden_field_id);
  }

  var data_allday_attr = picker.attr("data-allday");
  if (data_allday_attr) {
    var checked = $(data_allday_attr).is(':checked')
    $("#" + hidden_field_id + "-time").toggle(!checked);
    if (data_range_to_attr) {
      $(data_range_to_attr + "-time").toggle(!checked);
    }

    $(data_allday_attr).on('change', function() {
      $("#" + hidden_field_id + "-time").toggle(!this.checked);
      if (data_range_to_attr) {
        $(data_range_to_attr + "-time").toggle(!this.checked);
      }

      onAlldayChecked(this, hidden_field_id)

      // var start_moment = get_moment_with_time("#" + hidden_field_id).startOf('day');

      // if (this.checked) {
      //   set_picker_date(picker, start_moment.toDate());
      // } else {
      //   var next_hour = moment().add(1, 'hour').startOf('hour');
      //   start_moment = start_moment.set({"hour": next_hour.hour(), "minute": next_hour.minute()});
      //   set_picker_date(picker, start_moment.toDate());

      //   if (data_range_to_attr) {
      //     var end_moment = get_moment_with_time(data_range_to_attr);
      //     end_moment = end_moment.startOf('day').set({"hour": next_hour.hour(), "minute": next_hour.minute()});
      //     set_picker_date($(data_range_to_attr), end_moment.add(3, 'hours').toDate());
      //   }
      // }
    });
  }

  hidden_field.change(function () {
    var hidden_value = hidden_field.val();
    var existing_date = picker.datepicker("getDate");
    var existing_moment = existing_date != null ? moment(existing_date) : null;

    if (hidden_value) {
      hidden_moment = moment(hidden_value);
      if (!hidden_moment.isSame(existing_moment)) {
        picker.datepicker("setDate", hidden_moment.toDate());
      }
      set_date_bounds(picker);
    } else if (existing_date != null) {
      set_picker_date(picker, null);
    }
  });

  user_field.change(function () {
    var user_value = user_field.val();
    if (!user_value) {
      set_picker_date(picker, null);
    }
  });

  $("#" + hidden_field_id + "-time").change(function () {
    set_date_bounds(picker);
  });

  return picker;
}

function start_timepicker(input) {
  input.timepicker({
    timeFormat: "H:i",
  });
}

function handle_request_start(
  result_id = "#result_container",
  spinner_id = "#spinner",
  error_id = "#error_alert"
) {
  $(result_id).hide();
  $(spinner_id).show();
  $(error_id).hide();
}

function handle_request_error(
  xhr,
  status,
  error,
  result_id = "#result_container",
  spinner_id = "#spinner",
  error_id = "#error_alert"
) {
  $(error_id).text(status);
  $(error_id).show();
  $(spinner_id).hide();
}

function handle_request_success(
  result_id = "#result_container",
  spinner_id = "#spinner",
  error_id = "#error_alert"
) {
  $(result_id).show();
  $(spinner_id).hide();
  $(error_id).hide();
}

function reset_location_form(prefix = "") {
  $("#" + prefix + "location-street").val("");
  $("#" + prefix + "location-postalCode").val("");
  $("#" + prefix + "location-city").val("");
  $("#" + prefix + "location-state").val("");
  $("#" + prefix + "location-latitude").val("");
  $("#" + prefix + "location-longitude").val("");
}

function reset_place_form(prefix = "") {
  $("#" + prefix + "name").val("");
  $("#" + prefix + "url").val("");
  reset_location_form(prefix);
}

function reset_organizer_form(prefix = "") {
  $("#" + prefix + "name").val("");
  reset_location_form(prefix);
}

function fill_place_form_with_gmaps_place(
  place,
  prefix = "",
  location_only = false
) {
  var street_number = "";
  var route = "";
  var city = "";

  for (var i = 0; i < place.address_components.length; i++) {
    var component = place.address_components[i];
    var addressType = component.types[0];
    var val = component.long_name;

    if (addressType == "street_number") {
      street_number = val;
    } else if (addressType == "route") {
      route = val;
    } else if (addressType == "locality") {
      city = val;
    } else if (addressType == "administrative_area_level_1") {
      $("#" + prefix + "location-state").val(val);
    } else if (addressType == "postal_code") {
      $("#" + prefix + "location-postalCode").val(val);
    }
  }

  if (!location_only) {
    $("#" + prefix + "name").val(place.name);

    if (place.website) {
      $("#" + prefix + "url").val(place.website);
    }
  }

  $("#" + prefix + "location-street").val([route, street_number].join(" "));
  $("#" + prefix + "location-city").val(city);
  $("#" + prefix + "location-latitude").val(place.geometry.location.lat);
  $("#" + prefix + "location-longitude").val(place.geometry.location.lng);
}

function showLink(e, element) {
  if (e != null) {
    e.preventDefault();
    e.stopPropagation();
  }

  $("#" + $(element).attr("data-show-container")).hide();
  $("#" + $(element).attr("data-container")).show();
  $("#" + $(element).attr("data-container")).trigger("shown");
}

function hideLink(e, element) {
  if (e != null) {
    e.preventDefault();
    e.stopPropagation();
  }

  $("#" + $(element).attr("data-show-container")).show();
  $("#" + $(element).attr("data-container")).hide();
  $("#" + $(element).attr("data-container")).trigger("hidden");
}

String.prototype.truncate =
  String.prototype.truncate ||
  function (n, useWordBoundary) {
    if (this.length <= n) {
      return this;
    }
    const subString = this.substr(0, n - 1); // the original check
    return (
      (useWordBoundary
        ? subString.substr(0, subString.lastIndexOf(" "))
        : subString) + "&hellip;"
    );
  };

function scroll_to_element(element, complete) {
  $("html, body").animate(
    { scrollTop: element.offset().top },
    { duration: "slow", complete: complete }
  );
}

(function($) {
  function GsevptDateDefinition(element, options) {
    var self = this;
    var container = $(element);
    var prefix = container.attr('data-prefix');

    var startInput = container.find("input[id$='-start']");
    var endInput = container.find("input[id$='-end']");

    var startTimeInput = container.find("input[id$='-start-time']");
    var endTimeInput = container.find("input[id$='-end-time']");

    var endShowContainer = container.find("div[id$='-end-show-container']");
    var endContainer = container.find("div[id$='-end-container']");
    var alldayInput = container.find("input[id$='-allday']");
    var recurrenceRuleTextarea = container.find("textarea[id$='-recurrence_rule']");

    start_timepicker(startTimeInput);
    start_timepicker(endTimeInput);

    start_datepicker(startInput);
    start_datepicker(endInput);

    recurrenceRuleTextarea.recurrenceinput({prefix: prefix, ajaxURL: "/events/rrule"});

    var removeButton = container.find("button.remove-date-defintion-btn");
    var startUserInput = container.find("input[id$='-start-user']");
    var endUserInput = container.find("input[id$='-end-user']");

    startInput.rules("add", { dateRange: ["#start", "#end"] });
    endInput.rules("add", { dateRangeDay: ["#start", "#end"] });

    startTimeInput.rules("add", "time");
    endTimeInput.rules("add", "time");

    endContainer.on('shown', function() {
      var end_moment = get_moment_with_time('#' + startInput.attr('id'));

      if (alldayInput.is(':checked')) {
        end_moment = end_moment.endOf('day');
      } else {
        end_moment = end_moment.add(3, 'hours');
      }

      set_picker_date(endUserInput, end_moment.toDate());
    });

    endContainer.on('hidden', function() {
      set_picker_date(endUserInput, null);
      alldayInput.prop('checked', false).trigger("change");
    });

    alldayInput.on('change', function() {
      if (this.checked && !endContainer.is(":visible")) {
        showLink(null, endShowContainer.find("a.show-link"));
      }
    });

    removeButton.click(function () {
      var count = $.find(".date-definition-container").length;
      if (count > 1) {
          var container = $(this).closest(".date-definition-container");
          container.remove();
          count--;

          if (count == 1) {
            $('.date-definition-container button.remove-date-defintion-btn').addClass("d-none");
          }
      }

      return false;
    });

    container.find(".show-link").click(function (e) {
      showLink(e, this);
    });

    container.find(".hide-link").click(function (e) {
      hideLink(e, this);
    });
  }

  $.fn.gsevptDateDefinition = function(options) {
      var defaults = {};
      var settings = $.extend({}, defaults, options);

      if (this.length > 1) {
          this.each(function() { $(this).gsevptDateDefinition(options) });
          return this;
      }

      if (this.data('gsevptDateDefinition')) {
          return this.data('gsevptDateDefinition');
      }

      var gsevptDateDefinition = new GsevptDateDefinition(this, settings);
      this.data('gsevptDateDefinition', gsevptDateDefinition);
      return gsevptDateDefinition;
  }
})(jQuery);

$(function () {
  $('[data-toggle="tooltip"]').tooltip();

  $("form .datepicker").each(function (index, element) {
    start_datepicker($(element));
  });

  $("form .timepicker").each(function (index, element) {
    start_timepicker($(element));
  });

  $("#clear_location_btn").click(function () {
    $("#coordinate").val("");
    $("#location").val("").trigger('change');
  });

  $(".btn-print").click(function () {
    window.print();
    return false;
  });

  $("#copy_input_button").click(function () {
    $("#copy_input").select();
    document.execCommand("copy");
    $(this).tooltip("show");
  });

  $("#copy_input_button").mouseleave(function () {
    $(this).tooltip("hide");
  });

  $("#geolocation_btn").click(function () {
    if ("geolocation" in navigator) {
      navigator.geolocation.getCurrentPosition(function (position) {
        $("#coordinate").val(
          position.coords.latitude + "," + position.coords.longitude
        );
        $("#location").val("Aktuelle Position");
        $("#location").removeClass("is-invalid");
      }, handleError);

      function handleError(error) {
        //Handle Errors
        switch (error.code) {
          case error.PERMISSION_DENIED:
            alert("User denied the request for Geolocation.");
            break;
          case error.POSITION_UNAVAILABLE:
            alert("Location information is unavailable.");
            break;
          case error.TIMEOUT:
            alert("The request to get user location timed out.");
            break;
          case error.UNKNOWN_ERROR:
            alert("An unknown error occurred.");
            break;
        }
      }
    } else {
      alert("Browser doesn't support geolocation!");
    }
  });

  $(".dropzone-wrapper").on("dragover", function (e) {
    e.preventDefault();
    e.stopPropagation();
    $(this).addClass("dragover");
  });

  $(".dropzone-wrapper").on("dragleave", function (e) {
    e.preventDefault();
    e.stopPropagation();
    $(this).removeClass("dragover");
  });

  $(".show-link").click(function (e) {
    showLink(e, this);
  });

  $(".hide-link").click(function (e) {
    hideLink(e, this);
  });
});
