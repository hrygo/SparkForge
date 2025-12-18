#!/usr/bin/env python3
import sys
import os
import argparse
from pathlib import Path
from datetime import datetime

# Adjust path to include project root for imports
current_dir = Path(__file__).parent
project_root = current_dir.parent
sys.path.append(str(project_root))

from llm import LLMClient
from prompts.templates import (
    AffirmativeConfig, AffirmativePrompt,
    NegativeConfig, NegativePrompt,
    AdjudicatorConfig, AdjudicatorPrompt
)

def read_file(path: str) -> str:
    try:
        return Path(path).read_text(encoding='utf-8')
    except Exception as e:
        print(f"Error reading {path}: {e}")
        return ""

def run_debate(target_file: str, reference_file: str = "", instruction: str = ""):
    client = LLMClient()
    
    target_content = read_file(target_file)
    ref_content = read_file(reference_file) if reference_file else "无参考文档"
    
    # Construct Context
    context_blocks = []
    if instruction:
        context_blocks.append(f"【用户临时指令/特别关注】\n{instruction}")
    
    context_blocks.append(f"【参考背景】\n{ref_content}")
    context_blocks.append(f"【待审材料】\n{target_content}")
    
    user_input = "\n\n".join(context_blocks)
    
    # 1. Affirmative Phase
    print(f"🚀 [Affirmative] Engaging {AffirmativeConfig.get('provider')}...")
    
    affirmative_resp = client.chat(
        messages=[
            {"role": "system", "content": AffirmativePrompt},
            {"role": "user", "content": user_input}
        ],
        **AffirmativeConfig
    )
    print("✅ Affirmative argument generated.")

    # 2. Negative Phase
    print(f"🛡️ [Negative] Engaging {NegativeConfig.get('provider')}...")
    negative_resp = client.chat(
        messages=[
            {"role": "system", "content": NegativePrompt},
            {"role": "user", "content": user_input}
        ],
        **NegativeConfig
    )
    print("✅ Negative argument generated.")

    # 3. Adjudicator Phase
    print(f"⚖️ [Adjudicator] Engaging {AdjudicatorConfig.get('provider')}...")
    adjudicator_input = f"""
【待审材料】
{target_content}

【正方观点】
{affirmative_resp.content}

【反方观点】
{negative_resp.content}
"""
    adjudicator_resp = client.chat(
        messages=[
            {"role": "system", "content": AdjudicatorPrompt},
            {"role": "user", "content": adjudicator_input}
        ],
        **AdjudicatorConfig
    )
    print("✅ Final verdict reached.")

    # Save Report
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    target_p = Path(target_file)
    # Create sub-directory based on target filename (sans extension)
    report_tag = target_p.stem
    report_dir = project_root / "docs" / "reports" / report_tag
    report_dir.mkdir(parents=True, exist_ok=True)
    report_path = report_dir / f"debate_{timestamp}.md"
    
    report_content = f"""# Council Debate Report
**Date**: {timestamp}
**Target**: `{target_file}`
**Ref**: `{reference_file}`

---

## ✊ Affirmative ({AffirmativeConfig.get('model')})
{affirmative_resp.content}

---

## 👊 Negative ({NegativeConfig.get('model')})
{negative_resp.content}

---

## ⚖️ Adjudicator ({AdjudicatorConfig.get('model')})
{adjudicator_resp.content}
"""
    report_path.write_text(report_content, encoding='utf-8')
    print(f"\n📄 Report saved to: {report_path}")
    return report_path


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="SparkForge Council Debate CLI")
    parser.add_argument("target", help="Path to the document to be optimized")
    parser.add_argument("--ref", help="Path to reference document (optional)", default="")
    parser.add_argument("--instruction", "-i", help="Temporary user instruction or focus area (optional)", default="")
    
    args = parser.parse_args()
    run_debate(args.target, args.ref, args.instruction)
