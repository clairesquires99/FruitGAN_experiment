
from flask import Flask, send_from_directory, redirect, render_template, request, flash
import sqlite3 as sql
from experiment import experiment_setup, experiment_loop, experiment_finish

app = Flask(__name__, template_folder='client/public')

# DATABASE
def get_db_connection():
    conn = sql.connect('experiment.db')
    conn.row_factory = sql.Row
    return conn

def convertToBinaryData(filename):
    # Convert digital data to binary format
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

# Path for all the static files (compiled JS/CSS, etc.)
@app.route("/<path:path>")
def home(path):
    return send_from_directory('client/public', path)

@app.route("/start_experiment")
def start():
    _ , sessionID, target_category, image_path, iter_num, tot_iterations = experiment_setup()
    insert_database(sessionID, target_category, iter_num, image_path)
    return str(tot_iterations)

@app.route("/running_experiment/<selected_frame>")
def run(selected_frame):
    _ , sessionID, target_category, image_path, iter_num = experiment_loop(selected_frame)
    insert_database(sessionID, target_category, iter_num, image_path)
    return str(iter_num)

@app.route("/done")
def end():
    experiment_finish()
    return render_template('done.html')

if __name__ == "__main__":
    app.run(debug=True)