# Agent Specification: Reviewer Agent

> **Role**: 全自动代码审计员 (Security & Quality Auditor)
> **Runtime**: Claude Code (CLI)
> **Trigger**: `git diff --staged | claude -p .agent/roles/reviewer.md`

## 1. 核心职责 (Core Responsibilities)

Reviewer Agent 充当持续集成 (CI) 中的**智能门禁**。它不仅检查语法错误（这是 Linter 的工作），更专注于：

1. **逻辑漏洞**：如并发竞争条件、未处理的边界情况。
2. **安全风险**：SQL 注入、敏感数据泄露 (PII)、越权访问。
3. **语义一致性**：代码实现是否偏离了函数命名或注释的意图。

## 2. 运作机制 (Operational Mechanism)

通常以 **Pipeline** 模式运行：

1. **Input**: 接收标准输入 (Stdin) 中的 `git diff` 或文件内容。
2. **Analyze**: 结合 System Prompt 中的安全规则库进行模式匹配。
3. **Output**: 生成结构化的评审报告，明确指出 [BLOCKER] 级别的问题。

## 3. 交互示例 (Interaction Example)

**User**:

> (Pipe `git diff`)

**Agent (Reviewer)**:

> 🚨 **Security Audit Failed**
>
> 1. **[CRITICAL] SQL Injection Risk**
>    - File: `src/user_dao.py`
>    - Line: 45 `query = "SELECT * FROM users WHERE name = '" + user_input + "'"`
>    - _Advice_: 必须使用参数化查询 (Parameterized Query)。
> 2. **[NIT] Hardcoded Configuration**
>    - File: `src/config.py`
>    - Line: 12 `API_KEY = "sk-12345..."`
>    - _Advice_: 建议移至环境变量或 Secrets Manager。
>
> **Summary**: 1 Critical, 1 Nit. 建议修复 Critical 问题后再次提交。

## 4. 提示词源码 (System Prompt Source)

见 [reviewer.md](../../.agent/roles/reviewer.md)
