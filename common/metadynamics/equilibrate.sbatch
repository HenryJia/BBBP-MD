#!/bin/bash
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=1
#SBATCH --cpus-per-task=42
#SBATCH --gres=gpu:ampere_a100:1
#SBATCH --time=48:00:00
#SBATCH --mem-per-cpu=3850 
#SBATCH --partition=gpu
#SBATCH --account=su007-gcs-gpu
#SBATCH --mail-type=ALL
#SBATCH --mail-user=h.jia.2@warwick.ac.uk

module purge
module load GCC/12.3.0  OpenMPI/4.1.5
module load GROMACS/2023.3-CUDA-12.1.1-PLUMED-2.9.0

if [ -f "equilibrate.cpt" ]; then
	echo "Continuing for last run"
	srun bash -c 'gmx mdrun -nt 42 -v -deffnm equilibrate -cpi equilibrate.cpt -plumed equilibrate2'
else
	srun bash -c 'gmx grompp -f equilibrate_nvt.mdp -o equilibrate_nvt.tpr -c setup.gro -r setup.gro -p topol.top && gmx mdrun -nt 42 -v -deffnm equilibrate_nvt -plumed equilibrate'
	srun bash -c 'gmx grompp -f equilibrate.mdp -o equilibrate.tpr -c setup.gro -r setup.gro -p topol.top -t equilibrate_nvt.cpt && gmx mdrun -nt 42 -v -deffnm equilibrate -plumed equilibrate'
fi


