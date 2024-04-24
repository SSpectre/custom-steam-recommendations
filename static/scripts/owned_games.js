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

function recommendGames() {
    for (let i = 0; i < 100; i++) {
        $("#rec" + (i+1)).html("Calculating...");
    }
    
    $.ajax({
        type: "GET",
        url: $('body').data('recommendgames'),
        success: function(response) {
            for (let i = 0; i < 100; i++) {
                let game = JSON.parse(response[i]);

                let url = game.store_url;
                let logo = game.game_logo_url;
                let name = game.game_name;
                let innerHTML = `<a href=${url}><img src=${logo} alt=${name}></a>${name}`;
                $("#rec" + (i+1)).html(innerHTML);
            }
        },
        error: function() {
            for (let i = 0; i < 100; i++) {
                $("#rec" + (i+1)).html("");
            }

            alert("Something went wrong. Please try logging in again or try again later.");
        },
    });
}