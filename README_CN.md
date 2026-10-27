# Hydra-PaiNN: 物理信息多塔Δ学习与互变异构水相平衡比例预测

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/KeantChen/TautomerRatio/blob/main/notebooks/Hydra_PaiNN_Quickstart.ipynb)
[![GitHub](https://img.shields.io/badge/GitHub-Repository-blue.svg?logo=github)](https://github.com/KeantChen/TautomerRatio)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

> **Languages / 语言版本 / Langues** : [English](README.md) | [中文 (Chinese)](README_CN.md) | [Français (French)](README_FR.md)

Hydra-PaiNN 是一个用于预测水相溶液中分子互变异构自由能差（**ΔG_aq**）、平衡常数（**K_eq**）以及玻尔兹曼优势异构体分布比例的物理信息机器学习预测框架。

$$
\Delta G_{\text{aq}} = -RT \ln K_{\text{eq}}, \quad K_{\text{eq}} = \frac{[\text{Tautomer B}]}{[\text{Tautomer A}]}
$$

框架包含：
1. **PaiNN 等变神经消息传递**：捕获具备连续方向性的 3D 几何与电子结构特征。
2. **半经验量子化学物理基线**：耦合 GFN2-xTB（含 ALPB 隐式水溶剂化）与 g-xTB 描述符。
3. **适用域前置诊断**：基于芳香性守恒与 Raghavachari 等键同构规则的 2D 分流。

---

## ⚡ Google Colab 一键云端运行（免本地安装）

无需在本地配置环境，点击下方链接即可在浏览器中运行：

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/KeantChen/TautomerRatio/blob/main/notebooks/Hydra_PaiNN_Quickstart.ipynb)

* **可视化表单**：输入两个互变异构体 SMILES，自动绘制 2D 分子图并输出玻尔兹曼比例。
* **结果展示**：展示相对自由能 ΔG、平衡常数 K_eq 与分流评级。
* **批量预测**：支持上传 CSV 文件进行批量计算。
* **硬件支持**：运行于 Google Colab CPU/GPU。

---

## 🎯 适用域与子集划分

根据芳香性守恒与 Raghavachari 等键同构规则进行前置划分：

### 1. 舒适区 (Comfort Zone, $|\Delta N_{\text{aro}}| = 0$，占数据集 79.4%)
芳香原子数守恒的互变异构对：
* **CBH-Taut Subset**（占 TautoBase-539 的 11.3%，61 对）：
  * **判据**：重原子杂化状态（$H_i$）与共价键连接类型（$B_{ij}$）在异构体间严格守恒。
  * **结果**：
    * **TautoBase-539**：MAE = **1.29 kcal/mol**（中位数 1.15 kcal/mol，RMSE = 1.76 kcal/mol）。
    * **DFT-460**：MAE = **1.38 kcal/mol**（DFT 参考值：MAE = 1.56 kcal/mol）。
    * **sPhysNet-Taut-100**：MAE = **1.02 kcal/mol**。
* **Normal Subset**（占 TautoBase-539 的 68.1%，367 对）：
  * **判据**：芳香性守恒（|ΔN_aro| = 0），伴随常规局域单双键重排。
  * **结果**：
    * **TautoBase-539**：MAE = **1.97 kcal/mol**（中位数 1.53 kcal/mol，RMSE = 2.56 kcal/mol，方向准确率 88.3%）。
    * **DFT-460**：MAE = **1.78 kcal/mol**（DFT 参考值：MAE = 1.82 kcal/mol）。
    * **sPhysNet-Taut-100**：MAE = **1.82 kcal/mol**。

### 2. 风险区 (Risk Zone, $|\Delta N_{\text{aro}}| > 0$，占数据集 20.6%，111 对)
伴随芳香环生成或破坏的转化（例如：苯酚 $\leftrightarrow$ 2,4-环己二烯酮）。
* **结果**：
  * **TautoBase-539**：MAE = **5.14 kcal/mol**（中位数 4.06 kcal/mol，RMSE = 6.73 kcal/mol）。
  * **DFT-460**：MAE = **4.38 kcal/mol**（DFT 参考值：MAE = 4.07 kcal/mol）。
* **注**：(Update is coming soon)

---

### 📊 3-Tier 分流体系

| 层级 (Tier) | 子集 / 适用域 | 判据 | 预期 MAE |
| :---: | :--- | :--- | :---: |
| **Tier 1** | **CBH-Taut Subset** | $\|\Delta N_\text{aro}\| = 0$，等键等杂化守恒 | **1.29 kcal/mol** |
| **Tier 2** | **Normal Subset** | $\|\Delta N_\text{aro}\| = 0$，芳香性守恒 | **1.97 kcal/mol** |
| **Tier 3** | **Risk Zone** | $\|\Delta N_\text{aro}\| > 0$，芳香性破坏与重构 | **5.14 kcal/mol** *(Update is coming soon)* |

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

### 1. 2D 拓扑分流初筛
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

# 2. 2D 适用域诊断
triage = predictor.triage_check("OC1=CC=CC=N1", "O=C1NC=CC=C1")
print(f"Domain: {triage['domain']} ({triage['subset']}) | 预期 MAE: {triage['expected_mae']} kcal/mol")

# 3. 预测
result = predictor.predict(
    smiles_A="OC1=CC=CC=N1",
    smiles_B="O=C1NC=CC=C1",
    mode="xtb_only",       # 或 "three_towers"
    temperature=298.15,    # 开尔文
    solvent="water"        # ALPB 溶剂
)

# 打印预测报告
predictor.print_report(result)
```

---

## 📄 许可证 (License)
本项目基于 MIT License 开源 - 详见 [LICENSE](LICENSE) 文件。
