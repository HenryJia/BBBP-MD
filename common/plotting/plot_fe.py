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
            names=['d_abs', 'G', 'dG']
            )
        # Remove out of bounds data
        data = data[(data['d_abs'] > 0) * (data['d_abs'] < 8)]
        # We should shift the zero point of the free energy to the value in the water
        zero_point = data['G'][data['d_abs'] > 7.0].mean()
        data['G'] -= zero_point
        plt.plot(data['d_abs'], data['G'], label=name)

    plt.xlabel('Distance From Membrane Centre (nm)')
    plt.ylabel('G (kJ/mol)')
    plt.legend()
    plt.title(args.title)
    plt.savefig(args.out)

# If no arguments are provided, use our hardcoded values
if len(sys.argv) == 1:
    membranes = [
        ('Apical Membrane', '../../apical/charmm-gui-3989364611/gromacs/', './apical'),
        ('Basolateral Membrane', '../../basolateral/charmm-gui-3989651295/gromacs/', './basolateral')]
    molecules = ['trihexyphenidyl', 'isopropanol', 'caffeine', 'morphine-6-glucuronide', 'sucrose']
    
    for membrane_name, membrane_fn, out_fn in membranes:
        os.makedirs(out_fn, exist_ok=True)
        args.fn = []
        args.names = []
        args.out = out_fn + '.png'
        args.title = f'{membrane_name} - Free Energy'
        for molecule in molecules:
            args.fn += [membrane_fn + molecule + '/fes.dat']
            args.names += [f'{molecule}']

        plot_fe(args)

else:
    plot_fe(args)

plt.show()