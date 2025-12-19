# 📄 SparkForge Industrial-Grade Makefile
# Usage: make <target> <file> [optional_param]

# --- Configuration ---
PYTHON = /opt/anaconda3/bin/python3
CONVERTER = scripts/pdf_tool/converter.py
DEBATE_SCRIPT = scripts/dialecta_debate.py

# --- Positional Arguments Capture ---
# MD: The primary file (Markdown or PDF)
# ARG: The secondary parameter (Instruction for debate or Message for sign)
MD = $(word 2,$(MAKECMDGOALS))
ARG = $(word 3,$(MAKECMDGOALS))

# --- Colors ---
BLUE   = \033[34m
CYAN   = \033[36m
GREEN  = \033[32m
YELLOW = \033[33m
RESET  = \033[0m
BOLD   = \033[1m

.PHONY: help
help:
	@echo "$(BOLD)⚡ SparkForge 2.0 CLI Interface$(RESET)"
	@echo "------------------------------------------------------------------"
	@echo "$(CYAN)[1. PDF GENERATION]$(RESET)"
	@echo "  $(GREEN)make a4$(RESET) <file.md>              - Business Formal A4 Report"
	@echo "  $(GREEN)make glass$(RESET) <file.md>           - Glass-Style A4 Report"
	@echo "  $(GREEN)make poster$(RESET) <file.md>          - Professional Long-Scroll (210mm)"
	@echo "  $(GREEN)make mobile$(RESET) <file.md>          - Mobile High-Impact Poster (500px)"
	@echo ""
	@echo "$(CYAN)[2. AI CONTENT AUDIT]$(RESET)"
	@echo "  $(GREEN)make debate$(RESET) <file.md> [prompt] - Run Dialecta Council Debate for optimization"
	@echo ""
	@echo "$(CYAN)[3. QUALITY CONTROL]$(RESET)"
	@echo "  $(GREEN)make lint$(RESET) [file.md]           - Check markdown syntax & rules"
	@echo "  $(GREEN)make fix$(RESET) [file.md]            - Auto-fix markdown formatting errors"
	@echo ""
	@echo "$(CYAN)[4. SECURITY & SIGNING]$(RESET)"
	@echo "  $(GREEN)make sign$(RESET) <file.pdf> [msg]     - Manually sign PDF with PhantomGuard"
	@echo "------------------------------------------------------------------"
	@echo "$(YELLOW)💡 EXAMPLES:$(RESET)"
	@echo "  $(BLUE)»$(RESET) make a4 docs/plan.md"
	@echo "  $(BLUE)»$(RESET) make debate docs/strategy.md \"Enhance professional tone\""
	@echo "  $(BLUE)»$(RESET) make fix docs/AI_Training_Strategy_ALM.md"
	@echo "------------------------------------------------------------------"

# -----------------------------------------------------------------------------
# 1. PDF Generation (Business & Council Styles)
# -----------------------------------------------------------------------------

.PHONY: a4
a4: check-md
	@echo "🚀 Rendering Business A4: $(MD)"
	@$(PYTHON) $(CONVERTER) $(MD) --theme business_formal.css --a4

.PHONY: glass
glass: check-md
	@echo "🚀 Rendering Glass A4: $(MD)"
	@$(PYTHON) $(CONVERTER) $(MD) --theme council_poster.css --a4 --glass-cards

.PHONY: poster
poster: check-md
	@echo "🚀 Rendering Long-Scroll: $(MD)"
	@$(PYTHON) $(CONVERTER) $(MD) --theme business_formal.css --width 210mm

.PHONY: mobile
mobile: check-md
	@echo "🚀 Rendering Mobile Poster: $(MD)"
	@$(PYTHON) $(CONVERTER) $(MD) --theme council_poster.css --width 500px --glass-cards

# -----------------------------------------------------------------------------
# 2. AI Content Audit (The Council)
# -----------------------------------------------------------------------------

.PHONY: debate
debate: check-md
	@echo "🧠 Engaging The Council for: $(MD)"
	@$(PYTHON) $(DEBATE_SCRIPT) $(MD) --instruction "$(if $(ARG),$(ARG),优化并精炼文档内容，增强专业感)" --cite

# -----------------------------------------------------------------------------
# 3. Quality Control (Linting & Formatting)
# -----------------------------------------------------------------------------

.PHONY: lint
lint:
	@echo "🔍 Linting Markdown assets..."
	@if [ -z "$(MD)" ]; then \
		markdownlint "**/*.md" --ignore "**/node_modules/**" --ignore "docs/reports/**" --ignore "docs/backup/**"; \
	else \
		markdownlint "$(MD)"; \
	fi

.PHONY: fix
fix:
	@echo "🛠️  Auto-fixing Markdown formatting..."
	@if [ -z "$(MD)" ]; then \
		prettier --write "**/*.md" --ignore-path .gitignore; \
		markdownlint --fix "**/*.md" --ignore "**/node_modules/**" --ignore "docs/reports/**" --ignore "docs/backup/**"; \
	else \
		prettier --write "$(MD)"; \
		markdownlint --fix "$(MD)"; \
	fi

# -----------------------------------------------------------------------------
# 4. Security & Signing (PhantomGuard)
# -----------------------------------------------------------------------------

.PHONY: sign
sign:
	@echo "🔐 Applying PhantomGuard Signature: $(MD)"
	@phantom-guard sign -f "$(MD)" -m "$(if $(ARG),$(ARG),SparkForge_Industrial_Grade_$(shell date +%Y%m%d))"

# -----------------------------------------------------------------------------
# Utility & Infrastructure
# -----------------------------------------------------------------------------

.PHONY: check-md
check-md:
	@if [ -z "$(MD)" ]; then \
		echo "$(BOLD)$(RED)❌ Error: Missing input file.$(RESET) Usage: make <target> <file>"; \
		exit 1; \
	fi
	@if [ ! -f "$(MD)" ]; then \
		echo "$(BOLD)$(RED)❌ Error: File '$(MD)' not found.$(RESET)"; \
		exit 1; \
	fi

# Positional argument magic
%:
	@:
