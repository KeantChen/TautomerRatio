"""
================================================================================
Filename: tautomer_predictor.py
Author: Cheng Chen
Date file created: 2025-11-15
Most recent author to change the file: Cheng Chen
Date last modified: 2026-10-28
Description: Core inference engine for aqueous tautomeric free energy difference
             (Delta G_aq), equilibrium constants, and Boltzmann ratios using
             Hydra-PaiNN and GFN2-xTB with 3-Tier applicability domain triage.
================================================================================
Hydra-PaiNN: Physics-Informed Multi-Tower Delta-Learning and 3-Tier Domain Triage
================================================================================
A unified pipeline for predicting tautomeric free energy differences (ΔG_aq),
equilibrium constants (K_eq), Boltzmann population ratios, and applicability domain.

Supports:
  1. Fast 2D Topological Triage (<1 ms, zero quantum calculation)
  2. Mode "xtb_only": Standalone xTB GFN2 (ALPB water) + Tower-A ML Delta Correction
  3. Mode "three_towers": Full multi-tower evaluation (Tower-A xTB, Tower-B g-xTB, Tower-C Mixed Fusion)
"""

import os
import sys
import re
import math
import shutil
import tempfile
import subprocess
import numpy as np
import pandas as pd
try:
    import torch
    import torch.nn as nn
    from torch_geometric.utils import scatter
    TORCH_AVAILABLE = True
    _BaseModule = nn.Module
except ImportError:
    torch = None
    nn = None
    scatter = None
    TORCH_AVAILABLE = False
    _BaseModule = object

from rdkit import Chem
from rdkit.Chem import AllChem, rdMolDescriptors

os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

# ==============================================================================
# 0. Physical Constants & Default Feature Columns
# ==============================================================================
HARTREE_TO_KCAL = 627.509
R_GAS_KCAL = 1.98720425864083e-3  # kcal / (mol * K)

XTB_COLS = [
    "xtb_Gap_eV", "xtb_Dipole", "xtb_Gelec", "xtb_Gsasa", "xtb_Ghb",
    "xtb_iso_ES", "xtb_dispersion", "xtb_repulsion", "xtb_Mol_alpha",
    "xtb_alpha_max", "xtb_alpha_mean"
]
GXTB_COLS = [
    "gxtb_Gap_eV", "gxtb_IP", "gxtb_EA", "gxtb_Dipole",
    "gxtb_q_max", "gxtb_q_min", "gxtb_q_delta"
]

# Calibration factors fitted on SAMPL2 benchmark (y = k * x, Manuscript Table 2)
K_X = 0.575  # Tower A (xTB)
K_G = 0.576  # Tower B (g-xTB)
K_M = 0.577  # Tower C (Mixed Fusion)

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_MODEL_PATH = os.path.join(CURRENT_DIR, "models", "hydra_painn_best.pth")
DEFAULT_SCALER_DIR = os.path.join(CURRENT_DIR, "models", "scalers")


def resolve_xtb_bin(custom_path=None):
    """
    Auto-detect xTB executable across Windows, Linux, and macOS:
    1. Explicit custom argument
    2. Environment variable XTB_BIN or XTB_CMD
    3. Bundled binary in bin/xtb.exe (Windows) or bin/xtb (Linux)
    4. System PATH via shutil.which('xtb')
    """
    if custom_path:
        return custom_path

    env_cmd = os.environ.get("XTB_BIN") or os.environ.get("XTB_CMD")
    if env_cmd:
        return env_cmd

    # Check local bundled binary inside bin/
    local_bin = os.path.join(CURRENT_DIR, "bin", "xtb.exe" if sys.platform == "win32" else "xtb")
    if os.path.exists(local_bin):
        return local_bin

    # Check system PATH
    path_bin = shutil.which("xtb.exe" if sys.platform == "win32" else "xtb")
    if path_bin:
        return path_bin

    # Fallback to local path (will be checked before execution)
    return local_bin


# ==============================================================================
# 1. Neural Network Architecture (Hydra-PaiNN)
# ==============================================================================
def pure_pytorch_radius_graph(pos, r, batch):
    dist_mat = torch.cdist(pos, pos)
    batch_mask = batch.unsqueeze(0) == batch.unsqueeze(1)
    valid_mask = batch_mask & (dist_mat < r) & (dist_mat > 1e-5)
    row, col = valid_mask.nonzero(as_tuple=True)
    return torch.stack([row, col], dim=0)


class GaussianSmearing(_BaseModule):
    def __init__(self, start=0.0, stop=5.0, num_gaussians=50):
        super().__init__()
        offset = torch.linspace(start, stop, num_gaussians)
        self.coeff = -0.5 / (offset[1] - offset[0]).item() ** 2
        self.register_buffer('offset', offset)

    def forward(self, dist):
        dist = dist.view(-1, 1) - self.offset.view(1, -1)
        return torch.exp(self.coeff * torch.pow(dist, 2))


class PaiNNInteraction(_BaseModule):
    def __init__(self, hidden_channels, num_rbf):
        super().__init__()
        self.hidden_channels = hidden_channels
        self.mlp = nn.Sequential(
            nn.Linear(hidden_channels, hidden_channels),
            nn.SiLU(),
            nn.Linear(hidden_channels, 3 * hidden_channels)
        )
        self.filter_net = nn.Linear(num_rbf, 3 * hidden_channels)

    def forward(self, s, v, edge_index, edge_attr, edge_vec):
        j, i = edge_index
        W = self.filter_net(edge_attr)
        x = self.mlp(s[j]) * W

        x_vv, x_sv, x_ss = torch.split(x, self.hidden_channels, dim=-1)
        v_msg = x_vv.unsqueeze(1) * v[j] + x_sv.unsqueeze(1) * edge_vec.unsqueeze(2)
        s_msg = x_ss

        v_out = scatter(v_msg, i, dim=0, dim_size=s.size(0), reduce='sum')
        s_out = scatter(s_msg, i, dim=0, dim_size=s.size(0), reduce='sum')
        return s_out, v_out


class PaiNNUpdate(_BaseModule):
    def __init__(self, hidden_channels):
        super().__init__()
        self.vec_proj = nn.Linear(hidden_channels, hidden_channels * 2, bias=False)
        self.mlp = nn.Sequential(
            nn.Linear(hidden_channels * 2, hidden_channels),
            nn.SiLU(),
            nn.Linear(hidden_channels, hidden_channels * 3)
        )
        self.a = nn.Linear(hidden_channels, hidden_channels)

    def forward(self, s, v):
        v_proj = self.vec_proj(v)
        v_u, v_v = torch.split(v_proj, self.vec_proj.out_features // 2, dim=-1)
        v_v_norm = torch.norm(v_v, dim=1)

        mlp_out = self.mlp(torch.cat([s, v_v_norm], dim=-1))
        a_vv, a_sv, a_ss = torch.split(mlp_out, s.size(-1), dim=-1)

        v_out = v_u * a_vv.unsqueeze(1)
        s_v = torch.sum(self.a(v) * v_v, dim=1)
        s_out = s_v * a_sv + a_ss
        return s + s_out, v + v_out


class HydraPaiNN(_BaseModule):
    def __init__(self, hidden_channels=256, num_layers=3, num_rbf=50, cutoff=5.0,
                 num_xtb_feats=11, num_gxtb_feats=7, num_phys_features=3):
        super().__init__()
        self.hidden_channels = hidden_channels
        self.cutoff = cutoff
        self.atom_emb = nn.Embedding(100, hidden_channels)
        self.rbf = GaussianSmearing(0.0, cutoff, num_rbf)
        self.phys_proj = nn.Sequential(
            nn.Linear(hidden_channels + num_phys_features, hidden_channels),
            nn.SiLU(),
            nn.Linear(hidden_channels, hidden_channels)
        )
        self.interactions = nn.ModuleList([PaiNNInteraction(hidden_channels, num_rbf) for _ in range(num_layers)])
        self.updates = nn.ModuleList([PaiNNUpdate(hidden_channels) for _ in range(num_layers)])

        def build_head(in_dim):
            return nn.Sequential(
                nn.Linear(in_dim, hidden_channels // 2),
                nn.SiLU(),
                nn.Linear(hidden_channels // 2, hidden_channels // 4),
                nn.SiLU(),
                nn.Linear(hidden_channels // 4, 1)
            )

        self.head_xtb = build_head(hidden_channels + num_xtb_feats)
        self.head_gxtb = build_head(hidden_channels + num_gxtb_feats)
        self.head_mixed = build_head(hidden_channels + num_xtb_feats + num_gxtb_feats)

    def forward(self, z, pos, phys_node, f_xtb, f_gxtb, mask_xtb=None, mask_gxtb=None):
        batch_idx = torch.zeros(z.size(0), dtype=torch.long, device=z.device)
        bs = 1

        f_xtb = f_xtb.view(bs, -1)
        f_gxtb = f_gxtb.view(bs, -1)

        if mask_xtb is not None:
            f_xtb = f_xtb * mask_xtb
        if mask_gxtb is not None:
            f_gxtb = f_gxtb * mask_gxtb

        s = self.atom_emb(z)
        h_concat = torch.cat([s, phys_node], dim=-1)
        s = self.phys_proj(h_concat)
        v = torch.zeros((s.size(0), 3, self.hidden_channels), device=s.device)

        edge_index = pure_pytorch_radius_graph(pos, r=self.cutoff, batch=batch_idx)
        row, col = edge_index
        edge_vec = pos[row] - pos[col]
        edge_dist = torch.norm(edge_vec, dim=-1)
        edge_vec = edge_vec / (edge_dist.unsqueeze(-1) + 1e-8)
        edge_attr = self.rbf(edge_dist)

        for interaction, update in zip(self.interactions, self.updates):
            s_msg, v_msg = interaction(s, v, edge_index, edge_attr, edge_vec)
            s = s + s_msg
            v = v + v_msg
            s, v = update(s, v)

        graph_repr = s.sum(dim=0, keepdim=True)

        pred_xtb = self.head_xtb(torch.cat([graph_repr, f_xtb], dim=-1))
        pred_gxtb = self.head_gxtb(torch.cat([graph_repr, f_gxtb], dim=-1))
        pred_mixed = self.head_mixed(torch.cat([graph_repr, f_xtb, f_gxtb], dim=-1))

        return pred_xtb.squeeze(), pred_gxtb.squeeze(), pred_mixed.squeeze()


# ==============================================================================
# 2. Main Prediction Engine
# ==============================================================================
class TautomerPredictor:
    def __init__(self, model_path=DEFAULT_MODEL_PATH, scaler_dir=DEFAULT_SCALER_DIR,
                 xtb_bin=None, gxtb_cmd=None, device=None):
        if not TORCH_AVAILABLE:
            raise ImportError(
                "PyTorch / torch_geometric is not installed in your Python environment.\n"
                "To run full 3D neural network predictions (works on CPU without GPU), please install it via:\n"
                "    pip install torch torch_geometric\n"
                "(Note: You can still use the 2D topological triage with --triage_only without PyTorch!)"
            )

        self.device = device or ('cuda' if torch.cuda.is_available() else 'cpu')
        self.xtb_bin = resolve_xtb_bin(xtb_bin)
        self.gxtb_cmd = gxtb_cmd or self._detect_default_gxtb()

        # Load scalers
        if not os.path.exists(scaler_dir):
            raise FileNotFoundError(f"Scaler directory not found: {scaler_dir}")
        self.scaler_node = torch.load(os.path.join(scaler_dir, "scaler_node.pt"), map_location='cpu', weights_only=False)
        self.scaler_xtb = torch.load(os.path.join(scaler_dir, "scaler_global_xtb.pt"), map_location='cpu', weights_only=False)
        self.scaler_gxtb = torch.load(os.path.join(scaler_dir, "scaler_global_gxtb.pt"), map_location='cpu', weights_only=False)

        # Initialize neural network
        self.model = HydraPaiNN(
            hidden_channels=256, num_layers=3, num_rbf=50, cutoff=5.0,
            num_xtb_feats=len(XTB_COLS), num_gxtb_feats=len(GXTB_COLS), num_phys_features=3
        ).to(self.device)

        if os.path.exists(model_path):
            state_dict = torch.load(model_path, map_location=self.device)
            self.model.load_state_dict(state_dict)
            self.model.eval()
            print(f"[TautomerPredictor] Model weights loaded successfully on {self.device}")
        else:
            raise FileNotFoundError(f"Model checkpoint not found: {model_path}")

    @staticmethod
    def _detect_default_gxtb():
        """Auto-detect g-xTB binary path across platforms."""
        env_cmd = os.environ.get("GXTB_BIN") or os.environ.get("GXTB_CMD")
        if env_cmd:
            return env_cmd

        path_bin = shutil.which("gxtb") or shutil.which("gxtb.exe")
        if path_bin:
            return path_bin

        local_bin = os.path.join(CURRENT_DIR, "bin", "gxtb.exe" if sys.platform == "win32" else "gxtb")
        if os.path.exists(local_bin):
            return local_bin

        return None

    @staticmethod
    def generate_3d_coords(smiles, seed=42):
        """Generate 3D conformer using RDKit ETKDGv3 with MMFF pre-optimization."""
        mol = Chem.MolFromSmiles(smiles)
        if mol is None:
            raise ValueError(f"Invalid SMILES string: {smiles}")
        mol = Chem.AddHs(mol)

        params = AllChem.ETKDGv3()
        params.randomSeed = seed
        res = AllChem.EmbedMolecule(mol, params)
        if res != 0:
            AllChem.EmbedMolecule(mol, randomSeed=seed)

        try:
            AllChem.MMFFOptimizeMolecule(mol, maxIters=500)
        except Exception:
            pass

        conf = mol.GetConformer()
        symbols = [atom.GetSymbol() for atom in mol.GetAtoms()]
        z = [atom.GetAtomicNum() for atom in mol.GetAtoms()]
        pos = conf.GetPositions()
        return mol, symbols, np.array(z, dtype=int), np.array(pos, dtype=float)

    def calculate_xtb_properties(self, symbols, coords, solvent="water", optimize=False, hessian=False):
        """
        Execute xTB GFN2 calculation (gas/ALPB water) and extract electronic & solvation descriptors.
        """
        xtb_exec = self.xtb_bin
        if not os.path.exists(xtb_exec) and not shutil.which(xtb_exec):
            raise FileNotFoundError(
                f"xTB binary not found at '{xtb_exec}'. "
                f"Please install xTB (e.g. 'conda install -c conda-forge xtb'), "
                f"place it in 'bin/', or specify via --xtb_bin / XTB_BIN. "
                f"See bin/README_ENGINES.md for platform instructions."
            )

        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as td:
            xyz = os.path.join(td, 'mol.xyz')
            with open(xyz, 'w', encoding='utf-8') as f:
                f.write(f"{len(symbols)}\n\n")
                for s, (x, y, z) in zip(symbols, coords):
                    f.write(f"{s:<2} {x:12.6f} {y:12.6f} {z:12.6f}\n")

            current_xyz = "mol.xyz"

            # 1. Geometry Optimization if requested
            if optimize:
                cmd_opt = [xtb_exec, current_xyz, "--opt", "--gfn", "2", "--alpb", solvent]
                res_opt = subprocess.run(cmd_opt, cwd=td, capture_output=True, text=True, encoding='utf-8', errors='ignore')
                opt_xyz = os.path.join(td, "xtbopt.xyz")
                if os.path.exists(opt_xyz):
                    current_xyz = "xtbopt.xyz"

            # 2. Single Point or Hessian Frequency Analysis
            cmd_main = [xtb_exec, current_xyz, "--gfn", "2", "--alpb", solvent]
            if hessian:
                cmd_main.extend(["--hess", "--norestart"])

            res = subprocess.run(cmd_main, cwd=td, capture_output=True, text=True, encoding='utf-8', errors='ignore')
            content = res.stdout

            # Read final coordinates
            final_xyz_path = os.path.join(td, current_xyz)
            final_coords = []
            if os.path.exists(final_xyz_path):
                with open(final_xyz_path, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                    if len(lines) > 2:
                        for line in lines[2:]:
                            parts = line.split()
                            if len(parts) >= 4:
                                final_coords.append([float(parts[1]), float(parts[2]), float(parts[3])])
            if len(final_coords) != len(coords):
                final_coords = coords

            data = {}
            energies = re.findall(r'(?:::|TOTAL)\s+ENERGY\s+(-?\d+\.\d+)', content, re.IGNORECASE)
            data['xTB_E'] = float(energies[-1]) if energies else 0.0

            g_tot_m = re.findall(r'(?:TOTAL FREE ENERGY|Gibbs Free Energy)\s+(-?\d+\.\d+)', content, re.IGNORECASE)
            data['xtb_G_tot'] = float(g_tot_m[-1]) if g_tot_m else data['xTB_E']
            data['G_corr'] = data['xtb_G_tot'] - data['xTB_E']

            gaps = re.findall(r'HOMO-LUMO GAP\s+(-?\d+\.\d+)', content, re.IGNORECASE)
            data['xtb_Gap_eV'] = float(gaps[-1]) if gaps else 2.5

            dipoles = re.findall(r'full:\s+-?\d+\.\d+\s+-?\d+\.\d+\s+-?\d+\.\d+\s+(\d+\.\d+)', content)
            data['xtb_Dipole'] = float(dipoles[-1]) if dipoles else 2.0

            m = re.search(r'-> Gsolv\s+(-?\d+\.\d+)', content)
            data['xtb_Gsolv'] = float(m.group(1)) if m else 0.0

            for k in ['Gelec', 'Gsasa', 'Ghb']:
                m = re.search(fr'-> {k}\s+(-?\d+\.\d+)', content)
                data[f'xtb_{k}'] = float(m.group(1)) if m else 0.0

            m_es = re.search(r'-> isotropic ES\s+(-?\d+\.\d+)', content)
            m_disp = re.search(r'-> dispersion\s+(-?\d+\.\d+)', content)
            m_rep = re.search(r'repulsion energy\s+(-?\d+\.\d+)', content)
            data['xtb_iso_ES'] = float(m_es.group(1)) if m_es else 0.0
            data['xtb_dispersion'] = float(m_disp.group(1)) if m_disp else 0.0
            data['xtb_repulsion'] = float(m_rep.group(1)) if m_rep else 0.0

            m_alpha = re.search(r'Mol\.\s+α\(0\)\s+/au\s*:\s+(\d+\.\d+)', content)
            data['xtb_Mol_alpha'] = float(m_alpha.group(1)) if m_alpha else 50.0

            alpha_lines = re.findall(r'^\s+\d+\s+\d+\s+[A-Za-z]+\s+\d+\.\d+\s+-?\d+\.\d+\s+\d+\.\d+\s+(\d+\.\d+)', content, re.MULTILINE)
            if alpha_lines:
                alphas = [float(x) for x in alpha_lines]
                data['xtb_alpha_max'] = max(alphas)
                data['xtb_alpha_mean'] = float(np.mean(alphas))
            else:
                data['xtb_alpha_max'] = 10.0
                data['xtb_alpha_mean'] = 5.0

            node_features = []
            capture_flag = False
            for line in content.splitlines():
                if '#   Z          covCN         q      C6AA      α(0)' in line:
                    capture_flag = True
                    continue
                if capture_flag:
                    if line.strip() == '' or 'Mol.' in line:
                        capture_flag = False
                        continue
                    parts = line.split()
                    if len(parts) >= 7:
                        node_features.append([float(parts[3]), float(parts[4]), float(parts[6])])

            if len(node_features) != len(symbols):
                node_features = [[2.0, 0.0, 5.0] for _ in symbols]
            data['node_features'] = np.array(node_features, dtype=np.float32)
            data['global_xtb'] = np.array([data.get(c, 0.0) for c in XTB_COLS], dtype=np.float32)
            data['final_coords'] = np.array(final_coords, dtype=float)
            data['method'] = f"xTB 6.7.1 GFN2-xTB ({solvent})"
            return data

    def calculate_gxtb_properties(self, symbols, coords):
        """
        Execute g-xTB calculation (gas-phase single point) and extract electronic descriptors.
        """
        if not self.gxtb_cmd:
            raise RuntimeError("g-xTB command is not configured or not found. Please provide --gxtb_cmd or set GXTB_BIN.")

        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as td:
            xyz = os.path.join(td, 'mol.xyz')
            with open(xyz, 'w', encoding='utf-8') as f:
                f.write(f"{len(symbols)}\n\n")
                for s, (x, y, z) in zip(symbols, coords):
                    f.write(f"{s:<2} {x:12.6f} {y:12.6f} {z:12.6f}\n")

            if self.gxtb_cmd.startswith("wsl "):
                wsl_bin = self.gxtb_cmd[4:].strip()
                wsl_xyz = '/mnt/' + td[0].lower() + '/' + td[3:].replace('\\', '/') + '/mol.xyz'
                cmd = ["wsl", wsl_bin, wsl_xyz]
            else:
                cmd = [self.gxtb_cmd, "mol.xyz"]

            res = subprocess.run(cmd, cwd=td, capture_output=True, text=True, encoding='utf-8', errors='ignore')
            content = res.stdout

            data = {}
            m_gtot = re.search(r"total\s+(-?\d+\.\d+)", content)
            data['gxtb_E_total'] = float(m_gtot.group(1)) if m_gtot else 0.0

            m_gap = re.search(r"gap\s*\(eV\)\s*:\s*(\d+\.\d+)", content)
            data['gxtb_Gap_eV'] = float(m_gap.group(1)) if m_gap else 2.5

            m_ip = re.search(r"Janaks theorem for IP\s*:\s*(-?\d+\.\d+)", content)
            data['gxtb_IP'] = float(m_ip.group(1)) if m_ip else 0.0

            m_ea = re.search(r"Janaks theorem for EA\s*:\s*(-?\d+\.\d+)", content)
            data['gxtb_EA'] = float(m_ea.group(1)) if m_ea else 0.0

            m_gdip = re.findall(r"total\s+\(au/Debye\)\s*:\s*\d+\.\d+\s+(\d+\.\d+)", content)
            data['gxtb_Dipole'] = float(m_gdip[-1]) if m_gdip else 2.0

            charges = []
            for line in content.splitlines():
                m_ch = re.match(r"^##\s+\d+\s+[A-Za-z]+\s+\d+\.\d+\s+(\d+\.\d+)\s+(\d+\.\d+)", line)
                if m_ch:
                    charges.append(float(m_ch.group(1)) - float(m_ch.group(2)))
            if charges:
                data['gxtb_q_max'] = max(charges)
                data['gxtb_q_min'] = min(charges)
                data['gxtb_q_delta'] = max(charges) - min(charges)
            else:
                data['gxtb_q_max'], data['gxtb_q_min'], data['gxtb_q_delta'] = 0.5, -0.5, 1.0

            data['global_gxtb'] = np.array([data.get(c, 0.0) for c in GXTB_COLS], dtype=np.float32)
            data['method'] = "g-xTB gas electronic single point"
            return data

    @staticmethod
    def extract_cbh2_fingerprint(smiles):
        """Extract CBH-2 topological fingerprint (aromaticity, hybridizations, exact bond types)."""
        mol = Chem.MolFromSmiles(smiles)
        if mol is None:
            raise ValueError(f"Invalid SMILES: {smiles}")

        n_aro = sum(1 for atom in mol.GetAtoms() if atom.GetIsAromatic())
        n_arorings = rdMolDescriptors.CalcNumAromaticRings(mol)

        elem_hyb = {}
        for atom in mol.GetAtoms():
            if atom.GetAtomicNum() <= 1:
                continue
            sym = atom.GetSymbol()
            hyb = str(atom.GetHybridization())
            key = f"{sym}_{hyb}"
            elem_hyb[key] = elem_hyb.get(key, 0) + 1

        exact_bonds = {}
        for bond in mol.GetBonds():
            a1 = bond.GetBeginAtom()
            a2 = bond.GetEndAtom()
            if a1.GetAtomicNum() <= 1 or a2.GetAtomicNum() <= 1:
                continue
            sym1 = a1.GetSymbol()
            sym2 = a2.GetSymbol()
            pair_sym = "-".join(sorted([sym1, sym2]))
            b_type = str(bond.GetBondType())
            bond_key = f"{pair_sym}_{b_type}"
            exact_bonds[bond_key] = exact_bonds.get(bond_key, 0) + 1

        return {
            'n_aro': n_aro,
            'n_arorings': n_arorings,
            'elem_hyb': elem_hyb,
            'exact_bonds': exact_bonds
        }

    @classmethod
    def triage_check(cls, smiles_A, smiles_B):
        """
        Quantum-Topological Applicability Domain & 3-Tier Triage (<1 ms 2D evaluation).
        Partitions pairs into:
          - Comfort Zone (|ΔN_aro| = 0):
              ↳ CBH-Taut Subset (Tier 1)
              ↳ Normal Subset (Tier 2)
          - Risk Zone (|ΔN_aro| > 0, Tier 3)
        """
        fp_A = cls.extract_cbh2_fingerprint(smiles_A)
        fp_B = cls.extract_cbh2_fingerprint(smiles_B)

        n_aro_A = fp_A['n_aro']
        n_aro_B = fp_B['n_aro']
        delta_aro = abs(n_aro_A - n_aro_B)
        is_aromatic_conserved = (delta_aro == 0)
        min_arorings = min(fp_A['n_arorings'], fp_B['n_arorings'])

        all_hyb_keys = set(fp_A['elem_hyb'].keys()).union(set(fp_B['elem_hyb'].keys()))
        elem_hyb_diff = {k: abs(fp_A['elem_hyb'].get(k, 0) - fp_B['elem_hyb'].get(k, 0)) for k in all_hyb_keys}
        elem_hyb_conserved = all(v == 0 for v in elem_hyb_diff.values())

        all_bond_keys = set(fp_A['exact_bonds'].keys()).union(set(fp_B['exact_bonds'].keys()))
        exact_bond_diff = {k: abs(fp_A['exact_bonds'].get(k, 0) - fp_B['exact_bonds'].get(k, 0)) for k in all_bond_keys}
        exact_bonds_conserved = all(v == 0 for v in exact_bond_diff.values())

        strict_cbh2 = is_aromatic_conserved and elem_hyb_conserved and exact_bonds_conserved
        bond_diff_details = [f"{k}: Δ={v}" for k, v in exact_bond_diff.items() if v > 0]
        hyb_diff_details = [f"{k}: Δ={v}" for k, v in elem_hyb_diff.items() if v > 0]

        if not is_aromatic_conserved:
            status = "RISK_ZONE"
            domain = "Risk Zone"
            subset = "Risk Zone"
            tier = 3
            tier_name = "Tier 3 (Risk Zone)"
            expected_mae = 5.14
            confidence = "Expected MAE: 5.14 kcal/mol"
            message = (
                "[Tier 3 / Risk Zone]: Aromaticity transition (|ΔN_aro| > 0). "
                "TautoBase MAE = 5.14 kcal/mol (median 4.06 kcal/mol, RMSE = 6.73 kcal/mol); "
                "DFT-460 MAE = 4.38 kcal/mol (DFT reference MAE = 4.07 kcal/mol). (Update is coming soon)"
            )
        elif strict_cbh2:
            status = "COMFORT_ZONE"
            domain = "Comfort Zone"
            subset = "CBH-Taut Subset"
            tier = 1
            tier_name = "Tier 1 (CBH-Taut Subset)"
            expected_mae = 1.29
            confidence = "Expected MAE: 1.29 kcal/mol"
            message = (
                "[Tier 1 / CBH-Taut Subset]: Invariant heavy-atom hybridizations and bond-pair types (|ΔN_aro| = 0). "
                "TautoBase MAE = 1.29 kcal/mol (median 1.15 kcal/mol, RMSE = 1.76 kcal/mol); "
                "DFT-460 MAE = 1.38 kcal/mol."
            )
        else:
            status = "COMFORT_ZONE"
            domain = "Comfort Zone"
            subset = "Normal Subset"
            tier = 2
            tier_name = "Tier 2 (Normal Subset)"
            expected_mae = 1.97
            confidence = "Expected MAE: 1.97 kcal/mol"
            message = (
                "[Tier 2 / Normal Subset]: Aromaticity conserved (|ΔN_aro| = 0). "
                "TautoBase MAE = 1.97 kcal/mol (median 1.53 kcal/mol, RMSE = 2.56 kcal/mol); "
                "DFT-460 MAE = 1.78 kcal/mol."
            )

        return {
            'status': status,
            'domain': domain,
            'subset': subset,
            'tier': tier,
            'tier_name': tier_name,
            'expected_mae': expected_mae,
            'confidence': confidence,
            'strict_cbh2': strict_cbh2,
            'aromatic_rings': min_arorings,
            'aromatic_atoms_A': n_aro_A,
            'aromatic_atoms_B': n_aro_B,
            'delta_aro': delta_aro,
            'elem_hyb_conserved': elem_hyb_conserved,
            'exact_bonds_conserved': exact_bonds_conserved,
            'bond_diff_details': bond_diff_details,
            'hyb_diff_details': hyb_diff_details,
            'message': message
        }

    def predict(self, smiles_A, smiles_B, mode="xtb_only", temperature=298.15, solvent="water"):
        """
        Perform tautomer ratio & free energy prediction.

        Parameters:
            smiles_A (str): SMILES of tautomer A
            smiles_B (str): SMILES of tautomer B
            mode (str): "xtb_only" (fast, standalone Tower A) or "three_towers" (Towers A, B, and C)
            temperature (float): Kelvin (default: 298.15 K)
            solvent (str): Solvent environment for ALPB (default: "water")
        """
        # 1. 2D Topological Triage
        triage_info = self.triage_check(smiles_A, smiles_B)

        # 2. 3D Embedding
        mol_A, sym_A, z_A, coords_A = self.generate_3d_coords(smiles_A)
        mol_B, sym_B, z_B, coords_B = self.generate_3d_coords(smiles_B)

        do_opt = True
        res_xtb_A = self.calculate_xtb_properties(sym_A, coords_A, solvent=solvent, optimize=do_opt, hessian=do_opt)
        res_xtb_B = self.calculate_xtb_properties(sym_B, coords_B, solvent=solvent, optimize=do_opt, hessian=do_opt)

        has_gxtb = False
        res_gxtb_A = None
        res_gxtb_B = None

        if mode == "three_towers":
            if not self.gxtb_cmd:
                raise RuntimeError("Mode 'three_towers' requested, but g-xTB binary is not configured. Please specify --gxtb_cmd or set GXTB_BIN.")
            res_gxtb_A = self.calculate_gxtb_properties(sym_A, res_xtb_A['final_coords'])
            res_gxtb_B = self.calculate_gxtb_properties(sym_B, res_xtb_B['final_coords'])
            has_gxtb = True

        def prepare_tensors(z, pos, xtb_info, gxtb_info):
            z_t = torch.tensor(z, dtype=torch.long, device=self.device)
            pos_t = torch.tensor(pos, dtype=torch.float32, device=self.device)

            raw_node = torch.tensor(xtb_info['node_features'], dtype=torch.float32)
            norm_node = (raw_node - self.scaler_node['mean']) / self.scaler_node['std']
            norm_node = norm_node.to(self.device)

            raw_xtb = torch.tensor(xtb_info['global_xtb'], dtype=torch.float32)
            norm_xtb = (raw_xtb - self.scaler_xtb['mean']) / self.scaler_xtb['std']
            norm_xtb = norm_xtb.to(self.device).unsqueeze(0)

            if gxtb_info is not None:
                raw_gxtb = torch.tensor(gxtb_info['global_gxtb'], dtype=torch.float32)
                norm_gxtb = (raw_gxtb - self.scaler_gxtb['mean']) / self.scaler_gxtb['std']
                mask_g = torch.tensor([1.0], device=self.device)
            else:
                norm_gxtb = torch.zeros(len(GXTB_COLS), dtype=torch.float32)
                mask_g = torch.tensor([0.0], device=self.device)
            norm_gxtb = norm_gxtb.to(self.device).unsqueeze(0)

            return z_t, pos_t, norm_node, norm_xtb, norm_gxtb, mask_g

        zA, posA, nodeA, xtbA, gxtbA, mask_gA = prepare_tensors(z_A, res_xtb_A['final_coords'], res_xtb_A, res_gxtb_A)
        zB, posB, nodeB, xtbB, gxtbB, mask_gB = prepare_tensors(z_B, res_xtb_B['final_coords'], res_xtb_B, res_gxtb_B)

        with torch.no_grad():
            resA_x, resA_g, resA_m = self.model(zA, posA, nodeA, xtbA, gxtbA, mask_gxtb=mask_gA)
            resB_x, resB_g, resB_m = self.model(zB, posB, nodeB, xtbB, gxtbB, mask_gxtb=mask_gB)

            resA_x, resB_x = resA_x.item(), resB_x.item()
            resA_g, resB_g = resA_g.item(), resB_g.item()
            resA_m, resB_m = resA_m.item(), resB_m.item()

        def get_boltzmann_stats(dg):
            exponent = -dg / (R_GAS_KCAL * temperature)
            exponent = max(min(exponent, 50.0), -50.0)
            k_eq = math.exp(exponent)
            pop_A = 1.0 / (1.0 + k_eq) * 100.0
            pop_B = k_eq / (1.0 + k_eq) * 100.0

            if k_eq >= 1.0:
                major = "B"
                ratio_str = f"1 : {k_eq:.2f} (B-dominant)"
            else:
                major = "A"
                ratio_str = f"{1.0/k_eq:.2f} : 1 (A-dominant)"

            log10_k = -dg / (R_GAS_KCAL * temperature * math.log(10.0))
            return {
                'delta_G_kcal_mol': float(dg),
                'log10_K': float(log10_k),
                'K_eq': float(k_eq),
                'major_tautomer': major,
                'ratio': ratio_str,
                'population_pct': {'A': round(pop_A, 2), 'B': round(pop_B, 2)}
            }

        # Tower A (xTB-only): base = E_xtb + G_corr
        G_xtb_A = (res_xtb_A['xTB_E'] + res_xtb_A['G_corr']) * HARTREE_TO_KCAL + resA_x
        G_xtb_B = (res_xtb_B['xTB_E'] + res_xtb_B['G_corr']) * HARTREE_TO_KCAL + resB_x
        dG_raw_x = G_xtb_B - G_xtb_A
        dG_corr_x = dG_raw_x * K_X
        stats_x = get_boltzmann_stats(dG_corr_x)

        if has_gxtb:
            # Tower B & C: require g-xTB gas electronic energy + xTB G_corr + xTB G_solv
            G_gxtb_A = (res_gxtb_A['gxtb_E_total'] + res_xtb_A['G_corr'] + res_xtb_A['xtb_Gsolv']) * HARTREE_TO_KCAL + resA_g
            G_gxtb_B = (res_gxtb_B['gxtb_E_total'] + res_xtb_B['G_corr'] + res_xtb_B['xtb_Gsolv']) * HARTREE_TO_KCAL + resB_g
            dG_raw_g = G_gxtb_B - G_gxtb_A
            dG_corr_g = dG_raw_g * K_G
            stats_g = get_boltzmann_stats(dG_corr_g)

            G_mix_A = (res_gxtb_A['gxtb_E_total'] + res_xtb_A['G_corr'] + res_xtb_A['xtb_Gsolv']) * HARTREE_TO_KCAL + resA_m
            G_mix_B = (res_gxtb_B['gxtb_E_total'] + res_xtb_B['G_corr'] + res_xtb_B['xtb_Gsolv']) * HARTREE_TO_KCAL + resB_m
            dG_raw_m = G_mix_B - G_mix_A
            dG_corr_m = dG_raw_m * K_M
            stats_m = get_boltzmann_stats(dG_corr_m)

            recommended_prediction = stats_m
            recommended_tower = "Tower C (Mixed Fusion)"
        else:
            stats_g = {'status': 'Not Computed (Enabled in mode="three_towers")'}
            stats_m = {'status': 'Not Computed (Enabled in mode="three_towers")'}
            recommended_prediction = stats_x
            recommended_tower = "Tower A (xTB-only)"

        return {
            'inputs': {'SMILES_A': smiles_A, 'SMILES_B': smiles_B, 'temperature_K': temperature, 'solvent': solvent, 'mode': mode},
            'engine_info': {'xtb_backend': res_xtb_A['method'], 'gxtb_available': has_gxtb},
            'triage': triage_info,
            'tower_results': {
                'tower_A_xtb_only': stats_x,
                'tower_B_gxtb_only': stats_g,
                'tower_C_mixed_fusion': stats_m
            },
            'recommended_tower': recommended_tower,
            'recommended_prediction': recommended_prediction
        }

    @staticmethod
    def print_report(result):
        inputs = result['inputs']
        triage = result['triage']
        towers = result['tower_results']
        rec = result['recommended_prediction']
        rec_tower = result.get('recommended_tower', 'Recommended Prediction')

        print("\n" + "=" * 78)
        print("  [Hydra-PaiNN] Tautomer Free Energy & Ratio Prediction Report")
        print("=" * 78)
        print(f"  Tautomer A:   {inputs['SMILES_A']}")
        print(f"  Tautomer B:   {inputs['SMILES_B']}")
        print(f"  Mode:         {inputs['mode']} | Temperature: {inputs['temperature_K']} K (Solvent: {inputs['solvent']})")
        print(f"  Backend:      {result['engine_info']['xtb_backend']}")
        print("-" * 78)
        print(f"  [Triage Tier]:  {triage['tier_name']}")
        print(f"  [Domain]:       {triage['domain']} ({triage.get('subset', '')})")
        print(f"  [Expected MAE]: ~{triage['expected_mae']:.2f} kcal/mol  |  Confidence: {triage['confidence']}")
        print(f"  [Diagnostic]:   {triage['message']}")
        if triage.get('bond_diff_details'):
            print(f"  [Bond Shifts]:  {', '.join(triage['bond_diff_details'])}")
        print("-" * 78)
        print("  [Multi-Tower Predictions] (Calibrated Free Energy & Ratio):")

        ta = towers['tower_A_xtb_only']
        tag_a = " [RECOMMENDED]" if "Tower A" in rec_tower else ""
        print(f"  [1] Tower A (xTB-only){tag_a}:")
        print(f"      ΔG = {ta['delta_G_kcal_mol']:+.3f} kcal/mol | Ratio (A:B) = {ta['ratio']} | Pop: A {ta['population_pct']['A']}% / B {ta['population_pct']['B']}%")

        tb = towers['tower_B_gxtb_only']
        if 'delta_G_kcal_mol' in tb:
            print(f"  [2] Tower B (g-xTB):")
            print(f"      ΔG = {tb['delta_G_kcal_mol']:+.3f} kcal/mol | Ratio (A:B) = {tb['ratio']} | Pop: A {tb['population_pct']['A']}% / B {tb['population_pct']['B']}%")
        else:
            print(f"  [2] Tower B (g-xTB): {tb.get('status', 'Interface Reserved')}")

        tc = towers['tower_C_mixed_fusion']
        tag_c = " [RECOMMENDED]" if "Tower C" in rec_tower else ""
        if 'delta_G_kcal_mol' in tc:
            print(f"  [3] Tower C (Mixed Fusion){tag_c}:")
            print(f"      ΔG = {tc['delta_G_kcal_mol']:+.3f} kcal/mol | Ratio (A:B) = {tc['ratio']} | Pop: A {tc['population_pct']['A']}% / B {tc['population_pct']['B']}%")
        else:
            print(f"  [3] Tower C (Mixed Fusion): {tc.get('status', 'Interface Reserved')}")

        print("=" * 78)
        print(f"  FINAL PREDICTION ({rec_tower}): Predominant Tautomer is [{rec['major_tautomer']}], Equilibrium Ratio: {rec['ratio']}")
        print("=" * 78 + "\n")
