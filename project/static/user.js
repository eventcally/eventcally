$(function () {
    $('.toggle-user-event-favorite').click(function (e) {
        var button = $(this);
        var event_id = button.data("event-id");
        var icon = button.find("i");
        var is_favored = icon.hasClass("fa");

        if (is_favored) {
            $.ajax({
                url: "/api/v1/user/favorite-events/" + event_id,
                type: "delete",
                success: function () {
                    icon.removeClass("fa").addClass("far");
                }
            });
        } else {
            $.ajax({
                url: "/api/v1/user/favorite-events/" + event_id,
                type: "put",
                success: function () {
                    icon.removeClass("far").addClass("fa");
                }
            });
        }
    });
});