
-- User table
CREATE TABLE User (
	name VARCHAR(50) NOT NULL PRIMARY KEY,
	bio VARCHAR(250) DEFAULT "",
	is_admin TINYINT NOT NULL,
	public_key TEXT(728) NOT NULL,
	last_challenge_issued CHAR(10) DEFAULT "",
	challenge_issued_at DATETIME DEFAULT null,
	invite_code CHAR(10) NOT NULL
) ENGINE=InnoDB;

-- Because of circular dependency, foreign key is added below

-- InviteCode table
CREATE TABLE InviteCode (
	code CHAR(10) PRIMARY KEY NOT NULL,
	created_by VARCHAR(50) NOT NULL,
	FOREIGN KEY (created_by) REFERENCES User(name)
) ENGINE=InnoDB;

-- Add a user to represent the console, which can make invite codes
INSERT INTO User (name, bio, is_admin, public_key, invite_code) VALUES (
	"console",
	"console",
	1,
	"",
	"1234567890"
);

INSERT INTO InviteCode (code, created_by) VALUES (
	"1234567890", "console"
);

-- Now add the foreign key since dependency is resolved
ALTER TABLE User ADD FOREIGN KEY (invite_code) REFERENCES InviteCode(code);

-- File table
CREATE TABLE File (
	id INT NOT NULL PRIMARY KEY AUTO_INCREMENT,
	owner VARCHAR(50) NOT NULL,
	name VARCHAR(250) NOT NULL,
	is_read_only TINYINT DEFAULT 0,
	is_archived TINYINT DEFAULT 0,

	FOREIGN KEY (owner) REFERENCES User(name)
) ENGINE=InnoDB;

-- Access Permission
CREATE TABLE AccessPermission (
	file_id INT NOT NULL,
	username VARCHAR(50) NOT NULL,
	allow_read TINYINT NOT NULL,
	allow_write TINYINT NOT NULL,

	PRIMARY KEY (file_id, username),
	FOREIGN KEY (file_id) REFERENCES File(id),
	FOREIGN KEY (username) REFERENCES User(name)
) ENGINE=InnoDB;

-- History Statement
CREATE TABLE HistoryStatement (
	file_id INT NOT NULL,
	created_at DATETIME,
	alleged_username VARCHAR(50) NOT NULL,
	payload VARBINARY(3584) NOT NULL,

	PRIMARY KEY (file_id, created_at),
	FOREIGN KEY (file_id) REFERENCES File(id),
	FOREIGN KEY (alleged_username) REFERENCES User(name)
) ENGINE=InnoDB;