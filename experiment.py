########################################## code from rosinality #########################

import os
import shutil
import subprocess
import torch
from torchvision import utils

import sys
sys.path.append('stylegan2-pytorch')
from model import Generator


def pre_apply_factor( ckpt, cff_file_path, size, truncation, channel_multiplier=2, device='cuda'):
    torch.set_grad_enabled(False)

    eigvec = torch.load(cff_file_path)["eigvec"].to(device)
    ckpt = torch.load(ckpt)
    g = Generator(size, 512, 8, channel_multiplier=channel_multiplier).to(device)
    g.load_state_dict(ckpt["g_ema"], strict=False)

    trunc = g.mean_latent(4096)

    # latent = torch.randn(1, 512, device=device)
    # latent = g.get_latent(latent)
    return eigvec, g, trunc

def apply_factor(i, d, eigvec, g, latent, truncation, trunc, iteration_num):
    direction = d * eigvec[:, i].unsqueeze(0)

    vid_increment = 0.5 # increment degree for interpolation video

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


if __name__ == "__main__":
    # setup for applying factors
    ckpt = 'custom_models/fruits3.pt' 
    cff = 'stylegan2-pytorch/factor_fruits3.pt'
    eigvec, g, trunc = pre_apply_factor(ckpt, cff, size=128, truncation=1.5)
    
    if os.path.exists('experiment_out/selected'):
        shutil.rmtree('experiment_out/selected')
    if not os.path.exists('experiment_out/selected'):
        os.makedirs('experiment_out/selected')

    if os.path.exists('experiment_out/video_to_stream'):
        shutil.rmtree('experiment_out/video_to_stream')
    if not os.path.exists('experiment_out/video_to_stream'):
        os.makedirs('experiment_out/video_to_stream')

    # set starting seed, generate corresponding latent vector
    start_seed = 0
    torch.manual_seed(start_seed)
    l = torch.randn(1, 512, device='cuda')
    l = g.get_latent(l)

    # for loop
    repeats = 5 # number of times to run through all components
    num_components = 3 # number of eigen vectors to use
    tot_iterations = repeats * num_components
    for iter_num in range(tot_iterations):
        active_comp = iter_num % num_components # active component
        pts = apply_factor(i=active_comp, d=10, eigvec=eigvec, g=g, latent=l, truncation=1.5, trunc=trunc, iteration_num=iter_num)
        # create video
        cmd=f"ffmpeg -loglevel panic -y -r 24 -i experiment_out/dump/iteration-{iter_num:02}_frame-%03d.png -vcodec libx264 -pix_fmt yuv420p experiment_out/video_to_stream/iteration-{iter_num:02}.mp4"
        subprocess.call(cmd, shell=True)
        # get users selected frame
        selected_frame = int(input("Enter the selected frame:"))
        # move selected frame/image from dump to selected folder
        os.rename(f"experiment_out/dump/iteration-{iter_num:02}_frame-{selected_frame:03}.png",
        f"experiment_out/selected/iteration-{iter_num:02}_frame-{selected_frame:03}.png")
        l = pts[selected_frame]
