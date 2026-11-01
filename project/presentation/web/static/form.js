$.fn.select2.defaults.set("language", "de");

(function() {
  var CustomFormModule = function() {

    function processSelect2Tags($el) {
      $el.select2({
        width: '100%',
        theme: 'bootstrap4',
        tags: true,
        tokenSeparators: [',', ' '],
        language: {
            noResults: function () {
                  return "";
            }
        }
      });
    }

    function processFormValidation($form) {
      $form.validate({rules: {}});
    }

    this.init = function() {
      $("select[data-role=select2-tags]").each(function () {
        var $el = $(this);
        processSelect2Tags($el);
      });

      $("form[data-role=validation-form]").each(function () {
        var $el = $(this);
        processFormValidation($el);
      });

      $(".autocomplete").select2({
        width: "100%",
        theme: "bootstrap4",
      });

      $(".autocomplete-multi").select2({
        width: "100%",
      });
    }
  };

  var customFormModule = new CustomFormModule();

  $(function () {
    customFormModule.init();
  });

})();