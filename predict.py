#!/usr/bin/env python
"""
Hydra-PaiNN Prediction CLI
==========================
One-click CLI tool for tautomeric free energy difference (ΔG_aq),
equilibrium ratio (K_eq), Boltzmann population, and 3-tier domain triage.

Examples:
    # 1. Fast 2D Topological Triage Only (< 1 ms, zero quantum calculation):
    python predict.py --smi1 "OC1=CC=CC=N1" --smi2 "O=C1NC=CC=C1" --triage_only

    # 2. Standard Prediction (Mode: xtb_only, standalone Tower A):
    python predict.py --smi1 "OC1=CC=CC=N1" --smi2 "O=C1NC=CC=C1"

    # 3. Full Multi-Tower Prediction (Mode: three_towers, Tower A + B + C):
    python predict.py --smi1 "OC1=CC=CC=N1" --smi2 "O=C1NC=CC=C1" --mode three_towers

    # 4. Batch Prediction from CSV:
    python predict.py --input examples/test_cases.csv --output predictions.csv --mode xtb_only
"""

import os
import sys
import argparse
import pandas as pd
from tautomer_predictor import TautomerPredictor


def run_batch(predictor, input_csv, output_csv, mode="xtb_only", temp=298.15, solvent="water"):
    print(f"\n[Hydra-PaiNN] Starting Batch Prediction on {input_csv} (Mode: {mode}) ...")
    df = pd.read_csv(input_csv)

    # Identify SMILES columns
    col_a = next((c for c in ['smi1', 'smiles1', 'smiles_A', 'tautomer1', 'tautomer_A'] if c in df.columns), None)
    col_b = next((c for c in ['smi2', 'smiles2', 'smiles_B', 'tautomer2', 'tautomer_B'] if c in df.columns), None)

    if not col_a or not col_b:
        raise ValueError(f"Could not automatically detect tautomer SMILES columns in {input_csv}. Available columns: {list(df.columns)}")

    results = []
    total = len(df)
    for idx, row in df.iterrows():
        smi_a = str(row[col_a]).strip()
        smi_b = str(row[col_b]).strip()
        pair_id = row.get('id', f"Pair_{idx+1}")
        pair_name = row.get('name', '')
        print(f"[{idx+1}/{total}] Processing {pair_id} ({pair_name}) ..." if pair_name else f"[{idx+1}/{total}] Processing {pair_id} ...")

        try:
            res = predictor.predict(smi_a, smi_b, mode=mode, temperature=temp, solvent=solvent)
            rec = res['recommended_prediction']
            triage = res['triage']
            ta = res['tower_results']['tower_A_xtb_only']
            tb = res['tower_results']['tower_B_gxtb_only']
            tc = res['tower_results']['tower_C_mixed_fusion']

            res_dict = {
                'id': pair_id,
            }
            if 'name' in row and pd.notna(row['name']):
                res_dict['name'] = str(row['name'])

            res_dict.update({
                'triage_tier': triage['tier'],
                'subset': triage.get('subset', triage['tier_name']),
                'domain': triage['domain'],
                'pred_dG_kcal_mol': round(rec['delta_G_kcal_mol'], 2),
            })

            if 'dG_exp' in row and pd.notna(row['dG_exp']):
                exp_dg = float(row['dG_exp'])
                res_dict['dG_exp'] = round(exp_dg, 2)
                res_dict['error_abs_kcal'] = round(abs(rec['delta_G_kcal_mol'] - exp_dg), 2)

            res_dict['pred_log10_K'] = round(rec['log10_K'], 2)
            if 'logK_exp' in row and pd.notna(row['logK_exp']):
                res_dict['logK_exp'] = round(float(row['logK_exp']), 2)

            res_dict['major_tautomer'] = rec['major_tautomer']
            if 'exp_major' in row and pd.notna(row['exp_major']):
                res_dict['exp_major'] = str(row['exp_major'])

            res_dict.update({
                'pop_A_pct': rec['population_pct']['A'],
                'pop_B_pct': rec['population_pct']['B'],
                'expected_mae_kcal': triage['expected_mae'],
                'SMILES_A': smi_a,
                'SMILES_B': smi_b,
                'pred_K_eq': rec['K_eq'],
                'recommended_tower': res['recommended_tower'],
                'tower_A_dG': ta.get('delta_G_kcal_mol', None),
                'tower_B_dG': tb.get('delta_G_kcal_mol', None),
                'tower_C_dG': tc.get('delta_G_kcal_mol', None),
            })
            results.append(res_dict)
        except Exception as e:
            print(f"  [Error] Failed on {pair_id}: {e}")
            results.append({
                'id': pair_id,
                'SMILES_A': smi_a,
                'SMILES_B': smi_b,
                'error': str(e)
            })

    out_df = pd.DataFrame(results)
    out_df.to_csv(output_csv, index=False)
    print(f"\n[Hydra-PaiNN] Batch processing complete! Results saved to: {output_csv}\n")
    if 'error_abs_kcal' in out_df.columns:
        valid = out_df.dropna(subset=['error_abs_kcal'])
        if len(valid) > 0:
            print(f"  Evaluation on {len(valid)} labeled pairs: Overall MAE = {valid['error_abs_kcal'].mean():.2f} kcal/mol")
            if 'triage_tier' in valid.columns:
                for tier_val, grp in valid.groupby('triage_tier'):
                    sub_name = grp['subset'].iloc[0] if 'subset' in grp.columns else f"Tier {tier_val}"
                    print(f"    - Tier {tier_val} ({sub_name}, N={len(grp)}): MAE = {grp['error_abs_kcal'].mean():.2f} kcal/mol")


def main():
    parser = argparse.ArgumentParser(description="Hydra-PaiNN: Tautomer Free Energy, Ratio, and 3-Tier Domain Triage Predictor.")
    parser.add_argument("--smi1", "--smiles_A", "-a", type=str, help="SMILES of Tautomer A")
    parser.add_argument("--smi2", "--smiles_B", "-b", type=str, help="SMILES of Tautomer B")
    parser.add_argument("--mode", type=str, default="xtb_only", choices=["xtb_only", "three_towers"],
                        help="Prediction mode: 'xtb_only' (standalone, fast) or 'three_towers' (xTB + g-xTB + Mixed fusion). Default: xtb_only")
    parser.add_argument("--temp", type=float, default=298.15, help="Temperature in Kelvin (default: 298.15)")
    parser.add_argument("--solvent", type=str, default="water", help="Solvent environment (default: water)")
    parser.add_argument("--triage_only", action="store_true", help="Perform 2D topological triage only without running 3D quantum calculations")
    parser.add_argument("--input", "-i", type=str, help="Input CSV path for batch predictions")
    parser.add_argument("--output", "-o", type=str, default="predictions.csv", help="Output CSV path for batch predictions (default: predictions.csv)")
    parser.add_argument("--xtb_bin", type=str, default=None, help="Custom path to xTB binary executable")
    parser.add_argument("--gxtb_cmd", type=str, default=None, help="Custom path/command to g-xTB executable (e.g. 'wsl /path/to/gxtb')")
    parser.add_argument("--device", type=str, default=None, help="Computation device ('cpu' or 'cuda', default: auto-detect)")

    args = parser.parse_args()

    # Fast 2D Triage
    if args.triage_only:
        if args.input:
            df = pd.read_csv(args.input)
            col_a = next((c for c in ['smi1', 'smiles1', 'smiles_A', 'tautomer1', 'tautomer_A'] if c in df.columns), None)
            col_b = next((c for c in ['smi2', 'smiles2', 'smiles_B', 'tautomer2', 'tautomer_B'] if c in df.columns), None)
            print("\n" + "=" * 90)
            print(f"  [Hydra-PaiNN] Batch 2D Topological Triage ({args.input})")
            print("=" * 90)
            print(f"  {'ID':<10} {'Tier':<8} {'Subset':<20} {'Domain':<16} {'Expected MAE':<15}")
            print("-" * 90)
            for idx, row in df.iterrows():
                pid = str(row.get('id', f"Pair_{idx+1}"))
                t = TautomerPredictor.triage_check(str(row[col_a]).strip(), str(row[col_b]).strip())
                print(f"  {pid:<10} Tier {t['tier']:<3} {t['subset']:<20} {t['domain']:<16} ±{t['expected_mae']:.2f} kcal/mol")
            print("=" * 90 + "\n")
            return

        if not args.smi1 or not args.smi2:
            parser.error("--triage_only requires either --input CSV or both --smi1 and --smi2.")
        triage = TautomerPredictor.triage_check(args.smi1, args.smi2)
        print("\n" + "=" * 78)
        print("  [Hydra-PaiNN] Quantum-Topological Domain & Triage Diagnostic (2D Fast)")
        print("=" * 78)
        print(f"  Tautomer A:    {args.smi1}")
        print(f"  Tautomer B:    {args.smi2}")
        print("-" * 78)
        print(f"  [Domain]:       {triage.get('domain', 'N/A')} ({triage.get('subset', 'N/A')})")
        print(f"  [Triage Tier]:  {triage['tier_name']}")
        print(f"  [Expected MAE]: ~{triage['expected_mae']:.2f} kcal/mol  |  Confidence: {triage['confidence']}")
        print(f"  [Diagnostic]:   {triage['message']}")
        if triage.get('bond_diff_details'):
            print(f"  [Bond Shifts]:  {', '.join(triage['bond_diff_details'])}")
        if triage.get('hyb_diff_details'):
            print(f"  [Hyb Shifts]:   {', '.join(triage['hyb_diff_details'])}")
        print("=" * 78 + "\n")
        return

    # Initialize Predictor
    predictor = TautomerPredictor(
        xtb_bin=args.xtb_bin,
        gxtb_cmd=args.gxtb_cmd,
        device=args.device
    )

    # Batch Mode
    if args.input:
        run_batch(predictor, args.input, args.output, mode=args.mode, temp=args.temp, solvent=args.solvent)
        return

    # Single Pair Mode
    if not args.smi1 or not args.smi2:
        parser.error("Please provide either --input CSV or both --smi1 and --smi2.")

    result = predictor.predict(args.smi1, args.smi2, mode=args.mode, temperature=args.temp, solvent=args.solvent)
    predictor.print_report(result)


if __name__ == "__main__":
    main()
