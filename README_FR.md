# Hydra-PaiNN : Apprentissage Delta Multi-Tours Guidé par la Physique et Triage CBH-2 pour les Ratios Tautomériques en Solution Aqueuse

> **Languages / 语言版本 / Langues** : [Français (French)](README_FR.md) | [English](README.md) | [中文 (Chinese)](README_CN.md)

Hydra-PaiNN est une suite logicielle open source d'apprentissage automatique guidé par la physique conçue pour prédire les différences d'énergie libre de tautomérisation en solution aqueuse (**ΔG_aq**), les constantes d'équilibre (**K_eq**) et les populations de Boltzmann des équilibres tautomériques.

$$
\Delta G_{\text{aq}} = -RT \ln K_{\text{eq}}, \quad K_{\text{eq}} = \frac{[\text{Tautomère B}]}{[\text{Tautomère A}]}
$$

L'architecture intègre :
1. **Passage de Messages Neuronaux Équivariants PaiNN** : Modélise les interactions géométriques 3D directionnelles et continues.
2. **Chimie Quantique Semi-Empirique** : Combine les descripteurs électroniques de GFN2-xTB (eau implicite ALPB) et de g-xTB.
3. **Filtrage Quantum-Topologique CBH-Taut** : Diagnostic 2D sur graphe moléculaire permettant de vérifier la validité de la compensation des erreurs quantiques systématiques (règles homodesmotiques de Raghavachari) avant tout calcul lourd, en orientant les cas à rupture diélectrique ou perte d'aromaticité vers la DFT de haut niveau.

---

## Caractéristiques Principales

- **Inférence Immédiate et Clé en Main** : Fourni avec les poids pré-entraînés (`hydra_painn_best.pth`), les scalers et les binaires xTB pré-compilés.
- **Deux Modes d'Exécution** :
  - `--mode xtb_only` (Par défaut) : Repose uniquement sur GFN2-xTB (ALPB). Autonome sous Windows et Linux sans dépendance externe complexe.
  - `--mode three_towers` : Active simultanément les trois tours (Tour A : xTB, Tour B : g-xTB, Tour C : Fusion Hybride).
- **Filtrage Topologique 2D Instantané** (`--triage_only`, < 1 ms) :
  - **Niveau 1 (Zone Dorée CBH-Taut Stricte)** : |ΔN_aro| = 0, types de liaisons et hybridations 100% conservés (TautoBase MAE = 1,29 kcal/mol, médiane 1,15 kcal/mol ; Wieder DFT MAE = 1,38 kcal/mol).
  - **Niveau 2 (Squelette Aromatique Standard / Zone de Confort)** : |ΔN_aro| = 0 sur squelette aromatique (TautoBase Sous-ensemble Normal MAE = 1,97 kcal/mol, médiane 1,53 kcal/mol, précision de signe 88,3%).
  - **Niveau 3 (Aliphatique Flexible / Zone de Confort)** : |ΔN_aro| = 0 sans cycle aromatique (Zone de Confort Combinée MAE = 1,87 kcal/mol, médiane 1,44 kcal/mol).
  - **Niveau 4 (Zone à Risque / Rupture d'Aromaticité)** : |ΔN_aro| > 0. La perte de résonance rompt l'hypothèse de solvatation continue (TautoBase MAE = 5,14 kcal/mol, médiane 4,06 kcal/mol ; Wieder MAE = 4,38 kcal/mol vs. DFT 4,07 kcal/mol ; orientation recommandée vers DFT).

---

## Installation

### 1. Cloner et Configurer l'Environnement Python
```bash
git clone https://github.com/KeantChen/TautomerRatio.git
cd TautomerRatio

# Créer l'environnement conda
conda env create -f environment.yml
conda activate hydra_painn
```

Ou via `pip` :
```bash
pip install -r requirements.txt
```

### 2. Vérification de l'Installation
Exécutez le script d'auto-test pour contrôler les dépendances, les poids et les moteurs quantiques :
```bash
python verify_installation.py
```

---

## Démarrage Rapide

### 1. Filtrage Topologique 2D Rapide (< 1 ms)
Évaluez le domaine d'applicabilité et l'incertitude sans lancer de calcul quantique :
```bash
python predict.py --smi1 "OC1=CC=CC=N1" --smi2 "O=C1NC=CC=C1" --triage_only
```

### 2. Prédiction Standard (Tour A xTB, Autonome)
Prédit la différence d'énergie libre aqueuse, la constante d'équilibre et le tautomère majoritaire :
```bash
python predict.py --smi1 "OC1=CC=CC=N1" --smi2 "O=C1NC=CC=C1" --mode xtb_only
```

### 3. Mode Trois Tours (Recommandé avec WSL/Linux)
```bash
python predict.py --smi1 "OC1=CC=CC=N1" --smi2 "O=C1NC=CC=C1" --mode three_towers
```

### 4. Évaluation par Lot (Fichier CSV)
```bash
python predict.py --input examples/test_cases.csv --output my_predictions.csv --mode xtb_only
```

---

## Structure du Répertoire

```text
TautomerRatio/
├── bin/
│   ├── xtb.exe                     # Binaire xTB Windows (GFN2-xTB)
│   ├── libiomp5md.dll              # Bibliothèque OpenMP Intel
│   └── README_ENGINES.md           # Instructions pour Linux & WSL
├── models/
│   ├── hydra_painn_best.pth        # Poids PyTorch entraînés (Seed 42)
│   └── scalers/                    # Normaliseurs statistiques
├── examples/
│   ├── test_cases.csv              # Cas de validation représentatifs
│   └── test_predictions.csv        # Résultats d'exécution types
├── tautomer_predictor.py           # Moteur d'inférence modulaire
├── predict.py                      # Interface en ligne de commande (CLI)
├── verify_installation.py          # Script d'auto-test
├── environment.yml                 # Environnement Conda
├── requirements.txt                # Dépendances Pip
├── LICENSE                         # Licence MIT
└── README.md                       # Documentation
```

---

## Licence

Ce projet est distribué sous la [Licence MIT](LICENSE).
Les moteurs quantiques (xTB, g-xTB) sont soumis à leurs licences respectives (LGPL-3.0 / GPL).
