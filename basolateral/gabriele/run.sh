#!/bin/bash

idx="/home/wolf/CODES/GROMACS/gromacs-2022.3/build/bin/gmx make_ndx"
grompp="/home/wolf/CODES/GROMACS/gromacs-2022.3/build/bin/gmx grompp"
mdrun="/home/wolf/CODES/GROMACS/gromacs-2022.3/build/bin/gmx mdrun"

#rm -r -f ener.edr md.log mdout.mdp topol.tpr traj.* index.ndx
#rm -r -f rm charges.q charge.xvg energy.xvg field.xvg hin_structure.in hin_structure.log hin_structure.out.electro hin_structure.out.zdens last list.dat log.log md.edr md.gro md.log mdout.mdp potential.xvg state.cpt state_prev.cpt topol.top_OLD topol.tpr traj.xtc

$grompp -f grompp.mdp -c conf.gro -r conf.gro -p topol.top -o topol.tpr -n index.ndx -maxwarn 1
$mdrun -s topol.tpr -o traj.trr -x traj.xtc -c md.gro -e md.edr -g md.log

# RESTART
#$mdrun -ntomp 4 -s topol.tpr -cpi state.cpt -o traj.1.trr -x traj.1.xtc -c md.1.gro -e md.1.edr -g md.1.log >/dev/null &

exit 0
