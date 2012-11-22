$(document).ready(function() {
    $(".hide").hide()
    $(".hide-title").click(function() {
        $(this).next(".hide").slideToggle("fast");
    });
});


