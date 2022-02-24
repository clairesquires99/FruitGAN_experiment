import shutil

def clear(path):
    if os.path.exists(path):
        shutil.rmtree(path)
 
if __name__ = "__main__":
    clear("client/public/images/")
    clear("flask-app/experiment.db")
    clear("experiment_out/selected/")

    