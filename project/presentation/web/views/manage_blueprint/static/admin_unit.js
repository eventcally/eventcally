$(function () {
  function suggest_short_name() {
    if ($("#short_name").val().length == 0) {
      var name = $("#name")
        .val()
        .toLowerCase()
        .replace(/ä/g, "ae")
        .replace(/ö/g, "oe")
        .replace(/ü/g, "ue")
        .replace(/ß/g, "ss");
      var re = /\w/g;
      var suggestion = (name.match(re) || []).join("");

      $("#short_name").val(suggestion);
      $("#short_name").valid();
    }
  }

  $("#name").blur(function () {
    suggest_short_name();
  });

  if ($("#name").val().length > 0) {
    $("#name").valid();
    suggest_short_name();
  }
});
