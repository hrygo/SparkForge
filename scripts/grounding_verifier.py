"""
Grounding Verifier Module for SparkForge Council.

This module provides tool-based fact verification to combat "collective hallucination"
in multi-agent debates. It extracts citations from debate outputs and physically
verifies them against the source document.
"""
import re
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass, field
from difflib import SequenceMatcher


@dataclass
class Citation:
    """Represents a citation extracted from debate content."""
    line_number: Optional[int] = None  # [Line XX] style
    quoted_text: Optional[str] = None  # Direct quote
    section_ref: Optional[str] = None  # "第X节" or "Section X"
    source: str = ""  # "affirmative" or "negative"
    context: str = ""  # Surrounding text for debugging


@dataclass
class VerificationResult:
    """Result of verifying a single citation."""
    citation: Citation
    is_valid: bool
    confidence: float  # 0.0 to 1.0
    matched_content: str = ""
    error_reason: str = ""


@dataclass
class GroundingReport:
    """Complete grounding verification report."""
    total_citations: int = 0
    verified_count: int = 0
    hallucination_count: int = 0
    weak_match_count: int = 0
    results: List[VerificationResult] = field(default_factory=list)
    
    @property
    def grounding_score(self) -> float:
        """Calculate overall grounding score (0-100)."""
        if self.total_citations == 0:
            return 100.0  # No citations = no hallucinations detected
        return (self.verified_count / self.total_citations) * 100
    
    @property
    def hallucination_rate(self) -> float:
        """Calculate hallucination rate as percentage."""
        if self.total_citations == 0:
            return 0.0
        return (self.hallucination_count / self.total_citations) * 100
    
    def to_markdown(self) -> str:
        """Generate markdown summary for inclusion in debate report."""
        status_emoji = "✅" if self.hallucination_count == 0 else "⚠️"
        
        md = f"""
## 🔍 Grounding Verification Report

{status_emoji} **Grounding Score**: {self.grounding_score:.1f}/100
- **Total Citations Analyzed**: {self.total_citations}
- **Verified (High Confidence)**: {self.verified_count}
- **Weak Matches**: {self.weak_match_count}
- **Hallucinations Detected**: {self.hallucination_count}

"""
        if self.hallucination_count > 0:
            md += "### ❌ Hallucination Details\n\n"
            for r in self.results:
                if not r.is_valid:
                    source_emoji = "✊" if r.citation.source == "affirmative" else "👊"
                    md += f"- {source_emoji} **{r.citation.source.capitalize()}**: "
                    if r.citation.line_number:
                        md += f"[Line {r.citation.line_number}] "
                    if r.citation.quoted_text:
                        md += f'"{r.citation.quoted_text[:50]}..." '
                    md += f"→ {r.error_reason}\n"
        
        return md


class GroundingVerifier:
    """
    Verifies citations in debate outputs against the source document.
    
    Supports:
    - [Line XX] style citations
    - Direct quoted text ("...")
    - Section references (第X节, Section X)
    """
    
    # Thresholds
    FUZZY_MATCH_THRESHOLD = 0.7  # Minimum similarity for fuzzy quote matching
    WEAK_MATCH_THRESHOLD = 0.5   # Below this is considered hallucination
    
    def __init__(self, source_content: str, source_lines: List[str] = None):
        """
        Initialize verifier with source document.
        
        Args:
            source_content: The raw content of the target document
            source_lines: Pre-split lines (optional, for efficiency)
        """
        self.source_content = source_content
        self.source_lines = source_lines or source_content.splitlines()
        self.total_lines = len(self.source_lines)
    
    def extract_citations(self, content: str, source: str) -> List[Citation]:
        """
        Extract all citations from debate content.
        
        Args:
            content: The debate output (affirmative or negative)
            source: "affirmative" or "negative"
        
        Returns:
            List of Citation objects
        """
        citations = []
        
        # Pattern 1: [Line XX] or [Line XX-YY]
        line_pattern = r'\[Line\s*(\d+)(?:\s*-\s*\d+)?\]'
        for match in re.finditer(line_pattern, content, re.IGNORECASE):
            line_num = int(match.group(1))
            # Get surrounding context (50 chars before and after)
            start = max(0, match.start() - 50)
            end = min(len(content), match.end() + 50)
            context = content[start:end]
            
            citations.append(Citation(
                line_number=line_num,
                source=source,
                context=context
            ))
        
        # Pattern 2: Direct quotes with Chinese or English quotation marks
        quote_patterns = [
            r'"([^"]{10,100})"',  # English quotes, 10-100 chars
            r'"([^"]{10,100})"',  # Chinese quotes
            r'「([^」]{10,100})」',  # Japanese-style quotes
            r'『([^』]{10,100})』',  # Double Japanese quotes
        ]
        for pattern in quote_patterns:
            for match in re.finditer(pattern, content):
                quoted = match.group(1).strip()
                # Skip if it's clearly a label or instruction, not a citation
                if any(x in quoted.lower() for x in ['例如', 'example', '如：', 'e.g.']):
                    continue
                citations.append(Citation(
                    quoted_text=quoted,
                    source=source,
                    context=match.group(0)
                ))
        
        # Pattern 3: Section references (第X节, Section X)
        section_patterns = [
            r'第\s*([一二三四五六七八九十\d]+)\s*[节章部分]',
            r'[Ss]ection\s*(\d+)',
            r'[Pp]art\s*(\d+)',
        ]
        for pattern in section_patterns:
            for match in re.finditer(pattern, content):
                citations.append(Citation(
                    section_ref=match.group(0),
                    source=source,
                    context=match.group(0)
                ))
        
        return citations
    
    def verify_citation(self, citation: Citation) -> VerificationResult:
        """
        Verify a single citation against the source document.
        
        Returns:
            VerificationResult with validation status and details
        """
        # Verify line number citations
        if citation.line_number is not None:
            if citation.line_number > self.total_lines:
                return VerificationResult(
                    citation=citation,
                    is_valid=False,
                    confidence=0.0,
                    error_reason=f"Line {citation.line_number} exceeds document length ({self.total_lines} lines)"
                )
            elif citation.line_number < 1:
                return VerificationResult(
                    citation=citation,
                    is_valid=False,
                    confidence=0.0,
                    error_reason=f"Invalid line number: {citation.line_number}"
                )
            else:
                # Line exists, return the actual content for cross-reference
                actual_line = self.source_lines[citation.line_number - 1]
                return VerificationResult(
                    citation=citation,
                    is_valid=True,
                    confidence=1.0,
                    matched_content=actual_line[:100]
                )
        
        # Verify quoted text citations using fuzzy matching
        if citation.quoted_text:
            # Try exact substring match first
            if citation.quoted_text in self.source_content:
                # Find the line number for context
                for i, line in enumerate(self.source_lines):
                    if citation.quoted_text in line:
                        return VerificationResult(
                            citation=citation,
                            is_valid=True,
                            confidence=1.0,
                            matched_content=f"Found at Line {i+1}: {line[:100]}"
                        )
                return VerificationResult(
                    citation=citation,
                    is_valid=True,
                    confidence=1.0,
                    matched_content="Exact match found in document"
                )
            
            # Fuzzy match: find best matching line
            best_ratio = 0.0
            best_line = ""
            best_line_num = 0
            
            for i, line in enumerate(self.source_lines):
                # Use SequenceMatcher for fuzzy comparison
                ratio = SequenceMatcher(None, citation.quoted_text.lower(), line.lower()).ratio()
                if ratio > best_ratio:
                    best_ratio = ratio
                    best_line = line
                    best_line_num = i + 1
            
            if best_ratio >= self.FUZZY_MATCH_THRESHOLD:
                return VerificationResult(
                    citation=citation,
                    is_valid=True,
                    confidence=best_ratio,
                    matched_content=f"Fuzzy match at Line {best_line_num} ({best_ratio:.0%}): {best_line[:80]}"
                )
            elif best_ratio >= self.WEAK_MATCH_THRESHOLD:
                return VerificationResult(
                    citation=citation,
                    is_valid=True,  # Weak but not hallucination
                    confidence=best_ratio,
                    matched_content=f"Weak match at Line {best_line_num} ({best_ratio:.0%})",
                    error_reason="Low confidence match - may be paraphrased"
                )
            else:
                return VerificationResult(
                    citation=citation,
                    is_valid=False,
                    confidence=best_ratio,
                    error_reason=f"Quote not found in document (best match: {best_ratio:.0%})"
                )
        
        # Section references - just check if the section header exists
        if citation.section_ref:
            if citation.section_ref.lower() in self.source_content.lower():
                return VerificationResult(
                    citation=citation,
                    is_valid=True,
                    confidence=0.9,
                    matched_content=f"Section reference found"
                )
            # Check for similar patterns
            return VerificationResult(
                citation=citation,
                is_valid=False,
                confidence=0.0,
                error_reason=f"Section '{citation.section_ref}' not found in document"
            )
        
        # Unknown citation type
        return VerificationResult(
            citation=citation,
            is_valid=True,
            confidence=0.5,
            error_reason="Unknown citation type - skipped"
        )
    
    def verify_debate_outputs(
        self, 
        affirmative_content: str, 
        negative_content: str
    ) -> GroundingReport:
        """
        Verify all citations from both debate sides.
        
        Args:
            affirmative_content: Output from Affirmative agent
            negative_content: Output from Negative agent
        
        Returns:
            GroundingReport with complete verification results
        """
        report = GroundingReport()
        
        # Extract citations from both sides
        aff_citations = self.extract_citations(affirmative_content, "affirmative")
        neg_citations = self.extract_citations(negative_content, "negative")
        
        all_citations = aff_citations + neg_citations
        report.total_citations = len(all_citations)
        
        # Verify each citation
        for citation in all_citations:
            result = self.verify_citation(citation)
            report.results.append(result)
            
            if result.is_valid:
                if result.confidence >= self.FUZZY_MATCH_THRESHOLD:
                    report.verified_count += 1
                else:
                    report.weak_match_count += 1
            else:
                report.hallucination_count += 1
        
        return report


def run_grounding_check(
    target_content: str,
    affirmative_output: str,
    negative_output: str,
    logger=None
) -> Tuple[GroundingReport, str]:
    """
    Convenience function to run grounding verification.
    
    Returns:
        Tuple of (GroundingReport, markdown_summary)
    """
    verifier = GroundingVerifier(target_content)
    report = verifier.verify_debate_outputs(affirmative_output, negative_output)
    
    if logger:
        if report.hallucination_count > 0:
            logger.warning(f"🔍 Grounding Check: {report.hallucination_count} hallucinations detected!")
        else:
            logger.info(f"🔍 Grounding Check: All {report.total_citations} citations verified.")
    
    return report, report.to_markdown()
