$.datepicker.setDefaults($.datepicker.regional["de"]);
$.fn.select2.defaults.set("language", "de");

(function() {
  var CustomFormModule = function() {

    function processGooglePlace($el) {
      var target_prefix = $el.attr("data-target-prefix") || "";
      $el.select2({
        theme: 'bootstrap4',
        ajax: {
          url: $el.attr("data-url"),
          headers: { "X-Backend-For-Frontend": "google_places" },
          dataType: 'json',
          delay: 250,
          cache: true,
          data: function (params) {
            return {
              keyword: params.term
            };
          }
        },
        placeholder: $el.attr("data-placeholder"),
        minimumInputLength: 1,
        templateResult: select2TemplateResult
      }).on('select2:close', function (e) {
        var data = select2GetData(e);

        if ("gmaps_id" in data) {
          $(this).val(null).trigger('change');
          var location_only = $(this).attr("data-location-only");
          if (location_only) {
            reset_location_form(target_prefix);
          } else {
            reset_place_form(target_prefix);
            $('#place-name').val(data.main_text);
            if ($('#place-name').length > 0 && $.isFunction($('#place-name').valid)) {
              $('#place-name').valid();
            }
          }

          get_gmaps_place_details($el.attr("data-url"), target_prefix, data.gmaps_id, location_only);
        }
      });
    }

    function get_gmaps_place_details(url, target_prefix, place_id, location_only) {
      $.ajax({
          url: url,
          headers: { "X-Backend-For-Frontend": "google_place" },
          type: "get",
          dataType: "json",
          data: "gmaps_id=" + place_id,
          success: function (data) {
            fill_place_form_with_gmaps_place(data, target_prefix, location_only);
          }
      });
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

        if ($.isFunction($("#" + prefix + "name").valid)) {
          $("#" + prefix + "name").valid();
        }

        if (place.website) {
          $("#" + prefix + "url").val(place.website);
        }
      }

      $("#" + prefix + "location-street").val([route, street_number].join(" "));
      $("#" + prefix + "location-city").val(city);
      $("#" + prefix + "location-latitude").val(place.geometry.location.lat);
      $("#" + prefix + "location-longitude").val(place.geometry.location.lng);
    }

    function select2GetData(e) {
      var dataArray = $(e.target).select2('data');
      var data = {};

      if (dataArray.length > 0) {
        data = dataArray[0];
      }

      return data;
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

    function processCropperImage($el) {
      var subForm = $el.closest("[data-element=subform]");
      var container = $el.closest("[data-element=cropper-image-container]");
      var photo_modal = container.find("[role=dialog]");
      var photo_preview = container.find("[data-element=photo_preview]");

      var minWidth = $el.attr("data-min-width");
      var minHeight = $el.attr("data-min-height");

      var inputImage = subForm.find("input[type=file]")[0];
      var Cropper = window.Cropper;
      var URL = window.URL || window.webkitURL;
      var image = photo_modal.find("img[data-element=image]")[0];
      var cropper = null;
      var crop_data = null;
      var minCroppedWidth = minWidth;
      var minCroppedHeight = minHeight;
      var uploadedImageURL;

      if (URL) {
        inputImage.onchange = function () {
          $(".dropzone-wrapper").removeClass("dragover");

          var files = this.files;
          var file;

          if (files && files.length) {
            file = files[0];

            if (/^image\/\w+/.test(file.type)) {
              if (uploadedImageURL) {
                URL.revokeObjectURL(uploadedImageURL);
              }

              image.src = uploadedImageURL = URL.createObjectURL(file);
              inputImage.value = null;
              crop_data = null;
              photo_modal.modal();
            } else {
              window.alert("Please choose an image file.");
            }
          }
        };

        photo_modal
          .on("shown.bs.modal", function () {
            cropper = new Cropper(image, {
              viewMode: 1,
              autoCropArea: 1.0,
              data: crop_data,
              ready() {
                var image_data = cropper.getImageData();
                if (
                  image_data.naturalWidth < minCroppedWidth ||
                  image_data.naturalHeight < minCroppedHeight
                ) {
                  window.alert(
                    "Die Auflösung ist zu gering. Mindestens " +
                      minCroppedWidth +
                      "x" +
                      minCroppedHeight +
                      "px."
                  );
                  photo_modal.modal("hide");
                }
              },
              crop: function (event) {
                var width = event.detail.width;
                var height = event.detail.height;

                if (width < minCroppedWidth || height < minCroppedHeight) {
                  cropper.setData({
                    width: Math.max(minCroppedWidth, width),
                    height: Math.max(minCroppedHeight, height),
                  });
                }
              },
            });
          })
          .on("hidden.bs.modal", function () {
            cropper.destroy();
            cropper = null;
          });

        var hide_if_photo_exists = container.find(".hide-if-photo-exists");
        var show_if_photo_exists = container.find(".show-if-photo-exists");
        var copyright_field = subForm.find("input[name$=copyright_text]");

        if (photo_preview.attr("src")) {
          image.src = uploadedImageURL = photo_preview.attr("src");
          hide_if_photo_exists.hide();
          copyright_field.prop("required", true);
        } else {
          show_if_photo_exists.hide();
          copyright_field.prop("required", false);
        }
        container.find("[data-element=photo-edit-btn]").click(function (e) {
          e.preventDefault();
          photo_modal.modal();
        });
        container.find("[data-element=photo-delete-btn]").click(function (e) {
          e.preventDefault();
          $el.val("");
          photo_preview.attr("src", "");
          show_if_photo_exists.hide();
          hide_if_photo_exists.show();
          copyright_field.prop("required", false);
          copyright_field.valid();
        });

        photo_modal.find("[data-element=photo-zoom-in]").click(function (e) {
          e.preventDefault();
          cropper.zoom(0.1);
        });

        photo_modal.find("[data-element=photo-zoom-out]").click(function (e) {
          e.preventDefault();
          cropper.zoom(-0.1);
        });

        photo_modal.find("[data-element=photo-rotate-left]").click(function (e) {
          e.preventDefault();
          cropper.rotate(-90);
        });

        photo_modal.find("[data-element=photo-rotate-right]").click(function (e) {
          e.preventDefault();
          cropper.rotate(90);
        });

        photo_modal.find("[data-element=photo-save-btn]").click(function (e) {
          e.preventDefault();
          photo_modal.modal("hide");

          if (cropper) {
            var canvas = cropper.getCroppedCanvas({
              maxWidth: 1200,
              maxHeight: 1200,
              fillColor: "transparent",
            });
            var data_url = canvas.toDataURL();
            crop_data = cropper.getData();

            $el.val(data_url);
            photo_preview.attr("src", data_url);
            show_if_photo_exists.show();
            hide_if_photo_exists.hide();
            copyright_field.prop("required", true);
            copyright_field.valid();
          }
        });
      } else {
        inputImage.disabled = true;
        inputImage.parentNode.className += " disabled";
      }
    }

    function processFormValidation($form) {
      $form.validate({rules: {}});

      $form.find("input[data-role=ajax-validation]").each(function () {
        var $input = $(this);
        $input.rules("add", {
          remote: {
            url: $input.attr("data-url"),
            headers: { "X-Backend-For-Frontend": "ajax_validation" },
            type: "post",
            async: false,
          }
        });
      });
    }

    function select2TemplateResult(state) {
      if ("is_new_tag" in state) {
          return $("<strong>" + state.tag_text + "</strong>");
        }
        return state.text;
    }

    this.init = function() {
      $("select[data-role=select2-ajax]").each(function () {
        var $el = $(this);
        processSelect2Ajax($el);
      });

      $("select[data-role=google-place]").each(function () {
        var $el = $(this);
        processGooglePlace($el);
      });

      $("form[data-role=validation-form]").each(function () {
        var $el = $(this);
        processFormValidation($el);
      });

      $("input[data-role=cropper-image]").each(function () {
        var $el = $(this);
        processCropperImage($el);
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