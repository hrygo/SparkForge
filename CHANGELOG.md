# Changelog

All notable changes to this project will be documented in this file.

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
