$(function () {
  $('[data-toggle="tooltip"]').tooltip();

  $(document).on('select2:open', function(e) {
    document.querySelector(`[aria-controls="select2-${e.target.id}-results"]`).focus();
  });
});
