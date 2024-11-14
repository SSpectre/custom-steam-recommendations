DROP TABLE IF EXISTS user_games;
DROP TABLE IF EXISTS user_filter_prefs;

CREATE TABLE user_games (
	user_id INTEGER NOT NULL,
	game_id INTEGER NOT NULL,
	owned BOOLEAN,
	rating INTEGER
);

CREATE TABLE user_filter_prefs (
	user_id INTEGER NOT NULL,
	flag_1_name TEXT,
	include_flag_1 INTEGER NOT NULL,
	flag_2_name TEXT,
	include_flag_2 INTEGER NOT NULL,
	flag_3_name TEXT,
	include_flag_3 INTEGER NOT NULL,
	flag_4_name TEXT,
	include_flag_4 INTEGER NOT NULL,
	flag_5_name TEXT,
	include_flag_5 INTEGER NOT NULL
);