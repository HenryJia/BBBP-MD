import pandas as pd

# Load the data
pos = pd.read_csv('bbbp_positive_pubchem.csv', comment=';') # colon for comments because # is already used
neg = pd.read_csv('bbbp_negative_pubchem.csv', comment=';')
print(pos.columns)

# Print all of the important columns
pd.set_option('display.max_colwidth', None)
print('Positive candidates:')
print(pos[['idx', 'InChIKey', 'SMILES', 'MolWt', 'LogP', 'BBB+', 'logBB']])
print('Negative candidates:')
print(neg[['idx', 'InChIKey', 'SMILES', 'MolWt', 'LogP', 'BBB+', 'logBB']])