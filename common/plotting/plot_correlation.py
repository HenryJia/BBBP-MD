import pandas as pd
import numpy as np

import matplotlib.pyplot as plt

# Probably shouldn't hardcode this
# But it's fine for now and this is the fastest way to get it done

membranes = [
        ('Apical Membrane', '../../apical/charmm-gui-2960669761-charmm36-nacl/gromacs/'),
        ('Basolateral Membrane', '../../basolateral/charmm-gui-2960967181-nacl-charmm36/gromacs/')]
molecules = {
    'trihexyphenidyl': 1.32,
    'isopropanol': -0.1,
    'morphine-6-glucuronide': -2.09,
    'sucrose': -1.7}


# Note max_idx is exclusive
apical_barriers = {}
for molecule in molecules:
    data = pd.read_csv( # Read free energy data from plumed outputs
        membranes[0][1] + molecule + '/fes.dat',
        comment='#',
        sep='\\s+',
        names=['z', 'G', 'dG']
        )
    # Remove out of bounds data
    data = data[(data['z'] > 0) * (data['z'] < 4)]
    # We should shift the zero point of the free energy to the value in the water
    zero_point = data['G'][data['z'] > 3.0].mean()
    data['G'] -= zero_point

    if molecule not in apical_barriers:
        apical_barriers[molecule] = 0
    apical_barriers[molecule] += data['G'].max()

basolateral_barriers = {}
for molecule in molecules:
    data = pd.read_csv( # Read free energy data from plumed outputs
        membranes[1][1] + molecule + '/fes.dat',
        comment='#',
        sep='\\s+',
        names=['z', 'G', 'dG']
        )
    # Remove out of bounds data
    data = data[(data['z'] > 0) * (data['z'] < 4)]
    # We should shift the zero point of the free energy to the value in the water
    zero_point = data['G'][data['z'] > 3.0].mean()
    data['G'] -= zero_point

    if molecule not in basolateral_barriers:
        basolateral_barriers[molecule] = 0
    basolateral_barriers[molecule] += data['G'].max()

barriers = {}
for molecule in molecules:
    barriers[molecule] = apical_barriers[molecule] + basolateral_barriers[molecule]

plt.figure()
for k in molecules:
    x = barriers[k]
    y = molecules[k]
    plt.scatter(x, y)
    plt.annotate(k, (x, y))

# Add a horizontal line at y=-1 to separate BBBP+ and BBBP-
# Molecules with logBB > -1 are considered to be BBBP+
plt.axhline(y=-1, color='r', linestyle='--')
plt.xlabel('Total Barrier Height (kJ/mol)')
plt.ylabel('Experimental logBB')
plt.title('Total Apical and Basolateral Barrier Height vs. Experimental logBB')
plt.savefig('barrier_vs_logBB.png')

plt.figure()
for k in molecules:
    x = apical_barriers[k]
    y = molecules[k]
    plt.scatter(x, y)
    plt.annotate(k, (x, y))

# Add a horizontal line at y=-1 to separate BBBP+ and BBBP-
# Molecules with logBB > -1 are considered to be BBBP+
plt.axhline(y=-1, color='r', linestyle='--')
plt.xlabel('Apical Barrier Height (kJ/mol)')
plt.ylabel('Experimental logBB')
plt.title('Apical Barrier Height vs. Experimental logBB')
plt.savefig('apical_barrier_vs_logBB.png')

plt.figure()
for k in molecules:
    x = basolateral_barriers[k]
    y = molecules[k]
    plt.scatter(x, y)
    plt.annotate(k, (x, y))

# Add a horizontal line at y=-1 to separate BBBP+ and BBBP-
# Molecules with logBB > -1 are considered to be BBBP+
plt.axhline(y=-1, color='r', linestyle='--')
plt.xlabel('Basolateral Barrier Height (kJ/mol)')
plt.ylabel('Experimental logBB')
plt.title('Basolateral Barrier Height vs. Experimental logBB')
plt.savefig('basolateral_barrier_vs_logBB.png')

plt.show()