# Hydra-PaiNN: 物理信息多塔Δ学习与互变异构水相平衡比例预测

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/KeantChen/TautomerRatio/blob/main/notebooks/Hydra_PaiNN_Quickstart.ipynb)
[![GitHub](https://img.shields.io/badge/GitHub-Repository-blue.svg?logo=github)](https://github.com/KeantChen/TautomerRatio)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

> **Languages / 语言版本 / Langues** : [English](README.md) | [中文 (Chinese)](README_CN.md) | [Français (French)](README_FR.md)

Hydra-PaiNN 是一个用于预测水相溶液中分子互变异构自由能差（**ΔG_aq**）、平衡常数（**K_eq**）以及玻尔兹曼优势异构体分布比例的物理信息机器学习预测框架。

$$
\Delta G_{\text{aq}} = -RT \ln K_{\text{eq}}, \quad K_{\text{eq}} = \frac{[\text{Tautomer B}]}{[\text{Tautomer A}]}
$$

核心架构深度融合了：
1. **PaiNN 等变神经消息传递**：捕获具备连续方向性与空间对称性的 3D 几何特征与电子局域场。
2. **半经验量子化学物理底座**：耦合 GFN2-xTB（含 ALPB 隐式水溶剂化）与 g-xTB 电子结构描述符。
3. **基于连接性层级（CBH-Taut）的拓扑分流**：基于 Raghavachari 等保键反应理论的 2D 图论诊断算法，在量子计算前快速评估系统误差相消程度。

---

## ⚡ Google Colab 一键云端速览（免本地安装）

合作者无需在本地配置环境、CUDA 或编译 xTB，直接点击下方徽章即可在浏览器中一键运行：

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/KeantChen/TautomerRatio/blob/main/notebooks/Hydra_PaiNN_Quickstart.ipynb)

* **可视化交互表单**：输入任意两个互变异构体 SMILES，自动绘制 2D 分子结构图并标注优势构型与平衡比例。
* **高颜值结果卡片**：清晰展示相对自由能 ΔG、平衡常数 K_eq 与分流评级卡片。
* **批量 CSV 上传**：一键评估多个分子对并导出结果表。
* **全平台免配置**：运行于免费的 Google Colab 云端（支持自动 GPU 加速）。

---

## 🎯 适用域划分与置信度层级体系（与论文正文完全一致）

在论文正文中，互变异构体在进入量子计算前，首先根据**芳香性守恒**与**Raghavachari 等键同构理论**进行严格的前置化学拓扑分流：

### 1. 舒适区 (Comfort Zone, $|\Delta N_{\text{aro}}| = 0$，占数据集 79.4%)
两异构体之间的芳香环原子数完全守恒，连续溶剂化模型与半经验底层的系统误差能够稳健自我抵消。舒适区内部进一步细分为两个子集：
* **CBH-Taut Subset (严格等键同构子集)**（占 TautoBase-539 的 11.3%，61 对）：
  * **划分标准**：重原子杂化状态（$H_i$）与无序共价键连接类型（$B_{ij}$）在互变异构对之间**完全严格守恒**。
  * **表现**：底层系统误差实现几乎完美的代数相消，稳健达到高精度化学精度：
    * **TautoBase-539**：MAE = **1.29 kcal/mol**（中位数 1.15 kcal/mol，RMSE = 1.76 kcal/mol）。
    * **DFT-460**：MAE = **1.38 kcal/mol**（超越高阶 DFT 参考基准的 1.56 kcal/mol）。
    * **sPhysNet-Taut-100**：MAE = **1.02 kcal/mol**。
* **Normal Subset (常规舒适子集)**（占 TautoBase-539 的 68.1%，367 对）：
  * **划分标准**：芳香性守恒，但存在常规的局域单双键重排或杂化状态局部转移。
  * **表现**：在绝大多数类药刚性骨架上保持极高可靠性：
    * **TautoBase-539**：MAE = **1.97 kcal/mol**（中位数 1.53 kcal/mol，RMSE = 2.56 kcal/mol，优势构型方向准确率 88.3%）。
    * **DFT-460**：MAE = **1.78 kcal/mol**（比肩高阶 DFT 参考基准的 1.82 kcal/mol）。
    * **sPhysNet-Taut-100**：MAE = **1.82 kcal/mol**。

### 2. 风险区 (Risk Zone, $|\Delta N_{\text{aro}}| > 0$，占数据集 20.6%，111 对)
伴随芳香环生成或破坏的复杂转化（例如：苯酚 $\leftrightarrow$ 2,4-环己二烯酮，吡唑 $\leftrightarrow$ 烯胺）。
* **表现**：
  * **TautoBase-539**：MAE = **5.14 kcal/mol**（中位数 4.06 kcal/mol，RMSE = 6.73 kcal/mol）。
  * **DFT-460**：Hydra-PaiNN MAE = **4.38 kcal/mol**。
* **物理化学本质与演进方向**：
  芳香性的破坏引发强烈的芳香稳定化能（ASE）剧烈突变，并伴随离散溶剂化氢键网络的显著重组，导致连续介质假定在此失效。值得注意的是，**即便高阶 DFT（B3LYP/aug-cc-pVTZ//B3LYP/6-31G(d)/SMD）在该区间的 MAE 也高达 4.07 kcal/mol**，说明这是连续介质物理模型的共同物理极限。**我们目前正在积极研发结合显式微溶剂化鞘层与混合多塔的高阶架构，以专项攻关并提升 Risk Zone 的预测精度。**

---

### 📊 虚拟筛选 3-Tier 置信度映射表

对于大规模虚拟筛选与自动化打分管线，上述三个集合天然映射为简洁的 **3-Tier 置信度层级**：

| 层级 (Tier) | 正文子集 (Subset) | 核心拓扑判据 | 预期 MAE | 置信等级 | 虚拟筛选管线建议 |
| :---: | :--- | :--- | :---: | :---: | :--- |
| **Tier 1** | **CBH-Taut Subset** | $\|\Delta N_\text{aro}\| = 0$，严格等键等杂化守恒 | **1.29 kcal/mol** | **极高 (化学精度)** | 可直接用于高精度结合自由能及活性计算 |
| **Tier 2** | **Normal Subset** | $\|\Delta N_\text{aro}\| = 0$，芳香性守恒刚性骨架 | **1.97 kcal/mol** | **高 (工业基准)** | 适用于常规高通量虚拟筛选与先导化合物优化 |
| **Tier 3** | **Risk Zone** | $\|\Delta N_\text{aro}\| > 0$，芳香性破坏与重构 | **5.14 kcal/mol** | **谨慎 (高风险)** | 标记存在芳香重排，提示高风险（正在专项提升） |

---

## 🔬 基准评测全景表 (Benchmark Summary)

模型在各数据集与子集上的基准对比（摘自论文 Table 4 / Table 5）：

| 数据集 | 子集划分 | 样本数 (%) | 基线 / DFT MAE | Hydra-PaiNN MAE | 基线 RMSE | Hydra-PaiNN RMSE |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: |
| **TautoBase-539** | CBH-Taut Subset | 61 (11.3%) | 1.29 | **1.29** | 1.76 | **1.76** |
| | Normal Subset | 367 (68.1%) | 1.97 | **1.97** | 2.56 | **2.56** |
| | Risk Zone | 111 (20.6%) | 5.14 | **5.14** | 6.73 | **6.73** |
| **DFT-460** | CBH-Taut Subset | 48 (10.4%) | 1.56 (DFT) | **1.38** | 2.16 (DFT) | **1.86** |
| | Normal Subset | 330 (71.7%) | 1.82 (DFT) | **1.78** | 2.43 (DFT) | **2.29** |
| | Risk Zone | 82 (17.8%) | 4.07 (DFT) | **4.38** | 5.14 (DFT) | **5.95** |
| **sPhysNet-Taut-100**| CBH-Taut Subset | 11 (11.0%) | 1.58 (预训练) | **1.02** | 1.98 | **1.30** |
| | Normal Subset | 68 (68.0%) | 2.97 (预训练) | **1.82** | 3.74 | **2.19** |
| | Risk Zone | 21 (21.0%) | 10.19 (预训练) | **5.06** | 11.90 | **6.00** |

---

## 💻 本地安装与环境部署

### 1. 克隆仓库并安装依赖
```bash
git clone https://github.com/KeantChen/TautomerRatio.git
cd TautomerRatio

pip install -r requirements.txt
```

### 2. 运行自动化验证自检
```bash
python verify_installation.py
```

---

## 🚀 命令行（CLI）使用指南

### 1. 毫秒级 2D 拓扑分流初筛 (< 1 ms)
在不运行量子化学计算的前提下，快速判定分子对的适用域与预期误差：
```bash
python predict.py --smi1 "OC1=CC=CC=N1" --smi2 "O=C1NC=CC=C1" --triage_only
```

### 2. 标准单点预测 (xTB Tower-A, 开箱即用)
预测水相自由能差、平衡常数及主导异构体：
```bash
python predict.py --smi1 "OC1=CC=CC=N1" --smi2 "O=C1NC=CC=C1" --mode xtb_only
```

### 3. 多塔联合预测 (Towers A, B, and C)
当本地或 WSL 配置好 g-xTB 时启用：
```bash
python predict.py --smi1 "OC1=CC=CC=N1" --smi2 "O=C1NC=CC=C1" --mode three_towers
```

### 4. 批量 CSV 文件预测
```bash
python predict.py --input examples/test_cases.csv --output predictions.csv --mode xtb_only
```

---

## 🐍 Python 代码接口调用

```python
from tautomer_predictor import TautomerPredictor

# 1. 初始化预测器（加载权重与归一化参数）
predictor = TautomerPredictor()

# 2. 毫秒级 2D 适用域诊断
triage = predictor.triage_check("OC1=CC=CC=N1", "O=C1NC=CC=C1")
print(f"Domain: {triage['domain']} ({triage['subset']}) | 预期 MAE: {triage['expected_mae']} kcal/mol")

# 3. 完整 3D 量化 + ML 残差预测
result = predictor.predict(
    smiles_A="OC1=CC=CC=N1",
    smiles_B="O=C1NC=CC=C1",
    mode="xtb_only",       # 或 "three_towers"
    temperature=298.15,    # 开尔文
    solvent="water"        # ALPB 溶剂
)

# 打印美化后的预测报告
predictor.print_report(result)
```

---

## 📄 许可证 (License)
本项目基于 MIT License 开源 - 详见 [LICENSE](LICENSE) 文件。
