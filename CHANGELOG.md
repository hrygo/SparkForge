# Changelog

All notable changes to this project will be documented in this file.

## [2.0.0] - 2025-12-25

### 🚀 Major Release: The Crucible Engine

SparkForge 2.0 "The Crucible" 正式发布。本次更新完成了从单纯的文档生成器向 **高保真认知熔炉** 的战略转型，引入了外部事实锚定与多智能体对抗辩论的完整闭环。

### Added

- **The Crucible Workflow**: 全新的核心工作流 (`.agent/workflows/crucible.md`)，集成了 Oracle Scanning、Council Debate、Adjudication、Surgical Action 四大阶段。
- **Oracle Scanner**: 新增 `scripts/oracle_scanner.py`，能够自动识别文档知识盲区，执行网络搜索，并将结构化事实注入本地知识库 (`docs/knowledge/`)。
- **Dialecta Debate 2.0**: 辩论引擎升级，支持基于 Oracle 知识库的 **Fact-Grounded Attack** (事实锚定攻击)，彻底消除了 AI "闭门造车" 的幻觉风险。
- **RACI With R-Prime**: 在方法论报告中成功实践了带有 "R-Prime" (主责人) 与 "Tiered Escalation" (分级升级) 的新型 RACI 矩阵。
- **Audit Trails**: 新增 `history_summary.md` 自动追踪每一次循环的决策演变与得分趋势。

### Changed

- **文档架构重组**:
  - 废弃 `docs/backup/` 的扁平结构，改为 `docs/reports/{Target}/` 的项目隔离结构。
  - `prompts/` 目录结构化，分离 `adjudicator`, `negative`, `affirmative` 等角色定义。
- **PDF 导出升级**: 支持 Mermaid 图表的语义化 Emoji 与高对比度渲染。

### Verified

- **员工画像方法论报告**: 作为 2.0 版本的首个验证对象，该报告在 Loop 4 中通过了 92 分的高分验收，证明了 Crucible 流程的实战价值。

## [1.1.1] - 2025-12-24

### Fixed

- **依赖审计与清理**: 审计并补全了 `requirements.txt` 中遗漏的 `Markdown`, `pikepdf`, `Jinja2` 关键依赖，并移除了冗余的 `google-generativeai` 库。

## [1.1.0] - 2025-12-24

### Added

- **MathJax 公式支持**: 实现了在 PDF 转换中对 LaTeX 公式的渲染支持，确保技术文档中的数学表达精确呈现。
- **LLM 客户端弹性增强**: 新增重试与 Fallback 机制。实现了 Provider 级联回退 (Sticky Fallback)，提升了长任务的稳定性。

### Changed

- **样式优化**: 调整了引用块 (Blockquote) 的样式。
- **文档更新**: 同步更新 README 与 PRD 文档。

## [1.0.4] - 2025-12-23

### Added

- **深度锻造模式 (彩蛋)**: 在 `README.md` 中揭示了隐藏指令——使用 **"锻造"** 关键词即可触发更严苛的工业级审查模式。
- **CLI 示例增强**: 进一步优化了自动化优化循环的指令示例，添加了带有 "锻造" 意图的实战 Case。

## [1.0.3] - 2025-12-23

### Added

- **文档发布闭环**: 在 `README.md` 中新增 **"导出发布级 PDF"** 章节，详细引导用户使用 `scripts/pdf_tool` 生成高质量 A4 报告与长图，补全了从优化到发布的最后一块拼图。

## [1.0.2] - 2025-12-23

### Changed

- **PRD 术语规范化**: 在 `PRD_Spec_Builder.md` 中将 "智能 IDE"、"Cursor"、"Copilot" 等特定厂商词汇统一替换为中立的 **"AI Coder"**，以突显平台中立性。
- **术语表增强**: 新增 **Spec** (规格)、**SDD** (规格驱动开发) 标准定义，并细化 **BizDevOps** 为"企业级全生命周期研发管理平台"。
- **架构图布局优化**: 重构 PRD 3.1 节功能架构图为 **2x2 矩阵布局**，完美适配 A4 纸张比例，避免垂直方向过长。
- **CLI 使用体验**: 优化 `README.md` 中 `/optimize-design-loop` 的使用示例，清晰区分 "上下文模式" 与 "指定文件模式"。

## [1.0.1] - 2025-12-19

### Changed

- **Makefile 逻辑解耦**: 将 PDF 签名由自动触发改为手动执行 (`make sign`)，确保签名操作在人工审计后进行。
- **CLI 交互优化**: 更新了 `make help` 的指令说明与示例，提升了 PDF/Security 模块的易用性。

### Fixed

- **文档补充**: 在 README.md 中增加了 `phantom-guard` 工具的安装引导及 GitHub 获取地址。
- **安装指导**: 明确了签名工具为可选组件，避免非必要安装。

## [1.0.0] - 2025-12-19

### Added

- **安全审计与签名 (PhantomGuard)**: Makefile 集成 PDF 自动安全签名机制，支持自定义追踪信息。
- **现代化 CLI 界面**: 重构 Makefile，支持带颜色的分组指令与更友好的示例引导。

- **SparkForge-3 协议**: Expansion, Validation, Action 的工业级文档演进流程。
- **The Council (AI 理事会)**: 基于多模型对抗的文档语义审计系统。
- **Dialecta 辩论引擎**: 支持并行并发认知博弈与引文真实性校验。
- **质量控制体系**: 集成 `markdownlint` 与 `prettier`，确保文档工业级整洁。
- **自动化 PDF 导出**: 支持多种视觉样式的 A4 报告与长图导出。
- **原子化安全机制**: 完整的备份与分值骤降回滚逻辑。
- **GitHub 集成**: 脱敏发布流程与 Git 排除策略。

### Optimized

- **Mermaid 架构图**: 全面支持 GitHub 暗黑模式。
- **LLM 推理中枢**: 深度集成 Gemini 3 Pro、DeepSeek-V3 等主流模型。
- **工作流编排**: 实现滚动历史裁剪与认知补丁机制。
