import sys
import re
import argparse

# Parse command line arguments
parser = argparse.ArgumentParser(description='Generate Plumed 2.8 configuration file for steered MD')
parser.add_argument('--equilibrate-template', type=str, help='Template file for Plumed configuration')
parser.add_argument('--initial-template', type=str, help='Template file for Plumed configuration')
parser.add_argument('--output', type=str, help='Output file for Plumed configuration')
parser.add_argument('--setup', type=str, help='Setup gro file for Plumed configuration')
parser.add_argument('--force', type=str, help='Force constant for pulling in kJ/(mol nm^2)', default=500)
parser.add_argument('--start_z', type=float, help='Starting z coordinate for initial pull', default=8.0)
parser.add_argument('--end_z', type=float, help='Ending z coordinate for initial pull', default=1.0)
parser.add_argument('--initial_time', type=int, help='Initial time for pulling in ps', default=14) # This gives us 0.5 nm/ns by default
#parser.add_argument('--num_umbrellas', type=int, help='Number of umbrellas to use', default=32)

args = parser.parse_args()

def main(args):
    print(f'Generating Plumed configuration file for steered MD with the following arguments: {args}')

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

    # Must provide exactly one of initial template or equilibrate template
    assert args.initial_template or args.equilibrate_template, 'Must provide exactly one of initial template or equilibrate template'
    if args.initial_template:
        with open(args.initial_template, 'r') as f:
            initial_template = f.read()
        output_dat = initial_template.format(
            atoms='-'.join([atom_num[0], atom_num[-1]]),
            force=args.force,
            start_z=args.start_z,
            end_z=args.end_z,
            time=args.initial_time * 1000, # Convert to ps
        )
    if args.equilibrate_template:
        assert not args.initial_template, 'Cannot use both initial and equilibrate templates'
        with open(args.equilibrate_template, 'r') as f:
            equilibrate_template = f.read()
        output_dat = equilibrate_template.format(
            atoms='-'.join([atom_num[0], atom_num[-1]]),
        )

    with open(args.output, 'w') as f:
        f.write(output_dat)

# If no arguments are provided, use our hardcoded values
# example: python generate_plumed.py --template smd_template.dat --output ../../basolateral/charmm-gui-2960967181-nacl-charmm36/gromacs/caffeine/smd_vfast.dat --setup ../../basolateral/charmm-gui-2960967181-nacl-charmm36/gromacs/caffeine/setup.gro --force 1000 --speed 4 --name vfast 
if len(sys.argv) == 1:
    membranes = ['../../apical/charmm-gui-2960669761-charmm36-nacl/gromacs/', '../../basolateral/charmm-gui-2960967181-nacl-charmm36/gromacs/']
    templates = [('umbrella_initial_template.dat', 'umbrella_initial.dat')]
    molecules = ['trihexyphenidyl', 'isopropanol', 'caffeine', 'morphine-6-glucuronide', 'sucrose']
    args.force = 250

    for membrane in membranes:
        for molecule in molecules:
                for t, output in templates:
                    args.initial_template = t
                    args.output = membrane + molecule + '/' + output
                    args.setup = membrane + molecule + '/setup.gro'
                    main(args)
else:
    main(args)
