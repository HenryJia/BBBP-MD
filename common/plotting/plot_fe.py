import argparse

import pandas as pd
import numpy as np

import matplotlib.pyplot as plt

parser = argparse.ArgumentParser(description='Plot convergence of free energy calculations')
parser.add_argument('--fn', type=str, nargs='+', help='Filename pattern for free energy data') # e.g. 'smd_fast_fe'
parser.add_argument('--names', type=str, nargs='+', help='Names for each free energy data')
parser.add_argument('--title', type=str, help='Plot title')
parser.add_argument('--out', type=str, help='Output filename')

args = parser.parse_args()

def plot_fe(fns, names):
    for fn, name in zip(fns, names):
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