import numpy as np
import pandas as pd
from rdkit import Chem
import itertools
import networkx as nx
from . import mol_tree as mt



# Obtaining the list of vocabulary for a data set 
def Vocabulary(data):
    cset=set()
    for m in data:
        mol=mt.MolTree(m)
        for c in mol.nodes:
            cset.add(c.smiles)
    return cset


# Creating dictionary for vocab/categorical  
def Vocab2Cat(vocabset):
    vocab=list(vocabset)
    chars=list(np.arange(len(vocabset)))
    MolDict=dict(zip(vocab,chars))
    return MolDict


# Obtaining the clusters for moles in the training set 
def Clusters(data):
    clusters=[]
    for m in data:
        c=[] #using c for clusters
        tree=mt.MolTree(m)
        for node in tree.nodes:
            c.append(node.smiles)
        clusters.append(c)
    return clusters


# For parallelizing the cluster generation for each molecule
def SingleCluster(smile):
    c=[]
    tree=mt.MolTree(smile)
    for node in tree.nodes:
        c.append(node.smiles)
    return c


# Turning each set of clusters for each molecule into categorical labels
def Cluster2Cat(clusters,MolDict):
    cat=[]
    for cluster in clusters:
        l=[]
        for c in cluster:
            l.append(MolDict[c])
        cat.append(l)
    return cat

# For parallelizing the cluster to categorical label conversion
def SingleCluster2Cat(args):
    cluster, MolDict = args
    l=[]
    for c in cluster:
        if c in MolDict:
            l.append(MolDict[c])
    return l


# Creating vector descriptions from one hot encoded labels of clusters
# size is the number of categorical labels
def Vectorize(catdata,size):
    vectors=[]
    for c in catdata:
        c0=np.array(c).astype(int)
        b=np.zeros((len(c0),size))
        b[np.arange(len(c0)),c0]=1
        b1=b.sum(axis=0)
        vectors.append(b1)
    return vectors

# For parallelizing the vectorization of the categorical labels
def SingleVectorize(args):
    c, size = args
    c0 = np.array(c).astype(int)
    b = np.zeros((len(c0), size))
    b[np.arange(len(c0)), c0] = 1
    b1 = b.sum(axis=0)
    return b1


# Decomposes a list of molecules in smiles into cliques and returns a clique decompostion dataframe and the list of cliques
def get_clique_decomposition(mol_smiles, outputs=None, output_name='output'):
    # Generating Cliques
    vocab=Vocabulary(mol_smiles)
    size=len(vocab)
    vocabl = list(vocab)
    MolDict=Vocab2Cat(vocab)
    clustersTR=Clusters(mol_smiles)
    catTR=Cluster2Cat(clustersTR,MolDict)
    clique_decomposition=Vectorize(catTR,size)

    descriptors_df = pd.DataFrame(data=clique_decomposition, columns = [x for x in range(len(vocabl))])

    if (outputs != None):
        descriptors_df[output_name] = outputs

    return descriptors_df, vocabl

# For parallelizing the clique decomposition
def SingleCliqueDecomposition(mol_smiles, vocab, mol_dict):
    assert type(vocab) == list, "Vocab must be a list"
    size = len(vocab)
    clusters = SingleCluster(mol_smiles)
    cat = SingleCluster2Cat((clusters, mol_dict))
    clique_decomposition = SingleVectorize((cat, size))
    clique_decomposition = pd.Series(data=clique_decomposition, index=vocab)
    clique_decomposition = clique_decomposition.clip(0, 255).astype(np.uint8)
    #clique_decomposition = pd.DataFrame(data=clique_decomposition, columns = [v for v in vocab], index=[index])
    return clique_decomposition
