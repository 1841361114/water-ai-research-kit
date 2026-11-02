# 功能说明：给什么输入，会得到什么

本页按实际任务介绍工具接口。所有示例都在项目根目录使用 Python 运行，无需下载数据或模型。示例中的数字、文本和标注均为人为构造。

## 1. 检查相同来源是否跨越数据集合

`assert_disjoint_groups(partitions)` 接收“集合名称 → 身份 ID 列表”。身份可以是测站、流域、机组、原始文档或事先计算出的连通组件。检查通过返回 `None`；同一个 ID 出现在多个集合中会抛出 `ValueError`，说明发生了你所定义的组重叠。

```python
from water_ai_research.splits import assert_disjoint_groups, connected_components

assert_disjoint_groups({"train": ["station-A"], "test": ["station-B"]})

# 两行只要共享任意身份就连在一起，间接共享也会传递。
groups = connected_components([
    ["basin:A", "record:1"],
    ["basin:B", "record:1"],
    ["basin:C"],
])
print(groups)  # [0, 0, 1]
```

后两种身份可以帮助发现“流域不同，但记录来源相同”的情况。函数不会自动识别流域之间的水文联系，也不会自动按比例分配训练集；身份定义及整个组件的分配由研究者决定。

`cross_split_duplicates(partitions)` 接收各集合中的文本，返回“重复内容的哈希 → 出现过的集合名称”。文本先进行 Unicode NFC、大小写折叠和空白合并，标点保留。返回值为空字典表示没有发现这种规范化规则下的跨集合重复。

```python
from water_ai_research.audit import cross_split_duplicates

duplicates = cross_split_duplicates({"train": ["Rain  fall"], "test": ["RAIN fall"]})
print(list(duplicates.values()))  # [['test', 'train']]
```

## 2. 给时序模型准备输入与预测目标

`temporal_windows(n, lookback, horizon, train_end, validation_end, gap=0)` 返回含 `train`、`validation`、`test` 三个列表的字典。每个 `Window` 包含四个索引：

| 属性 | 含义 |
|---|---|
| `input_start`, `input_stop` | 历史输入的起点和终点，用 `values[start:stop]` 提取 |
| `target_start`, `target_stop` | 需要预测的未来目标区间，用同样的切片方式提取 |

全部区间为左闭右开。训练拥有 `[0, train_end)`，验证拥有 `[train_end+gap, validation_end)`，测试拥有 `[validation_end+gap, n)`。一个样本的输入和目标必须完整落在同一集合，因此不同集合不共享原始观测；同一集合内部的窗口仍可能重叠。

这是保守的时间划分策略。它不会自动检查时间戳、不连续观测、多测站混排，也不会拟合归一化或缺测插补。区间太短时相应窗口列表可能为空。完整调用见仓库首页和 [水利接入说明](WATER_AI_GUIDE.md)。

## 3. 用简单方法给资料排序

### BM25：按查询词与文本匹配程度打分

`BM25(documents).score(query)` 接收候选文本列表和查询字符串，返回与候选顺序对应的分数。`rank_scores(scores, k=None)` 把分数转成从高到低的候选索引；并列时保留原顺序。

```python
from water_ai_research.retrieval import BM25, rank_scores

texts = ["rainfall runoff forecasting", "turbine vibration monitoring"]
scores = BM25(texts).score("runoff")
order = rank_scores(scores)
print(order)  # [0, 1]
print(texts[order[0]])  # rainfall runoff forecasting
```

它只对已经给出的文本评分，不负责上网找论文、读取 PDF、生成向量或回答问题。默认分词器适合简单词元演示；中文分词请通过 `BM25(texts, tokenizer=自己的分词函数)` 接入。

### RRF：合并不同检索器已经给出的排名

`reciprocal_rank_fusion(rankings, rank_constant=60)` 接收多条资料 ID 排名，返回按融合分数排序的 `(ID, 分数)` 列表。排名从 1 开始；某条排名里没有出现的 ID，在该条排名中贡献为 0。每条排名内部不能重复 ID。

```python
from water_ai_research.retrieval import reciprocal_rank_fusion

fused = reciprocal_rank_fusion([["A", "B"], ["B", "A", "C"]])
print([item for item, score in fused])  # ['A', 'B', 'C']
```

这里 A 与 B 并列，按首次出现顺序输出。RRF 不会替你运行产生这些排名的模型。

### MMR：在相关性与重复程度之间做选择

`mmr_select(relevance, similarity, k=10, weight=0.7)` 接收候选池的相关性分数和方形相似度矩阵，返回逐步选择记录。每步含 `index`、`relevance`、`redundancy`、`gain`，可用来解释为什么选中该项。

```python
from water_ai_research.retrieval import mmr_select

trace = mmr_select(
    relevance=[1.0, 0.9, 0.8],
    similarity=[[1, 1, 0], [1, 1, 0], [0, 0, 1]],
    k=2, weight=0.7,
)
print([step.index for step in trace])  # [0, 2]
```

第二项和第一项高度重复，因此第三项先被选中。相似度会裁剪到 `[0,1]`；相关性不会自动归一化，候选池顺序用于打破并列。这个机制不保证提高召回率。

## 4. 评价检索结果与数值预测

`retrieval_metrics(ranking, gold, k=10)` 接收资料 ID 排名和人工标注的正确 ID 集合，返回：

| 返回字段 | 含义 |
|---|---|
| `gold_count` | 金标中的正确资料总数 |
| `hits_at_k` | 前 k 项找到了多少个正确 ID |
| `recall_at_k` | 找到的正确 ID 数 / 全部正确 ID 数 |
| `hit_at_k` | 前 k 项至少命中一个则为 1，否则为 0 |
| `all_gold_at_k` | 前 k 项全部找齐则为 1，否则为 0 |
| `reciprocal_rank` | 完整传入排名中第一个正确结果的排名倒数；未命中为 0 |

```python
from water_ai_research.metrics import retrieval_metrics

result = retrieval_metrics(["A", "C", "B"], {"A", "B"}, k=2)
print(result["recall_at_k"], result["all_gold_at_k"])  # 0.5 0
```

金标为空时返回 `None`，不把未标注内容当作已确认负例。金标 ID 不在候选池中时，仍计入召回率分母；重复预测 ID 会报错。函数返回逐查询结果，跨查询如何汇总需要研究者明确规定。

`regression_metrics(observed, predicted)` 接收等长、按样本对齐的数值列表，返回 `n`、`mae`、`rmse`、`nse`。MAE 是绝对误差均值，RMSE 是均方根误差，二者越小越好且单位与输入相同。NSE 为 1 表示完全拟合，为 0 表示平方误差等于使用**当前评价集合观测均值**作为常数预测的误差，负数表示更差；该均值参考值不是一个只在训练集拟合的业务预测模型。观测为常数时 NSE 返回 `None`。缺失或无穷值会报错，不会自动删除。

## 5. 记录输入和结果文件，检查内容变化

`build_manifest(root, paths)` 对明确给出的文件列表记录相对路径、字节数和 SHA-256。`verify_manifest(root, rows)` 再次计算并比较，变化时报错；检查通过返回 `None`。`write_json(path, value)` 将记录以 UTF-8 和稳定键顺序写入 JSON，拒绝 NaN 等非有限数值。

```python
import tempfile
from pathlib import Path
from water_ai_research.audit import build_manifest, verify_manifest, write_json

with tempfile.TemporaryDirectory() as directory:
    root = Path(directory)
    write_json(root / "result.json", {"mae": 0.5})
    manifest = build_manifest(root, ["result.json"])
    verify_manifest(root, manifest)  # 文件未变化，通过
```

清单只覆盖你列出的文件，不检查遗漏的其他文件，也不自动记录运行环境、参数或代码版本。应将这些内容另存为协议文件，再列入清单。文件哈希能检测变化，不能证明原发布者可信或研究结论正确。

## 6. 检查已有标注视图对结论的影响

`grouped_view_bounds(group_sums, query_count)` 适合逐样本差值可加总的平均指标。每组提供各允许标注视图下的差值总和，同一组只能整组切换视图；各组可独立选择。输出 `lower` 和 `upper`。

```python
from water_ai_research.sensitivity import grouped_view_bounds

bounds = grouped_view_bounds({"group-A": [-2.0, 3.0], "group-B": [1.0, -1.0]}, query_count=5)
print(bounds)  # {'lower': -0.6, 'upper': 0.8}
```

输入必须对应完全相同的固定评价人群；函数不能替你核查这一前提。这只是允许视图组合中的范围，不是置信区间、统计显著性或真实标签界限。不能把语料整体 AUC 等不可按这里方式加总的指标直接代入。

## 7. 离线示例与命令行入口

`python3 -m water_ai_research demo --output outputs/first-run` 运行固定合成示例，生成数据、协议、结果和文件清单。`python3 -m water_ai_research verify outputs/first-run` 校验这批输出。安装后对应命令是 `water-ai demo ...` 和 `water-ai verify ...`。

示例的作用是帮助理解流程并核对环境。接入真实水利数据时，应自行实现有许可的数据读取、时间清洗和模型训练，并遵守 [实验记录模板](EXPERIMENT_TEMPLATE.md) 中的数据及评价约定。
