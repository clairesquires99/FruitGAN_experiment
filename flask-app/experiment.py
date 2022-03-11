import os
import shutil
import subprocess
import torch
from torchvision import utils
import binascii
from PIL import Image
import math
import timeit
import random
import json
from utils import *

import sys
sys.path.insert(0, '/home/csquires/FruitGAN_experiment/stylegan2-pytorch') # necessary to get Generator from model
from model import Generator

# settings
device = 'cuda'
ckpt_path = '../custom_models/fruits3.pt' 
cff_path = '../stylegan2-pytorch/factor_fruits3.pt'
states_path = '../states/'
size = 128
truncation = 1.5
target_categories = ['apple', 'orange', 'grape']
tot_chains = 3 # number of chains per category
num_components = 5 # number of eigen vectors/components to use
repeats = 4 # number of times to run through all components
file_path_dump = '../client/public/images'
file_path_selected = '../results'
# file_path_video = '../experiment_out/video_to_stream'

# calculations
tot_experiments = tot_chains * len(target_categories)
tot_iterations = repeats * num_components

# setup for applying factors
torch.manual_seed(0)
torch.set_grad_enabled(False)
eigvec = torch.load(cff_path)["eigvec"].to(device)
ckpt = torch.load(ckpt_path)
g = Generator(size, 512, 8, 2).to(device)
g.load_state_dict(ckpt["g_ema"], strict=False)
mean_latent, sd_latent = g.mean_sd(10000)
trunc = mean_latent
r = euclidean_dist(mean_latent, (mean_latent + (2 * sd_latent))) # 2 standard deviations away from the mean


def get_points(index, latent):
    e = eigvec[:, index].unsqueeze(0) # unit eigen vector
    pts = [latent]
    # positive direction
    new_pt_pos = latent + e
    d = euclidean_dist(new_pt_pos, mean_latent)
    # print(f"d < r = {d.item():.4f} < {r.item():.4f} = {(d < r).item()}")
    while d < r:
        pts += [new_pt_pos] # append new point to right
        new_pt_pos += e
        d = euclidean_dist(new_pt_pos, mean_latent)

    # negative direction
    new_pt_neg = latent - e
    d = euclidean_dist(new_pt_neg, mean_latent)
    while d < r:
        pts = [new_pt_neg] + pts # append new point to left
        new_pt_neg -= e
        d = euclidean_dist(new_pt_neg, mean_latent)

    return pts



########################################## code from rosinality #########################

def apply_factor(session_ID, iter_num, index, latent, file_path):
    pts = get_points(index, latent)
    left = pts[0]
    right = pts [-1]
    pts = line_interpolate([left, latent, right], 50)

    # clear dump before every iteration
    clear_dir(file_path)

    frame_count = 0
    for pt in pts:
        img, _ = g(
            [pt],
            truncation=truncation,
            truncation_latent=trunc,
            input_is_latent=True,
        )
        grid = utils.save_image(
            img,
            f"{file_path}/iteration-{iter_num:02}_frame-{frame_count:03}.png", # if you have more that 999 frames, increase the padding to :04
            normalize=True,
            value_range=(-1, 1), # updated to 'value_range' from 'range'
            nrow=1,
        )
        frame_count += 1

    return pts

###################################### end of code from rosinality ################################

########################################## code from dvschultz ####################################

def line_interpolate(zs, steps):
    out = []
    for i in range(len(zs)-1):
        for index in range(steps):
            t = index/float(steps)
            out.append(zs[i+1]*t + zs[i]*(1-t))
    return out

###################################### end of code from dvschultz ################################

def generate_ID():
    # generate experiment ID
    session_ID = binascii.hexlify(os.urandom(20)).decode()
    exp_num = 0
    chain_num = exp_num // tot_chains
    target_category = target_categories[exp_num % tot_chains]
    json_obj = {
        "session_ID": session_ID,
        "exp_num": exp_num,
        "tot_experiments": tot_experiments,
        "target_category": target_category,
        "tot_chains": tot_chains,
        "chain_num": chain_num
    }
    return json.dumps(json_obj), session_ID, exp_num

def experiment_setup(session_ID, exp_num):
    chain_num = exp_num // tot_chains
    target_category = target_categories[exp_num % tot_chains]

    this_dump_path = f"{file_path_dump}/{session_ID}/{target_category}{chain_num}"
    this_selected_path = f"{file_path_selected}/{session_ID}/{target_category}{chain_num}"

    clear_dir(this_dump_path)
    clear_dir(this_selected_path)

    # generate starting latent vector
    start_seed = random.randint(0,1000)
    torch.manual_seed(start_seed)
    l = torch.randn(1, 512, device=device)
    l = g.get_latent(l)
    latent_as_list = l.squeeze().tolist() # used in database storage

    # start experiment
    iter_num = 0
    active_comp = iter_num % num_components # active component
    pts = apply_factor(session_ID, iter_num, index=active_comp, latent=l, file_path=this_dump_path)
    # cmd=f"ffmpeg -loglevel panic -y -r 10 -i {file_path_dump}/iteration-{iter_num:02}_frame-%03d.png -vcodec libx264 -pix_fmt yuv420p experiment_out/video_to_stream/iteration-{iter_num:02}.mp4"
    # subprocess.call(cmd, shell=True)
    
    starting_image_num = math.floor(len(pts)/2)
    starting_image_path = f"{this_dump_path}/iteration-00_frame-{starting_image_num:03}.png"
    shutil.copyfile(starting_image_path,f"{this_selected_path}/0seed.png")

    json_obj = {
        "session_ID": session_ID,
        "exp_num": exp_num,
        "target_category": target_category,
        "tot_chains": tot_chains,
        "chain_num": chain_num,
        "image_path": starting_image_path,
        "iter_num": iter_num,
        "tot_iterations": tot_iterations,
        "tot_frames": len(pts)-1,
        "latent": latent_as_list
    }

    torch.save(pts, f'{states_path}{session_ID}.pt')

    print("Experiment setup finished for ", session_ID)
    return json.dumps(json_obj), session_ID, exp_num, target_category, starting_image_path, iter_num, tot_iterations

def experiment_loop(session_ID, exp_num, selected_frame, iter_num):
    chain_num = exp_num // tot_chains
    target_category = target_categories[exp_num % tot_chains]

    selected_frame = int(selected_frame)
    iter_num = int(iter_num)
    # move selected frame/image from dump to selected folder
    this_dump_path = f"{file_path_dump}/{session_ID}/{target_category}{chain_num}"
    this_selected_path = f"{file_path_selected}/{session_ID}/{target_category}{chain_num}"
    selected_image_path = f"{this_selected_path}/iteration-{iter_num:02}_frame-{selected_frame:03}.png"
    os.rename(f"{this_dump_path}/iteration-{iter_num:02}_frame-{selected_frame:03}.png",
    selected_image_path)

    # start next iteration
    iter_num += 1
    pts = torch.load(f'{states_path}{session_ID}.pt')
    l = pts[selected_frame]
    latent_as_list = l.squeeze().tolist() # used in database storage
    active_comp = iter_num % num_components # active component
    pts = apply_factor(session_ID, iter_num,index=active_comp, latent=l, file_path=this_dump_path)
    torch.save(pts, f'{states_path}{session_ID}.pt')

    # create video
    # cmd=f"ffmpeg -loglevel panic -y -r 10 -i {file_path_dump}/iteration-{iter_num:02}_frame-%03d.png -vcodec libx264 -pix_fmt yuv420p experiment_out/video_to_stream/iteration-{iter_num:02}.mp4"
    # subprocess.call(cmd, shell=True)

    json_obj = {
        "session_ID": session_ID,
        "exp_num": exp_num,
        "target_category": target_category,
        "tot_chains": tot_chains,
        "chain_num": chain_num,
        "image_path": selected_image_path,
        "iter_num": iter_num,
        "tot_iterations": tot_iterations,
        "tot_frames": len(pts)-1,
        "latent": latent_as_list
    }
    return json.dumps(json_obj), session_ID, iter_num

def experiment_finish(session_ID, exp_num):
    chain_num = exp_num // tot_chains
    target_category = target_categories[exp_num % tot_chains]

    this_dump_path = f"{file_path_dump}/{session_ID}/{target_category}{chain_num}"
    this_selected_path = f"{file_path_selected}/{session_ID}/{target_category}{chain_num}"
    # saves selected images to progression.png
    if os.path.exists(this_dump_path):
        shutil.rmtree(this_dump_path)
    images = os.listdir(this_selected_path)
    images.sort()
    cwd = os.getcwd()
    os.chdir(this_selected_path) # change direcotory to where images are
    images = [Image.open(im) for im in images]
    os.chdir(cwd) # change back to original directory
    #create two lists - one for heights and one for widths
    widths, heights = zip(*(i.size for i in images))
    width_of_new_image = sum(widths)
    height_of_new_image = min(heights) #take minimum height
    # create new image
    new_im = Image.new('RGB', (width_of_new_image, height_of_new_image))
    new_pos = 0
    for im in images:
        new_im.paste(im, (new_pos,0))
        new_pos += im.size[0]
    new_im.save(f'{this_selected_path}/progression.png')

    # cleanup
    os.remove(f'{states_path}{session_ID}.pt')

    # increase exp_num (experiment number) for next experiment start
    exp_num += 1

    json_obj = {
        "session_ID": session_ID,
        "exp_num": exp_num,
        "target_category": target_category,
        "tot_chains": tot_chains,
        "chain_num": chain_num
    }

    print(f"Experiment {exp_num} ended (chain {target_category}{chain_num}; {session_ID})")
    return json.dumps(json_obj), exp_num

# timing tests
def time_this():
    for i in range(10):
        arg = random.randrange(0, 39)
        experiment_loop(arg)

if __name__ == "__main__":
    _, session_ID, exp_num = generate_ID()
    while int(exp_num) < tot_experiments:
        _ , session_ID, exp_num, target_category, starting_image_path, iter_num, tot_iterations = experiment_setup(session_ID, exp_num)
        while iter_num < tot_iterations:
            selected_frame = int(input("selected frame: "))
            _ , session_ID, iter_num = experiment_loop(session_ID, exp_num, selected_frame, iter_num)
        _, exp_num = experiment_finish(session_ID, exp_num)

    # TIMING TESTS
    # experiment_setup()
    # duration = timeit.timeit(time_this, number=1)
    # print(duration)
