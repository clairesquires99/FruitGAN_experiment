import os
import shutil
import torch

def clear_dir(path):
    if os.path.exists(path):
        shutil.rmtree(path)
    if not os.path.exists(path):
        os.makedirs(path)

def euclidean_dist(a, b):
    return torch.sqrt(torch.sum((a-b)**2))