"""
00_extract_raw_frag20_taut.py
==============================
Extracts raw Frag20-taut pickle partitions (*.pl) from the original Frag20 dataset
release into standardized tabular CSV format (SMILES, E_gas_DFT, E_water_DFT, MolBlock).

Author: Cheng Chen
Institution: McGill University / Moitessier Research Group
Date: 2026-03
License: MIT
"""

import os
import sys
import pickle
import argparse
import pandas as pd

def extract_pl_partition(pl_path: str) -> pd.DataFrame:
    """Reads a .pl pickle partition file and standardizes column naming."""
    print(f"[*] Reading pickle partition: {pl_path}")
    with open(pl_path, "rb") as f:
        data = pickle.load(f)
    
    if not isinstance(data, pd.DataFrame):
        raise ValueError(f"Expected pandas DataFrame in {pl_path}, found {type(data)}")
    
    rename_dict = {
        "smi_dft": "SMILES",
        "E_gas": "E_gas_DFT",
        "E_water": "E_water_DFT",
        "molbock_dft": "MolBlock"
    }
    
    available_cols = [c for c in rename_dict.keys() if c in data.columns]
    df_sub = data[available_cols].rename(columns=rename_dict)
    print(f"    Loaded {len(df_sub):,} records with columns: {list(df_sub.columns)}")
    return df_sub

def resolve_raw_dir(script_dir: str, candidate_dir: str) -> str:
    """Resolves raw directory path across local DMP and release repo structures."""
    if os.path.isabs(candidate_dir) and os.path.exists(candidate_dir):
        return candidate_dir
    # Check candidate relative to script_dir
    p1 = os.path.abspath(os.path.join(script_dir, candidate_dir))
    if os.path.exists(p1):
        return p1
    # Check ./raw_data/frag20_taut
    p2 = os.path.abspath(os.path.join(script_dir, "raw_data", "frag20_taut"))
    if os.path.exists(p2):
        return p2
    # Check ../raw_data/frag20_taut
    p3 = os.path.abspath(os.path.join(script_dir, "..", "raw_data", "frag20_taut"))
    if os.path.exists(p3):
        return p3
    return p1

def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    parser = argparse.ArgumentParser(description="Extract Frag20-taut .pl partitions into unified CSV.")
    parser.add_argument("--raw_dir", type=str, default="raw_data/frag20_taut",
                        help="Directory containing frag20_taut_*.pl files.")
    parser.add_argument("--output_csv", type=str, default="taut_extracted_from_pl.csv",
                        help="Target output CSV path.")
    parser.add_argument("--demo", action="store_true",
                        help="Fast demo mode (extracts validation partition or sample CSV).")
    args = parser.parse_args()

    raw_dir = resolve_raw_dir(script_dir, args.raw_dir)
    out_csv = args.output_csv if os.path.isabs(args.output_csv) else os.path.join(script_dir, args.output_csv)
    os.makedirs(os.path.dirname(os.path.abspath(out_csv)), exist_ok=True)
    
    partitions = ["valid"] if args.demo else ["train", "valid", "test"]
    dfs = []
    
    for split in partitions:
        pl_file = os.path.join(raw_dir, f"frag20_taut_{split}.pl")
        if os.path.exists(pl_file):
            df_part = extract_pl_partition(pl_file)
            df_part["Partition"] = split
            dfs.append(df_part)
        else:
            print(f"[!] Info: Partition file not found: {pl_file}")
            
    if not dfs:
        # Check if sample CSV is available in raw_dir
        sample_csv = os.path.join(raw_dir, "frag20_taut_sample_1000.csv")
        if os.path.exists(sample_csv):
            print(f"[*] Raw .pl archives not found in this lightweight repository.")
            print(f"    (Full archives are preserved in local DMP storage; using included authentic sample dataset: {sample_csv})")
            sample_df = pd.read_csv(sample_csv, nrows=100 if args.demo else 1000)
            sample_df.to_csv(out_csv, index=False)
            print(f"[+] Successfully copied {len(sample_df):,} sample records to: {out_csv}")
            return
        else:
            print("[!] Error: Neither .pl files nor sample CSV were found.")
            sys.exit(1)
        
    full_df = pd.concat(dfs, ignore_index=True)
    full_df.to_csv(out_csv, index=False)
    print(f"[+] Successfully extracted {len(full_df):,} records to: {out_csv}")

if __name__ == "__main__":
    main()
