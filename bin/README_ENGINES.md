# Quantum Chemistry Engines Setup Guide

Hydra-PaiNN relies on semi-empirical quantum chemical calculations (GFN2-xTB) to compute physical electronic and implicit solvation descriptors.

---

## 1. GFN2-xTB Setup (Required for `--mode xtb_only` and `--mode three_towers`)

### Windows
- **Included Out-of-the-Box**: The `bin/` folder already includes a pre-compiled, optimized Windows binary:
  - `bin/xtb.exe` (xTB 6.7.1)
  - `bin/libiomp5md.dll` (Intel OpenMP runtime)
- **Action Required**: None. Windows users can run `python predict.py` directly without any additional setup.

### Linux
- **Option A (Recommended - One-line via Conda)**:
  ```bash
  conda install -c conda-forge xtb
  ```
  The pipeline will automatically detect `xtb` in your system `PATH`.
- **Option B (Official Precompiled Binaries)**:
  Download the latest Linux release from [Grimme-Lab GitHub Releases](https://github.com/grimme-lab/xtb/releases):
  ```bash
  # Example:
  tar -xf xtb-*-linux-x86_64.tar.xz
  # Either add xtb/bin to your PATH:
  export PATH="/path/to/xtb/bin:$PATH"
  # Or copy the xtb binary directly into this bin/ folder:
  cp /path/to/xtb/bin/xtb ./bin/xtb
  ```

### macOS
- Install via Conda:
  ```bash
  conda install -c conda-forge xtb
  ```

### Verification & Detection Priority
The predictor resolves the xTB executable in the following order:
1. Explicit CLI argument: `--xtb_bin /path/to/xtb`
2. Environment variable: `XTB_BIN`
3. Local bundled binary: `bin/xtb.exe` (Windows) or `bin/xtb` (Linux/macOS)
4. System PATH: `shutil.which("xtb")`

---

## 2. g-xTB Setup (Optional, only for `--mode three_towers`)

The default and recommended operating mode is `--mode xtb_only` (Tower A), which does **not** require g-xTB.

If you wish to run the full multi-tower architecture (`--mode three_towers`), configure g-xTB as follows:
- **Linux**:
  Install or compile g-xTB, then either:
  ```bash
  export GXTB_BIN="/path/to/gxtb"
  ```
  or pass the flag:
  ```bash
  python predict.py --smi1 "..." --smi2 "..." --mode three_towers --gxtb_cmd "/path/to/gxtb"
  ```
- **Windows (via WSL)**:
  If g-xTB is compiled inside WSL (Windows Subsystem for Linux), specify the WSL invocation command:
  ```bash
  python predict.py --smi1 "..." --smi2 "..." --mode three_towers --gxtb_cmd "wsl /home/user/gxtb/gxtb"
  ```
