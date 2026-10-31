#!/usr/bin/env python
"""
04_curate_benchmark_datasets.py
===============================
Independent Experimental Benchmark Curation (TautoBase 539 & SAMPL2 28)
and 3-Tier Topological Applicability Domain Stratification.

Author: Cheng Chen
Institution: McGill University / Moitessier Research Group
Date: 2026-03
License: MIT
"""

import os
import sys
import argparse
import numpy as np
import pandas as pd
from rdkit import Chem
from rdkit.Chem import Descriptors, rdMolDescriptors

R_GAS_KCAL = 1.98720425864083e-3  # kcal / (mol * K)
TEMP_DEFAULT = 298.15             # Kelvin

def compute_3tier_triage(smiles_A: str, smiles_B: str) -> dict:
    """Evaluate 3-Tier topological applicability domain."""
    mol_A = Chem.MolFromSmiles(smiles_A)
    mol_B = Chem.MolFromSmiles(smiles_B)
    if mol_A is None or mol_B is None:
        return {'tier': 3, 'tier_name': 'Tier 3 (Risk Zone)', 'status': 'HIGH_RISK'}

    n_aro_A = sum(1 for a in mol_A.GetAtoms() if a.GetIsAromatic())
    n_aro_B = sum(1 for a in mol_B.GetAtoms() if a.GetIsAromatic())
    is_aro_changed = (n_aro_A != n_aro_B)

    n_arorings_A = rdMolDescriptors.CalcNumAromaticRings(mol_A)
    n_arorings_B = rdMolDescriptors.CalcNumAromaticRings(mol_B)

    def get_bond_counts(m):
        c = {}
        for b in m.GetBonds():
            bt = b.GetBondTypeAsDouble()
            a1 = min(b.GetBeginAtom().GetAtomicNum(), b.GetEndAtom().GetAtomicNum())
            a2 = max(b.GetBeginAtom().GetAtomicNum(), b.GetEndAtom().GetAtomicNum())
            key = (a1, a2, bt)
            c[key] = c.get(key, 0) + 1
        return c

    bc_A = get_bond_counts(mol_A)
    bc_B = get_bond_counts(mol_B)
    cbh2_conserved = (bc_A == bc_B)

    if is_aro_changed or (n_arorings_A != n_arorings_B):
        return {'tier': 3, 'tier_name': 'Tier 3 (Risk Zone - Aromatic Disruption)', 'status': 'HIGH_RISK', 'expected_mae': 3.42}
    elif cbh2_conserved:
        return {'tier': 1, 'tier_name': 'Tier 1 (Golden Subset - Strictly Isodesmic)', 'status': 'HIGH_CONFIDENCE', 'expected_mae': 0.82}
    else:
        return {'tier': 2, 'tier_name': 'Tier 2 (Normal Subset)', 'status': 'COMFORT_ZONE', 'expected_mae': 1.85}

def find_file(script_dir: str, rel_path: str):
    p1 = os.path.abspath(os.path.join(script_dir, rel_path))
    if os.path.exists(p1):
        return p1
    p2 = os.path.abspath(os.path.join(script_dir, "..", rel_path))
    if os.path.exists(p2):
        return p2
    return p1

def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    default_tb_raw = find_file(script_dir, "raw_data/tautobase/tautobase_full_raw.csv")
    default_sampl2_raw = find_file(script_dir, "raw_data/sampl2/samplr2_final.csv")
    default_out_dir = os.path.join(script_dir, "benchmarks")

    parser = argparse.ArgumentParser(description="TautoBase & SAMPL2 Benchmark Curation")
    parser.add_argument("--tautobase_raw", type=str, default=default_tb_raw, help="Path to raw TautoBase CSV")
    parser.add_argument("--sampl2_raw", type=str, default=default_sampl2_raw, help="Path to raw SAMPL2 CSV")
    parser.add_argument("--output_dir", type=str, default=default_out_dir, help="Directory to save curated benchmark CSVs")
    args = parser.parse_args()

    print("=" * 80)
    print("  [Stage 4/4] Independent Experimental Benchmark Datasets Curation")
    print("=" * 80)
    print(f"  Source TautoBase: {args.tautobase_raw}")
    print(f"  Source SAMPL2:    {args.sampl2_raw}")
    print(f"  Output Dir:       {args.output_dir}")
    print("=" * 80)

    os.makedirs(args.output_dir, exist_ok=True)

    if os.path.exists(args.tautobase_raw):
        print("\nLoading TautoBase raw database...")
        df_raw = pd.read_csv(args.tautobase_raw)
        print(f"  Total raw entries: {len(df_raw)}")

        water_mask = df_raw['State/Solvent'].astype(str).str.contains('water', case=False, na=False)
        w_df = df_raw[water_mask].copy()
        print(f"  Water solvent records: {len(w_df)}")

        records = []
        for idx, row in w_df.iterrows():
            logk_val = row.get('log K')
            if pd.isna(logk_val):
                continue
            try:
                logk = float(logk_val)
            except (ValueError, TypeError):
                continue

            smi_A = str(row['SMILES_A']).strip()
            smi_B = str(row['SMILES_B']).strip()
            mol_A = Chem.MolFromSmiles(smi_A)
            mol_B = Chem.MolFromSmiles(smi_B)
            if mol_A is None or mol_B is None:
                continue

            exp_dg = -2.302585 * R_GAS_KCAL * TEMP_DEFAULT * logk
            triage = compute_3tier_triage(smi_A, smi_B)

            records.append({
                'pair_id': f"TB_{len(records)+1:04d}",
                'smiles_A': smi_A,
                'smiles_B': smi_B,
                'log_K': logk,
                'exp_dG': exp_dg,
                'tier': triage['tier'],
                'tier_name': triage['tier_name'],
                'status': triage['status']
            })

        df_tb_curated = pd.DataFrame(records)
        tb_out = os.path.join(args.output_dir, "tautobase_curated_539.csv")
        df_tb_curated.to_csv(tb_out, index=False)
        print(f"  [OK] Successfully extracted {len(df_tb_curated)} water tautomer pairs.")
        print(f"       Tier 1 (Golden):  {(df_tb_curated['tier']==1).sum()} pairs")
        print(f"       Tier 2 (Normal):  {(df_tb_curated['tier']==2).sum()} pairs")
        print(f"       Tier 3 (Risk):    {(df_tb_curated['tier']==3).sum()} pairs")
        print(f"       Saved to -> {tb_out}")
    else:
        print(f"[!] Warning: Raw TautoBase CSV not found at {args.tautobase_raw}")

    if os.path.exists(args.sampl2_raw):
        print("\nLoading SAMPL2 experimental database...")
        df_s2 = pd.read_csv(args.sampl2_raw)
        s2_out = os.path.join(args.output_dir, "sampl2_curated_28.csv")
        df_s2.to_csv(s2_out, index=False)
        print(f"  [OK] Curated {len(df_s2)} SAMPL2 experimental pairs -> {s2_out}")

    print("\n[SUCCESS] Benchmark datasets curation complete.\n")

if __name__ == "__main__":
    main()
