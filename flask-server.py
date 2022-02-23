
from flask import Flask, send_from_directory, redirect, render_template, request, flash
import sqlite3 as sql
from experiment import experiment_setup, experiment_loop, experiment_finish

app = Flask(__name__, template_folder='client/public')

# DATABASE
# db_name = 'experiment.db'
# app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + db_name
# app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True
# db = SQLAlchemy(app)

def get_db_connection():
    conn = sql.connect('experiment.db')
    conn.row_factory = sql.Row
    return conn

def convertToBinaryData(filename):
    # Convert digital data to binary format
    with open(filename, 'rb') as file:
        binaryData = file.read()
    return binaryData

# ROUTING
# Path for start page
@app.route("/")
def hello():
    return send_from_directory('client/public', 'index.html')

# Path for our main Svelte page (experiment)
@app.route("/experiment")
def experiment():
    return send_from_directory('client/public', 'experiment.html')

# Path for all the static files (compiled JS/CSS, etc.)
@app.route("/<path:path>")
def home(path):
    return send_from_directory('client/public', path)

@app.route("/start_experiment")
def start():
    _ , sessionID, target_category, starting_image_path, iter_num, tot_iterations = experiment_setup()
    image_blob = convertToBinaryData(starting_image_path)
    conn = get_db_connection()
    conn.execute('INSERT INTO results \
    (session_id, target_category, iteration_num, image) \
    VALUES (?, ?, ?, ?)',(sessionID, target_category, iter_num, image_blob))
    conn.commit()
    conn.close()
    return str(tot_iterations)

@app.route("/running_experiment/<selected_frame>")
def run(selected_frame):
    _ , sessionID, target_category, image_path, iter_num = experiment_loop(selected_frame)
    image_blob = convertToBinaryData(image_path)
    conn = get_db_connection()
    conn.execute('INSERT INTO results \
    (session_id, target_category, iteration_num, image) \
    VALUES (?, ?, ?, ?)',(sessionID, target_category, iter_num, image_blob))
    conn.commit()
    conn.close()
    return str(iter_num)

@app.route("/done")
def end():
    experiment_finish()
    return send_from_directory('client/public','done.html')

if __name__ == "__main__":
    app.run(debug=True)