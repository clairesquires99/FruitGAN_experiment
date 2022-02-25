
from flask import Flask, send_from_directory, redirect, render_template, request, flash
import sqlite3 as sql
from experiment import experiment_setup, experiment_loop, experiment_finish
import json

app = Flask(__name__, template_folder='../client/public')

# DATABASE
write_to_database = False
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
        conn.execute('INSERT INTO results \
        (session_id, target_category, iteration_num, image) \
        VALUES (?, ?, ?, ?)',(sessionID, target_category, iter_num, image_blob))
        conn.commit()
    except:
        conn.rollback()
        print("ERROR: could not insert data into table")
    finally:
        conn.close()

# ROUTING
# Path for start page
@app.route("/")
def hello():
    return render_template('index.html')

# Path for our main Svelte page (experiment)
@app.route("/experiment")
def experiment():
    return render_template('experiment.html')

@app.route("/error")
def error():
    return render_template('error_page.html')

# Path for all the static files (compiled JS/CSS, etc.)
@app.route("/<path:path>")
def home(path):
    return send_from_directory('../client/public', path)

@app.route("/start_experiment")
def start():
    return_str = ''
    try:
        _ , session_ID, target_category, image_path, iter_num, tot_iterations = experiment_setup()
        if write_to_database:
            insert_database(session_ID, target_category, iter_num, image_path)
        json_str = {
            "tot_iterations": str(tot_iterations),
            "session_ID": str(session_ID),
            "target_category": str(target_category)
        }
        return_str = json.dumps(json_str)
    except AttributeError:
        print('''Error: 'dict' object has no attribute 'seek' (probably during the loading of the checkpoint,
        suspected because more than one person is accessing the experiment at the same time)''')
    return return_str


@app.route("/running_experiment/<selected_frame>")
def run(selected_frame):
    _ , session_ID, target_category, image_path, iter_num = experiment_loop(selected_frame)
    if write_to_database:
        insert_database(session_ID, target_category, iter_num, image_path)
    return str(iter_num)

@app.route("/done")
def end():
    experiment_finish()
    return render_template('done.html')

if __name__ == "__main__":
    app.run(host='0.0.0.0')