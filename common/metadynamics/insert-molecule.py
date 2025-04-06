import subprocess
import os

# Step 1, run the insert-molecule.sh script
subprocess.run(['sh', 'insert-molecule.sh'])

assert os.path.exists('setup.gro') # Check if the setup.gro file was created

# Step 2, update the topology file using the gro files
with open('setup.gro', 'r') as f:
    setup_lines = f.readlines()

with open('topol.top', 'r') as f:
    topol_lines = f.readlines()

num_tip3 = 0
for i, lines in enumerate(setup_lines[::-1]):
    if 'TIP3' in lines.strip():
        num_tip3 = int(lines.split('TIP3')[0].strip())
        break
print(f'Number of TIP3P water molecules: {num_tip3}')

for i, lines in enumerate(topol_lines):
    if lines.startswith('TIP3'):
        topol_lines[i] = f'TIP3P  \t{num_tip3}\n'
        break

topol_lines += ['LIG  \t1\n']
with open('topol.top', 'w') as f:
    f.writelines(topol_lines)
print('Updated topology file with the number of TIP3P water molecules and added LIG 1')