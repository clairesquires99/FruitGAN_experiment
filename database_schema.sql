 CREATE TABLE results (
    session_ID VARCHAR(40) NOT NULL,
    target_category VARCHAR(20) NOT NULL,
    chain_num VARCHAR(10) NOT NULL,
    iteration_num INTEGER NOT NULL,
    image BLOB NOT NULL
);

CREATE TABLE states (
    session_ID VARCHAR(40) PRIMARY KEY,
    json_obj TEXT
);