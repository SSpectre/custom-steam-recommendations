/** General, all-purpose error message. */
function errorMessage() {
    alert("Something went wrong. Please try logging in again or try again later.");
}

/** Sends an HTTP request to the server to update a game's rating in the database.
 * @param {number} gameID - The game's Steam app ID.
 * @param {string} rating - User's rating, either a number or "exclude".
 */
function assignRating(gameID, rating) {
    var data = {
        id: gameID,
        rating: rating
    };

    $.ajax({
        type: "POST",
        url: $('body').data('assignrating'),
        data: JSON.stringify(data),
        contentType: "application/json",
        dataType: 'json',
        error: function() {
            errorMessage();
        }
    });
}

/** Sends an HTTP request to the server to change the number of recommendations. Redraws the list if successful.
 * @param {string} size - The new number of recommendations.
 */
function changeListSize(size) {
    //have all instances of the recommendation number dropdown reflect the new size
    $(".rec-number").val(size);

    //prevent list resize while calculation in progress
    if (calculatingRecs()) {
        return;
    }

    var data = {
        size: size
    };

    $.ajax({
        type: "POST",
        url: $('body').data('changelistsize'),
        data: JSON.stringify(data),
        contentType: "application/json",
        dataType: 'json',
        success: function(response) {
            let oldSize = JSON.parse(response["old_size"]);
            $(".rec-button").attr("onclick", "recommendGames('" + size + "')");

            //redraw recommendation list, keeping existing recommendations
            let innerHTML = "";
            for (let i = 0; i < size; i++) {
                let index = i + 1;
                let id = "rec" + index;
                let existingValue = $("#" + id).html();

                let row =
                `<tr>
                    <td>` + index +`.</td>
                    <td id="` + id + `">` + existingValue + `</td>
                </tr>`;
                innerHTML = innerHTML + row;
            }

            $("#rec-body").html(innerHTML);

            //don't need to recalculate recommendations if the list is smaller
            if (oldSize < size) {
                recommendGames(size);
            }

            //tell parent container to resize the iframe. Needs to be placed here in case the list is smaller and recommendGames() isn't called
            loadComplete();
        },
        error: function() {
            errorMessage();
        }
    });
}

/** Sends an HTTP request to the server to calculate recommended games. Draws the list if successful.
 * @param {number} list_size - Number of games to recommend.
 */
function recommendGames(list_size) {
    //prevent recommendations while calculation in progress
    if (calculatingRecs()) {
        return;
    }

    //scrolls to top of page, since that's where recommendations appear.
    parent.window.scrollTo(0,0);

    //loading animation
    for (let i = 0; i < list_size; i++) {
        $("#rec" + (i+1)).html(`Calculating<span class="ellipsis"></span>`);
    }

    var innerHTML = "";
    var eInterval = setInterval(function() {
        if (innerHTML.length > 3)
            innerHTML = "";
        else
            innerHTML += ".";

        $(".ellipsis").html(innerHTML);
    }, 333);

    if ($('.column-switch-button').data('showinglibrary')) {
        switchColumns();
    }
    
    $.ajax({
        type: "GET",
        url: $('body').data('recommendgames'),
        contentType: "application/json",
        dataType: 'json',
        success: function(response) {
            for (let i = 0; i < list_size; i++) {
                console.log(response);
                let game = JSON.parse(response[i]);

                let url = game.store_url;
                let logo = game.game_logo_url;
                let name = game.game_name;

                //add onload event to last image in the list to notify parent container to resize iframe
                let finalLoad = i == list_size - 1 ? ` onload='loadComplete()'` : ``;

                //draw recommendation
                let innerHTML =
                `<a href="#" onclick='window.open("${url}");return false;'>
                    <figure>
                        <img src=${logo} alt="${name}"` + finalLoad + `>
                        <figcaption>
                            ${name}
                        </figcaption>
                    </figure>
                </a>`;
                $("#rec" + (i+1)).html(innerHTML);

                //stop loading animation
                clearInterval(eInterval);
            }
        },
        error: function(xhr) {
            let message = JSON.parse(xhr.responseText)["error_message"];

            //message only exists if the user has no games/ratings
            if (message) {
                alert(message);
            }
            else {
                errorMessage();
            }

            //clear loading animation
            for (let i = 0; i < list_size; i++) {
                $("#rec" + (i+1)).html("");
            }
        },
    });
}

/** Sends an HTTP request to the server to set all of the user's ratings to null. Set dropdown values to N/A if successful. */
function clearRatings() {
    if (confirm("Are you sure you want to clear all of your ratings?")) {
        $.ajax({
            type: "GET",
            url: $('body').data('clearratings'),
            success: function() {
                let i = 0;
                while (true) {
                    id = "#rating" + i;
                    rating = $(id);

                    if (rating.length) {
                        if (rating.val() != "exclude"){
                            rating.val("exclude");
                        }
                    }
                    else {
                        //reached the end of user's library
                        break;
                    }
                    i++;
                }
            },
            error: function() {
                errorMessage();
            },
        });
    }
}

/** Sends an HTTP request to the server to delete the user's data. Logs out if successful. */
function deleteUser() {
    if (confirm("Are you sure you want to delete your user data?")) {
        $.ajax({
            type: "GET",
            url: $('body').data('deleteuser'),
            success: function() {
                window.location = $('body').data('logout');
            },
            error: function() {
                errorMessage();
            },
        });
    }
}

/** Logs out the user */
function logout() {
    if (confirm("Are you sure you want to log out?")) {
        window.location = $('body').data('logout');
    }
}

/** Switches whether the library or recommendation column is visible when the window is too thin to display both */
function switchColumns() {
    //showingLibrary needs to be a string so it can be stored as an HTML data attribute
    let button = $('.column-switch-button');
    let showingLibrary = button.data('showinglibrary');

    if (showingLibrary) {
        button.html("<<");
        button.data('showinglibrary', "")

        $('#library-column').css('display', 'none');
        $('#rec-column').css('display', 'inline-block');
    }
    else {
        button.html(">>");
        button.data('showinglibrary', "true")

        $('#library-column').css('display', 'inline-block');
        $('#rec-column').css('display', 'none');
    }

    //resize iframe if the visible column is larger
    loadComplete();
}

/** Function for checking if recommendation calculation is currently in progress. Returns a boolean and causes an alert asking the user to wait if true */
function calculatingRecs() {
    let calculatingRegex = new RegExp("^Calculating");
    if (calculatingRegex.test($("#rec1").html())) {
        alert("Please wait while recommendations are being calculated.")
        return true;
    }

    return false;
}

/** Tells the parent container to resize the containing iframe. To be called when all elements are loaded. */
function loadComplete() {
    //add a delay because otherwise the resize occurs before everything is in place
    setTimeout(function() {
        parent.postMessage({
            type: "resizeFrame"
        });
    }, 100)
    
}