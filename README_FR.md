# Hydra-PaiNN: Physics-Informed Multi-Tower Delta-Learning and Applicability Domain Triage for Aqueous Tautomer Ratios

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/KeantChen/TautomerRatio/blob/main/notebooks/Hydra_PaiNN_Quickstart.ipynb)
[![GitHub](https://img.shields.io/badge/GitHub-Repository-blue.svg?logo=github)](https://github.com/KeantChen/TautomerRatio)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

> **Langues / Languages / 语言版本** : [English](README.md) | [中文 (Chinese)](README_CN.md) | [Français (French)](README_FR.md)

Hydra-PaiNN is an open-source, physics-informed machine learning pipeline for predicting tautomeric aqueous free energy differences (**ΔG_aq**), equilibrium constants (**K_eq**), and Boltzmann population distributions in aqueous solution.

$$
\Delta G_{\text{aq}} = -RT \ln K_{\text{eq}}, \quad K_{\text{eq}} = \frac{[\text{Tautomer B}]}{[\text{Tautomer A}]}
$$

The framework integrates:
1. **PaiNN Equivariant Neural Message Passing**: Captures directional, continuous 3D geometric and electronic interactions.
2. **Semi-Empirical Quantum Chemistry Baseline**: Couples GFN2-xTB (ALPB implicit water) with optional g-xTB electronic descriptors.
3. **Connectivity-Based Hierarchy (CBH-Taut) Triage**: A 2D SMILES graph diagnostic based on Raghavachari homodesmotic rules that identifies whether systematic baseline errors cancel prior to quantum calculations, routing high-risk aromatic breakdown cases.

---

## ⚡ Quickstart on Google Colab (Zero-Setup in Browser)

You can run Hydra-PaiNN directly in your browser without installing anything locally:

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/KeantChen/TautomerRatio/blob/main/notebooks/Hydra_PaiNN_Quickstart.ipynb)

* **Interactive Form**: Type any two SMILES and instantly view 2D structures labeled with Boltzmann population percentages.
* **Formatted Summary Cards**: Inspect ΔG, K_eq, and applicability domain diagnostics.
* **Batch CSV Processing**: Upload your own dataset and download predicted ratios.
* **Cloud Acceleration**: Runs on free Google Colab Cloud CPU/GPU (automatic CUDA acceleration).

---

## 🎯 Applicability Domains & Confidence Hierarchy

In our manuscript, tautomer pairs are partitioned upfront into rigorous chemical domains based on aromaticity conservation and Raghavachari Connectivity-Based Hierarchy (CBH) theory:

### 1. Comfort Zone ($|\Delta N_{\text{aro}}| = 0$, 79.4% of Dataset)
Aromaticity is strictly conserved between tautomeric forms. Within this domain, systematic continuum solvation and tight-binding errors cancel reliably:
* **CBH-Taut Subset** (11.3% of TautoBase-539, 61 pairs):
  * **Criterion**: Heavy-atom hybridization states ($H_i$) and covalent bond topologies ($B_{ij}$) are strictly invariant across tautomers under Raghavachari homodesmotic rules.
  * **Performance**: Systematic baseline errors cancel out almost completely, reaching chemical accuracy:
    * **TautoBase-539**: MAE = **1.29 kcal/mol** (median = 1.15 kcal/mol, RMSE = 1.76 kcal/mol).
    * **DFT-460**: MAE = **1.38 kcal/mol** (exceeds high-level DFT reference MAE of 1.56 kcal/mol).
    * **sPhysNet-Taut-100**: MAE = **1.02 kcal/mol**.
* **Normal Subset** (68.1% of TautoBase-539, 367 pairs):
  * **Criterion**: Aromaticity is conserved, with standard localized bond and hybridization rearrangements.
  * **Performance**: High fidelity across drug-like scaffolds:
    * **TautoBase-539**: MAE = **1.97 kcal/mol** (median = 1.53 kcal/mol, RMSE = 2.56 kcal/mol, Direction Acc = 88.3%).
    * **DFT-460**: MAE = **1.78 kcal/mol** (matches high-level DFT reference MAE of 1.82 kcal/mol).
    * **sPhysNet-Taut-100**: MAE = **1.82 kcal/mol**.

### 2. Risk Zone ($|\Delta N_{\text{aro}}| > 0$, 20.6% of Dataset, 111 pairs)
Transformations accompanied by the creation or destruction of aromatic rings (e.g., phenol $\leftrightarrow$ 2,4-cyclohexadienone, pyrazole $\leftrightarrow$ enamine).
* **Performance**:
  * **TautoBase-539**: MAE = **5.14 kcal/mol** (median = 4.06 kcal/mol, RMSE = 6.73 kcal/mol).
  * **DFT-460**: Hydra-PaiNN MAE = **4.38 kcal/mol**.
* **Physical Chemistry Root Cause & Ongoing Development**:
  Aromaticity breakdown induces large shifts in Aromatic Stabilization Energy (ASE) and severe discrete solvent reorganization that breaks continuum dielectric cancellation. Importantly, **even uncalibrated multi-conformation high-level DFT (B3LYP/aug-cc-pVTZ//B3LYP/6-31G(d)/SMD) struggles in this regime with an elevated MAE of 4.07 kcal/mol**, confirming that continuum solvent physics reaches an intrinsic ceiling. **Update is coming soon.**

---

### 📊 Mapping to a Practical 3-Tier Confidence Hierarchy

For high-throughput screening and automated scoring pipelines, these three domains naturally map into a clean **3-Tier confidence hierarchy**:

| Tier | Domain / Subset | Criteria | Expected MAE | Confidence Level | Recommended Pipeline Application |
| :---: | :--- | :--- | :---: | :---: | :--- |
| **Tier 1** | **CBH-Taut Subset** | $\|\Delta N_\text{aro}\| = 0$, strict homodesmotic invariance | **1.29 kcal/mol** | **Ultra-High** | Quantitative binding affinity & potency ranking |
| **Tier 2** | **Normal Subset** | $\|\Delta N_\text{aro}\| = 0$, standard aromatic/aliphatic scaffold | **1.97 kcal/mol** | **High** | High-throughput virtual screening & lead optimization |
| **Tier 3** | **Risk Zone** | $\|\Delta N_\text{aro}\| > 0$, aromaticity transition/breakdown | **5.14 kcal/mol** | **Caution** | Flags aromatic disruption (Update is coming soon) |

---

## 💻 Local Installation & Setup

### 1. Clone & Set Up Python Environment
```bash
git clone https://github.com/KeantChen/TautomerRatio.git
cd TautomerRatio

# Using pip
pip install -r requirements.txt
```

### 2. Verify Installation
Run the automated self-test script to verify dependencies, model weights, and quantum engines:
```bash
python verify_installation.py
```

---

## 🚀 Command-Line Usage

### 1. Fast 2D Topological Triage (< 1 ms)
Examine domain applicability and expected uncertainty without running any quantum chemistry:
```bash
python predict.py --smi1 "OC1=CC=CC=N1" --smi2 "O=C1NC=CC=C1" --triage_only
```

### 2. Standard Prediction (xTB Tower-A, Standalone)
Predict aqueous free energy difference, equilibrium constant, and dominant tautomer:
```bash
python predict.py --smi1 "OC1=CC=CC=N1" --smi2 "O=C1NC=CC=C1" --mode xtb_only
```

### 3. Multi-Tower Prediction (Towers A, B, and C)
If g-xTB is configured (see [bin/README_ENGINES.md](bin/README_ENGINES.md)):
```bash
python predict.py --smi1 "OC1=CC=CC=N1" --smi2 "O=C1NC=CC=C1" --mode three_towers
```

### 4. Batch Prediction from CSV
Evaluate a dataset of tautomer pairs:
```bash
python predict.py --input examples/test_cases.csv --output predictions.csv --mode xtb_only
```

---

## 🐍 Python API Usage

```python
from tautomer_predictor import TautomerPredictor

# 1. Initialize predictor (loads weights and scalers)
predictor = TautomerPredictor()

# 2. Fast 2D Triage
triage = predictor.triage_check("OC1=CC=CC=N1", "O=C1NC=CC=C1")
print(f"Domain: {triage['domain']} ({triage['subset']}) | Expected MAE: {triage['expected_mae']} kcal/mol")

# 3. Full 3D + Quantum + ML Prediction
result = predictor.predict(
    smiles_A="OC1=CC=CC=N1",
    smiles_B="O=C1NC=CC=C1",
    mode="xtb_only",       # or "three_towers"
    temperature=298.15,    # Kelvin
    solvent="water"        # ALPB solvent
)

# Print formatted report
predictor.print_report(result)
```

---

## 📁 Directory Structure

```text
TautomerRatio/
├── notebooks/
│   └── Hydra_PaiNN_Quickstart.ipynb # Interactive Google Colab notebook
├── bin/
│   ├── xtb.exe                      # Pre-compiled xTB 6.7.1 (Windows)
│   ├── libiomp5md.dll               # Intel OpenMP runtime
│   └── README_ENGINES.md            # Instructions for Linux & WSL setup
├── models/
│   ├── hydra_painn_best.pth         # Trained PyTorch model weights (Seed 42)
│   └── scalers/                     # Pre-fitted feature normalization scalers
├── examples/
│   ├── test_cases.csv               # Curated validation pairs across 3 tiers
│   └── test_predictions.csv         # Reference execution output
├── tautomer_predictor.py            # Core Python prediction engine
├── predict.py                       # Command-line interface (CLI)
├── verify_installation.py           # Self-test diagnostic script
├── CASE_STUDIES.md                  # Detailed walkthrough of validation cases
├── README.md                        # Documentation (English)
├── README_CN.md                     # Documentation (Chinese)
└── README_FR.md                     # Documentation (French)
```

---

## 📖 Citation

If you use Hydra-PaiNN in your research, please cite our manuscript:

```bibtex
@article{hydra_painn_2026,
  title={Physics-Informed Multi-Tower Delta-Learning and Applicability Domain Triage for Aqueous Tautomer Ratios},
  author={Chen, et al.},
  journal={Journal of Chemical Information and Modeling},
  year={2026}
}
```

---

## 📄 License
This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
