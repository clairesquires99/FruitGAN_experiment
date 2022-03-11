 CREATE TABLE results (
    session_ID VARCHAR(40) NOT NULL,
    target_category VARCHAR(20) NOT NULL,
    chain_num VARCHAR(10) NOT NULL,
    iteration_num INTEGER NOT NULL,
    image BLOB NOT NULL,
    latent TEXT NOT NULL
);

-- Store session states (under the hood stuff)
CREATE TABLE states (
    session_ID VARCHAR(40) PRIMARY KEY,
    json_obj TEXT
);

-- Store experiment session_IDs of participants that completed the experiment
CREATE TABLE completed (
    session_ID VARCHAR(40) PRIMARY KEY
);