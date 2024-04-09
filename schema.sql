DROP TABLE IF EXISTS user_games;

CREATE TABLE user_games (
	user_id INTEGER NOT NULL,
	game_id INTEGER NOT NULL,
	rating INTEGER
);