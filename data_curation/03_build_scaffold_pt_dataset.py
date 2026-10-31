#!/usr/bin/env python
"""
03_build_scaffold_pt_dataset.py
===============================
Bemis-Murcko Scaffold Splitting (88/10/2) and PyTorch Geometric Graph Serialization.

Author: Cheng Chen
Institution: McGill University / Moitessier Research Group
Date: 2026-03
License: MIT

This script performs the strict, zero-leakage Bemis-Murcko scaffold split:
  - 88% Training Set (train_hydra.pt)
  - 10% Validation Set (val_hydra.pt)
  - 2% Independent Test Set (test_hydra.pt)
And serializes molecular structures into PyG Data objects with:
  - Atomic numbers (z)
  - 3D conformer coordinates (pos)
  - Bond topology (edge_index)
  - 12D global xTB features (global_features_xtb)
  - 12D global g-xTB features (global_features_gxtb)
  - Target DFT reference energies (y)
"""

import os
import sys
import argparse
import random
from collections import defaultdict
import numpy as np
import pandas as pd
import torch
from rdkit import Chem
from rdkit.Chem import AllChem
from rdkit.Chem.Scaffolds import MurckoScaffold
from torch_geometric.data import Data

XTB_COLS = [
    "xtb_Gap_eV", "xtb_Dipole", "xtb_Gelec", "xtb_Gsasa", "xtb_Ghb",
    "xtb_iso_ES", "xtb_dispersion", "xtb_repulsion", "xtb_Mol_alpha",
    "xtb_alpha_max", "xtb_alpha_mean", "xTB_E"
]

GXTB_COLS = [
    "gxtb_electronegativity", "gxtb_hardness", "gxtb_electrophilicity",
    "gxtb_fukui_elec", "gxtb_fukui_nuc", "gxtb_local_softness",
    "gxtb_HOMO_eV", "gxtb_LUMO_eV", "gxtb_gap_eV",
    "gxtb_dipole_x", "gxtb_dipole_y", "gxtb_dipole_z"
]

def get_scaffold(smiles: str) -> str:
    """Return Bemis-Murcko scaffold SMILES."""
    try:
        mol = Chem.MolFromSmiles(smiles)
        if mol is None:
            return ""
        return MurckoScaffold.MurckoScaffoldSmiles(mol=mol, includeChirality=False).strip()
    except Exception:
        return ""

def mol_to_pyg_data(row, smi_col='SMILES', target_col='dft_water') -> Data:
    """Construct PyG Data instance from tabular record."""
    smi = str(row[smi_col]).strip()
    mol = Chem.MolFromSmiles(smi)
    if mol is None:
        return None
    mol = Chem.AddHs(mol)
    params = AllChem.ETKDGv3()
    params.randomSeed = 42
    status = AllChem.EmbedMolecule(mol, params)
    if status != 0:
        AllChem.EmbedMolecule(mol, AllChem.ETKDG())

    try:
        conf = mol.GetConformer()
        pos = torch.tensor(conf.GetPositions(), dtype=torch.float)
    except Exception:
        pos = torch.zeros((mol.GetNumAtoms(), 3), dtype=torch.float)

    z = torch.tensor([atom.GetAtomicNum() for atom in mol.GetAtoms()], dtype=torch.long)

    edge_list = []
    for bond in mol.GetBonds():
        i = bond.GetBeginAtomIdx()
        j = bond.GetEndAtomIdx()
        edge_list.append([i, j])
        edge_list.append([j, i])
    if edge_list:
        edge_index = torch.tensor(edge_list, dtype=torch.long).t().contiguous()
    else:
        edge_index = torch.empty((2, 0), dtype=torch.long)

    xtb_feats = [float(row.get(c, 0.0)) for c in XTB_COLS]
    gxtb_feats = [float(row.get(c, 0.0)) for c in GXTB_COLS]

    global_xtb = torch.tensor(xtb_feats, dtype=torch.float).unsqueeze(0)
    global_gxtb = torch.tensor(gxtb_feats, dtype=torch.float).unsqueeze(0)

    y_val = float(row.get(target_col, 0.0))
    y = torch.tensor([[y_val]], dtype=torch.float)

    data = Data(z=z, pos=pos, edge_index=edge_index, y=y)
    data.global_features_xtb = global_xtb
    data.global_features_gxtb = global_gxtb
    data.smiles = smi
    return data

def scaffold_split(df, smi_col='SMILES', train_ratio=0.88, val_ratio=0.10, test_ratio=0.02, seed=42):
    """Partition dataset by Bemis-Murcko scaffolds."""
    scaffold_to_indices = defaultdict(list)
    for idx, smi in enumerate(df[smi_col]):
        scaff = get_scaffold(smi)
        scaffold_to_indices[scaff].append(idx)

    scaffold_sets = list(scaffold_to_indices.values())
    random.seed(seed)
    random.shuffle(scaffold_sets)

    n_total = len(df)
    train_cutoff = int(n_total * train_ratio)
    val_cutoff = int(n_total * (train_ratio + val_ratio))

    train_idx, val_idx, test_idx = [], [], []
    for sc_group in scaffold_sets:
        if len(train_idx) + len(sc_group) <= train_cutoff:
            train_idx.extend(sc_group)
        elif len(val_idx) + len(sc_group) <= val_cutoff:
            val_idx.extend(sc_group)
        else:
            test_idx.extend(sc_group)

    return train_idx, val_idx, test_idx

def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    default_in = os.path.join(script_dir, "Master_Dataset_Final_Train_Ready.csv")
    default_out_dir = os.path.join(script_dir, "pt_datasets")

    parser = argparse.ArgumentParser(description="Scaffold Split & PyG Serialization")
    parser.add_argument("--input_csv", type=str, default=default_in, help="Input merged CSV")
    parser.add_argument("--output_dir", type=str, default=default_out_dir, help="Directory to save .pt files")
    parser.add_argument("--max_samples", type=int, default=None, help="Demo cap on samples")
    args = parser.parse_args()

    print("=" * 80)
    print("  [Stage 3/4] Bemis-Murcko Scaffold Partition & PyG Graph Tensor Serialization")
    print("=" * 80)
    print(f"  Input:      {args.input_csv}")
    print(f"  Output Dir: {args.output_dir}")
    print("=" * 80)

    if not os.path.exists(args.input_csv):
        print(f"[!] Warning: Input CSV not found: {args.input_csv}. Creating dummy samples.")
        df = pd.DataFrame({
            'SMILES': ["Oc1ccccn1", "O=c1cccc[nH]1", "CC(=O)CC(=O)C", "c1ccccc1", "c1ccncc1", "c1ccoc1"],
            'dft_water': [-300.5, -300.55, -280.1, -230.2, -245.8, -225.1]
        })
    else:
        df = pd.read_csv(args.input_csv, nrows=args.max_samples)

    smi_col = 'SMILES' if 'SMILES' in df.columns else df.columns[0]
    train_idx, val_idx, test_idx = scaffold_split(df, smi_col=smi_col)

    print(f"Scaffold Partition Summary:")
    print(f"  Train: {len(train_idx):,} ({len(train_idx)/len(df)*100:.1f}%)")
    print(f"  Val:   {len(val_idx):,} ({len(val_idx)/len(df)*100:.1f}%)")
    print(f"  Test:  {len(test_idx):,} ({len(test_idx)/len(df)*100:.1f}%)")

    splits = {'train': train_idx, 'val': val_idx, 'test': test_idx}
    os.makedirs(args.output_dir, exist_ok=True)

    for split_name, indices in splits.items():
        data_list = []
        for i in indices:
            row = df.iloc[i]
            d = mol_to_pyg_data(row, smi_col=smi_col)
            if d is not None:
                data_list.append(d)
        out_pt = os.path.join(args.output_dir, f"{split_name}_hydra.pt")
        torch.save(data_list, out_pt)
        print(f"Saved {len(data_list)} PyG graphs -> {out_pt}")

    print("\n[SUCCESS] Scaffold-split PyG datasets generated successfully.\n")

if __name__ == "__main__":
    main()
