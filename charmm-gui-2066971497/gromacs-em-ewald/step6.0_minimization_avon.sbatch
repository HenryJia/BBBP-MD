#!/bin/bash
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=1
#SBATCH --cpus-per-task=42
#SBATCH --gres=gpu:ampere_a100:1
#SBATCH --time=01:00:00 # We do not need a lot of time for each of this step. Asking for less time on the queue means we get scheduled faster
#SBATCH --mem-per-cpu=3850 
#SBATCH --partition=gpu
#SBATCH --account=su007-gcs-gpu
#SBATCH --mail-type=ALL
#SBATCH --mail-user=h.jia.2@warwick.ac.uk

module purge
module load GCC/11.2.0 OpenMPI/4.1.1
module load GROMACS/2023.3-CUDA-11.4.1

srun bash -c 'gmx grompp -f step6.0_minimization.mdp -o step6.0_minimization.tpr -c step5_scaled.gro -r step5_scaled.gro -p topol.top -n index.ndx && gmx mdrun -v -deffnm step6.0_minimization'

