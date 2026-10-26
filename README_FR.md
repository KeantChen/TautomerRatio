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

## Résumé des Performances et Validation Expérimentale

Toutes les métriques sont directement extraites de l'article final et des informations supplémentaires :

### 1. Évaluation Expérimentale Aqueuse (TautoBase & SAMPL2)

#### A. Benchmark TautoBase-539 (Table 3, Table 5 & Table S7)

| Domaine d'Applicabilité | Échantillon (N) | Proportion (%) | Hydra-PaiNN Tour C MAE | Médiane AE | RMSE | Précision Direction (%) | Facteur Boltzmann e^(MAE/RT) | Erreur ≤ 1 kcal/mol (%) |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Zone Dorée CBH-Taut** (|ΔN_aro| = 0, liaisons/hybridation symétriques) | 61 | 11,3% | **1,29 kcal/mol** (Tour A: 1,31) | 1,15 kcal/mol | 1,76 kcal/mol | 83,6% | 8,9 | 47,5% |
| **Sous-ensemble Normal** (|ΔN_aro| = 0, réorganisation de liaisons) | 367 | 68,1% | **1,97 kcal/mol** (Tour A: 1,97) | 1,53 kcal/mol | 2,56 kcal/mol | 88,3% | 28,1 | 31,9% |
| ├─ Réorganisation Générale de Liaisons | 355 | 65,9% | **1,95 kcal/mol** | 1,52 kcal/mol | 2,51 kcal/mol | 87,9% | 26,7 | 32,7% |
| └─ Contrôle Échange de Liaisons (Amide–Imidique) | 12 | 2,2% | **2,67 kcal/mol** | 2,48 kcal/mol | 3,08 kcal/mol | 100,0% | 90,8 | 8,3% |
| **Zone de Confort Combinée** (|ΔN_aro| = 0) | 428 | 79,4% | **1,87 kcal/mol** (Tour A: 1,88) | 1,44 kcal/mol | 2,46 kcal/mol | 87,6% | 24,5 | 34,1% |
| **Zone à Risque** (|ΔN_aro| > 0, transition d'aromaticité) | 111 | 20,6% | **5,14 kcal/mol** (Tour A: 5,12) | 4,06 kcal/mol | 6,73 kcal/mol | 72,1% | 6806,0 | 11,7% |
| **Benchmark TautoBase Complet** | 539 | 100,0% | **2,55 kcal/mol** (Tour A: 2,55) | 1,75 kcal/mol | 3.76 kcal/mol | 84,4% | 73,6 | 29,5% |

#### B. Jeu d'Étalonnage Symétrisé SAMPL2 (Table 2, N = 28)

| Branche du Modèle | Facteur de Courbure (k) | Corrélation R | MAE Brut | MAE Étalonné | RMSE Étalonné | Précision Direction (%) |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Tour A (xTB pur)** | 0,575 | 0,88 | 2,94 kcal/mol | **1,81 kcal/mol** | 2,22 kcal/mol | 78,6% |
| **Tour B (g-xTB pur)** | 0,576 | 0,88 | 2,86 kcal/mol | **1,81 kcal/mol** | 2,20 kcal/mol | 85,7% |
| **Tour C (Fusion Hybride)** | 0,577 | 0,88 | 2,89 kcal/mol | **1,81 kcal/mol** | 2,19 kcal/mol | 78,6% |

---

### 2. Comparaison Directe avec le Protocole DFT de Wieder et al. (Table 4, Table 5 & Table S8)

Sur les 460 paires identiques évaluées par DFT multi-conformationnelle de haut niveau (B3LYP/aug-cc-pVTZ//B3LYP/6-31G(d)/SMD) :

| Sous-ensemble | Échantillon (N) | MAE Ligne Zéro | Wieder Multi-conf DFT (MAE / RMSE / Médiane) | Hydra-PaiNN Tour A (MAE / RMSE / Médiane) | Hydra-PaiNN Tour C (MAE / RMSE / Médiane) |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Benchmark Complet Alignél** | 460 (100,0%) | 4,33 kcal/mol | 2,20 / 3,07 / 1,61 kcal/mol | 2,22 / 3,20 / 1,66 kcal/mol | **2,21 / 3,23 / 1,64 kcal/mol** |
| **Zone de Confort** (|ΔN_aro| = 0) | 378 (82,2%) | 4,62 kcal/mol | 1,79 / 2,39 / 1,38 kcal/mol | 1,75 / 2,22 / 1,54 kcal/mol | **1,73 / 2,24 / 1,42 kcal/mol** |
| ├─ **Zone Dorée CBH-Taut** | 48 (10,4%) | 2,36 kcal/mol | 1,56 / 2,16 / 1,20 kcal/mol | 1,42 / 1,89 / 1,25 kcal/mol | **1,38 / 1,86 / 1,27 kcal/mol** |
| └─ **Sous-ensemble Normal** | 330 (71,7%) | 4,95 kcal/mol | 1,82 / 2,43 / 1,42 kcal/mol | 1,80 / 2,26 / 1,59 kcal/mol | **1,78 / 2,29 / 1,44 kcal/mol** |
| **Zone à Risque** (|ΔN_aro| > 0) | 82 (17,8%) | 3,00 kcal/mol | 4,07 / 5,14 / 3,50 kcal/mol | 4,36 / 5,91 / 3,45 kcal/mol | **4,38 / 5.95 / 3,50 kcal/mol** |

---

### 3. Comparaison avec la Littérature (Table 4)

| Jeu de Données | Échantillon (N) | Méthode / Modèle | MAE (kcal/mol) | RMSE (kcal/mol) |
| :--- | :--- | :--- | :--- | :--- |
| **Sous-ensemble DFT** | 460 | B3LYP/aug-cc-pVTZ//B3LYP/6-31G(d)/SMD | 2,20 | 3,07 |
| | 460 | **Hydra-PaiNN: Tour C** | **2,21** | **3,23** |
| **Sous-ensemble MolTaut** | 460 | MolTaut (*J. Chem. Inf. Model.* 2024) | 2,39 | 3,15 |
| | 460 | ωB97X/6-31G* // M06-2X/6-31G*/SMD | 2,50 | 3,46 |
| | 460 | **Hydra-PaiNN: Tour C** | **2,26** | **2,98** |
| **Sous-ensemble sPhysNet** | 100 | sPhysNet-Pre (zéro-shot) | 4,33 | 6,30 |
| | 100 | sPhysNet-FF (fine-tuné sur données expérimentales) | 1,16 | 1,93 |
| | 100 | MolTaut | 2,61 | 3,64 |
| | 100 | **Hydra-PaiNN: Tour C (transfert zéro-shot pur)** | **2,41** | **3,32** |

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
