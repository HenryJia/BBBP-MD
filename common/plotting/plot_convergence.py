import argparse, sys, os

import pandas as pd
import numpy as np

import matplotlib.pyplot as plt

parser = argparse.ArgumentParser(description='Plot convergence of free energy calculations')
parser.add_argument('--fn', type=str, help='Filename pattern for free energy data') # e.g. 'smd_fast_fe'
parser.add_argument('--out', type=str, help='Output filename')
parser.add_argument('--min_idx', type=int, help='Minimum index', default=0)
parser.add_argument('--max_idx', type=int, help='Maximum index, exclusive', default=20)
parser.add_argument('--title', type=str, help='Plot title')

args = parser.parse_args()

# Note max_idx is exclusive
def main(args):
    plt.figure(figsize=(16, 10))
    cmap = plt.get_cmap('viridis')
    for idx in range(args.min_idx, args.max_idx):
        data = pd.read_csv( # Read free energy data from plumed outputs
            args.fn.format(idx=idx),
            comment='#',
            sep='\\s+',
            names=['z', 'G', 'dG']
            )
        plt.plot(data['z'], data['G'], label=f'Metadynamics Iteration {idx}', color=cmap(idx / args.max_idx))
    plt.xlabel('Distance from membrane (nm)')
    plt.ylabel('G (kJ/mol)')
    plt.xlim(0, 4)
    plt.ylim(-5, None)
    plt.legend()
    plt.title(args.title)
    plt.savefig(args.out)

if len(sys.argv) == 1:
    membranes = [
        ('Apical Membrane', '../../apical/charmm-gui-2960669761-charmm36-nacl/gromacs/', './apical'),
        ('Basolateral Membrane', '../../basolateral/charmm-gui-2960967181-nacl-charmm36/gromacs/', './basolateral')]
    molecules = ['trihexyphenidyl', 'isopropanol', 'caffeine', 'morphine-6-glucuronide', 'sucrose']
    
    for membrane_name, membrane_fn, out_fn in membranes:
        for molecule in molecules:
            os.makedirs(out_fn, exist_ok=True)
            args.fn = membrane_fn + molecule + '/fes_{idx}.dat'
            args.out = out_fn + '/' + molecule + '_convergence.png'
            args.title = f'{membrane_name} - {molecule} - Free Energy Convergence'
            args.min_idx = 0
            args.max_idx = 11

            main(args)
else:
    main(args)

plt.show()