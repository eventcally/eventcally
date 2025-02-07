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

$(function () {
  $("select[data-role=select2-ajax]").each(function () {
    var $el = $(this);
    processSelect2Ajax($el);
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
});
