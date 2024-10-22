#!/bin/bash
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=1
#SBATCH --cpus-per-task=16
#SBATCH --gres=gpu:quadro_rtx_6000:1
#SBATCH --time=48:00:00
#SBATCH --mem-per-cpu=3700
#SBATCH --partition=gpu
#SBATCH --mail-type=ALL
#SBATCH --mail-user=h.jia.2@warwick.ac.uk

module purge
module load GCC/11.2.0 OpenMPI/4.1.1
module load GROMACS/2023.3-CUDA-11.4.1

srun bash -c 'gmx grompp -f step6.2_equilibration.mdp -o step6.2_equilibration.tpr -c step6.1_equilibration.gro -r step6.1_equilibration.gro -p topol.top -n index.ndx && gmx mdrun -v -deffnm step6.2_equilibration'

