
from flask import Flask, send_from_directory, redirect, render_template
import random

app = Flask(__name__)

from experiment import experiment_setup, experiment_loop

# Path for our start page
@app.route("/")
def hello():
    return send_from_directory('client/public', 'index.html')

# Path for our main Svelte page (experiment)
@app.route("/experiment")
def base():
    return send_from_directory('client/public', 'experiment.html')

# Path for our final page
@app.route("/done")
def end():
    return send_from_directory('client/public', 'done.html')

# Path for all the static files (compiled JS/CSS, etc.)
@app.route("/<path:path>")
def home(path):
    return send_from_directory('client/public', path)

@app.route("/start_experiment")
def start():
    tot_iterations, _ = experiment_setup()
    return str(tot_iterations)

@app.route("/running_experiment/<selected_frame>")
def run(selected_frame):
    experiment_loop(selected_frame)
    return 'this worked'


if __name__ == "__main__":
    app.run(debug=True)