# Hydra-PaiNN: Physics-Informed Multi-Tower Delta-Learning and Applicability Domain Triage for Aqueous Tautomer Ratios

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/KeantChen/TautomerRatio/blob/main/notebooks/Hydra_PaiNN_Quickstart.ipynb)
[![GitHub](https://img.shields.io/badge/GitHub-Repository-blue.svg?logo=github)](https://github.com/KeantChen/TautomerRatio)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

> **Languages / 语言版本 / Langues** : [English](README.md) | [中文 (Chinese)](README_CN.md) | [Français (French)](README_FR.md)

Hydra-PaiNN is an open-source machine learning pipeline for predicting tautomeric aqueous free energy differences (**ΔG_aq**), equilibrium constants (**K_eq**), and Boltzmann population distributions in aqueous solution.

$$
\Delta G_{\text{aq}} = -RT \ln K_{\text{eq}}, \quad K_{\text{eq}} = \frac{[\text{Tautomer B}]}{[\text{Tautomer A}]}
$$

The framework integrates:
1. **PaiNN Equivariant Neural Message Passing**: Captures directional 3D geometric interactions.
2. **Semi-Empirical Quantum Chemistry**: Couples GFN2-xTB (ALPB implicit water) with optional g-xTB descriptors.
3. **Applicability Domain Triage**: A 2D SMILES graph diagnostic based on aromaticity conservation and Raghavachari Connectivity-Based Hierarchy (CBH) rules.

---

## ⚡ Quickstart on Google Colab (Zero-Setup in Browser)

Run Hydra-PaiNN directly in Google Colab without local installation:

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/KeantChen/TautomerRatio/blob/main/notebooks/Hydra_PaiNN_Quickstart.ipynb)

* **Interactive Form**: Input two SMILES to view 2D structures and predicted Boltzmann population percentages.
* **Summary Cards**: Inspect ΔG, K_eq, and domain diagnostics.
* **Batch CSV Processing**: Upload a CSV file and download predicted values.
* **Hardware**: Runs on Google Colab CPU/GPU.

---

## 🎯 Applicability Domains & Subsets

Tautomer pairs are partitioned upfront based on aromaticity conservation and Raghavachari Connectivity-Based Hierarchy (CBH) rules:

### 1. Comfort Zone ($|\Delta N_{\text{aro}}| = 0$, 79.4% of Dataset)
Tautomer pairs with conserved aromatic atom counts:
* **CBH-Taut Subset** (11.3% of TautoBase-539, 61 pairs):
  * **Criteria**: Heavy-atom hybridization states ($H_i$) and covalent bond topologies ($B_{ij}$) are invariant across tautomers under Raghavachari homodesmotic rules.
  * **Results**:
    * **TautoBase-539**: MAE = **1.29 kcal/mol** (median = 1.15 kcal/mol, RMSE = 1.76 kcal/mol).
    * **DFT-460**: MAE = **1.38 kcal/mol** (DFT reference: MAE = 1.56 kcal/mol).
    * **sPhysNet-Taut-100**: MAE = **1.02 kcal/mol**.
* **Normal Subset** (68.1% of TautoBase-539, 367 pairs):
  * **Criteria**: Aromaticity is conserved (|ΔN_aro| = 0), with localized bond and hybridization rearrangements.
  * **Results**:
    * **TautoBase-539**: MAE = **1.97 kcal/mol** (median = 1.53 kcal/mol, RMSE = 2.56 kcal/mol, Direction Acc = 88.3%).
    * **DFT-460**: MAE = **1.78 kcal/mol** (DFT reference: MAE = 1.82 kcal/mol).
    * **sPhysNet-Taut-100**: MAE = **1.82 kcal/mol**.

### 2. Risk Zone ($|\Delta N_{\text{aro}}| > 0$, 20.6% of Dataset, 111 pairs)
Transformations accompanied by the creation or destruction of aromatic rings (e.g., phenol $\leftrightarrow$ 2,4-cyclohexadienone).
* **Results**:
  * **TautoBase-539**: MAE = **5.14 kcal/mol** (median = 4.06 kcal/mol, RMSE = 6.73 kcal/mol).
  * **DFT-460**: MAE = **4.38 kcal/mol** (DFT reference: MAE = 4.07 kcal/mol).
* **Note**: (Update is coming soon)

---

### 📊 3-Tier Confidence Hierarchy

| Tier | Subset / Domain | Criteria | Expected MAE |
| :---: | :--- | :--- | :---: |
| **Tier 1** | **CBH-Taut Subset** | $\|\Delta N_\text{aro}\| = 0$, invariant hybridizations and bond types | **1.29 kcal/mol** |
| **Tier 2** | **Normal Subset** | $\|\Delta N_\text{aro}\| = 0$, aromaticity conserved | **1.97 kcal/mol** |
| **Tier 3** | **Risk Zone** | $\|\Delta N_\text{aro}\| > 0$, aromaticity transition | **5.14 kcal/mol** *(Update is coming soon)* |

---

## 💻 Local Installation & Setup

### 1. Clone & Set Up Python Environment
```bash
git clone https://github.com/KeantChen/TautomerRatio.git
cd TautomerRatio

pip install -r requirements.txt
```

### 2. Verify Installation
Run the self-test script:
```bash
python verify_installation.py
```

---

## 🚀 Command-Line Usage

### 1. 2D Topological Triage
Examine domain applicability and expected uncertainty without running quantum chemistry:
```bash
python predict.py --smi1 "OC1=CC=CC=N1" --smi2 "O=C1NC=CC=C1" --triage_only
```

### 2. Standard Prediction (xTB Tower-A, Standalone)
Predict aqueous free energy difference, equilibrium constant, and dominant tautomer:
```bash
python predict.py --smi1 "OC1=CC=CC=N1" --smi2 "O=C1NC=CC=C1" --mode xtb_only
```

### 3. Multi-Tower Prediction (Towers A, B, and C)
When g-xTB is configured (see [bin/README_ENGINES.md](bin/README_ENGINES.md)):
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

# 2. 2D Triage
triage = predictor.triage_check("OC1=CC=CC=N1", "O=C1NC=CC=C1")
print(f"Domain: {triage['domain']} ({triage['subset']}) | Expected MAE: {triage['expected_mae']} kcal/mol")

# 3. Full Prediction
result = predictor.predict(
    smiles_A="OC1=CC=CC=N1",
    smiles_B="O=C1NC=CC=C1",
    mode="xtb_only",       # or "three_towers"
    temperature=298.15,    # Kelvin
    solvent="water"        # ALPB solvent
)

# Print report
predictor.print_report(result)
```

---

## 📁 Directory Structure

```text
TautomerRatio/
├── notebooks/
│   └── Hydra_PaiNN_Quickstart.ipynb # Google Colab notebook
├── bin/
│   ├── xtb.exe                      # Pre-compiled xTB 6.7.1 (Windows)
│   ├── libiomp5md.dll               # Intel OpenMP runtime
│   └── README_ENGINES.md            # Instructions for Linux & WSL setup
├── models/
│   ├── hydra_painn_best.pth         # Trained PyTorch model weights
│   └── scalers/                     # Feature normalization scalers
├── examples/
│   ├── test_cases.csv               # Curated validation pairs across 3 tiers
│   └── test_predictions.csv         # Reference execution output
├── tautomer_predictor.py            # Prediction engine
├── predict.py                       # Command-line interface
├── verify_installation.py           # Self-test diagnostic script
├── CASE_STUDIES.md                  # Validation cases walkthrough
├── README.md                        # English documentation
├── README_CN.md                     # Chinese documentation
└── README_FR.md                     # French documentation
```

---

## 📄 License
This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
