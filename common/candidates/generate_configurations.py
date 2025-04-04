import pandas as pd

# Load the data
pos_cand = pd.read_csv('bbbp_positive_pubchem.csv')
neg_cand = pd.read_csv('bbbp_negative_pubchem.csv')

def process_candidate(cid):
    # Process a candidate molecule for metadynamics.

    # Step 1: Extract the tarball from Charmm-GUI
