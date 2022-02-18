
from flask import Flask, send_from_directory, redirect
import random

app = Flask(__name__)

from experiment import experiment_setup, experiment_loop

# Path for our main Svelte page
@app.route("/")
def base():
    return send_from_directory('client/public', 'index.html')

# Path for all the static files (compiled JS/CSS, etc.)
@app.route("/<path:path>")
def home(path):
    return send_from_directory('client/public', path)

@app.route("/start_experiment")
def start():
    experiment_setup()
    return 'this worked'

@app.route("/running_experiment/<selected_frame>")
def run(selected_frame):
    experiment_loop(selected_frame)
    return 'this worked'

# @app.route("/test/<arg>")
# def hello(arg):
#     test(arg)
#     return 'this worked'

if __name__ == "__main__":
    app.run(debug=True)