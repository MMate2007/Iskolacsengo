DROP TABLE IF EXISTS patterns;
CREATE TABLE patterns (
	id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
	friendlyname TEXT,
	description TEXT,
	asset_ids TEXT
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
	filepath TEXT NOT NULL,
	length INTEGER,
	volume INTEGER,
	date DATE,
	schedule_id INTEGER
);
DROP TABLE IF EXISTS music;
CREATE TABLE music (
	id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
	file TEXT NOT NULL,
	length INTEGER NOT NULL,
	artist TEXT,
	title TEXT,
	date DATE,
	schedule_id INTEGER
);
