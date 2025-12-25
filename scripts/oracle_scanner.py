#!/usr/bin/env python3
"""
Oracle Scanner - Phase 0 of The Crucible

Analyzes a target document and generates search queries for external fact-checking.
Outputs are project-isolated and include summary extraction.
"""
import sys
from pathlib import Path
from datetime import datetime

# Adjust path to include project root
current_dir = Path(__file__).parent
project_root = current_dir.parent
sys.path.append(str(project_root))

from llm.client import LLMClient

# Oracle Scanner Prompt
ORACLE_SCAN_PROMPT = """
You are the "Oracle Scanner". Your job is to analyze the input document and identify CRITICAL uncertainties that require external verification.

Target Document:
{target_content}

Instructions:
1. Identify 3-5 specific technical claims, assumptions, or market data points in the text that might be outdated or hallucinatory.
2. Formulate a precise "Search Query" for each.
3. Explain WHY this needs verification (The "Risk").

Output Format (Markdown):
## 🔮 Oracle Search Request
**Target**: `{filename}`
**Date**: {date}

### 1. [Query Topic]
- **Risk**: Why verify this?
- **Search Query**: `exact search keywords`

### 2. [Query Topic]
...
"""

SUMMARY_PROMPT = """
You are a knowledge archivist. Given a list of Oracle search requests from multiple sessions, extract a consolidated summary of the key knowledge gaps and recurring themes.

Input:
{all_requests}

Output a concise summary (max 200 words) in Markdown format:
## 📋 Oracle Request Summary
**Document**: {target_name}
**Sessions Analyzed**: {session_count}

### Key Knowledge Gaps
- ...

### Recurring Themes
- ...
"""

def get_project_isolated_path(target_path: Path, base_dir: str) -> Path:
    """Generate a project-isolated path consistent with docs/reports/ structure."""
    try:
        rel_from_root = target_path.relative_to(project_root)
        rel_dir = rel_from_root.parent
        # Remove redundant 'docs' prefix if present
        if rel_dir.parts and rel_dir.parts[0] == 'docs':
            rel_dir = Path(*rel_dir.parts[1:])
    except ValueError:
        rel_dir = Path("external")
    
    return project_root / "docs" / base_dir / rel_dir / target_path.stem


def update_summary(req_dir: Path, target_name: str):
    """Update the summary.md file with insights from all request files."""
    request_files = sorted(req_dir.glob("request_*.md"))
    if not request_files:
        return
    
    # Collect all request contents
    all_contents = []
    for rf in request_files[-5:]:  # Only last 5 for efficiency
        all_contents.append(rf.read_text(encoding='utf-8'))
    
    combined = "\n\n---\n\n".join(all_contents)
    
    client = LLMClient(context_id="oracle_summary")
    response = client.chat(
        messages=[
            {"role": "user", "content": SUMMARY_PROMPT.format(
                all_requests=combined[:8000],
                target_name=target_name,
                session_count=len(request_files)
            )}
        ],
        provider="deepseek",
        model="deepseek-chat",
        temperature=0.2
    )
    
    summary_file = req_dir / "summary.md"
    summary_file.write_text(response.content, encoding='utf-8')
    print(f"📋 Summary updated: {summary_file}")


def scan_for_questions(target_file: str):
    target_path = Path(target_file).absolute()
    if not target_path.exists():
        print(f"Error: File {target_path} not found.")
        sys.exit(1)
        
    content = target_path.read_text(encoding='utf-8')
    
    client = LLMClient(context_id="oracle_scanner")
    
    print(f"🔮 Scanning {target_path.name} for knowledge gaps...")
    
    response = client.chat(
        messages=[
           {"role": "user", "content": ORACLE_SCAN_PROMPT.format(
               target_content=content[:10000],
               filename=target_path.name,
               date=datetime.now().strftime("%Y-%m-%d")
           )} 
        ],
        provider="deepseek",
        model="deepseek-chat",
        temperature=0.3
    )
    
    # Output to stdout
    print("\n" + "="*50)
    print(response.content)
    print("="*50 + "\n")
    
    # Save to project-isolated path
    req_dir = get_project_isolated_path(target_path, "oracle_requests")
    req_dir.mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    req_file = req_dir / f"request_{timestamp}.md"
    req_file.write_text(response.content, encoding='utf-8')
    print(f"✅ Request saved to: {req_file}")
    
    # Update summary
    update_summary(req_dir, target_path.name)
    
    # Also create/update a 'latest.md' symlink-like file for easy access
    latest_file = req_dir / "latest.md"
    latest_file.write_text(response.content, encoding='utf-8')
    print(f"🔗 Latest request: {latest_file}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python oracle_scanner.py <target_file>")
        sys.exit(1)
    scan_for_questions(sys.argv[1])
