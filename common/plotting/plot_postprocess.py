import sys, os

import pandas as pd
import numpy as np

import matplotlib.pyplot as plt

# Fuck it, hardcode the arguments, we're not gonna really change them anyway
args = {}

cmap = plt.get_cmap('viridis')
reference_colors = ['red', 'blue', 'green', 'orange', 'purple']

membranes = [
    ('Apical Membrane', '../../apical/', './apical/'),
    ('Basolateral Membrane', '../../basolateral/', './basolateral/')]

apical_fn = '../../apical'
basolateral_fn = '../../basolateral'
pos_csv = '../candidates/bbbp_positive_pubchem.csv'
neg_csv = '../candidates/bbbp_negative_pubchem.csv'

pos_cand = pd.read_csv(pos_csv, comment=';') # colon for comments because # is already used
neg_cand = pd.read_csv(neg_csv, comment=';')

def read_smac(fn):
    data = pd.read_csv( # Read free energy data from plumed outputs
        fn,
        comment='#',
        sep='\\s+',
        names=['time', 'd_abs', 'smac']
        )
    return data

plt.figure(figsize=(16, 10))
#for i, idx in enumerate(neg_cand['idx']):
i = 0
idx = 57998458
fn = f'{apical_fn}/candidates/neg/{idx}/smac.txt'
smac = read_smac(fn)

plt.scatter(
    smac['d_abs'], smac['smac'],
    label=str(idx), color=cmap(i / len(neg_cand['idx']))
)

print(smac.head())
plt.show()