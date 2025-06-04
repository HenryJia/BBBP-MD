import re, os

smac_atoms = {
    'SAPS': ('C21', 'C220'),
    'SAPC': ('C21', 'C220'),
    'POPC': ('C21', 'C218'),
    'CHL1': ('C20', 'C27'),
    'OSM': ('C1F', 'C18F'),
    'SAPE': ('C21', 'C220'),
    'SOPE': ('C21', 'C218'),
    'SAPI': ('C21', 'C220'),
    'SLPC': ('C21', 'C218'),
}
max_lipids = 96 * 2  # Maximum number of lipids in the membrane


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

with open('com_membrane_template.dat', 'r') as f:
    com_membrane = f.read()

with open('com_position.txt', 'r') as f:
    com = f.read().split('\n')[-2].split()[1:]

# Load the scaled components from the plumed driver output
with open('com_membrane.dat', 'w') as f:
    f.write(com_membrane.format(
        membrane=str(membrane_start) + '-' + str(membrane_end)
    ))

if os.path.exists('com_membrane.txt'): # Once we have the com of the membrane, we can set up for SMAC
    with open('com_membrane.txt', 'r') as f:
        com_mem = f.read().split('\n')[-2].strip().split(' ')[1:]
    com_mem = [float(c) for c in com_mem]

    mols = ''
    below = 0
    for i in range(1, max_lipids + 1):
        # Note: We could probably do all of this in one regex, but it's clearer to split it up
        # Step 1: Find our desired lipid type in the gro file
        str_lipid = re.findall(r'^\s*' + str(i) + r'[A-Z]+.+$', gro, re.MULTILINE)
        str_lipid = '\n'.join(str_lipid)

        # Step 2: Get the lipid type
        lipid_type = re.match(r'^\s*'+ str(i) + r'(' + '|'.join(smac_atoms.keys()) + r')\s+', str_lipid)
        lipid_type = lipid_type.group(1)

        # Step 3: Get the atom numbers we want, and the Z coordinate
        # We need this to figure out the "direction" of the lipid in the membrane
        atoms = []
        z_mean = 0.0
        for a in smac_atoms[lipid_type]:
            atom = re.search( # Note we need a lookbehind assertion to ensure we start matching the atom number after the 15th character
                r'^\s*' + str(i) + lipid_type + r'\s*' + a + '(?<=^.{15})' + \
                r'\s*(\d+)\s*([+-]?\d+[.]\d+)\s*([+-]?\d+[.]\d+)\s*([+-]?\d+[.]\d+)$',
                str_lipid, re.MULTILINE)
            assert atom is not None, f'Could not find atom {a} in lipid {i} of type {lipid_type}\n{str_lipid}'
            atoms += [atom.group(1)]
            z_mean += float(atom.group(4)) / len(smac_atoms[lipid_type])

        if z_mean < com_mem[2]:
            print('Lipid ', i, 'of type', lipid_type, 'is below the COM of the membrane at', com_mem[2], 'z_mean:', z_mean)
            atoms = atoms[::-1] # Reverse the order of the atoms if the lipid is below the COM of the membrane
            below += 1
        else:
            print('Lipid ', i, 'of type', lipid_type, 'is above the COM of the membrane at', com_mem[2], 'z_mean:', z_mean)
        atoms += [atoms[0]] # We need the first atom at the end if we're going by the angles vetween vectors of atom pairs

        # Step 4: Generate the SMAC string for this lipid
        mols += f'  MOL{i}={atoms[0]},{atoms[1]},{atoms[2]}\n'
    
    print('Total lipids below the COM:', below, 'out of', max_lipids)
    print(mols)

    with open('smac_template.dat', 'r') as f:
        smac = f.read()
 
    with open('smac.dat', 'w') as f:
        f.write(smac.format(
            lig=str(atom_num[0]) + '-' + str(atom_num[-1]),
            membrane=str(membrane_start) + '-' + str(membrane_end),
            mem_lipids=mols,
        ))

