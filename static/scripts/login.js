/** Sends an HTTP request to the server to confirm if the user logged in with Steam. Draws loading message and begins constructing the user's library if successful. */
function confirmLogin() {
    $.ajax({
        type: "GET",
        url: $('body').data('confirmlogin'),
        success: function(response) {
            try {
                json = JSON.parse(response);
            }
            catch {
                return;
            }
            
            if (json["user_id"]) {
                //draw loading message
                $("#login-button").hide();
                $("#center-content").empty();
                $("#center-content").append(`<h2>Loading<span id="ellipsis"></span></h2>`);
                $("#center-content").append(`<h3>(This might take a minute if it's your first time or you have a large Steam library)</h3>`);

                //notify parent container to resize iframe for loading message
                parent.postMessage({
                    type: "resizeFrame"
                });

                //loading animation
                let innerHTML = "";
                let eInterval = setInterval(function() {
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