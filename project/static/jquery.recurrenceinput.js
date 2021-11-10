/*jslint regexp: false, continue: true, indent: 4 */
/*global $, alert, jQuery */
"use strict";

(function ($) {
    $.tools = $.tools || {version: '@VERSION'};
    $.views.settings.debugMode(true);

    var tool;
    var LABELS = {};

    tool = $.tools.recurrenceinput = {
        conf: {
            lang: 'de',
            readOnly: false,
            firstDay: 1,
            prefix: '',

            // "REMOTE" FIELD
            startField: null,
            startFieldYear: null,
            startFieldMonth: null,
            startFieldDay: null,
            ajaxURL: null,
            ajaxContentType: 'application/json; charset=utf8',
            ributtonExtraClass: '',

            // INPUT CONFIGURATION
            hasRepeatForeverButton: true,

            // FORM OVERLAY
            formOverlay: {
                speed: 'fast',
                fixed: false
            },

            // JQUERY TEMPLATE NAMES
            template: {
                form: '#jquery-recurrenceinput-form-tmpl',
                display: '#jquery-recurrenceinput-display-tmpl'
            },

            // RECURRENCE TEMPLATES
            rtemplate: {
                daily: {
                    rrule: 'FREQ=DAILY',
                    fields: [
                        'ridailyinterval',
                        'rirangeoptions'
                    ]
                },
                weekly: {
                    rrule: 'FREQ=WEEKLY',
                    fields: [
                        'riweeklyinterval',
                        'riweeklyweekdays',
                        'rirangeoptions'
                    ]
                },
                monthly: {
                    rrule: 'FREQ=MONTHLY',
                    fields: [
                        'rimonthlyinterval',
                        'rimonthlyoptions',
                        'rirangeoptions'
                    ]
                },
                yearly: {
                    rrule: 'FREQ=YEARLY',
                    fields: [
                        'riyearlyinterval',
                        'riyearlyoptions',
                        'rirangeoptions'
                    ]
                }
            }
        },

        localize: function (language, labels) {
            LABELS[language] = labels;
        },

        setTemplates: function (templates, titles) {
            var lang, template;
            tool.conf.rtemplate = templates;
            for (lang in titles) {
                if (titles.hasOwnProperty(lang)) {
                    for (template in titles[lang]) {
                        if (titles[lang].hasOwnProperty(template)) {
                            LABELS[lang].rtemplate[template] = titles[lang][template];
                        }
                    }
                }
            }
        }

    };

    tool.localize("en", {
        displayUnactivate: 'Does not repeat',
        displayActivate: 'Repeats every',
        add_rules: 'Add',
        edit_rules: 'Edit',
        delete_rules: 'Delete',
        add:  'Add',
        refresh: 'Refresh',

        title: 'Repeat',
        preview: 'Selected dates',
        addDate: 'Add date',

        recurrenceType: 'Repeats:',

        dailyInterval1: 'Repeat every:',
        dailyInterval2: 'days',

        weeklyInterval1: 'Repeat every:',
        weeklyInterval2: 'week(s)',
        weeklyWeekdays: 'Repeat on:',
        weeklyWeekdaysHuman: 'on:',

        monthlyInterval1: 'Repeat every:',
        monthlyInterval2: 'month(s)',
        monthlyDayOfMonth1: 'Day',
        monthlyDayOfMonth1Human: 'on day',
        monthlyDayOfMonth2: 'of the month',
        monthlyDayOfMonth3: 'month(s)',
        monthlyWeekdayOfMonth1: 'The',
        monthlyWeekdayOfMonth1Human: 'on the',
        monthlyWeekdayOfMonth2: '',
        monthlyWeekdayOfMonth3: 'of the month',
        monthlyRepeatOn: 'Repeat on:',

        yearlyInterval1: 'Repeat every:',
        yearlyInterval2: 'year(s)',
        yearlyDayOfMonth1: 'Every',
        yearlyDayOfMonth1Human: 'on',
        yearlyDayOfMonth2: '',
        yearlyDayOfMonth3: '',
        yearlyWeekdayOfMonth1: 'The',
        yearlyWeekdayOfMonth1Human: 'on the',
        yearlyWeekdayOfMonth2: '',
        yearlyWeekdayOfMonth3: 'of',
        yearlyWeekdayOfMonth4: '',
        yearlyRepeatOn: 'Repeat on:',

        range: 'End recurrence:',
        rangeNoEnd: 'Never',
        rangeByOccurrences1: 'After',
        rangeByOccurrences1Human: 'ends after',
        rangeByOccurrences2: 'occurrence(s)',
        rangeByEndDate: 'On',
        rangeByEndDateHuman: 'ends on',

        including: ', and also',
        except: ', except for',

        cancel: 'Cancel',
        save: 'Save',

        recurrenceStart: 'Start of the recurrence',
        additionalDate: 'Additional date',
        include: 'Include',
        exclude: 'Exclude',
        remove: 'Remove',

        orderIndexes: ['first', 'second', 'third', 'fourth', 'last'],
        months: [
            'January', 'February', 'March', 'April', 'May', 'June',
            'July', 'August', 'September', 'October', 'November', 'December'],
        shortMonths: [
            'Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
            'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'],
        weekdays: [
            'Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday',
            'Friday', 'Saturday'],
        shortWeekdays: [
            'Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'],

        longDateFormat: 'mmmm dd, yyyy',
        shortDateFormat: 'mm/dd/yyyy',

        unsupportedFeatures: 'Warning: This event uses recurrence features not ' +
                              'supported by this widget. Saving the recurrence ' +
                              'may change the recurrence in unintended ways:',
        noTemplateMatch: 'No matching recurrence template',
        multipleDayOfMonth: 'This widget does not support multiple days in monthly or yearly recurrence',
        bysetpos: 'BYSETPOS is not supported',
        noRule: 'No RRULE in RRULE data',
        noRepeatEvery: 'Error: The "Repeat every"-field must be between 1 and 1000',
        noEndDate: 'Error: End date is not set. Please set a correct value',
        noRepeatOn: 'Error: "Repeat on"-value must be selected',
        pastEndDate: 'Error: End date cannot be before start date',
        noEndAfterNOccurrences: 'Error: The "After N occurrences"-field must be between 1 and 1000',
        alreadyAdded: 'This date was already added',

        rtemplate: {
            daily: 'Daily',
            mondayfriday: 'Monday and Friday',
            weekdays: 'Weekday',
            weekly: 'Weekly',
            monthly: 'Monthly',
            yearly: 'Yearly'
        },

        reccStart: 'Start date',
        reccStartTime: 'Begin',
        reccFoEndTime: 'End',
        reccAllDay: 'All day',
    });


    var OCCURRENCETMPL = ['<div class="rioccurrences list-group list-group-flush">',
        '{{for occurrences}}',
            '<div class="occurrence {{:type}} list-group-item d-flex justify-content-between align-items-center p-1">',
                '<span>',
                    '{{:formattedDate}}',
                    '{{if type === "start"}}',
                        '<span class="rlabel">{{:~root.i18n.recurrenceStart}}</span>',
                    '{{/if}}',
                    '{{if type === "rdate"}}',
                        '<span class="rlabel">{{:~root.i18n.additionalDate}}</span>',
                    '{{/if}}',
                '</span>',
                '{{if !~root.readOnly}}',
                    '<span class="action">',
                        '{{if type === "rrule"}}',
                            '<a date="{{:date}}" href="#"',
                               'class="{{:type}} btn btn-outline-secondary btn-sm" title="{{:~root.i18n.exclude}}">',
                                '<i class="fa fa-trash"></i>',
                            '</a>',
                        '{{/if}}',
                        '{{if type === "rdate"}}',
                            '<a date="{{:date}}" href="#"',
                               'class="{{:type}} btn btn-outline-secondary btn-sm" title="{{:~root.i18n.remove}}" >',
                                '<i class="fa fa-trash"></i>',
                            '</a>',
                        '{{/if}}',
                        '{{if type === "exdate"}}',
                            '<a date="{{:date}}" href="#"',
                               'class="{{:type}} btn btn-outline-secondary btn-sm" title="{{:~root.i18n.include}}">',
                                '<i class="fa fa-trash-restore"></i>',
                            '</a>',
                        '{{/if}}',
                    '</span>',
                '{{/if}}',
            '</div>',
        '{{/for}}',
        '<div class="batching">',
            '{{for batch.batches}}',
                '{{if #getIndex() === ~root.batch.currentBatch}}<span class="current">{{/if}}',
                    '<a href="#" start="{{:~root.batch.batches[#getIndex()][0]}}">[{{:~root.batch.batches[#getIndex()][0]}} - {{:~root.batch.batches[#getIndex()][1]}}]</a>',
                '{{if #getIndex() === ~root.batch.currentBatch}}</span>{{/if}}',
            '{{/for}}',
        '</div></div>'].join('\n');

    $.templates('occurrenceTmpl', OCCURRENCETMPL);

    var DISPLAYTMPL = ['<div class="ridisplay">',
        '<div class="rimain bg-light mt-3 p-3 rounded border">',
            '<div class="mb-2">',
                '<div class="ridisplay-start"></div>',
                '<div class="ridisplay-times"></div>',
                '<div class="ridisplay">{{:i18n.displayUnactivate}}</div>',
            '</div>',
            '{{if !readOnly}}',
                '<button type="button" name="riedit" class="btn btn-outline-secondary">{{:i18n.add_rules}}</button>',
                '<button type="button" name="ridelete" class="btn btn-outline-secondary" style="display:none">{{:i18n.delete_rules}}</button>',
            '{{/if}}',
        '</div>',
        '<div class="rioccurrences" style="display:none" /></div>'].join('\n');

    $.templates('displayTmpl', DISPLAYTMPL);

    var FORMTMPL = ['<div class="modal fade" tabindex="-1" role="dialog">',
                        '<div class="modal-dialog" role="document">',
                            '<div class="modal-content modal-recurrence">',
                                '<div class="modal-header">',
                                    '<h5 class="modal-title">{{:i18n.title}}</h5>',
                                    '<button type="button" class="close" data-dismiss="modal" aria-label="Close">',
                                        '<span aria-hidden="true">&times;</span>',
                                    '</button>',
                                '</div>',
                                '<div class="modal-body">',
                                    '<div class="riform">',
                                        '<form>',
                                            '<div id="messagearea" style="display: none;">',
                                            '</div>',

                                            '<div class="form-row">',
                                                '<div class="form-group col-md-4">',
                                                    '<label class="mb-0" for="recc-start">{{:i18n.reccStart}}</label>',
                                                    '<input type="text" class="form-control datepicker" data-range-to="#recc-end" data-allday="#recc-allday" id="recc-start" name="recc-start" required="" />',
                                                '</div>',

                                                '<div class="form-group col-md-4" id="recc-start-time-group">',
                                                    '<label class="mb-0" for="recc-start-time">{{:i18n.reccStartTime}}</label>',
                                                    '<input type="text" class="form-control timepicker" id="recc-start-time" name="recc-start-time" required="" />',
                                                '</div>',

                                                '<div class="form-group col-md-4" id="recc-fo-end-time-group">',
                                                    '<label class="mb-0" for="recc-fo-end-time">{{:i18n.reccFoEndTime}}</label>',
                                                    '<input type="text" class="form-control timepicker" id="recc-fo-end-time" name="recc-fo-end-time" />',
                                                '</div>',
                                            '</div>',

                                            '<div class="form-row">',
                                                '<div class="form-group col-md">',
                                                    '<div class="form-check">',
                                                        '<input class="form-check-input" id="recc-allday" name="recc-allday" type="checkbox" value="y">',
                                                        '<label class="form-check-label" for="recc-allday">{{:i18n.reccAllDay}}</label>',
                                                    '</div>',
                                                '</div>',
                                            '</div>',

                                            '<div class="form-row">',
                                                '<div id="rirangeoptions" class="form-group col-md">',
                                                    '<label class="mb-0">{{:i18n.range}}</label>',
                                                        '<div class="input-group mb-1">',
                                                            '<div class="input-group-prepend">',
                                                                '<div class="input-group-text">',
                                                                    '<input',
                                                                        'type="radio"',
                                                                        'checked="checked"',
                                                                        'value="BYENDDATE"',
                                                                        'name="rirangetype"',
                                                                        'class="form-check-inline"',
                                                                        'id="{{:name}}rangetype:BYENDDATE"/>',
                                                                    '{{:i18n.rangeByEndDate}}',
                                                                '</div>',
                                                            '</div>',
                                                            '<input',
                                                                'type="text"',
                                                                'class="form-control"',
                                                                'name="rirangebyenddatecalendar" id="recc-end" />',
                                                        '</div>',
                                                        '<div class="input-group mb-1">',
                                                            '<div class="input-group-prepend">',
                                                                '<div class="input-group-text">',
                                                                    '<input',
                                                                        'type="radio"',
                                                                        'value="BYOCCURRENCES"',
                                                                        'name="rirangetype"',
                                                                        'class="form-check-inline"',
                                                                        'id="{{:name}}rangetype:BYOCCURRENCES"/>',
                                                                    '{{:i18n.rangeByOccurrences1}}',
                                                                '</div>',
                                                            '</div>',
                                                            '<input',
                                                                'type="text" size="3"',
                                                                'value="7"',
                                                                'class="form-control"',
                                                                'name="rirangebyoccurrencesvalue" />',
                                                            '<div class="input-group-append">',
                                                                '<span class="input-group-text">',
                                                                    '{{:i18n.rangeByOccurrences2}}',
                                                                '</span>',
                                                            '</div>',
                                                        '</div>',
                                                    '{{if hasRepeatForeverButton}}',
                                                        '<div class="input-group mb-1">',
                                                            '<div class="input-group-text w-100">',
                                                                '<input',
                                                                    'type="radio"',
                                                                    'value="NOENDDATE"',
                                                                    'name="rirangetype"',
                                                                    'class="form-check-inline"',
                                                                    'id="{{:name}}rangetype:NOENDDATE"/>',
                                                                '{{:i18n.rangeNoEnd}}',
                                                            '</div>',
                                                        '</div>',
                                                    '{{/if}}',
                                                '</div>',
                                            '</div>',

                                            '<div class="form-row">',
                                                '<div class="form-group col-md">',
                                                    '<label for="{{:name}}rtemplate" class="mb-0">',
                                                        '{{:i18n.recurrenceType}}',
                                                    '</label>',
                                                    '<select id="rirtemplate" name="rirtemplate" class="form-control">',
                                                        '{{props rtemplate}}',
                                                            '<option value="{{>key}}">{{:~root.i18n.rtemplate[key]}}</value>',
                                                        '{{/props}}',
                                                    '</select>',
                                                '</div>',

                                                '<div class="col-md">',
                                                    '<div id="ridailyinterval" class="form-group rifield">',
                                                        '<label for="{{:name}}dailyinterval" class="mb-0">',
                                                            '{{:i18n.dailyInterval1}}',
                                                        '</label>',
                                                        '<div class="input-group">',
                                                            '<input type="text" size="2"',
                                                                'value="1"',
                                                                'name="ridailyinterval"',
                                                                'class="form-control"',
                                                                'id="{{:name}}dailyinterval" />',
                                                            '<div class="input-group-append">',
                                                                '<span class="input-group-text">',
                                                                    '{{:i18n.dailyInterval2}}',
                                                                '</span>',
                                                            '</div>',
                                                        '</div>',
                                                    '</div>',
                                                    '<div id="riweeklyinterval" class="form-group rifield">',
                                                        '<label for="{{:name}}weeklyinterval" class="mb-0">',
                                                            '{{:i18n.weeklyInterval1}}',
                                                        '</label>',
                                                        '<div class="input-group">',
                                                            '<input type="text" size="2"',
                                                                'value="1"',
                                                                'name="riweeklyinterval"',
                                                                'class="form-control"',
                                                                'id="{{:name}}riweeklyinterval" />',
                                                            '<div class="input-group-append">',
                                                                '<span class="input-group-text">',
                                                                    '{{:i18n.weeklyInterval2}}',
                                                                '</span>',
                                                            '</div>',
                                                        '</div>',
                                                    '</div>',
                                                    '<div id="rimonthlyinterval" class="form-group rifield">',
                                                        '<label for="rimonthlyinterval" class="mb-0">{{:i18n.monthlyInterval1}}</label>',
                                                        '<div class="input-group">',
                                                            '<input type="text" size="2"',
                                                                'value="1"',
                                                                'name="rimonthlyinterval"',
                                                                'class="form-control" />',
                                                            '<div class="input-group-append">',
                                                                '<span class="input-group-text">',
                                                                    '{{:i18n.monthlyInterval2}}',
                                                                '</span>',
                                                            '</div>',
                                                        '</div>',
                                                    '</div>',
                                                    '<div id="riyearlyinterval" class="form-group rifield">',
                                                        '<label for="riyearlyinterval" class="mb-0">{{:i18n.yearlyInterval1}}</label>',
                                                        '<div class="input-group">',
                                                            '<input type="text" size="2"',
                                                                'value="1" ',
                                                                'class="form-control"',
                                                                'name="riyearlyinterval"/>',
                                                            '<div class="input-group-append">',
                                                                '<span class="input-group-text">',
                                                                    '{{:i18n.yearlyInterval2}}',
                                                                '</span>',
                                                            '</div>',
                                                        '</div>',
                                                    '</div>',
                                                '</div>',
                                            '</div>',

                                            '<div id="riweeklyweekdays" class="form-group rifield">',
                                                '<label for="{{:name}}weeklyinterval" class="mb-0">{{:i18n.weeklyWeekdays}}</label>',
                                                '<div>',
                                                    '{{for orderedWeekdays itemVar=\'~value\'}}',
                                                        '<div class="form-check form-check-inline">',
                                                            '<input type="checkbox"',
                                                                'name="riweeklyweekdays{{:~root.weekdays[~value]}}"',
                                                                'id="{{:name}}weeklyWeekdays{{:~root.weekdays[~value]}}"',
                                                                'class="form-check-input"',
                                                                'value="{{:~root.weekdays[~value]}}" />',
                                                            '<label for="{{:name}}weeklyWeekdays{{:~root.weekdays[~value]}}" class="form-check-label">{{:~root.i18n.shortWeekdays[~value]}}</label>',
                                                        '</div>',
                                                    '{{/for}}',
                                                '</div>',
                                            '</div>',
                                            '<div id="rimonthlyoptions" class="form-group rifield">',
                                                '<label for="rimonthlytype" class="mb-0">{{:i18n.monthlyRepeatOn}}</label>',
                                                '<div>',
                                                    '<div class="input-group mb-1">',
                                                        '<div class="input-group-prepend">',
                                                            '<div class="input-group-text">',
                                                                '<input',
                                                                    'type="radio"',
                                                                    'value="DAYOFMONTH"',
                                                                    'name="rimonthlytype"',
                                                                    'class="form-check-inline"',
                                                                    'id="{{:name}}monthlytype:DAYOFMONTH" />',
                                                                '{{:i18n.monthlyDayOfMonth1}}',
                                                            '</div>',
                                                        '</div>',
                                                        '<select name="rimonthlydayofmonthday" class="form-control"',
                                                            'id="{{:name}}monthlydayofmonthday">',
                                                        '{{for start=1 end=32}}',
                                                            '<option value="{{:}}">{{:}}</option>',
                                                        '{{/for}}',
                                                        '</select>',
                                                        '<div class="input-group-append">',
                                                            '<div class="input-group-text">',
                                                                '{{:i18n.monthlyDayOfMonth2}}',
                                                            '</div>',
                                                        '</div>',
                                                    '</div>',
                                                    '<div class="input-group">',
                                                        '<div class="input-group-prepend">',
                                                            '<div class="input-group-text">',
                                                                '<input',
                                                                    'type="radio"',
                                                                    'value="WEEKDAYOFMONTH"',
                                                                    'name="rimonthlytype"',
                                                                    'class="form-check-inline"',
                                                                    'id="{{:name}}monthlytype:WEEKDAYOFMONTH" />',
                                                                '{{:i18n.monthlyWeekdayOfMonth1}}',
                                                            '</div>',
                                                        '</div>',
                                                        '<select name="rimonthlyweekdayofmonthindex" class="form-control">',
                                                            '{{for i18n.orderIndexes}}',
                                                                '<option value="{{:~root.orderIndexes[$index]}}">{{:}}</option>',
                                                            '{{/for}}',
                                                        '</select>',
                                                        '<select name="rimonthlyweekdayofmonth" class="form-control">',
                                                            '{{for orderedWeekdays itemVar=\'~value\'}}',
                                                                '<option value="{{:~root.weekdays[~value]}}">{{:~root.i18n.weekdays[~value]}}</option>',
                                                            '{{/for}}',
                                                        '</select>',
                                                        '<div class="input-group-append">',
                                                            '<div class="input-group-text">',
                                                                '{{:i18n.monthlyWeekdayOfMonth3}}',
                                                            '</div>',
                                                        '</div>',
                                                    '</div>',
                                                '</div>',
                                            '</div>',
                                            '<div id="riyearlyoptions" class="form-group rifield">',
                                                '<label for="riyearlyType" class="mb-0">{{:i18n.yearlyRepeatOn}}</label>',
                                                '<div>',
                                                    '<div class="input-group mb-1">',
                                                        '<div class="input-group-prepend">',
                                                            '<div class="input-group-text">',
                                                                '<input',
                                                                    'type="radio"',
                                                                    'value="DAYOFMONTH"',
                                                                    'name="riyearlyType"',
                                                                    'class="form-check-inline"',
                                                                    'id="{{:name}}yearlytype:DAYOFMONTH" />',
                                                                '{{:i18n.yearlyDayOfMonth1}}',
                                                            '</div>',
                                                        '</div>',
                                                        '<select name="riyearlydayofmonthday" class="form-control">',
                                                        '{{for start=1 end=32}}',
                                                            '<option value="{{:}}">{{:}}</option>',
                                                        '{{/for}}',
                                                        '</select>',
                                                        '<select name="riyearlydayofmonthmonth" class="form-control">',
                                                        '{{for i18n.months}}',
                                                            '<option value="{{:#getIndex()+1}}">{{:}}</option>',
                                                        '{{/for}}',
                                                        '</select>',
                                                    '</div>',
                                                    '<div class="input-group">',
                                                        '<div class="input-group-prepend">',
                                                            '<div class="input-group-text">',
                                                                '<input',
                                                                    'type="radio"',
                                                                    'value="WEEKDAYOFMONTH"',
                                                                    'name="riyearlyType"',
                                                                    'class="form-check-inline"',
                                                                    'id="{{:name}}yearlytype:WEEKDAYOFMONTH"/>',
                                                            '{{:i18n.yearlyWeekdayOfMonth1}}',
                                                            '</div>',
                                                        '</div>',
                                                        '<select name="riyearlyweekdayofmonthindex" class="form-control">',
                                                        '{{for i18n.orderIndexes}}',
                                                            '<option value="{{:~root.orderIndexes[#getIndex()]}}">{{:}}</option>',
                                                        '{{/for}}',
                                                        '</select>',
                                                        '<select name="riyearlyweekdayofmonthday" class="form-control">',
                                                        '{{for orderedWeekdays itemVar=\'~value\'}}',
                                                            '<option value="{{:~root.weekdays[~value]}}">{{:~root.i18n.weekdays[~value]}}</option>',
                                                        '{{/for}}',
                                                        '</select>',
                                                        '<div class="input-group-append">',
                                                            '<div class="input-group-text">',
                                                                '{{:i18n.yearlyWeekdayOfMonth3}}',
                                                            '</div>',
                                                        '</div>',
                                                        '<select name="riyearlyweekdayofmonthmonth" class="form-control">',
                                                        '{{for i18n.months}}',
                                                            '<option value="{{:#getIndex()+1}}">{{:}}</option>',
                                                        '{{/for}}',
                                                        '</select>',
                                                    '</div>',
                                                '</div>',
                                            '</div>',

                                            '<div id="occurences-show-container">',
                                                '<a href="#" class="show-link" data-container="occurences-container" data-show-container="occurences-show-container"><i class="fa fa-chevron-down"></i> {{:i18n.preview}}</a>',
                                            '</div>',
                                            '<div id="occurences-container" style="display: none;">',
                                                '<div class="rioccurrencesactions">',
                                                    '<div class="rioccurancesheader">',
                                                        '<h2 class="my-2">{{:i18n.preview}}',
                                                            '<span class="refreshbutton action">',
                                                                '<a class="btn btn-sm btn-outline-secondary rirefreshbutton" href="#" title="{{:i18n.refresh}}">',
                                                                    '<i class="fa fa-sync-alt"></i>',
                                                                '</a>',
                                                            '</span>',
                                                        '</h2>',
                                                    '</div>',
                                                '</div>',
                                                '<div class="rioccurrences">',
                                                '</div>',
                                                '<div class="rioccurrencesactions">',
                                                    '<div class="riaddoccurrence mt-3">',
                                                        '<div class="errorarea"></div>',
                                                        '<div class="input-group">',
                                                            '<div class="input-group-prepend">',
                                                                '<span class="input-group-text">{{:i18n.addDate}}</span>',
                                                            '</div>',
                                                            '<input type="text" class="form-control" name="adddate" id="adddate" />',
                                                            '<div class="input-group-append">',
                                                                '<input type="button" class="btn btn-outline-secondary" name="addoccurencebtn" id="addoccurencebtn" value="{{:i18n.add}}" />',
                                                            '</div>',
                                                        '</div>',
                                                    '</div>',
                                                '</div>',
                                                '<div class="mt-3" id="occurences-hide-container">',
                                                    '<a href="#" class="hide-link" data-container="occurences-container" data-show-container="occurences-show-container"><i class="fa fa-chevron-up"></i> {{:i18n.preview}}</a>',
                                                '</div>',
                                            '</div>',
                                        '</form>',
                                    '</div>',
                                '</div>',
                                '<div class="modal-footer">',
                                    '<button type="button" class="btn btn-secondary" data-dismiss="modal">{{:i18n.cancel}}</button>',
                                    '<button type="button" class="btn btn-primary risavebutton">{{:i18n.save}}</button>',
                                '</div>',
                            '</div>',
                        '</div>',
                    '</div>'].join('\n');

    $.templates('formTmpl', FORMTMPL);

    function format(date, fmt, conf) {
        return $.datepicker.formatDate(fmt, date);
    }

    /**
     * Parsing RFC5545 from widget
     */
    function widgetSaveToRfc5545(form, conf, tz) {
        var value = form.find('select[name=rirtemplate]').val();
        var rtemplate = conf.rtemplate[value];
        var result = rtemplate.rrule;
        var human = conf.i18n.rtemplate[value];
        var field, input, weekdays, i18nweekdays, i, j, index, tmp;
        var day, month, year, interval, yearlyType, occurrences, date;

        for (i = 0; i < rtemplate.fields.length; i++) {
            field = form.find('#' + rtemplate.fields[i]);

            switch (field.attr('id')) {

            case 'ridailyinterval':
                interval = field.find('input[name=ridailyinterval]').val();
                if (interval !== '1') {
                    result += ';INTERVAL=' + interval;
                }
                human = interval + ' ' + conf.i18n.dailyInterval2;
                break;

            case 'riweeklyinterval':
                interval = field.find('input[name=riweeklyinterval]').val();
                if (interval !== '1') {
                    result += ';INTERVAL=' + interval;
                }
                human = interval + ' ' + conf.i18n.weeklyInterval2;
                break;

            case 'riweeklyweekdays':
                weekdays = '';
                i18nweekdays = '';
                for (j = 0; j < conf.weekdays.length; j++) {
                    input = field.find('input[name=riweeklyweekdays' + conf.weekdays[j] + ']');
                    if (input.is(':checked')) {
                        if (weekdays) {
                            weekdays += ',';
                            i18nweekdays += ', ';
                        }
                        weekdays += conf.weekdays[j];
                        i18nweekdays += conf.i18n.weekdays[j];
                    }
                }
                if (weekdays) {
                    result += ';BYDAY=' + weekdays;
                    human += ' ' + conf.i18n.weeklyWeekdaysHuman + ' ' + i18nweekdays;
                }
                break;

            case 'rimonthlyinterval':
                interval = field.find('input[name=rimonthlyinterval]').val();
                if (interval !== '1') {
                    result += ';INTERVAL=' + interval;
                }
                human = interval + ' ' + conf.i18n.monthlyInterval2;
                break;

            case 'rimonthlyoptions':
                var monthlyType = $('input[name=rimonthlytype]:checked', form).val();
                switch (monthlyType) {

                case 'DAYOFMONTH':
                    day = $('select[name=rimonthlydayofmonthday]', form).val();
                    result += ';BYMONTHDAY=' + day;
                    human += ', ' + conf.i18n.monthlyDayOfMonth1Human + ' ' + day + ' ' + conf.i18n.monthlyDayOfMonth2;
                    break;
                case 'WEEKDAYOFMONTH':
                    index = $('select[name=rimonthlyweekdayofmonthindex]', form).val();
                    day = $('select[name=rimonthlyweekdayofmonth]', form).val();
                    if ($.inArray(day, ['MO', 'TU', 'WE', 'TH', 'FR', 'SA', 'SU']) > -1) {
                        result += ';BYDAY=' + index + day;
                        human += ', ' + conf.i18n.monthlyWeekdayOfMonth1Human + ' ';
                        human += ' ' + conf.i18n.orderIndexes[$.inArray(index, conf.orderIndexes)];
                        human += ' ' + conf.i18n.monthlyWeekdayOfMonth2;
                        human += ' ' + conf.i18n.weekdays[$.inArray(day, conf.weekdays)];
                        human += ' ' + conf.i18n.monthlyDayOfMonth2;
                    }
                    break;
                }
                break;

            case 'riyearlyinterval':
                interval = field.find('input[name=riyearlyinterval]').val();
                if (interval !== '1') {
                    result += ';INTERVAL=' + interval;
                }
                human = interval + ' ' + conf.i18n.yearlyInterval2;
                break;

            case 'riyearlyoptions':
                yearlyType = $('input[name=riyearlyType]:checked', form).val();
                switch (yearlyType) {

                case 'DAYOFMONTH':
                    month = $('select[name=riyearlydayofmonthmonth]', form).val();
                    day = $('select[name=riyearlydayofmonthday]', form).val();
                    result += ';BYMONTH=' + month;
                    result += ';BYMONTHDAY=' + day;
                    human += ', ' + conf.i18n.yearlyDayOfMonth1Human + ' ' + conf.i18n.months[month - 1] + ' ' + day;
                    break;
                case 'WEEKDAYOFMONTH':
                    index = $('select[name=riyearlyweekdayofmonthindex]', form).val();
                    day = $('select[name=riyearlyweekdayofmonthday]', form).val();
                    month = $('select[name=riyearlyweekdayofmonthmonth]', form).val();
                    result += ';BYMONTH=' + month;
                    if ($.inArray(day, ['MO', 'TU', 'WE', 'TH', 'FR', 'SA', 'SU']) > -1) {
                        result += ';BYDAY=' + index + day;
                        human += ', ' + conf.i18n.yearlyWeekdayOfMonth1Human;
                        human += ' ' + conf.i18n.orderIndexes[$.inArray(index, conf.orderIndexes)];
                        human += ' ' + conf.i18n.yearlyWeekdayOfMonth2;
                        human += ' ' + conf.i18n.weekdays[$.inArray(day, conf.weekdays)];
                        human += ' ' + conf.i18n.yearlyWeekdayOfMonth3;
                        human += ' ' + conf.i18n.months[month - 1];
                        human += ' ' + conf.i18n.yearlyWeekdayOfMonth4;
                    }
                    break;
                }
                break;

            case 'rirangeoptions':
                var rangeType = form.find('input[name=rirangetype]:checked').val();
                switch (rangeType) {

                case 'BYOCCURRENCES':
                    occurrences = form.find('input[name=rirangebyoccurrencesvalue]').val();
                    result += ';COUNT=' + occurrences;
                    human += ', ' + conf.i18n.rangeByOccurrences1Human;
                    human += ' ' + occurrences;
                    human += ' ' + conf.i18n.rangeByOccurrences2;
                    break;
                case 'BYENDDATE':
                    field = form.find('input[name=rirangebyenddatecalendar]');
                    date = $.datepicker.formatDate("yymmdd", field.data('picker').datepicker("getDate"));
                    result += ';UNTIL=' + date + 'T000000';
                    if (tz === true) {
                        // Make it UTC:
                        result += 'Z';
                    }
                    human += ', ' + conf.i18n.rangeByEndDateHuman;
                    human += ' ' + $.datepicker.formatDate("D, dd.mm.yy", field.data('picker').datepicker("getDate"));
                    break;
                }
                break;
            }
        }

        if (form.ical.RDATE !== undefined && form.ical.RDATE.length > 0) {
            form.ical.RDATE.sort();
            tmp = [];
            for (i = 0; i < form.ical.RDATE.length; i++) {
                if (form.ical.RDATE[i] !== '') {
                    year = parseInt(form.ical.RDATE[i].substring(0, 4), 10);
                    month = parseInt(form.ical.RDATE[i].substring(4, 6), 10) - 1;
                    day = parseInt(form.ical.RDATE[i].substring(6, 8), 10);
                    tmp.push(format(new Date(year, month, day), conf.i18n.longDateFormat, conf));
                }
            }
            if (tmp.length !== 0) {
                human = human + conf.i18n.including + ' ' + tmp.join('; ');
            }
        }

        if (form.ical.EXDATE !== undefined && form.ical.EXDATE.length > 0) {
            form.ical.EXDATE.sort();
            tmp = [];
            for (i = 0; i < form.ical.EXDATE.length; i++) {
                if (form.ical.EXDATE[i] !== '') {
                    year = parseInt(form.ical.EXDATE[i].substring(0, 4), 10);
                    month = parseInt(form.ical.EXDATE[i].substring(4, 6), 10) - 1;
                    day = parseInt(form.ical.EXDATE[i].substring(6, 8), 10);
                    tmp.push(format(new Date(year, month, day), conf.i18n.longDateFormat, conf));
                }
            }
            if (tmp.length !== 0) {
                human = human + conf.i18n.except + ' ' + tmp.join('; ');
            }
        }
        result = 'RRULE:' + result;
        if (form.ical.EXDATE !== undefined && form.ical.EXDATE.join() !== "") {
            tmp = $.map(form.ical.EXDATE, function (x) {
                if (x.length === 8) { // DATE format. Make it DATE-TIME
                    x += 'T000000';
                }
                if (tz === true) {
                    // Make it UTC:
                    x += 'Z';
                }
                return x;
            });
            result = result + '\nEXDATE:' + tmp;
        }
        if (form.ical.RDATE !== undefined && form.ical.RDATE.join() !== "") {
            tmp = $.map(form.ical.RDATE, function (x) {
                if (x.length === 8) { // DATE format. Make it DATE-TIME
                    x += 'T000000';
                }
                if (tz === true) {
                    // Make it UTC:
                    x += 'Z';
                }
                return x;
            });
            result = result + '\nRDATE:' + tmp;
        }
        return {result: result, description: human};
    }

    function parseLine(icalline) {
        var result = {};
        var pos = icalline.indexOf(':');
        var property = icalline.substring(0, pos);
        result.value = icalline.substring(pos + 1);

        if (property.indexOf(';') !== -1) {
            pos = property.indexOf(';');
            result.parameters = property.substring(pos + 1);
            result.property = property.substring(0, pos);
        } else {
            result.parameters = null;
            result.property = property;
        }
        return result;
    }

    function cleanDates(dates) {
        // Get rid of timezones
        // TODO: We could parse dates and range here, maybe?
        var result = [];
        var splitDates = dates.split(',');
        var date;

        for (date in splitDates) {
            if (splitDates.hasOwnProperty(date)) {
                if (splitDates[date].indexOf('Z') !== -1) {
                    result.push(splitDates[date].substring(0, 15));
                } else {
                    result.push(splitDates[date]);
                }
            }
        }
        return result;
    }

    function parseIcal(icaldata) {
        var lines = [];
        var result = {};
        var propAndValue = [];
        var line = null;
        var nextline;

        lines = icaldata.split('\n');
        lines.reverse();
        while (true) {
            if (lines.length > 0) {
                nextline = lines.pop();
                if (nextline.charAt(0) === ' ' || nextline.charAt(0) === '\t') {
                    // Line continuation:
                    line = line + nextline;
                    continue;
                }
            } else {
                nextline = '';
            }

            // New line; the current one is finished, add it to the result.
            if (line !== null) {
                line = parseLine(line);
                 // We ignore properties for now
                if (line.property === 'RDATE' || line.property === 'EXDATE') {
                    result[line.property] = cleanDates(line.value);
                } else {
                    result[line.property] = line.value;
                }
            }

            line = nextline;
            if (line === '') {
                break;
            }
        }
        return result;
    }

    function widgetLoadFromRfc5545(form, conf, icaldata, force) {
        var unsupportedFeatures = [];
        var i, matches, match, matchIndex, rtemplate, d, input, index;
        var selector, selectors, field, radiobutton, start, end;
        var interval, byday, bymonth, bymonthday, count, until;
        var day, month, year, weekday, ical;

        form.ical = parseIcal(icaldata);
        if (form.ical.RRULE === undefined) {
            unsupportedFeatures.push(conf.i18n.noRule);
            if (!force) {
                return -1; // Fail!
            }
        } else {


            matches = /INTERVAL=([0-9]+);?/.exec(form.ical.RRULE);
            if (matches) {
                interval = matches[1];
            } else {
                interval = '1';
            }

            matches = /BYDAY=([^;]+);?/.exec(form.ical.RRULE);
            if (matches) {
                byday = matches[1];
            } else {
                byday = '';
            }

            matches = /BYMONTHDAY=([^;]+);?/.exec(form.ical.RRULE);
            if (matches) {
                bymonthday = matches[1].split(",");
            } else {
                bymonthday = null;
            }

            matches = /BYMONTH=([^;]+);?/.exec(form.ical.RRULE);
            if (matches) {
                bymonth = matches[1].split(",");
            } else {
                bymonth = null;
            }

            matches = /COUNT=([0-9]+);?/.exec(form.ical.RRULE);
            if (matches) {
                count = matches[1];
            } else {
                count = null;
            }

            matches = /UNTIL=([0-9T]+);?/.exec(form.ical.RRULE);
            if (matches) {
                until = matches[1];
            } else {
                until = null;
            }

            matches = /BYSETPOS=([^;]+);?/.exec(form.ical.RRULE);
            if (matches) {
                unsupportedFeatures.push(conf.i18n.bysetpos);
            }

            // Find the best rule:
            match = '';
            matchIndex = null;
            for (i in conf.rtemplate) {
                if (conf.rtemplate.hasOwnProperty(i)) {
                    rtemplate = conf.rtemplate[i];
                    if (form.ical.RRULE.indexOf(rtemplate.rrule) === 0) {
                        if (form.ical.RRULE.length > match.length) {
                            // This is the best match so far
                            match = form.ical.RRULE;
                            matchIndex = i;
                        }
                    }
                }
            }

            if (match) {
                rtemplate = conf.rtemplate[matchIndex];
                // Set the selector:
                selector = form.find('select[name=rirtemplate]').val(matchIndex);
            } else {
                for (rtemplate in conf.rtemplate) {
                    if (conf.rtemplate.hasOwnProperty(rtemplate)) {
                        rtemplate = conf.rtemplate[rtemplate];
                        break;
                    }
                }
                unsupportedFeatures.push(conf.i18n.noTemplateMatch);
            }

            for (i = 0; i < rtemplate.fields.length; i++) {
                field = form.find('#' + rtemplate.fields[i]);
                switch (field.attr('id')) {

                case 'ridailyinterval':
                    field.find('input[name=ridailyinterval]').val(interval);
                    break;

                case 'riweeklyinterval':
                    field.find('input[name=riweeklyinterval]').val(interval);
                    break;

                case 'riweeklyweekdays':
                    byday = byday.split(",");
                    for (d = 0; d < conf.weekdays.length; d++) {
                        day = conf.weekdays[d];
                        input = field.find('input[name=riweeklyweekdays' + day + ']');
                        input.attr('checked', $.inArray(day, byday) !== -1);
                    }
                    break;

                case 'rimonthlyinterval':
                    field.find('input[name=rimonthlyinterval]').val(interval);
                    break;

                case 'rimonthlyoptions':
                    var monthlyType = 'DAYOFMONTH'; // Default to using BYMONTHDAY

                    if (bymonthday) {
                        monthlyType = 'DAYOFMONTH';
                        if (bymonthday.length > 1) {
                            // No support for multiple days in one month
                            unsupportedFeatures.push(conf.i18n.multipleDayOfMonth);
                            // Just keep the first
                            bymonthday = bymonthday[0];
                        }
                        field.find('select[name=rimonthlydayofmonthday]').val(bymonthday);
                    }

                    if (byday) {
                        monthlyType = 'WEEKDAYOFMONTH';

                        if (byday.indexOf(',') !== -1) {
                            // No support for multiple days in one month
                            unsupportedFeatures.push(conf.i18n.multipleDayOfMonth);
                            byday = byday.split(",")[0];
                        }
                        index = byday.slice(0, -2);
                        if (index.charAt(0) !== '+' && index.charAt(0) !== '-') {
                            index = '+' + index;
                        }
                        weekday = byday.slice(-2);
                        field.find('select[name=rimonthlyweekdayofmonthindex]').val(index);
                        field.find('select[name=rimonthlyweekdayofmonth]').val(weekday);
                    }

                    selectors = field.find('input[name=rimonthlytype]');
                    for (index = 0; index < selectors.length; index++) {
                        radiobutton = selectors[index];
                        $(radiobutton).attr('checked', radiobutton.value === monthlyType);
                    }
                    break;

                case 'riyearlyinterval':
                    field.find('input[name=riyearlyinterval]').val(interval);
                    break;

                case 'riyearlyoptions':
                    var yearlyType = 'DAYOFMONTH'; // Default to using BYMONTHDAY

                    if (bymonthday) {
                        yearlyType = 'DAYOFMONTH';
                        if (bymonthday.length > 1) {
                            // No support for multiple days in one month
                            unsupportedFeatures.push(conf.i18n.multipleDayOfMonth);
                            bymonthday = bymonthday[0];
                        }
                        field.find('select[name=riyearlydayofmonthmonth]').val(bymonth);
                        field.find('select[name=riyearlydayofmonthday]').val(bymonthday);
                    }

                    if (byday) {
                        yearlyType = 'WEEKDAYOFMONTH';

                        if (byday.indexOf(',') !== -1) {
                            // No support for multiple days in one month
                            unsupportedFeatures.push(conf.i18n.multipleDayOfMonth);
                            byday = byday.split(",")[0];
                        }
                        index = byday.slice(0, -2);
                        if (index.charAt(0) !== '+' && index.charAt(0) !== '-') {
                            index = '+' + index;
                        }
                        weekday = byday.slice(-2);
                        field.find('select[name=riyearlyweekdayofmonthindex]').val(index);
                        field.find('select[name=riyearlyweekdayofmonthday]').val(weekday);
                        field.find('select[name=riyearlyweekdayofmonthmonth]').val(bymonth);
                    }

                    selectors = field.find('input[name=riyearlyType]');
                    for (index = 0; index < selectors.length; index++) {
                        radiobutton = selectors[index];
                        $(radiobutton).attr('checked', radiobutton.value === yearlyType);
                    }
                    break;

                case 'rirangeoptions':
                    var rangeType = 'NOENDDATE';

                    if (count) {
                        rangeType = 'BYOCCURRENCES';
                        field.find('input[name=rirangebyoccurrencesvalue]').val(count);
                    }

                    if (until) {
                        rangeType = 'BYENDDATE';
                        input = field.find('input[name=rirangebyenddatecalendar]');
                        year = until.slice(0, 4);
                        month = until.slice(4, 6);
                        month = parseInt(month, 10) - 1;
                        day = until.slice(6, 8);
                        input.data('picker').datepicker("setDate", new Date(year, month, day));
                    }

                    selectors = field.find('input[name=rirangetype]');
                    for (index = 0; index <  selectors.length; index++) {
                        radiobutton = selectors[index];
                        $(radiobutton).attr('checked', radiobutton.value === rangeType);
                    }
                    break;
                }
            }
        }

        var messagearea = form.find('#messagearea');
        if (unsupportedFeatures.length !== 0) {
            messagearea.text(conf.i18n.unsupportedFeatures + ' ' + unsupportedFeatures.join('; '));
            messagearea.show();
            return 1;
        } else {
            messagearea.text('');
            messagearea.hide();
            return 0;
        }

    }

    /**
     * RecurrenceInput - form, display and tools for recurrenceinput widget
     */
    function RecurrenceInput(conf, textarea) {

        var self = this;
        var form, display, dialog;
        var prefix = conf.prefix;

        // Extend conf with non-configurable data used by templates.
        var orderedWeekdays = [];
        var index, i;
        for (i = 0; i < 7; i++) {
            index = i + conf.firstDay;
            if (index > 6) {
                index = index - 7;
            }
            orderedWeekdays.push(index);
        }

        $.extend(conf, {
            orderIndexes: ['+1', '+2', '+3', '+4', '-1'],
            weekdays: ['SU', 'MO', 'TU', 'WE', 'TH', 'FR', 'SA'],
            orderedWeekdays: orderedWeekdays
        });

        // The recurrence type dropdown should show certain fields depending
        // on selection:
        function displayFields(selector) {
            var i;
            // First hide all the fields
            form.find('.rifield').hide();
            // Then show the ones that should be shown.
            var value = selector.val();
            if (value) {
                var rtemplate = conf.rtemplate[value];
                for (i = 0; i < rtemplate.fields.length; i++) {
                    form.find('#' + rtemplate.fields[i]).show();
                }
            }
        }

        function occurrenceExclude(event) {
            event.preventDefault();
            if (form.ical.EXDATE === undefined) {
                form.ical.EXDATE = [];
            }
            form.ical.EXDATE.push(this.attributes.date.value);
            var $this = $(this);
            $this.removeClass('rrule').addClass('exdate');
            $this.parent().parent().addClass('exdate');
            $(this).find('i').removeClass('fa-trash').addClass('fa-trash-restore');
            $this.unbind(event);
            $this.click(occurrenceInclude); // Jslint warns here, but that's OK.
        }

        function occurrenceInclude(event) {
            event.preventDefault();
            form.ical.EXDATE.splice($.inArray(this.attributes.date.value, form.ical.EXDATE), 1);
            var $this = $(this);
            $this.removeClass('exdate').addClass('rrule');
            $this.parent().parent().removeClass('exdate');
            $(this).find('i').removeClass('fa-trash-restore').addClass('fa-trash');
            $this.unbind(event);
            $this.click(occurrenceExclude);
        }

        function occurrenceDelete(event) {
            event.preventDefault();
            form.ical.RDATE.splice($.inArray(this.attributes.date.value, form.ical.RDATE), 1);
            $(this).parent().parent().hide('slow', function () {
                $(this).remove();
            });
        }

        function occurrenceAdd(event) {
            event.preventDefault();
            var dateinput = form
                .find('.riaddoccurrence input#adddate');
            var datevalue = $.datepicker.formatDate("yymmdd", dateinput.data('picker').datepicker("getDate")) + 'T000000';
            if (form.ical.RDATE === undefined) {
                form.ical.RDATE = [];
            }
            var errorarea = form.find('.riaddoccurrence div.errorarea');
            errorarea.text('');
            errorarea.hide();

            // Add date only if it is not already in RDATE
            if ($.inArray(datevalue, form.ical.RDATE) === -1) {
                form.ical.RDATE.push(datevalue);
                var html = ['<div class="occurrence rdate list-group-item d-flex justify-content-between align-items-center p-1" style="display: none;">',
                        '<span class="rdate">',
                            $.datepicker.formatDate("D, dd.mm.yy", dateinput.data('picker').datepicker("getDate")),
                            '<span class="rlabel">' + conf.i18n.additionalDate + '</span>',
                        '</span>',
                        '<span class="action">',
                            '<a date="' + datevalue + '" href="#" class="rdate btn btn-outline-secondary btn-sm" >',
                                '<i class="fa fa-trash"></i>',
                            '</a>',
                        '</span>',
                        '</div>'].join('\n');
                form.find('div.rioccurrences').prepend(html);
                $(form.find('div.rioccurrences div')[0]).slideDown();
                $(form.find('div.rioccurrences .action a.rdate')[0]).click(occurrenceDelete);
            } else {
                errorarea.text(conf.i18n.alreadyAdded).show();
            }
        }

        // element is where to find the tag in question. Can be the form
        // or the display widget. Defaults to the form.
        function loadOccurrences(startdate, rfc5545, start, readonly) {
            var element, occurrenceDiv;

            if (!readonly) {
                element = form;
            } else {
                element = display;
            }

            occurrenceDiv = element.find('.rioccurrences');
            occurrenceDiv.hide();

            var year, month, day;
            year = startdate.getFullYear();
            month = startdate.getMonth() + 1;
            day = startdate.getDate();

            var data = {year: year,
                       month: month, // Sending January as 0? I think not.
                       day: day,
                       rrule: rfc5545,
                       format: conf.i18n.longDateFormat,
                       start: start};

            var dict = {
                url: conf.ajaxURL,
                async: true, // Can't be tested if it's asynchronous, annoyingly.
                type: 'post',
                dataType: 'json',
                contentType: conf.ajaxContentType,
                cache: false,
                data: JSON.stringify(data, null, '\t'),
                success: function (data, status, jqXHR) {
                    var result, element;

                    if (!readonly) {
                        element = form;
                    } else {
                        element = display;
                    }
                    data.readOnly = readonly;
                    data.i18n = conf.i18n;

                    // Format dates:
                    var occurrence, date, y, m, d, each;
                    for (each in data.occurrences) {
                        if (data.occurrences.hasOwnProperty(each)) {
                            occurrence = data.occurrences[each];
                            date = occurrence.date;
                            y = parseInt(date.substring(0, 4), 10);
                            m = parseInt(date.substring(4, 6), 10) - 1; // jan=0
                            d = parseInt(date.substring(6, 8), 10);
                            occurrence.formattedDate = format(new Date(y, m, d), conf.i18n.longDateFormat, conf);
                        }
                    }

                    result = $.templates.occurrenceTmpl(data);
                    occurrenceDiv = element.find('.rioccurrences');
                    occurrenceDiv.replaceWith(result);

                    // Add the batch actions:
                    element.find('.rioccurrences .batching a').click(
                        function (event) {
                            event.preventDefault();
                            loadOccurrences(startdate, rfc5545, this.attributes.start.value, readonly);
                        }
                    );

                    // Add the delete/undelete actions:
                    if (!readonly) {
                        element.find('.rioccurrences .action a.rrule').click(occurrenceExclude);
                        element.find('.rioccurrences .action a.exdate').click(occurrenceInclude);
                        element.find('.rioccurrences .action a.rdate').click(occurrenceDelete);
                    }
                    // Show the new div
                    element.find('.rioccurrences').show();
                },
                error: function (jqXHR, textStatus, errorThrown) {
                    alert(textStatus);
                }
            };

            $.ajax(dict);
        }

        function getField(field) {
            var realField = null;

            if (field instanceof Element) {
                // See if it is a field already
                realField = $(field);
            }

            if (realField == null || !realField.length) {
                // Otherwise, we assume it's an id:
                realField = $('#' + field);
            }

            if (realField == null || !realField.length) {
                // Still not? Then it's a name.
                realField = $("input[name='" + field + "']");
            }
            return realField;
        }
        function findStartDate() {
            var startdate = null;
            var startField, startFieldYear, startFieldMonth, startFieldDay;

            var startField = 'recc-start'; // conf.startField;

            // Find the default byday and bymonthday from the start date, if any:
            if (startField) {
                startField = getField(startField);
                if (!startField.length) {
                    // Field not found
                    return null;
                }
                // Now we have a field, see if it is a dateinput field:
                startdate = startField.data('dateinput');
                if (!startdate) {
                    //No, it wasn't, just try to interpret it with Date()
                    startdate = startField.val();
                    if (startdate === "") {
                        // Probably not an input at all. Try to see if it contains a date
                        startdate = startField.text();
                    }
                } else {
                    // Yes it was, get the date:
                    startdate = startdate.getValue();
                }

                if (typeof startdate === 'string') {
                    // convert human readable, non ISO8601 dates, like
                    // '2014-04-24 19:00', where the 'T' separator is missing.
                    startdate = startdate.replace(' ', 'T');
                }

                startdate = new Date(startdate);
            } else if (conf.startFieldYear &&
                       conf.startFieldMonth &&
                       conf.startFieldDay) {
                startFieldYear = getField(conf.startFieldYear);
                startFieldMonth = getField(conf.startFieldMonth);
                startFieldDay = getField(conf.startFieldDay);
                if (!startFieldYear.length &&
                    !startFieldMonth.length &&
                    !startFieldDay.length) {
                    // Field not found
                    return null;
                }
                startdate = new Date(startFieldYear.val(),
                                     startFieldMonth.val() - 1,
                                     startFieldDay.val());
            }
            if (startdate === null) {
                return null;
            }
            // We have some sort of startdate:
            if (isNaN(startdate)) {
                return null;
            }
            return startdate;
        }
        function findEndDate(form) {
            var endField, enddate;

            endField = form.find('input[name=rirangebyenddatecalendar]');

            // Now we have a field, see if it is a dateinput field:
            enddate = endField.data('dateinput');
            if (!enddate) {
                //No, it wasn't, just try to interpret it with Date()
                enddate = endField.val();
            } else {
                // Yes it was, get the date:
                enddate = enddate.getValue();
            }
            enddate = new Date(enddate);

            // if the end date is incorrect or the field is left empty
            if (isNaN(enddate) || endField.val() === "") {
                return null;
            }
            return enddate;
        }
        function findIntField(fieldName, form) {
            var field, num, isInt;

            field = form.find('input[name=' + fieldName + ']');

            num = field.val();

            // if it's not a number or the field is left empty
            if (isNaN(num) || (num.toString().indexOf('.') !== -1) || field.val() === "") {
                return null;
            }
            return num;
        }

        // Loading (populating) display and form widget with
        // passed RFC5545 string (data)
        function loadData(rfc5545) {
            var selector, format, startdate, dayindex, day;

            if (rfc5545) {
                widgetLoadFromRfc5545(form, conf, rfc5545, true);
            }

            startdate = findStartDate();

            if (startdate !== null) {
                // If the date is a real date, set the defaults in the form
                form.find('select[name=rimonthlydayofmonthday]').val(startdate.getDate());
                dayindex = conf.orderIndexes[Math.floor((startdate.getDate() - 1) / 7)];
                day = conf.weekdays[startdate.getDay()];
                form.find('select[name=rimonthlyweekdayofmonthindex]').val(dayindex);
                form.find('select[name=rimonthlyweekdayofmonth]').val(day);

                form.find('select[name=riyearlydayofmonthmonth]').val(startdate.getMonth() + 1);
                form.find('select[name=riyearlydayofmonthday]').val(startdate.getDate());
                form.find('select[name=riyearlyweekdayofmonthindex]').val(dayindex);
                form.find('select[name=riyearlyweekdayofmonthday]').val(day);
                form.find('select[name=riyearlyweekdayofmonthmonth]').val(startdate.getMonth() + 1);

                // Now when we have a start date, we can also do an ajax call to calculate occurrences:
                loadOccurrences(startdate, widgetSaveToRfc5545(form, conf, false).result, 0, false);

                // Show the add and refresh buttons:
                form.find('div.rioccurrencesactions').show();

            } else {
                // No EXDATE/RDATE support
                form.find('div.rioccurrencesactions').hide();
            }


            selector = form.find('select[name=rirtemplate]');
            displayFields(selector);
        }

        function displayOn() {
            display.find('div[class=ridisplay-start]').text($('#' + conf.prefix + 'start-user').val());

            if ($('#' + conf.prefix + 'allday').is(':checked')) {
                display.find('div[class=ridisplay-times]').text(conf.i18n.reccAllDay);
            } else {
                var times = $('#' + conf.prefix + 'start-time').val();
                var end_time = $('#' + conf.prefix + 'end-time').val();
                if (end_time) {
                    times += ' - ' + end_time
                }
                display.find('div[class=ridisplay-times]').text(times);
            }

            $('#' + conf.prefix + 'single-event-container').hide();
            $('#' + conf.prefix + 'recc-event-container').show();
        }

        function recurrenceOn() {
            var RFC5545 = widgetSaveToRfc5545(form, conf, false);
            var label = display.find('div[class=ridisplay]');
            label.text(conf.i18n.displayActivate + ' ' + RFC5545.description);
            textarea.val(RFC5545.result).change();
            // var startdate = findStartDate();
            // if (startdate !== null) {
            //     loadOccurrences(startdate, widgetSaveToRfc5545(form, conf, false).result, 0, true);
            // }
            display.find('button[name="riedit"]').text(conf.i18n.edit_rules);
            display.find('button[name="ridelete"]').show();

            displayOn();
        }

        function displayOff() {
            $('#' + conf.prefix + 'single-event-container').show();
            $('#' + conf.prefix + 'recc-event-container').hide();
        }

        function recurrenceOff() {
            var label = display.find('div[class=ridisplay]');
            label.text(conf.i18n.displayUnactivate);
            textarea.val('').change();  // Clear the textarea.
            display.find('.rioccurrences').hide();
            display.find('button[name="riedit"]').text(conf.i18n.add_rules);
            display.find('button[name="ridelete"]').hide();

            set_picker_date($('#' + conf.prefix + 'end-user'), null);
            hideLink(null, $("#" + conf.prefix + "end-hide-container a.hide-link"));

            displayOff();
        }

        function checkFields(form) {
            var startDate, endDate, num, messagearea;
            startDate = findStartDate();

            // Hide any error message from before
            messagearea = form.find('#messagearea');
            messagearea.text('');
            messagearea.hide();

            // Hide add field errors
            form.find('.riaddoccurrence div.errorarea').text('').hide();

            // Repeats Daily
            if (form.find('#ridailyinterval').css('display') === 'block') {
                // Check repeat every field
                num = findIntField('ridailyinterval', form);
                if (!num || num < 1 || num > 1000) {
                    messagearea.text(conf.i18n.noRepeatEvery).show();
                    return false;
                }
            }

            // Repeats Weekly
            if (form.find('#riweeklyinterval').css('display') === 'block') {
                // Check repeat every field
                num = findIntField('riweeklyinterval', form);
                if (!num || num < 1 || num > 1000) {
                    messagearea.text(conf.i18n.noRepeatEvery).show();
                    return false;
                }
            }

            // Repeats Monthly
            if (form.find('#rimonthlyinterval').css('display') === 'block') {
                // Check repeat every field
                num = findIntField('rimonthlyinterval', form);
                if (!num || num < 1 || num > 1000) {
                    messagearea.text(conf.i18n.noRepeatEvery).show();
                    return false;
                }

                // Check repeat on
                if (form.find('#rimonthlyoptions input:checked').length === 0) {
                    messagearea.text(conf.i18n.noRepeatOn).show();
                    return false;
                }
            }

            // Repeats Yearly
            if (form.find('#riyearlyinterval').css('display') === 'block') {
                // Check repeat every field
                num = findIntField('riyearlyinterval', form);
                if (!num || num < 1 || num > 1000) {
                    messagearea.text(conf.i18n.noRepeatEvery).show();
                    return false;
                }

                // Check repeat on
                if (form.find('#riyearlyoptions input:checked').length === 0) {
                    messagearea.text(conf.i18n.noRepeatOn).show();
                    return false;
                }
            }

            // End recurrence fields

            // If after N occurences is selected, check its value
            if (form.find('input[value="BYOCCURRENCES"]:visible:checked').length > 0) {
                num = findIntField('rirangebyoccurrencesvalue', form);
                if (!num || num < 1 || num > 1000) {
                    messagearea.text(conf.i18n.noEndAfterNOccurrences).show();
                    return false;
                }
            }

            // If end date is selected, check its value
            if (form.find('input[value="BYENDDATE"]:visible:checked').length > 0) {
                endDate = findEndDate(form);
                if (!endDate) {
                    // if endDate is null that means the field is empty
                    messagearea.text(conf.i18n.noEndDate).show();
                    return false;
                } else if (endDate < startDate) {
                    // the end date cannot be before start date
                    messagearea.text(conf.i18n.pastEndDate).show();
                    return false;
                }
            }

            return true;
        }

        function save(event) {
            event.preventDefault();
            // if no field errors, process the request
            if (checkFields(form)) {

                var start_moment = get_moment_with_time_from_fields(form.find('input[name=recc-start]'), form.find('input[name=recc-start-time]'));
                set_picker_date($('#' + conf.prefix + 'start-user'), start_moment.toDate());

                var end_time = form.find('input[name=recc-fo-end-time]').timepicker("getTime");
                var end_datetime = null;
                if (end_time != null) {
                    var end_moment = moment(start_moment).set({hour: end_time.getHours(), minute: end_time.getMinutes()});

                    if (end_moment < start_moment) {
                        end_moment = end_moment.add(1, 'days');
                    }

                    end_datetime = end_moment.toDate()
                }

                set_picker_date($('#' + conf.prefix + 'end-user'), end_datetime);

                $('#' + conf.prefix + 'allday').prop('checked', form.find('input[name=recc-allday]').is(':checked'));

                recurrenceOn();

                // close overlay
                dialog.modal('hide');
                //form.overlay().close();
            }
        }

        function cancel(event) {
            event.preventDefault();
            // close overlay
            dialog.modal('hide');
            //form.overlay().close();
        }

        function updateOccurances() {
            var startDate;
            startDate = findStartDate();

            // if no field errors, process the request
            if (checkFields(form)) {
                loadOccurrences(startDate,
                    widgetSaveToRfc5545(form, conf, false).result,
                    0,
                    false);
            }
        }

        /*
          Load the templates
        */

        display = $($.templates.displayTmpl(conf));
        form = $($.templates.formTmpl(conf));

        // Make an overlay and hide it
        dialog = form;
        //form.overlay(conf.formOverlay).hide();
        form.ical = {RDATE: [], EXDATE: []};

        // $.tools.dateinput.localize(conf.lang,  {
        //     months:      LABELS[conf.lang].months.join(),
        //     shortMonths: LABELS[conf.lang].shortMonths.join(),
        //     days:        LABELS[conf.lang].weekdays.join(),
        //     shortDays:   LABELS[conf.lang].shortWeekdays.join()
        // });

        // Make the date input into a calendar dateinput()
        start_datepicker(form.find('input[name=recc-start]'));

        var rirangebyenddatecalendar_input = form.find('input[name=rirangebyenddatecalendar]');
        start_datepicker(rirangebyenddatecalendar_input).datepicker("setDate", moment().toDate());

        start_timepicker(form.find('input[name=recc-start-time]'));
        start_timepicker(form.find('input[name=recc-fo-end-time]'));

        if (textarea.val()) {
            var result = widgetLoadFromRfc5545(form, conf, textarea.val(), false);
            if (result === -1) {
                var label = display.find('div[class=ridisplay]');
                label.text(conf.i18n.noRule);
                displayOff();
            } else {
                recurrenceOn();
            }
        } else {
            displayOff();
        }

        /*
          Do all the GUI stuff:
        */

        // When you click "Delete...", the recurrence rules should be cleared.
        display.find('button[name=ridelete]').click(function (e) {
            e.preventDefault();
            recurrenceOff();
        });

        // Show form overlay when you click on the "Edit..." link
        display.find('button[name=riedit]').click(
            function (e) {
                // Load the form to set up the right fields to show, etc.
                loadData(textarea.val());

                e.preventDefault();
                dialog.modal();
                //form.overlay().load();
            }
        );

        dialog.on('shown.bs.modal', function (e) {
            var recc_start_time = form.find('input[name=recc-start-time]');
            var recc_fo_end_time = form.find('input[name=recc-fo-end-time]');

            recc_start_time.change(function() {
                recc_fo_end_time.timepicker('option', 'minTime', $(this).timepicker("getTime"));
            });

            form.find('input[id=recc-start-user]').datepicker("setDate", $('#' + conf.prefix + 'start-user').datepicker("getDate"));
            recc_start_time.timepicker('setTime', $('#' + conf.prefix + 'start-time').timepicker("getTime"));
            recc_start_time.change();
            recc_fo_end_time.timepicker('setTime', $('#' + conf.prefix + 'end-time').timepicker("getTime"));

            var recc_allday = form.find('input[name=recc-allday]');
            recc_allday.prop('checked', $('#' + conf.prefix + 'allday').is(':checked'));
            var allday_checked = recc_allday.is(':checked');
            var recc_start_time_group = form.find("#recc-start-time-group");
            var recc_fo_end_time_group = form.find('#recc-fo-end-time-group');
            recc_start_time_group.toggle(!allday_checked);
            recc_fo_end_time_group.toggle(!allday_checked);

            recc_allday.on('change', function() {
                recc_start_time_group.toggle(!this.checked);
                recc_fo_end_time_group.toggle(!this.checked);

                onAlldayChecked(this, "recc-start");

                var end_moment = get_moment_with_time_from_fields(form.find('input[name=recc-start]'), form.find('input[name=recc-start-time]'));
                if (this.checked) {
                    end_moment = end_moment.endOf('day');
                } else {
                    end_moment = end_moment.add(3, 'hours');
                }
                recc_fo_end_time.timepicker('setTime', end_moment.toDate());
            });

            form.find('#occurences-show-container .show-link').click(function(e){
                showLink(e, this);
            });

            form.find('#occurences-hide-container .hide-link').click(function(e){
                hideLink(e, this);
            });

            // Load the form to set up the right fields to show, etc.
            loadData(textarea.val());
        });

        // Pop up the little add form when clicking "Add"
        var riaddoccurrence_input = form.find('div.riaddoccurrence input#adddate');
        start_datepicker(riaddoccurrence_input).datepicker("setDate", moment().toDate());
        form.find('input#addoccurencebtn').click(occurrenceAdd);

        // When the reload button is clicked, reload
        form.find('a.rirefreshbutton').click(
            function (event) {
                event.preventDefault();
                updateOccurances();
            }
        );

        // When selecting template, update what fieldsets are visible.
        form.find('select[name=rirtemplate]').change(
            function (e) {
                displayFields($(this));
            }
        );

        // When focus goes to a drop-down, select the relevant radiobutton.
        form.find('select').change(
            function (e) {
                $(this).parent().find('> input').click().change();
            }
        );
        form.find('input[name=rirangebyoccurrencesvalue]').change(
            function (e) {
                $(this).parent().find('input[name=rirangetype]').click().change();
            }
        );
        form.find('input[name=rirangebyenddatecalendar]').change(function () {
            // Update only if the occurances are shown
            $(this).parent().find('input[name=rirangetype]').click();
            if (form.find('.rioccurrencesactions:visible').length !== 0) {
                updateOccurances();
            }
        });
        // Update the selected dates section
        form.find('input:radio, .riweeklyweekday > input, input[name=ridailyinterval], input[name=riweeklyinterval], input[name=rimonthlyinterval], input[name=riyearlyinterval], input[name=recc-start]').change(
            function (e) {
                // Update only if the occurances are shown
                if (form.find('.rioccurrencesactions:visible').length !== 0) {
                    updateOccurances();
                }
            }
        );

        /*
          Save and cancel methods:
        */
        form.find('.ricancelbutton').click(cancel);
        form.find('.risavebutton').click(save);

        $('#' + conf.prefix + 'recc-button').click(function() {
            $('button[name=riedit]').click();
        });

        /*
         * Public API of RecurrenceInput
         */

        $.extend(self, {
            display: display,
            form: form,
            loadData: loadData, //Used by tests.
            save: save //Used by tests.
        });

    }


    /*
     * jQuery plugin implementation
     */
    $.fn.recurrenceinput = function (conf) {
        if (this.data('recurrenceinput')) {
            // plugin already installed
            return this.data('recurrenceinput');
        }

        // "compile" configuration for widget
        var config = $.extend({}, tool.conf);
        $.extend(config, conf);
        $.extend(config, {i18n: LABELS[config.lang], name: this.attr('name')});

        // our recurrenceinput widget instance
        var recurrenceinput = new RecurrenceInput(config, this);
        // hide textarea and place display widget after textarea
        //recurrenceinput.form.appendTo('body');
        this.after(recurrenceinput.display);

        // hide the textarea
        this.hide();

        // save the data for next call
        this.data('recurrenceinput', recurrenceinput);
        return recurrenceinput;
    };

}(jQuery));

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
    reccAllDay: "Ganztägig",
  });