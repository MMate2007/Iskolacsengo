DROP TABLE IF EXISTS users;
CREATE TABLE users (
	id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
	username TEXT NOT NULL UNIQUE,
	password TEXT NOT NULL
);
DROP TABLE IF EXISTS permissions;
CREATE TABLE permissions (
	id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
	friendlyname TEXT NOT NULL UNIQUE, 
	humanname TEXT
);
DROP TABLE IF EXISTS userpermissions;
CREATE TABLE userpermissions (
	user_id INTEGER NOT NULL,
	permission_id INTEGER NOT NULL
);
