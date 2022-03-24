import sqlite3 as sql
import shutil
import os
import numpy as np
import torch
from torchvision import utils
from sklearn.mixture import GaussianMixture
from tabulate import tabulate
from sklearn.metrics import silhouette_score
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import matplotlib.image as mpimg

import sys
sys.path.insert(0, '/home/csquires/FruitGAN_experiment/stylegan2-pytorch') # necessary to get Generator from model
from model import Generator

device = 'cpu'
ckpt_path = 'custom_models/fruits3.pt' 
cff_path = 'stylegan2-pytorch/factor_fruits3.pt'
size = 128
torch.manual_seed(0)
torch.set_grad_enabled(False)
eigvec = torch.load(cff_path)["eigvec"].to(device)
ckpt = torch.load(ckpt_path)
g = Generator(size, 512, 8, 2).to(device)
g.load_state_dict(ckpt["g_ema"], strict=False)


def get_db_connection():
    conn = sql.connect('flask-app/experiment.db')
    conn.row_factory = sql.Row
    return conn

def get_completed():
    conn = get_db_connection()
    cusor = conn.cursor()
    query = "SELECT * FROM completed"
    cusor.execute(query)
    rows = cusor.fetchall()
    completed_IDs = [row[0] for row in rows]
    conn.close()
    return completed_IDs

def collect_by_fruit():
    # aggregate all fruit progressions by category
    # only works for experiment1 (due to the way that they directories are structured)
    completed_IDs = get_completed()
    fruits = ['apple', 'orange', 'grape']
    count = 0
    for ID in completed_IDs:
        path = f'results_experiment1/{ID}/'
        dirs = os.listdir(path)
        fruit = dirs[0][:-1]
        assert fruit in fruits, f"The directory name encounterd ({fruit}) is not one of the fruit categories"
        destination = f'analysis/results_by_fruit/experiment1/{fruit}'
        if not os.path.exists(destination): os.mkdir(destination)
        for d in dirs:
            shutil.copyfile(f'{path}/{d}/progression.png', f'{destination}/progression{count:02}.png')
            count += 1

def create_analysis_database():
    shutil.copyfile('flask-app/experiment.db', 'analysis.db')
    conn = sql.connect('analysis.db')
    cusor = conn.cursor()
    # no burn-in all
    query = ''' CREATE TABLE no_burnin_all AS 
        SELECT *
        FROM results
        WHERE results.iteration_num > 6;'''
    cusor.execute(query)
    # no burn-in individual fruit
    for fruit in ['apple', 'orange', 'grape']:
        query = f'''CREATE TABLE no_burnin_{fruit} AS 
            SELECT *
            FROM no_burnin_all
            WHERE target_category = "{fruit}";'''
        cusor.execute(query)
    # delete unecessary tables
    for table in ['results', 'states', 'completed']:
        query = f'''DROP TABLE {table}'''
        cusor.execute(query)
    conn.close()

def generate_image(pt, fname):
    img, _ = g(
        [pt],
        truncation=1.0,
        truncation_latent=None,
        input_is_latent=True,
    )
    grid = utils.save_image(
        img,
        fname,
        normalize=True,
        value_range=(-1, 1),
        nrow=1,
    )

def get_latents(fruit):
    conn = sql.connect('analysis.db')
    conn.row_factory = sql.Row
    cusor = conn.cursor()
    query = f'SELECT latent FROM no_burnin_{fruit};'
    cusor.execute(query)
    rows = cusor.fetchall()
    conn.close()
    return rows

def rows_to_tensors(rows):
    # input: row objects from databse
    # output: python list of pytorch tensors
    latents = []
    for row in rows:
        string = row[0][1:-1]
        latent = list(string.split(", "))
        latent = [float(l) for l in latent]
        latent = torch.tensor(latent, device=device)
        latent = latent.unsqueeze(0)
        latents.append(latent)
    return latents

def rows_to_array(rows):
    # input: row objects from databse
    # output: np array
    latents = []
    for row in rows:
        string = row[0][1:-1]
        latent = list(string.split(", "))
        latent = [float(l) for l in latent]

        latents.append(latent)
    array = np.array(latents)
    return array

def get_mean_fruits():
    means = {}
    for fruit in ['apple', 'orange', 'grape']:
        rows = get_latents(fruit)
        latents = rows_to_tensors(rows)
        latents = torch.stack(latents)
        mean = torch.mean(latents,0)
        means[fruit] = mean
    conn.close()
    return means

def gmm(data, n):
    # Gaussian mixture model
    gmm = GaussianMixture(n_components = n, covariance_type='full')
    gmm.fit(data)
    labels = gmm.predict(data)
    if n > 1:
        silhouette = silhouette_score(data, labels)
    else: 
        silhouette = 'na'
    bic = int(gmm.bic(data))
    aic = int(gmm.aic(data))
    # print(tabulate([[n, aic, bic, silhouette]]))
    return gmm.means_, aic, bic, silhouette

def plot_aic():
    for fruit in  ['apple', 'orange', 'grape']:
        rows = get_latents(fruit)
        latents = rows_to_array(rows)
        aics = []
        bics = []
        x = [1,2,3,4,5]
        for n in x:
            _, aic, bic = gmm(latents,n)
            aics.append(aic)
            bics.append(bic)
        if fruit == 'apple':
            color = 'tab:green'
        elif fruit == 'orange':
            color = 'tab:orange'
        elif fruit == 'grape':
            color = 'tab:purple'
        plt.plot(x, aics, color=color, linestyle='dashed', label=f'AIC score for {fruit}')
        plt.plot(x, bics, color=color, label=f'BIC score for {fruit}')
    plt.xlabel('Number of clusters')
    plt.ylabel('Score')
    plt.title(f'AIC and BIC scores by number of clusters')
    plt.xticks(x)
    plt.legend()
    plt.ticklabel_format(style='sci', axis='y', scilimits=(0,0))
    plt.savefig(f"AIC_BIC.png")

def plot_sil():
    # silhouette score
    for fruit in  ['apple', 'orange', 'grape']:
        rows = get_latents(fruit)
        latents = rows_to_array(rows)
        sil_scores = []
        x = [2,3,4,5]
        for n in x:
            _, _, _, sil = gmm(latents,n)
            sil_scores.append(sil)
        if fruit == 'apple':
            color = 'tab:green'
        elif fruit == 'orange':
            color = 'tab:orange'
        elif fruit == 'grape':
            color = 'tab:purple'
        plt.plot(x, sil_scores, color=color, label=fruit)
    plt.xlabel('Number of clusters')
    plt.ylabel('Score')
    plt.title('Silhouette score by number of clusters')
    plt.xticks(x)
    plt.legend()
    plt.savefig(f"silhouette_score.png")

def plot_chains(fruit):
    img = mpimg.imread(f'analysis/results_by_fruit/experiment1/{fruit}.png')
    ax = plt.imshow(img)
    ticks = list(range(64, 3264+1, 128))
    labels = ['random seed']
    labels += [str(i) for i in range(1,26)]
    plt.xticks(ticks, labels)
    sns.despine(top=True, right=True, left=True, bottom=True)
    plt.savefig(f"chains_{fruit}.png")

def project_features(latents, e_num):
    # transform latents from 512 dimensions to 1
    # using eigen vector as projection matrix
    e = eigvec[e_num]
    reduced = latents.dot(e)
    return reduced

def density_plot(fruits, labels):
    r = len(fruits)
    fig, axes = plt.subplots(r, 5, sharex=True, sharey=True, figsize=(14,10))
    for i, fruit in enumerate(fruits):
        rows = get_latents(fruit)
        latents = rows_to_array(rows)
        for e_num in range(5):
            data = project_features(latents, e_num)
            a = sns.distplot(data, hist=True, kde=True, ax=axes[i, e_num])
            a.set_xlabel(f'eigen direction {e_num}')
            a.set_ylabel(labels[i])
    fig.savefig('density_plot.png')
    

if __name__ == '__main__':
    density_plot(['all', 'apple', 'orange', 'grape'], ['All fruits', 'Apple', 'Orange', 'Grape'])


        

    