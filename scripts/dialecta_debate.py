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
import concurrent.futures
import re

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
    
    # Simple Log Pruning: Keep only last 20 logs to save space
    existing_logs = sorted(log_dir.glob("debate_exec_*.log"))
    if len(existing_logs) > 20:
        for old_log in existing_logs[:-20]:
            try:
                old_log.unlink()
            except:
                pass
    
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

def prepend_line_numbers(text: str) -> str:
    lines = text.splitlines()
    # Format: "  1 | content"
    width = len(str(len(lines)))
    return "\n".join(f"{str(i+1).rjust(width)} | {line}" for i, line in enumerate(lines))

def format_usage(usage):
    if not usage:
        return "N/A"
    return f"In:{usage.prompt_tokens} Out:{usage.completion_tokens} Total:{usage.total_tokens}"

def extract_one_liner(content: str) -> str:
    """Extracts the first executive summary/one-liner found in markdown headers."""
    # Look for ## 💡 One-Liner or ## 💡 决策简报 followed by any text until next header or end
    patterns = [
        r"##\s*💡\s*决策简报\s*(?:\(Executive Summary\))?\s*\n+(.*?)(?=\n+##|$)",
        r"##\s*💡\s*价值核心\s*(?:\(Core Value\))?\s*\n+(.*?)(?=\n+##|$)",
        r"##\s*💡\s*风险识别\s*(?:\(Risk Spotlight\))?\s*\n+(.*?)(?=\n+##|$)",
        r"##\s*💡\s*One-Liner\s*\n+(.*?)(?=\n+##|$)"
    ]
    for pattern in patterns:
        match = re.search(pattern, content, re.DOTALL)
        if match:
            return match.group(1).strip()
    return ""

def run_debate(target_file: str, reference_file: str = "", instruction: str = "", **kwargs):
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
    
    target_content_raw = read_file(target_file, logger)
    target_content = prepend_line_numbers(target_content_raw)
    ref_content = read_file(reference_file, logger) if reference_file else "无参考文档"
    
    # Construct Context with Layered XML Isolation
    context_blocks = []
    
    # 1. High-Level Instructions (Essential Runtime Context Only)
    # Note: Strategic directives are now embedded in individual role prompt files
    instr_block = f"<instructions>\n"
    instr_block += f"初始目标：{instruction if instruction else '未指定'}\n"
    if int(kwargs.get('loop', 0)) > 5:
        instr_block += "【退火策略激活】当前已进入后期迭代，请优先关注逻辑一致性与结构稳定性，避免破坏性创新。\n"
    if kwargs.get('cite_check'):
        instr_block += "【证据链要求】所有批评必须在原文中找到依据，并标注 [Line XX] 或引用具体原文段落。\n"
    instr_block += "</instructions>"
    context_blocks.append(instr_block)

    # 2. Historical Context (History Summary)
    context_blocks.append(f"<history_summary>\n{ref_content}\n</history_summary>")
    
    # 3. Target Material
    context_blocks.append(f"<target_material>\n{target_content}\n</target_material>")
    
    user_input = "\n\n".join(context_blocks)
    
    # Define parallel execution helper
    def call_phase(role_name, prompt, config):
        p_start = time.time()
        provider = config.get('provider')
        model = config.get('model')
        logger.info(f"🚀 [{role_name}] Engaging {provider} ({model})...")
        
        try:
            res = client.chat(
                messages=[
                    {"role": "system", "content": prompt},
                    {"role": "user", "content": user_input}
                ],
                **config
            )
            p_duration = time.time() - p_start
            return res, p_duration
        except Exception as e:
            logger.error(f"❌ {role_name} API Call Failed: {e}")
            raise

    # 1 & 2. Parallel Affirmative and Negative Phase
    logger.info(f"\n{Colors.CYAN}🔥 [Parallel Phase] Generating Affirmative & Negative arguments...{Colors.ENDC}")
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
        with ThinkingSpinner("Both sides are preparing their arguments...\n\n", delay=1.0):
            future_aff = executor.submit(call_phase, "Affirmative", AffirmativePrompt, AffirmativeConfig)
            future_neg = executor.submit(call_phase, "Negative", NegativePrompt, NegativeConfig)
            
            # Wait for results with global timeout (180s)
            futures = {"Affirmative": future_aff, "Negative": future_neg}
            done, not_done = concurrent.futures.wait(futures.values(), timeout=180)
            
            if not_done:
                logger.error(f"{Colors.RED}💥 Parallel Phase Timeout: Some LLM calls exceeded 180s limit.{Colors.ENDC}")
                for f in not_done: f.cancel()
                return None

            # Collect Affirmative
            try:
                affirmative_resp, time_stats["affirmative"] = future_aff.result()
                usage_stats["affirmative"] = affirmative_resp.usage
                one_liner = extract_one_liner(affirmative_resp.content)
                logger.info(f"{Colors.GREEN}✅ Affirmative generated.{Colors.ENDC} ({format_usage(affirmative_resp.usage)})")
                if one_liner:
                    logger.info(f"{Colors.CYAN}📢 One-Liner: {Colors.ENDC}{one_liner}\n")
            except Exception as e:
                logger.error(f"{Colors.RED}💥 Affirmative Phase Failed: {e}{Colors.ENDC}")
                return None

            # Collect Negative
            try:
                negative_resp, time_stats["negative"] = future_neg.result()
                usage_stats["negative"] = negative_resp.usage
                one_liner = extract_one_liner(negative_resp.content)
                logger.info(f"{Colors.GREEN}✅ Negative generated.{Colors.ENDC} ({format_usage(negative_resp.usage)})")
                if one_liner:
                    logger.info(f"{Colors.CYAN}📢 One-Liner: {Colors.ENDC}{one_liner}\n")
            except Exception as e:
                logger.error(f"{Colors.RED}💥 Negative Phase Failed: {e}{Colors.ENDC}")
                return None

    # 3. Adjudicator Phase
    phase_start = time.time()
    provider = AdjudicatorConfig.get('provider')
    model = AdjudicatorConfig.get('model')
    logger.info(f"{Colors.HEADER}⚖️  [Adjudicator]{Colors.ENDC} Engaging {provider} ({model})...")
    
    adjudicator_input = f"""
{instr_block}

<history_summary>
{ref_content}
</history_summary>

【待审材料】
{target_content}

【正方观点】 (SparkForge 价值辩护人)
{affirmative_resp.content}

【反方观点】 (SparkForge 风险审计官)
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
        
        # Post-Response Citation Audit
        if kwargs.get('cite_check'):
            total_lines = len(target_content.splitlines())
            # Simple heuristic for citation hallucination: check if cited line exceeds file length
            citations = re.findall(r"\[Line\s*(\d+)\]", adjudicator_resp.content)
            for c in citations:
                if int(c) > total_lines:
                    logger.warning(f"{Colors.RED}⚠️  Citation Hallucination Detected: Line {c} exceeds total lines ({total_lines}).{Colors.ENDC}")
            
            if not citations and "引用" not in adjudicator_resp.content:
                logger.warning(f"{Colors.YELLOW}⚠️  Citation Check Warning: Adjudicator did not explicitly cite lines.{Colors.ENDC}")
            
        one_liner = extract_one_liner(adjudicator_resp.content)
        logger.info(f"{Colors.GREEN}✅ Verdict reached.{Colors.ENDC} ({format_usage(adjudicator_resp.usage)})")
        if one_liner:
            logger.info(f"{Colors.YELLOW}⚖️  One-Liner: {Colors.ENDC}{one_liner}")
        
        # New: Logic Pulse - Extract the first conflict point for quick scanning
        pulse_match = re.search(r"\* \*\*焦点\[.*?\]\*\*：(.*?)(?=\s*\*|\s*###|$)", adjudicator_resp.content, re.DOTALL)
        if pulse_match:
            pulse_text = pulse_match.group(1).strip().replace('\n', ' ')
            logger.info(f"{Colors.CYAN}🧬 Logic Pulse: {Colors.ENDC}{pulse_text[:120]}...\n")
        else:
            logger.info("") # Just a newline
        logger.debug(f"Adjudicator Content:\n{adjudicator_resp.content[:500]}...")
    except Exception as e:
        logger.error(f"{Colors.RED}💥 Adjudicator Phase Failed: {e}{Colors.ENDC}", exc_info=True)
        return
    time_stats["adjudicator"] = time.time() - phase_start

    # Save Report
    save_start = time.time()
    timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
    target_p = Path(target_file).absolute()
    
    # Improved directory logic: Mirror target's relative path to avoid collisions
    try:
        # Get path relative to current working directory or project root
        # We use a simplified mapping to avoid too many nested folders if possible, 
        # but full relative path is safest against collisions.
        rel_from_root = target_p.relative_to(project_root)
        # remove the filename from tail to get parent structure
        rel_dir = rel_from_root.parent
        # Remove redundant 'docs' prefix if present to avoid docs/reports/docs/...
        if rel_dir.parts and rel_dir.parts[0] == 'docs':
             rel_dir = Path(*rel_dir.parts[1:])
    except ValueError:
        # Fallback for files outside project root
        rel_dir = Path("external")
    
    report_tag = target_p.stem
    report_dir = project_root / "docs" / "reports" / rel_dir / report_tag
    report_dir.mkdir(parents=True, exist_ok=True)
    report_path = report_dir / f"debate_{timestamp_str}.md"
    
    # Path Sanitization for report
    try:
        rel_target = Path(target_file).absolute().relative_to(project_root)
        rel_ref = Path(reference_file).absolute().relative_to(project_root) if reference_file else "N/A"
    except ValueError:
        rel_target = target_file
        rel_ref = reference_file if reference_file else "N/A"

    report_content = f"""# Council Debate Report
**Date**: {timestamp_str}
**Target**: `{rel_target}`
**Objective**: {instruction if instruction else 'Standard Optimization'}
**Ref**: `{rel_ref}`

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
    parser.add_argument("--instruction", "-i", help="Temporary user instruction", default="")
    parser.add_argument("--loop", type=int, help="Current iteration loop number", default=0)
    parser.add_argument("--cite", action="store_true", help="Enable strict citation enforcement")
    
    args = parser.parse_args()
    if not os.path.exists(args.target):
        print(f"{Colors.RED}Error: Target file not found: {args.target}{Colors.ENDC}")
        sys.exit(1)
        
    result = run_debate(args.target, args.ref, args.instruction, loop=args.loop, cite_check=args.cite)
    if not result:
        sys.exit(1)
    sys.exit(0)
