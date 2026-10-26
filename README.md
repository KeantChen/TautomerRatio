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
