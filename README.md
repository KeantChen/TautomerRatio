# Hydra-PaiNN: Physics-Informed Multi-Tower Delta-Learning and 4-Tier CBH-2 Triage for Aqueous Tautomer Ratios

> **Languages / 语言版本 / Langues** : [English](README.md) | [中文 (Chinese)](README_CN.md) | [Français (French)](README_FR.md)

Hydra-PaiNN is an open-source, physics-informed machine learning pipeline for predicting tautomeric aqueous free energy differences (**ΔG_aq**), equilibrium constants (**K_eq**), and Boltzmann population distributions in aqueous solution.

$$
\Delta G_{\text{aq}} = -RT \ln K_{\text{eq}}, \quad K_{\text{eq}} = \frac{[\text{Tautomer B}]}{[\text{Tautomer A}]}
$$

The framework integrates:
1. **PaiNN Equivariant Neural Message Passing**: Captures directional, continuous 3D geometric interactions.
2. **Semi-Empirical Quantum Chemistry**: Couples GFN2-xTB (ALPB implicit water) and g-xTB electronic descriptors.
3. **Connectivity-Based Hierarchy (CBH-Taut) Triage**: A 2D SMILES graph diagnostic based on Raghavachari homodesmotic rules that identifies whether systematic baseline errors cancel prior to quantum calculations, routing high-risk aromatic breakdown cases to high-level DFT.

---

## Key Features

- **Out-of-the-Box Inference**: Includes pre-trained weights (`hydra_painn_best.pth`), scalers, and pre-compiled Windows xTB binaries.
- **Dual Operating Modes**:
  - `--mode xtb_only` (Default): Runs solely on GFN2-xTB (ALPB water). Fully standalone on Windows and Linux with zero external dependencies.
  - `--mode three_towers`: Runs all three readout branches (Tower A: xTB, Tower B: g-xTB, Tower C: Mixed Fusion) when g-xTB is available.
- **Instantaneous 2D Triage** (`--triage_only`): Classifies tautomer pairs into confidence tiers in under 1 ms:
  - **Tier 1 (Strict CBH-Taut Golden Zone)**: |ΔN_aro| = 0 with identical bond-pair types and atom hybridizations (TautoBase MAE = 1.29 kcal/mol, median = 1.15 kcal/mol; Wieder DFT MAE = 1.38 kcal/mol).
  - **Tier 2 (Standard Aromatic Scaffold Comfort Zone)**: |ΔN_aro| = 0 with aromatic ring(s) (TautoBase Normal MAE = 1.97 kcal/mol, median = 1.53 kcal/mol, Direction Acc = 88.3%).
  - **Tier 3 (Flexible Aliphatic Comfort Zone)**: |ΔN_aro| = 0 acyclic / 0 aromatic rings (Comfort Zone Combined MAE = 1.87 kcal/mol, median = 1.44 kcal/mol).
  - **Tier 4 (High-Risk Breakdown Zone / Tier 3 in Manuscript)**: |ΔN_aro| > 0. Aromaticity transitions break continuum solvation error cancellation (TautoBase MAE = 5.14 kcal/mol, median = 4.06 kcal/mol; Wieder MAE = 4.38 kcal/mol vs. DFT 4.07 kcal/mol; routed to DFT).

---

## Installation

### 1. Clone & Set Up Python Environment
```bash
git clone https://github.com/KeantChen/TautomerRatio.git
cd TautomerRatio

# Create conda environment
conda env create -f environment.yml
conda activate hydra_painn
```

Alternatively, install dependencies via `pip`:
```bash
pip install -r requirements.txt
```

### 2. Verify Installation
Run the automated self-test script to verify dependencies, model weights, and quantum engines:
```bash
python verify_installation.py
```

---

## Quick Start

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

## Python API Usage

```python
from tautomer_predictor import TautomerPredictor

# 1. Initialize predictor (loads weights and scalers)
predictor = TautomerPredictor()

# 2. Fast 2D Triage
triage = predictor.triage_check("OC1=CC=CC=N1", "O=C1NC=CC=C1")
print(f"Tier: {triage['tier_name']} | Expected MAE: {triage['expected_mae']} kcal/mol")

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

## Benchmark Performance Summary

All benchmark results are directly extracted from the final manuscript and supplementary information:

### 1. Authentic Experimental Benchmarks (TautoBase & SAMPL2)

#### A. TautoBase-539 Benchmark Across Applicability Domains (Manuscript Table 3, Table 5 & SI Table S7)

| Applicability Domain Subset | Sample Size (N) | Share (%) | Hydra-PaiNN Tower C MAE | Median AE | RMSE | Direction Acc (%) | Boltzmann Factor e^(MAE/RT) | Within 1 kcal/mol (%) |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **CBH-Taut Golden Subset** (|ΔN_aro| = 0, conserved bonds & hyb) | 61 | 11.3% | **1.29 kcal/mol** (Tower A: 1.31) | 1.15 kcal/mol | 1.76 kcal/mol | 83.6% | 8.9 | 47.5% |
| **Normal Subset** (|ΔN_aro| = 0, bond-reorganized) | 367 | 68.1% | **1.97 kcal/mol** (Tower A: 1.97) | 1.53 kcal/mol | 2.56 kcal/mol | 88.3% | 28.1 | 31.9% |
| ├─ General Bond-Reorganized | 355 | 65.9% | **1.95 kcal/mol** | 1.52 kcal/mol | 2.51 kcal/mol | 87.9% | 26.7 | 32.7% |
| └─ Swapped-Bond Control (Amide–Imidic) | 12 | 2.2% | **2.67 kcal/mol** | 2.48 kcal/mol | 3.08 kcal/mol | 100.0% | 90.8 | 8.3% |
| **Comfort Zone Combined** (|ΔN_aro| = 0) | 428 | 79.4% | **1.87 kcal/mol** (Tower A: 1.88) | 1.44 kcal/mol | 2.46 kcal/mol | 87.6% | 24.5 | 34.1% |
| **Risk Zone** (|ΔN_aro| > 0, aromaticity transition) | 111 | 20.6% | **5.14 kcal/mol** (Tower A: 5.12) | 4.06 kcal/mol | 6.73 kcal/mol | 72.1% | 6806.0 | 11.7% |
| **Full TautoBase Benchmark** | 539 | 100.0% | **2.55 kcal/mol** (Tower A: 2.55) | 1.75 kcal/mol | 3.76 kcal/mol | 84.4% | 73.6 | 29.5% |

*Overall Baseline Comparison on Full TautoBase-539 (Manuscript Table 3)*:
- **Raw GFN2-xTB**: Raw MAE = 3.67 kcal/mol, Calibrated MAE = 3.69 kcal/mol, Direction Acc = 66.5%
- **Raw g-xTB**: Raw MAE = 2.93 kcal/mol, Calibrated MAE = 2.78 kcal/mol, Direction Acc = 82.5%
- **Hydra-PaiNN Tower A**: Calibrated MAE = **2.55 kcal/mol** (Raw MAE = 4.28 kcal/mol), Direction Acc = **84.6%**
- **Hydra-PaiNN Tower B**: Calibrated MAE = **2.55 kcal/mol** (Raw MAE = 4.34 kcal/mol), Direction Acc = **84.8%**
- **Hydra-PaiNN Tower C**: Calibrated MAE = **2.55 kcal/mol** (Raw MAE = 4.35 kcal/mol), Direction Acc = **84.4%**

#### B. Symmetrized SAMPL2 Calibration Set (Manuscript Table 2, N = 28)

| Model Branch | Curvature Factor (k) | Pearson R | Raw MAE | Calibrated MAE | Calibrated RMSE | Direction Acc (%) |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Tower A (xTB-only)** | 0.575 | 0.88 | 2.94 kcal/mol | **1.81 kcal/mol** | 2.22 kcal/mol | 78.6% |
| **Tower B (g-xTB-only)** | 0.576 | 0.88 | 2.86 kcal/mol | **1.81 kcal/mol** | 2.20 kcal/mol | 85.7% |
| **Tower C (Mixed Fusion)** | 0.577 | 0.88 | 2.89 kcal/mol | **1.81 kcal/mol** | 2.19 kcal/mol | 78.6% |

*For the 12 aromaticity-conserving pairs in SAMPL2, Hydra-PaiNN achieves a mean absolute deviation of only **0.49 kcal/mol** (reaching the strict < 1.0 kcal/mol chemical accuracy target).*

---

### 2. Direct Pairwise Benchmark Against Wieder et al. DFT Protocol (Manuscript Table 4, Table 5 & SI Table S8)

On the identical 460 aligned tautomer pairs evaluated with high-level multiconformational DFT (B3LYP/aug-cc-pVTZ//B3LYP/6-31G(d)/SMD) by Wieder et al. (*Chem. Sci.* 2021):

| Subset Definition | Sample Size (N) | Null Baseline MAE | Wieder Multi-conf DFT (MAE / RMSE / Median) | Hydra-PaiNN Tower A (MAE / RMSE / Median) | Hydra-PaiNN Tower C (MAE / RMSE / Median) |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Full Aligned Benchmark** | 460 (100.0%) | 4.33 kcal/mol | 2.20 / 3.07 / 1.61 kcal/mol | 2.22 / 3.20 / 1.66 kcal/mol | **2.21 / 3.23 / 1.64 kcal/mol** |
| **Comfort Zone Combined** (|ΔN_aro| = 0) | 378 (82.2%) | 4.62 kcal/mol | 1.79 / 2.39 / 1.38 kcal/mol | 1.75 / 2.22 / 1.54 kcal/mol | **1.73 / 2.24 / 1.42 kcal/mol** |
| ├─ **CBH-Taut Golden Subset** | 48 (10.4%) | 2.36 kcal/mol | 1.56 / 2.16 / 1.20 kcal/mol | 1.42 / 1.89 / 1.25 kcal/mol | **1.38 / 1.86 / 1.27 kcal/mol** |
| └─ **Normal Subset** | 330 (71.7%) | 4.95 kcal/mol | 1.82 / 2.43 / 1.42 kcal/mol | 1.80 / 2.26 / 1.59 kcal/mol | **1.78 / 2.29 / 1.44 kcal/mol** |
| **Risk Zone** (|ΔN_aro| > 0) | 82 (17.8%) | 3.00 kcal/mol | 4.07 / 5.14 / 3.50 kcal/mol | 4.36 / 5.91 / 3.45 kcal/mol | **4.38 / 5.95 / 3.50 kcal/mol** |

> **Key Theoretical Takeaway**: Notice that even multiconformational high-level DFT exhibits an error of 4.07 kcal/mol on the Risk Zone while converging to 1.56 kcal/mol on the CBH-Taut subset. This demonstrates that electronic reorganization accompanying aromaticity transitions represents a **universal physical bottleneck across quantum chemical methods**, which Hydra-PaiNN efficiently diagnoses and intercepts via upfront 2D CBH-Taut triage in < 1 ms.

---

### 3. External Literature Benchmark Comparisons (Manuscript Table 4)

| Literature Benchmark Subset | Sample Size (N) | Method / Model | MAE (kcal/mol) | RMSE (kcal/mol) |
| :--- | :--- | :--- | :--- | :--- |
| **DFT Subset** | 460 | B3LYP/aug-cc-pVTZ//B3LYP/6-31G(d)/SMD | 2.20 | 3.07 |
| | 460 | **Hydra-PaiNN: Tower C** | **2.21** | **3.23** |
| **MolTaut Subset** | 460 | MolTaut (*J. Chem. Inf. Model.* 2024) | 2.39 | 3.15 |
| | 460 | ωB97X/6-31G* // M06-2X/6-31G*/SMD | 2.50 | 3.46 |
| | 460 | **Hydra-PaiNN: Tower C** | **2.26** | **2.98** |
| **sPhysNet Subset** | 100 | sPhysNet-Pre (before fine-tuning) | 4.33 | 6.30 |
| | 100 | sPhysNet-FF (fine-tuned on experimental ΔG) | 1.16 | 1.93 |
| | 100 | MolTaut | 2.61 | 3.64 |
| | 100 | **Hydra-PaiNN: Tower C (zero-shot transfer)** | **2.41** | **3.32** |

---

### 4. Microscopic Electronic Energy Residual Learning (Frag20-Taut Holdout, Manuscript Table 1 & SI Table S5)

The neural network backbone was pre-trained on single-molecule electronic energy residuals from Frag20-Taut calculated at the **B3LYP/6-31G*/SMD** level of theory:

| Model Branch | Input Features | Holdout MAE (kcal/mol) | Holdout RMSE (kcal/mol) | Holdout R² |
| :--- | :--- | :--- | :--- | :--- |
| **Tower-A** | xTB | **1.33 ± 0.02** | 2.09 ± 0.04 | 0.97 ± 0.001 |
| **Tower-B** | g-xTB | **1.28 ± 0.01** | 1.99 ± 0.07 | 0.97 ± 0.002 |
| **Tower-C** | Mixed Fusion | **1.28 ± 0.01** | 1.95 ± 0.05 | 0.97 ± 0.002 |

*Evaluated on N = 2,026 orphan scaffold graphs strictly isolated by tautomer group-locking.*

---

## Directory Structure

```text
TautomerRatio/
├── bin/
│   ├── xtb.exe                     # Pre-compiled xTB 6.7.1 (Windows)
│   ├── libiomp5md.dll              # Intel OpenMP runtime
│   └── README_ENGINES.md           # Instructions for Linux & WSL setup
├── models/
│   ├── hydra_painn_best.pth        # Trained PyTorch model weights (Seed 42)
│   └── scalers/                    # Pre-fitted feature normalization scalers
├── examples/
│   ├── test_cases.csv              # Curated validation pairs across 4 tiers
│   └── test_predictions.csv        # Reference execution output
├── tautomer_predictor.py           # Core Python prediction engine
├── predict.py                      # Command-line interface (CLI)
├── verify_installation.py          # Automated self-test script
├── environment.yml                 # Conda environment definition
├── requirements.txt                # Pip requirements file
├── LICENSE                         # MIT License
└── README.md                       # Documentation
```

---

## License

This project is released under the [MIT License](LICENSE).
Quantum engines (xTB, g-xTB) are subject to their respective open-source licenses (LGPL-3.0 / GPL).
