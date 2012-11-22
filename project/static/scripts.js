$(document).ready(function() {
    if ($("ul.errorlist").length == 0) {
        $(".hide").hide();
    }
    $(".hide-title").click(function() {
        $(this).next(".hide").slideToggle("fast");
    });
});


