moment.locale('de')
$.datepicker.setDefaults($.datepicker.regional["de"]);

jQuery.tools.recurrenceinput.localize('de', {
    displayUnactivate: 'Keine Wiederholungen',
    displayActivate: 'Wiederholt sich alle ',
    edit_rules: 'Bearbeiten...',
    add_rules: 'Hinzufügen...',
    delete_rules: 'Löschen',
    add: 'Hinzufügen',
    refresh: 'Aktualisieren',
    title: 'Wiederholung',
    preview: 'Ausgewählte Termine',
    addDate: 'Termin hinzufügen',
    recurrenceType: 'Wiederholt sich:',
    dailyInterval1: 'Wiederholung :',
    dailyInterval2: 'Tage',
    weeklyInterval1: 'Wiederholt sich alle:',
    weeklyInterval2: 'Woche(n)',
    weeklyWeekdays: 'Wiederholt sich alle:',
    weeklyWeekdaysHuman: 'am: ',
    monthlyInterval1: 'Wiederholt sich alle:',
    monthlyInterval2: 'Monat(e)',
    monthlyDayOfMonth1: 'Tag',
    monthlyDayOfMonth1Human: 'am Tag',
    monthlyDayOfMonth2: 'des Monats',
    monthlyDayOfMonth3: 'Monat(e)',
    monthlyDayOfMonth4: 'monthly_day_of_month_4',
    monthlyWeekdayOfMonth1: 'Den',
    monthlyWeekdayOfMonth1Human: 'am',
    monthlyWeekdayOfMonth2: ' ',
    monthlyWeekdayOfMonth3: 'im Monat',
    monthlyRepeatOn: 'Wiederholt sich:',
    yearlyInterval1: 'Wiederholt sich alle:',
    yearlyInterval2: 'Jahr(e)',
    yearlyDayOfMonth1: 'Jeden',
    yearlyDayOfMonth1Human: 'am',
    yearlyDayOfMonth2: ' ',
    yearlyDayOfMonth3: ' ',
    yearlyWeekdayOfMonth1: 'Den',
    yearlyWeekdayOfMonth1Human: 'am',
    yearlyWeekdayOfMonth2: ' ',
    yearlyWeekdayOfMonth3: 'von',
    yearlyWeekdayOfMonth4: ' ',
    yearlyRepeatOn: 'Wiederholt sich:',
    range: 'Ende der Wiederholung:',
    rangeNoEnd: 'Niemals',
    rangeByOccurrences1: 'Endet nach',
    rangeByOccurrences1Human: 'endet nach',
    rangeByOccurrences2: 'Ereigniss(en)',
    rangeByEndDate: 'Bis ',
    rangeByEndDateHuman: 'endet am ',
    including: ', und auch ',
    except Exception: ', ausser für',
    cancel: 'Abbrechen',
    save: 'Speichern',
    recurrenceStart: 'Beginn der Wiederholung',
    additionalDate: 'Weitere Termine',
    include: 'Eingeschlossen',
    exclude: 'Ausgenommen',
    remove: 'Entfernen',
    orderIndexes: [
        'ersten', 'zweiten', 'dritten',
        'vierten', 'letzten'],
    months: [
        'Januar', 'Februar', 'März', 'April',
        'Mai', 'Juni', 'Juli', 'August',
        'September', 'Oktober', 'November', 'Dezember'],
    shortMonths: [
        'Jan', 'Feb', 'Mär',
        'Apr', 'Mai', 'Jun',
        'Jul', 'Aug', 'Sep',
        'Okt', 'Nov', 'Dez'],
    weekdays: [
        'Sonntag', 'Montag', 'Dienstag', 'Mittwoch', 'Donnerstag',
        'Freitag', 'Samstag'],
    shortWeekdays: ['Son', 'Mon', 'Die', 'Mit', 'Don', 'Fre', 'Sam'],
    longDateFormat: 'D, dd.mm.yy',
    shortDateFormat: 'dd.mm.yy',
    unsupportedFeatures: 'Warning: This event uses recurrence features not supported by this widget. Saving the recurrence may change the recurrence in unintended ways: ',
    noTemplateMatch: 'No matching recurrence template',
    multipleDayOfMonth: 'Dieses Widget unterstützt keine mehrfach angelegten Tage in monatlicher oder jährlicher Wiederholung',
    bysetpos: 'BYSETPOS wird nicht unterstützt',
    noRule: 'Keine RRULE in RRULE Daten',
    noRepeatEvery: 'Error: The "Repeat every"-field must be between 1 and 1000',
    noEndDate: 'Fehler: Das Terminende ist nicht gesetzt. Bitte geben Sie einen korrekten Wert ein.',
    noRepeatOn: 'Error: "Repeat on"-value must be selected',
    pastEndDate: 'Fehler: Das Terminende kann nicht vor dem Terminanfang sein.',
    noEndAfterNOccurrences: 'Error: The "After N occurrences"-field must be between 1 and 1000',
    alreadyAdded: 'Das Datum wurde bereits hinzugefügt',
    rtemplate: {
        daily: 'Täglich',
        mondayfriday: 'Montags und Freitags',
        weekdays: 'Wochentags',
        weekly: 'Wöchentlich',
        monthly: 'Monatlich',
        yearly: 'Jährlich',
        }
});

function start_datepicker(input) {
    var hidden_field = input;
    var hidden_field_id = hidden_field.attr('id');

    var user_field = hidden_field.clone();
    user_field.removeAttr('name');
    user_field.removeClass('datepicker');
    user_field.attr('id', hidden_field_id + '-user');
    user_field.attr('autocomplete', 'off');

    var picker = user_field.datepicker({
        dateFormat: "D, dd.mm.yy",
        altField: hidden_field,
        altFormat: "yy-mm-dd",
        onSelect: function(date) {
            hidden_field.change();
        }
      });

    hidden_field.data('picker', picker);
    hidden_field.hide();

    var hidden_value = hidden_field.val();
    if (hidden_value) {
        picker.datepicker("setDate", moment(hidden_value).toDate());
    }

    hidden_field.after(user_field);

    $("#" + hidden_field_id + "-clear-button").click(function() {
        picker.datepicker("setDate", null);
        $("#" + hidden_field_id + "-hour").val("00");
        $("#" + hidden_field_id + "-minute").val("00");
      });

    hidden_field.change(function() {
        var hidden_value = hidden_field.val();
        var existing_date = picker.datepicker( "getDate" );
        var existing_moment = existing_date != null ? moment(existing_date) : null;

        if (hidden_value) {
            hidden_moment = moment(hidden_value);
            if (!hidden_moment.isSame(existing_moment)) {
                picker.datepicker("setDate", hidden_moment.toDate());
            }
        } else if (existing_date != null) {
            picker.datepicker("setDate", null);
        }
    });

    user_field.change(function() {
        var user_value = user_field.val();
        if (!user_value) {
            picker.datepicker("setDate", null);
        }
    });

    return picker;
}

function handle_request_start(result_id = '#result_container', spinner_id = '#spinner', error_id = '#error_alert') {
    $(result_id).hide();
    $(spinner_id).show();
    $(error_id).hide();
}

function handle_request_error(xhr, status, error, result_id = '#result_container', spinner_id = '#spinner', error_id = '#error_alert') {
    $(error_id).text(status);
    $(error_id).show();
    $(spinner_id).hide();
}

function handle_request_success(result_id = '#result_container', spinner_id = '#spinner', error_id = '#error_alert') {
    $(result_id).show();
    $(spinner_id).hide();
    $(error_id).hide();
}

$( function() {
    $('[data-toggle="tooltip"]').tooltip();
    $('.autocomplete').select2({width: '100%'});
    $('.autocomplete-tags').select2({width: '100%', tags: true});
    $('.datepicker').each(function (index, element){
        start_datepicker($(element));
    });

    $("#clear_location_btn").click(function () {
        $("#coordinate").val("");
        $("#location").val("");
    });

    $("#geolocation_btn").click(function () {
        if ("geolocation" in navigator){
            navigator.geolocation.getCurrentPosition(function(position){
                    $("#coordinate").val(position.coords.latitude+","+position.coords.longitude);
                    $("#location").val("Aktuelle Position");
                    $("#location").removeClass("is-invalid");
            }, handleError);

            function handleError(error){
                //Handle Errors
                switch(error.code) {
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
        }else{
            alert("Browser doesn't support geolocation!");
        }
    });
});

String.prototype.truncate = String.prototype.truncate ||
function ( n, useWordBoundary ){
  if (this.length <= n) { return this; }
  const subString = this.substr(0, n-1); // the original check
  return (useWordBoundary
    ? subString.substr(0, subString.lastIndexOf(" "))
    : subString) + "&hellip;";
};

function scroll_to_element(element, complete) {
    $('html, body').animate({ scrollTop: element.offset().top }, { duration: 'slow', complete: complete });
}