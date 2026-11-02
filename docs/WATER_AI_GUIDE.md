# 把工具接入水利与 AI 研究

这里提供的是实验准备方法。当前仓库没有真实测站数据、降雨径流训练模型、水轮机诊断模型或物理求解器。

## 先明确要检验的任务

| 任务例子 | 首要划分问题 | 当前可复用工具 |
|---|---|---|
| 同一测站预测未来流量 | 时间先后、滑窗边界、预测步长 | `temporal_windows`、持续性基线、回归指标 |
| 推广到未见流域 | 流域/测站隔离、共享上游及重复记录 | `connected_components`、`assert_disjoint_groups` |
| 水轮机传感器故障识别 | 同一机组、工况和连续事件不得随机打散后冒充独立测试 | 组隔离检查、文件身份记录；分类模型需另行实现 |
| 水利技术资料检索 | 相同来源文档的重复、候选池与评价范围 | BM25、RRF、MMR、检索指标、重复文本审计 |

时间泛化与新流域泛化是不同问题。`temporal_windows` 保证单条输入序列各划分不共享原始观测，但不会自动实现未见流域测试；组检查也不会自动发现你没有提供的水文联系。

## 使用真实时序前要准备的字段

最小记录可包含 `station_id`、`basin_id`、`timestamp`、`variable`、`value`、`unit`、`quality_flag`。这些是接入约定示例，不是强制文件格式；本版没有 CSV 导入器。

1. 确认数据使用许可、单位、时区、测量频率和缺失标记。
2. 按测站检查时间单调、重复时间、缺测和间隔；不要把多个测站串成一条序列。
3. 固定训练/验证/测试的日期边界及研究问题，再创建滑窗。
4. 归一化、插补、特征筛选和模型参数只在允许的训练数据上拟合。当前工具不负责这些拟合步骤。
5. 保留持续性等简单基线，按预测步长和测站报告结果。不要把多步预测摊平后的样本相关性当成独立重复。
6. 测试集用于最终一次固定方案评价；调参和反复查看均应在记录中如实说明。

## 时间窗口的精确定义

```python
from water_ai_research.splits import temporal_windows

parts = temporal_windows(
    n=1000, lookback=24, horizon=6,
    train_end=600, validation_end=800, gap=24,
)
for w in parts["test"]:
    x = values[w.input_start:w.input_stop]
    y = values[w.target_start:w.target_stop]
```

`values` 应由你从同一测站的连续、等间隔观测中准备。这里 `gap=24` 表示 24 条观测；只有每小时采样且没有缺口时才等于 24 小时。所有区间为左闭右开。边界窗口会舍弃；验证/测试不会借用训练区间历史，因此比部分业务滚动预测协议更保守。若改成允许历史上下文的协议，应明确规定目标时间和特征可见性，再增补相应检查。

## 连通组件与组隔离

```python
from water_ai_research.splits import connected_components, assert_disjoint_groups

# 每一行对应一个样本；同一身份的行通过传递关系连通。
components = connected_components([
    ["basin:A", "record-hash:abc"],
    ["basin:B", "record-hash:abc"],
    ["basin:C"],
])
assert components == [0, 0, 1]
assert_disjoint_groups({"train": [components[0]], "test": [components[2]]})
```

先定义身份的含义，再按整个组件分配集合。跨流域共享记录可能使两个流域连在一起；函数不会替你决定这种关系在任务中是否应该隔离，也不会自动分配训练比例。

## 下一次实质扩展

选定一个有许可的真实小数据集后，新增独立的数据适配器和固定协议，保存哈希与数据来源。通过最简单的真实基线后，再决定是否值得引入神经网络。应把这一步视为新研究验证，不能把本仓库合成示例的通过当作已经完成。
