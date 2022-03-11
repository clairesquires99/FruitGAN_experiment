import sys
import PIL
from PIL import Image
import os
import numpy as np

def get_images(path_to_folders):
    path = os.path.join(os.getcwd(), path_to_folders)
    folders = os.listdir(path)
    all_images = []
    for folder_name in folders:
        dir = os.path.join(path, folder_name)
        folder_images = []
        with os.scandir(dir) as images:
            for image in images:
                folder_images.append(Image.open(os.path.join(dir, image.name)))
        all_images.append(folder_images)
    return all_images

def make_collage(images, size):
    # size: size of each image in pixels (images are expected to be square)
    length = len(images[0])*size
    height = len(images)*size
    collage = Image.new("RGBA", (length, height)) #blank collage
    for i, row in enumerate(images):
        for j, image in enumerate(row):
            collage.paste(image, (j*size, i*size))
    collage.save( os.path.join(os.getcwd(), 'collage.png'))


def get_images_vh(path):
    # get images for vertical and horizontal stacking
    path = os.path.join(os.getcwd(), path)
    images = os.listdir(path)
    images.sort()
    # print names to ensure alphabetical order
    for i in images:
        print(i)
    cwd = os.getcwd()
    os.chdir(path) # change direcotory to where images are
    images = [Image.open(im) for im in images]
    os.chdir(cwd) # change back to original directory
    return images

def merge_images_vertically(imgs, file_name):
    #create two lists - one for heights and one for widths
    widths, heights = zip(*(i.size for i in imgs))
    width_of_new_image = min(widths)  #take minimum width
    height_of_new_image = sum(heights)
    # create new image
    new_im = Image.new('RGB', (width_of_new_image, height_of_new_image))
    new_pos = 0
    for im in imgs:
        new_im.paste(im, (0, new_pos))
        new_pos += im.size[1]
    new_im.save(file_name)   

def merge_images_horizontally(imgs, file_name):
    #create two lists - one for heights and one for widths
    widths, heights = zip(*(i.size for i in imgs))
    width_of_new_image = sum(widths)
    height_of_new_image = min(heights) #take minimum height
    # create new image
    new_im = Image.new('RGB', (width_of_new_image, height_of_new_image))
    new_pos = 0
    for im in imgs:
        new_im.paste(im, (new_pos,0))
        new_pos += im.size[0]
    new_im.save(file_name) #change the filename if you want

def merge_progressions(path):
    # vertically stacks chains of all experiments for each session
    sessions = os.listdir(path)
    categories = ['apple0', 'apple1', 'apple2', 'orange0', 'orange1', 'orange2', 'grape0', 'grape1', 'grape2']
    for s in sessions:
        images = []
        for c in categories:
            if os.path.exists(f"{path}{s}/{c}/progression.png"):
                images.append(Image.open(f"{path}{s}/{c}/progression.png"))
        merge_images_vertically(images, f"{path}{s}/progressions_{s}.png")


if __name__ == '__main__':
    merge_progressions("test_runs/results_rea2/")
    
