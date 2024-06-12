DROP TABLE IF EXISTS patterns;
CREATE TABLE patterns (
	id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
	friendlyname TEXT UNIQUE,
	description TEXT
);
DROP TABLE IF EXISTS schedule;
CREATE TABLE schedule (
	id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
	pattern_id INTEGER NOT NULL,
	schedule_type INTEGER NOT NULL,
	start TIME NOT NULL,
	end TIME,
	asset_id INTEGER
);
DROP TABLE IF EXISTS dates;
CREATE TABLE dates (
	date DATE NOT NULL PRIMARY KEY,
	pattern_id INTEGER NOT NULL
);
DROP TABLE IF EXISTS assets;
CREATE TABLE assets (
	id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
	asset_type INTEGER NOT NULL,
	filepath TEXT NOT NULL UNIQUE,
	length INTEGER
);
DROP TABLE IF EXISTS customsounds;
CREATE TABLE customsounds (
	id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
	asset_id INTEGER NOT NULL,
	date DATE NOT NULL,
	schedule_id INTEGER NOT NULL,
	params TEXT
);
DROP TABLE IF EXISTS playbacks;
CREATE TABLE playbacks (
	id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
	asset_id INTEGER NOT NULL,
	date DATE NOT NULL,
	time TIME NOT NULL
);