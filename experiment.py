########################################## code from rosinality #########################

import os
import shutil
import subprocess
import torch
from torchvision import utils
import binascii

import sys
sys.path.append('stylegan2-pytorch') # necessary to get Generator from model
from model import Generator

def apply_factor(i, d, eigvec, g, latent, truncation, trunc, iteration_num):
    direction = d * eigvec[:, i].unsqueeze(0)
    vid_increment = 1 # increment degree for interpolation video
    pts = line_interpolate([latent-direction, latent+direction], int((d*2)/vid_increment))

    # clear dump before every iteration
    if os.path.exists('experiment_out/dump'):
        shutil.rmtree('experiment_out/dump')
    if not os.path.exists('experiment_out/dump'):
        os.makedirs('experiment_out/dump')

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
            f"experiment_out/dump/iteration-{iteration_num:02}_frame-{frame_count:03}.png", # if you have more that 999 frames, increase the padding to :04
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


def experiment_setup(ckpt, cff, size, truncation, start_seed, channel_multiplier=2, device='cuda'):
    # generate experiment ID
    sessionID = binascii.hexlify(os.urandom(8)).decode()
    print(sessionID)

    # setup for applying factors
    torch.set_grad_enabled(False)
    eigvec = torch.load(cff)["eigvec"].to(device)
    ckpt = torch.load(ckpt)
    g = Generator(size, 512, 8, channel_multiplier=channel_multiplier).to(device)
    g.load_state_dict(ckpt["g_ema"], strict=False)
    trunc = g.mean_latent(4096)
    
    if os.path.exists('experiment_out/selected'):
        shutil.rmtree('experiment_out/selected')
    if not os.path.exists('experiment_out/selected'):
        os.makedirs('experiment_out/selected')

    if os.path.exists('experiment_out/video_to_stream'):
        shutil.rmtree('experiment_out/video_to_stream')
    if not os.path.exists('experiment_out/video_to_stream'):
        os.makedirs('experiment_out/video_to_stream')

    # set starting seed, generate corresponding latent vector
    torch.manual_seed(start_seed)
    l = torch.randn(1, 512, device='cuda')
    l = g.get_latent(l)

    return eigvec, g, trunc, l

def experiment_loop(iter_num, num_components, eigvec, g, l, truncation, trunc):
    active_comp = iter_num % num_components # active component
    pts = apply_factor(i=active_comp, d=20, eigvec=eigvec, g=g, latent=l, truncation=truncation, trunc=trunc, iteration_num=iter_num)
    # create video
    cmd=f"ffmpeg -loglevel panic -y -r 10 -i experiment_out/dump/iteration-{iter_num:02}_frame-%03d.png -vcodec libx264 -pix_fmt yuv420p experiment_out/video_to_stream/iteration-{iter_num:02}.mp4"
    subprocess.call(cmd, shell=True)
    # get users selected frame
    selected_frame = int(input("Enter the selected frame: "))
    # move selected frame/image from dump to selected folder
    os.rename(f"experiment_out/dump/iteration-{iter_num:02}_frame-{selected_frame:03}.png",
    f"experiment_out/selected/iteration-{iter_num:02}_frame-{selected_frame:03}.png")
    l = pts[selected_frame]
    return l

if __name__ == "__main__":
    ckpt = 'custom_models/fruits3.pt' 
    cff = 'stylegan2-pytorch/factor_fruits3.pt'
    size = 128
    truncation = 1.5
    start_seed = 1
    repeats = 5 # number of times to run through all components
    num_components = 5 # number of eigen vectors to use
    tot_iterations = repeats * num_components

    eigvec, g, trunc, l = experiment_setup(ckpt, cff, size, truncation, start_seed)

    for iter_num in range(tot_iterations):
        l = experiment_loop(iter_num, num_components, eigvec, g, l, truncation, trunc)
