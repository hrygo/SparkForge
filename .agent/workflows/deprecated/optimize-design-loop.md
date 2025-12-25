---
description: Run an iterative design optimization loop using The Council (Dialecta) with human-in-the-loop application.
---

# Design Optimization Loop

// turbo-all

This workflow guides you through the process of refining the design draft using AI debates and consistency checks, with a focus on observability and stability.

## Parameters

- `max_loops`: (Optional) Maximum number of iteration cycles. Default: 3.

## 🧠 战略意图 (Strategic Intent)

本工作流并非为了观察 AI 之间的“斗争”，而是利用对抗性思维作为**质量杠杆**。理事会（The Council）被赋予“上帝视角”，其唯一目标是协助用户锻造出具备工业级可执行性的卓越文档。

## Process Overview

1. **Extract History**: Agent intelligently summarizes past debate verdicts.
2. **Convene**: The AI Council debates the current draft.
3. **Monitor**: Real-time status with throttled updates (avoiding noise).
4. **Verify**: Flip-Flop detection.
5. **Apply & Loop**: Apply changes and loop if conditions met.

## Step-by-Step Instructions

### Step 1: Compress History Context (Agent Task)

**Before starting**: Check `docs/reports/{TargetFile}/` for recent debate reports.

- **Task**: Read the most recent 2-3 debate reports for the target file.
- **Action**: Create or Update `docs/reports/{EffectiveRelativePath}/{TargetFileStem}/history_summary.md`.
  - _Path Rule_: If the target file is in `docs/` (e.g., `docs/MyFile.md`), `{EffectiveRelativePath}` is empty (i.e., `docs/reports/MyFile/`). If in `src/utils/`, it remains `src/utils`. This prevents `docs/reports/docs/...`.
  - _Requirement_: You **MUST** capture the **User's Initial Objective** and persistent constraints.
  - _Rolling Pruning_: Maintain only the latest **3 loops** in full detail. Older loops must be collapsed into a "Legacy Context Summary" to prevent context noise.
  - _Format_:
    1. `# Initial Optimization Objective`: The verbatim initial request.
    2. `## Chronological Verdicts`: Recent 3 loops table.
    3. `## Persistent Constraints`: Key rules.
    4. `## Legacy Context Summary`: Condensed insights from early iterations.

### Step 2: Convene The Council

Run the debate script. The Council is now primed with a **Strategic Directive** (God's eye view):

- **Strategic Priming**: Prioritize core architectural integrity over pedantic details.
- **Precision Cooling** (退火策略):
  - If `Loop > 5`, instruct models to prioritize logical consistency and document stability.
- **Evidence Requirement**: Explicitly instruct the Adjudicator to provide **line citations or specific quotes** for every critique.

```bash
# Optimized CLI call using Structured Parameters
# {EffectiveRelativePath} follows the Path Rule defined in Step 1
python3 scripts/dialecta_debate.py {path/to/your_document.md} \
  --ref docs/reports/{EffectiveRelativePath}/{TargetFileStem}/history_summary.md \
  --instruction "{CurrentOptimizationObjective}" \
  --loop {CurrentLoopIndex} \
  --cite
```

### Step 3: Verify Consistency & Convergence (Agent Logic)

Read the new report.

1. **Multi-Criteria Scoring Analysis**:
   - Evaluate the Verdict based on a weighted matrix:
     - **Strategic Alignment (40%)**: Does it meet the Initial Objective?
     - **Practical Value (30%)**: Are the suggestions actionable?
     - **Logical Consistency (30%)**: Does it maintain internal coherence?
   - Calculate the **Weighted Score** and its **Delta**.

2. **Convergence Tracking**:
   - **If Delta < -10 (Negative Delta)**: **STOP & ROLLBACK**. Revert **both** the Target Document and its `history_summary.md` to the previous snapshot from the backup folder.
   - **If Delta < 5 for 2 loops**: **STASIS DETECTED**. Flag this in the report and attempt a different tactical approach in Step 5.

3. **Flip-Flop & Blockage Check**:
   - Ensure issues aren't oscillating or persisting (Advice Counter).

### Step 4: Snapshot Backup (Safety)

**Role**: Ensure roll-back capability before surgical changes.

- **Action**:
  1. Ensure `docs/backup/{TargetFileStem}/` directory exists.
  2. Copy the current **Target Document** AND its corresponding `history_summary.md` (from `docs/reports/...`) to this folder.
  3. **Naming Convention**:
     - Target: `{Filename}_backup_{Timestamp}.md`
     - History: `{Filename}_history_backup_{Timestamp}.md`

### Step 5: The Surgeon (Agent Intelligence - CRITICAL)

**This is the core value add.** This is NOT a mechanical task; it requires deep thinking and strategic planning.

1. **Pre-edit Logical Verification (The Sandbox)**:
   - **Existence Guard (Anti-Hallucination)**: Check if the Adjudicator's critiques actually refer to existing text. If a critique refers to a non-existent flaw, discard it and flag it in the Impact Summary.
   - **Objective Check**: Ensure the fix doesn't compromise the **Initial Optimization Objective**.

2. **Standard Mode (Standard Repair)**:
   - Reflect on the **裁决详情 (Detailed Verdict)** and plan edits across the document.

3. **Deep Reflection Mode (Escalation/Regression)**:
   - **Trigger**: Triggered by Blockage (Count >= 2) or Negative Delta Rollback.
   - **Strategy**: Perform a **structural reconstruction**.
   - **Self-Correction**: Analyze why previous attempts failed or why the score dropped. Double-check the logic chain.

4. **Impact Summary (Crucial)**:
   - After the edit, generate a concise **"Change Impact Matrix"** (e.g., _Section X: Improved tone to be more strategic; Section Y: Resolved vendor-logic conflict_).
   - **Action Trace**: Explicitly state which debate point prompted which change. This summary will guide the Adjudicator in the next round by being appended to the context.

5. **Conflict Resolution**:
   - If a new suggestion contradicts a previous decision or the initial objective, perform deep reasoning to determine the superior path. Increment the "arbitration count" to detect logic loops.

### Step 6: State Update & Loop Decision (The Driver)

1. **Update History**:
   - Append the latest result (Version, Score, Delta, Key Changes) to `docs/reports/{RelativePath}/{TargetFileStem}/history_summary.md`.
   - **New Section**: Update `## Legacy Context Summary` by condensing the previous version's impact into a one-line **"Version Delta"** to preserve evolution context without bloating history.
   - **Action Trace**: Ensure the "Change Impact Matrix" from Step 5 is archived here.
2. **Check Exit Conditions**:
   - **Condition A (Success)**: Score >= 90 AND Verdict matches "Approved" or "直接通过". -> **STOP**.
   - **Condition B (Timeout)**: `Current_Loop` >= `max_loops`. -> **STOP**.
   - **Condition C (Anomaly)**: **Flip-Flop** or **Persistent Stasis** detected. -> **STOP** and ask User.
3. **The Next Move**:
   - **IF NO EXIT CONDITION MET**: Trigger Step 2.
   - _Agent Directive_: You are authorized to proceed automatically. Carry the Initial Objective.
