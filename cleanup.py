import shutil
import os

def clear(path):
    if os.path.exists(path):
        shutil.rmtree(path)
 
if __name__ == "__main__":
    clear("client/public/images/")
    os.remove("flask-app/experiment.db")
    clear("experiment_out/selected/")



    