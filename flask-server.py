
from flask import Flask, send_from_directory, redirect, render_template
import random

app = Flask(__name__, template_folder='client/public')

from experiment import experiment_setup, experiment_loop, experiment_finish

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
    experiment_finish()
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
    iter_num , _ = experiment_loop(selected_frame)
    return str(iter_num)


if __name__ == "__main__":
    app.run(debug=True)