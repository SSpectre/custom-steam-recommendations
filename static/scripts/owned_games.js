function errorMessage() {
    alert("Something went wrong. Please try logging in again or try again later.");
}

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

function changeListSize(size) {
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

            if (oldSize < size) {
                recommendGames(size);
            }

            $(".rec-number").val(size);
            loadComplete();
        },
        error: function() {
            errorMessage();
        }
    });
}

function recommendGames(list_size) {
    parent.window.scrollTo(0,0);

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
    
    $.ajax({
        type: "GET",
        url: $('body').data('recommendgames'),
        success: function(response) {
            for (let i = 0; i < list_size; i++) {
                let game = JSON.parse(response[i]);

                let url = game.store_url;
                let logo = game.game_logo_url;
                let name = game.game_name;

                let finalLoad = i == list_size - 1 ? ` onload='loadComplete()'` : ``;

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

                clearInterval(eInterval);
            }
        },
        error: function() {
            for (let i = 0; i < list_size; i++) {
                $("#rec" + (i+1)).html("");
            }

            errorMessage();
        },
    });
}

function clearRatings() {
    let i = 0;
    while (true) {
        id = "#rating" + i;
        rating = $(id);

        if (rating.length) {
            rating.val("exclude");
            rating.change();
        }
        else {
            break;
        }
        i++;
    }
}

function deleteUser() {
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

function loadComplete() {
    parent.postMessage({
        type: "resizeFrame"
    });
}