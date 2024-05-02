function confirmLogin() {
    $.ajax({
        type: "GET",
        url: "{{url_for('confirm_login')}}",
        success: function(response) {
            //confirm_login returns empty json if error was encountered
            if (response.length > 0) {
                $("#login_button").hide();
                $("#center-content").empty();
                $("#center-content").append(`<h1>Loading<span id="ellipsis"></span></h1>`);
                $("#center-content").append(`<h2>(This might take a minute if it's your first time or you have a large Steam library)</h2>`);

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

                window.location = "{{url_for('get_user_id')}}";
            }
        },
    });
}