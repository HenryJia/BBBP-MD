import warnings
import shlex
import subprocess
import os
import pickle
import argparse

import numpy as np
import pandas as pd # for dataframe and CSV handling

import dask
import dask.dataframe as dd
from dask.distributed import Client, LocalCluster

#from mpi4py import MPI
#if MPI.COMM_WORLD.Get_rank() == 0:
#    with open("ssh_out.log", "wb") as ssh_log:
#        print('Starting SSH reverse tunnel on MPI Rank 0\n')
#        ssh_log.write('Starting SSH reverse tunnel on MPI Rank 0\n'.encode('utf-8'))
#        subprocess.Popen(shlex.split('ssh -o ExitOnForwardFailure=yes -f -N -R 0.0.0.0:8787:localhost:8787 henry@46.101.4.181'), stdout=ssh_log, stderr=ssh_log)

#from dask_mpi import initialize
#initialize(local_directory='/tmp', memory_limit=int(31418*10**6), dashboard=True, nthreads=1)

import rdkit.Chem.Descriptors as Descriptors
import rdkit.Chem as Chem

from tqdm import tqdm

from cliques import cliques as cl

heavy_atoms = {
    21, 22, 23, 24, 25, 26, 27, 28, 29, 31, 32, 33, 34,
    37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49,
    50, 51, 52, 55, 56, 57, 58, 59, 60, 61, 62, 63, 64,
    65, 66, 67, 68, 69, 70, 71, 72, 73, 74, 75, 76, 77,
    78, 79, 80, 81, 82, 83, 84, 85, 86, 87, 88, 89, 90,
    91, 92, 93, 94, 95, 96, 97, 98, 99, 100, 101, 102,
    103, 104, 105, 106, 107, 108, 109, 110, 111, 112, 113,
    114, 115, 116, 117, 118}

def filter_molecules(inchi):
    try:
        # First perform the same kind of filtering as B3DB and remove molecules with heavy atoms
        mol = Chem.MolFromInchi(inchi, sanitize=False, removeHs=False, logLevel=None)
        atom_list = [atom.GetAtomicNum() for atom in mol.GetAtoms()]
        if len(heavy_atoms.intersection(set(atom_list))) > 0:
            return False
        else:
            # Then, filter by molecular weight. Molecules with molecular weight > 1000 are removed
            # This is mainly computational, as the clique decomposition can be very slow for large molecules
            # This shouldn't affect our analysis much, since most BBBP+ molecules are small
            # Almost none of the molecules in the B3DB dataset have molecular weight > 1000
            return Descriptors.MolWt(mol) <= 1000
    except:
        return False

def filter_partition(partition):
    mask = []
    for idx, row in partition.iterrows():
        mask.append(filter_molecules(row['InChIID']))

    return partition[mask]

def compute_cliques(row, vocab, mol_dict):
    try:
        return cl.SingleCliqueDecomposition(row['SMILES'], vocab, mol_dict)
    except:
        return pd.Series([np.nan for _ in vocab], index=vocab)

def map_descriptors(partition, vocab, mol_dict):
    #output_df = pd.DataFrame(columns=list(partition.columns) + ['MolWt', 'LogP', 'SMILES'] + vocab)
    output = []
    for idx, row in partition.iterrows():
        try:
            mol = Chem.MolFromInchi(row['InChIID'], sanitize=False, removeHs=False, logLevel=None)
            molwt = Descriptors.MolWt(mol)
            logp = Descriptors.MolLogP(mol)
            smiles = Chem.MolToSmiles(mol)
            cliques = cl.SingleCliqueDecomposition(smiles, vocab, mol_dict)
            output_row = pd.concat([row, pd.Series({
                'MolWt': molwt,
                'LogP': logp,
                'SMILES': smiles,
            }), cliques])
        except:
            output_row = pd.concat([row, pd.Series({
                'MolWt': np.nan,
                'LogP': np.nan,
                'SMILES': '',
                **{v: np.nan for v in vocab}
            })])
        output.append(output_row)
    return pd.DataFrame(output, columns=list(partition.columns) + ['MolWt', 'LogP', 'SMILES'] + vocab, index=partition.index)   

if __name__ == '__main__':

    #dask.config.set(shuffle='disk')
    dask.config.set({'temporary_directory': './tmp'})

    #mp.set_start_method('forkserver')


    # Set up the argument parser
    parser = argparse.ArgumentParser(description='Process Pubchem data using the cliques descriptor')
    parser.add_argument('--vocab_data', type=str, help='Path to the Pubchem data file')
    parser.add_argument('--pubchem_data', type=str, help='Path to the Pubchem data file')
    parser.add_argument('--output_data', type=str, help='Path to the output directory')
    parser.add_argument('--n_jobs', type=int, default=8, help='Number of parallel jobs')
    parser.add_argument('--n_threads', type=int, default=8, help='Number of parallel jobs')
    parser.add_argument('--start', type=int, default=0, help='Start index for the data')
    parser.add_argument('--end', type=int, default=0, help='End index for the data, exclusive')
    parser.add_argument('--memory', type=str, default='2GB', help='memory per worker')
    parser.add_argument('--tunnel_port', type=int, default=8787, help='tunnel port to forward to')

    args = parser.parse_args()

    with open("ssh_out.log", "wb") as ssh_log:
        print('Starting SSH reverse tunnel on MPI Rank 0\n')
        ssh_log.write('Starting SSH reverse tunnel on MPI Rank 0\n'.encode('utf-8'))
        subprocess.Popen(shlex.split(f"ssh -o ExitOnForwardFailure=yes -f -N -R 0.0.0.0:{args.tunnel_port}:localhost:8787 henry@46.101.4.181"), stdout=ssh_log, stderr=ssh_log)

    # Set up the dask client
    print('Starting dask client')
    cluster = LocalCluster(threads_per_worker=args.n_threads, n_workers=args.n_jobs, memory_limit=args.memory)
    client = Client(cluster)
    #client = Client()
    print('Dask client started')
    print(client, client.dashboard_link)
    with open('dask_address.log', mode='wt') as f:
        f.write('Dask:' + str(client.dashboard_link) + '\n')

    # Set up the parallel pool. We'll keep this global and the same across all functions
    #mp_pool = mp.Pool(args.n_jobs)

    # Load the data
    print('Loading vocabulary data')
    if args.vocab_data.endswith('.parquet'):
        print('Loading vocabulary data from parquet')
        vocab_data = dd.read_parquet(args.vocab_data)
        print('Setting Index for vocabulary data')
        vocab_data.set_index('NO.')
    else:
        print('Loading vocabulary data from csv')
        vocab_data = dd.read_csv(args.vocab_data, sample_rows=1000)
        print('Setting Index for vocabulary data')
        vocab_data.set_index('NO.')
        print('Saving vocabulary data to parquet')
        assert args.vocab_data.endswith('.csv')
        args.vocab_data = args.vocab_data[:-4] + '.parquet'
        vocab_data.to_parquet(args.vocab_data)

    if args.pubchem_data.endswith('.parquet'):
        print('Loading NIH Pubchem data from parquet')
        pubchem_data = dd.read_parquet(args.pubchem_data)
        print('Setting Index for Pubchem data')
        #pubchem_data.set_index('idx')
    else:
        print('Loading NIH Pubchem data from csv')
        pubchem_data = dd.read_csv(args.pubchem_data, delimiter='\t', header=None, names=['idx', 'InChIID', 'InChIKey'])
        print('Setting Index for Pubchem data')
        pubchem_data.set_index('idx')

        # Filter the data in the same way as the B3DB data
        print('Filtering Pubchem data')
        len_before = len(pubchem_data)
        #filter = pubchem_data.apply(lambda row: filter_molecules(row['InChIID']), axis=1, meta=('filter', 'bool'))
        #pubchem_data = pubchem_data[filter]
        pubchem_data = pubchem_data.map_partitions(filter_partition, meta=pubchem_data)

        print('Saving NIH Pubchem data to parquet')
        args.pubchem_data = args.pubchem_data + '.parquet'
        pubchem_data.to_parquet(args.pubchem_data, compression='gzip', engine='pyarrow', overwrite=True)
        pubchem_data = dd.read_parquet(args.pubchem_data)

        len_after = len(pubchem_data)
        print('Done filtering Pubchem data')
        print('Kept {} rows out of {}, {:.2f}%'.format(len_after, len_before, 100*len_after/len_before))

    if not os.path.exists(args.vocab_data + '.vocab'):
        print('Computing vocabulary')
        vocab = list(cl.Vocabulary(vocab_data['SMILES']))
        mol_dict = cl.Vocab2Cat(vocab)
        print('Vocabulary size:', len(vocab))

        print('Saving vocabulary to file')
        with open(args.vocab_data + '.vocab', 'wb') as f:
            pickle.dump((vocab, mol_dict), f)
        print('Done saving vocabulary to file')
        print('Saving mol_dict to file')
        with open(args.vocab_data + '.mol_dict', 'wb') as f:
            pickle.dump(mol_dict, f)
        print('Done saving mol_dict to file')
    else:
        print('Loading vocabulary from file')
        with open(args.vocab_data + '.vocab', 'rb') as f:
            vocab, mol_dict = pickle.load(f)
        print('Done loading vocabulary from file')
        print('Loading mol_dict from file')
        with open(args.vocab_data + '.mol_dict', 'rb') as f:
            mol_dict = pickle.load(f)
        print('Done loading mol_dict from file')

    if any([v not in vocab_data.columns for v in vocab]): 
        print('Setting up the dask apply function')
        clique_decomposition = vocab_data.apply(
            lambda row, vocab, mol_dict: cl.SingleCliqueDecomposition(row['SMILES'], vocab, mol_dict),
            args=(vocab, mol_dict), axis=1, result_type='expand', meta=[(v, 'uint8') for v in vocab])
        print('Computing clique decomposition on the vocabulary data')
        clique_decomposition = clique_decomposition.compute()
        print('Done computing clique decomposition')

        print('Merging vocabulary data with clique decomposition')
        vocab_data = vocab_data.merge(clique_decomposition, left_index=True, right_index=True)
        print('Saving vocabulary data to parquet')
        vocab_data.to_parquet(args.vocab_data)
        print('Done saving vocabulary data to parquet')

    #print('Repartitioning Pubchem data for memory efficiency')
    #pubchem_data = pubchem_data.repartition(npartitions=int(pubchem_data.npartitions*32))
    #print('Done repartitioning Pubchem data')
    #print('Note: Total number of partitions:', pubchem_data.npartitions)

    print('Setting up the dask map partitions function')
    meta = pubchem_data.dtypes.to_dict()
    meta.update({'MolWt': 'float32', 'LogP': 'float32', 'SMILES': 'str'})
    meta.update({v: 'uint8' for v in vocab})
    full_data = pubchem_data.map_partitions(map_descriptors, vocab=vocab, mol_dict=mol_dict, meta=meta)

    print('Saving full data to parquet')
    full_data.to_parquet(args.output_data, compression='gzip', engine='pyarrow', overwrite=True)
    print('Done saving full data to parquet')
