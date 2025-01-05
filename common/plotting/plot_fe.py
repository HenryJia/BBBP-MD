import argparse
import sys, os

import pandas as pd
import numpy as np

import matplotlib.pyplot as plt

parser = argparse.ArgumentParser(description='Plot convergence of free energy calculations')
parser.add_argument('--fn', type=str, nargs='+', help='Filename pattern for free energy data') # e.g. 'smd_fast_fe'
parser.add_argument('--names', type=str, nargs='+', help='Names for each free energy data')
parser.add_argument('--title', type=str, help='Plot title')
parser.add_argument('--out', type=str, help='Output filename')

args = parser.parse_args()

def plot_fe(args):
    print('Plotting free energy data with the following arguments:', args)
    plt.figure(figsize=(16, 10))
    for fn, name in zip(args.fn, args.names):
        data = pd.read_csv( # Read free energy data from plumed outputs
            fn,
            comment='#',
            sep='\\s+',
            names=['z', 'G', 'dG']
            )
        plt.plot(data['z'], data['G'], label=name)
    plt.xlabel('z (nm)')
    plt.ylabel('G (kJ/mol)')
    plt.xlim(1, 8)
    plt.ylim(-5, None)
    plt.legend()
    plt.title(args.title)
    plt.savefig(args.out)

# If no arguments are provided, use our hardcoded values
if len(sys.argv) == 1:
    membranes = [
        ('Apical Membrane', '../../apical/charmm-gui-2960669761-charmm36-nacl/gromacs/', './apical/'),
        ('Basolateral Membrane', '../../basolateral/charmm-gui-2960967181-nacl-charmm36/gromacs/', './basolateral/')]
    molecules = ['trihexyphenidyl', 'isopropanol', 'caffeine', 'morphine-6-glucuronide', 'sucrose']
    configurations = [(0.5, 'vslow'), (1, 'slow'), (2, 'fast'), (4, 'vfast')]
    
    for membrane_name, membrane_fn, out_fn in membranes:
        os.makedirs(out_fn, exist_ok=True)
        for molecule in molecules:
            args.out = out_fn + molecule + '.png'
            args.fn = []
            args.names = []
            args.title = f'{membrane_name} - {molecule} Free Energy'
            for s, speed_name in configurations:
                args.fn += [membrane_fn + molecule + '/smd_' + speed_name + '_fe']
                args.names += [f'{s} nm/ns']

            plot_fe(args)

else:
    plot_fe(args)