---
description: Council Debate with Human-Agent-Oracle Loop
---

# Council Debate with Oracle Integration

This workflow implements the "Duplex Collaboration System" where the Agent (Antigravity) acts as the bridge between the internal debate council and the external web.

## Phase 1: Oracle Scanning (Internal)

1. Run the Oracle Scanner to identify knowledge gaps in the target document.
   ```bash
   python3 scripts/oracle_scanner.py <target_file>
   ```
2. Read the generated request at `docs/oracle_requests/latest_request.md`.

## Phase 2: Knowledge Retrieval (Agent Action)

3. **[AGENT ACTION]**: Based on the request in `latest_request.md`, use your `search_web` tool to find the requested information. Focus on:
   - Official Documentation / RFCs
   - SOTA Benchmarks (within last 12 months)
   - Known Vulnerabilities (CVEs)
   - "Vs" Comparisons (e.g., Qwen vs DeepSeek)

4. **[AGENT ACTION]**: Summarize your findings into a new file: `docs/knowledge/current_session_facts.md`. 
   - Format: Markdown.
   - Content: Bullet points with source links.
   - Tone: Objective, purely factual.

## Phase 3: Council Debate (Internal)

5. Run the debate script with the Oracle knowledge injected.
   ```bash
   python3 scripts/dialecta_debate.py <target_file> --oracle docs/knowledge/current_session_facts.md
   ```

6. Review the generated report. If the Council identifies FURTHER gaps, repeat Phase 2.
