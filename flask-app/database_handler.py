import sqlite3 as sql

def get_db_connection():
    conn = sql.connect('experiment.db')
    conn.row_factory = sql.Row
    return conn

def convertToBinaryData(filename):
    # convert digital data to binary format
    with open(filename, 'rb') as file:
        binaryData = file.read()
    return binaryData

def insert_database(sessionID, target_category, iter_num, image_path):
    image_blob = convertToBinaryData(image_path)
    conn = get_db_connection()
    try:
        conn.execute(f'INSERT INTO results \
        (session_ID, target_category, iteration_num, image) \
        VALUES (?, ?, ?, ?)',(sessionID, target_category, iter_num, image_blob))
        conn.commit()
    except Exception as e:
        conn.rollback()
        print("ERROR: could not insert data into table 'results'")
        print(e)
    finally:
        conn.close()

def save_state(session_ID, json_obj):
    conn = get_db_connection()
    try:
        conn.execute('INSERT OR REPLACE INTO states \
        (session_ID, json_obj) \
        VALUES (?, ?);',(session_ID, json_obj))
        conn.commit()
    except Exception as e:
        conn.rollback()
        print("ERROR: could not insert data into table 'states'")
        print(e)
    finally:
        conn.close()

def get_state(session_ID):
    conn = get_db_connection()
    cusor = conn.cursor()
    query = """SELECT json_obj FROM states WHERE session_ID = ?"""
    cusor.execute(query, (session_ID,))
    rows = cusor.fetchall()
    if len(rows) != 1:
        print(f"WARNING: something has gone wrong in the database, there should only be one entry for session_ID {session_ID}")
    return rows[0][0]