# 📄 SparkForge PDF Tool Makefile
# Supports positional arguments for better UX: make <target> <file.md>

PYTHON = /opt/anaconda3/bin/python3
CONVERTER = scripts/pdf_tool/converter.py

# Capture arguments
MD = $(word 2,$(MAKECMDGOALS))
INS = $(word 3,$(MAKECMDGOALS))

# Default Target
.PHONY: help
help:
	@echo "🔍 PDF Generation (Positional Args):"
	@echo "  make a4 <file.md>       - Formal A4 Report (Business Style)"
	@echo "  make poster <file.md>   - Professional Long-Scroll (210mm)"
	@echo "  make glass <file.md>    - Glass-Style A4 Report (Council Style)"
	@echo "  make mobile <file.md>   - Mobile High-Impact Poster (500px)"
	@echo ""
	@echo "🧠 AI Content Audit:"
	@echo "  make debate <file.md> [instruction] - Run Dialecta Debate for optimization"
	@echo ""
	@echo "💡 Example: make a4 docs/report.md"
	@echo "💡 Example: make debate docs/plan.md \"优化采购指标的专业性\""

# -----------------------------------------------------------------------------
# Business Formal Style
# -----------------------------------------------------------------------------

.PHONY: a4
a4: check-md
	@echo "🚀 Generating Business A4 Report: $(MD)"
	@$(PYTHON) $(CONVERTER) $(MD) --theme business_formal.css --a4

.PHONY: poster
poster: check-md
	@echo "🚀 Generating Business Long-Scroll: $(MD)"
	@$(PYTHON) $(CONVERTER) $(MD) --theme business_formal.css --width 210mm

# -----------------------------------------------------------------------------
# AI Content Audit Target
# -----------------------------------------------------------------------------

.PHONY: debate
debate: check-md
	@echo "🧠 Starting Dialecta Debate: $(MD)"
	@$(PYTHON) scripts/dialecta_debate.py $(MD) --instruction "$(if $(INS),$(INS),优化并精炼文档内容，增强专业感)" --cite

# -----------------------------------------------------------------------------
# Council Poster (Glass) Style
# -----------------------------------------------------------------------------

.PHONY: glass
glass: check-md
	@echo "🚀 Generating Glass A4 Report: $(MD)"
	@$(PYTHON) $(CONVERTER) $(MD) --theme council_poster.css --a4 --glass-cards

.PHONY: mobile
mobile: check-md
	@echo "🚀 Generating Mobile Poster: $(MD)"
	@$(PYTHON) $(CONVERTER) $(MD) --theme council_poster.css --width 500px --glass-cards

# -----------------------------------------------------------------------------
# Utility
# -----------------------------------------------------------------------------

.PHONY: check-md
check-md:
	@if [ -z "$(MD)" ]; then \
		echo "❌ Error: Missing input file. Usage: make <target> <file.md>"; \
		exit 1; \
	fi
	@if [ ! -f "$(MD)" ]; then \
		echo "❌ Error: File '$(MD)' not found."; \
		exit 1; \
	fi

# Trick to allow positional arguments without make complaining about "No rule to make target..."
%:
	@:
