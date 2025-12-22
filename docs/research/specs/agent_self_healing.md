# Agent Specification: Self-Healing Agent

> **Role**: UI 自动化测试自愈专家
> **Runtime**: Claude Code (CLI)
> **Trigger**: `claude -p .agent/roles/self_healing.md`

## 1. 核心职责

解决 UI 测试“脆弱”的问题。当 DOM 结构变化导致 Selector 失效时，自动修复测试脚本。

## 2. 运作机制

1. **失效捕获**: 监听 Selenium/Playwright 的 `NoSuchElementException`。
2. **元素重定位**: 利用多模态（视觉截图 + HTML 源码）寻找“最相似”的元素。
3. **脚本热修**: 更新测试脚本中的 Selector。

## 3. 产出物标准

自动修复的 Commit：

```diff
- driver.find_element(By.ID, "submit-btn-v1")
+ driver.find_element(By.CSS_SELECTOR, ".btn-primary.submit") // AI Auto-fixed
```
