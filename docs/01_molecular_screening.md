# Stage 1 — Machine-Learning Screening and Candidate Selection

This stage trains a small, interpretable machine-learning model on experimental
BBB-permeability data, applies it to the whole of PubChem, and hierarchically
filters the predictions down to a small set of molecules to simulate.

All code for this stage lives in `ipynb/`.

---

## 1.1 Training data

Two datasets are used, both derived from **B3DB** (the BBB database):

| File | Rows | Purpose |
| --- | --- | --- |
| `ipynb/B3DB/B3DB_classification_clean.parquet` | 7,809 | Binary `BBB+/BBB-` classification |
| `ipynb/B3DB/B3DB_regression_clean.csv` | 1,060 | Continuous `logBB` regression |
| `ipynb/B3DB/DrugBank_B3DB_common.csv` | 3,088 | Overlap between DrugBank and B3DB |

The classification table has columns `NO.`, `compound_name`, `IUPAC_name`,
`SMILES`, `CID`, `logBB`, `BBB+/BBB-`, `Inchi`, `threshold`, `reference`,
`group`, `comments`. The regression table is the subset of molecules for which a
`logBB` value is available.

`ipynb/B3DB/B3DB_classification_clean.parquet.vocab` is a pickled
`(vocab, mol_dict)` pair produced by the descriptor pipeline (see §1.2). The
vocabulary contains **393 cliques**.

---

## 1.2 The clique-decomposition descriptor

Rather than using a fixed fingerprint, the model uses a **clique decomposition**
of each molecule, implemented in `ipynb/cliques/` (a JT-VAE-style molecular
tree decomposition):

- `cliques/mol_tree.py` — `MolTree` decomposes a molecule into a tree of
  ring systems, bonds and linker atoms (`tree_decomp` in `chemutils.py`).
- `cliques/cliques.py` — `Vocabulary()` collects the set of clique SMILES
  present in a dataset; `SingleCliqueDecomposition()` converts one molecule into
  a count vector over that vocabulary.

Each molecule is therefore represented as a **393-dimensional integer vector**
counting how many times each clique occurs (clipped to `uint8`, i.e. 0–255).
This descriptor is sparse, chemically interpretable, and cheap to compute, which
is what makes screening all of PubChem tractable.

The vocabulary is built from the B3DB SMILES and reused for PubChem, so a
PubChem molecule is only representable if all of its cliques appear in B3DB.

---

## 1.3 PubChem pre-processing — `ipynb/process_pubchem.py`

This is a Dask pipeline that turns the raw NIH PubChem dump into a parquet file
of descriptors. It expects a tab-separated file with columns
`idx`, `InChIID`, `InChIKey` (the NIH CID/InChI/InChIKey dump) and the B3DB
parquet.

Steps:

1. Start a `dask.distributed.LocalCluster` (`--n_jobs` workers, `--n_threads`
   threads each, `--memory` per worker). An SSH reverse tunnel is opened for the
   Dask dashboard (hard-coded to a specific host; environment-specific).
2. **Filter** each molecule (`filter_molecules`):
   - reject any molecule containing a "heavy" atom. The `heavy_atoms` set is
     atomic numbers 21–29, 31–34, 37–52 and 55–118 — i.e. transition metals,
     post-transition metals, metalloids, lanthanides and actinides. Notably it
     **excludes** Zn (30), Br (35), Kr (36), I (53) and Xe (54), so common
     halogens are allowed;
   - reject molecules with RDKit `MolWt > 1000` (mainly to keep the clique
     decomposition fast; almost no B3DB molecule exceeds this).
3. Compute `MolWt`, `LogP` (RDKit Crippen), canonical `SMILES`, and the
   393-dimensional clique vector for every surviving molecule.
4. Write the result to parquet (gzip/pyarrow).

The pipeline is resumable: intermediate parquet files and the pickled
vocabulary are cached next to the inputs.

---

## 1.4 Model training and evaluation — `ipynb/screen_pubchem.ipynb`

Two random forests are trained on the clique vectors:

```python
clf     = RandomForestClassifier(n_estimators=128, random_state=42)  # BBB+/BBB-
clf_logbb = RandomForestRegressor(n_estimators=128, random_state=42) # logBB
```

Rows whose clique vector is all-zero are dropped from training
(`np.any(X_train > 0, axis=1)`).

**Evaluation** uses repeated 5-fold cross-validation (10 repeats, `random_state`
0–9). The notebook reports:

- precision/recall for BBBP+ at a probability threshold of **1.0** (all trees
  vote positive);
- precision/recall for BBBP− at a threshold of **0.05** (≈6 of 128 trees vote
  positive);
- RMSE and R² for `logBB`, compared against the standard deviation of `logBB`.

These extreme thresholds are deliberate: the screen is used as a *high-confidence
enrichment* step, not as a calibrated probabilistic classifier.

The final forests are refit on all data and pickled to
`ipynb/forest_clf.pickle` and `ipynb/forest_rgr.pickle`.

---

## 1.5 Screening PubChem

`predict_forest()` is mapped over the PubChem parquet with Dask, adding two
columns:

- `BBB+` — predicted probability of being BBB-permeable;
- `logBB` — predicted `logBB`.

The full predictions are written to `ipynb/pred_pubchem.parquet`, and the two
extreme sets are extracted:

- **BBBP+ candidates**: `BBB+ == 1.0`
- **BBBP− candidates**: `BBB+ <= 0.05`

---

## 1.6 Hierarchical filtering

The funnel plot in `ipynb/plot_results.ipynb` (`funnel_pubchem.png`) records the
following counts, which are the authoritative numbers for the screen:

| Stage | BBBP+ | BBBP− |
| --- | ---: | ---: |
| PubChem after pre-processing | 112,194,965 | 112,194,965 |
| Random-forest screening | 197,884 | 96,949 |
| Molecular weight ≤ 500 and 2 ≤ LogP ≤ 10 | 115,003 | 10,741 |
| Remove previously studied molecules (B3DB + DrugBank) | 112,598 | 9,117 |
| Remove poorly represented molecules | 4,209 | 964 |
| **Final candidates for metadynamics** | **10** | **10** |

The filters, in the order applied in `screen_pubchem.ipynb`:

1. **Random-forest screen** — keep `BBB+ == 1.0` (positive) or `BBB+ <= 0.05`
   (negative).
2. **Physicochemical filters** — `MolWt <= 500` and `2 <= LogP <= 10`. The LogP
   lower bound keeps molecules lipophilic enough to be plausible membrane
   permeants; the upper bound excludes extreme lipophiles.
3. **Remove previously studied molecules** — drop any PubChem molecule whose
   InChI already appears in B3DB, and any whose InChI identifier or InChI-key
   first block appears in DrugBank (`DrugBank/structures.sdf`). This prevents
   the model from "rediscovering" its own training data.
4. **Remove poorly represented molecules** — drop molecules whose clique vector
   is all-zero, and molecules containing cliques not present in the B3DB
   vocabulary (`contains_unknown_cliques`).
5. **Remove non-unique representations** — `drop_duplicates(subset=vocab,
   keep=False)` removes molecules that share an identical clique vector with
   another molecule, so each simulated molecule has a unique descriptor.
6. **Remove azetidine-containing molecules** — the clique `C1CNC1` is excluded
   because CHARMM-GUI/CGenFF parameterises it poorly and GROMACS crashes on it.
7. **Select the extremes** — sort by predicted `logBB` and keep the highest
   (positive) and lowest (negative) molecules. The notebook's final cell is
   parameterised to keep up to 30 per class; the committed candidate lists
   (`common/candidates/bbbp_{positive,negative}_pubchem.csv`) and the funnel
   plot both contain **10 per class**.

The resulting CSVs contain the columns `idx` (PubChem CID), `InChIID`,
`InChIKey`, `MolWt`, `LogP`, `SMILES`, the 393 clique columns, `BBB+` and
`logBB`. The `_old.csv` files are the earlier, larger (~52 per class) candidate
lists retained for reference.

---

## 1.7 Reference molecules

Five hand-picked molecules are simulated alongside the candidates to anchor the
free-energy results to known experimental behaviour:

| Molecule | Experimental `logBB` |
| --- | ---: |
| trihexyphenidyl | 1.32 |
| isopropanol | −0.10 |
| caffeine | (BBB+, no value used in the correlation script) |
| morphine-6-glucuronide | −2.09 |
| sucrose | −1.70 |

The `logBB` values above are the ones hard-coded in
`common/plotting/plot_correlation.py`. Molecules with `logBB > −1` are treated
as BBBP+ in that script.

---

## 1.8 Validation of the screen — `ipynb/analyse_pubchem.ipynb`

This notebook characterises the screen and checks that the candidates are not
trivially similar to the training set:

- **Prediction distributions** — overlays the PubChem and B3DB predicted
  `BBB+`/`logBB` histograms (`histogram_bbbp.png`, `histogram logbb.png`).
  Histogram counts are cached to `hist_pubchem.csv`, `histbins_pubchem.csv`,
  `hist_b3db.csv`, `histbins_b3db.csv` so the figure can be regenerated without
  the full PubChem dataframe.
- **Chemical-space coverage** — UMAP embeddings of Morgan fingerprints
  (radius 3, 2048 bits) and MACCS keys (167 bits), using the Jaccard metric
  (`n_neighbors=100`, `min_dist=0.1`, `random_state=1209`). A 100,000-molecule
  PubChem subset is embedded together with B3DB and the candidates
  (`umap_morgan.png`, `umap_maccs.png`). The embeddings are cached as `.npy`
  files.
- **Similarity to training data** — Tanimoto similarity of every candidate to
  the B3DB set, using both Morgan and MACCS fingerprints, reporting max/mean/
  standard deviation and the most similar B3DB molecule.

---

## 1.9 Next steps

The 20 selected candidates (10 positive, 10 negative) are parameterised and
prepared for simulation in `common/candidates/` (see
`docs/03_ligand_insertion_and_metadynamics.md`), while the two membranes are
built and equilibrated as described in `docs/02_membrane_preparation.md`.