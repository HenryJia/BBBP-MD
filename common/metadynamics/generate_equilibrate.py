import re

# Load template file
with open('./equilibrate_template.dat', 'r') as f:
    equilibrate = f.read()

with open('./ini_com_template.dat', 'r') as f:
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
with open('equilibrate2.dat', 'w') as f:
    f.write('RESTART\n' + equilibrate.format(lig=str(atom_num[0]) + '-' + str(atom_num[-1])))
with open('ini_com.dat', 'w') as f:
    f.write(ini_com.format(lig=str(atom_num[0]) + '-' + str(atom_num[-1])))

# Since the reviewers asked us to simulate with other locations, we now need to jank our way into updating the restraint locations
# When the locations are not the centre, we'll use a different named location file
from pathlib import Path
import subprocess

if not Path("./location.dat").is_file():
    fn = list(Path("./").glob("location*dat"))[0]
    with open(fn) as f:
        location = f.readline()
        location = re.sub("\s+", ",", location.strip())

        subprocess.call(['sed', '-i', 's/3.4,3.4,16.5/'+location+'/g', 'equilibrate.dat', 'equilibrate2.dat'])

