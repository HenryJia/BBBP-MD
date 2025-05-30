# Regenerate ndx file from the metadynamic.gro for gmx order

SAPS_C = set(
    [
        'C21', 'C22', 'C23', 'C24', 'C25', 'C26', 'C27', 'C28', 'C29',
        'C210', 'C211', 'C212', 'C213', 'C214', 'C215', 'C216', 'C217', 'C218', 'C219', 'C220',
        'C31', 'C32', 'C33', 'C34', 'C35', 'C36', 'C37', 'C38', 'C39',
        'C310', 'C311', 'C312', 'C313', 'C314', 'C315', 'C316', 'C317', 'C318',
    ]
)
SAPC_C = set(
    [
        'C21', 'C22', 'C23', 'C24', 'C25', 'C26', 'C27', 'C28', 'C29',
        'C210', 'C211', 'C212', 'C213', 'C214', 'C215', 'C216', 'C217', 'C218', 'C219', 'C220',
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
    for atom in SAPS_C:
        f.write(f'[ SAPS {atom}]\n')
        atom_str = re.findall(r'\d+SAPS\s+'+ atom + '\s+\d+', gro)
        atom_num = [str(int(a[-5:])) for a in atom_str]

        print(f'Found {len(atom_num)} SAPS {atom} atoms for gmx order')

        for i, a in enumerate(atom_num):
            f.write(f'{a}\t')
            if ((i + 1) % 15 == 0):
                f.write('\n')
        f.write('\n')

    for atom in SAPC_C:
        f.write(f'[ SAPC {atom}]\n')
        atom_str = re.findall(r'\d+SAPC\s+'+ atom + '\s+\d+', gro)
        atom_num = [str(int(a[-5:])) for a in atom_str]

        print(f'Found {len(atom_num)} SAPC {atom} atoms for gmx order')

        for i, a in enumerate(atom_num):
            f.write(f'{a}\t')
            if ((i + 1) % 15 == 0):
                f.write('\n')
        f.write('\n')
