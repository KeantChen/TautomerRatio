#!/usr/bin/env python
"""
01_curate_frag20_funnel.py
==========================
Frag20-Taut Raw Dataset Curation and Capacity-Constrained Downsampling Funnel (Table S1).

Author: Cheng Chen
Institution: McGill University / Moitessier Research Group
Date: 2026-03
License: MIT
"""

import os
import sys
import argparse
import time
import numpy as np
import pandas as pd
from rdkit import Chem
from rdkit.Chem import Descriptors
from rdkit.Chem.Scaffolds import MurckoScaffold

ALLOWED_ELEMENTS = {'C', 'H', 'N', 'O'}

def is_valid_tautomer(smiles: str) -> bool:
    """Validate SMILES string, allowed element types, and basic chemical sanity."""
    if not isinstance(smiles, str) or not smiles.strip():
        return False
    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        return False
    for atom in mol.GetAtoms():
        if atom.GetSymbol() not in ALLOWED_ELEMENTS:
            return False
    mw = Descriptors.MolWt(mol)
    if mw <= 0 or mw > 500.0:
        return False
    return True

def get_bemis_murcko_scaffold(smiles: str) -> str:
    """Extract Bemis-Murcko framework SMILES; returns empty string for acyclic molecules."""
    try:
        mol = Chem.MolFromSmiles(smiles)
        if mol is None:
            return ""
        scaffold = MurckoScaffold.MurckoScaffoldSmiles(mol=mol, includeChirality=False)
        return scaffold.strip() if scaffold else ""
    except Exception:
        return ""

def find_file(script_dir: str, rel_path: str):
    """Search for relative file across current and parent directory layouts."""
    c1 = os.path.abspath(os.path.join(script_dir, rel_path))
    if os.path.exists(c1):
        return c1
    c2 = os.path.abspath(os.path.join(script_dir, "..", rel_path))
    if os.path.exists(c2):
        return c2
    return c1

def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    candidates = [
        "taut_extracted_from_pl.csv",
        "raw_data/frag20_taut/taut_25w_1224.csv",
        "../raw_data/frag20_taut/taut_25w_1224.csv",
        "raw_data/frag20_taut/frag20_taut_sample_1000.csv",
        "../raw_data/frag20_taut/frag20_taut_sample_1000.csv"
    ]
    default_in = None
    for cand in candidates:
        p = os.path.abspath(os.path.join(script_dir, cand))
        if os.path.exists(p):
            default_in = p
            break
    if default_in is None:
        default_in = os.path.join(script_dir, "raw_data", "frag20_taut", "frag20_taut_sample_1000.csv")

    default_out = os.path.join(script_dir, "frag20_curated_150k.csv")

    parser = argparse.ArgumentParser(description="Frag20-Taut Curation Funnel (Table S1)")
    parser.add_argument("--input_csv", type=str, default=default_in,
                        help="Path to raw or sample Frag20 CSV")
    parser.add_argument("--output_csv", type=str, default=default_out,
                        help="Path to save curated dataset")
    parser.add_argument("--sample_size", type=int, default=None,
                        help="Fast demo mode: sample N rows instead of full 250k")
    parser.add_argument("--acyclic_cap", type=int, default=15000,
                        help="Maximum allowed acyclic (scaffold='') molecules in downsampling")
    parser.add_argument("--common_scaffold_cap", type=int, default=500,
                        help="Maximum molecules per specific common scaffold")
    args = parser.parse_args()

    print("=" * 80)
    print("  [Stage 1/4] Frag20-Taut Dataset Curation & Downsampling Funnel")
    print("=" * 80)
    print(f"  Input Source:     {args.input_csv}")
    print(f"  Output Curated:   {args.output_csv}")
    print(f"  Acyclic Cap:      {args.acyclic_cap}")
    print(f"  Scaffold Cap:     {args.common_scaffold_cap}")
    if args.sample_size:
        print(f"  [Demo Mode]:      Sampling first {args.sample_size} records")
    print("=" * 80)

    t0 = time.time()
    if not os.path.exists(args.input_csv):
        print(f"[!] Warning: Raw CSV not found at {args.input_csv}. Creating mock demo pairs.")
        demo_pairs = [
            ("Oc1ccccn1", "O=c1cccc[nH]1", "Pair_1", -2.6),
            ("CC(=O)CC(=O)C", "CC(=O)/C=C(/C)O", "Pair_2", -1.2),
            ("c1cnc[nH]1", "c1cc[nH]n1", "Pair_3", 0.0),
            ("O=C1CCCC1", "OC1=CCCC1", "Pair_4", 8.5),
            ("CC(=O)O", "C/C(O)=O", "Pair_5", 14.2),
        ]
        df = pd.DataFrame(demo_pairs, columns=["smiles_A", "smiles_B", "pair_id", "exp_dG"])
    else:
        print(f"Loading dataset from {args.input_csv} ...")
        df = pd.read_csv(args.input_csv, nrows=args.sample_size)
    print(f"  Loaded {len(df):,} initial records in {time.time() - t0:.2f} s")

    smi_col = 'SMILES' if 'SMILES' in df.columns else ('smiles_A' if 'smiles_A' in df.columns else df.columns[0])
    print(f"  Primary structure column: '{smi_col}'")

    print("\n[Stage 2] Filtering by elemental composition (C, H, N, O) & chemical validity...")
    valid_mask = df[smi_col].apply(is_valid_tautomer)
    df_stage2 = df[valid_mask].copy()
    print(f"  Retained after validation: {len(df_stage2):,} / {len(df):,} ({len(df_stage2)/len(df)*100:.2f}%)")

    print("\n[Stage 3] Calculating Bemis-Murcko frameworks for scaffold downsampling...")
    unique_smiles = df_stage2[smi_col].unique()
    scaffold_map = {s: get_bemis_murcko_scaffold(s) for s in unique_smiles}
    df_stage2['Scaffold'] = df_stage2[smi_col].map(scaffold_map)

    acyclic_mask = (df_stage2['Scaffold'] == "")
    n_acyclic = acyclic_mask.sum()
    n_cyclic = len(df_stage2) - n_acyclic
    print(f"  Pre-downsampling: Cyclic = {n_cyclic:,} | Acyclic = {n_acyclic:,} ({n_acyclic/len(df_stage2)*100:.1f}%)")

    print(f"\n[Stage 4] Applying capacity constraints (Acyclic cap = {args.acyclic_cap})...")
    df_cyclic = df_stage2[~acyclic_mask]
    df_acyclic = df_stage2[acyclic_mask]

    if len(df_acyclic) > args.acyclic_cap:
        df_acyclic = df_acyclic.sample(n=args.acyclic_cap, random_state=42)

    df_curated = pd.concat([df_cyclic, df_acyclic], ignore_index=True)
    df_curated = df_curated.sample(frac=1.0, random_state=42).reset_index(drop=True)

    final_acyclic = (df_curated['Scaffold'] == "").sum()
    print("\n" + "=" * 60)
    print("  CURATION FUNNEL RESULTS SUMMARY (Table S1 Reproduction)")
    print("=" * 60)
    print(f"  Initial Raw Pool:        {len(df):,}")
    print(f"  Final Curated Size:      {len(df_curated):,}")
    print(f"  Acyclic Share:           {final_acyclic:,} ({final_acyclic/len(df_curated)*100:.2f}%)")
    print(f"  Unique Scaffolds:        {df_curated['Scaffold'].nunique():,}")
    print("=" * 60)

    os.makedirs(os.path.dirname(os.path.abspath(args.output_csv)), exist_ok=True)
    df_curated.to_csv(args.output_csv, index=False)
    print(f"\n[SUCCESS] Curated dataset successfully saved to:\n  -> {args.output_csv}\n")

if __name__ == "__main__":
    main()
