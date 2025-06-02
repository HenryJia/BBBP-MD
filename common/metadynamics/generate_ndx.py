# Regenerate ndx file from the metadynamic.gro for gmx order

desired_atoms = {
    'SAPS': set(
        [
            'C21', 'C22', 'C23', 'C24', 'C25', 'C26', 'C27', 'C28', 'C29',
            'C210', 'C211', 'C212', 'C213', 'C214', 'C215', 'C216', 'C217', 'C218', 'C219', 'C220',
            'C31', 'C32', 'C33', 'C34', 'C35', 'C36', 'C37', 'C38', 'C39',
            'C310', 'C311', 'C312', 'C313', 'C314', 'C315', 'C316', 'C317', 'C318',
        ]
    ),
    'SAPC': set(
        [
            'C21', 'C22', 'C23', 'C24', 'C25', 'C26', 'C27', 'C28', 'C29',
            'C210', 'C211', 'C212', 'C213', 'C214', 'C215', 'C216', 'C217', 'C218', 'C219', 'C220',
            'C31', 'C32', 'C33', 'C34', 'C35', 'C36', 'C37', 'C38', 'C39',
            'C310', 'C311', 'C312', 'C313', 'C314', 'C315', 'C316', 'C317', 'C318',
        ]
    ),
    'POPC': set(
        [
            'C21', 'C22', 'C23', 'C24', 'C25', 'C26', 'C27', 'C28', 'C29',
            'C210', 'C211', 'C212', 'C213', 'C214', 'C215', 'C216', 'C217', 'C218',
            'C31', 'C32', 'C33', 'C34', 'C35', 'C36', 'C37', 'C38', 'C39',
            'C310', 'C311', 'C312', 'C313', 'C314', 'C315', 'C316',
        ]
    ),
    'CHL1': set(
        [
            'C20', 'C21', 'C22', 'C23', 'C24', 'C25', 'C26', 'C27',
        ]
    ),
    'OSM': set(
        [
            'C1F', 'C2F', 'C3F', 'C4F', 'C5F', 'C6F', 'C7F', 'C8F', 'C9F', 'C10F',
            'C11F', 'C12F', 'C13F', 'C14F', 'C15F', 'C16F', 'C17F', 'C18F',
            'C1S', 'C2S', 'C3S', 'C4S', 'C5S', 'C6S', 'C7S', 'C8S', 'C9S', 'C10S',
            'C11S', 'C12S', 'C13S', 'C14S', 'C15S', 'C16S', 'C17S', 'C18S',
        ]
    ),
    'SAPE': set(
        [
            'C21', 'C22', 'C23', 'C24', 'C25', 'C26', 'C27', 'C28', 'C29',
            'C210', 'C211', 'C212', 'C213', 'C214', 'C215', 'C216', 'C217', 'C218', 'C219', 'C220',
            'C31', 'C32', 'C33', 'C34', 'C35', 'C36', 'C37', 'C38', 'C39',
            'C310', 'C311', 'C312', 'C313', 'C314', 'C315', 'C316', 'C317', 'C318',
        ]
    ),
    'SOPE': set(
        [
            'C21', 'C22', 'C23', 'C24', 'C25', 'C26', 'C27', 'C28', 'C29',
            'C210', 'C211', 'C212', 'C213', 'C214', 'C215', 'C216', 'C217', 'C218',
            'C31', 'C32', 'C33', 'C34', 'C35', 'C36', 'C37', 'C38', 'C39',
            'C310', 'C311', 'C312', 'C313', 'C314', 'C315', 'C316', 'C317', 'C318',
        ]
    ),
    'SAPI': set(
        [
            'C21', 'C22', 'C23', 'C24', 'C25', 'C26', 'C27', 'C28', 'C29',
            'C210', 'C211', 'C212', 'C213', 'C214', 'C215', 'C216', 'C217', 'C218', 'C219', 'C220',
            'C31', 'C32', 'C33', 'C34', 'C35', 'C36', 'C37', 'C38', 'C39',
            'C310', 'C311', 'C312', 'C313', 'C314', 'C315', 'C316', 'C317', 'C318',
        ]
    ),
    'SLPC': set(
        [
            'C21', 'C22', 'C23', 'C24', 'C25', 'C26', 'C27', 'C28', 'C29',
            'C210', 'C211', 'C212', 'C213', 'C214', 'C215', 'C216', 'C217', 'C218',
            'C31', 'C32', 'C33', 'C34', 'C35', 'C36', 'C37', 'C38', 'C39',
            'C310', 'C311', 'C312', 'C313', 'C314', 'C315', 'C316', 'C317', 'C318',
        ]
    ),
}

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
    for key in desired_atoms:
        for atom in desired_atoms[key]:
            f.write(f'[ {key} {atom}]\n')
            atom_str = re.findall(r'\d+'+ key +'\s+'+ atom + '.{4}\d\s', gro)
            #print(atom_str)
            atom_num = [str(int(a[-6:])) for a in atom_str]

            print(f'Found {len(atom_num)} {key} {atom} atoms for gmx order')

            for i, a in enumerate(atom_num):
                f.write(f'{a}\t')
                if ((i + 1) % 15 == 0):
                    f.write('\n')
            f.write('\n')
