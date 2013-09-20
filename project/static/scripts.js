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
    $("select#id_cluster").change( function () {
        var val = $(this).val();
        $.get("/chem/template/"+val, function (data) {
            $("textarea#id_template").val(data);
        });
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