#!/usr/bin/env python3
"""
Test script for Grounding Verifier functionality.
"""
import sys
from pathlib import Path

# Add project root
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from scripts.grounding_verifier import GroundingVerifier, run_grounding_check

# ANSI Colors
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
CYAN = '\033[96m'
ENDC = '\033[0m'
BOLD = '\033[1m'


def test_line_number_verification():
    """Test [Line XX] citation verification."""
    print(f"\n{CYAN}Test 1: Line Number Verification{ENDC}")
    
    source = """Line 1: Introduction
Line 2: This is the main content.
Line 3: Some important data here.
Line 4: Conclusion."""
    
    verifier = GroundingVerifier(source)
    
    # Test valid line
    from scripts.grounding_verifier import Citation
    valid_citation = Citation(line_number=2, source="affirmative")
    result = verifier.verify_citation(valid_citation)
    
    assert result.is_valid, "Valid line should be verified"
    assert result.confidence == 1.0, "Valid line should have full confidence"
    print(f"  {GREEN}✓{ENDC} Valid line citation correctly verified")
    
    # Test invalid line (exceeds document)
    invalid_citation = Citation(line_number=100, source="negative")
    result = verifier.verify_citation(invalid_citation)
    
    assert not result.is_valid, "Invalid line should fail verification"
    assert "exceeds" in result.error_reason.lower(), "Should mention line exceeds document"
    print(f"  {GREEN}✓{ENDC} Invalid line citation correctly rejected")
    
    return True


def test_quote_verification():
    """Test quoted text verification."""
    print(f"\n{CYAN}Test 2: Quote Verification{ENDC}")
    
    source = """# SparkForge Architecture
The system uses a three-agent council for document optimization.
Each agent has a distinct role: Affirmative, Negative, and Adjudicator.
This ensures balanced decision making through structured debate."""
    
    verifier = GroundingVerifier(source)
    
    # Test exact quote
    from scripts.grounding_verifier import Citation
    exact_quote = Citation(quoted_text="three-agent council", source="affirmative")
    result = verifier.verify_citation(exact_quote)
    
    assert result.is_valid, "Exact quote should be verified"
    assert result.confidence == 1.0, "Exact quote should have full confidence"
    print(f"  {GREEN}✓{ENDC} Exact quote correctly verified")
    
    # Test fuzzy match (slight variation)
    fuzzy_quote = Citation(quoted_text="a three agent council system", source="negative")
    result = verifier.verify_citation(fuzzy_quote)
    
    # Fuzzy match may or may not pass depending on threshold
    print(f"  {YELLOW}ℹ{ENDC} Fuzzy quote confidence: {result.confidence:.2f}")
    
    # Test hallucinated quote
    fake_quote = Citation(quoted_text="quantum blockchain integration", source="affirmative")
    result = verifier.verify_citation(fake_quote)
    
    assert not result.is_valid, "Hallucinated quote should fail verification"
    print(f"  {GREEN}✓{ENDC} Hallucinated quote correctly rejected")
    
    return True


def test_full_debate_verification():
    """Test complete debate output verification."""
    print(f"\n{CYAN}Test 3: Full Debate Verification{ENDC}")
    
    source = """# Project Requirements
1. The system must handle 1000 requests per second.
2. All data should be encrypted at rest.
3. User authentication is mandatory.
4. Logging must be implemented for audit purposes."""
    
    affirmative_output = """
## Value Analysis
The document clearly states [Line 1] that performance is critical.
The requirement for "1000 requests per second" demonstrates serious throughput considerations.
Furthermore, [Line 2] shows commitment to security through encryption.
"""
    
    negative_output = """
## Risk Assessment
While [Line 1] mentions performance, there's no mention of scalability testing.
The claim about "quantum-resistant encryption" is not supported by the document.
[Line 5] discusses backup procedures. <- This is a hallucination
"""
    
    report, markdown = run_grounding_check(source, affirmative_output, negative_output)
    
    print(f"  Total Citations: {report.total_citations}")
    print(f"  Verified: {report.verified_count}")
    print(f"  Hallucinations: {report.hallucination_count}")
    print(f"  Grounding Score: {report.grounding_score:.1f}/100")
    
    # Should detect at least one hallucination (Line 5 doesn't exist)
    assert report.hallucination_count >= 1, "Should detect at least one hallucination"
    print(f"  {GREEN}✓{ENDC} Hallucination detection working")
    
    # Markdown report should be generated
    assert "Grounding Score" in markdown, "Markdown report should include score"
    print(f"  {GREEN}✓{ENDC} Markdown report generated correctly")
    
    return True


def main():
    print(f"\n{BOLD}{'='*60}{ENDC}")
    print(f"{BOLD}🔍 Grounding Verifier - Unit Tests{ENDC}")
    print(f"{BOLD}{'='*60}{ENDC}")
    
    tests = [
        ("Line Number Verification", test_line_number_verification),
        ("Quote Verification", test_quote_verification),
        ("Full Debate Verification", test_full_debate_verification),
    ]
    
    passed = 0
    failed = 0
    
    for name, test_func in tests:
        try:
            if test_func():
                passed += 1
                print(f"  {GREEN}✅ {name} PASSED{ENDC}")
        except AssertionError as e:
            failed += 1
            print(f"  {RED}❌ {name} FAILED: {e}{ENDC}")
        except Exception as e:
            failed += 1
            print(f"  {RED}❌ {name} ERROR: {e}{ENDC}")
    
    print(f"\n{BOLD}{'='*60}{ENDC}")
    print(f"{BOLD}📊 Results: {passed} passed, {failed} failed{ENDC}")
    print(f"{BOLD}{'='*60}{ENDC}")
    
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
