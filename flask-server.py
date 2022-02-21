
from flask import Flask, send_from_directory, redirect, render_template, request, flash
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.sql import text
from experiment import experiment_setup, experiment_loop, experiment_finish

app = Flask(__name__, template_folder='client/public')

# DATABASE
db_name = 'experiment.db'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + db_name
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True
db = SQLAlchemy(app)

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
    return str(tot_iterations)

@app.route("/running_experiment/<selected_frame>")
def run(selected_frame):
    _ , sessionID, target_category, image_path, iter_num = experiment_loop(selected_frame)
    return str(iter_num)

@app.route("/done")
def end():
    experiment_finish()
    return send_from_directory('client/public','done.html')

if __name__ == "__main__":
    app.run(debug=True)