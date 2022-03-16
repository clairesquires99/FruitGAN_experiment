import torch
from experiment import g
from experiment import Generator, cff_path, ckpt_path, size
from utils import *
from torchvision import utils
import sys
sys.path.insert(0, '/home/csquires/FruitGAN_experiment/stylegan2-ada-pytorch')

states_path = '../states/'
analysis_path = '../analysis/'
device = 'cpu'
torch.manual_seed(0)
torch.set_grad_enabled(False)

# fruits3
eigvec = torch.load(cff_path)["eigvec"].to(device)
ckpt = torch.load(ckpt_path)
g = Generator(size, 512, 8, 2).to(device)
g.load_state_dict(ckpt["g_ema"], strict=False)

mean_latent = torch.load(f'{states_path}mean_latent.pt')
sd_latent = torch.load(f'{states_path}sd_latent.pt')

# fruits2
ckpt2_path = '../custom_models/fruits2.pkl'
ckpt2 = torch.load(ckpt2_path)



def generate_image(latent, fname):
    img, _ = g(
        [latent],
        truncation=5,
        truncation_latent=mean_latent,
        input_is_latent=True,
    )
    grid = utils.save_image(
        img,
        f"{analysis_path}{fname}.png", 
        normalize=True,
        value_range=(-1, 1), # updated to 'value_range' from 'range'
        nrow=1,
    )


if __name__=="__main__":
    generate_image(mean_latent+(4*sd_latent), 'mean+4sd')




    
