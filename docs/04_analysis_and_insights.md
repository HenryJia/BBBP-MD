# Stage 4 — Analysis and Results

This stage turns the raw metadynamics output into the quantitative results and
figures of the paper. The analysis is split between the notebooks in `ipynb/`
(which produce the paper figures) and the standalone scripts in
`common/plotting/` (which reproduce the same analyses from the command line).

Sections 4.1–4.6 describe the analyses and how to interpret them; sections
4.7–4.12 are the practical reference for the stage (environment, file formats,
commands, troubleshooting and hardware).

---

## 4.1 Reading a free-energy profile

Every analysis starts from a PLUMED `fes.dat` file with three columns
`d_abs`, `G`, `dG`. The shared helper `read_fes` / `read_fe_csv` does the same
three things everywhere:

1. Read the file, skipping `#` comments.
2. Discard points outside `0 < d_abs < 8 nm` (the CV range).
3. **Shift the zero of free energy to the water phase**: subtract the mean of
   `G` over `d_abs > 7 nm`, so that the free energy in bulk water is 0.

The **permeation barrier** for a molecule is then `G.max()` of the shifted
profile. For the total barrier across the BBB, the apical and basolateral
barriers are added.

---

## 4.2 `ipynb/plot_results.ipynb` — paper figures

This is the main analysis notebook. It is run from the `ipynb/` directory and
reads `../apical` and `../basolateral`.

### 4.2.1 Filtering funnel

A Plotly funnel (`funnel_pubchem.png`) showing the hierarchical screen counts
from Stage 1 (see `docs/01_molecular_screening.md` §1.6). The x-axis is
`log10(count)` (multiplied by 2 for the total-PubChem bar to keep it on scale).

### 4.2.2 Candidate barrier boxplots

For each membrane, `load_fes()` reads the FES of every positive and negative
candidate plus the five reference molecules, and plots:

- `apical_candidates_boxplot.png` / `basolateral_candidates_boxplot.png` —
  boxplots of the maximum barrier for positive vs negative candidates, with the
  reference molecules drawn as horizontal lines.
- `total_candidates_boxplot.png` — the sum of the apical and basolateral
  barriers.

The boxplots use `whis=[0, 100]` (full range) and a Mann–Whitney U test
(`alternative="greater"`, exact method) tests the hypothesis that negative
candidates have a **higher** barrier than positive candidates. The U statistic
and p-value are printed for the apical, basolateral and total cases.

### 4.2.3 Reference-molecule FES

`reference_fes_{apical,basolateral}.png` overlays the free-energy profiles of
the five reference molecules, labelled by distance from the membrane centre.

### 4.2.4 Candidate FES

`apical_fes.png` / `basolateral_fes.png` plot every candidate's profile, with
positive candidates in a green (`PuBuGn`) colormap and negative candidates in a
red/orange (`YlOrRd`) colormap.

### 4.2.5 Convergence

`compute_convergence()` reads the 21 strided FES files `fes_0.dat` … `fes_20.dat`
and computes, for each successive pair, the mean absolute change in `G`:

```python
time += [i * 2 * 10000 * 500 / 1e6]   # ns
dG   += [np.mean(np.abs(hill_fes[i+1]['G'] - hill_fes[i]['G']))]
```

The time axis is derived from the metadynamics parameters: 500 steps between
hills × 0.002 ps/step × 10,000 hills per stride = 10 ns per block. The result is
plotted as `convergence_{apical,basolateral}.png` (seaborn lineplot of `dG` vs
time for positive and negative candidates).

### 4.2.6 SMAC (membrane order)

For each membrane and each candidate class, the notebook concatenates every
`smac.txt` and plots a 2-D kernel density estimate of SMAC vs distance from the
membrane centre (`sns.kdeplot`, viridis, `thresh=0.05`, 100 levels):

- `apical_smac_pos.png`, `apical_smac_neg.png`
- `basolateral_smac_pos.png`, `basolateral_smac_neg.png`
- `smac_pos.png`, `smac_neg.png` (both membranes combined)

### 4.2.7 CGenFF penalty scores

The notebook globs each candidate's CHARMM-GUI `lig.prm` and extracts every
`penalty=<value>` with a regex, printing the mean and standard deviation of the
CGenFF penalty per candidate. This is a quality check on the ligand
parameterisation.

### 4.2.8 Prediction histograms

`histogram_bbbp.png` overlays the PubChem and B3DB predicted `BBB+`
distributions on twin axes, using the cached histogram counts
(`hist_pubchem.csv`, `histbins_pubchem.csv`, `hist_b3db.csv`,
`histbins_b3db.csv`) so the full PubChem dataframe is not needed.

### 4.2.9 Reviewer-requested figures

- `semiistropic_fes_{apical,basolateral}.png` — reference-molecule FES from the
  semi-isotropic pressure-coupling runs (`../{mem}/semiisotropic/`).
- `reference_fes_band_{apical,basolateral}.png` — the centre profile plus the
  four alternate starting positions, drawn as a min–max shaded band around the
  centre line.

---

## 4.3 `ipynb/analyse_pubchem.ipynb` — screen validation

Described in `docs/01_molecular_screening.md` §1.8. Produces the prediction
histograms, the Morgan/MACCS UMAP embeddings and the Tanimoto similarity
tables.

---

## 4.4 `common/plotting/` — standalone scripts

These reproduce the notebook analyses without Jupyter. They hard-code the
membrane paths (`../../apical/`, `../../basolateral/`) and the candidate CSVs
(`../candidates/bbbp_{positive,negative}_pubchem.csv`), so they must be run from
`common/plotting/`.

| Script | Output |
| --- | --- |
| `plot_fe.py` | Reference-molecule FES per membrane (`apical.png`, `basolateral.png`) |
| `plot_candidates.py` | Candidate FES, barrier boxplots, total boxplot, cLogP/MolWt/clique-count distributions |
| `plot_convergence.py` | Per-molecule convergence plots from `fes_{idx}.dat` |
| `plot_correlation.py` | Barrier height vs experimental `logBB` for the reference molecules |
| `plot_postprocess.py` | SMAC KDEs per membrane and combined |

### `plot_correlation.py`

This is the only script that uses experimental data. It hard-codes the
reference `logBB` values:

```python
molecules = {
    'trihexyphenidyl': 1.32,
    'isopropanol': -0.1,
    'morphine-6-glucuronide': -2.09,
    'sucrose': -1.7}
```

It computes the apical, basolateral and total barriers and plots each against
`logBB`, with a dashed line at `logBB = -1` separating BBBP+ from BBBP−. Note
that this script uses a different distance window for the basolateral membrane
(`0 < z < 4 nm`, zero point at `z > 3 nm`) than the other scripts.

---

## 4.5 Interpreting the results

- **Barrier height** is the primary quantity: a lower maximum in the free-energy
  profile means a lower energetic cost to cross the membrane, hence a higher
  expected permeability.
- **Positive vs negative candidates**: the Mann–Whitney tests in
  `plot_results.ipynb` quantify whether the ML-predicted permeable set really
  does have lower barriers than the predicted impermeable set.
- **Reference molecules** anchor the scale: trihexyphenidyl (high `logBB`) is
  expected to have a low barrier, sucrose and morphine-6-glucuronide (low
  `logBB`) high barriers.
- **SMAC** shows whether the ligand disrupts local lipid packing as it crosses;
  a strong perturbation at a particular depth can indicate a defect-mediated
  permeation mechanism.
- **Convergence** plots show whether the FES has stopped changing; the mean
  absolute change per 10 ns should decay towards zero.
- **Uncertainty bands** from the alternate starting positions and the
  semi-isotropic control bound the systematic error on the reference profiles.

---

## 4.6 Outputs

The analysis produces the figures listed in the README §5, plus the printed
statistics (cross-validation metrics, Mann–Whitney U/p, CGenFF penalties,
Tanimoto similarities). These are the inputs to the manuscript.

---

## 4.7 Environment

### 4.7.1 Python (analysis)

The analysis environment is defined by `ipynb/Pipfile` (Python 3.9):

```bash
cd ipynb
pipenv install
pipenv run jupyter notebook
```

Key packages: `rdkit-pypi`, `numpy`, `pandas`, `dask[complete]`, `scikit-learn`,
`umap-learn`, `matplotlib`, `seaborn`, `plotly`, `pyarrow`, `networkx`.

On the Warwick Sulis cluster:

```bash
source ipynb/modules.sh           # GCC 11.2.0, OpenMPI 4.1.1, Python 3.9.6
bash ipynb/jupyter_interactive.sh # salloc on the vhmem partition
```

### 4.7.2 MD (simulations)

GROMACS 2023.3 built with PLUMED 2.9.0. The sbatch scripts load:

```bash
module purge
module load GCC/12.3.0 OpenMPI/4.1.5
module load GROMACS/2023.3-CUDA-12.1.1-PLUMED-2.9.0
```

---

## 4.8 Directory conventions

- **`common/`** holds all shared inputs. Simulation directories contain
  **relative symlinks** into `common/`, so the tree is portable between
  machines. Do not copy the files; keep the symlinks.
- **`apical/`** and **`basolateral/`** have identical layouts:
  - `gromacs/` — equilibrated membrane + the five reference molecules.
  - `candidates/{pos,neg}/<CID>/` — the 20 candidate metadynamics runs.
  - `position_{ne,nw,se,sw}/` — alternate starting positions.
  - `semiisotropic/` — semi-isotropic pressure-coupling variant.
- **`ipynb/`** holds all Python code and notebooks. Notebooks assume the working
  directory is `ipynb/` and reference `../apical`, `../basolateral`,
  `../common/candidates/...`.

---

## 4.9 Running the workflow

### 4.9.1 Membrane equilibration

From `apical/gromacs/` or `basolateral/gromacs/`:

```bash
sbatch run_default.sbatch        # A100
# or
sbatch run_default_avon.sbatch   # RTX 6000
```

This runs `run_default.sh`: minimisation, `step6.1`–`step6.6`, then
`step7_production`. See `docs/02_membrane_preparation.md` for the parameters.

### 4.9.2 Candidate setup

From `common/candidates/`:

```bash
python generate_configurations.py   # extract CHARMM-GUI output, build sim dirs
python print_candidates.py          # inspect the candidate tables
```

`generate_configurations.py` expects each candidate to have a
`charmm-gui.tgz` tarball in `common/candidates/{pos,neg}/<CID>/`. It creates the
simulation directories under both membranes and symlinks in the shared files.

### 4.9.3 Per-candidate metadynamics

From a candidate directory, e.g. `apical/candidates/pos/129723484/`:

```bash
python insert-molecule.py        # gmx insert-molecules + fix topol.top
sh genion.sh                     # optional: neutralise with SOD/CLA
python generate_equilibrate.py   # write equilibrate.dat, equilibrate2.dat, ini_com.dat
sh plumed_driver.sh              # write com_position.txt
python generate_metadynamics.py  # write metadynamics.dat, metadynamics2.dat
sbatch equilibrate.sbatch        # NVT (10 ns) then NPT (100 ns)
sbatch metadynamics.sbatch       # 200 ns well-tempered metadynamics
sh sum_hills.sh                  # fes.dat + fes_0..20.dat
python generate_postprocess.py   # com_membrane.dat + smac.dat
sh smac.sh                       # smac.txt
```

For the alternate starting positions, run the same sequence from
`{apical,basolateral}/position_{ne,nw,se,sw}/<molecule>/`; the presence of a
non-default `location*.dat` makes `generate_equilibrate.py` move the restraint.

For the semi-isotropic variant, run from
`{apical,basolateral}/semiisotropic/<molecule>/`; `metadynamics.mdp` there is a
symlink to `metadynamics_semiistropic.mdp`.

---

## 4.10 File formats

### 4.10.1 PLUMED outputs

| File | Columns | Notes |
| --- | --- | --- |
| `COLVAR` | `time`, `d_abs`, `mtd.bias`, `r_lig_xy.bias` | Written every 500 steps |
| `HILLS` | `time`, `d_abs`, `sigma_d_abs`, `height`, `biasf` | Metadynamics hills |
| `fes.dat` | `d_abs`, `G`, `dG` | Final FES (`sum_hills`) |
| `fes_0..20.dat` | `d_abs`, `G`, `dG` | Strided FES for convergence |
| `smac.txt` | `time`, `d_abs`, `smac` | Membrane order parameter |
| `com_position.txt` | `p.a`, `p.b`, `p.c` | Ligand COM (scaled) |
| `com_membrane.txt` | `p.x`, `p.y`, `p.z` | Membrane COM |
| `mcfile` | mass/charge | Needed by `plumed driver` |

### 4.10.2 Candidate CSVs

`common/candidates/bbbp_{positive,negative}_pubchem.csv` have columns:

```
idx, InChIID, InChIKey, MolWt, LogP, SMILES, <393 clique columns>, BBB+, logBB
```

`idx` is the PubChem CID and is used as the directory name for the simulation.
The `_old.csv` files are the earlier, larger candidate lists.

### 4.10.3 Index file

`index.ndx` — the first group `[ MEMB ]` lists all membrane atoms. The PLUMED
generators use its first and last atom numbers to define the membrane COM.

---

## 4.11 Analysis commands

### 4.11.1 Notebooks (paper figures)

Run from `ipynb/`:

1. `screen_pubchem.ipynb` — train, screen, select candidates.
2. `analyse_pubchem.ipynb` — distributions, UMAP, Tanimoto.
3. `plot_results.ipynb` — all simulation figures.

### 4.11.2 Standalone scripts

Run from `common/plotting/`:

```bash
python plot_fe.py            # reference FES
python plot_candidates.py    # candidate FES + boxplots + property distributions
python plot_convergence.py   # per-molecule convergence
python plot_correlation.py   # barrier vs experimental logBB
python plot_postprocess.py   # SMAC KDEs
```

### 4.11.3 Barrier extraction recipe

```python
data = pd.read_csv(fn, comment='#', sep=r'\s+', names=['d_abs', 'G', 'dG'])
data = data[(data['d_abs'] > 0) & (data['d_abs'] < 8)]
data['G'] -= data['G'][data['d_abs'] > 7.0].mean()   # zero in water
barrier = data['G'].max()
```

Total barrier = apical barrier + basolateral barrier.

---

## 4.12 Troubleshooting and hardware

| Symptom | Likely cause / fix |
| --- | --- |
| `grompp` duplicate atom type / bond type errors | Ligand `.itp` not de-duplicated against `charmm36-jul2022.ff`; re-run `process_candidate()` in `generate_configurations.py` |
| Ligand fired through the membrane during equilibration | Missing `NOPBC` on the COM in `equilibrate_template.dat` |
| `plumed driver` cannot find masses/charges | `mcfile` missing; run `plumed_driver.sh` (uses `DUMPMASSCHARGE`) |
| GROMACS crashes on a candidate | Azetidine (`C1CNC1`) is poorly parameterised by CGenFF; it is filtered out in `screen_pubchem.ipynb` |
| `sum_hills` output looks wrong | Check `--kt 2.577` (k_BT at 310 K in kJ/mol) |
| Analysis notebook cannot find files | Run from `ipynb/`; paths are relative to it |
| Symlinks broken after moving the repo | Re-run `generate_configurations.py`; symlinks are relative to the repo root |
| `SyntaxError` in `common/plotting/plot_candidates.py` | It uses nested same-type quotes inside f-strings (`f'{args['fn']}...'`), which requires Python ≥ 3.12 (PEP 701). The `Pipfile` pins Python 3.9, so either run it with a newer interpreter or change the inner quotes to `"` |
| Dask dashboard unreachable | `process_pubchem.py` opens an SSH reverse tunnel to a hard-coded host; edit or remove that block for your environment |

The sbatch scripts target the Warwick Sulis cluster:

| Script | GPU | Partition | Account |
| --- | --- | --- | --- |
| `*.sbatch` | A100 | `gpu` | `su007-gcs-gpu` |
| `*_avon.sbatch` | RTX 6000 | `gpu` | (default) |
| `*_l40.sbatch` | L40 | `gpulowpri` | `su007-gpulowpri` |

Adjust the `--account`, `--partition` and `--gres` lines for other clusters.