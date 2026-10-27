# Tautomer Prediction Case Studies
## 3-Tier Applicability Domain Triage & Multi-Tower Prediction

This document provides examples across the three applicability domain subsets:
- **Comfort Zone ($|\Delta N_\text{aro}| = 0$)**:
  - **Tier 1 (CBH-Taut Subset)**: Invariant heavy-atom hybridizations and bond-pair types (Expected MAE: 1.29 kcal/mol).
  - **Tier 2 (Normal Subset)**: Conserved aromaticity with localized bond rearrangements (Expected MAE: 1.97 kcal/mol).
- **Risk Zone ($|\Delta N_\text{aro}| > 0$)**:
  - **Tier 3 (Risk Zone)**: Aromaticity transitions (Expected MAE: 5.14 kcal/mol). *(Update is coming soon)*

---

## Case 1: Acetylcyclopentanone Enol-Enol — Tier 1 (CBH-Taut Subset)

* **Input Molecules**:
  * Tautomer A: `CC(=O)C1=C(O)CCC1`
  * Tautomer B: `C/C(O)=C1\CCCC1=O`
* **Criteria**: $\Delta N_\text{aro} = 0$, and heavy-atom hybridizations and bond-pair types ($C=O, C-O, C=C, C-C$) are identically conserved across tautomers.
* **Experimental Reference (TautoBase Row 37)**: $\log_{10} K = 0.60$, $\Delta G_\text{exp} = -0.82\text{ kcal/mol}$ (Tautomer B dominant).
* **Command**:
  ```bash
  python predict.py --smi1 "CC(=O)C1=C(O)CCC1" --smi2 "C/C(O)=C1\CCCC1=O"
  ```
* **Prediction (Tower A)**: $\Delta G_\text{pred} = -0.62\text{ kcal/mol}$, $\log_{10} K = +0.45$, Predominant: **B (74.0%)**, Absolute Error = $0.20\text{ kcal/mol}$.

---

## Case 2: 2-Hydroxypyridine / 2-Pyridone — Tier 2 (Normal Subset)

* **Input Molecules**:
  * Tautomer A (2-Hydroxypyridine): `OC1=CC=CC=N1`
  * Tautomer B (2-Pyridone): `O=C1NC=CC=C1`
* **Criteria**: Conserved aromatic atom count ($|\Delta N_\text{aro}| = 0$) with lactam-lactim bond rearrangement.
* **Experimental Reference (SAMPL2)**: $\Delta G_\text{exp} = -2.60\text{ kcal/mol}$ (Tautomer B dominant).
* **Command**:
  ```bash
  python predict.py --smi1 "OC1=CC=CC=N1" --smi2 "O=C1NC=CC=C1"
  ```
* **Prediction (Tower A)**: $\Delta G_\text{pred} = -2.45\text{ kcal/mol}$, $\log_{10} K = +1.80$, Predominant: **B (98.4%)**, Absolute Error = $0.15\text{ kcal/mol}$.

---

## Case 3: Phenol / 2,4-Cyclohexadienone — Tier 3 (Risk Zone)

* **Input Molecules**:
  * Tautomer A (Phenol): `Oc1ccccc1` ($N_\text{aro} = 6$)
  * Tautomer B (2,4-Cyclohexadienone): `O=C1C=CC=CC1` ($N_\text{aro} = 0$)
* **Criteria**: Aromaticity transition ($|\Delta N_\text{aro}| = 6 > 0$).
* **Experimental Reference**: $\Delta G_\text{exp} = +14.00\text{ kcal/mol}$ (Tautomer A dominant).
* **Command**:
  ```bash
  python predict.py --smi1 "Oc1ccccc1" --smi2 "O=C1C=CC=CC1"
  ```
* **Prediction (Tower A)**: $\Delta G_\text{pred} = +7.71\text{ kcal/mol}$, Predominant: **A (100.0%)**, Absolute Error = $6.29\text{ kcal/mol}$. *(Update is coming soon)*

---

## Summary Table

| Tier | Subset / Domain | Example Pair | $\Delta G_\text{pred}$ | $\Delta G_\text{exp}$ | Expected Subset MAE |
| :---: | :--- | :--- | :---: | :---: | :---: |
| **Tier 1** | **CBH-Taut Subset** | `CC(=O)C1=C(O)CCC1` $\to$ `C/C(O)=C1\CCCC1=O` | $-0.62\text{ kcal/mol}$ | $-0.82\text{ kcal/mol}$ | **1.29 kcal/mol** |
| **Tier 2** | **Normal Subset** | `OC1=CC=CC=N1` $\to$ `O=C1NC=CC=C1` | $-2.45\text{ kcal/mol}$ | $-2.60\text{ kcal/mol}$ | **1.97 kcal/mol** |
| **Tier 3** | **Risk Zone** | `Oc1ccccc1` $\to$ `O=C1C=CC=CC1` | $+7.71\text{ kcal/mol}$ | $+14.00\text{ kcal/mol}$ | **5.14 kcal/mol** *(Update is coming soon)* |
