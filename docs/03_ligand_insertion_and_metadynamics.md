# Stage 3 — Ligand Insertion, Re-equilibration and Metadynamics

This stage takes each selected candidate (and each reference molecule), inserts
it into an equilibrated membrane, re-equilibrates the system, and runs
well-tempered metadynamics to obtain a free-energy profile for crossing the
membrane.

All machinery lives in `common/metadynamics/`; each simulation directory
(e.g. `apical/candidates/pos/129723484/`) contains **relative symlinks** back to
those shared files, so the same scripts work on any machine regardless of the
absolute path.

---

## 3.1 Ligand parameterisation — `common/candidates/`

Each candidate is submitted to **CHARMM-GUI Ligand Designer** (CGenFF). The
output is stored under `common/candidates/{pos,neg}/<CID>/`:

```
common/candidates/pos/129723484/
├── charmm-gui-4475231340/     Full CHARMM-GUI output (incl. lig.prm, lig.sdf)
├── lig/
│   ├── LIG.itp                Ligand topology (atom types, bonds, angles, dihedrals)
│   └── charmm36.itp           CGenFF parameters for the ligand's atom types
├── lig.sdf                    Ligand structure
└── ligandrm.pdb               Ligand PDB (all atoms, incl. hydrogens) for insertion
```

`common/candidates/generate_configurations.py` automates the setup:

1. **`process_candidate(cid, cls)`** — extracts the `.itp` and `.pdb` files from
   the CHARMM-GUI tarball into `lig/` and the candidate directory.
2. **De-duplicates the ligand `.itp`** — CHARMM-GUI writes copies of atom
   types, bond/angle/dihedral types and `[ defaults ]` that are already present
   in `charmm36-jul2022.ff`. The script comments out any line whose type
   already exists in `ffnonbonded.itp` / `ffbonded.itp`, and comments out any
   section header that becomes empty. This avoids duplicate-definition errors
   in `grompp`.
3. **`setup_files(cid, cls, membrane)`** — creates the simulation directory
   under `{apical,basolateral}/candidates/{pos,neg}/<cid>/` and symlinks in the
   ligand files, the shared metadynamics scripts, the force field, the
   equilibrated membrane (`step7_production.gro`), `index.ndx` and `toppar/`.
   It also writes a candidate-specific `topol.top` that includes
   `charmm36-jul2022.ff/forcefield.itp`, `lig/charmm36.itp` and `lig/LIG.itp`,
   and disables the membrane `toppar/forcefield.itp` include.

`common/candidates/print_candidates.py` simply prints the candidate tables
(CID, InChIKey, SMILES, MolWt, LogP, `BBB+`, `logBB`) for inspection.

> **Note:** `process_candidate()` expects a `charmm-gui.tgz` tarball in each
> candidate directory. The tarballs are **not committed** to the repository —
> only the extracted `charmm-gui-*/` output and the `lig/` files are. To re-run
> the extraction you must re-download the CHARMM-GUI archives, or skip
> `process_candidate()` and use the committed `lig/` files directly.

---

## 3.2 Ligand insertion — `insert-molecule.sh` / `insert-molecule.py`

`insert-molecule.sh`:

```bash
gmx insert-molecules -f step7_production.gro -ci ligandrm.pdb \
    -ip location*dat -o setup.gro -nmol 1 -replace TIP3 -scale 1.0
```

- `-ci ligandrm.pdb` — the ligand PDB produced by CHARMM-GUI (all atoms,
  including hydrogens).
- `-ip location*dat` — the insertion position (see §3.6).
- `-replace TIP3` — the ligand replaces a water molecule, so the box size and
  lipid positions are unchanged.
- `-nmol 1` — one ligand per system.

`insert-molecule.py` then fixes the topology:

- counts the TIP3P molecules in `setup.gro` and rewrites the `TIP3` line in
  `topol.top`;
- appends `LIG  1` to the `[ molecules ]` section if not already present.

`genion.sh` (run when the system needs neutralising) uses `gmx grompp` with
`genion.mdp` followed by `gmx genion -pname SOD -nname CLA -neutral`, replacing
`setup.gro` with the neutralised structure.

---

## 3.3 PLUMED input generation

The PLUMED inputs are generated from templates by three scripts. All of them
locate the ligand atoms by regex on `setup.gro` (the ligand is the last
molecule, so its atoms are the highest-numbered ones) and the membrane atoms
from the first block of `index.ndx` (`[ MEMB ]`).

### `generate_equilibrate.py`

Reads `equilibrate_template.dat` and `ini_com_template.dat` and writes:

- `equilibrate.dat` — restraint for the first re-equilibration run;
- `equilibrate2.dat` — same, prefixed with `RESTART` for continuation;
- `ini_com.dat` — used by `plumed driver` to compute the ligand COM.

It also handles the alternate starting positions: if `location.dat` is absent,
it globs `location*dat`, reads the coordinates, and `sed`-replaces the default
restraint centre `3.4,3.4,16.5` in `equilibrate.dat`/`equilibrate2.dat`.

### `generate_metadynamics.py`

Reads `metadynamics_template.dat`, `index.ndx`, `setup.gro` and
`com_position.txt` (the ligand COM in scaled coordinates) and writes
`metadynamics.dat` and `metadynamics2.dat` (the latter with `RESTART`).

### `generate_plumed.py`

A more general, argument-driven version of the above that can generate the
equilibration, COM and metadynamics inputs in one pass
(`--equilibrate`, `--ini_com`, `--meta`, `--ndx`, `--mc`, `--output`, `--setup`,
`--name`, `--num_runs`). With no arguments it loops over both membranes and the
five reference molecules.

---

## 3.4 PLUMED templates

### `ini_com_template.dat` — ligand centre of mass

```
c_lig: COM ATOMS={lig}
p: POSITION ATOM=c_lig SCALED_COMPONENTS
PRINT ARG=p.a,p.b,p.c FILE=com_position.txt STRIDE=1
FLUSH STRIDE=1
```

Run with `plumed driver --mc mcfile --igro equilibrate.gro --plumed ini_com.dat`
(`plumed_driver.sh`). The scaled x/y components are later used to restrain the
ligand laterally.

### `equilibrate_template.dat` — re-equilibration restraint

```
vol: VOLUME
G: ENERGY
c: COM ATOMS={lig}
p: POSITION ATOM=c NOPBC
restraint: RESTRAINT ARG=p.x,p.y,p.z AT=3.4,3.4,16.5 KAPPA=100.0,100.0,100.0
PRINT ARG=G,vol,p.x,p.y,p.z STRIDE=10000 FILE=equilibrate_out
DUMPMASSCHARGE FILE=mcfile STRIDE=50000000
```

The ligand COM is harmonically restrained to a point in the water phase
(`3.4, 3.4, 16.5` nm by default, or the alternate `location*.dat` position).
`NOPBC` is essential: without it PLUMED uses a different coordinate convention
from GROMACS and the restraint can fire the ligand through the membrane.
`DUMPMASSCHARGE` writes `mcfile`, which is needed by `plumed driver` for the
COM calculations.

### `metadynamics_template.dat` — well-tempered metadynamics

```
c_lig: COM ATOMS={lig}
p: POSITION ATOM=c_lig SCALED_COMPONENTS

c_mem: COM ATOMS={membrane}
r_lig_xy: RESTRAINT ARG=p.a,p.b AT={lig_pos} KAPPA=1000,1000

d: DISTANCE ATOMS=c_lig,c_mem COMPONENTS
d_abs: MATHEVAL ARG=d.z FUNC=abs(x) VAR=x PERIODIC=NO

mtd: METAD ARG=d_abs SIGMA=0.2 HEIGHT=2.4 TEMP=310 PACE=500 BIASFACTOR=50

PRINT ARG=d_abs,mtd.bias,r_lig_xy.bias FILE=COLVAR STRIDE=500
```

- **Collective variable:** `d_abs`, the absolute z-distance between the ligand
  COM and the membrane COM. Using the absolute value makes the two membrane
  faces equivalent and halves the CV range.
- **Lateral restraint:** `r_lig_xy` keeps the ligand's x/y position fixed
  (force constant 1000 kJ mol⁻¹ nm⁻²) so it cannot drift sideways out of the
  membrane patch.
- **Metadynamics parameters:** Gaussian width `SIGMA = 0.2 nm`, initial height
  `HEIGHT = 2.4 kJ/mol`, `PACE = 500` steps (1 ps at `dt = 0.002 ps`),
  `BIASFACTOR = 50`, temperature 310 K.
- **Output:** `COLVAR` (CV, metadynamics bias, restraint bias) and `HILLS`.

### `com_membrane_template.dat` and `smac_template.dat`

Used for the post-processing membrane-order analysis (see §3.8).

---

## 3.5 Re-equilibration and metadynamics runs

### `equilibrate.sbatch`

Two-stage re-equilibration of the inserted ligand:

1. **NVT** — `grompp -f equilibrate_nvt.mdp` from `setup.gro`, then `mdrun`
   with `-plumed equilibrate`. `equilibrate_nvt.mdp` is 10 ns at `dt = 0.001 ps`
   with `pcoupl = no` and the same lipid/dihedral restraints as the membrane
   equilibration.
2. **NPT** — `grompp -f equilibrate.mdp` continuing from `equilibrate_nvt.cpt`,
   then `mdrun` with `-plumed equilibrate`. `equilibrate.mdp` is 100 ns at
   `dt = 0.002 ps` with `C-rescale` semi-isotropic pressure coupling.

If `equilibrate.cpt` already exists the script restarts from it with
`-plumed equilibrate2`.

### `metadynamics.sbatch`

```bash
gmx grompp -f metadynamics.mdp -o metadynamics.tpr \
    -c equilibrate.gro -r equilibrate.gro -t equilibrate.cpt -p topol.top
gmx mdrun -v -deffnm metadynamics -plumed metadynamics
```

`metadynamics.mdp` is **200 ns** at `dt = 0.002 ps` (100,000,000 steps) with
`pcoupl = no` — the box is held fixed during metadynamics so the CV is
well-defined. Restarting uses `-plumed metadynamics2`.

Three sbatch variants exist for different hardware:

| Script | GPU | Partition |
| --- | --- | --- |
| `equilibrate.sbatch` / `metadynamics.sbatch` | A100 | `gpu` |
| `*_avon.sbatch` | RTX 6000 | `gpu` |
| `*_l40.sbatch` | L40 | `gpulowpri` |

All load `GCC/12.3.0`, `OpenMPI/4.1.5` and
`GROMACS/2023.3-CUDA-12.1.1-PLUMED-2.9.0`.

---

## 3.6 Alternate starting positions (reviewer request)

To estimate the uncertainty in the free-energy profiles, the reference molecules
were re-run from four different lateral starting positions. The positions are
defined in `common/metadynamics/location*.dat`:

| File | x, y, z (nm) |
| --- | --- |
| `location.dat` | 3.4, 3.4, 16.5 (centre) |
| `location_ne.dat` | 5.1, 5.1, 16.5 |
| `location_nw.dat` | 1.7, 5.1, 16.5 |
| `location_se.dat` | 5.1, 1.7, 16.5 |
| `location_sw.dat` | 1.7, 1.7, 16.5 |

The corresponding simulation trees are `{apical,basolateral}/position_{ne,nw,se,sw}/`.
`generate_equilibrate.py` detects the non-default `location*.dat` and rewrites
the restraint centre accordingly. The analysis notebook overlays the five
profiles (centre + four corners) as a min–max band
(`reference_fes_band_{apical,basolateral}.png`).

---

## 3.7 Semi-isotropic pressure-coupling variant (reviewer request)

The main metadynamics runs use `pcoupl = no` (constant volume). As a control,
the reference molecules were also run with a **semi-isotropic C-rescale
barostat** active during metadynamics
(`common/metadynamics/metadynamics_semiistropic.mdp`):

```
pcoupl          = C-rescale
pcoupltype      = semiisotropic
compressibility = 4.5e-5  0
ref_p           = 1.0     1.0
```

The z-compressibility is set to zero so the membrane normal direction is not
compressed, while x/y are coupled to 1 bar. These runs live in
`{apical,basolateral}/semiisotropic/` and are plotted as
`semiistropic_fes_{apical,basolateral}.png`.

---

## 3.8 Free-energy and membrane-order post-processing

### `sum_hills.sh` — free-energy profiles

```bash
plumed sum_hills --hills HILLS --kt 2.577 --mintozero
plumed sum_hills --hills HILLS --kt 2.577 --mintozero --stride 10000
```

- `--kt 2.577` is $k_BT$ at 310 K in kJ/mol.
- The first command writes the final `fes.dat`.
- The second writes `fes_0.dat` … `fes_20.dat`, the FES accumulated after each
  successive block of 10,000 hills, used for the convergence analysis.

### `generate_postprocess.py` — membrane COM and SMAC

1. Writes `com_membrane.dat` from `com_membrane_template.dat` (membrane COM).
2. Runs `plumed driver` to produce `com_membrane.txt`.
3. Builds `smac.dat` from `smac_template.dat`: for each of the 192 lipids it
   identifies the first and last acyl carbons that define the lipid's
   orientation vector (the `smac_atoms` table maps each lipid type to this
   pair), appends the first atom again to form the three-atom `MOL` entry, and
   reverses the atom order for lipids below the membrane COM so all vectors
   point the same way.

### `smac.sh` — membrane order parameter

```bash
plumed driver --mc mcfile --ixtc metadynamics.xtc --plumed smac.dat --timestep 100
```

This computes the PLUMED **SMAC** (a variant of the "SMAC" collective variable
from the crystallization module) for the membrane lipids along the metadynamics
trajectory, writing `smac.txt` with columns `time`, `d_abs`, `smac`. SMAC
measures the local orientational order of neighbouring lipid molecules; it is
used to check whether the ligand perturbs the bilayer as it crosses.

---

## 3.9 Directory contents after a completed run

A finished candidate directory (e.g. `apical/candidates/pos/129723484/`)
contains:

| File | Description |
| --- | --- |
| `setup.gro` | System after ligand insertion |
| `equilibrate_nvt.gro/.cpt` | NVT re-equilibration |
| `equilibrate.gro/.cpt` | NPT re-equilibration |
| `metadynamics.gro/.cpt` | Final metadynamics frame/checkpoint |
| `COLVAR` | CV and bias vs time |
| `HILLS` | Metadynamics hills |
| `fes.dat`, `fes_0..20.dat` | Final and strided free-energy profiles |
| `com_position.txt`, `com_membrane.txt` | Ligand/membrane COM |
| `smac.txt` | SMAC vs distance |
| `mcfile` | Mass/charge file for `plumed driver` |
| `topol.top` | Candidate-specific topology |
| `lig/`, `lig.sdf`, `ligandrm.pdb` | Ligand files (symlinks) |
| `*.dat` PLUMED inputs, `*.mdp`, `*.sbatch`, `*.sh` | Symlinks to `common/` |

---

## 3.10 Next steps

The FES, SMAC and convergence data are analysed in
`docs/04_analysis_and_insights.md`.