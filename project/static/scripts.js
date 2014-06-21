$(document).ready(function() {
    if ($("ul.errorlist").length == 0) {
        $(".hide").hide();
    }
    $(".hide-title").click(function() {
        $(this).next(".hide").slideToggle("fast");
    });

    $("body").on({
        ajaxStart: function() {
            $(".ajax-modal").fadeIn("slow");
        },
        ajaxStop: function() {
            $(".ajax-modal").hide();
        }
    });
    $("select#id_base_template").change( function () {
        var val = $(this).val();
        if (val) {
            $.get("/media/"+val, function (data) {
                $("textarea#id_template").val(data);
            });
        }
    });
    $("#id_custom_template").change( function () {
        $("textarea#id_template").attr('disabled', !this.checked);
    });
});

String.prototype.format = function () {
  var args = arguments;
  return this.replace(/\{\{|\}\}|\{(\d+)\}/g, function (m, n) {
    if (m == "{{") { return "{"; }
    if (m == "}}") { return "}"; }
    return args[n];
  });
};