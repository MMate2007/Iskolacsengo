CREATE TABLE users (
	id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
	username TEXT NOT NULL,
	password TEXT NOT NULL
);
CREATE TABLE permissions (
	id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
	friendlyname TEXT NOT NULL,
	description TEXT
);
CREATE TABLE userpermissions (
	user_id INTEGER NOT NULL,
	permission_id INTEGER NOT NULL
);
CREATE TABLE tokens (
	id TEXT NOT NULL PRIMARY KEY,
	user_id INTEGER NOT NULL,
	created_at DATE NOT NULL DEFAULT (datetime('now', 'localtime')),
	last_activity DATE NOT NULL DEFAULT (datetime('now', 'localtime'))
);
