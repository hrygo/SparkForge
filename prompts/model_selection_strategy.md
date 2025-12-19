# 🧠 SparkForge Council: Model Orchestration Strategy

本文档详细阐述了 SparkForge **"Council" (三方会谈)** 架构中，针对不同角色（Role）的模型选型逻辑、参数配置策略以及设计初衷。

---

## 1. 核心设计哲学：思维异构 (Think Heterogeneously)

为了避免单一模型家族（如全部使用 GPT 系列）带来的思维同质化盲区，我们采用了 **"模型联邦" (Model Federation)** 策略。通过组合不同技术基因、不同训练偏好、甚至不同文化背景（中美模型混用）的顶级 LLM，构建一个多维度的认知网络。

![Strategy](https://mermaid.ink/img/pako:eNpVkMtqwzAQRX9FzKpFIPjQRbFJoS10100XTTEejS1lI8tGMqGE_HutaJPsbnbOuXfuCGa1IhIwflp9m1f17m29_V48L5_L5-p197K6Oyy_D_dfx-P74em0A-NcCymQ4zhMeZp8yJIkTvI4S_M0z7I8e0-zNMuK4j1N86IoyvcoK4qi_IiyqijKn6q6qqr6E9raGmtc40wI7ZwH4wM655ALpXUwLvhAzhunXQgGfPTkQjDe-8A4b00wDq13PniD7KMGQx5kP1roUYZBfa3RkEP9SKMhT_qRRkOe9CONhjzpRxoNedKPNBrypB9pNORJP9JoyJN-5B81GvK0H_k_zJv-5H8x7_qT_8O860_-D_OuP_k_zLv-5P8w7_qT_8O8b9-sX1i2l1c?type=png)

---

## 2. 角色阵营与模型配置 (Role Configuration)

### ✊ 正方：战略支持者 (The Affirmative)

- **选型模型**: **Google Gemini 3.0 Pro**
- **核心任务**: 挖掘价值、跨界联想、构建愿景。
- **选型逻辑**:
  - **联想力 (Association)**: Gemini 系列拥有最强的多模态底座和长窗口记忆，极擅长发散性思维和跨学科知识迁移。
  - **创造性 (Creativity)**: 相比其他模型，Gemini 在生成建设性、启发性内容时表现出更高的热情和多样性。
- **参数策略**:
  - `Temperature = 0.9`: 高温设置，鼓励模型跳出常规逻辑，寻找边缘创新点。
  - `Top_P = 0.95`: 保持词汇选择的丰富性。

### 👊 反方：风险控制官 (The Negative)

- **选型模型**: **DeepSeek-V3**
- **核心任务**: 逻辑查错、压力测试、寻找死角。
- **选型逻辑**:
  - **纯理性 (Pure Logic)**: DeepSeek 拥有极强的 Coding/Math 基因，思维方式接近编译器，对逻辑断层极其敏感。
  - **冷峻 (Cold-blooded)**: 它不擅长“端水”，直击痛点的能力远超经过过度 RLHF (人类反馈对齐) 的欧美模型。
- **参数策略**:
  - `Temperature = 0.6`: 中低温设置，抑制幻觉，确保反驳基于坚实的逻辑链条而非情绪宣泄。
  - `Provider`: `deepseek` (直连以保证原汁原味的推理能力)。

### ⚖️ 裁判：首席裁决官 (The Adjudicator)

- **选型模型**: **Zhipu GLM-4.6** (via SiliconFlow)
- **核心任务**: 综合权衡、深度决断、行动规划。
- **选型逻辑**:
  - **慢思考 (System 2)**: GLM-4.6 具备类似 o1 的深度推理能力，适合处理需要多步权衡的裁决任务。
  - **中正平和 (Balance)**: 在中文语境下，GLM 对"言外之意"和"文化潜台词"的理解力最强，能很好地平衡激进与保守的观点。
  - **Agent Native**: 极强的指令遵循能力，确保产出的裁决报告严格符合结构化要求。
- **参数策略**:
  - `Temperature = 0.2`: 极低温设置，要求裁判绝对冷静、客观，输出稳定可复现的结果。

---

## 3. 动态参数与配置管理

所有配置均已解耦至 `prompts/*.md` 文件的 **YAML Front Matter** 中，实现了“Prompt 即配置” (Configuration as Code)。

### 示例结构

```yaml
---
model_config:
  provider: gemini
  model: gemini-3.0-pro-preview
  temperature: 0.9 # 高创造性
  max_tokens: 8192 # 允许长篇论证
---
### Role
Draft content...
```

### 调整指南

1. **如果正方不够兴奋**: 提高 Gemini 的 `temperature` 至 1.0，或尝试 Grok (OpenRouter)。
2. **如果反方攻击性不足**: 确认使用的是 DeepSeek 原生接口，避免中间商的 System Prompt 干扰。
3. **如果裁判逻辑混乱**: 降低 GLM 的 `temperature` 至 0.1，或开启思维链模式。

---

> **SparkForge Principle**: 我们不相信单一的“最强模型”，我们相信只有**正确的模型放在正确的位置**，才能涌现出超越个体的群体智慧。
