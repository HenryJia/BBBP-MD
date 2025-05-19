# Regenerate ndx file from the metadynamic.gro
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
    f.write('[ MEMB ]\n')
    for i in range(membrane_start, membrane_end + 1):
        f.write(f'{i}\t')
        if (i % 15 == 0):
            f.write('\n')
    f.write('\n')

    f.write('[ SOLV ]\n')
    for i in range(membrane_end + 1, int(atom_num[0])):
        f.write(f'{i}\t')
        if (i % 15 == 0):
            f.write('\n')
    f.write('\n')

    f.write('[ LIGAND ]\n')
    for i in range(int(atom_num[0]), int(atom_num[-1]) + 1):
        f.write(f'{i}\t')
        if (i % 15 == 0):
            f.write('\n')
    f.write('\n')

    f.write('[ SYSTEM ]\n')
    for i in range(1, int(atom_num[-1]) + 1):
        f.write(f'{i}\t')
        if (i % 15 == 0):
            f.write('\n')
    f.write('\n')

