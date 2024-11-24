/** General, all-purpose error message. */
function errorMessage() {
    alert("Something went wrong. Please try logging in again or try again later.");
}

/** Sends an HTTP request to the server to update a game's rating in the database.
 * @param {number} gameID - The game's Steam app ID.
 * @param {string} rating - User's rating, either a number or "exclude".
 */
function assignRating(gameID, rating) {
    let data = {
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

    let data = {
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

/** Sends an HTTP request to the server to update one of the user's content filter preferences in the database.
 * @param {number} filterID - The id of the filter from 1-5, using Steam's internal numbering.
 * @param {boolean} value - Whether or not the content is allowed to be recommended.
 */
function updateFilterPref(filterID, value) {
    $(".filter-check-" + filterID).prop('checked', value);

    let data = {
        filterID: filterID,
        value: value
    };

    $.ajax({
        type: "POST",
        url: $('body').data('updatefilterpref'),
        data: JSON.stringify(data),
        contentType: "application/json",
        dataType: 'json',
        error: function() {
            //revert clicked checkboxes
            $(".filter-check-" + filterID).prop('checked', !value);
            errorMessage();
        }
    });
}

/** Sends an HTTP request to the server to add a non-Steam game to the user's list.
 * @param {number} appID 
 */
function addOtherGame(appID) {
    let data = {
        appID: appID
    };

    $.ajax({
        type: "POST",
        url: $('body').data('addothergame'),
        contentType: "application/json",
        dataType: 'json',
        data: JSON.stringify(data),
        success: function(response) {
            let game = JSON.parse(response);

            let id = game.game_id
            let url = game.store_url;
            let logo = game.game_logo_url;
            let name = game.game_name;

            //find the current number of added games and set the new element's id to 1 higher
            let i = 0;
                while (true) {
                    let id = "#other-rating" + i;
                    let rating = $(id);

                    if (rating.length == 0) {
                        break;
                    }
                    i++;
                }

            let new_rating = i;
            let selectID = "other-rating" + new_rating;

            //for populating the rating dropdown
            let ratingOptions = "";
            for (let i = 1; i < 11; i++) {
                let option = "<option>" + i + "</option>"
                ratingOptions = ratingOptions + option;
            }

            //add the game to the non-Steam games table
            let game_listing =
            `<tr>
                <td>
                    <a href="#" onclick='window.open("` + url + `"); return false;'>
                        <figure>
                            <img src=` + logo + ` alt="` + name + `}}">
                            <figcaption>
                                    ` + name + `
                            </figcaption>
                        </figure>
                    </a>
                </td>
                <td>
                    <form>
                        <select name="rating" id="` + selectID + `" onchange="assignRating(` + id + `, this.value)">
                            <option value="exclude" selected=>N/A</option>` + ratingOptions + `
                        </select>
                    </form>
                </td>
            </tr>`;

            $("#other-table-body").append(game_listing);

            //resize iframe
            loadComplete();
        },
        error: function(xhr) {
            let message = JSON.parse(xhr.responseText)["error_message"];

            if (message) {
                alert(message);
            }
            else {
                errorMessage();
            }
        },
    });

    //clear the input textbox
    $("#other-text").val("");
}

/** Sends an HTTP request to the server to calculate recommended games. Draws the list if successful.
 * @param {number} listSize - Number of games to recommend.
 */
function recommendGames(listSize) {
    //prevent recommendations while calculation in progress
    if (calculatingRecs()) {
        return;
    }

    //scrolls to top of page, since that's where recommendations appear.
    parent.window.scrollTo(0,0);

    //loading animation
    for (let i = 0; i < listSize; i++) {
        $("#rec" + (i+1)).html(`Calculating<span class="ellipsis"></span>`);
    }

    let ellipsisHTML = "";
    let ellipsisInterval = setInterval(function() {
        if (ellipsisHTML.length > 3)
            ellipsisHTML = "";
        else
            ellipsisHTML += ".";

        $(".ellipsis").html(ellipsisHTML);
    }, 333);

    if ($('.column-switch-button').data('showinglibrary')) {
        switchColumns();
    }
    
    $.ajax({
        type: "GET",
        url: $('body').data('recommendgames'),
        dataType: 'json',
        success: function(response) {
            for (let i = 0; i < listSize; i++) {
                let game = JSON.parse(response[i]);

                let url = game.store_url;
                let logo = game.game_logo_url;
                let name = game.game_name;

                //add onload event to last image in the list to notify parent container to resize iframe
                let finalLoad = i == listSize - 1 ? ` onload='loadComplete()'` : ``;

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
                clearInterval(ellipsisInterval);
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
            for (let i = 0; i < listSize; i++) {
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
                    let id = "#rating" + i;
                    let rating = $(id);

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

                i = 0;
                while (true) {
                    let id = "#other-rating" + i;
                    let rating = $(id);

                    if (rating.length) {
                        if (rating.val() != "exclude"){
                            rating.val("exclude");
                        }
                    }
                    else {
                        //reached the end of user's additional games
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
        button.html("<< Library");
        button.data('showinglibrary', "")

        $('#library-column').css('display', 'none');
        $('#other-column').css('display', 'none');
        $('#rec-column').css('display', 'inline-block');
    }
    else {
        button.html("Recommendations >>");
        button.data('showinglibrary', "true")

        $('#library-column').css('display', 'inline-block');
        $('#other-column').css('display', 'inline-block');
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