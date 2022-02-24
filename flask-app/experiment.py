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

import sys
sys.path.insert(0, '/home/csquires/FruitGAN_experiment/stylegan2-pytorch') # necessary to get Generator from model
from model import Generator

# settings
ckpt_path = '../custom_models/fruits3.pt' 
cff_path = '../stylegan2-pytorch/factor_fruits3.pt'
size = 128
truncation = 1.5
device='cuda'
start_seed = 0
degree = 20 # amount of variation for each eigvec
repeats = 1 # number of times to run through all components
num_components = 5 # number of eigen vectors to use
tot_iterations = repeats * num_components
target_categories = ['apple', 'orange', 'grape']
file_path_dump = '../client/public/images'
file_path_selected = '../experiment_out/selected'
# file_path_video = '../experiment_out/video_to_stream'

count = 0 

def clear_dir(path):
    if os.path.exists(path):
        shutil.rmtree(path)
    if not os.path.exists(path):
        os.makedirs(path)

########################################## code from rosinality #########################

def apply_factor(index, latent, dump_path, iter_num):
    direction = degree * eigvec[:, index].unsqueeze(0)
    vid_increment = 1 # increment degree for interpolation video
    pts = line_interpolate([latent-direction, latent+direction], int((degree*2)/vid_increment))

    # clear dump before every iteration
    clear_dir(dump_path)

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
            f"{dump_path}/iteration-{iter_num:02}_frame-{frame_count:03}.png", # if you have more that 999 frames, increase the padding to :04
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


def experiment_setup(channel_multiplier=2):
    global eigvec
    global g
    global trunc

    # setup for applying factors
    torch.set_grad_enabled(False)
    eigvec = torch.load(cff_path)["eigvec"].to(device)
    ckpt = torch.load(ckpt_path)
    g = Generator(size, 512, 8, channel_multiplier=channel_multiplier).to(device)
    g.load_state_dict(ckpt["g_ema"], strict=False)
    trunc = g.mean_latent(4096)

    torch.manual_seed(start_seed) # set start seed

    return tot_iterations

def experiment_start():
    # generate experiment ID
    session_ID = binascii.hexlify(os.urandom(8)).decode()

    target_category = target_categories[0]

    clear_dir(f"{file_path_dump}/{session_ID}/")
    clear_dir(f"{file_path_selected}/{session_ID}/")
    #clear_dir(f"{file_path_video}/{session_ID}/")

    # generate starting latent vector
    l = torch.randn(1, 512, device=device)
    l = g.get_latent(l)

    iter_num = 0
    active_comp = iter_num % num_components # active component
    pts = apply_factor(index=active_comp, latent=l, dump_path=f"{file_path_dump}/{session_ID}", iter_num=iter_num)
    # cmd=f"ffmpeg -loglevel panic -y -r 10 -i {file_path_dump}/iteration-{iter_num:02}_frame-%03d.png -vcodec libx264 -pix_fmt yuv420p experiment_out/video_to_stream/iteration-{iter_num:02}.mp4"
    # subprocess.call(cmd, shell=True)
    
    starting_image_num = math.floor(len(pts)/2)
    starting_image_path = f"{file_path_dump}/{session_ID}/iteration-{iter_num:02}_frame-{starting_image_num:03}.png"

    global count
    count += 1

    return pts, session_ID, target_category, starting_image_path, iter_num, count

def experiment_loop(selected_frame, pts, session_ID, iter_num):
    print(f"Experiment loop num {iter_num:02} running with selected frame: {selected_frame}")
    selected_frame = int(selected_frame)
    # move selected frame/image from dump to selected folder
    selected_image_path = f"{file_path_selected}/{session_ID}/iteration-{iter_num:02}_frame-{selected_frame:03}.png"
    os.rename(f"{file_path_dump}/{session_ID}/iteration-{iter_num:02}_frame-{selected_frame:03}.png",
    selected_image_path)
    # start next iteration
    iter_num += 1
    l = pts[selected_frame]
    active_comp = iter_num % num_components # active component
    pts = apply_factor(index=active_comp, latent=l, dump_path=f"{file_path_dump}/{session_ID}", iter_num=iter_num)
    # create video
    # cmd=f"ffmpeg -loglevel panic -y -r 10 -i {file_path_dump}/iteration-{iter_num:02}_frame-%03d.png -vcodec libx264 -pix_fmt yuv420p experiment_out/video_to_stream/iteration-{iter_num:02}.mp4"
    # subprocess.call(cmd, shell=True)

    global count
    count += 1

    return pts, session_ID, selected_image_path, iter_num, count

def experiment_finish():
    # saves selected images to progression.png
    images = os.listdir(f'{file_path_selected}/{session_ID}')
    images.sort()
    cwd = os.getcwd()
    os.chdir(f'{file_path_selected}/{session_ID}') # change direcotory to where images are
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

# timing tests
def time_this():
    for i in range(10):
        arg = random.randrange(0, 39)
        experiment_loop(arg)

if __name__ == "__main__":
    experiment_setup()
    pts, session_ID, target_category, starting_image_path, iter_num, _ = experiment_start()
    while iter_num < tot_iterations:
        selected_frame = int(input("selected frame: "))
        pts, session_ID, selected_image_path, iter_num, _ = experiment_loop(selected_frame, pts, session_ID, iter_num)
    experiment_finish()

    # TIMING TESTS
    # experiment_setup()
    # duration = timeit.timeit(time_this, number=1)
    # print(duration)
