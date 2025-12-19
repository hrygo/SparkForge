#!/usr/bin/env python3
import sys
import os
import argparse
import subprocess
import markdown
import re
from jinja2 import Environment, FileSystemLoader

def main():
    parser = argparse.ArgumentParser(description="Universal Markdown to PDF Converter (Council Engine)")
    parser.add_argument("input", help="Path to input Markdown file")
    parser.add_argument("-o", "--output", help="Path to output PDF file (default: same as input)")
    parser.add_argument("--theme", default="council_poster.css", help="Theme CSS file name (in themes/ dir)")
    parser.add_argument("--width", default="210mm", help="PDF Width (e.g. 210mm, 1200px)")
    parser.add_argument("--glass-cards", action="store_true", help="Enable Glass Card layout wrapping")
    parser.add_argument("--a4", action="store_true", help="Use standard A4 pagination instead of long scroll")
    
    args = parser.parse_args()
    
    # Paths
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../'))
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    md_path = os.path.abspath(args.input)
    if not os.path.exists(md_path):
        print(f"Error: Input file not found: {md_path}")
        sys.exit(1)
        
    # Determine Output Path
    if args.output:
        pdf_path = os.path.abspath(args.output)
    else:
        pdf_path = os.path.splitext(md_path)[0] + ".pdf"
    
    html_path = os.path.splitext(pdf_path)[0] + ".html"
    
    # 1. Read Markdown
    with open(md_path, 'r', encoding='utf-8') as f:
        md_content = f.read()

    # Pre-process: Fix lists (ensure blank lines)
    md_content = re.sub(r'(:|：)\n(-|\*|\d+\.) ', r'\1\n\n\2 ', md_content)

    # Pre-process: Wrap Mermaid
    md_content = re.sub(r'```mermaid\n(.*?)```', 
                       r'<div class="mermaid">\1</div>', 
                       md_content, flags=re.DOTALL)
    
    # Pre-process: Wrap Images
    md_content = re.sub(r'!\[(.*?)\]\((.*?)\)', 
                       r'<figure class="main-visual"><img src="\2" alt="\1"><figcaption>\1</figcaption></figure>', 
                       md_content)

    # 2. Convert to HTML
    html_body = markdown.markdown(md_content, extensions=['tables', 'fenced_code', 'toc', 'sane_lists'])

    # 3. Post-Process HTML (Laytout Plugins)
    if args.glass_cards:
        # Wrap H2 sections in glass cards
        html_body = re.sub(
            r'(<h2.*?>[\s\S]*?)(?=<h2|\Z)', 
            r'<section class="glass-card">\1</section>', 
            html_body
        )

    # 4. Render Template
    env = Environment(loader=FileSystemLoader(os.path.join(script_dir, 'templates')))
    template = env.get_template('layout.html')
    
    # Resolve CSS Path (Absolute for local rendering)
    theme_path = os.path.join(script_dir, 'themes', args.theme)
    if not os.path.exists(theme_path):
        print(f"Warning: Theme not found: {theme_path}, falling back to council_poster.css")
        theme_path = os.path.join(script_dir, 'themes', 'council_poster.css')
        
    body_classes = []
    if args.glass_cards:
        body_classes.append("glass-theme")
    if args.a4:
        body_classes.append("paginated-mode")
        
    final_html = template.render(
        title=os.path.basename(md_path),
        content=html_body,
        theme_css_path='file://' + theme_path,
        body_class=" ".join(body_classes)
    )
    
    with open(html_path, 'w', encoding='utf-8') as f:
        f.write(final_html)
        
    print(f"✅ HTML Generated: {html_path}")
    
    # 5. Call Node Renderer
    renderer_script = os.path.join(script_dir, 'renderer.js')
    print(f"🚀 Rendering PDF ({'A4 Pagination' if args.a4 else args.width})...")
    
    cmd = ['node', renderer_script, html_path, pdf_path, args.width]
    if args.a4:
        cmd.append('--a4')

    try:
        subprocess.run(cmd, check=True)
        print(f"🎉 PDF Generated Successfully: {pdf_path}")
    except subprocess.CalledProcessError:
        print("❌ PDF Rendering Failed.")
        sys.exit(1)
    except FileNotFoundError:
        print("❌ Error: 'node' not found.")
        sys.exit(1)

if __name__ == "__main__":
    main()
