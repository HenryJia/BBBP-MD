module purge
module load GCC/11.2.0 OpenMPI/4.1.1
module load GROMACS/2021.5-CUDA-11.4.1-PLUMED-2.8.0

gmx insert-molecules -f step7_production.gro -ci ligandrm.pdb -ip location.dat -o setup.gro -nmol 1 -replace TIP3
