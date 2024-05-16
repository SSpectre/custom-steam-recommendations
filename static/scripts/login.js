function confirmLogin() {
    $.ajax({
        type: "GET",
        url: $('body').data('confirmlogin'),
        success: function(response) {
            //confirm_login returns empty json if error was encountered
            if (response.length > 0) {
                $("#login_button").hide();
                $("#center-content").empty();
                $("#center-content").append(`<h2>Loading<span id="ellipsis"></span></h2>`);
                $("#center-content").append(`<h3>(This might take a minute if it's your first time or you have a large Steam library)</h3>`);

                parent.postMessage({
                    type: "resizeFrame"
                });

                var innerHTML = "";
                var eInterval = setInterval(function() {
                    if (innerHTML.length > 3)
                        innerHTML = "";
                    else
                        innerHTML += ".";

                    $("#ellipsis").html(innerHTML);
                }, 333);

                window.location = $('body').data('getuserid');
            }
        },
    });
}