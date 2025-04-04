import os
import tarfile
import pandas as pd

# Load the data
pos_cand = pd.read_csv('bbbp_positive_pubchem.csv', comment=';') # colon for comments because # is already used
neg_cand = pd.read_csv('bbbp_negative_pubchem.csv', comment=';')

# Quick way of checking if the atom specifications are already in the charmm36 section
def compare(atoms, lines1, section):
    predefined_section = None
    for nline in lines1:
        if nline.startswith('['):
            predefined_section = nline.strip()
            continue
        if predefined_section != section:
            continue

        predefined = nline.strip().split()[0:len(atoms)]
        if atoms == predefined:
            return True
    return False

def process_candidate(cid, root_dir):
    # Process a candidate molecule for metadynamics.

    # Step 1: Extract the files we want from the tarball produced by Charmm-GUI
    charmmgui = tarfile.open(f'{root_dir}/{cid}/charmm-gui.tgz', 'r')

    # We want the itp and pdb files. We need the pdb files so we can run gmx insert-molecule
    # and we want the itp files so we can run gmx grompp
    # Note that charmm-gui's tar file has their job id for the directory name annoying, so find this
    filelist = charmmgui.getmembers()
    itp_files = [f for f in filelist if f.name.endswith('.itp')]
    pdb_files = [f for f in filelist if f.name.endswith('.pdb')]
    print(f'Found itp files: {itp_files}')
    print(f'Found pdb files: {pdb_files}')

    # Now extract them
    if not os.path.exists(f'{root_dir}/{cid}/lig'):
        os.makedirs(f'{root_dir}/{cid}/lig')
    for f in itp_files:
        f.name = os.path.basename(f.name) # This seems hacky...
        charmmgui.extract(f, path=f'{root_dir}/{cid}/lig', filter='data')
    for f in pdb_files:
        f.name = os.path.basename(f.name)
        charmmgui.extract(f, path=f'{root_dir}/{cid}', filter='data')
    charmmgui.close()

    # Step 2: We now have to clean up the itp files by removing any duplicate lines with the Charmm36m forcefield
    # This is because Charmm-GUI adds the same lines that are already in the forcefield files we get separately    

    charmm36ff = '../metadynamics/charmm36-jul2022.ff'

    ffnonbonded = open(f'{charmm36ff}/ffnonbonded.itp', 'r')
    nonbonded_lines = ffnonbonded.readlines()
    ffnonbonded.close()

    ffbonded = open(f'{charmm36ff}/ffbonded.itp', 'r')
    bonded_lines = ffbonded.readlines()
    ffbonded.close()

    ffmdihedrals = open(f'{charmm36ff}/ffmissingdihedrals.itp', 'r')
    missing_dihedrals_lines = ffmdihedrals.readlines()
    ffmdihedrals.close()

    lig_charmm36 = f'{root_dir}/{cid}/lig/charmm36.itp'
    f_lig = open(lig_charmm36, 'r')
    lines = f_lig.readlines()
    f_lig.close()
    # Comment out the lines that are already in the forcefield files
    section = None
    for i, line in enumerate(lines):
        if line.startswith(';') or line == '\n':
            continue

        if line.startswith('['):
            section = line.strip()
            if section != '[ defaults ]':
                continue

        # Everything in the [ defaults ] section is already in the forcefield files
        if section == '[ defaults ]':
            lines[i] = f'; {line}'
            continue

        if section == '[ atomtypes ]':
            atomtype = line.strip().split()[0:1]
            if compare(atomtype, nonbonded_lines, section):
                lines[i] = f'; {line}'
                continue

        if section == '[ bondtypes ]':
            bondtype = line.strip().split()[0:2]
            if compare(bondtype, bonded_lines, section) or compare(bondtype[::-1], bonded_lines, section):
                lines[i] = f'; {line}'
                continue

        if section == '[ pairtypes ]':
            pairtype = line.strip().split()[0:2]
            if compare(pairtype, nonbonded_lines, section):
                lines[i] = f'; {line}'
                continue

        if section == '[ angletypes ]':
            angletype = line.strip().split()[0:3]
            if compare(angletype, bonded_lines, section) or compare(angletype[::-1], bonded_lines, section):
                lines[i] = f'; {line}'
                continue

        if section == '[ dihedraltypes ]':
            dihedraltype = line.strip().split()[0:4]
            dihedral_lines = missing_dihedrals_lines + bonded_lines
            if compare(dihedraltype, dihedral_lines, section) or compare(dihedraltype[::-1], dihedral_lines, section):
                lines[i] = f'; {line}'
                continue

    # For testing, just print the lines
    # for i, line in enumerate(lines):
    #     print(line, end='')

    # Write the lines to the file
    f_lig = open(lig_charmm36, 'w')
    f_lig.writelines(lines)
    f_lig.close()
    print(f'Wrote {lig_charmm36}')



if __name__ == '__main__':
    # Process the positive candidates
    for i, row in pos_cand.iterrows():
        cid = row['idx']
        print(f'Processing Positive Candidate {cid}')
        process_candidate(cid, 'pos')
        exit() # Just for testing

    # # Process the negative candidates
    # for i, row in neg_cand.iterrows():
    #     cid = row['idx']
    #     print(f'Processing Negative Candidate {cid}')
    #     process_candidate(cid, 'neg')