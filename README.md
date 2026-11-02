# Water AI Research Kit

一个从 AI 检索研究探索中整理出来的轻量工具包，用于积累可复用代码，并为后续水利与 AI 实验准备可靠的数据划分、基线和复现记录。

**当前版本 v0.1.0：Python 3.10+，运行时零第三方依赖，离线 CPU 可运行。**
它包含已有算法的实现和研究工程工具；目前没有新方法论文主张，也没有经过真实水文数据验证的预测模型。

[English overview](README_EN.md) · [代码来源与算法参考](docs/PROVENANCE.md) · [水利实验接入说明](docs/WATER_AI_GUIDE.md) · [MIT License](LICENSE)

## 能用来做什么

| 模块 | 已实现 | 对水利与 AI 的用途 |
|---|---|---|
| `retrieval.py` | BM25、RRF 融合、带逐步记录的 MMR | 建立文献/技术资料检索的简单基线 |
| `metrics.py` | Recall、Hit、找全率、倒数排名；MAE、RMSE、NSE | 明确评价口径，比较检索或预测基线 |
| `audit.py` | SHA-256、显式文件清单、文本重复检查、JSON 输出 | 追踪输入和结果，检查跨划分重复 |
| `splits.py` | 来源连通分量、组隔离检查、先切分再构窗 | 检查流域/测站跨集合重叠、避免窗口共享原始观测 |
| `sensitivity.py` | 整组切换标注视图的有限敏感性范围 | 查看固定人群上的结论是否依赖已有标注视图 |
| `demo.py` | 合成时序、持续性基线、资料检索、文件校验 | 运行一个完整且不需要数据下载的入门流程 |

文本重复检查只能发现特定规范化后的相同文本。它不能证明语义独立、上游数据独立或模型预训练无污染。MMR、融合或复杂模型均不保证优于简单基线。

## 立即运行

在解压后的项目根目录运行，无需安装包或联网：

```bash
python3 -m unittest discover -s tests -v
python3 -m water_ai_research demo --output outputs/first-run
python3 -m water_ai_research verify outputs/first-run
```

示例写出 `series.json`、`protocol.json`、`report.json`、`manifest.json`。重复运行请换输出目录；已有结果不会被覆盖。数值序列和检索资料均为人为构造，不能用示例分数证明真实预测效果。

也可在自己的虚拟环境中安装：

```bash
python3 -m pip install -e .
water-ai demo --output outputs/installed-run
```

安装时可能需要取得构建工具；直接用模块运行不需要第三方包。该项目未发布到 PyPI。

## 在自己的代码中使用

```python
from water_ai_research.retrieval import BM25, rank_scores
from water_ai_research.metrics import retrieval_metrics
from water_ai_research.splits import temporal_windows

documents = ["rainfall runoff forecasting", "turbine vibration monitoring"]
order = rank_scores(BM25(documents).score("runoff"))
ids = ["note-1", "note-2"]
print(retrieval_metrics([ids[i] for i in order], {"note-1"}, k=1))

# 单个测站、已检查时间顺序且连续等间隔的 1000 个观测。
windows = temporal_windows(
    n=1000, lookback=24, horizon=1,
    train_end=600, validation_end=800, gap=24,
)
```

中文资料请向 `BM25(..., tokenizer=你的分词函数)` 传入分词器。默认仅使用正则词元，不提供中文分词。检索评分和数值计算采用清晰的小规模实现，未针对大型语料优化。

## 评价约定

- 排名分数相同时，保留输入候选顺序；RRF 并列按首次出现顺序。输入顺序应写入实验记录。
- 空金标返回 `None`，表示本函数不评分；不得悄悄当作已确认负例。
- 金标中不在候选池的 ID 仍计入召回率分母。倒数排名使用传入的完整排名，其他检索指标使用前 `k` 项。
- NSE 的观测方差为零时返回 `None`；负 NSE 原样保留，非有限输入报错。
- 时序构窗采用保守策略：输入及目标都必须位于同一划分，边界窗口直接舍弃。间隔单位为观测条数。
- 标注敏感性仅适用于同一固定人群、可加总的逐样本差值；它不是置信区间或显著性检验。

## 研究来源与开源范围

检索、评测和标注审计来自此前的探索工程，经重构后移除具体数据路径及跨轮次依赖。水文指标、通用划分接口和合成时序示例是此次整理时新增的适配代码，未宣称已在真实水利场景验证。

此前探索没有建立新算法贡献，也未完成独立留出验证；本仓库不发布顶会录用或性能领先的说法。第三方语料、模型权重、外部作者实现、个人资料和未发表论文均不在本仓库中。代码在 AI 辅助下整理；使用者仍需阅读实现并验证自己的实验。

原始算法论文及具体适配变化见 [PROVENANCE.md](docs/PROVENANCE.md)。MIT 许可覆盖仓库内原创代码和文档；外部数据、模型及论文遵守各自许可。项目名称描述研究使用方向，不代表任何机构或已有软件的背书。

## 后续积累方式

先用 [水利实验接入说明](docs/WATER_AI_GUIDE.md) 固定一个具体任务，再接入有许可的数据及简单基线。新增实验使用 [实验记录模板](docs/EXPERIMENT_TEMPLATE.md)，记录数据版本、划分、参数、计算预算和失败结果；真实原始数据及模型文件默认留在仓库外。

欢迎提交带可复现最小示例的修复；请勿把真实敏感测站数据、密钥或无权分发的数据作为问题附件。贡献代码应注明来源，并保持 `python3 -m unittest discover -s tests -v` 通过。
