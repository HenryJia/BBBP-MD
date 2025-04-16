import pandas as pd

# Load the data
pos = pd.read_csv('bbbp_positive_pubchem.csv', comment=';') # colon for comments because # is already used
neg = pd.read_csv('bbbp_negative_pubchem.csv', comment=';')

# Print all of the important columns
pd.set_option('display.max_colwidth', None)
print('Positive candidates:')
print(pos[['idx', 'InChIKey', 'SMILES', 'MolWt', 'LogP', 'BBB+', 'logBB']])
print('Negative candidates:')
print(neg[['idx', 'InChIKey', 'SMILES', 'MolWt', 'LogP', 'BBB+', 'logBB']])

# Also print the old candidates

old_pos = pd.read_csv('bbbp_positive_pubchem_old.csv', comment=';')
old_neg = pd.read_csv('bbbp_negative_pubchem_old.csv', comment=';')

print('Old positive candidates:')
print(old_pos[['idx', 'InChIKey', 'SMILES', 'MolWt', 'LogP', 'BBB+', 'logBB']])
print('Old negative candidates:')
print(old_neg[['idx', 'InChIKey', 'SMILES', 'MolWt', 'LogP', 'BBB+', 'logBB']])

