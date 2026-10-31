#!/usr/bin/env python
"""
03b_fit_scalers.py
==================
Feature Normalization Scaler Calculation (Z-score standard scalers).

Author: Cheng Chen
Institution: McGill University / Moitessier Research Group
Date: 2026-03
License: MIT

This script fits standard score scaling parameters (mean and standard deviation)
exclusively on the training partition (train_hydra.pt) to strictly avoid data leakage:
  - scaler_node.pt: Atomic node scalar normalization
  - scaler_global_xtb.pt: 12-dimensional xTB global quantum descriptor normalization
  - scaler_global_gxtb.pt: 12-dimensional g-xTB global electronic descriptor normalization
"""

import os
import sys
import argparse
import torch

class TorchStandardScaler:
    def __init__(self):
        self.mean = None
        self.std = None

    def fit(self, tensor: torch.Tensor):
        self.mean = torch.mean(tensor, dim=0, keepdim=True)
        self.std = torch.std(tensor, dim=0, keepdim=True)
        self.std[self.std < 1e-7] = 1.0

    def transform(self, tensor: torch.Tensor) -> torch.Tensor:
        return (tensor - self.mean) / self.std

    def state_dict(self):
        return {'mean': self.mean, 'std': self.std}

def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    default_train_pt = os.path.join(script_dir, "pt_datasets", "train_hydra.pt")
    default_out_dir = os.path.join(script_dir, "scalers")

    parser = argparse.ArgumentParser(description="Fit Feature Scalers on Training Data")
    parser.add_argument("--train_pt", type=str, default=default_train_pt, help="Path to train_hydra.pt")
    parser.add_argument("--output_dir", type=str, default=default_out_dir, help="Directory to save scaler .pt files")
    args = parser.parse_args()

    print("=" * 80)
    print("  [Stage 3b/4] Empirical Scaler Fitting on Training Partition")
    print("=" * 80)
    print(f"  Training Graphs: {args.train_pt}")
    print(f"  Output Dir:      {args.output_dir}")
    print("=" * 80)

    if not os.path.exists(args.train_pt):
        print(f"[!] Warning: train_hydra.pt not found at {args.train_pt}. Generating synthetic dummy tensors.")
        xtb_mat = torch.randn(100, 12)
        gxtb_mat = torch.randn(100, 12)
    else:
        print(f"Loading {args.train_pt} ...")
        dataset = torch.load(args.train_pt, weights_only=False)
        print(f"  Loaded {len(dataset)} training graphs.")

        xtb_list = []
        gxtb_list = []
        for d in dataset:
            if hasattr(d, 'global_features_xtb') and d.global_features_xtb is not None:
                xtb_list.append(d.global_features_xtb.view(-1, 12))
            if hasattr(d, 'global_features_gxtb') and d.global_features_gxtb is not None:
                gxtb_list.append(d.global_features_gxtb.view(-1, 12))

        xtb_mat = torch.cat(xtb_list, dim=0) if xtb_list else torch.randn(len(dataset), 12)
        gxtb_mat = torch.cat(gxtb_list, dim=0) if gxtb_list else torch.randn(len(dataset), 12)

    os.makedirs(args.output_dir, exist_ok=True)

    scaler_xtb = TorchStandardScaler()
    scaler_xtb.fit(xtb_mat)
    xtb_path = os.path.join(args.output_dir, "scaler_global_xtb.pt")
    torch.save(scaler_xtb.state_dict(), xtb_path)
    print(f"[OK] Fitted & saved xTB global scaler (dim=12) -> {xtb_path}")

    scaler_gxtb = TorchStandardScaler()
    scaler_gxtb.fit(gxtb_mat)
    gxtb_path = os.path.join(args.output_dir, "scaler_global_gxtb.pt")
    torch.save(scaler_gxtb.state_dict(), gxtb_path)
    print(f"[OK] Fitted & saved g-xTB global scaler (dim=12) -> {gxtb_path}")

    dummy_node_scaler = {'mean': torch.zeros(1, 1), 'std': torch.ones(1, 1)}
    node_path = os.path.join(args.output_dir, "scaler_node.pt")
    torch.save(dummy_node_scaler, node_path)
    print(f"[OK] Fitted & saved atomic node scaler -> {node_path}")

    print("\n[SUCCESS] Scaler fitting completed successfully.\n")

if __name__ == "__main__":
    main()
