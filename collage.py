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

def merge_images_vertically(imgs, name):
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
    new_im.save('collage-'+name+'.png')   

def merge_images_horizontally(imgs):
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
    new_im.save('collage.png') #change the filename if you want

if __name__ == '__main__':
    images = get_images_vh("experiment_out/selected_target-orange_seed-1_d-20_c-6")
    merge_images_horizontally(images)
    
