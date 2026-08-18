module purge
module load GCC/12.3.0  OpenMPI/4.1.5
module load GROMACS/2023.3-CUDA-12.1.1-PLUMED-2.9.0

gmx insert-molecules -f step7_production.gro -ci ligandrm.pdb -ip location*dat -o setup.gro -nmol 1 -replace TIP3 -scale 1.0 # use a larger scale because equilibrium seems to fail sometimes
