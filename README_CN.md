# Hydra-PaiNN: 物理驱动的多塔Δ学习与四级CBH-2拓扑分级水相互变异构体比例预测

> **Languages / 语言版本 / Langues** : [中文 (Chinese)](README_CN.md) | [English](README.md) | [Français (French)](README_FR.md)

Hydra-PaiNN 是一个开源的物理信息融合机器学习工作流，用于预测水相中互变异构体对的自由能差（**ΔG_aq**）、平衡常数（**K_eq**）以及玻尔兹曼布居分布。

$$
\Delta G_{\text{aq}} = -RT \ln K_{\text{eq}}, \quad K_{\text{eq}} = \frac{[\text{异构体 B}]}{[\text{异构体 A}]}
$$

本系统深度集成了三项核心技术：
1. **PaiNN 3D 等变神经网络消息传递**：捕捉连续、方向敏感的三维空间几何相互作用。
2. **半经验量子化学物理基线**：耦合 GFN2-xTB（ALPB 水相隐式溶剂化模型）及 g-xTB 电子结构描述符。
3. **基于连接性层次理论（CBH-Taut）的适用域拓扑诊断**：基于 Raghavachari 严格同合同（Homodesmotic）化学键平衡理论，在开展昂贵量子计算前毫秒级判定基线系统误差是否满足抵消条件，自动识别高风险芳香性破坏案例并路由至高精度 DFT。

---

## 核心特性

- **开箱即用（Out-of-the-Box）**：内含完整预训练权重（`hydra_painn_best.pth`）、特征归一化器以及预编译的 Windows xTB 6.7.1 执行文件。
- **双运行模式**：
  - `--mode xtb_only`（默认）：纯基于 GFN2-xTB（ALPB 水相）。在 Windows 与 Linux 环境下完全独立运行，无需外部商业软件。
  - `--mode three_towers`：当本地配置好 g-xTB 时，可同时运行三塔推断（塔 A: xTB, 塔 B: g-xTB, 塔 C: 混合融合）。
- **极速 2D 适用域诊断**（`--triage_only`，耗时 < 1 毫秒）：
  - **Tier 1 (Strict CBH-Taut 黄金域)**：|ΔN_aro| = 0，重原子键型与杂化状态 100% 严格对称守恒（TautoBase 实测 MAE = 1.29 kcal/mol，中位数 1.15 kcal/mol；Wieder DFT 集 MAE = 1.38 kcal/mol）。
  - **Tier 2 (刚性芳香骨架舒适域)**：|ΔN_aro| = 0，分子含芳香环（TautoBase 常规子集 MAE = 1.97 kcal/mol，中位数 1.53 kcal/mol，方向准确率 88.3%）。
  - **Tier 3 (柔性脂肪链舒适域)**：|ΔN_aro| = 0，分子不含芳香环（舒适区总体 MAE = 1.87 kcal/mol，中位数 1.44 kcal/mol）。
  - **Tier 4 (高风险物理崩溃域 / 论文 Tier 3)**：|ΔN_aro| > 0，芳香环发生崩塌或重构，破坏连续介质溶剂化抵消假设（TautoBase 实测 MAE = 5.14 kcal/mol，中位数 4.06 kcal/mol；Wieder 数据集 MAE = 4.38 kcal/mol vs. DFT 4.07 kcal/mol；建议直接路由至高阶 DFT 专家系统）。

---

## 安装说明

### 1. 克隆仓库并配置 Python 环境
```bash
git clone https://github.com/KeantChen/TautomerRatio.git
cd TautomerRatio

# 使用 conda 创建虚拟环境
conda env create -f environment.yml
conda activate hydra_painn
```

或者使用 `pip` 安装依赖：
```bash
pip install -r requirements.txt
```

### 2. 验证安装环境
运行自动化自检脚本，验证核心依赖、模型权重以及量子引擎：
```bash
python verify_installation.py
```

---

## 快速上手

### 1. 极速 2D 拓扑分级诊断（< 1 ms，零量子计算）
在进行任何耗时的量子计算前，先行检查适用域与预期误差范围：
```bash
python predict.py --smi1 "OC1=CC=CC=N1" --smi2 "O=C1NC=CC=C1" --triage_only
```

### 2. 标准模式预测（单塔 xTB 独立运行）
预测水相自由能差、平衡常数及主导异构体：
```bash
python predict.py --smi1 "OC1=CC=CC=N1" --smi2 "O=C1NC=CC=C1" --mode xtb_only
```

### 3. 多塔融合预测（塔 A + 塔 B + 塔 C）
如果系统已配置 g-xTB 引擎（详见 [bin/README_ENGINES.md](bin/README_ENGINES.md)）：
```bash
python predict.py --smi1 "OC1=CC=CC=N1" --smi2 "O=C1NC=CC=C1" --mode three_towers
```

### 4. 批量 CSV 预测
批量评估用户数据集：
```bash
python predict.py --input examples/test_cases.csv --output predictions.csv --mode xtb_only
```

---

## Python API 调用示例

```python
from tautomer_predictor import TautomerPredictor

# 1. 初始化预测器（自动加载模型权重与归一化参数）
predictor = TautomerPredictor()

# 2. 极速 2D 拓扑诊断
triage = predictor.triage_check("OC1=CC=CC=N1", "O=C1NC=CC=C1")
print(f"层级: {triage['tier_name']} | 预期 MAE: {triage['expected_mae']} kcal/mol")

# 3. 完整 3D 几何构型 + 量子化学 + 神经网络预测
result = predictor.predict(
    smiles_A="OC1=CC=CC=N1",
    smiles_B="O=C1NC=CC=C1",
    mode="xtb_only",       # 或 "three_towers"
    temperature=298.15,    # 开尔文温度
    solvent="water"        # ALPB 水相溶剂
)

# 打印格式化预测报告
predictor.print_report(result)
```

---

## 实验与基准测试结果核对

所有指标均严格对齐发表论文最终稿（`Manuscipt-1021.docx`）与补充材料（`SI-1021.docx`）中的统计结果：

### 1. 水相真实实验基准评估 (TautoBase 与 SAMPL2)

#### A. TautoBase-539 全盲测数据集适用域分层评估 (论文 Table 3, Table 5 与 SI Table S7)

| 适用域子集划分 | 样本量 (N) | 占比 (%) | Hydra-PaiNN Tower C MAE | 中位数误差 | RMSE | 方向准确率 (%) | 玻尔兹曼误差因子 e^(MAE/RT) | 误差 ≤ 1 kcal/mol 比例 (%) |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **CBH-Taut 黄金域** (|ΔN_aro| = 0, 键型与杂化完全守恒) | 61 | 11.3% | **1.29 kcal/mol** (Tower A: 1.31) | 1.15 kcal/mol | 1.76 kcal/mol | 83.6% | 8.9 | 47.5% |
| **常规子集** (|ΔN_aro| = 0, 局域键型重排) | 367 | 68.1% | **1.97 kcal/mol** (Tower A: 1.97) | 1.53 kcal/mol | 2.56 kcal/mol | 88.3% | 28.1 | 31.9% |
| ├─ 普遍键型重组子集 | 355 | 65.9% | **1.95 kcal/mol** | 1.52 kcal/mol | 2.51 kcal/mol | 87.9% | 26.7 | 32.7% |
| └─ 交换键控制组 (酰胺–亚胺) | 12 | 2.2% | **2.67 kcal/mol** | 2.48 kcal/mol | 3.08 kcal/mol | 100.0% | 90.8 | 8.3% |
| **舒适区综合** (|ΔN_aro| = 0) | 428 | 79.4% | **1.87 kcal/mol** (Tower A: 1.88) | 1.44 kcal/mol | 2.46 kcal/mol | 87.6% | 24.5 | 34.1% |
| **高风险区** (|ΔN_aro| > 0, 芳香性发生转移破坏) | 111 | 20.6% | **5.14 kcal/mol** (Tower A: 5.12) | 4.06 kcal/mol | 6.73 kcal/mol | 72.1% | 6806.0 | 11.7% |
| **TautoBase 全盲测数据集** | 539 | 100.0% | **2.55 kcal/mol** (Tower A: 2.55) | 1.75 kcal/mol | 3.76 kcal/mol | 84.4% | 73.6 | 29.5% |

*全数据集整体基线方法对比 (论文 Table 3)*:
- **原始 GFN2-xTB**: 原始 MAE = 3.67 kcal/mol, 线性校正后 MAE = 3.69 kcal/mol, 方向准确率 = 66.5%
- **原始 g-xTB**: 原始 MAE = 2.93 kcal/mol, 线性校正后 MAE = 2.78 kcal/mol, 方向准确率 = 82.5%
- **Hydra-PaiNN Tower A**: 校正后 MAE = **2.55 kcal/mol** (原始 MAE = 4.28 kcal/mol), 方向准确率 = **84.6%**
- **Hydra-PaiNN Tower B**: 校正后 MAE = **2.55 kcal/mol** (原始 MAE = 4.34 kcal/mol), 方向准确率 = **84.8%**
- **Hydra-PaiNN Tower C**: 校正后 MAE = **2.55 kcal/mol** (原始 MAE = 4.35 kcal/mol), 方向准确率 = **84.4%**

#### B. 对称化 SAMPL2 盲测标定集 (论文 Table 2, N = 28)

| 模型分支 | 势能面曲率因子 (k) | Pearson R | 原始 MAE | 校正后 MAE | 校正后 RMSE | 方向准确率 (%) |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Tower A (xTB-only 独立模式)** | 0.575 | 0.88 | 2.94 kcal/mol | **1.81 kcal/mol** | 2.22 kcal/mol | 78.6% |
| **Tower B (g-xTB 模式)** | 0.576 | 0.88 | 2.86 kcal/mol | **1.81 kcal/mol** | 2.20 kcal/mol | 85.7% |
| **Tower C (多物理量混合融合)** | 0.577 | 0.88 | 2.89 kcal/mol | **1.81 kcal/mol** | 2.19 kcal/mol | 78.6% |

*在 SAMPL2 包含的 12 对芳香性守恒分子对上，Hydra-PaiNN 平均绝对偏差仅为 **0.49 kcal/mol**，稳固进入 < 1.0 kcal/mol 的严苛化学精度区间。*

---

### 2. Wieder et al. 460 对数据集成对严格对比 (论文 Table 4, Table 5 与 SI Table S8)

在 Wieder 等人（*Chem. Sci.* 2021）采用高阶多构象系综 DFT（B3LYP/aug-cc-pVTZ//B3LYP/6-31G(d)/SMD）完全评估的 460 对同源互变异构体测试集上：

| 适用域分层子集 | 样本量 (N) | 零基准 MAE | Wieder 多构象 DFT (MAE / RMSE / 中位数) | Hydra-PaiNN Tower A (MAE / RMSE / 中位数) | Hydra-PaiNN Tower C (MAE / RMSE / 中位数) |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **460 对全基准数据集** | 460 (100.0%) | 4.33 kcal/mol | 2.20 / 3.07 / 1.61 kcal/mol | 2.22 / 3.20 / 1.66 kcal/mol | **2.21 / 3.23 / 1.64 kcal/mol** |
| **舒适区综合** (|ΔN_aro| = 0) | 378 (82.2%) | 4.62 kcal/mol | 1.79 / 2.39 / 1.38 kcal/mol | 1.75 / 2.22 / 1.54 kcal/mol | **1.73 / 2.24 / 1.42 kcal/mol** |
| ├─ **CBH-Taut 黄金域** | 48 (10.4%) | 2.36 kcal/mol | 1.56 / 2.16 / 1.20 kcal/mol | 1.42 / 1.89 / 1.25 kcal/mol | **1.38 / 1.86 / 1.27 kcal/mol** |
| └─ **常规子集** | 330 (71.7%) | 4.95 kcal/mol | 1.82 / 2.43 / 1.42 kcal/mol | 1.80 / 2.26 / 1.59 kcal/mol | **1.78 / 2.29 / 1.44 kcal/mol** |
| **高风险区** (|ΔN_aro| > 0) | 82 (17.8%) | 3.00 kcal/mol | 4.07 / 5.14 / 3.50 kcal/mol | 4.36 / 5.91 / 3.45 kcal/mol | **4.38 / 5.95 / 3.50 kcal/mol** |

> **关键物理化学机理启示**：即使是消耗巨大算力的高阶多构象 DFT 方法，在高风险区的误差也骤升至 4.07 kcal/mol，而在 CBH-Taut 黄金域则收敛至 1.56 kcal/mol。这充分证实芳香性破坏导致的电子重排是**所有当代量子化学理论与连续介质溶剂化模型的共性物理瓶颈**，而非机器学习的偶然拟合缺陷。Hydra-PaiNN 提出的 2D CBH-Taut 适用域分级能在小于 1 毫秒内前置诊断并成功拦截该风险。

---

### 3. 文献外部基准对比评估 (论文 Table 4)

| 文献测试基准子集 | 样本量 (N) | 对比方法 / 模型 | MAE (kcal/mol) | RMSE (kcal/mol) |
| :--- | :--- | :--- | :--- | :--- |
| **DFT Subset** | 460 | B3LYP/aug-cc-pVTZ//B3LYP/6-31G(d)/SMD | 2.20 | 3.07 |
| | 460 | **Hydra-PaiNN: Tower C** | **2.21** | **3.23** |
| **MolTaut Subset** | 460 | MolTaut (*J. Chem. Inf. Model.* 2024) | 2.39 | 3.15 |
| | 460 | ωB97X/6-31G* // M06-2X/6-31G*/SMD | 2.50 | 3.46 |
| | 460 | **Hydra-PaiNN: Tower C** | **2.26** | **2.98** |
| **sPhysNet Subset** | 100 | sPhysNet-Pre (迁移前零样本) | 4.33 | 6.30 |
| | 100 | sPhysNet-FF (在真实实验 ΔG 上微调) | 1.16 | 1.93 |
| | 100 | MolTaut | 2.61 | 3.64 |
| | 100 | **Hydra-PaiNN: Tower C (纯理论零样本迁移)** | **2.41** | **3.32** |

---

### 4. 微观电子能残差学习评估 (Frag20-Taut 独立测试集, 论文 Table 1 与 SI Table S5)

模型预训练基于 Frag20-Taut 数据库，拟合目标为 **B3LYP/6-31G*/SMD** 理论级别下的水相单分子微观单点电子能残差：

| 预测塔分支 | 物理特征输入 | 测试集 MAE (kcal/mol) | 测试集 RMSE (kcal/mol) | 决定系数 R² |
| :--- | :--- | :--- | :--- | :--- |
| **Tower-A** | xTB | **1.33 ± 0.02** | 2.09 ± 0.04 | 0.97 ± 0.001 |
| **Tower-B** | g-xTB | **1.28 ± 0.01** | 1.99 ± 0.07 | 0.97 ± 0.002 |
| **Tower-C** | 混合融合特征 | **1.28 ± 0.01** | 1.95 ± 0.05 | 0.97 ± 0.002 |

*测试集包含通过互变异构体家族锁（Tautomer Group-Locking）完全物理隔离的 2,026 个独立罕见骨架图分子。*

---

## 目录结构说明

```text
TautomerRatio/
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
├── verify_installation.py          # 自动化验证与自检脚本
├── environment.yml                 # Conda 环境文件
├── requirements.txt                # pip 依赖文件
├── LICENSE                         # MIT 开源协议
└── README.md                       # 说明文档
```

---

## 开源协议

本项目基于 [MIT License](LICENSE) 开源。
量子化学计算引擎（xTB, g-xTB）分别遵循其各自的开源许可协议（LGPL-3.0 / GPL）。
