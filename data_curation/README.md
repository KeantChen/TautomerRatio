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

## Data Provenance & Large File Availability

Due to GitHub repository file size limits (<100 MB), the full 1.2 GB Frag20 raw pickle archive (`frag20_taut_train.pl`) and the 650 MB full DFT dataset (`taut_25w_1224.csv`) are archived in institutional repositories (Zenodo DOI: 10.5281/zenodo.XXXXXXX).

A representative 1,000-molecule subset (`raw_data/frag20_taut/frag20_taut_sample_1000.csv`) as well as the complete raw TautoBase (`tautobase_full_raw.csv`) and SAMPL2 (`samplr2_final.csv`) datasets are included directly in this directory for immediate out-of-the-box execution.
