# Raw Datasets Documentation (Data Management Plan)

**Author:** Cheng Chen  
**Institution:** McGill University / Moitessier Research Group  
**Project:** Tautomer Ratio and Aqueous Tautomerization Free Energy Prediction via Hydra-ResGNN  
**Date:** March 2026  
**License:** MIT  

---

## Overview

This directory (`raw_data/`) hosts the authentic, unaltered source datasets used in the study, preserving the exact data provenance required by institutional Data Management Plans (DMPs):

```
raw_data/
├── frag20_taut/
│   ├── frag20_taut_train.pl          (1.20 GB, training partition pickle)
│   ├── frag20_taut_valid.pl          (40.7 MB, validation partition pickle)
│   ├── frag20_taut_test.pl           (39.9 MB, test partition pickle)
│   ├── taut_25w_1224.csv             (651.6 MB, extracted 250,822 tautomer pool)
│   ├── frag20_taut_sample_1000.csv   (compact sample for rapid CI / testing)
│   ├── process_data_taut.py          (original dataset extraction utility)
│   └── run.s                         (original HPC submission script)
│
├── tautobase/
│   ├── tautobase_full_raw.csv        (435 KB, authentic full 1,680 pairs raw CSV)
│   └── Tautomer_database_release_3a.xlsx (1.83 MB, official Release 3a spreadsheet)
│
└── sampl2/
    ├── samplr2_final.csv             (2.0 KB, authentic 28 pairs experimental challenge)
    ├── smiles-number.csv             (612 B, original identifier mapping)
    └── sampl2_raw_and_calibration_data.csv (5.7 KB, experimental free energy + baseline predictions)
```

---

## Data Provenance & References

1. **Frag20-Taut:**
   - **Source:** Frag20 quantum-chemical benchmark dataset (Huang & von Lilienfeld, *J. Chem. Phys.* 2020 / *Sci. Data*).
   - **Properties:** Gas and aqueous DFT energies computed at B3LYP/6-31G* level of theory with Gaussian 16.
   - **Processing:** Converted and curated via `scripts/00_extract_raw_frag20_taut.py` and `scripts/01_curate_frag20_funnel.py`.

2. **TautoBase:**
   - **Source:** Wahl & Sander, *J. Chem. Inf. Model.* 2020, 60, 4172–4189 (Release 3a).
   - **Properties:** 1,680 experimentally determined tautomeric equilibria across diverse solvents and temperatures.
   - **Processing:** Curated to 539 aqueous pairs with 3-tier domain triage via `scripts/04_curate_benchmark_datasets.py`.

3. **SAMPL2 Tautomer Blind Challenge:**
   - **Source:** Guthrie et al., *J. Comput. Aided Mol. Des.* 2010, 24, 269–281.
   - **Properties:** 28 experimental aqueous tautomer equilibrium constants used for empirical curvature calibration ($k = 0.575$).
