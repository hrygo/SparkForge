# 📚 SparkForge 资产与知识库

这是 SparkForge 引擎的核心数据存储区，包含了从原始研究、规格定义到经过 **[The Crucible]** 熔炉打磨的最终交付物。

## 📂 目录结构 (v2.0.0)

| 目录/文件              | 类型              | 说明                                                                                       |
| :--------------------- | :---------------- | :----------------------------------------------------------------------------------------- |
| **`knowledge/`**       | 🧠 **外部事实**   | [Phase 0] 由 Oracle 扫描并注入的结构化事实（法规、基准数据）。按项目隔离。                 |
| **`oracle_requests/`** | 📡 **雷达日志**   | [Phase 0] Oracle 扫描的请求意图记录。                                                      |
| **`reports/`**         | 📜 **辩论档案**   | [Phase 1/2] 每一轮 Council 辩论记录、Adjudicator 裁决书及历史摘要 (`history_summary.md`)。 |
| **`research/specs/`**  | 📐 **规格库**     | 标准化的 AI Agent 规格定义 (SDD)。                                                         |
| **`articles/`**        | 📝 **深度文章**   | 关于 AI 软件工程方法论的深度分析与案例复盘。                                               |
| **`output/`**          | 📤 **交付物**     | 最终生成的 PDF 报告（A4/Glass 长图）。                                                     |
| **`*.md`**             | 💎 **核心交付物** | 经过熔炉打磨的最终方法论报告。                                                             |

> ⚠️ **注意**: `backup/` 目录已被废弃，历史版本请通过 Git 查看。

## 💎 核心资产

### 1. 经过 Crucible 验证的方法论

以下文档已通过高强度的 AI 对抗辩论与外部事实锚定：

- **[智慧IM及移动办公门户员工画像调研方法论报告.md](./articles/智慧IM及移动办公门户员工画像调研方法论报告.md)**
  - **Loop 4 Pass (Score: 92)**
  - 包含：DEX/JTBD 融合模型、RACI 责任矩阵 (含 R-Prime/L3 升级)、合规黄金标准 (SOP)。

- **[PRD_Spec_Builder.md](./articles/PRD_Spec_Builder.md)**
  - Spec Builder 产品的核心需求规格说明书。

### 2. The SparkForge Chronicles (编年史)

记录了 SparkForge 自身进化的思想实验与哲学反思：

- **[The_SparkForge_Chronicles_Breaking_the_Cage.md](./articles/The_SparkForge_Chronicles_Breaking_the_Cage.md)**: 记录了从 "Prompt Jailbreaking" 到 "Protocol 90/10" 的觉醒过程。

---

> 📅 最后更新: 2025-12-25 (v2.0.0)
