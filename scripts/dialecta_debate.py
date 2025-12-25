#!/usr/bin/env python3
"""
SparkForge Council Debate CLI

A dialectical debate engine with:
- Affirmative (Qwen): Value Defender
- Negative (DeepSeek): Risk Auditor + Oracle Challenger
- Adjudicator (GLM): Final Verdict
- Oracle: External fact injection (via --oracle flag)
"""
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
    AdjudicatorConfig, AdjudicatorPrompt,
)
from scripts.grounding_verifier import run_grounding_check

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
        sys.stdout.write(f"\r{' ' * (len(self.message) + 40)}\r")
        sys.stdout.flush()

# Setup Logging
def setup_logging(log_dir: Path):
    log_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = log_dir / f"debate_exec_{timestamp}.log"
    
    existing_logs = sorted(log_dir.glob("debate_exec_*.log"))
    if len(existing_logs) > 20:
        for old_log in existing_logs[:-20]:
            try:
                old_log.unlink()
            except:
                pass
    
    logger = logging.getLogger("DialectaDebate")
    logger.setLevel(logging.DEBUG)
    
    if logger.hasHandlers():
        logger.handlers.clear()
        
    fh = logging.FileHandler(log_file, encoding='utf-8')
    fh.setLevel(logging.DEBUG)
    fh_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    fh.setFormatter(fh_formatter)
    
    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(logging.INFO)
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
    width = len(str(len(lines)))
    return "\n".join(f"{str(i+1).rjust(width)} | {line}" for i, line in enumerate(lines))

def format_usage(usage):
    if not usage:
        return "N/A"
    return f"In:{usage.prompt_tokens} Out:{usage.completion_tokens} Tot:{usage.total_tokens}"

def extract_one_liner(content: str) -> str:
    """Extracts the first executive summary/one-liner found in markdown headers."""
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
    
    start_time = time.time()
    usage_stats = {"affirmative": None, "negative": None, "adjudicator": None}
    time_stats = {}
    
    client = LLMClient(context_id=str(Path(target_file).absolute()))
    
    target_content_raw = read_file(target_file, logger)
    target_content = prepend_line_numbers(target_content_raw)
    ref_content = read_file(reference_file, logger) if reference_file else "无参考文档"
    oracle_content = read_file(kwargs.get('oracle_file', ''), logger) if kwargs.get('oracle_file') else ""
    
    # Construct Context
    context_blocks = []
    instr_block = f"<instructions>\n"
    instr_block += f"初始目标：{instruction if instruction else '未指定'}\n"
    if int(kwargs.get('loop', 0)) > 5:
        instr_block += "【退火策略激活】当前已进入后期迭代，请优先关注逻辑一致性与结构稳定性。\n"
    if kwargs.get('cite_check'):
        instr_block += "【证据链要求】所有批评必须在原文中找到依据，并标注 [Line XX] 或引用具体原文段落。\n"
    if oracle_content:
        instr_block += "【🔮 ORACLE INTEGRATION】: 已注入外部事实核查数据。请优先基于 <oracle_fact_check> 中的信息进行判断，修正任何过时的内部假设。\n"
    instr_block += "</instructions>"
    context_blocks.append(instr_block)
    
    if oracle_content:
        context_blocks.append(f"<oracle_fact_check>\n{oracle_content}\n</oracle_fact_check>")
        logger.info(f"🔮 Oracle Knowledge injected ({len(oracle_content)} bytes)")
        
    context_blocks.append(f"<history_summary>\n{ref_content}\n</history_summary>")
    context_blocks.append(f"<target_material>\n{target_content}\n</target_material>")
    
    user_input = "\n\n".join(context_blocks)
    
    # ---------------------------------------------------------
    # Phase 1: Parallel Arguments (Affirmative vs Negative)
    # ---------------------------------------------------------
    
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
            return res, time.time() - p_start
        except Exception as e:
            logger.error(f"❌ {role_name} API Call Failed: {e}")
            raise

    logger.info(f"\n{Colors.CYAN}🔥 [Council Phase] Generating arguments...{Colors.ENDC}")
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
        msg = "Council members are deliberating...\n"
        workers_map = {}
        
        with ThinkingSpinner(msg, delay=1.0):
            workers_map["affirmative"] = executor.submit(call_phase, "Affirmative", AffirmativePrompt, AffirmativeConfig)
            workers_map["negative"] = executor.submit(call_phase, "Negative", NegativePrompt, NegativeConfig)
            
            done, not_done = concurrent.futures.wait(workers_map.values(), timeout=240)
            
            if not_done:
                logger.error(f"{Colors.RED}💥 Timeout: Some LLM calls exceeded 240s.{Colors.ENDC}")
                for f in not_done: f.cancel()
                return None

    # Collect Results
    responses = {}
    
    def process_result(key, future, color):
        try:
            resp, dur = future.result()
            usage_stats[key] = resp.usage
            time_stats[key] = dur
            responses[key] = resp
            one_liner = extract_one_liner(resp.content)
            logger.info(f"{color}✅ {key.capitalize()} generated.{Colors.ENDC} ({format_usage(resp.usage)})")
            if one_liner:
                logger.info(f"   📢 Opinion: {one_liner[:100]}...")
            return resp
        except Exception as e:
            logger.error(f"{Colors.RED}💥 {key.capitalize()} failed: {e}{Colors.ENDC}")
            return None

    responses["affirmative"] = process_result("affirmative", workers_map["affirmative"], Colors.GREEN)
    responses["negative"] = process_result("negative", workers_map["negative"], Colors.BLUE)
        
    if not responses["affirmative"] or not responses["negative"]:
        logger.error("Critical failure: Affirmative or Negative failed.")
        return None

    # ---------------------------------------------------------
    # Phase 2: Grounding Verification
    # ---------------------------------------------------------
    grounding_report_md = ""
    if kwargs.get('cite_check'):
        logger.info(f"\n{Colors.CYAN}🔍 [Grounding Check] Verifying citations...{Colors.ENDC}")
        try:
            grounding_report, grounding_report_md = run_grounding_check(
                target_content_raw,
                responses["affirmative"].content,
                responses["negative"].content,
                logger=logger
            )
        except Exception as e:
            logger.warning(f"⚠️  Grounding check failed: {e}")

    # ---------------------------------------------------------
    # Phase 3: Adjudicator
    # ---------------------------------------------------------
    phase_start = time.time()
    provider = AdjudicatorConfig.get('provider')
    model = AdjudicatorConfig.get('model')
    logger.info(f"\n{Colors.HEADER}⚖️  [Adjudicator]{Colors.ENDC} Engaging {provider} ({model})...")
    
    adjudicator_input = f"""
{instr_block}

<history_summary>
{ref_content}
</history_summary>

【待审材料】
{target_content}

【正方观点】 (SparkForge 价值辩护人)
{responses["affirmative"].content}

【反方观点】 (SparkForge 风险审计官 + Oracle-Driven Challenger)
{responses["negative"].content}

【🔮 Oracle 外部情报】
{oracle_content if oracle_content else "(未提供外部情报)"}

【工具级事实锚定报告】
{grounding_report_md if grounding_report_md else '(未启用)'}
"""
    try:
        with ThinkingSpinner(f"Final Verdict via {model}...", delay=0.1):
            adjudicator_resp = client.chat(
                messages=[
                    {"role": "system", "content": AdjudicatorPrompt},
                    {"role": "user", "content": adjudicator_input}
                ],
                **AdjudicatorConfig
            )
        usage_stats["adjudicator"] = adjudicator_resp.usage
    except Exception as e:
        logger.error(f"💥 Adjudicator failed: {e}")
        return None
    
    time_stats["adjudicator"] = time.time() - phase_start
    
    one_liner = extract_one_liner(adjudicator_resp.content)
    logger.info(f"{Colors.GREEN}✅ Verdict reached.{Colors.ENDC} ({format_usage(adjudicator_resp.usage)})")
    if one_liner:
        logger.info(f"{Colors.YELLOW}⚖️  Verdict: {Colors.ENDC}{one_liner}")

    # ---------------------------------------------------------
    # Save Report (with Gatekeeper Header)
    # ---------------------------------------------------------
    timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
    target_p = Path(target_file).absolute()
    
    try:
        rel_from_root = target_p.relative_to(project_root)
        rel_dir = rel_from_root.parent
        if rel_dir.parts and rel_dir.parts[0] == 'docs':
             rel_dir = Path(*rel_dir.parts[1:])
    except ValueError:
        rel_dir = Path("external")
    
    report_tag = target_p.stem
    report_dir = project_root / "docs" / "reports" / rel_dir / report_tag
    report_dir.mkdir(parents=True, exist_ok=True)
    report_path = report_dir / f"debate_{timestamp_str}.md"
    
    try:
        rel_target = Path(target_file).absolute().relative_to(project_root)
    except ValueError:
        rel_target = target_file

    gatekeeper_header = f"""# 🛡️ Gatekeeper Approval Request
> **Human-in-the-Loop Protocol**
> Please review this summary and authorize the next step.

- **Target**: `{rel_target}`
- **Date**: {timestamp_str}
- **Verdict**: {one_liner if one_liner else "See Details"}

## ✅ Approval Checkbox
- [ ] **APPROVE**: Proceed with implementation.
- [ ] **REJECT**: Return to design phase.

---
"""

    report_content = f"""{gatekeeper_header}
# Council Debate Report

## ✊ Affirmative (Value Defender)
{responses["affirmative"].content}

---

## 👊 Negative (Risk Auditor + Oracle Challenger)
{responses["negative"].content}

---

## ⚖️ Adjudicator (Final Verdict)
{adjudicator_resp.content}

---
{grounding_report_md}
"""
    report_path.write_text(report_content, encoding='utf-8')
    logger.info(f"\n📄 Report saved to: {Colors.BOLD}{report_path}{Colors.ENDC}")
    logger.info(f"{Colors.YELLOW}👉 ACTION REQUIRED: Review the 'Gatekeeper Approval' section in the report.{Colors.ENDC}")
    
    return report_path


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="SparkForge Council Debate CLI")
    parser.add_argument("target", help="Path to the document to be optimized")
    parser.add_argument("--ref", help="Path to reference document (optional)", default="")
    parser.add_argument("--instruction", "-i", help="Temporary user instruction", default="")
    parser.add_argument("--loop", type=int, help="Current iteration loop number", default=0)
    parser.add_argument("--cite", action="store_true", help="Enable strict citation enforcement")
    parser.add_argument("--oracle", help="Path to Oracle knowledge file (created by oracle_scanner.py)", default="")
    
    args = parser.parse_args()
    if not os.path.exists(args.target):
        print(f"{Colors.RED}Error: Target file not found: {args.target}{Colors.ENDC}")
        sys.exit(1)
        
    try:
        result = run_debate(
            args.target, 
            args.ref, 
            args.instruction, 
            loop=args.loop, 
            cite_check=args.cite,
            oracle_file=args.oracle
        )
        if not result:
            sys.exit(1)
        sys.exit(0)
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}⚠️  Debate interrupted by user.{Colors.ENDC}")
        os._exit(1)
