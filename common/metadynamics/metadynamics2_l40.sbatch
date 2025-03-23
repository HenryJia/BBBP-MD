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

if [ -f "metadynamics2.tpr" ]; then
	echo "Continuing for last meta2 run"
	srun bash -c 'gmx mdrun -nt 42 -v -s metadynamics2.tpr -deffnm metadynamics -cpi metadynamics.cpt -plumed metadynamics2'
else
	echo "running convert-tpr"
	#srun bash -c 'gmx grompp -f metadynamics.mdp -o metadynamics2.tpr -c metadynamics.gro -r metadynamics.gro -t metadynamics.cpt -p topol.top && gmx mdrun -nt 16 -v -deffnm metadynamics2 -plumed metadynamics2'
	srun bash -c 'gmx convert-tpr -s metadynamics.tpr -o metadynamics2.tpr -extend 100000 && gmx mdrun -nt 16 -v -deffnm metadynamics -s metadynamics2.tpr -cpi metadynamics.cpt -plumed metadynamics2'
fi

