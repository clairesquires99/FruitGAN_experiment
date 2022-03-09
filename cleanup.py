import shutil
import os

def clear(path):
    if os.path.exists(path):
        shutil.rmtree(path)
 
if __name__ == "__main__":
    clear("client/public/images/")
    if os.path.exists("flask-app/experiment.db"):
        os.remove("flask-app/experiment.db")
    clear("results")
    clear("states/")
    os.mkdir("states/")



    