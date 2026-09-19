# BBBP-MD

A combined machine-learning + molecular-dynamics workflow for studying passive
permeation of small molecules across the blood–brain barrier (BBB).

The project couples a cheap, interpretable machine-learning screen of the entire
PubChem database to explicit-solvent, well-tempered metadynamics simulations of
two model membranes (an **apical** and a **basolateral** leaflet model). The
simulations produce free-energy profiles for pulling a molecule through each
membrane, which are then compared against the machine-learning predictions and
against experimental `logBB` values for a set of reference compounds.

The repository accompanies a manuscript (see `composition-nature-paper.txt` for
the membrane compositions used) and also contains the extra simulations added
during peer review (alternate ligand starting positions and a semi-isotropic
pressure-coupling variant).

> **Disclaimer.** All of the work in this repository — the machine learning, the
> code, and the molecular dynamics simulations and analysis — was done by the
> repository author. This README and the documentation in `docs/` were generated
> by **DeepSeek V4.1 Flash (low thinking setting)**. While the documentation was
> written from a detailed reading of the repository, it may contain errors or
> omissions; the code and simulation inputs are the authoritative source.

---

## 1. Scientific overview

The workflow has five stages:

1. **Machine-learning screening of PubChem** (`ipynb/`, `common/candidates/`).
   A random forest is trained on the B3DB dataset using a *clique decomposition*
   molecular descriptor. The trained classifier/regressor is applied to all of
   PubChem to predict BBB permeability (`BBB+` probability) and `logBB`. A
   hierarchical set of filters then narrows ~112 million molecules down to 10
   predicted-permeable and 10 predicted-impermeable candidates for simulation.

2. **Membrane construction and equilibration** (`apical/`, `basolateral/`,
   `common/step6.*.mdp`). Two CHARMM36m lipid bilayers representing the apical
   and basolateral faces of the BBB are built with CHARMM-GUI Membrane Builder
   and equilibrated with GROMACS. Each bilayer is symmetric between its
   leaflets, but the two membranes have different lipid compositions.

3. **Ligand insertion and re-equilibration** (`common/metadynamics/`). Each
   candidate is parameterised with CHARMM-GUI Ligand Designer, inserted into the
   equilibrated membrane, and re-equilibrated under a PLUMED restraint that
   holds the ligand in the water phase.

4. **Well-tempered metadynamics** (`common/metadynamics/`). The ligand is driven
   across the membrane along the absolute distance from the membrane centre of
   mass, giving a free-energy profile (FES) and hence a permeation barrier.

5. **Analysis** (`ipynb/`, `common/plotting/`). Free-energy barriers are
   extracted, compared between predicted-permeable and predicted-impermeable
   sets, correlated with experimental `logBB`, and complemented by membrane-order
   (SMAC) and convergence analyses.

---

## 2. Repository layout

```
BBBP-MD/
├── README.md                     This file
├── composition-nature-paper.txt  Per-leaflet lipid counts for the two membranes
│
├── ipynb/                        All Python analysis code and notebooks
│   ├── screen_pubchem.ipynb      Train RF on B3DB, screen PubChem, select candidates
│   ├── analyse_pubchem.ipynb     Distribution / UMAP / Tanimoto analysis of the screen
│   ├── plot_results.ipynb        All simulation-result figures for the paper
│   ├── process_pubchem.py        Dask pipeline: filter PubChem + clique descriptors
│   ├── cliques/                  Clique-decomposition descriptor (JT-VAE style)
│   ├── B3DB/                     Training data (classification + regression)
│   ├── Pipfile                   Python environment (pipenv)
│   └── *.png, *.npy, *.csv       Cached figures and intermediate data
│
├── common/                       Shared simulation inputs and helper scripts
│   ├── step6.0–6.6_*.mdp         Membrane minimisation + 6 equilibration stages
│   ├── step7_production.mdp      Membrane production MD
│   ├── run_default.sh/.sbatch    CHARMM-GUI-style membrane run script
│   ├── candidates/               Candidate selection + CHARMM-GUI ligand setup
│   │   ├── generate_configurations.py
│   │   ├── print_candidates.py
│   │   ├── bbbp_{positive,negative}_pubchem.csv
│   │   └── pos/, neg/            Per-candidate CHARMM-GUI ligand output
│   ├── metadynamics/             Insertion / equilibration / metadynamics machinery
│   │   ├── *.mdp                 equilibrate_nvt, equilibrate, metadynamics (+semiisotropic)
│   │   ├── *_template.dat        PLUMED templates
│   │   ├── generate_*.py         PLUMED input generators
│   │   ├── insert-molecule.{sh,py}
│   │   ├── *.sbatch              Sulis / Avon / L40 job scripts
│   │   └── charmm36-jul2022.ff/  CHARMM36m force field
│   └── plotting/                 Standalone plotting scripts
│
├── apical/                       Apical membrane system
│   ├── charmm-gui-3989364611/    CHARMM-GUI Membrane Builder output
│   ├── gromacs/                  Equilibrated membrane + reference molecules
│   ├── candidates/{pos,neg}/     Metadynamics runs for the 20 candidates
│   ├── position_{ne,nw,se,sw}/   Alternate ligand starting positions (reviewer request)
│   └── semiisotropic/            Semi-isotropic pressure-coupling variant
│
├── basolateral/                  Basolateral membrane system (same layout as apical/)
│
├── charmm-gui-2066971497/        Earlier/alternative membrane model (DOPE/DOPC/23SM)
├── DrugBank/structures.sdf       DrugBank structures used for duplicate filtering
└── docs/                         Detailed documentation (see below)
```

> **Note on data volume.** The `apical/` and `basolateral/` trees contain the
> full simulation output (trajectories, checkpoints, HILLS, COLVAR, FES files)
> for every candidate and reference molecule. These are large; the analysis
> scripts read them directly from disk.

---

## 3. Documentation

Detailed, stage-by-stage documentation lives in `docs/`:

| Document | Contents |
| --- | --- |
| [`docs/01_molecular_screening.md`](docs/01_molecular_screening.md) | B3DB training data, clique descriptor, random forest, hierarchical PubChem filtering, candidate selection, UMAP/Tanimoto validation |
| [`docs/02_membrane_preparation.md`](docs/02_membrane_preparation.md) | Membrane compositions, CHARMM-GUI build, GROMACS minimisation/equilibration protocol |
| [`docs/03_ligand_insertion_and_metadynamics.md`](docs/03_ligand_insertion_and_metadynamics.md) | Ligand parameterisation, insertion, re-equilibration, PLUMED metadynamics, FES generation, SMAC, alternate positions, semi-isotropic variant |
| [`docs/04_analysis_and_insights.md`](docs/04_analysis_and_insights.md) | Analysis notebooks and scripts, barrier extraction, statistics, convergence, figures, plus the practical reference (environment, file formats, commands, troubleshooting) |

---

## 4. Quick start

### 4.1 Environment

The analysis code is a Python 3.9 environment managed with `pipenv`
(`ipynb/Pipfile`). Key dependencies: `rdkit-pypi`, `numpy`, `pandas`, `dask`,
`scikit-learn`, `umap-learn`, `matplotlib`, `seaborn`, `plotly`, `pyarrow`.

```bash
cd ipynb
pipenv install
pipenv run jupyter notebook
```

On the Warwick Sulis cluster, `ipynb/modules.sh` loads the required modules and
`ipynb/jupyter_interactive.sh` requests an interactive node.

### 4.2 Reproducing the screen

1. Pre-process PubChem with `ipynb/process_pubchem.py` (Dask; expects the
   NIH PubChem CID/InChI/InChIKey dump and the B3DB parquet).
2. Run `ipynb/screen_pubchem.ipynb` to train the forests, predict on PubChem,
   apply the filters, and write
   `common/candidates/bbbp_{positive,negative}_pubchem.csv`.
3. Run `ipynb/analyse_pubchem.ipynb` for the distribution/UMAP/Tanimoto figures.

### 4.3 Running the simulations

Simulations require GROMACS 2023.3 built with PLUMED 2.9 (the sbatch scripts
load `GROMACS/2023.3-CUDA-12.1.1-PLUMED-2.9.0`).

Membrane equilibration (per membrane, from `apical/gromacs/` or
`basolateral/gromacs/`):

```bash
sbatch run_default.sbatch      # minimisation + step6.1–6.6 + step7 production
```

Per-candidate metadynamics (from a candidate directory such as
`apical/candidates/pos/129723484/`):

```bash
python insert-molecule.py      # insert ligand, fix topology
sh genion.sh                   # neutralise with Na+/Cl- (if needed)
python generate_equilibrate.py # write equilibrate.dat / ini_com.dat
sh plumed_driver.sh            # compute ligand COM (com_position.txt)
python generate_metadynamics.py
sbatch equilibrate.sbatch      # NVT then NPT re-equilibration
sbatch metadynamics.sbatch     # 200 ns well-tempered metadynamics
sh sum_hills.sh                # fes.dat + fes_0..20.dat
python generate_postprocess.py # com_membrane.dat + smac.dat
sh smac.sh                     # smac.txt
```

### 4.4 Analysis

Open `ipynb/plot_results.ipynb` and run it from the `ipynb/` directory; it reads
the FES/SMAC files under `../apical` and `../basolateral` and writes the paper
figures. The standalone equivalents are in `common/plotting/`.

---

## 5. Key results produced

- `ipynb/funnel_pubchem.png` — hierarchical filtering funnel.
- `ipynb/histogram_bbbp.png`, `histogram logbb.png` — predicted distributions.
- `ipynb/umap_morgan.png`, `umap_maccs.png` — chemical-space coverage.
- `ipynb/{apical,basolateral}_candidates_boxplot.png` — barrier distributions.
- `ipynb/total_candidates_boxplot.png` — summed apical + basolateral barriers.
- `ipynb/reference_fes_{apical,basolateral}.png` — reference-molecule FES.
- `ipynb/reference_fes_band_{apical,basolateral}.png` — FES uncertainty bands
  from alternate starting positions.
- `ipynb/convergence_{apical,basolateral}.png` — metadynamics convergence.
- `ipynb/{apical,basolateral}_smac_{pos,neg}.png` — membrane-order (SMAC) KDEs.
- `ipynb/semiistropic_fes_{apical,basolateral}.png` — semi-isotropic variant.

---

## 6. Software and force fields

| Component | Version / choice |
| --- | --- |
| MD engine | GROMACS 2023.3 (CUDA 12.1.1) |
| Enhanced sampling | PLUMED 2.9.0 |
| Force field | CHARMM36m (`charmm36-jul2022.ff`, `toppar/`) |
| Water | TIP3P |
| Ions | Na⁺ (SOD) / Cl⁻ (CLA) |
| Membrane builder | CHARMM-GUI Membrane Builder (v3.7) |
| Ligand parameterisation | CHARMM-GUI Ligand Designer (CGenFF) |
| ML | scikit-learn random forests on a clique-decomposition descriptor |
| Analysis | Python 3.9, RDKit, Dask, UMAP, matplotlib/seaborn/plotly |

---

## 7. Citation

If you use this repository, please cite the associated manuscript. The membrane
compositions used are recorded in `composition-nature-paper.txt`.