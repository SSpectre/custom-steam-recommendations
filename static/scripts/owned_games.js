function assignRating(gameID, rating) {
    var data = {
        id: gameID,
        rating: rating
    };

    $.ajax({
        type: "POST",
        url: "/assign_rating",
        data: JSON.stringify(data),
        contentType: "application/json",
        dataType: 'json',
        error: function() {
            alert("Please log in again.")
        }
    });
}

function recommendGames() {
    for (let i = 0; i < 100; i++) {
        $("#rec" + (i+1)).html("Calculating...");
    }
    
    $.ajax({
        type: "GET",
        url: "/recommend_games",
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

            alert("Please log in again.")
        },
    });
}