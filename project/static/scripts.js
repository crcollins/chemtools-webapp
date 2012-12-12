$(document).ready(function() {
    if ($("ul.errorlist").length == 0) {
        $(".hide").hide();
    }
    $(".hide-title").click(function() {
        $(this).next(".hide").slideToggle("fast");
    });

    $("body").on({
        // When ajaxStart is fired, add 'loading' to body class
        ajaxStart: function() {
            $(this).addClass("loading");
        },
        // When ajaxStop is fired, rmeove 'loading' from body class
        ajaxStop: function() {
            $(this).removeClass("loading");
        }
    });
});