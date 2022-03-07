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
degree = 20 # amount of variation for each eigvec
repeats = 1 # number of times to run through all components
num_components = 5 # number of eigen vectors to use
tot_iterations = repeats * num_components
target_categories = ['apple', 'orange', 'grape']
file_path_dump = '../client/public/images'
file_path_selected = '../experiment_out/selected'
# file_path_video = '../experiment_out/video_to_stream'

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

print("Mean latent : ", mean_latent[0][:5])
print("Mean + 2sds : ", r)


def dunno(index, latent):
    e = eigvec[:, index].unsqueeze(0) # unit eigen vector
    pts = [latent]
    print("Start latent: ", latent[0][:5])
    # positive direction
    new_pt_pos = latent + e
    d = euclidean_dist(new_pt_pos, mean_latent)
    print(f"d < r = {d.item():.4f} < {r.item():.4f} = {(d < r).item()}")
    while d < r:
        pts += [new_pt_pos] # append new point to right
        new_pt_pos += e
        d = euclidean_dist(new_pt_pos, mean_latent)
        print(f"d < r = {d.item():.4f} < {r.item():.4f} = {(d < r).item()}")

    # negative direction
    new_pt_neg = latent - e
    d = euclidean_dist(new_pt_neg, mean_latent)
    print(f"\nd < r = {d.item():.4f} < {r.item():.4f} = {(d < r).item()}")
    while d < r:
        pts = [new_pt_neg] + pts # append new point to left
        new_pt_neg -= e
        d = euclidean_dist(new_pt_neg, mean_latent)
        print(f"d < r = {d.item():.4f} < {r.item():.4f} = {(d < r).item()}")

    return pts



########################################## code from rosinality #########################

def apply_factor(session_ID, iter_num, index, latent):
    pts = dunno(index, latent)
    left = pts[0]
    right = pts [-1]
    pts = line_interpolate([left, latent, right], 25)
    # direction = degree * eigvec[:, index].unsqueeze(0)
    # vid_increment = 1 # increment degree for interpolation video
    # pts = line_interpolate([latent-direction, latent+direction], int((degree*2)/vid_increment))

    # clear dump before every iteration
    clear_dir(f"{file_path_dump}/{session_ID}")

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
            f"{file_path_dump}/{session_ID}/iteration-{iter_num:02}_frame-{frame_count:03}.png", # if you have more that 999 frames, increase the padding to :04
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

def experiment_setup():
    # generate experiment ID
    session_ID = binascii.hexlify(os.urandom(20)).decode()
    print(session_ID)

    clear_dir(f"{file_path_dump}/{session_ID}")
    clear_dir(f"{file_path_selected}/{session_ID}")
    #clear_dir(f"{file_path_video}/{session_ID}")

    # generate starting latent vector
    start_seed = random.randint(0,1000)
    start_seed = 0
    torch.manual_seed(start_seed)
    l = torch.randn(1, 512, device=device)
    l = g.get_latent(l)

    # start experiment
    target_category = random.choice(target_categories)
    iter_num = 0
    active_comp = iter_num % num_components # active component
    pts = apply_factor(session_ID, iter_num, index=active_comp, latent=l)
    # cmd=f"ffmpeg -loglevel panic -y -r 10 -i {file_path_dump}/iteration-{iter_num:02}_frame-%03d.png -vcodec libx264 -pix_fmt yuv420p experiment_out/video_to_stream/iteration-{iter_num:02}.mp4"
    # subprocess.call(cmd, shell=True)
    
    starting_image_num = math.floor(len(pts)/2)
    starting_image_path = f"{file_path_dump}/{session_ID}/iteration-00_frame-{starting_image_num:03}.png"
    shutil.copyfile(starting_image_path,f"{file_path_selected}/{session_ID}/0seed.png")

    json_obj = {
        "session_ID": session_ID,
        "target_category": target_category,
        "image_path": starting_image_path,
        "iter_num": iter_num,
        "tot_iterations": tot_iterations,
        "tot_frames": len(pts)-1
    }

    torch.save(pts, f'{states_path}{session_ID}.pt')

    print("Experiment setup finished")
    return json.dumps(json_obj), session_ID, target_category, starting_image_path, iter_num, tot_iterations

def experiment_loop(session_ID, selected_frame, iter_num, target_category):
    # print("Experiment loop running with selected frame: ", selected_frame)
    selected_frame = int(selected_frame)
    iter_num = int(iter_num)
    # print("Iteration #", iter_num)
    # move selected frame/image from dump to selected folder
    selected_image_path = f"{file_path_selected}/{session_ID}/iteration-{iter_num:02}_frame-{selected_frame:03}.png"
    os.rename(f"{file_path_dump}/{session_ID}/iteration-{iter_num:02}_frame-{selected_frame:03}.png",
    selected_image_path)
    # start next iteration
    iter_num += 1
    pts = torch.load(f'{states_path}{session_ID}.pt')
    l = pts[selected_frame]
    active_comp = iter_num % num_components # active component
    pts = apply_factor(session_ID, iter_num,index=active_comp, latent=l)
    torch.save(pts, f'{states_path}{session_ID}.pt')
    # create video
    # cmd=f"ffmpeg -loglevel panic -y -r 10 -i {file_path_dump}/iteration-{iter_num:02}_frame-%03d.png -vcodec libx264 -pix_fmt yuv420p experiment_out/video_to_stream/iteration-{iter_num:02}.mp4"
    # subprocess.call(cmd, shell=True)

    json_obj = {
        "session_ID": session_ID,
        "target_category": target_category,
        "image_path": selected_image_path,
        "iter_num": iter_num,
        "tot_iterations": tot_iterations,
        "tot_frames": len(pts)-1
    }
    return json.dumps(json_obj), session_ID, iter_num

def experiment_finish(session_ID):
    # saves selected images to progression.png
    if os.path.exists(f"{file_path_dump}/{session_ID}"):
        shutil.rmtree(f"{file_path_dump}/{session_ID}")
    images = os.listdir(f"{file_path_selected}/{session_ID}")
    images.sort()
    cwd = os.getcwd()
    os.chdir(f"{file_path_selected}/{session_ID}") # change direcotory to where images are
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
    new_im.save(f'{file_path_selected}/{session_ID}/progression.png')

    # cleanup
    os.remove(f'{states_path}{session_ID}.pt')

# timing tests
def time_this():
    for i in range(10):
        arg = random.randrange(0, 39)
        experiment_loop(arg)

if __name__ == "__main__":
    _ , session_ID, target_category, image_path, iter_num, tot_iterations = experiment_setup()
    while iter_num < tot_iterations:
        selected_frame = int(input("selected frame: "))
        _ , session_ID, iter_num = experiment_loop(session_ID, selected_frame, iter_num, target_category)
    experiment_finish(session_ID)

    # TIMING TESTS
    # experiment_setup()
    # duration = timeit.timeit(time_this, number=1)
    # print(duration)
