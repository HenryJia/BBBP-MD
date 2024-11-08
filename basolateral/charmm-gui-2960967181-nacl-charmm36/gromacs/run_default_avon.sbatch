#!/bin/bash
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=1
#SBATCH --cpus-per-task=16
#SBATCH --gres=gpu:quadro_rtx_6000:1
#SBATCH --time=1:00:00
#SBATCH --mem-per-cpu=3700
#SBATCH --partition=gpu
#SBATCH --mail-type=ALL
#SBATCH --mail-user=h.jia.2@warwick.ac.uk

module purge
module load GCC/11.2.0 OpenMPI/4.1.1
module load GROMACS/2021.5-CUDA-11.4.1-PLUMED-2.8.0

srun ./run_default.sh
