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
            alert("Something went wrong. Please try logging in again or try again later.");
        }
    });
}

function recommendGames(list_size) {
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

                let innerHTML = `<a href="#" onclick='window.open("${url}");return false;'><img src=${logo} alt=${name}` + finalLoad + `></a>${name}`;
                $("#rec" + (i+1)).html(innerHTML);

                clearInterval(eInterval);
            }
        },
        error: function() {
            for (let i = 0; i < list_size; i++) {
                $("#rec" + (i+1)).html("");
            }

            alert("Something went wrong. Please try logging in again or try again later.");
        },
    });
}

function loadComplete() {
    parent.postMessage({
        type: "recommendGames"
    });
}