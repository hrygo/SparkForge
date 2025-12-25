---
description: The Crucible - Iterative design refinement with Oracle-grounded Council debate.
---

# The Crucible

// turbo-all

The Crucible is SparkForge's core refinement protocol. It fuses **Oracle** (external fact-grounding) with **The Council** (internal dialectical debate) in an iterative loop until industrial-grade quality is achieved.

## Parameters

- `target`: Path to the document to be refined.
- `max_loops`: (Optional) Maximum iteration cycles. Default: 3.

## Directory Structure (Project-Isolated)

All outputs are organized by target document:

```
docs/
├── oracle_requests/{path}/{stem}/
│   ├── request_20251225_160534.md   ← Individual request
│   ├── latest.md                     ← Most recent request
│   └── summary.md                    ← Consolidated summary
├── knowledge/{path}/{stem}/
│   ├── facts_20251225_160534.md      ← Individual search results
│   ├── latest.md                     ← Most recent facts
│   └── summary.md                    ← Consolidated summary
└── reports/{path}/{stem}/
    ├── debate_20251225_160534.md     ← Debate report
    └── history_summary.md            ← Historical verdicts
```

Where `{path}` is the relative path from `docs/` and `{stem}` is the filename without extension.

---

## Phase 0: Oracle Scanning

Identify knowledge gaps in the target document.

```bash
python3 scripts/oracle_scanner.py {target}
```

- **Output**: `docs/oracle_requests/{path}/{stem}/request_{timestamp}.md`
- **Summary**: Auto-updated at `docs/oracle_requests/{path}/{stem}/summary.md`

---

## Phase 1: Knowledge Retrieval (Agent Action)

**[AGENT ACTION]**: Read `docs/oracle_requests/{path}/{stem}/latest.md` and use `search_web` to find:

- Official Documentation / RFCs
- SOTA Benchmarks (within last 12 months)
- Known Vulnerabilities (CVEs)
- Comparative analyses

**[AGENT ACTION]**: Write findings to `docs/knowledge/{path}/{stem}/facts_{timestamp}.md`.

- Format: Markdown with bullet points and source links.
- Tone: Objective, purely factual.

**[AGENT ACTION]**: Update `docs/knowledge/{path}/{stem}/summary.md` with consolidated insights.

---

## Phase 2: Council Debate

Run the debate with Oracle knowledge injected.

```bash
python3 scripts/dialecta_debate.py {target} \
  --ref docs/reports/{path}/{stem}/history_summary.md \
  --oracle docs/knowledge/{path}/{stem}/latest.md \
  --instruction "{CurrentOptimizationObjective}" \
  --loop {CurrentLoopIndex} \
  --cite
```

- **Affirmative (Qwen)**: Defends the proposal's value.
- **Negative (DeepSeek)**: Audits risks, weaponizes Oracle facts.
- **Adjudicator (GLM)**: Final verdict with weighted scoring.

---

## Phase 3: Verify Consistency & Convergence

Read the generated report and evaluate:

1. **Weighted Score Analysis**:
   - Strategic Alignment (40%)
   - Practical Value (30%)
   - Logical Consistency (30%)

2. **Convergence Rules**:
   - **If Delta < -10**: **STOP & ROLLBACK** to previous backup.
   - **If Delta < 5 for 2 loops**: **STASIS DETECTED** → Escalate or ask User.
   - **If Score >= 90 AND Verdict = "Approved"**: **SUCCESS** → Exit.

---

## Phase 4: Snapshot Backup

Before applying changes, create safety snapshots:

1. Ensure `docs/backup/{stem}/` exists.
2. Copy:
   - Target document → `{Filename}_backup_{Timestamp}.md`
   - History summary → `{Filename}_history_backup_{Timestamp}.md`

---

## Phase 5: Apply Changes (The Surgeon)

1. **Existence Guard**: Verify critiques refer to actual text. Discard hallucinated critiques.
2. **Objective Check**: Ensure edits don't compromise the Initial Objective.
3. **Apply Edits**: Based on Adjudicator's `Mending Orders`.
4. **Impact Summary**: Generate a "Change Impact Matrix" for the next loop.

---

## Phase 6: Loop Decision

1. **Update History**: Append results to `history_summary.md`.
2. **Check Exit Conditions**:
   - **Success**: Score >= 90 AND Verdict = "Approved".
   - **Timeout**: Loop >= max_loops.
   - **Anomaly**: Flip-flop or persistent stasis detected.
3. **If no exit condition met**: Return to **Phase 0** for the next cycle.

---

## Exit

When the loop exits:

1. Archive the final report.
2. Notify the User with final score and verdict.
3. If successful, the document is ready for review via **Gatekeeper Approval**.
