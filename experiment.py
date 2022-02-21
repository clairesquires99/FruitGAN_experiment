import os
import shutil
import subprocess
import torch
from torchvision import utils
import binascii
from PIL import Image
import math

import sys
sys.path.append('stylegan2-pytorch') # necessary to get Generator from model
from model import Generator

# settings
ckpt = 'custom_models/fruits3.pt' 
cff = 'stylegan2-pytorch/factor_fruits3.pt'
size = 128
truncation = 1.5
start_seed = 0
degree = 20 # amount of variation for each eigvec
repeats = 1 # number of times to run through all components
num_components = 1 # number of eigen vectors to use
tot_iterations = repeats * num_components
session_ID = None
target_category = 'apple'
file_path_dump = 'client/public/images'
file_path_selected = 'experiment_out/selected'
# file_path_video = 'experiment_out/video_to_stream'

def clear_dir(path):
    if os.path.exists(path):
        shutil.rmtree(path)
    if not os.path.exists(path):
        os.makedirs(path)

########################################## code from rosinality #########################

def apply_factor(index, latent):
    direction = degree * eigvec[:, index].unsqueeze(0)
    vid_increment = 1 # increment degree for interpolation video
    pts = line_interpolate([latent-direction, latent+direction], int((degree*2)/vid_increment))

    # clear dump before every iteration
    clear_dir(file_path_dump)

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
            f"{file_path_dump}/iteration-{iter_num:02}_frame-{frame_count:03}.png", # if you have more that 999 frames, increase the padding to :04
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


def experiment_setup(channel_multiplier=2, device='cuda'):
    global session_ID
    global eigvec
    global ckpt
    global g
    global trunc
    global iter_num
    global pts
    # generate experiment ID
    session_ID = binascii.hexlify(os.urandom(8)).decode()
    print(session_ID)

    # setup for applying factors
    torch.set_grad_enabled(False)
    eigvec = torch.load(cff)["eigvec"].to(device)
    ckpt = torch.load(ckpt)
    g = Generator(size, 512, 8, channel_multiplier=channel_multiplier).to(device)
    g.load_state_dict(ckpt["g_ema"], strict=False)
    trunc = g.mean_latent(4096)
    
    clear_dir(file_path_dump)
    clear_dir(file_path_selected)
    #clear_dir(file_path_video)

    # generate starting latent vector
    torch.manual_seed(start_seed)
    l = torch.randn(1, 512, device='cuda')
    l = g.get_latent(l)

    # start experiment
    iter_num = 0
    active_comp = iter_num % num_components # active component
    pts = apply_factor(index=active_comp, latent=l)
    # cmd=f"ffmpeg -loglevel panic -y -r 10 -i {file_path_dump}/iteration-{iter_num:02}_frame-%03d.png -vcodec libx264 -pix_fmt yuv420p experiment_out/video_to_stream/iteration-{iter_num:02}.mp4"
    # subprocess.call(cmd, shell=True)
    
    starting_image_num = Math.floor(len(pts)/2)
    starting_image_path = f"{file_path_dump}/iteration-{iter_num:02}_frame-{starting_image_num:03}.png"

    print("Experiment setup finished")

    return pts, sessionID, target_category, starting_image_path, iter_num, tot_iterations

def experiment_loop(selected_frame):
    print("Experiment loop running with selected frame: ", selected_frame)
    global iter_num
    global pts
    selected_frame = int(selected_frame)
    print(iter_num)
    # move selected frame/image from dump to selected folder
    selected_image_path = f"{file_path_selected}/iteration-{iter_num:02}_frame-{selected_frame:03}.png"
    os.rename(f"{file_path_dump}/iteration-{iter_num:02}_frame-{selected_frame:03}.png",
    selected_image_path)
    # start next iteration    
    iter_num += 1
    l = pts[selected_frame]
    active_comp = iter_num % num_components # active component
    pts = apply_factor(index=active_comp, latent=l)
    # create video
    # cmd=f"ffmpeg -loglevel panic -y -r 10 -i {file_path_dump}/iteration-{iter_num:02}_frame-%03d.png -vcodec libx264 -pix_fmt yuv420p experiment_out/video_to_stream/iteration-{iter_num:02}.mp4"
    # subprocess.call(cmd, shell=True)
    return pts, sessionID, target_category, selected_image_path, iter_num

def experiment_finish():
    # saves selected images to progression.png
    images = os.listdir(file_path_selected)
    images.sort()
    cwd = os.getcwd()
    os.chdir(file_path_selected) # change direcotory to where images are
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
    new_im.save(f'{file_path_selected}/progression.png')

if __name__ == "__main__":
    global pts
    pts = experiment_setup()
    while iter_num < tot_iterations:
        selected_frame = int(input("selected frame: "))
        pts = experiment_loop(selected_frame)
    experiment_finish()
