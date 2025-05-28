# Regenerate ndx file from the metadynamic.gro for gmx order

SAPS_C = set(
    [
        'C31', 'C32', 'C33', 'C34', 'C35', 'C36', 'C37', 'C38', 'C39',
        'C310', 'C311', 'C312', 'C313', 'C314', 'C315', 'C316', 'C317', 'C318',
    ]
)

import re


# Load index file
with open('index.ndx', 'r') as f:
    ndx = f.read()

# Load setup gro file
with open('setup.gro', 'r') as f:
    gro = f.read()

# Find the membrane atom numbers using the ndx file
# This should be much easier than using the gro file
# In the index file, the first block are the membrane atoms
# So we take the first and last atom numbers from that block
membrane_start = int(ndx.split('\n')[1].split()[0])
membrane_end = 0
for line in ndx.split('\n')[1:]:
    if line == '':
        break
    else:
        membrane_end = int(line.split()[-1])

# Find the atom numbers for the ligand we want to do steered MD on
# Easiest way to do this is probably using regex on the gro file
# The gro file is formatted like this:
# 7072LIG      O42774   3.567   3.601   8.056
# We want to find the atom numbers for the LIG atoms, in this it's 42774
atom_str = re.findall(r'\d+LIG\s+[A-Z]+\d+', gro)
atom_num = [a[-5:] for a in atom_str]

with open('index_local.ndx', 'w') as f:
    f.write('[ SAPS ]\n')
    atom_num = []
    for atom in SAPS_C:
        atom_str = re.findall(r'\d+SAPS\s+'+ atom + '\s+\d+', gro)
        atom_num += [str(int(a[-5:])) for a in atom_str]

    for a in atom_num:
        f.write(f'{a}\t')
        if (i % 15 == 0):
            f.write('\n')
    f.write('\n')