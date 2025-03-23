#!/bin/bash
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=1
#SBATCH --cpus-per-task=42
#SBATCH --gres=gpu:lovelace_l40:1
#SBATCH --time=48:00:00
#SBATCH --mem-per-cpu=3850 
#SBATCH --partition=gpu
#SBATCH --account=su007-gcs-gpu
#SBATCH --mail-type=ALL
#SBATCH --mail-user=h.jia.2@warwick.ac.uk

module purge
module load GCC/12.3.0  OpenMPI/4.1.5
module load GROMACS/2023.3-CUDA-12.1.1-PLUMED-2.9.0

if [ -f "metadynamics.cpt" ]; then
	echo "Continuing for last run"
	srun bash -c 'gmx mdrun -nt 42 -v -deffnm metadynamics -cpi metadynamics.cpt -plumed metadynamics2'
else
	srun bash -c 'gmx grompp -f metadynamics.mdp -o metadynamics.tpr -c equilibrate.gro -r equilibrate.gro -t equilibrate.cpt -p topol.top && gmx mdrun -nt 42 -v -deffnm metadynamics -plumed metadynamics'
fi
