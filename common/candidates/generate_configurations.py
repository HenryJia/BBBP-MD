import os
import tarfile
import pandas as pd

# Load the data
pos_cand = pd.read_csv('bbbp_positive_pubchem.csv', comment=';') # colon for comments because # is already used
neg_cand = pd.read_csv('bbbp_negative_pubchem.csv', comment=';')

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
        charmmgui.extract(f, path=f'{root_dir}/{cid}/lig', filter='data')
    for f in pdb_files:
        charmmgui.extract(f, path=f'{root_dir}/{cid}', filter='data')
    charmmgui.close()

    # Step 2: We now have to clean up the itp files by removing any duplicate lines with the Charmm36m forcefield
    # This is because Charmm-GUI adds the same lines that are already in the forcefield files we get separately    

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