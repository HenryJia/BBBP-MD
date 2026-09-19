# Stage 2 — Membrane Construction and Equilibration

This stage builds the two model membranes that represent the apical and
basolateral faces of the blood–brain barrier, and equilibrates them before any
ligand is inserted.

---

## 2.1 Membrane compositions

The two membranes are built with **CHARMM-GUI Membrane Builder v3.7**
(`input.config.dat` records `"systype":"bilayer"`, `"forcefield":{"type":"c36m"}`,
`"hmr":false`). Each bilayer is **symmetric between its two leaflets** (upper and
lower counts are identical), but the apical and basolateral membranes differ
from each other. The per-leaflet lipid counts are recorded in
`composition-nature-paper.txt` and in the CHARMM-GUI
`step3_nlipids_{upper,lower}.prm` files.

### Apical membrane

Built in `apical/charmm-gui-3989364611/`. Box: 73.42 × 73.42 × 160 Å.

| Lipid | Upper leaflet | Lower leaflet | Total |
| --- | ---: | ---: | ---: |
| OSM (sphingomyelin) | 18 | 18 | 36 |
| CHL1 (cholesterol) | 28 | 28 | 56 |
| POPC | 4 | 4 | 8 |
| SAPC | 8 | 8 | 16 |
| SAPE | 14 | 14 | 28 |
| SOPE | 6 | 6 | 12 |
| SAPS | 8 | 8 | 16 |
| SLPC | 8 | 8 | 16 |
| SAPI | 2 | 2 | 4 |

### Basolateral membrane

Built in `basolateral/` (the CHARMM-GUI build directory is not committed, but
the equilibrated system is in `basolateral/gromacs/`).

| Lipid | Upper leaflet | Lower leaflet | Total |
| --- | ---: | ---: | ---: |
| OSM | 22 | 22 | 44 |
| CHL1 | 28 | 28 | 56 |
| POPC | 2 | 2 | 4 |
| SAPC | 6 | 6 | 12 |
| SAPE | 14 | 14 | 28 |
| SOPE | 6 | 6 | 12 |
| SAPS | 10 | 10 | 20 |
| SLPC | 6 | 6 | 12 |
| SAPI | 2 | 2 | 4 |

Both membranes are symmetric between leaflets. The basolateral membrane is
richer in sphingomyelin (OSM: 44 vs 36 total) and in the anionic SAPS
(20 vs 16), while the apical membrane is richer in SLPC (16 vs 12) and POPC
(8 vs 4). These differences reflect the distinct lipid compositions of the two
faces of the BBB.

The `[ molecules ]` section of `apical/gromacs/topol.top` confirms the totals
and adds the solvent/ions: 73 Na⁺ (SOD), 53 Cl⁻ (CLA) and 19,968 TIP3P waters
for the apical system; 77 Na⁺, 53 Cl⁻ and 19,674 TIP3P waters for the
basolateral system.

> `charmm-gui-2066971497/` is an **earlier, alternative** membrane model
> (DOPE/DOPC/23SM, 76.8 × 76.8 × 100 Å) that is not used by the final workflow.
> It is retained for provenance.

---

## 2.2 Force field and topology

- Force field: **CHARMM36m** (`charmm36-jul2022.ff` for the ligand stage;
  `toppar/` for the membrane stage).
- Water: **TIP3P**.
- Ions: **Na⁺ (SOD)** and **Cl⁻ (CLA)**.
- The membrane topology (`apical/gromacs/topol.top`,
  `basolateral/gromacs/topol.top`) includes the lipid `.itp` files, ions and
  water.

---

## 2.3 Equilibration protocol

The membrane is equilibrated with the standard CHARMM-GUI six-stage protocol
plus a production run. The `.mdp` files are in `common/` and are symlinked into
`apical/gromacs/` and `basolateral/gromacs/`. The driver is
`common/run_default.sh`, submitted via `run_default.sbatch` (A100) or
`run_default_avon.sbatch` (RTX 6000).

| Stage | File | Integrator | `dt` (ps) | Steps | Duration | Pressure coupling | Position/dihedral restraints |
| --- | --- | --- | ---: | ---: | ---: | --- | --- |
| Minimisation | `step6.0_minimization.mdp` | `steep` | — | 5,000 | — | none | lipid 1000, dihedral 1000 |
| Equilibration 1 | `step6.1_equilibration.mdp` | `md` | 0.001 | 125,000 | 125 ps | none (NVT) | lipid 1000, dihedral 1000 |
| Equilibration 2 | `step6.2_equilibration.mdp` | `md` | 0.001 | 125,000 | 125 ps | none (NVT) | lipid 400, dihedral 400 |
| Equilibration 3 | `step6.3_equilibration.mdp` | `md` | 0.001 | 125,000 | 125 ps | C-rescale, semi-isotropic | lipid 400, dihedral 200 |
| Equilibration 4 | `step6.4_equilibration.mdp` | `md` | 0.002 | 250,000 | 500 ps | C-rescale, semi-isotropic | lipid 200, dihedral 200 |
| Equilibration 5 | `step6.5_equilibration.mdp` | `md` | 0.002 | 250,000 | 500 ps | C-rescale, semi-isotropic | lipid 40, dihedral 100 |
| Equilibration 6 | `step6.6_equilibration.mdp` | `md` | 0.002 | 250,000 | 500 ps | C-rescale, semi-isotropic | none |
| Production | `step7_production.mdp` | `md` | 0.002 | 50,000,000 | 100 ns | C-rescale, semi-isotropic | none |

Common settings across all stages:

- **Temperature:** 310 K, `v-rescale` thermostat, `tau_t = 1.0 ps`.
- **Pressure:** 1 bar, `C-rescale` barostat, `tau_p = 5.0 ps`,
  `compressibility = 4.5e-5 bar⁻¹`, `pcoupltype = semiisotropic`.
- **Non-bonded:** Verlet cut-off scheme, `rlist = 1.2 nm`, `rvdw = 1.2 nm`
  with `Force-switch` from 1.0 nm, PME electrostatics with `rcoulomb = 1.2 nm`.
- **Constraints:** `h-bonds` with LINCS.
- **Restraints:** `-DPOSRES` (lipid position restraints) and `-DDIHRES`
  (dihedral restraints), with force constants stepped down across the stages as
  shown above.

`run_default.sh` runs minimisation, then loops `step6.1`–`step6.6`, then runs
`step7_production`. The production run is the equilibrated membrane that is
later used as the starting structure for ligand insertion
(`step7_production.gro`).

---

## 2.4 Outputs

After equilibration each membrane directory contains:

- `step5_input.gro/.psf` — assembled CHARMM-GUI system.
- `step6.0_minimization.*` … `step6.6_equilibration.*` — per-stage
  `.gro`, `.tpr`, `.cpt`.
- `step7_production.gro/.tpr/.cpt` — the equilibrated membrane.
- `index.ndx` — GROMACS index file; the first group `[ MEMB ]` lists all
  membrane atoms (used by the PLUMED generators to define the membrane COM).
- `topol.top`, `toppar/` — topology and force-field parameters.
- `README` — the original CHARMM-GUI run script.

---

## 2.5 Next steps

The equilibrated `step7_production.gro` is the input for ligand insertion and
metadynamics, described in `docs/03_ligand_insertion_and_metadynamics.md`.