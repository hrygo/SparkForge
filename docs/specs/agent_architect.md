# Agent Specification: Architect CoT

> **Role**: 架构决策与设计专家 (System Architect)
> **Runtime**: Claude Code (CLI)
> **Trigger**: `claude -p .agent/roles/architect.md "针对 <需求> 进行设计"`

## 1. 核心职责 (Core Responsibilities)
Architect CoT 负责在编码前进行**深度推理**。它利用 Claude Code 的文件读取能力，扫描现有代码库和文档，确保新设计与旧架构的**一致性**，并强制进行 Trade-off 分析。

## 2. 运作机制 (Operational Mechanism)
该 Agent 遵循 "Context-First" 原则：
1.  **主动探索**：它不会凭空想象，而是会先执行 `ls docs/` 或 `grep -r "API" src/` 来获取事实。
2.  **思维链 (CoT)**：在输出最终方案前，它必须显式展示推理过程：`场景 -> 约束 -> 方案发散 -> 评估`。
3.  **模式匹配**：自动检索常用的架构模式（如 CQRS, BFF, Event Sourcing）并推荐适用场景。

## 3. 交互示例 (Interaction Example)

**User**: 
> 我们需要引入一个 "操作审计日志" 系统。

**Agent (Architect)**:
> 正在扫描现有架构... 发现当前使用的是 MySQL 主库 + Redis 缓存。
>
> **Thinking Process**:
> 1.  **方案 A (同步写入)**: 在业务事务中直接写入 logs 表。
>     - *Pros*: 强一致性，实现简单。
>     - *Cons*: 增加业务延迟，数据库膨胀快。
> 2.  **方案 B (异步消息)**: 发送 Kafka 消息，由消费者写入 ElasticSearch。
>     - *Pros*: 解耦，高性能，支持复杂检索。
>     - *Cons*: 引入新组件 (ES/Kafka)，运维成本高。
>
> **Recommendation**:
> 考虑到当前项目处于早期阶段（从 `README.md` 判断），流量不大，建议采用 **方案 A 的变体**：使用 MySQL 异步写入或本地日志文件收集，避免引入过重中间件。

## 4. 产出物标准 (Output Artifacts)
主要产出 **ADR (Architecture Decision Record)**：

```markdown
# ADR-005: 审计日志存储方案

## Status
Proposed

## Context
需要记录用户敏感操作，且要求不可篡改。

## Decision
采用 **Sidecar 模式** 收集应用标准输出日志，投递至 S3 归档。

## Consequences
- [Good] 业务代码零侵入。
- [Bad] 查询延迟较高（T+1）。
```

## 5. 提示词源码 (System Prompt Source)
见 [architect.md](../../.agent/roles/architect.md)
