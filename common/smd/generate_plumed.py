import os
import re
import argparse

# Parse command line arguments
parser = argparse.ArgumentParser(description='Generate Plumed 2.8 configuration file for steered MD')
parser.add_argument('--template', type=str, required=True, help='Template file for Plumed configuration')
parser.add_argument('--output', type=str, required=True, help='Output file for Plumed configuration')
parser.add_argument('--setup', type=str, required=True, help='Setup gro file for Plumed configuration')
parser.add_argument('--force', type=str, help='Force constant for pulling in kJ/(mol nm^2)', default=1000)
parser.add_argument('--speed', type=int, help='Pulling speed for pulling in nm/ns', default=2)
parser.add_argument('--name', type=str, help='Name to use for output data in PLUMED configuration')

args = parser.parse_args()

# Set up some constants
box_height = 7 # nm

# Load template file
with open(args.template, 'r') as f:
    template = f.read()

# Load setup gro file
with open(args.setup, 'r') as f:
    gro = f.read()

# Find the atom numbers for the ligand we want to do steered MD on
# Easiest way to do this is probably using regex on the gro file
# The gro file is formatted like this:
# 7072LIG      O42774   3.567   3.601   8.056
# We want to find the atom numbers for the LIG atoms, in this it's 42774
atom_str = re.findall(r'\d+LIG\s+[A-Z]+\d+', gro)
atom_num = [a[-5:] for a in atom_str]
print(f'Atom strings: {atom_str}')
print(f'Found atom numbers: {atom_num}')

time_period = box_height / (args.speed / 2) * 1000 # ps
time_period = round(time_period)

if 'smd' in args.template:
    output_dat = template.format(
        atoms='-'.join([atom_num[0], atom_num[-1]]),
        period=time_period,
        force=args.force,
        name=args.name
    )
elif 'equilibrate' in args.template:
    output_dat = template.format(
        atoms='-'.join([atom_num[0], atom_num[-1]]),
    )
else:
    raise ValueError('Template file must be for SMD or equilibration')

with open(args.output, 'w') as f:
    f.write(output_dat)