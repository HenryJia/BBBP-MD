# Generate Plumed 2.8 configuration file for Jarzynski sampling
import os
import re
import argparse
import numpy as np
import pandas as pd
from sklearn.kernel_ridge import KernelRidge
from sklearn.svm import SVR
from sklearn.neural_network import MLPRegressor
from sklearn.metrics import root_mean_squared_error
from sklearn.model_selection import KFold

import matplotlib.pyplot as plt

# Parse command line arguments
parser = argparse.ArgumentParser(description='Generate Plumed 2.8 configuration file for Jarzynski sampling')
parser.add_argument('--fe', type=str, nargs='+', help='Free energy file(s) in Plumed output format')
parser.add_argument('--cv', type=str, nargs='+', help='Collective variable file in Plumed output format')
parser.add_argument('--template', type=str, required=True, help='Template file for Plumed configuration')
parser.add_argument('--previous', type=str, required=True, help='A previous Plumed configuration file for us to pull the CVs from')
parser.add_argument('--output', type=str, required=True, help='Output file for Plumed configuration')

args = parser.parse_args()

assert hasattr(args, 'fe') or hasattr(args, 'cv'), 'Either --fe or --cv must be specified'

avogadro = 6.02214076e23 # Avogadro's number<
k_B = 1.38064852e-23 # Boltzmann constant in J/K
T = 310 # Simulation temperature in K (also human body temperature)

# Load free energy data
if args.fe:
    print('Loading free energy data...')
    z = []
    fe = []
    names = []
    for f in args.fe:
        data = pd.read_csv(f, sep='\\s+', comment='#', header=None)
        z.append(data[0].values)
        fe.append(data[1].values)
        names.append(os.path.splitext(os.path.basename(f))[0])
else:
    print('Loading collective variable data...')
    z = []
    fe = []
    names = []
    for f in args.cv:
        data = pd.read_csv(f, sep='\\s+', comment='#', header=None)
        z.append(data[4].values)
        fe.append(data[7].values)
        names.append(os.path.splitext(os.path.basename(f))[0])

z = np.stack(z, axis=0)
fe = np.stack(fe, axis=0)
# Do the preprocessing
# Get rid of the edge points by capping the free energy
if args.fe:
    fe[z < 1.0] = np.max(fe[(z > 1.0) * (z < 1.5)])
    fe[z > 8.0] = np.max(fe[(z > 7.5) * (z < 8.0)])
    fe = -fe # I think the free energy is negated in the Plumed output...

# Smooth the free energy using a kernel ridge regression
# I'm not entirely convinced this is necessary, but it's what the authors did
# So we'll do it too for now...
# We do this independently for each FE profile
print('Smoothing free energy profiles with kernel ridge regression...')
grid = np.linspace(0, 10, 10000)
fe_smooth = np.zeros((fe.shape[0], grid.shape[0]))
for i in range(fe.shape[0]):
    # Use a kernel ridge regression model
    model = KernelRidge(kernel='rbf', alpha=0.1)
    model.fit(z[i, :, None], fe[i, :])
    fe_smooth[i, :] = model.predict(grid[:, None])
    #model = SVR(kernel='rbf', C=1, gamma=0.1)
    #model.fit(z[i, :, None], fe[i, :])
    #fe_smooth[i, :] = model.predict(grid[:, None])

# Plot the free energy profiles
plt.figure()
for i in range(fe.shape[0]):
    plt.scatter(z[i], fe[i], label='FE ' + names[i])
    plt.plot(grid, fe_smooth[i, :], label='FE ' + names[i] + ' smooth')
plt.legend()
plt.xlabel('z')
plt.ylabel('Free energy (kJ/mol)')
plt.savefig('fe_kr.png')

# I'm not entirely sure why the authorse subtract the variance divided by 2k_BT
# but we'll do it too and see what happens
fe_smooth = np.mean(fe_smooth, axis=0)
#if args.cv:
    #fe_smooth = fe_smooth - k_B * T * avogadro * np.var(fe_smooth, axis=0)/(2.0*k_B*T)
#fe_smooth -= np.max(fe_smooth)

# Fit a neural network to the free energy profile
# We'll use a 5-fold cross-validation to give us an idea of the error
print('Fitting neural network to smoothed free energy profile...')
kf = KFold(n_splits=5)
rmse = []
n_hidden = 20
for train_index, test_index in kf.split(fe_smooth):
    # Fit a neural network to the free energy profile with a single hidden layer of 10 neurons
    # This is to keep the model as simple as possible
    model = MLPRegressor(hidden_layer_sizes=(n_hidden,), activation='tanh',
                         max_iter=10000, alpha=0, solver='adam',
                         early_stopping=False, tol=1e-9)
    model.fit(grid[train_index, None], fe_smooth[train_index])
    fe_pred = model.predict(grid[test_index, None])
    rmse.append(root_mean_squared_error(fe_smooth[test_index], fe_pred))

# Print the RMSE
print('RMSE: ', np.mean(rmse), '+/-', np.std(rmse))

# Final fit
model = MLPRegressor(hidden_layer_sizes=(n_hidden,), activation='tanh',
                    max_iter=10000, alpha=0, solver='adam',
                    early_stopping=False, tol=1e-9)
model.fit(grid[:, None], fe_smooth)
fe_pred = model.predict(grid[:, None])

# Plot the free energy profile and the neural network fit
plt.figure()
plt.plot(grid, fe_smooth, label='Mean FE Kernel Ridge')
plt.plot(grid, fe_pred, label='FE Neural Network')
plt.legend()
plt.xlabel('z')
plt.ylabel('Free energy (kJ/mol)')
plt.savefig('fe_fit.png')

print('Writing Plumed configuration file...')
template = open(args.template, 'r').read()

# Load the previous Plumed configuration file
previous = open(args.previous, 'r').read()

atoms = re.search(r'(c: COM ATOMS=)(\d+-\d+)', previous).group(2)

output_plumed = template.format(
    atoms=atoms,
    n_hidden=n_hidden,
    weights_0=','.join([str(w) for w in model.coefs_[0].flatten().tolist()]),
    biases_0=','.join([str(w) for w in model.intercepts_[0].flatten().tolist()]),
    weights_1=','.join([str(w) for w in model.coefs_[1].flatten().tolist()]),
    biases_1=model.intercepts_[1].item(),
)
print(output_plumed)

with open(args.output, 'w') as f:
    f.write(output_plumed)

plt.show()