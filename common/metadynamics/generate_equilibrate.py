import re

# Load template file
with open('./equilibrate_template.dat', 'r') as f:
    equilibrate = f.read()

with open(args.ini_com, 'r') as f:
    ini_com = f.read()

with open('setup.gro', 'r') as f:
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

with open('equilibrate.dat', 'w') as f:
    f.write(equilibrate.format(lig=str(atom_num[0]) + '-' + str(atom_num[-1])))

with open('ini_com.dat', 'w') as f:
    f.write(ini_com.format(lig=str(atom_num[0]) + '-' + str(atom_num[-1])))