# Sum all hills to get a FE profile
plumed sum_hills --hills HILLS --kt 2.577 --mintozero
# Same thing but strided so we can check convergence
plumed sum_hills --hills HILLS --kt 2.577 --mintozero --stride 100
