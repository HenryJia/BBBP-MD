import argparse

import pandas as pd
import numpy as np

import matplotlib.pyplot as plt

parser = argparse.ArgumentParser(description='Plot convergence of free energy calculations')
parser.add_argument('--fn', type=str, help='Filename pattern for free energy data') # e.g. 'smd_fast_fe'
parser.add_argument('--out', type=str, help='Output filename')
parser.add_argument('--min_idx', type=int, help='Minimum index', default=0)
parser.add_argument('--max_idx', type=int, help='Maximum index, exclusive', default=20)
parser.add_argument('--steps', type=int, help='Number of steps per index', default=2500000)
parser.add_argument('--step_size', type=float, help='Step size in ns', default=0.002)
parser.add_argument('--title', type=str, help='Plot title')

args = parser.parse_args()

# Note max_idx is exclusive
def plot_convergence(fn, min_idx=0, max_idx=19, steps=2500000, step_size=0.002):
    for idx in range(min_idx, max_idx):
        data = pd.read_csv( # Read free energy data from plumed outputs
            fn.format(idx=idx),
            comment='#',
            sep='\\s+',
            names=['z', 'G', 'dG']
            )
        time = steps * step_size * (idx + 1) / 1000 # Convert to ns
        plt.plot(data['z'], data['G'], label=f'{time:.2f} ns')
    plt.xlabel('z (nm)')
    plt.ylabel('G (kJ/mol)')
    plt.xlim(1, 8)
    plt.ylim(-5, None)
    plt.legend()


plt.figure(figsize=(16, 10))
plot_convergence(fn=args.fn, min_idx=args.min_idx, max_idx=args.max_idx, steps=args.steps, step_size=args.step_size)
plt.title(args.title)
plt.savefig(args.out)

plt.show()