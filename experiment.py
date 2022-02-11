########################################## code from rosinality #########################

import argparse

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

    img, _ = g(
        [latent],
        truncation=truncation,
        truncation_latent=trunc,
        input_is_latent=True,
    )
    img1, _ = g(
        [latent + direction],
        truncation=truncation,
        truncation_latent=trunc,
        input_is_latent=True,
    )
    img2, _ = g(
        [latent - direction],
        truncation=truncation,
        truncation_latent=trunc,
        input_is_latent=True,
    )

    grid = utils.save_image(
        torch.cat([img1, img, img2], 0),
        f"experiment_out/{iteration_num}.png",
        normalize=True,
        value_range=(-1, 1), # updated to 'value_range' from 'range'
        nrow=1,
    )

###################################### end of code from rosinality ################################

if __name__ == "__main__":
    ckpt = 'custom_models/fruits3.pt' 
    cff = 'stylegan2-pytorch/factor_fruits3.pt'
    eigvec, g, trunc = pre_apply_factor(ckpt, cff, size=128, truncation=1.5)

    random_seed = 0
    torch.manual_seed(random_seed)
    l = torch.randn(1, 512, device='cuda')
    l = g.get_latent(l)
    
    apply_factor(i=0, d=10, eigvec=eigvec, g=g, latent=l, truncation=1.5, trunc=trunc, iteration_num=0)