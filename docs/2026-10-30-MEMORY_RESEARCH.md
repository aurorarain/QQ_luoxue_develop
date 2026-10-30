# 记忆层调研：所谓"3D 知识记忆网络"（2026-10-30）

结论先行：**不安装任何现成插件**，自建一个轻量图谱层（SQLite + 少量 LLM 抽取），3D 只做离线导出图。
本文记录为什么，以及如果以后一定要装现成的该怎么装。

## 1. 现状盘点：她现在的记忆是什么

| 层 | 存储 | 谁能用 | 检索方式 |
|---|---|---|---|
| Soul 设定 | `soul.md`（memory 插件） | 仅 Alex 私聊 | 整段注入 |
| 用户画像 | `profile.md` | 仅 Alex 私聊 | 整段注入 |
| 历史索引 | `history_index.md` | 仅 Alex 私聊 | 整段注入 + `read_memory_detail` 工具 |
| 备忘录 / TODO | `memo.md` + 工具 | 仅 Alex 私聊 | 工具按需读 |
| 群聊原文 | `events.db`（SQLite） | 群→私聊单向可查 | 关键词 `LIKE`，最多 12 条 |
| 私聊原文 | `state.json` 最近 120 条 | 仅私聊 | 时间顺序 |
| 说说/评论 | `posts_5.db`（空间插件） | 空间插件 | 插件自己的查询 |
| 关系数值 | `relationship_state.json` | 主人私聊 | 插件注入 |
| 成长 | `state.json → growth`（本轮新增） | 仅 Alex 私聊 | 固化条目注入 |

**没有实体、没有关系边、没有时间有效性、没有向量检索。** 问"上周那个说要做毕设的人"时，只能靠 `LIKE` 撞词。

## 2. 三个候选的真实评估

### 2.1 `astrbot_plugin_self_learning`（NickCharlie / EterUltimate，v4.4.5）

- 许可证：**AGPL-3.0**（衍生自 AstrBot，同样 AGPL）；AstrBot ≥ 4.11.4；Python 3.11+。
- 能力：对话风格学习（few-shot）、群黑话挖掘、**人格演化审查**（批准/拒绝/回滚）、社交关系与心理状态、**记忆与知识图谱 + 可视化查询入口**、`on_llm_request` 注入、独立 WebUI（默认 `:7833`）、多数据库（SQLite/MySQL/PostgreSQL）。
- 冲突面：它会**自己维护好感度与心理状态**、自己演化人格、自己建记忆库——和现有 `relationship`（好感/信任/熟悉度）、`astrbot_plugin_memory`（Soul/画像）、本轮新增的 `growth`（可审计成长）三套系统**正面重叠**。
- 结论：**不装**。理由是冲突而不是质量：三个系统同时往 system_prompt 里注入关系与人格，出问题时无法判断是谁改的；而且它自带 WebUI 常驻进程，4GB 机器上要多一份内存和端口暴露面。若将来要试，必须单独一台机器或先关掉 relationship + memory 再试。

### 2.2 `memory-brain`（peterpoal134）

- 许可证：**AGPL-3.0-or-later**；AstrBot 4.29.x；Python 3.12；SQLite 内置。
- 设计：五类记忆（事件/事实/反思/技能/道理）、五路混合检索（向量+关键词+**实体图谱**+重要性+新鲜度）、遗忘治理（衰减/归档/相似合并/冲突检测）、PAD 三维情绪、独立"生活层"进程、每日备份、**3D 面板**。
- 自报数据：常驻 100–200MB、检索 p50 120–140ms、每天 60 条约一年 2.2 万条、十年约 2.4GB。
- 硬约束（值得抄的设计）：人格文件**只读**、只追加带 marker 的注入块、每个模块单独开关且**默认关**。
- 冲突面：它是**四个插件**（记忆/情绪/风格清洗/自我档案）加一个可选生活层进程，会整体覆盖现有 memory + relationship 的分工；现有 `soul.md`/`profile.md` 数据需要迁移。
- 结论：**不整体安装**；**它的设计当参考照抄**（只追加不覆盖、marker 去重、模块开关默认关、遗忘与合并）。

### 2.3 Graphiti（getzep，Apache-2.0）

- 时序知识图谱（`valid_at`/`invalid_at`），最适合"某个事实什么时候为真"。
- 致命项：**写入延迟约 35 秒 / 3 轮对话**（第三方评估记录），且需要 Neo4j。
- 结论：**不适合本场景**。这是"记忆预处理工具"，不是实时聊天伴侣的组件。

### 2.4 关于"3D"

- 检索到与"3D 知识图谱"直接相关的是 `memory-brain` 的 3D 面板，以及第三方 3D 记忆图谱演示页（[studiomeyer.io 的 Memory 3D Knowledge Graph demo](https://studiomeyer.io/en/services/memory/demo)）——都属于**可视化**，不改变检索质量。
- 交接文档里提到的 "WaveMemory"：本轮没有检索到可信的同名项目，暂时按"记忆有误"处理，不再作为候选。

## 3. 为什么 3D 本身不值得做

1. **观感 ≠ 检索**：3D 星空图很好看，但回答"上周谁说要考研"靠的是实体+关系+时间过滤，不是旋转的球。
2. **常驻成本**：4GB 无 GPU，跑一个 WebGL 面板 + 图数据库不现实；导出成静态 HTML 反而零成本。
3. **已有替代品**：AstrBot 自带 WebUI 就能看记忆文件；真要"看得见"，离线导出一张力导向图足够。

## 4. 建议方案：自建轻量图谱 v0（约 150 行）

不引入新服务、不引入 embedding 服务器、不常驻界面。

```
memory_graph.db (SQLite)
  entities(id, name, kind, first_seen, last_seen)
  edges(id, src, rel, dst, ts, weight, channel, evidence_event)
  mentions(entity_id, event_id, ts)
```

- **抽取**：每累计 N 条新消息（或每 6 小时）抽一批，调一次主模型输出 JSON `{entities:[{name,kind}], edges:[{src,rel,dst}]}`；每批最多 20 条消息、1 次调用，日上限 12 次。
- **写入**：实体去重（同名同 kind 合并，`last_seen` 更新）；边按 `(src,rel,dst)` 去重累加 `weight`；证据只存 `events.db` 的 id，不复制原文。
- **检索**：命中实体名的做 1 跳扩展，按 `weight × 新鲜度` 排序取前 8 条，压成两三行注入（群聊只用公开群事件，私聊才含私聊事件）。
- **开关**：`state['graph']['enabled']` 默认关，先只写入不注入跑一天，看抽取质量。
- **预算**：一天 12 次小调用 ≈ 几分钱；SQLite 一年不到 10MB。
- **边界**：图谱只提供"可检索的事实线索"，**不改人设**；和 `growth`（改表达习惯）是两件事，互不覆盖。
- **3D**：`scripts/export_memory_graph.py` 一次导出 HTML（vis-network 之类单文件），本地打开看；不部署到服务器。

## 5. 如果以后一定要装现成的

优先 `memory-brain`，并按它的建议顺序灰度：

1. 复制一份容器/数据目录做**隔离试点**，不要直接上生产。
2. 先只开写入、不开注入，跑一天看摘要质量。
3. 私聊开注入 → 再开群聊；同时**关闭** `astrbot_plugin_memory` 与 `relationship` 的注入，避免三套系统同时写 prompt。
4. 建 20–40 条中文评估问题，改一次跑一次。
5. 注意 AGPL-3.0：如果要把本项目公开分发，不能把它的代码抄进来。

## 6. 明确不做

- 不装 self_learning（冲突 + AGPL + 常驻 WebUI）。
- 不装 Graphiti（35 秒写入延迟 + Neo4j）。
- 不做常驻 3D 可视化服务。
- 不在图谱里复制聊天原文（只存指针，隐私留在 `events.db`）。
- 不让图谱或成长层改写 `persona.py`。

## 7. 参考

- [astrbot_plugin_self_learning](https://github.com/NickCharlie/astrbot_plugin_self_learning)（AGPL-3.0，v4.4.5）
- [memory-brain](https://github.com/peterpoal134/memory-brain)（AGPL-3.0-or-later，AstrBot 4.29.x）
- [Graphiti](https://github.com/getzep/graphiti)（Apache-2.0，写入延迟约 35s/3 轮，需 Neo4j）
- [Memory 3D Knowledge Graph demo](https://studiomeyer.io/en/services/memory/demo)（可视化演示，非记忆引擎）
