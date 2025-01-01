import sys
import re
import argparse

# Parse command line arguments
parser = argparse.ArgumentParser(description='Generate Plumed 2.8 configuration file for steered MD')
parser.add_argument('--template', type=str, help='Template file for Plumed configuration')
parser.add_argument('--output', type=str, help='Output file for Plumed configuration')
parser.add_argument('--setup', type=str, help='Setup gro file for Plumed configuration')
parser.add_argument('--force', type=str, help='Force constant for pulling in kJ/(mol nm^2)', default=1000)
parser.add_argument('--speed', type=int, help='Pulling speed for pulling in nm/ns', default=2)
parser.add_argument('--name', type=str, help='Name to use for output data in PLUMED configuration')

args = parser.parse_args()

def main(args):
    print(f'Generating Plumed configuration file for steered MD with the following arguments: {args}')
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

# If no arguments are provided, use our hardcoded values
# example: python generate_plumed.py --template smd_template.dat --output ../../basolateral/charmm-gui-2960967181-nacl-charmm36/gromacs/caffeine/smd_vfast.dat --setup ../../basolateral/charmm-gui-2960967181-nacl-charmm36/gromacs/caffeine/setup.gro --force 1000 --speed 4 --name vfast 
if len(sys.argv) == 1:
    membranes = ['../../apical/charmm-gui-2960669761-charmm36-nacl/gromacs/', '../../basolateral/charmm-gui-2960967181-nacl-charmm36/gromacs/']
    templates = [('equilibrate_template.dat', 'equilibrate_plumed.dat'), ('smd_template.dat', 'smd_{name}.dat')]
    molecules = ['trihexyphenidyl', 'isopropanol', 'caffeine', 'morphine-6-glucuronide', 'sucrose']
    args.force = 1000
    speed = [(0.5, 'vslow'), (1, 'slow'), (2, 'fast'), (4, 'vfast')]

    for membrane in membranes:
        for molecule in molecules:
            for s, name in speed:
                for t, output in templates:
                    args.template = t
                    args.output = membrane + molecule + '/' + output.format(name=name)
                    args.setup = membrane + molecule + '/setup.gro'
                    args.speed = s
                    args.name = name
                    main(args)
else:
    main(args)
