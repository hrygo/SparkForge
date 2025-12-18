---
description: Run an iterative design optimization loop using The Council (Dialecta) with human-in-the-loop application.
---

# Design Optimization Loop
// turbo-all

This workflow guides you through the process of refining the design draft using AI debates and consistency checks, with a focus on observability and stability.

## Parameters
*   `max_loops`: (Optional) Maximum number of iteration cycles. Default: 3.

## Process Overview

1.  **Extract History**: Agent intelligently summarizes past debate verdicts.
2.  **Convene**: The AI Council debates the current draft.
3.  **Monitor**: Real-time status with throttled updates (avoiding noise).
4.  **Verify**: Flip-Flop detection.
5.  **Apply & Loop**: Apply changes and loop if conditions met.

## Step-by-Step Instructions

### Step 1: Compress History Context (Agent Task)

**Before starting**: Check `docs/reports/{TargetFile}/` for recent debate reports.

*   **Task**: Read the most recent 2-3 debate reports for the target file.
*   **Action**: Create or Update `docs/reports/{TargetFile}/history_summary.md`.
    *   *Format*: A chronological list of "Verdicts", "Key Decisions", and "Pending Issues".
    *   *Goal*: This file serves as the "Common Law" (判例法) and context for the next debate cycle.

### Step 2: Convene The Council

Run the debate script which now utilizes `llm` and `prompts` packages for "Configuration as Code".

```bash
# Basic usage with History Context
# Note: Always pass history_summary.md as the reference if no other spec exists, 
# or concatenate them if needed.
python3 scripts/dialecta_debate.py {path/to/your_document.md} \
  --ref docs/reports/{TargetFile}/history_summary.md \
  --instruction "基于历史判例进行审查，避免重复已解决的问题。"
```

### Step 3: Verify Consistency (Agent Logic)

Read the new report (path printed at end of Step 2).
Compare "Verdict" against `docs/reports/{TargetFile}/history_summary.md`.

*   **Flip-Flop Check**:
    *   **If FLIP-FLOP DETECTED**: STOP. Inform user.
    *   **If CONSISTENT**: Proceed.

### Step 4: Snapshot Backup (Safety)

**Role**: Ensure roll-back capability before surgical changes.

*   **Action**:
    1.  Ensure `docs/backup/{TargetFile}/` directory exists.
    2.  Copy the current **Target Document** (the file being optimized) to this folder.
    3.  **Naming Convention**: Use the format `{Filename}_backup_{Timestamp}.md`. (e.g., `Strategy_backup_20251218_120000.md`).

### Step 5: The Surgeon (Agent Intelligence - CRITICAL)

**This is the core value add.** This is NOT a mechanical task; it requires deep thinking and strategic planning.
1.  **Deep Synthesis & Planning**: Do not jump into editing. Reflect on the *Full Verdict* and evaluate how the suggestions impact the document's overall coherence and quality. Plan your edits across the entire document to ensure logical self-consistency.
2.  **Strategy Formulation**:
    *   **Prioritize**: Distinguish between "Critical Blockers" and "Stylistic Enhancements".
    *   **Conflict Resolution**: If a new suggestion contradicts a previous decision tracked in `docs/reports/{TargetFile}/history_summary.md`, perform deep reasoning to determine the superior path. Explicitly document your reasoning to prevent future Flip-Flops.
3.  **Surgical Execution**: Implement your plan using the `multi_replace_file_content` or `rewrite_file` tool.
    *   *Guideline*: Be bold. If the Adjudicator identifies a structural weakness, aim for a high-quality reconstruction rather than a minor patch. Ensure the tone remains professional and objective.

### Step 6: State Update & Loop Decision (The Driver)

1.  **Update History**: Append the latest result (Draft Version, Score, Key Changes) to `docs/reports/{TargetFile}/history_summary.md`.
2.  **Check Exit Conditions**:
    *   **Condition A (Success)**: Adjudicator Score >= 90 AND Verdict == "Approved". -> **STOP**.
    *   **Condition B (Timeout)**: `Current_Loop` >= `max_loops`. -> **STOP**.
    *   **Condition C (Anomaly)**: **Flip-Flop Detected** (The same issue is oscillating between two states across 3+ runs). -> **STOP** and ask User for arbitration.
3.  **The Next Move**:
    *   **IF NO EXIT CONDITION MET**: **IMMEDIATELY** trigger Step 2 again. (Self-Correction Loop).
    *   *Agent Directive*: You are authorized to proceed to the next loop automatically if within limits.
