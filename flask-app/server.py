
from flask import Flask, send_from_directory, redirect, render_template, request, flash
import sqlite3 as sql
from experiment import generate_ID, experiment_setup, experiment_loop, experiment_finish
from database_handler import insert_database, save_state, get_state
import json
from flask import request

app = Flask(__name__, template_folder='../client/public')

# DATABASE
write_to_database = False

# ROUTING
# Path for start page
@app.route("/")
def hello():
    return render_template('index.html')

@app.route("/information")
def pis():
    return render_template('information.html')

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

@app.route("/get_ID")
def get_ID():
    json_obj = generate_ID()[0]
    obj = json.loads(json_obj)
    save_state(obj['session_ID'], json_obj)
    return json_obj

@app.route("/start_experiment")
def start():
    session_ID = request.args.get('session_ID')
    obj = json.loads(get_state(session_ID))
    json_obj = experiment_setup(session_ID, obj['target_category'], obj['chain_num'])[0]
    save_state(session_ID, json_obj)
    if write_to_database:
        insert_database(obj)
    return json_obj


@app.route("/running_experiment/")
def run():
    selected_frame = request.args.get('selected_frame')
    session_ID = request.args.get('session_ID')
    obj_prev = json.loads(get_state(session_ID))
    json_obj = experiment_loop(session_ID, selected_frame, obj_prev['iter_num'], obj_prev['target_category'], obj_prev['chain_num'])[0]
    obj = json.loads(json_obj)
    save_state(session_ID, json_obj)
    if write_to_database:
        insert_database(obj)
    return json_obj

@app.route("/end_chain")
def end_chain():
    session_ID = request.args.get("session_ID")
    obj = json.loads(get_state(session_ID))
    json_obj = experiment_finish(session_ID, obj['target_category'], obj['chain_num'])[0]
    obj = json.loads(json_obj)
    save_state(session_ID, json_obj)
    return json_obj

@app.route("/done")
def done():
    return render_template('done.html')

if __name__ == "__main__":
    app.run(host='0.0.0.0', debug=True)