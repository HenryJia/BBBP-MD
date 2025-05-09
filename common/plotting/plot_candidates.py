import sys, os

import pandas as pd
import numpy as np

import matplotlib.pyplot as plt

# Fuck it, hardcode the arguments, we're not gonna really change them anyway
args = {}

cmap = plt.get_cmap('viridis')
reference_colors = ['red', 'blue', 'green', 'orange', 'purple']

def read_fes(fn):
    data = pd.read_csv( # Read free energy data from plumed outputs
        fn,
        comment='#',
        sep='\\s+',
        names=['d_abs', 'G', 'dG']
        )
    # Remove out of bounds data
    data = data[(data['d_abs'] > 0) * (data['d_abs'] < 8)]
    # We should shift the zero point of the free energy to the value in the water
    zero_point = data['G'][data['d_abs'] > 7.0].mean()
    data['G'] -= zero_point
    return data

def load_plot_fes(args):

    reference_molecules = ['trihexyphenidyl', 'isopropanol', 'caffeine', 'morphine-6-glucuronide', 'sucrose']
    reference_fes = {}

    for rm in reference_molecules:
        fn = f'{args['fn']}/gromacs/{rm}/fes.dat'
        reference_fes[rm] = read_fes(fn)

    pos_cand = pd.read_csv(args['pos_csv'], comment=';') # colon for comments because # is already used
    neg_cand = pd.read_csv(args['neg_csv'], comment=';')
    pos_fes = {}
    neg_fes = {}

    # Calculate the free energy barrier
    plt.figure(figsize=(16, 10))
    plt.title(args['name'] + ' - Free Energy Profile of Positive Candidates')
    for i, idx in enumerate(pos_cand['idx']):
        fn = f'{args['fn']}/candidates/pos/{idx}/fes.dat'
        pos_fes[idx] = read_fes(fn)

        plt.plot(
            pos_fes[idx]['d_abs'], pos_fes[idx]['G'],
            label=str(idx), color=cmap(i / len(pos_cand['idx']))
            )

    for i, rm in enumerate(reference_fes):
        plt.plot(
            reference_fes[rm]['d_abs'], reference_fes[rm]['G'],
            label=rm, color=reference_colors[i]
            )

    plt.xlabel('Distance From Membrane Centre (nm)')
    plt.ylabel('G (kJ/mol)')
    plt.legend()
    plt.savefig(args['out'] + 'candidates_pos.png')

    plt.figure(figsize=(16, 10))
    plt.title(args['name'] + ' - Free Energy Profile of Negative Candidates')
    for i, idx in enumerate(neg_cand['idx']):
        fn = f'{args['fn']}/candidates/neg/{idx}/fes.dat'
        neg_fes[idx] = read_fes(fn)
        plt.plot(
            neg_fes[idx]['d_abs'], neg_fes[idx]['G'],
            label=str(idx), color=cmap(i / len(neg_cand['idx']))
            )

    for i, rm in enumerate(reference_fes):
        plt.plot(
            reference_fes[rm]['d_abs'], reference_fes[rm]['G'],
            label=rm, color=reference_colors[i]
            )
    
    plt.xlabel('Distance From Membrane Centre (nm)')
    plt.ylabel('G (kJ/mol)')
    plt.legend()
    plt.savefig(args['out'] + 'candidates_neg.png')

    plt.figure(figsize=(8, 10))
    plt.title(args['name'] + ' - Maximum Free Energy Barrier of Candidates')
    pos_barriers = [pos_fes[idx]['G'].max() for idx in pos_cand['idx']]
    neg_barriers = [neg_fes[idx]['G'].max() for idx in neg_cand['idx']]
    plt.boxplot(
        [pos_barriers, neg_barriers],
        positions=[1, 2],
        widths=0.5, whis=[0, 100],
        patch_artist=True,
        boxprops=dict(facecolor='lightblue', color='black'),
        medianprops=dict(color='black'),
        )
    plt.xticks([1, 2], ['Positive Candidates', 'Negative Candidates'])
    plt.ylabel('Free Energy Barrier (kJ/mol)')

    # Add our reference molecules as horizontal lines
    for i, rm in enumerate(reference_fes):
        plt.axhline(
            reference_fes[rm]['G'].max(),
            label=rm, color=reference_colors[i],
            )
    plt.legend()
    plt.savefig(args['out'] + 'candidates_boxplot.png')

    return reference_fes, pos_fes, neg_fes


# If no arguments are provided, use our hardcoded values
membranes = [
    ('Apical Membrane', '../../apical/', './apical/'),
    ('Basolateral Membrane', '../../basolateral/', './basolateral/')]

args['name'] = 'Apical Membrane'
args['fn'] = '../../apical/'
args['out'] = './apical/'
args['pos_csv'] = '../candidates/bbbp_positive_pubchem.csv'
args['neg_csv'] = '../candidates/bbbp_negative_pubchem.csv'
apical_ref_fes, apical_pos_fes, apical_neg_fes = load_plot_fes(args)

args['name'] = 'Basolateral Membrane'
args['fn'] = '../../basolateral/'
args['out'] = './basolateral/'
basolateral_ref_fes, basolateral_pos_fes, basolateral_neg_fes = load_plot_fes(args)

plt.figure(figsize=(8, 10))
plt.title('Total Free Energy Barrier of Candidates Across Both Membranes')
pos_barriers = [apical_pos_fes[idx]['G'].max() + basolateral_pos_fes[idx]['G'].max() for idx in apical_pos_fes]
neg_barriers = [apical_neg_fes[idx]['G'].max() + basolateral_neg_fes[idx]['G'].max() for idx in apical_neg_fes]
reference_barriers = [apical_ref_fes[rm]['G'].max() + basolateral_ref_fes[rm]['G'].max() for rm in apical_ref_fes]

plt.boxplot(
    [pos_barriers, neg_barriers],
    positions=[1, 2],
    widths=0.5, whis=[0, 100],
    patch_artist=True,
    boxprops=dict(facecolor='lightblue', color='black'),
    medianprops=dict(color='black'),
    )
plt.xticks([1, 2], ['Positive Candidates', 'Negative Candidates'])
plt.ylabel('Total Free Energy Barrier (kJ/mol)')
# Add our reference molecules as horizontal lines
for i, rm in enumerate(apical_ref_fes):
    plt.axhline(
        reference_barriers[i],
        label=rm, color=reference_colors[i],
        )

plt.legend()
plt.savefig('candidates_boxplot_total.png')

plt.show()