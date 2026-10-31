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
  var date_field = $(document).find(field_id);
  var time_field = $(document).find(field_id + "-time");
  return get_moment_with_time_from_fields(date_field, time_field)
}

function set_date_bounds(picker) {
  var data_range_to_attr = picker.attr("data-range-to");

  if (data_range_to_attr) {
    var hidden_field_id = picker.attr("id").replace("-user", "");
    var from_moment = get_moment_with_time("#" + hidden_field_id);
    $(document).find(data_range_to_attr + "-user").datepicker(
      "option",
      "minDate",
      from_moment.toDate()
    );

    var end_val = $(document).find(data_range_to_attr).val();
    if (end_val != "") {
      var end_moment = get_moment_with_time(data_range_to_attr);

      if (end_moment < from_moment) {
        set_picker_date($(document).find(data_range_to_attr), from_moment.toDate());
      }
    }
  }

  var data_range_from_attr = picker.attr("data-range-from");
  if (data_range_from_attr) {
    var hidden_field_id = picker.attr("id").replace("-user", "");
    var to_moment = get_moment_with_time("#" + hidden_field_id);

    var start_val = $(document).find(data_range_from_attr).val();
    if (start_val != "") {
      var start_moment = get_moment_with_time(data_range_from_attr);
      if (start_moment > to_moment) {
        set_picker_date($(document).find(data_range_from_attr), to_moment.toDate());
      }
    }
  }
}

function set_picker_date(picker, date, timeout = -1) {
  picker.datepicker("setDate", date);

  if (timeout < 0) {
    set_date_bounds(picker);
  } else {
    window.setTimeout(function () {
      set_date_bounds(picker);
    }, timeout);
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
    $(document).find(data_range_to_attr).attr("data-range-from", "#" + hidden_field_id);
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

  return picker;
}

$(function () {
  $('[data-toggle="tooltip"]').tooltip();

  $("form .datepicker").each(function (index, element) {
    start_datepicker($(element));
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

  $(document).on('select2:open', function(e) {
    document.querySelector(`[aria-controls="select2-${e.target.id}-results"]`).focus();
  });
});
