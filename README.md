# Hydra-PaiNN: Physics-Informed Multi-Tower Delta-Learning and 4-Tier CBH-2 Triage for Aqueous Tautomer Ratios

> **Languages / 语言版本 / Langues** : [English](README.md) | [中文 (Chinese)](README_CN.md) | [Français (French)](README_FR.md)

Hydra-PaiNN is an open-source, physics-informed machine learning pipeline for predicting tautomeric free energy differences ($\Delta G_{\text{aq}}$), equilibrium constants ($K_{\text{eq}}$), and Boltzmann population distributions in aqueous solution.

The framework integrates:
1. **PaiNN Equivariant Neural Message Passing**: Captures directional, continuous 3D geometric interactions.
2. **Semi-Empirical Quantum Chemistry**: Couples GFN2-xTB (ALPB implicit water) and g-xTB electronic descriptors.
3. **4-Tier Quantum-Topological CBH-2 Triage**: A 2D SMILES graph diagnostic that identifies whether error cancellation holds (Raghavachari homodesmotic rules) prior to quantum calculations, routing high-risk aromatic breakdown cases to high-level DFT.

---

## Key Features

- **Out-of-the-Box Inference**: Includes pre-trained weights (`hydra_painn_best.pth`), scalers, and pre-compiled Windows xTB binaries.
- **Dual Operating Modes**:
  - `--mode xtb_only` (Default): Runs solely on GFN2-xTB (ALPB water). Fully standalone on Windows and Linux with zero external dependencies.
  - `--mode three_towers`: Runs all three readout branches (Tower A: xTB, Tower B: g-xTB, Tower C: Mixed Fusion) when g-xTB is available.
- **Instantaneous 2D Triage** (`--triage_only`): Classifies tautomer pairs into 4 confidence tiers in under 1 ms:
  - **Tier 1 (Strict CBH-2 Golden Zone)**: $\Delta N_{\text{aro}} = 0$ with identical bond-pair types and atom hybridizations (Benchmark MAE ~ 1.30 kcal/mol, median 0.99 kcal/mol).
  - **Tier 2 (Standard Aromatic Scaffold Comfort Zone)**: $\Delta N_{\text{aro}} = 0$ on aromatic scaffold(s) (Benchmark MAE ~ 1.81 kcal/mol).
  - **Tier 3 (Flexible Aliphatic Comfort Zone)**: $\Delta N_{\text{aro}} = 0$ without aromatic rings (Benchmark MAE ~ 2.64 kcal/mol).
  - **Tier 4 (High-Risk Breakdown Zone)**: $\Delta N_{\text{aro}} > 0$. Asymmetric resonance disruption breaks continuum solvation cancellation (Benchmark MAE ~ 5.25 kcal/mol; routed to DFT).

---

## Installation

### 1. Clone & Set Up Python Environment
```bash
git clone https://github.com/your-username/Hydra-PaiNN.git
cd Hydra-PaiNN

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

### 1. Aqueous Experimental Benchmarks
| Benchmark Dataset | Subset / Domain | Sample Size ($N$) | Hydra-PaiNN Tower A | Hydra-PaiNN Tower C | Literature Baseline |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **TautoBase Benchmark** | Comfort Zone ($\Delta N_{\text{aro}}=0$) | 428 | MAE = 1.94 kcal/mol | MAE = 1.95 kcal/mol | GFN2+k: 2.78 kcal/mol |
| *(Experimental $\Delta G_{\text{exp}}$)* | CBH-2 Golden Zone | 61 | MAE = 1.35 kcal/mol | MAE = 1.30 kcal/mol | Median = 0.99 kcal/mol |
| | Risk Zone ($\Delta N_{\text{aro}}>0$) | 111 | MAE = 5.04 kcal/mol | MAE = 5.02 kcal/mol | Physics Breakdown |
| **Wieder et al. Dataset** | Full Overlap | 460 | MAE = 1.85 kcal/mol | MAE = 1.85 kcal/mol | Multi-conf DFT: 1.99 kcal/mol |
| *(Experimental $\Delta G_{\text{exp}}$)* | CBH-Taut Subset | 48 | MAE = 1.16 kcal/mol | MAE = 1.13 kcal/mol | Multi-conf DFT: 1.40 kcal/mol |
| | Risk Zone Subset | 82 | MAE = 3.07 kcal/mol | MAE = 3.15 kcal/mol | Multi-conf DFT: 3.53 kcal/mol |
| **SAMPL2 Calibration Set** | Neutral Aqueous | 28 records | MAE = 0.65 kcal/mol | MAE = 0.65 kcal/mol | Raw GFN2: 1.34 kcal/mol |

*All experimental free energy predictions incorporate linear potential energy surface curvature scaling factors ($k_A = 0.568$, $k_C = 0.571$) fitted on SAMPL2.*

### 2. Note on Theoretical Training Dataset (Frag20-Taut Holdout)
The model was pre-trained on theoretical tautomer pairs from Frag20-Taut (Ref 19). These are **not experimental free energies**, but microscopic aqueous electronic energies calculated at the B3LYP/6-31G*/SMD level of theory. On the holdout test set of 2,026 rare/orphan scaffold graphs, Hydra-PaiNN achieves a residual electronic energy prediction MAE of 0.32 kcal/mol (Tower A) and 0.31 kcal/mol (Tower C) relative to the B3LYP/6-31G*/SMD reference, verifying that the neural message passing architecture effectively learned the target quantum residual mapping.

---

## Directory Structure

```
Hydra-PaiNN_Release/
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
