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

    function post_func() {
        event.preventDefault();
        var a = $('#id_job_form').serialize();
        a += "&html=true";
        $.post('', a, function(data) {
            if (data.success) {
                var dialog = $("#resultsModal .modal-body");
                dialog.html(data.html);
                $('#resultsModal').modal();
            } else {
                $("#id_form_input").html(data.form_html);
                var temp = $("div.has-error").get(0);
                if (temp !== undefined) {
                    temp.scrollIntoView();
                }
            }
        });
    }
    $("#id_post").click(post_func);
});

String.prototype.format = function () {
  var args = arguments;
  return this.replace(/\{\{|\}\}|\{(\d+)\}/g, function (m, n) {
    if (m == "{{") { return "{"; }
    if (m == "}}") { return "}"; }
    return args[n];
  });
};