$(function () {
  $('[data-toggle="tooltip"]').tooltip();

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
