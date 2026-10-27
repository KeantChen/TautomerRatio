# 互变异构预测案例说明
## 3-Tier 适用域分流与多塔预测

本文档展示三个适用域子集的典型预测案例：
- **Comfort Zone ($|\Delta N_\text{aro}| = 0$)**：
  - **Tier 1 (CBH-Taut Subset)**：重原子杂化与共价键连接类型严格守恒（预期 MAE: 1.29 kcal/mol）。
  - **Tier 2 (Normal Subset)**：芳香性守恒，伴随局域单双键重排（预期 MAE: 1.97 kcal/mol）。
- **Risk Zone ($|\Delta N_\text{aro}| > 0$)**：
  - **Tier 3 (Risk Zone)**：伴随芳香环生成或破坏的转化（预期 MAE: 5.14 kcal/mol）。*(Update is coming soon)*

---

## 案例 1: 乙酰基环戊酮烯醇-烯醇互变 — Tier 1 (CBH-Taut Subset)

* **输入分子**:
  * 异构体 A: `CC(=O)C1=C(O)CCC1`
  * 异构体 B: `C/C(O)=C1\CCCC1=O`
* **判据**: $\Delta N_\text{aro} = 0$，且异构体间重原子杂化与共价键类型严格守恒。
* **实验参考值 (TautoBase Row 37)**: $\log_{10} K = 0.60$, $\Delta G_\text{exp} = -0.82\text{ kcal/mol}$（B 占优）。
* **运行命令**:
  ```bash
  python predict.py --smi1 "CC(=O)C1=C(O)CCC1" --smi2 "C/C(O)=C1\CCCC1=O"
  ```
* **预测结果 (Tower A)**: $\Delta G_\text{pred} = -0.62\text{ kcal/mol}$, $\log_{10} K = +0.45$, 优势构型: **B (74.0%)**，绝对误差 = $0.20\text{ kcal/mol}$。

---

## 案例 2: 2-羟基吡啶 / 2-吡啶酮 — Tier 2 (Normal Subset)

* **输入分子**:
  * 异构体 A (2-羟基吡啶): `OC1=CC=CC=N1`
  * 异构体 B (2-吡啶酮): `O=C1NC=CC=C1`
* **判据**: 芳香原子数守恒 ($|\Delta N_\text{aro}| = 0$)，局域内酰胺-内酰亚胺重排。
* **实验参考值 (SAMPL2)**: $\Delta G_\text{exp} = -2.60\text{ kcal/mol}$（B 占优）。
* **运行命令**:
  ```bash
  python predict.py --smi1 "OC1=CC=CC=N1" --smi2 "O=C1NC=CC=C1"
  ```
* **预测结果 (Tower A)**: $\Delta G_\text{pred} = -2.45\text{ kcal/mol}$, $\log_{10} K = +1.80$, 优势构型: **B (98.4%)**，绝对误差 = $0.15\text{ kcal/mol}$。

---

## 案例 3: 苯酚 / 2,4-环己二烯酮 — Tier 3 (Risk Zone)

* **输入分子**:
  * 异构体 A (苯酚): `Oc1ccccc1` ($N_\text{aro} = 6$)
  * 异构体 B (2,4-环己二烯酮): `O=C1C=CC=CC1` ($N_\text{aro} = 0$)
* **判据**: 芳香性破坏 ($|\Delta N_\text{aro}| = 6 > 0$)。
* **实验参考值**: $\Delta G_\text{exp} = +14.00\text{ kcal/mol}$（A 占优）。
* **运行命令**:
  ```bash
  python predict.py --smi1 "Oc1ccccc1" --smi2 "O=C1C=CC=CC1"
  ```
* **预测结果 (Tower A)**: $\Delta G_\text{pred} = +7.71\text{ kcal/mol}$，优势构型: **A (100.0%)**，绝对误差 = $6.29\text{ kcal/mol}$。*(Update is coming soon)*

---

## 汇总表

| 层级 (Tier) | 子集 / 适用域 | 示例分子对 | $\Delta G_\text{pred}$ | $\Delta G_\text{exp}$ | 子集预期 MAE |
| :---: | :--- | :--- | :---: | :---: | :---: |
| **Tier 1** | **CBH-Taut Subset** | `CC(=O)C1=C(O)CCC1` $\to$ `C/C(O)=C1\CCCC1=O` | $-0.62\text{ kcal/mol}$ | $-0.82\text{ kcal/mol}$ | **1.29 kcal/mol** |
| **Tier 2** | **Normal Subset** | `OC1=CC=CC=N1` $\to$ `O=C1NC=CC=C1` | $-2.45\text{ kcal/mol}$ | $-2.60\text{ kcal/mol}$ | **1.97 kcal/mol** |
| **Tier 3** | **Risk Zone** | `Oc1ccccc1` $\to$ `O=C1C=CC=CC1` | $+7.71\text{ kcal/mol}$ | $+14.00\text{ kcal/mol}$ | **5.14 kcal/mol** *(Update is coming soon)* |
