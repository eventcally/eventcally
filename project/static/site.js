moment.locale("de");
$.datepicker.setDefaults($.datepicker.regional["de"]);

jQuery.tools.recurrenceinput.localize("de", {
  displayUnactivate: "Keine Wiederholungen",
  displayActivate: "Alle ",
  edit_rules: "Bearbeiten...",
  add_rules: "Hinzufügen...",
  delete_rules: "Löschen",
  add: "Hinzufügen",
  refresh: "Aktualisieren",
  title: "Regelmäßige Veranstaltung",
  preview: "Ausgewählte Termine",
  addDate: "Termin hinzufügen",
  recurrenceType: "Wiederholt sich",
  dailyInterval1: "Wiederholt sich alle",
  dailyInterval2: "Tage",
  weeklyInterval1: "Wiederholt sich alle",
  weeklyInterval2: "Woche(n)",
  weeklyWeekdays: "Wiederholt sich alle",
  weeklyWeekdaysHuman: "am: ",
  monthlyInterval1: "Wiederholt sich alle",
  monthlyInterval2: "Monat(e)",
  monthlyDayOfMonth1: "Tag",
  monthlyDayOfMonth1Human: "am Tag",
  monthlyDayOfMonth2: "des Monats",
  monthlyDayOfMonth3: "Monat(e)",
  monthlyDayOfMonth4: "monthly_day_of_month_4",
  monthlyWeekdayOfMonth1: "Den",
  monthlyWeekdayOfMonth1Human: "am",
  monthlyWeekdayOfMonth2: " ",
  monthlyWeekdayOfMonth3: "im Monat",
  monthlyRepeatOn: "Wiederholt sich",
  yearlyInterval1: "Wiederholt sich alle",
  yearlyInterval2: "Jahr(e)",
  yearlyDayOfMonth1: "Jeden",
  yearlyDayOfMonth1Human: "am",
  yearlyDayOfMonth2: " ",
  yearlyDayOfMonth3: " ",
  yearlyWeekdayOfMonth1: "Jeden",
  yearlyWeekdayOfMonth1Human: "am",
  yearlyWeekdayOfMonth2: " ",
  yearlyWeekdayOfMonth3: "im",
  yearlyWeekdayOfMonth4: " ",
  yearlyRepeatOn: "Wiederholt sich",
  range: "Ende der Wiederholung",
  rangeNoEnd: "Niemals",
  rangeByOccurrences1: "Endet nach",
  rangeByOccurrences1Human: "endet nach",
  rangeByOccurrences2: "Ereigniss(en)",
  rangeByEndDate: "Bis ",
  rangeByEndDateHuman: "endet am ",
  including: ", und auch ",
  except: ", ausser für",
  cancel: "Abbrechen",
  save: "Speichern",
  recurrenceStart: "Beginn der Wiederholung",
  additionalDate: "Weitere Termine",
  include: "Eingeschlossen",
  exclude: "Ausgenommen",
  remove: "Entfernen",
  orderIndexes: ["ersten", "zweiten", "dritten", "vierten", "letzten"],
  months: [
    "Januar",
    "Februar",
    "März",
    "April",
    "Mai",
    "Juni",
    "Juli",
    "August",
    "September",
    "Oktober",
    "November",
    "Dezember",
  ],
  shortMonths: [
    "Jan",
    "Feb",
    "Mär",
    "Apr",
    "Mai",
    "Jun",
    "Jul",
    "Aug",
    "Sep",
    "Okt",
    "Nov",
    "Dez",
  ],
  weekdays: [
    "Sonntag",
    "Montag",
    "Dienstag",
    "Mittwoch",
    "Donnerstag",
    "Freitag",
    "Samstag",
  ],
  shortWeekdays: ["Son", "Mon", "Die", "Mit", "Don", "Fre", "Sam"],
  longDateFormat: "D, dd.mm.yy",
  shortDateFormat: "dd.mm.yy",
  unsupportedFeatures:
    "Warning: This event uses recurrence features not supported by this widget. Saving the recurrence may change the recurrence in unintended ways: ",
  noTemplateMatch: "No matching recurrence template",
  multipleDayOfMonth:
    "Dieses Widget unterstützt keine mehrfach angelegten Tage in monatlicher oder jährlicher Wiederholung",
  bysetpos: "BYSETPOS wird nicht unterstützt",
  noRule: "Keine RRULE in RRULE Daten",
  noRepeatEvery: 'Error: The "Repeat every"-field must be between 1 and 1000',
  noEndDate:
    "Fehler: Das Terminende ist nicht gesetzt. Bitte geben Sie einen korrekten Wert ein.",
  noRepeatOn: 'Error: "Repeat on"-value must be selected',
  pastEndDate: "Fehler: Das Terminende kann nicht vor dem Terminanfang sein.",
  noEndAfterNOccurrences:
    'Error: The "After N occurrences"-field must be between 1 and 1000',
  alreadyAdded: "Das Datum wurde bereits hinzugefügt",
  rtemplate: {
    daily: "Täglich",
    mondayfriday: "Montags und Freitags",
    weekdays: "Wochentags",
    weekly: "Wöchentlich",
    monthly: "Monatlich",
    yearly: "Jährlich",
  },

  reccStart: "Startdatum",
  reccStartTime: "Beginn",
  reccFoEndTime: "Ende",
});

function get_moment_with_time(field_id) {
  var date_time_string = $(field_id).val();
  var time_string = $(field_id + "-time").val();

  if (time_string != undefined && time_string != "") {
    date_time_string += " " + time_string;
  }

  return moment(date_time_string);
}

function set_date_bounds(picker) {
  var data_range_to_attr = picker.attr("data-range-to");
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
      if (end_moment < from_moment) {
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

function start_datepicker(input) {
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

function reset_place_form(prefix = "") {
  $("#" + prefix + "name").val("");
  $("#" + prefix + "url").val("");
  $("#" + prefix + "location-street").val("");
  $("#" + prefix + "location-postalCode").val("");
  $("#" + prefix + "location-city").val("");
  $("#" + prefix + "location-state").val("");
  $("#" + prefix + "location-latitude").val("");
  $("#" + prefix + "location-longitude").val("");
}

function reset_organizer_form(prefix = "") {
  $("#" + prefix + "name").val("");
  $("#" + prefix + "location-street").val("");
  $("#" + prefix + "location-postalCode").val("");
  $("#" + prefix + "location-city").val("");
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
  e.preventDefault();
  e.stopPropagation();
  $("#" + $(element).attr("data-show-container")).hide();
  $("#" + $(element).attr("data-container")).show();
  $("#" + $(element).attr("data-container")).trigger("shown");
}

function hideLink(e, element) {
  e.preventDefault();
  e.stopPropagation();
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

$(function () {
  $('[data-toggle="tooltip"]').tooltip();

  $.fn.select2.defaults.set("language", "de");
  $(".autocomplete").select2({
    width: "100%",
    theme: "bootstrap4",
  });
  $(".autocomplete-multi").select2({
    width: "100%",
  });

  $(".datepicker").each(function (index, element) {
    start_datepicker($(element));
  });

  $(".timepicker").each(function (index, element) {
    start_timepicker($(element));
  });

  $("#clear_location_btn").click(function () {
    $("#coordinate").val("");
    $("#location").val("");
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
