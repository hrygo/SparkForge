#!/usr/bin/env python3
"""
Test script to verify model configurations for The Council.
This script makes a simple API call to each configured model to ensure:
1. Model name is valid and accessible.
2. Provider routing works correctly.
"""
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from llm import LLMClient
from prompts.templates import (
    AffirmativeConfig, NegativeConfig, AdjudicatorConfig
)

# ANSI Colors
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
CYAN = '\033[96m'
ENDC = '\033[0m'
BOLD = '\033[1m'

TEST_PROMPT = "Please respond with exactly one word: 'OK'"

def test_config(role_name: str, config: dict) -> bool:
    """Test a single model configuration."""
    provider = config.get('provider', 'unknown')
    model = config.get('model', 'unknown')
    
    print(f"\n{CYAN}Testing {BOLD}{role_name}{ENDC}{CYAN}...{ENDC}")
    print(f"  Provider: {provider}")
    print(f"  Model: {model}")
    print(f"  Temperature: {config.get('temperature', 'N/A')}")
    
    client = LLMClient(context_id=f"test_{role_name}")
    
    try:
        response = client.chat(
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": TEST_PROMPT}
            ],
            **config
        )
        
        # Check if we got a valid response
        if response and response.content:
            content_preview = response.content[:50].replace('\n', ' ')
            print(f"  {GREEN}✅ SUCCESS{ENDC}")
            print(f"  Response: \"{content_preview}...\"")
            if response.usage:
                print(f"  Tokens: In={response.usage.prompt_tokens}, Out={response.usage.completion_tokens}")
            return True
        else:
            print(f"  {RED}❌ FAILED: Empty response{ENDC}")
            return False
            
    except Exception as e:
        print(f"  {RED}❌ FAILED: {e}{ENDC}")
        return False

def main():
    print(f"\n{BOLD}{'='*60}{ENDC}")
    print(f"{BOLD}🧪 SparkForge Council - Model Configuration Test{ENDC}")
    print(f"{BOLD}{'='*60}{ENDC}")
    
    configs = {
        "Affirmative (Value Defender)": AffirmativeConfig,
        "Negative (Risk Auditor)": NegativeConfig,
        "Adjudicator (Chief Judge)": AdjudicatorConfig,
    }
    
    results = {}
    for role_name, config in configs.items():
        results[role_name] = test_config(role_name, config)
    
    # Summary
    print(f"\n{BOLD}{'='*60}{ENDC}")
    print(f"{BOLD}📊 Test Summary{ENDC}")
    print(f"{BOLD}{'='*60}{ENDC}")
    
    all_passed = True
    for role_name, passed in results.items():
        status = f"{GREEN}PASS{ENDC}" if passed else f"{RED}FAIL{ENDC}"
        print(f"  {role_name}: [{status}]")
        if not passed:
            all_passed = False
    
    if all_passed:
        print(f"\n{GREEN}{BOLD}🎉 All model configurations are valid!{ENDC}")
        return 0
    else:
        print(f"\n{YELLOW}{BOLD}⚠️  Some configurations failed. Please check model names.{ENDC}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
