import pandas as pd
import numpy as np

import matplotlib.pyplot as plt

# Note max_idx is exclusive
def plot_convergence(fn='analysis.{idx}.smd_fast_fe', min_idx=0, max_idx=19, steps=2500000, step_size=0.002):
    for idx in range(min_idx, max_idx):
        data = pd.read_csv( # Read free energy data from plumed outputs
            fn.format(idx=idx),
            comment='#',
            sep='\\s+',
            names=['z', 'G', 'dG']
            )
        time = steps * step_size * idx / 1000 # Convert to ns
        plt.plot(data['z'], data['G'], label=f'{time:.2f} ns')
    plt.xlabel('z (nm)')
    plt.ylabel('G (kJ/mol)')
    plt.xlim(1, 8)
    plt.ylim(-5, None)
    plt.legend()


plt.figure(figsize=(16, 10))
plot_convergence(fn='analysis.{idx}.smd_slow_fe', min_idx=0, max_idx=19, steps=2500000, step_size=0.002)
plt.title('Slow pulling (1 nm/ns)')
plt.savefig('slow-pulling.png')

plt.figure(figsize=(16, 10))
plot_convergence(fn='analysis.{idx}.smd_fast_fe', min_idx=0, max_idx=19, steps=2500000, step_size=0.002)
plt.title('Fast pulling (2 nm/ns)')
plt.savefig('fast-pulling.png')

plt.figure(figsize=(16, 10))
plot_convergence(fn='analysis.{idx}.smd_vfast_fe', min_idx=0, max_idx=19, steps=2500000, step_size=0.002)
plt.title('Very fast pulling (4 nm/ns)')
plt.savefig('very-fast-pulling.png')


plt.show()