#!/usr/bin/env python3
import sys
import os
import argparse
import logging
import time
import threading
import itertools
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

# ANSI Colors for CLI
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

class ThinkingSpinner:
    def __init__(self, message="Thinking...", delay=0.1):
        self.spinner = itertools.cycle(['⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏'])
        self.delay = delay
        self.message = message
        self.running = False
        self.thread = None

    def spin(self):
        while self.running:
            # \r moves cursor to start of line
            sys.stdout.write(f"\r{Colors.CYAN}{next(self.spinner)}{Colors.ENDC} {self.message}")
            sys.stdout.flush()
            time.sleep(self.delay)

    def __enter__(self):
        self.running = True
        self.thread = threading.Thread(target=self.spin)
        self.thread.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.running = False
        if self.thread:
            self.thread.join()
        # Clear the line
        sys.stdout.write(f"\r{' ' * (len(self.message) + 4)}\r")
        sys.stdout.flush()

# Setup Logging
def setup_logging(log_dir: Path):
    log_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = log_dir / f"debate_exec_{timestamp}.log"
    
    logger = logging.getLogger("DialectaDebate")
    logger.setLevel(logging.DEBUG)
    
    # Clear handlers if any
    if logger.hasHandlers():
        logger.handlers.clear()
        
    # File Handler - Detailed & Clean (No colors codes preferably, but we might log colors if we aren't careful)
    # Ideally checking if we want to strip colors for file, but keeping it simple for now.
    fh = logging.FileHandler(log_file, encoding='utf-8')
    fh.setLevel(logging.DEBUG)
    fh_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    fh.setFormatter(fh_formatter)
    
    # Console Handler
    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(logging.INFO)
    # Simple formatter for console
    ch_formatter = logging.Formatter('%(message)s')
    ch.setFormatter(ch_formatter)
    
    logger.addHandler(fh)
    logger.addHandler(ch)
    
    return logger, log_file

def read_file(path: str, logger: logging.Logger) -> str:
    try:
        content = Path(path).read_text(encoding='utf-8')
        logger.debug(f"Read {len(content)} bytes from {path}")
        return content
    except Exception as e:
        logger.error(f"Error reading {path}: {e}")
        return ""

def format_usage(usage):
    if not usage:
        return "N/A"
    return f"In:{usage.prompt_tokens} Out:{usage.completion_tokens} Total:{usage.total_tokens}"

def run_debate(target_file: str, reference_file: str = "", instruction: str = ""):
    # Initialize infrastructure
    log_dir = project_root / "logs"
    logger, log_file_path = setup_logging(log_dir)
    
    logger.info(f"{Colors.HEADER}🏁 Starting Dialecta Debate Sequence{Colors.ENDC}")
    logger.info(f"📂 Target: {Colors.BOLD}{target_file}{Colors.ENDC}")
    logger.info(f"📝 Logs: {Colors.BOLD}{log_file_path}{Colors.ENDC}")
    
    start_time = time.time()
    usage_stats = {"affirmative": None, "negative": None, "adjudicator": None}
    time_stats = {}
    
    client = LLMClient()
    
    target_content = read_file(target_file, logger)
    ref_content = read_file(reference_file, logger) if reference_file else "无参考文档"
    
    # Construct Context
    context_blocks = []
    if instruction:
        context_blocks.append(f"【用户临时指令/特别关注】\n{instruction}")
        logger.info(f"📌 Custom Instruction: {instruction}")
    
    context_blocks.append(f"【参考背景】\n{ref_content}")
    context_blocks.append(f"【待审材料】\n{target_content}")
    
    user_input = "\n\n".join(context_blocks)
    
    # 1. Affirmative Phase
    phase_start = time.time()
    provider = AffirmativeConfig.get('provider')
    model = AffirmativeConfig.get('model')
    logger.info(f"\n{Colors.BLUE}🚀 [Affirmative]{Colors.ENDC} Engaging {provider} ({model})...")
    
    try:
        with ThinkingSpinner(f"generating affirmative arguments via {model}..."):
            affirmative_resp = client.chat(
                messages=[
                    {"role": "system", "content": AffirmativePrompt},
                    {"role": "user", "content": user_input}
                ],
                **AffirmativeConfig
            )
        usage_stats["affirmative"] = affirmative_resp.usage
        logger.info(f"{Colors.GREEN}✅ Affirmative generated.{Colors.ENDC} ({format_usage(affirmative_resp.usage)})")
        logger.debug(f"Affirmative Content:\n{affirmative_resp.content[:500]}...")
    except Exception as e:
        logger.error(f"{Colors.RED}💥 Affirmative Phase Failed: {e}{Colors.ENDC}", exc_info=True)
        return
    time_stats["affirmative"] = time.time() - phase_start

    # 2. Negative Phase
    phase_start = time.time()
    provider = NegativeConfig.get('provider')
    model = NegativeConfig.get('model')
    logger.info(f"{Colors.YELLOW}🛡️  [Negative]{Colors.ENDC} Engaging {provider} ({model})...")
    
    try:
        with ThinkingSpinner(f"generating negative arguments via {model}..."):
            negative_resp = client.chat(
                messages=[
                    {"role": "system", "content": NegativePrompt},
                    {"role": "user", "content": user_input}
                ],
                **NegativeConfig
            )
        usage_stats["negative"] = negative_resp.usage
        logger.info(f"{Colors.GREEN}✅ Negative generated.{Colors.ENDC} ({format_usage(negative_resp.usage)})")
        logger.debug(f"Negative Content:\n{negative_resp.content[:500]}...")
    except Exception as e:
        logger.error(f"{Colors.RED}💥 Negative Phase Failed: {e}{Colors.ENDC}", exc_info=True)
        return
    time_stats["negative"] = time.time() - phase_start

    # 3. Adjudicator Phase
    phase_start = time.time()
    provider = AdjudicatorConfig.get('provider')
    model = AdjudicatorConfig.get('model')
    logger.info(f"{Colors.HEADER}⚖️  [Adjudicator]{Colors.ENDC} Engaging {provider} ({model})...")
    
    adjudicator_input = f"""
【待审材料】
{target_content}

【正方观点】
{affirmative_resp.content}

【反方观点】
{negative_resp.content}
"""
    try:
        with ThinkingSpinner(f"weighing arguments via {model}..."):
            adjudicator_resp = client.chat(
                messages=[
                    {"role": "system", "content": AdjudicatorPrompt},
                    {"role": "user", "content": adjudicator_input}
                ],
                **AdjudicatorConfig
            )
        usage_stats["adjudicator"] = adjudicator_resp.usage
        logger.info(f"{Colors.GREEN}✅ Verdict reached.{Colors.ENDC} ({format_usage(adjudicator_resp.usage)})")
        logger.debug(f"Adjudicator Content:\n{adjudicator_resp.content[:500]}...")
    except Exception as e:
        logger.error(f"{Colors.RED}💥 Adjudicator Phase Failed: {e}{Colors.ENDC}", exc_info=True)
        return
    time_stats["adjudicator"] = time.time() - phase_start

    # Save Report
    save_start = time.time()
    timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
    target_p = Path(target_file)
    report_tag = target_p.stem
    report_dir = project_root / "docs" / "reports" / report_tag
    report_dir.mkdir(parents=True, exist_ok=True)
    report_path = report_dir / f"debate_{timestamp_str}.md"
    
    report_content = f"""# Council Debate Report
**Date**: {timestamp_str}
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
    logger.info(f"\n📄 Report saved to: {Colors.BOLD}{report_path}{Colors.ENDC}")
    
    # Execution Summary
    total_time = time.time() - start_time
    total_tokens = sum(
        (u.total_tokens if u else 0) for u in usage_stats.values()
    )
    
    logger.info(f"\n{Colors.BOLD}📊 Execution Summary{Colors.ENDC}")
    logger.info("--------------------------------------------------")
    logger.info(f"| {'Phase':<15} | {'Duration (s)':<12} | {'Tokens':<15} |")
    logger.info("--------------------------------------------------")
    for phase in ["affirmative", "negative", "adjudicator"]:
        dur = f"{time_stats.get(phase, 0):.2f}"
        usage = usage_stats.get(phase)
        tok = usage.total_tokens if usage else 0
        logger.info(f"| {phase.capitalize():<15} | {dur:<12} | {tok:<15} |")
    logger.info("--------------------------------------------------")
    logger.info(f"| {'Total':<15} | {total_time:.2f}{'':<8} | {total_tokens:<15} |")
    logger.info("--------------------------------------------------")
    
    return report_path


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="SparkForge Council Debate CLI")
    parser.add_argument("target", help="Path to the document to be optimized")
    parser.add_argument("--ref", help="Path to reference document (optional)", default="")
    parser.add_argument("--instruction", "-i", help="Temporary user instruction or focus area (optional)", default="")
    
    args = parser.parse_args()
    if not os.path.exists(args.target):
        print(f"{Colors.RED}Error: Target file not found: {args.target}{Colors.ENDC}")
        sys.exit(1)
        
    run_debate(args.target, args.ref, args.instruction)
