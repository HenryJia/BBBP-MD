import sys, os

import pandas as pd
import numpy as np

import matplotlib.pyplot as plt
import seaborn as sns

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

def kde_smac(fns, title):
    smac = []
    for fn in fns:
        data = read_smac(fn)
        smac += [data]
    smac = pd.concat(smac, axis=0)

    plt.figure(figsize=(16, 10))

    sns.kdeplot(x=smac['d_abs'], y=smac['smac'], cmap='viridis', fill=True, thresh=0.05, levels=100)
    plt.xlabel('Distance to membrane (nm)')
    plt.ylabel('SMAC (kcal/mol)')
    plt.title(title)

apical_fns = []
basolateral_fns = []
for i, row in pos_cand.iterrows():
    apical_fns += [
        os.path.join(apical_fn, 'candidates/pos/', str(row['idx']), 'smac.txt')
    ]
    basolateral_fns += [
        os.path.join(basolateral_fn, 'candidates/pos/', str(row['idx']), 'smac.txt')
    ]

kde_smac(apical_fns, title='Kernel Density Estimate of SMAC vs Distance to Membrane Centre - Apical Membrane - BBBP+ Compounds')
plt.savefig('apical/smac_kde_pos.png')
kde_smac(basolateral_fns, title='Kernel Density Estimate of SMAC vs Distance to Membrane Centre - Basolateral Membrane - BBBP+ Compounds')
plt.savefig('basolateral/smac_kde_pos.png')
kde_smac(apical_fns + basolateral_fns, title='Kernel Density Estimate of SMAC vs Distance to Membrane Centre - BBBP+ Compounds')
plt.savefig('smac_kde_pos.png')

apical_fns = []
basolateral_fns = []
for i, row in neg_cand.iterrows():
    apical_fns += [
        os.path.join(apical_fn, 'candidates/neg/', str(row['idx']), 'smac.txt')
    ]
    basolateral_fns += [
        os.path.join(basolateral_fn, 'candidates/neg/', str(row['idx']), 'smac.txt')
    ]

kde_smac(apical_fns, title='Kernel Density Estimate of SMAC vs Distance to Membrane Centre - Apical Membrane - BBBP- Compounds')
plt.savefig('apical/smac_kde_neg.png')
kde_smac(basolateral_fns, title='Kernel Density Estimate of SMAC vs Distance to Membrane Centre - Basolateral Membrane - BBBP- Compounds')
plt.savefig('basolateral/smac_kde_neg.png')
kde_smac(apical_fns + basolateral_fns, title='Kernel Density Estimate of SMAC vs Distance to Membrane Centre - BBBP- Compounds')
plt.savefig('smac_kde_neg.png')

plt.show()