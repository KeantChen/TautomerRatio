# Hydra-PaiNN: 物理驱动的多塔Δ学习与四级CBH-2拓扑分级水相互变异构体比例预测

> **Languages / 语言版本 / Langues** : [中文 (Chinese)](README_CN.md) | [English](README.md) | [Français (French)](README_FR.md)

Hydra-PaiNN 是一个开源的物理信息融合机器学习工作流，用于预测水相中互变异构体对的自由能差（**ΔG_aq**）、平衡常数（**K_eq**）以及玻尔兹曼布居分布。

$$
\Delta G_{\text{aq}} = -RT \ln K_{\text{eq}}, \quad K_{\text{eq}} = \frac{[\text{异构体 B}]}{[\text{异构体 A}]}
$$

本系统深度集成了三项核心技术：
1. **PaiNN 3D 等变神经网络消息传递**：捕捉连续、方向敏感的三维空间几何相互作用。
2. **半经验量子化学物理基线**：耦合 GFN2-xTB（ALPB 水相隐式溶剂化模型）及 g-xTB 电子结构描述符。
3. **4 级量子拓扑 CBH-2 适用域诊断**：基于 Raghavachari 严格同合同（Homodesmotic）化学键平衡理论，在开展昂贵量子计算前毫秒级判定误差是否满足抵消条件，自动识别高风险芳香性破坏案例并路由至高精度 DFT。

---

## 核心特性

- **开箱即用（Out-of-the-Box）**：内含完整预训练权重（`hydra_painn_best.pth`）、特征归一化器以及预编译的 Windows xTB 6.7.1 执行文件。
- **双运行模式**：
  - `--mode xtb_only`（默认）：纯基于 GFN2-xTB（ALPB 水相）。在 Windows 与 Linux 环境下完全独立运行，无需外部商业软件。
  - `--mode three_towers`：当本地配置好 g-xTB 时，可同时运行三塔推断（塔 A: xTB, 塔 B: g-xTB, 塔 C: 混合融合）。
- **极速 2D 适用域诊断**（`--triage_only`，耗时 < 1 毫秒）：
  - **Tier 1 (Strict CBH-2 黄金域)**：|ΔN_aro| = 0，重原子键型与杂化状态 100% 严格对称守恒（实测 MAE = 1.29 kcal/mol，中位数 1.15 kcal/mol）。
  - **Tier 2 (刚性芳香骨架舒适域)**：|ΔN_aro| = 0，位于刚性芳香骨架上（实测 MAE ~ 1.81 kcal/mol）。
  - **Tier 3 (柔性脂肪链舒适域)**：|ΔN_aro| = 0，但分子不含芳香环（实测 MAE ~ 2.64 kcal/mol）。
  - **Tier 4 (高风险物理崩溃域)**：|ΔN_aro| > 0，芳香环发生崩塌或重构，破坏连续介质溶剂化抵消假设（实测 MAE = 5.14 kcal/mol，建议直接路由至高阶 DFT 专家系统）。

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

### 1. 水相真实实验基准评估
所有指标均严格对齐发表论文正文与补充材料中对真实实验数据集的盲测统计结果：

| 评估基准数据集 | 子集 / 适用域划分 | 样本量 (*N*) | Hydra-PaiNN (Tower C) | 文献/物理对比基线 | 指标详情与统计 |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **TautoBase-539 基准集** | **全盲测数据集** | 539 (100%) | **MAE = 2.55 kcal/mol** | 原始 GFN2: 3.67 kcal/mol | RMSE = 3.76, 方向准确率 = 84.8% |
| *(真实实验 ΔG_exp)* | **舒适区综合** (|ΔN_aro| = 0) | 428 (79.4%) | **MAE = 1.87 kcal/mol** | GFN2+k 校正: 2.78 kcal/mol | 中位数 = 1.44, RMSE = 2.46, 准确率 = 87.9% |
| | ├─ CBH-Taut 黄金域 | 61 (11.3%) | **MAE = 1.29 kcal/mol** | 化学精度目标区间 | 中位数 = 1.15, RMSE = 1.76, 准确率 = 83.6% |
| | └─ 常规舒适区子集 | 367 (68.1%) | **MAE = 1.97 kcal/mol** | 工业高通量筛选舒适区 | 中位数 = 1.52, RMSE = 2.56, 准确率 = 88.6% |
| | **高风险区** (|ΔN_aro| > 0) | 111 (20.6%) | **MAE = 5.14 kcal/mol** | 物理中毒崩溃区 | 中位数 = 4.04, RMSE = 6.73 (建议直接路由 DFT) |
| **Wieder et al. 数据集** | **460 对完全对齐基准** | 460 (100%) | **MAE = 2.21 kcal/mol** | Wieder 多构象 DFT: 2.20 kcal/mol | RMSE = 3.23 vs. 3.07, 方向准确率 = 85.9% |
| *(成对基准严格对比)* | **舒适区** (|ΔN_aro| = 0) | 378 (82.2%) | **MAE = 1.73 kcal/mol** | Wieder 多构象 DFT: 1.79 kcal/mol | RMSE = 2.24 vs. 2.39, 方向准确率 = 88.8% |
| | ├─ CBH-Taut 黄金域 | 48 (10.4%) | **MAE = 1.38 kcal/mol** | Wieder 多构象 DFT: 1.56 kcal/mol | RMSE = 1.86 vs. 2.16, 方向准确率 = 79.2% |
| | └─ 常规舒适区子集 | 330 (71.7%) | **MAE = 1.78 kcal/mol** | Wieder 多构象 DFT: 1.82 kcal/mol | RMSE = 2.29 vs. 2.43, 方向准确率 = 90.2% |
| | **高风险区** (|ΔN_aro| > 0) | 82 (17.8%) | **MAE = 4.38 kcal/mol** | Wieder 多构象 DFT: 4.07 kcal/mol | RMSE = 5.95 vs. 5.14 (证明为量子化学通用瓶颈) |
| **SAMPL2 标定集** | **中性水相完整集** | 28 条记录 | **MAE = 1.81 kcal/mol** | 原始 GFN2: 3.67 kcal/mol | RMSE = 2.22, 方向准确率 = 78.6% |
| | └─ 芳香性严格守恒分子对 | 12 条记录 | **MAE = 0.49 kcal/mol** | 原始 GFN2: 1.80+ kcal/mol | 步入化学精度极限区间 (< 1.0 kcal/mol) |

*注：所有真实实验水相自由能预测均包含基于 SAMPL2 确定的势能面线性曲率校正系数（k_A = 0.575, k_B = 0.576, k_C = 0.577）。*

### 2. 关于理论训练集（Frag20-Taut Holdout）的说明
本模型预训练时使用的是来自 Frag20-Taut 的微观理论计算互变异构体分子对。这部分数据为高斯软件在 B3LYP/6-31G*/SMD 理论层级下计算的水相微观单点电子能残差。在包含 2,026 张孤儿/罕见骨架图的独立测试集上，Hydra-PaiNN 相对 B3LYP/SMD 理论参考值的残差预测 MAE 为 **1.33 ± 0.02 kcal/mol**（Tower A）和 **1.28 ± 0.01 kcal/mol**（Tower C），决定系数 R² = 0.97，充分证明神经网络成功拟合了目标量子力学残差。

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
