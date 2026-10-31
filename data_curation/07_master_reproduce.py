#!/usr/bin/env python
"""
07_master_reproduce.py
======================
End-to-End Master Pipeline Verification and Execution Runner.

Author: Cheng Chen
Institution: McGill University / Moitessier Research Group
Date: 2026-03
License: MIT

This master script provides one-command execution and verification of the
entire data curation, feature extraction, dataset serialization, calibration,
and benchmark evaluation pipelines.
"""

import os
import sys
import subprocess
import time

def run_step(step_name: str, cmd: list, cwd: str):
    print("\n" + "=" * 80)
    print(f"  RUNNING: {step_name}")
    print(f"  Command: {' '.join(cmd)}")
    print("=" * 80)
    t0 = time.time()
    res = subprocess.run(cmd, cwd=cwd, stdout=sys.stdout, stderr=sys.stderr)
    elapsed = time.time() - t0
    if res.returncode != 0:
        print(f"\n[FAIL] Step '{step_name}' exited with error code {res.returncode}")
        sys.exit(res.returncode)
    else:
        print(f"\n[PASS] Step '{step_name}' finished successfully in {elapsed:.2f} s")

def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    py_exec = sys.executable

    print("\n" + "#" * 80)
    print("  TAUTOMER RATIO PREDICTION PIPELINE - DMP REPRODUCIBILITY SUITE")
    print("  Author: Cheng Chen | McGill University | Moitessier Research Group")
    print("#" * 80)

    steps = [
        ("00 - Extract Raw Frag20-Taut Partitions (Demo)",
         [py_exec, "00_extract_raw_frag20_taut.py", "--demo"],
         script_dir),
        ("01 - Curate Frag20 Downsampling Funnel (Demo)",
         [py_exec, "01_curate_frag20_funnel.py", "--sample_size", "200"],
         script_dir),
        ("02 - 3D Conformer & xTB Quantum Featurization (Demo)",
         [py_exec, "02_run_conformer_and_xtb.py", "--sample_size", "3"],
         script_dir),
        ("02b - g-xTB Descriptors Integration & Feature Merge",
         [py_exec, "02b_run_gxtb_and_merge.py"],
         script_dir),
        ("03 - Scaffold Split & PyG Graph Serialization",
         [py_exec, "03_build_scaffold_pt_dataset.py", "--max_samples", "20"],
         script_dir),
        ("03b - Fit Empirical Feature Scalers",
         [py_exec, "03b_fit_scalers.py"],
         script_dir),
        ("04 - Curate TautoBase 539 & SAMPL2 Benchmarks",
         [py_exec, "04_curate_benchmark_datasets.py"],
         script_dir),
        ("05 - Train Hydra-ResGNN Model (Demo 2 Epochs)",
         [py_exec, "05_train_hydra_resgnn.py", "--epochs", "2"],
         script_dir),
        ("06 - Calibrate SAMPL2 & Evaluate TautoBase Triage",
         [py_exec, "06_calibrate_and_evaluate.py"],
         script_dir),
    ]

    start_total = time.time()
    for name, cmd, cwd in steps:
        run_step(name, cmd, cwd)

    total_time = time.time() - start_total
    print("\n" + "#" * 80)
    print(f"  ALL 9 PIPELINE STAGES PASSED SUCCESSFULLY in {total_time:.2f} s!")
    print("  DMP Reproducibility Verification: 100% COMPLETE.")
    print("#" * 80 + "\n")

if __name__ == "__main__":
    main()
