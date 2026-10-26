# Hydra-PaiNN: 物理启发多塔残差学习与 4-Tier CBH-2 适用域分层预测工具

> **语言版本 / Languages / Langues** : [中文 (Chinese)](README_CN.md) | [English](README.md) | [Français (French)](README_FR.md)

Hydra-PaiNN 是一个用于水溶液中互变异构体自由能差（$\Delta G_{\text{aq}}$）、平衡常数（$K_{\text{eq}}$）与玻尔兹曼布居分布预测的开源物理启发机器学习框架。

本项目包含三大核心组件：
1. **PaiNN 等变几何消息传递网络**：提取具有方向感知的 3D 几何连续表征。
2. **半经验量子化学辅助特征**：耦合 GFN2-xTB（ALPB 水隐式溶剂化模型）与 g-xTB 的电子结构物理描述符。
3. **4-Tier 量子拓扑 CBH-2 适用域分层检测器**：基于 2D SMILES 图的快速筛查模块，在进行高耗时量子计算前判定其是否满足 Raghavachari 等键/等化学键条件（CBH-2 误差对消原理），并对破坏芳香性的高风险分子进行分流。

---

## 核心特性

- **开箱即用**：自带训练完成的神经网络权重（`hydra_painn_best.pth`）、特征归一化器（scalers）以及 Windows 预编译 xTB 6.7.1 二进制程序。
- **双工作模式支持**：
  - `--mode xtb_only`（默认）：仅依赖单机 GFN2-xTB，无需配置 WSL 或 Linux 环境，Windows / Linux 均可即开即用。
  - `--mode three_towers`：同时激活三塔输出（Tower A: xTB, Tower B: g-xTB, Tower C: 混合特征融合），并默认推荐 Tower C 结果。
- **瞬时 2D 拓扑分层（< 1 ms）**（`--triage_only`）：根据拓扑特征将分子划分为 4 个置信度层级：
  - **Tier 1 (Strict CBH-2 黄金域)**：$\Delta N_{\text{aro}} = 0$ 且原子杂化方式与具体化学键种类完全守恒（基准评估 MAE ~ 1.30 kcal/mol，中位数 0.99 kcal/mol）。
  - **Tier 2 (刚性芳香骨架舒适域)**：$\Delta N_{\text{aro}} = 0$ 且具备刚性芳香环（基准评估 MAE ~ 1.81 kcal/mol）。
  - **Tier 3 (柔性脂肪链舒适域)**：$\Delta N_{\text{aro}} = 0$ 但不含芳香环（基准评估 MAE ~ 2.64 kcal/mol，提示构象熵效应）。
  - **Tier 4 (芳香性破坏高风险域)**：$\Delta N_{\text{aro}} > 0$。共振能量不对称导致连续介质溶剂化模型系统误差放大（基准评估 MAE ~ 5.25 kcal/mol，建议直接分流至高精度 DFT 专家系统）。

---

## 环境安装与配置

### 1. 克隆仓库并创建环境
```bash
git clone https://github.com/your-username/Hydra-PaiNN.git
cd Hydra-PaiNN

# 使用 Conda 环境文件安装
conda env create -f environment.yml
conda activate hydra_painn
```

或使用 `pip` 安装依赖：
```bash
pip install -r requirements.txt
```

### 2. 运行一键自检脚本
运行内置的自检脚本，自动验证环境依赖、预训练权重及量子引擎：
```bash
python verify_installation.py
```

---

## 快速使用说明

### 1. 快速 2D 拓扑适用域分层（< 1 ms，无量子计算）
```bash
python predict.py --smi1 "OC1=CC=CC=N1" --smi2 "O=C1NC=CC=C1" --triage_only
```

### 2. 标准单对预测（Mode: xtb_only，即开即用）
```bash
python predict.py --smi1 "OC1=CC=CC=N1" --smi2 "O=C1NC=CC=C1" --mode xtb_only
```

### 3. 多塔全输出预测（Mode: three_towers）
若已在 WSL 或 Linux 中配置 g-xTB（详见 [bin/README_ENGINES.md](bin/README_ENGINES.md)）：
```bash
python predict.py --smi1 "OC1=CC=CC=N1" --smi2 "O=C1NC=CC=C1" --mode three_towers
```

### 4. 批量 CSV 预测
```bash
python predict.py --input examples/test_cases.csv --output predictions.csv --mode xtb_only
```

---

## Python API 调用示例

```python
from tautomer_predictor import TautomerPredictor

# 1. 初始化预测器（自动加载模型权重与特征归一化器）
predictor = TautomerPredictor()

# 2. 快速 2D 分层
triage = predictor.triage_check("OC1=CC=CC=N1", "O=C1NC=CC=C1")
print(f"层级: {triage['tier_name']} | 预期 MAE: {triage['expected_mae']} kcal/mol")

# 3. 完整 3D 量子 + ML 预测
result = predictor.predict(
    smiles_A="OC1=CC=CC=N1",
    smiles_B="O=C1NC=CC=C1",
    mode="xtb_only",       # 或 "three_towers"
    temperature=298.15,    # 开尔文温度
    solvent="water"        # ALPB 溶剂化环境
)

# 打印格式化报告
predictor.print_report(result)
```

---

## 实验与基准测试结果核对

### 1. 水相实验基准评估
| 评估基准数据集 | 子集 / 适用域划分 | 样本量 ($N$) | Hydra-PaiNN Tower A | Hydra-PaiNN Tower C | 文献/物理基线 |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **TautoBase 基准集** | 舒适区（Comfort Zone, $\Delta N_{\text{aro}}=0$） | 428 | MAE = 1.94 kcal/mol | MAE = 1.95 kcal/mol | GFN2+k: 2.78 kcal/mol |
| *(真实实验 $\Delta G_{\text{exp}}$)* | Strict CBH-2 黄金域 | 61 | MAE = 1.35 kcal/mol | MAE = 1.30 kcal/mol | 中位数 = 0.99 kcal/mol |
| | 风险区（Risk Zone, $\Delta N_{\text{aro}}>0$） | 111 | MAE = 5.04 kcal/mol | MAE = 5.02 kcal/mol | 误差对消失效 |
| **Wieder et al. 数据集** | 460 对完整重合集 | 460 | MAE = 1.85 kcal/mol | MAE = 1.85 kcal/mol | 多构象 DFT: 1.99 kcal/mol |
| *(真实实验 $\Delta G_{\text{exp}}$)* | CBH-Taut 子集 | 48 | MAE = 1.16 kcal/mol | MAE = 1.13 kcal/mol | 多构象 DFT: 1.40 kcal/mol |
| | 风险区子集 | 82 | MAE = 3.07 kcal/mol | MAE = 3.15 kcal/mol | 多构象 DFT: 3.53 kcal/mol |
| **SAMPL2 标定集** | 中性水相实验集 | 28 条记录 | MAE = 0.65 kcal/mol | MAE = 0.65 kcal/mol | 原始 GFN2: 1.34 kcal/mol |

*所有真实实验自由能预测均包含基于 SAMPL2 确定的势能面曲率校正系数（$k_A = 0.568$, $k_C = 0.571$）。*

### 2. 关于理论训练集（Frag20-Taut Holdout）的说明
本模型预训练时使用的是来自文献 19（Frag20-Taut）的理论计算互变异构体分子对。**这部分不是真实实验数据**，而是高斯软件在 B3LYP/6-31G*/SMD 理论层级下计算的水相微观单点电子能残差。在包含 2,026 张孤儿/罕见骨架图的独立测试集上，Hydra-PaiNN 相对 B3LYP/SMD 理论参考值的电子能残差预测 MAE 为 0.32 kcal/mol（Tower A）和 0.31 kcal/mol（Tower C），用于检验神经网络是否成功拟合了目标量子力学残差。

---

## 目录结构说明

```
Hydra-PaiNN_Release/
├── bin/
│   ├── xtb.exe                     # 预编译 Windows xTB 6.7.1 可执行程序
│   ├── libiomp5md.dll              # Intel OpenMP 运行库
│   └── README_ENGINES.md           # Linux 与 WSL 量子引擎配置指南
├── models/
│   ├── hydra_painn_best.pth        # 训练完毕的 PyTorch 模型权重 (Seed 42)
│   └── scalers/                    # 特征标准化归一化器文件
├── examples/
│   ├── test_cases.csv              # 跨越 4 个层级的校验分子对
│   └── test_predictions.csv        # 示例执行结果输出
├── tautomer_predictor.py           # 核心预测引擎代码
├── predict.py                      # 命令行交互工具 (CLI)
├── verify_installation.py          # 自动化环境与功能自检脚本
├── environment.yml                 # Conda 环境依赖配置
├── requirements.txt                # pip 依赖配置
├── LICENSE                         # MIT 开源协议
└── README.md                       # 说明文档
```

---

## 开源协议

本项目代码基于 [MIT License](LICENSE) 开源。
所调用的半经验量子化学程序（xTB、g-xTB）分别遵循其各自的开源协议（LGPL-3.0 / GPL）。
