# Data Curation, Featurization & Benchmark Reproduction Pipeline

**Author:** Cheng Chen  
**Institution:** Department of Chemistry, McGill University / Moitessier Research Group  
**Date:** March 2026  
**License:** MIT  

---

## Overview

This directory provides the end-to-end data processing and benchmark curation code supporting the manuscript:
**"Predicting Aqueous Tautomer Free Energies with Chemical Accuracy via Multi-Tower Equivariant Graph Neural Networks and Physics-Informed Domain Triage"**.

It bridges raw chemical databases with model training and experimental validation:
1. **Raw Database Ingestion**: Frag20-Taut (DFT reference calculations), TautoBase (Release 3a), and SAMPL2 tautomer blind challenge.
2. **Quality & Stoichiometric Filtering**: Strict elemental conservation (C, H, N, O only), chemical valence checks, and Bemis-Murcko capacity-constrained downsampling (reproducing Table S1).
3. **Quantum Featurization**: 3D conformer embedding via ETKDGv3 and GFN2-xTB / g-xTB implicit water solvation descriptors.
4. **Graph Serialization**: PyTorch Geometric `Data` tensor construction under zero-leakage Bemis-Murcko scaffold partitioning (88% train / 10% val / 2% test).
5. **Experimental Benchmarking**: 3-tier topological applicability domain triage on 539 TautoBase pairs and empirical curvature calibration ($k = 0.575$) on SAMPL2.

---

## Pipeline Execution Sequence

| Stage | Script | Purpose | Key Output |
|---|---|---|---|
| **00** | `00_extract_raw_frag20_taut.py` | Extracts raw `.pl` partitions from Frag20 archive | `taut_extracted_from_pl.csv` |
| **01** | `01_curate_frag20_funnel.py` | Curation funnel & capacity-constrained downsampling (Table S1) | `frag20_curated_150k.csv` |
| **02** | `02_run_conformer_and_xtb.py` | 3D conformers (ETKDGv3) & GFN2-xTB single point | `dataset_with_xtb_features.csv` |
| **02b** | `02b_run_gxtb_and_merge.py` | g-xTB electronic descriptors & multi-tower feature merging | `Master_Dataset_Final_Train_Ready.csv` |
| **03** | `03_build_scaffold_pt_dataset.py` | Bemis-Murcko scaffold split (88/10/2) & PyG tensor serialization | `pt_datasets/*.pt` |
| **03b** | `03b_fit_scalers.py` | Computes z-score scalers on training split | `scalers/*.pt` |
| **04** | `04_curate_benchmark_datasets.py` | Extracts TautoBase (539 aqueous pairs) & SAMPL2 | `benchmarks/*.csv` |
| **05** | `05_train_hydra_resgnn.py` | Model training with AdamW, Huber loss, and GPU acceleration | `checkpoints/hydra_resgnn_best.pt` |
| **06** | `06_calibrate_and_evaluate.py` | SAMPL2 calibration & TautoBase 3-tier triage evaluation | Table 2 & Table 3 metrics |
| **07** | `07_master_reproduce.py` | Automated master runner executing all 9 stages | Verified in ~18 s |

---

## Quick Start (One Command Verification)

```bash
# Activate your conda environment
conda activate chem

# Navigate to data_curation directory
cd data_curation

# Execute master reproduction suite
python 07_master_reproduce.py
```

---

## Data Provenance & Original Data Sources

The complete raw datasets (Frag20-Taut, TautoBase, and SAMPL2) are preserved under the institutional Data Management Plan (DMP) archive and are available upon request or directly through their primary literature sources.

Alternatively, researchers can obtain the full, unmodified raw archives directly from their respective primary literature and data repositories:
- **Frag20-Taut / SPhysNet-Taut**: The primary raw pickle partitions (`frag20_taut_train.pl`, `frag20_taut_valid.pl`, `frag20_taut_test.pl`) and DFT reference calculations originate from:
  > *"Fast and Accurate Prediction of Tautomer Ratios in Aqueous Solution via a Siamese Neural Network"*, *J. Chem. Theory Comput.* 2025, 21 (6), 3132–3142. [ACS JCTC Article Link](https://pubs.acs.org/jctcce/article/21/6/3132/3775827/Fast-and-Accurate-Prediction-of-Tautomer-Ratios-in).
- **TautoBase**: The primary database files (`Tautomer_database_release_3a.xlsx` and `tautobase_full_raw.csv`) are openly accessible from:
  > Wahl, J.; Sander, T. *"TautoBase: An Open Tautomer Database"*, *J. Chem. Inf. Model.* 2020, 60 (9), 4172–4189. [DOI: 10.1021/acs.jcim.0c00713](https://doi.org/10.1021/acs.jcim.0c00713).
- **SAMPL2 Tautomer Blind Challenge**: The 28 experimental aqueous equilibria originate from:
  > Geballe, M. T.; Guthrie, J. P. *"The SAMPL2 blind prediction challenge: introduction and overview"*, *J. Comput. Aided Mol. Des.* 2010, 24 (4), 259–279. [DOI: 10.1007/s10822-010-9350-8](https://link.springer.com/article/10.1007/s10822-010-9350-8).

A representative 1,000-molecule subset (`raw_data/frag20_taut/frag20_taut_sample_1000.csv`) as well as the complete raw TautoBase (`tautobase_full_raw.csv`) and SAMPL2 (`samplr2_final.csv`) datasets are included directly in this directory for immediate out-of-the-box execution.
