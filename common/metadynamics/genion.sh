gmx grompp -f genion.mdp -c setup.gro -p topol.top -o genion.tpr
gmx genion -s genion.tpr -o setup_balanced.gro -p topol.top -pname SOD -nname CLA -neutral
mv setup_balanced.gro setup.gro
