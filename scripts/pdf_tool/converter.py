#!/usr/bin/env python3
import sys
import os
import argparse
import subprocess
import markdown
import re
import glob
import signal
import warnings
import shutil
import pikepdf
from jinja2 import Environment, FileSystemLoader

# ... (Imports cleaned up below)

# Helper Functions
def get_anchor_id(filepath):
    """Generate a stable anchor ID from a file path."""
    name = os.path.splitext(os.path.basename(filepath))[0]
    return f"doc-{re.sub(r'[^a-zA-Z0-9]', '-', name).lower()}"

def resolve_link(link_target, current_file_path, file_registry):
    """
    Resolve a link target to an internal anchor ID if it exists in the registry.
    """
    if link_target.startswith(('http://', 'https://', 'mailto:', '#')):
        return link_target
    
    current_dir = os.path.dirname(os.path.abspath(current_file_path))
    if os.path.isabs(link_target):
        target_abs = os.path.normpath(link_target)
    else:
        target_abs = os.path.normpath(os.path.join(current_dir, link_target))
        
    if target_abs in file_registry:
        return f"#{file_registry[target_abs]}"
    
    return link_target

def resolve_image_path(img_src, current_file_path):
    """Convert relative image paths to absolute paths."""
    if img_src.startswith(('http://', 'https://', 'data:')):
        return img_src
    
    current_dir = os.path.dirname(os.path.abspath(current_file_path))
    if os.path.isabs(img_src):
        abs_path = img_src
    else:
        abs_path = os.path.normpath(os.path.join(current_dir, img_src))
    return abs_path

def process_file_content(filepath, file_registry, is_spec_file=False):
    """Read file, rewrite links/images, and prepare for merging."""
    with open(filepath, 'r', encoding='utf-8') as f:
        raw_content = f.read()

    # Pre-process: Fix lists (ensure blank lines)
    raw_content = re.sub(r'(:|：)\n(-|\*|\d+\.) ', r'\1\n\n\2 ', raw_content)

    if is_spec_file:
        # Standardize Spec Files
        filename = os.path.basename(filepath)
        anchor = file_registry[filepath]
        import html
        escaped_content = html.escape(raw_content)
        
        header = f'\n\n<div id="{anchor}" class="spec-source-container">\n'
        header += f'<h2 class="spec-title">Appendix: {filename}</h2>\n'
        header += f'<pre class="source-code"><code class="language-markdown">{escaped_content}</code></pre>\n'
        header += '</div>\n\n'
        return header
    
    # --- Normal Processing ---
    content = raw_content

    # Rewrite Links
    def link_replacer(match):
        text = match.group(1)
        target = match.group(2)
        new_target = resolve_link(target, filepath, file_registry)
        return f"[{text}]({new_target})"
    content = re.sub(r'(?<!!)\[(.*?)\]\((.*?)\)', link_replacer, content)
    
    # Rewrite Images
    def img_replacer(match):
        alt = match.group(1)
        src = match.group(2)
        new_src = resolve_image_path(src, filepath)
        return f"![{alt}]({new_src})"
    content = re.sub(r'!\[(.*?)\]\((.*?)\)', img_replacer, content)

    # Wrap Mermaid
    content = re.sub(r'```mermaid\n(.*?)```', 
                       r'<div class="mermaid">\1</div>', 
                       content, flags=re.DOTALL)
    
    # Wrap Images for Layout
    content = re.sub(r'!\[(.*?)\]\((.*?)\)', 
                       r'<figure class="main-visual"><img src="\2" alt="\1"><figcaption>\1</figcaption></figure>', 
                       content)
    
    anchor = file_registry[filepath]
    header_marker = f'<div id="{anchor}" class="doc-anchor" style="position:relative; top:-20px;"></div>\n\n'
    return header_marker + content

def render_html_to_pdf_puppeteer(html_path, pdf_path, width, is_a4=False, is_a3=False):
    """Call the node renderer to convert HTML to PDF."""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    renderer_script = os.path.join(script_dir, 'renderer.js')
    
    cmd = ['node', renderer_script, html_path, pdf_path, width]
    if is_a4: cmd.append('--a4')
    if is_a3: cmd.append('--a3')
    
    try:
        subprocess.run(cmd, check=True)
        return True
    except subprocess.CalledProcessError:
        print(f"❌ Failed to render {html_path}")
        return False

def main():
    parser = argparse.ArgumentParser(description="Universal Markdown to PDF Converter (Council Engine)")
    parser.add_argument("inputs", nargs='+', help="Path to input Markdown files or directories")
    parser.add_argument("-o", "--output", help="Path to output PDF file")
    parser.add_argument("--theme", default="council_poster.css", help="Theme CSS file")
    parser.add_argument("--width", default="210mm", help="PDF Width")
    parser.add_argument("--glass-cards", action="store_true", help="Enable Glass Card layout")
    parser.add_argument("--a4", action="store_true", help="Use standard A4 pagination")
    parser.add_argument("--a3", action="store_true", help="Use standard A3 pagination")
    
    args = parser.parse_args()
    script_dir = os.path.dirname(os.path.abspath(__file__))

    # 1. Collect Files
    files_to_process = []
    specs_files = set()
    for inp in args.inputs:
        abs_inp = os.path.abspath(inp)
        if os.path.isdir(abs_inp):
            found_files = sorted(glob.glob(os.path.join(abs_inp, "*.md")))
            is_specs_dir = "specs" in os.path.basename(abs_inp) or "specs" in abs_inp.split(os.sep)
            for f in found_files:
                f_abs = os.path.abspath(f)
                if f_abs not in [x for x in files_to_process]:
                    files_to_process.append(f_abs)
                    if is_specs_dir: specs_files.add(f_abs)
        elif os.path.isfile(abs_inp):
            if abs_inp not in files_to_process:
                files_to_process.append(abs_inp)
                if "specs" in os.path.basename(os.path.dirname(abs_inp)):
                    specs_files.add(abs_inp)

    if not files_to_process:
        print("Error: No files found.")
        sys.exit(1)

    # 2. Global Registry & Content Merging
    file_registry = {f: get_anchor_id(f) for f in files_to_process}
    
    print(f"🚀 Merging {len(files_to_process)} documents...")
    
    full_md_content = ""
    
    for filepath in files_to_process:
        is_spec = filepath in specs_files
        # Process and link files
        segment_content = process_file_content(filepath, file_registry, is_spec_file=is_spec)
        full_md_content += segment_content + "\n\n"

    # 3. HTML Conversion
    # Extensions: toc is needed for [TOC] tags, even if we build PDF outline separately
    html_body = markdown.markdown(full_md_content, extensions=['tables', 'fenced_code', 'toc', 'sane_lists'])
    
    # Layout Plugins
    if args.glass_cards:
        html_body = re.sub(r'(<h2.*?>[\s\S]*?)(?=<h2|\Z)', r'<section class="glass-card">\1</section>', html_body)

    # Template Loader
    env = Environment(loader=FileSystemLoader(os.path.join(script_dir, 'templates')))
    template = env.get_template('layout.html')

    # Resolve Theme
    theme_path = os.path.join(script_dir, 'themes', args.theme)
    if not os.path.exists(theme_path):
        theme_path = os.path.join(script_dir, 'themes', 'council_poster.css')
        
    body_classes = []
    if args.glass_cards: body_classes.append("glass-theme")
    if args.a4 or args.a3: body_classes.append("paginated-mode")
    if args.a4: body_classes.append("mode-a4")
    if args.a3: body_classes.append("mode-a3")
    
    # Output Paths
    temp_dir = os.path.join(script_dir, "temp_build")
    if not os.path.exists(temp_dir): os.makedirs(temp_dir)
    
    if args.output:
        final_pdf_path = os.path.abspath(args.output)
    elif files_to_process:
        # Default output to docs/output/ directory
        first_input = files_to_process[0]
        base_name = os.path.splitext(os.path.basename(first_input))[0]
        
        # Suffix logic
        suffix = ""
        if args.glass_cards: suffix += "_glass"
        if args.a4: suffix += "_A4"
        elif args.a3: suffix += "_A3"
        elif args.width == "210mm": suffix += "_poster" # Implicit poster logic for default width
        
        # Find project root (where docs/ is located)
        project_root = os.path.dirname(os.path.dirname(script_dir))
        output_dir = os.path.join(project_root, "docs", "output")
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        final_pdf_path = os.path.join(output_dir, f"{base_name}{suffix}.pdf")
    else:
        final_pdf_path = os.path.join(os.getcwd(), "output.pdf")
        
    temp_html_path = os.path.join(temp_dir, "merged_full.html")
    temp_pdf_path = os.path.join(temp_dir, "merged_full.pdf") # Intermediate Puppeteer Output

    # Render HTML
    final_html = template.render(
        title="Mermaid Document",
        content=html_body,
        theme_css_path='file://' + theme_path,
        body_class=" ".join(body_classes)
    )
    
    with open(temp_html_path, 'w', encoding='utf-8') as f:
        f.write(final_html)
        
    # 4. Render PDF (Puppeteer)
    print(f"🎨 Rendering high-fidelity PDF (Puppeteer)...")
    success = render_html_to_pdf_puppeteer(temp_html_path, temp_pdf_path, args.width, args.a4, args.a3)
    
    if not success:
        sys.exit(1)
        
    # 5. Inject Bookmarks (from generated JSON)
    json_path = temp_pdf_path + '.bookmarks.json'
    
    if os.path.exists(json_path):
        print("📑 Injecting intelligent bookmarks...")
        import json
        with open(json_path, 'r') as f:
            bookmarks = json.load(f)
            
        # Use Pikepdf to splice bookmarks
        pdf = pikepdf.Pdf.open(temp_pdf_path)
        with pdf.open_outline() as outline:
            # Simplified Flat Outline Injection
            # To avoid API complexity/errors with hierarchy, we inject all as top-level for now.
            # This ensures robustness.
            
            for b in bookmarks:
                title = b['title']
                page_idx = b['page'] # Renderer now returns 0-based index
                
                # Safety limits
                if page_idx < 0: page_idx = 0
                if page_idx >= len(pdf.pages): page_idx = len(pdf.pages) - 1
                
                try:
                    # FIX: Use raw list for destination [PageObject, /Type, (args...)]
                    # This works across all pikepdf versions
                    page_obj = pdf.pages[page_idx].obj
                    dest = [page_obj, pikepdf.Name("/Fit")]
                    item = pikepdf.OutlineItem(title, dest)
                    outline.root.append(item)
                except Exception as e:
                    print(f"Warning: Bookmark error {title}: {e}")
        
        pdf.save(final_pdf_path)
        print(f"🎉 Final PDF Generated: {final_pdf_path}")
    else:
        print("⚠️ No bookmark metadata found. Saving raw PDF.")
        shutil.copy(temp_pdf_path, final_pdf_path)
        
    # Cleanup
    shutil.rmtree(temp_dir)

if __name__ == "__main__":
    main()
