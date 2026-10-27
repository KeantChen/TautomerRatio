# Hydra-PaiNN : Apprentissage Delta Multi-Tours Informé par la Physique et Triage du Domaine d'Applicabilité pour les Rapports Tautomères en Phase Aqueuse

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/KeantChen/TautomerRatio/blob/main/notebooks/Hydra_PaiNN_Quickstart.ipynb)
[![GitHub](https://img.shields.io/badge/GitHub-Repository-blue.svg?logo=github)](https://github.com/KeantChen/TautomerRatio)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

> **Langues / Languages / 语言版本** : [English](README.md) | [中文 (Chinese)](README_CN.md) | [Français (French)](README_FR.md)

Hydra-PaiNN est un pipeline d'apprentissage automatique open-source conçu pour prédire les différences d'énergie libre tautomère en phase aqueuse (**ΔG_aq**), les constantes d'équilibre (**K_eq**) et les distributions de populations de Boltzmann en solution aqueuse.

$$
\Delta G_{\text{aq}} = -RT \ln K_{\text{eq}}, \quad K_{\text{eq}} = \frac{[\text{Tautomère B}]}{[\text{Tautomère A}]}
$$

L'architecture intègre :
1. **Passage de messages neuronaux équivariants PaiNN** : Capture les interactions géométriques 3D directionnelles.
2. **Chimie quantique semi-empirique** : Associe GFN2-xTB (solvatation implicite ALPB dans l'eau) aux descripteurs g-xTB optionnels.
3. **Triage du domaine d'applicabilité** : Diagnostic topologique 2D basé sur la conservation de l'aromaticité et la hiérarchie basée sur la connectivité (CBH) de Raghavachari.

---

## ⚡ Démarrage rapide sur Google Colab (Sans installation locale)

Exécutez Hydra-PaiNN directement dans votre navigateur via Google Colab :

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/KeantChen/TautomerRatio/blob/main/notebooks/Hydra_PaiNN_Quickstart.ipynb)

* **Formulaire interactif** : Saisissez deux chaînes SMILES pour visualiser les structures 2D et les pourcentages de population de Boltzmann prédits.
* **Cartes récapitulatives** : Consultez ΔG_aq, log10(K_eq), K_eq et le diagnostic du domaine d'applicabilité.
* **Traitement par lots (CSV)** : Évaluez un fichier CSV et comparez les résultats aux valeurs expérimentales.
* **Matériel** : Fonctionne sur CPU ou GPU dans Google Colab.

---

## 🎯 Domaines d'applicabilité et sous-ensembles

Les paires de tautomères sont réparties en amont selon la conservation de l'aromaticité et les règles CBH de Raghavachari :

### 1. Comfort Zone ($|\Delta N_{\text{aro}}| = 0$, 79,4 % du jeu de données)
Paires de tautomères conservant le nombre d'atomes aromatiques :
* **CBH-Taut Subset** (11,3 % de TautoBase-539, 61 paires) :
  * **Critères** : Les états d'hybridation des atomes lourds ($H_i$) et les topologies de liaisons covalentes ($B_{ij}$) sont invariants entre les tautomères selon les règles homodesmotiques de Raghavachari.
  * **Résultats** :
    * **TautoBase-539** : MAE = **1.29 kcal/mol** (médiane = 1.15 kcal/mol, RMSE = 1.76 kcal/mol).
    * **DFT-460** : MAE = **1.38 kcal/mol** (référence DFT : MAE = 1.56 kcal/mol).
    * **sPhysNet-Taut-100** : MAE = **1.02 kcal/mol**.
* **Normal Subset** (68,1 % de TautoBase-539, 367 paires) :
  * **Critères** : L'aromaticité est conservée ($|\Delta N_{\text{aro}}| = 0$), avec des réarrangements localisés de liaisons et d'hybridation.
  * **Résultats** :
    * **TautoBase-539** : MAE = **1.97 kcal/mol** (médiane = 1.53 kcal/mol, RMSE = 2.56 kcal/mol, précision directionnelle = 88.3 %).
    * **DFT-460** : MAE = **1.78 kcal/mol** (référence DFT : MAE = 1.82 kcal/mol).
    * **sPhysNet-Taut-100** : MAE = **1.82 kcal/mol**.

### 2. Risk Zone ($|\Delta N_{\text{aro}}| > 0$, 20,6 % du jeu de données, 111 paires)
Transformations accompagnées de la création ou de la destruction de cycles aromatiques (par ex., phénol $\leftrightarrow$ cyclohexa-2,4-diénone).
* **Résultats** :
  * **TautoBase-539** : MAE = **5.14 kcal/mol** (médiane = 4.06 kcal/mol, RMSE = 6.73 kcal/mol).
  * **DFT-460** : MAE = **4.38 kcal/mol** (référence DFT : MAE = 4.07 kcal/mol).
* **Note** : (Update is coming soon)

---

### 📊 Hiérarchie à 3 niveaux (3-Tier)

| Niveau (Tier) | Sous-ensemble / Domaine | Critères | MAE attendue |
| :---: | :--- | :--- | :---: |
| **Tier 1** | **CBH-Taut Subset** | $\|\Delta N_\text{aro}\| = 0$, hybridations et types de liaisons invariants | **1.29 kcal/mol** |
| **Tier 2** | **Normal Subset** | $\|\Delta N_\text{aro}\| = 0$, aromaticité conservée | **1.97 kcal/mol** |
| **Tier 3** | **Risk Zone** | $\|\Delta N_\text{aro}\| > 0$, transition d'aromaticité | **5.14 kcal/mol** *(Update is coming soon)* |

---

## 💻 Installation et configuration locales

### 1. Cloner le dépôt et installer les dépendances Python
```bash
git clone https://github.com/KeantChen/TautomerRatio.git
cd TautomerRatio

pip install -r requirements.txt
```

### 2. Vérifier l'installation
Exécutez le script d'auto-test :
```bash
python verify_installation.py
```

---

## 🚀 Utilisation en ligne de commande (CLI)

### 1. Triage topologique 2D
Évaluer le domaine d'applicabilité et l'incertitude attendue sans exécuter de calcul quantique :
```bash
python predict.py --smi1 "OC1=CC=CC=N1" --smi2 "O=C1NC=CC=C1" --triage_only
```

### 2. Prédiction standard (Tour A xTB, autonome)
Prédire la différence d'énergie libre en phase aqueuse, la constante d'équilibre et le tautomère majoritaire :
```bash
python predict.py --smi1 "OC1=CC=CC=N1" --smi2 "O=C1NC=CC=C1" --mode xtb_only
```

### 3. Prédiction multi-tours (Tours A, B et C)
Lorsque g-xTB est configuré (voir [bin/README_ENGINES.md](bin/README_ENGINES.md)) :
```bash
python predict.py --smi1 "OC1=CC=CC=N1" --smi2 "O=C1NC=CC=C1" --mode three_towers
```

### 4. Prédiction par lots à partir d'un fichier CSV
Évaluer un ensemble de paires de tautomères :
```bash
python predict.py --input examples/test_cases.csv --output predictions.csv --mode xtb_only
```

---

## 🐍 Utilisation via l'API Python

```python
from tautomer_predictor import TautomerPredictor

# 1. Initialiser le prédicteur (charge les poids et les paramètres de normalisation)
predictor = TautomerPredictor()

# 2. Triage topologique 2D
triage = predictor.triage_check("OC1=CC=CC=N1", "O=C1NC=CC=C1")
print(f"Domaine : {triage['domain']} ({triage['subset']}) | MAE attendue : {triage['expected_mae']} kcal/mol")

# 3. Prédiction complète
result = predictor.predict(
    smiles_A="OC1=CC=CC=N1",
    smiles_B="O=C1NC=CC=C1",
    mode="xtb_only",       # ou "three_towers"
    temperature=298.15,    # Kelvin
    solvent="water"        # solvant ALPB
)

# Afficher le rapport
predictor.print_report(result)
```

---

## 📁 Structure du répertoire

```text
TautomerRatio/
├── notebooks/
│   └── Hydra_PaiNN_Quickstart.ipynb # Notebook Google Colab
├── bin/
│   ├── xtb.exe                      # Exécutable précompilé xTB 6.7.1 (Windows)
│   ├── libiomp5md.dll               # Runtime Intel OpenMP
│   └── README_ENGINES.md            # Instructions pour Linux et WSL
├── models/
│   ├── hydra_painn_best.pth         # Poids du modèle PyTorch entraîné
│   └── scalers/                     # Paramètres de normalisation des descripteurs
├── examples/
│   ├── test_cases.csv               # Paires de validation avec valeurs expérimentales (3 niveaux)
│   └── test_predictions.csv         # Sortie de référence
├── tautomer_predictor.py            # Moteur de prédiction principal
├── predict.py                       # Interface en ligne de commande (CLI)
├── verify_installation.py           # Script de diagnostic et d'auto-test
├── CASE_STUDIES.md                  # Études de cas détaillées
├── README.md                        # Documentation en anglais
├── README_CN.md                     # Documentation en chinois
└── README_FR.md                     # Documentation en français
```

---

## 📄 Licence
Ce projet est distribué sous licence MIT — voir le fichier [LICENSE](LICENSE) pour plus de détails.
