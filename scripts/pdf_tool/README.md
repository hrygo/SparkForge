# 📄 Universal PDF Converter (Council Engine)

A flexible, theme-driven tool to convert Markdown documentation into high-quality, styled PDFs. It supports standard A4 documents, long-scroll mobile posters, and modern "glassmorphism" layouts.

## ✨ Features

*   **Markdown to PDF**: Full support for tables, code blocks, and standard markdown.
*   **Mermaid Diagrams**: Automatically renders `mermaid` code blocks into SVG diagrams.
*   **Theme Engine**: CSS-based theming (e.g., standard reports, dark mode, glass posters).
*   **Layout Plugins**: Special layouts like "Glass Cards" for creating visual posters.
*   **Dynamic Sizing**: Supports standard page sizes (A4) or custom widths for long-scroll mobile views.

## 🛠️ Prerequisites

*   **Python 3.8+**
*   **Node.js 16+** (for Puppeteer rendering engine)

### Python Dependencies
```bash
pip install markdown jinja2
```

### Node.js Dependencies
Inside `scripts/pdf_tool/`:
```bash
npm install puppeteer
```

## 🚀 Usage

Run the converter from the project root:

```bash
python3 scripts/pdf_tool/converter.py <INPUT_FILE> [OPTIONS]
```

### ⌨️ Quick Start with Makefile
For convenience, a `Makefile` is provided in the **project root** to quickly generate common formats:

```bash
make a4 docs/your-file.md      # Official A4 Report (Business)
make poster docs/your-file.md  # Professional Long-Scroll (Business)
make glass docs/your-file.md   # Glass-Style A4 Report (Council)
make mobile docs/your-file.md  # Mobile-Optimized Poster (Council)
```

### Examples

**1. Generate a Standard A4 Product Poster (Default)**
Wraps sections in glass cards, uses the Council Poster theme, A4 width.
```bash
python3 scripts/pdf_tool/converter.py docs/PRD.md --glass-cards --width 210mm
```

**2. Generate a Long-Scroll Mobile Poster**
Good for sharing on mobile devices. Uses pixel width.
```bash
python3 scripts/pdf_tool/converter.py docs/methodology/AI_DRIVEN_PRODUCT_PROCESS.md --glass-cards --width 450px
```

**3. Generate a Standard Document (No Glass Cards)**
Just a clean PDF conversion.
```bash
python3 scripts/pdf_tool/converter.py docs/TDD.md
```

## ⚙️ Options

| Argument         | Description                                                  | Default                |
| :--------------- | :----------------------------------------------------------- | :--------------------- |
| `input`          | Path to the input Markdown file.                             | (Required)             |
| `-o`, `--output` | Path to the output PDF file.                                 | Same as input filename |
| `--theme`        | Name of the CSS file in `themes/`.                           | `council_poster.css`   |
| `--width`        | PDF Width (e.g., `210mm`, `1200px`).                         | `210mm`                |
| `--glass-cards`  | Enable special "Glass Card" layout wrapping for H2 sections. | `False`                |

## 🎨 Themes

Themes are located in `scripts/pdf_tool/themes/`.
*   **`council_poster.css`**: The default Flat-Glass style, optimized for mobile performance and clean aesthetics.
*   **`business_formal.css`**: (New) A professional, high-authority theme designed for official reports and executive summaries. Uses deep navy accents and sharp typography.

To add a new theme, simply create a `.css` file in the `themes/` directory and reference it via `--theme your_theme.css`.
