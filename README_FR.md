# Hydra-PaiNN : Apprentissage Delta Multi-Tours Guidé par la Physique et Filtrage CBH-2 à 4 Niveaux pour les Ratios Tautomériques en Solution Aqueuse

Hydra-PaiNN est une suite logicielle open source d'apprentissage automatique guidé par la physique conçue pour prédire les différences d'énergie libre de tautomérisation en solution aqueuse ($\Delta G_{\text{aq}}$), les constantes d'équilibre ($K_{\text{eq}}$) et les populations de Boltzmann des équilibres tautomériques.

L'architecture intègre :
1. **Passage de Messages Neuronaux Équivariants PaiNN** : Modélise les interactions géométriques 3D directionnelles et continues.
2. **Chimie Quantique Semi-Empirique** : Combine les descripteurs électroniques de GFN2-xTB (eau implicite ALPB) et de g-xTB.
3. **Filtrage Quantum-Topologique CBH-2 à 4 Niveaux** : Diagnostic 2D sur graphe moléculaire permettant de vérifier la validité de la compensation des erreurs quantiques (règles homodesmotiques de Raghavachari) avant tout calcul lourd, en orientant les cas à rupture diélectrique vers la DFT de haut niveau.

---

## Caractéristiques Principales

- **Inférence Immédiate et Clé en Main** : Fourni avec les poids pré-entraînés (`hydra_painn_best.pth`), les scalers et les binaires xTB pré-compilés.
- **Deux Modes d'Exécution** :
  - `--mode xtb_only` (Par défaut) : Repose uniquement sur GFN2-xTB (ALPB). Autonome sous Windows et Linux sans dépendance externe complexe.
  - `--mode three_towers` : Active simultanément les trois tours (Tour A : xTB, Tour B : g-xTB, Tour C : Fusion Hybride).
- **Filtrage Topologique 2D Instantané** (`--triage_only`) : Catégorise les paires en 4 niveaux de confiance en moins d'une milliseconde :
  - **Niveau 1 (Zone Dorée CBH-2 Stricte)** : $\Delta N_{\text{aro}} = 0$, types de liaisons et hybridations identiques (MAE benchmark ~ 1,30 kcal/mol, médiane 0,99 kcal/mol).
  - **Niveau 2 (Squelette Aromatique Standard / Zone de Confort)** : $\Delta N_{\text{aro}} = 0$ sur squelette aromatique (MAE benchmark ~ 1,81 kcal/mol).
  - **Niveau 3 (Aliphatique Flexible / Zone de Confort)** : $\Delta N_{\text{aro}} = 0$ sans cycle aromatique (MAE benchmark ~ 2,64 kcal/mol).
  - **Niveau 4 (Zone à Risque / Rupture Diélectrique)** : $\Delta N_{\text{aro}} > 0$. La perte de résonance rompt l'hypothèse de solvatation continue (MAE benchmark ~ 5,25 kcal/mol ; orientation recommandée vers DFT).

---

## Installation

### 1. Cloner et Configurer l'Environnement Python
```bash
git clone https://github.com/your-username/Hydra-PaiNN.git
cd Hydra-PaiNN

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
Hydra-PaiNN_Release/
├── README.md                      # Guide en anglais
├── README_CN.md                   # Guide en chinois
├── README_FR.md                   # [Ce fichier] Guide en français
├── CASE_STUDIES.md                # Analyse détaillée de cas (anglais)
├── CASE_STUDIES_CN.md             # Analyse détaillée de cas (chinois)
├── tautomer_predictor.py          # API Python d'inférence modulaire
├── predict.py                     # Outil en ligne de commande (CLI)
├── verify_installation.py         # Script d'auto-vérification de l'installation
├── environment.yml                # Spécification de l'environnement Conda
├── requirements.txt               # Spécification des dépendances pip
├── LICENSE                        # Licence MIT Open-Source
├── bin/                           # Moteurs quantiques et bibliothèques
│   ├── xtb.exe                    # Binaire xTB Windows (GFN2-xTB)
│   ├── libiomp5md.dll             # Bibliothèque OpenMP Intel
│   ├── gxtb                       # Binaire Linux ELF g-xTB (via WSL sous Windows)
│   ├── basisq / gxtb_para         # Paramètres et bases quantiques
│   └── README_ENGINES.md          # Guide d'exécution multi-plateformes
├── models/                        # Modèle entraîné et scalers
│   ├── hydra_painn_best.pth       # Poids optimisés de Hydra-PaiNN
│   ├── scaler_node.pt             # Scaler des caractéristiques atomiques
│   ├── scaler_global_xtb.pt       # Scaler des descripteurs xTB
│   └── scaler_global_gxtb.pt      # Scaler des descripteurs g-xTB
└── examples/                      # Cas tests et exemples
    ├── test_cases.csv             # 8 paires représentatives des 4 niveaux
    └── test_predictions.csv       # Prédictions de référence
```

---

## Formulations Physiques et Équations

### Énergie Libre Aqueuse et Étalonnage de Courbure ($k$)
* **Tour A (xTB Pur)** :
  $$G^{(A)} = E_{\text{eau, xTB}} + G_{\text{corr}} + \Delta E_{\text{ML}}^{(A)}$$
  $$\Delta G_{\text{calib}}^{(A)} = k_A \cdot \left( G_B^{(A)} - G_A^{(A)} \right) \quad (k_A = 0,56825)$$

* **Tour C (Fusion Hybride)** :
  $$G^{(C)} = E_{\text{gaz, g-xTB}} + \Delta G_{\text{solv, xTB}}^{\text{ALPB}} + G_{\text{corr}} + \Delta E_{\text{ML}}^{(C)}$$
  $$\Delta G_{\text{calib}}^{(C)} = k_C \cdot \left( G_B^{(C)} - G_A^{(C)} \right) \quad (k_C = 0,57101)$$

### Ratios de Population de Boltzmann
$$K_{\text{eq}} = \exp\left( -\frac{\Delta G_{\text{calib}}}{RT} \right)$$
$$\text{Population}(A) = \frac{1}{1 + K_{\text{eq}}} \times 100\%, \quad \text{Population}(B) = \frac{K_{\text{eq}}}{1 + K_{\text{eq}}} \times 100\%$$

---

## Citation

Si vous utilisez Hydra-PaiNN dans vos recherches, veuillez citer notre article :
```bibtex
@article{HydraPaiNN2026,
  title={Tautomer Ratio Project: Aqueous Tautomeric Equilibria},
  author={Research Team},
  journal={Journal of Chemical Information and Modeling / Chemical Science},
  year={2026}
}
```
