const puppeteer = require('puppeteer');
const fs = require('fs');
const path = require('path');

// CLI Arguments: input_html, output_pdf, width, height (optional)
const args = process.argv.slice(2);

if (args.length < 2) {
    console.error("Usage: node renderer.js <input_html_path> <output_pdf_path> [width]");
    process.exit(1);
}

const inputPath = args[0];
const outputPath = args[1];
const width = args[2] || '210mm';
const isA4 = args.includes('--a4');
const isA3 = args.includes('--a3');

(async () => {
    try {
        const browser = await puppeteer.launch({
            headless: "new",
            args: ['--no-sandbox', '--disable-setuid-sandbox']
        });
        const page = await browser.newPage();

        // Convert file path to file:// URL
        const fileUrl = 'file://' + path.resolve(inputPath);
        console.log(`Rendering: ${fileUrl}`);

        await page.goto(fileUrl, { waitUntil: 'networkidle0' });

        // Wait for mermaid diagrams if they exist
        try {
            await page.waitForSelector('.mermaid svg', { timeout: 10000 });
            console.log('Mermaid diagrams rendered.');
        } catch (e) {
            console.log('No Mermaid diagrams found or timed out. Proceeding...');
        }

        // --- BOOKMARK EXTRACTION STRATEGY ---
        // We calculate the position of headers to estimate page numbers.
        // Standard A4: 297mm height. Puppeteer 96DPI: 1px = 0.264583mm. 
        // A4 Height in px = 1122.5px.
        // We need to account for margins if they affect the content flow, but Puppeteer's 
        // element.offsetTop is relative to the document body start.

        let bookmarks = [];

        if (!args.includes('--hydrate')) { // Only need bookmarks for final PDF
            bookmarks = await page.evaluate((isA4, isA3) => {
                const results = [];
                // Define page height in pixels (Approx 96 DPI)
                // A4: 297mm = 1122px; A3: 420mm = 1587px
                // Margin deduction: Top 20mm + Bottom 20mm = 40mm (~151px)
                // Content Height per page = Total Height - Margins? 
                // Actually, Puppeteer visual viewport paging is complex.
                // Simple heuristic: Total Height / Page Height.

                let PAGE_HEIGHT = 1122; // A4 Default
                if (isA3) PAGE_HEIGHT = 1587;
                // If using margins, the content flow is truncated. 
                // BUT offsetTop is absolute. 
                // A safer heuristic for Puppeteer with standard print settings:
                // Page N = Math.floor(offsetTop / (PAGE_HEIGHT - MARGIN_PADDING)) + 1
                // Let's assume standard formatting.

                // Effective content height per page roughly (minus 40mm margins)
                const EFFECTIVE_HEIGHT = PAGE_HEIGHT - 151;

                // Select headers
                const headers = document.querySelectorAll('h1, h2, .spec-title');

                headers.forEach(header => {
                    // Must use window.scrollY to get absolute document position
                    const rect = header.getBoundingClientRect();
                    const absoluteTop = rect.top + window.scrollY;

                    // Estimate Page Number (1-based)
                    // We assume 1px = 1px in PDF (Scale 1)
                    // A4 PDF Height @ 96DPI = 1123px.
                    // Total Vertical Margin = 40mm ≈ 151px.
                    // Content Area Height = 1123 - 151 = 972px.
                    // Ideally, we should add a small 'fudge factor' or check where breaks happen.
                    // But strictly: Page = floor(Y / ContentHeight)

                    const pageNum = Math.floor(absoluteTop / 972);

                    results.push({
                        title: header.innerText.replace(/^Appendix: /, ''),
                        page: pageNum, // 0-based for internal logic? No, let's store 0-based index directly.
                        level: header.tagName === 'H1' ? 1 : 2,
                        top: absoluteTop
                    });
                });
                return results;
            }, isA4, isA3);

            // Save bookmarks to file
            const bookmarkPath = outputPath + '.bookmarks.json';
            fs.writeFileSync(bookmarkPath, JSON.stringify(bookmarks, null, 2));
            console.log(`📑 Bookmark metadata saved: ${bookmarkPath}`);
        }

        if (args.includes('--hydrate')) {
            // Removed legacy hydration logic
        }

        // Regular PDF Logic
        const pdfOptions = {
            path: outputPath,
            printBackground: true,
            displayHeaderFooter: false,
        };

        if (isA4) {
            console.log("Mode: Standard A4 Pagination");
            pdfOptions.format = 'A4';
            pdfOptions.margin = { top: '20mm', right: '15mm', bottom: '20mm', left: '15mm' };
        } else if (isA3) {
            console.log("Mode: Standard A3 Pagination");
            pdfOptions.format = 'A3';
            pdfOptions.margin = { top: '20mm', right: '15mm', bottom: '20mm', left: '15mm' };
        } else {
            const bodyHeight = await page.evaluate(() => document.body.scrollHeight + 50);
            console.log(`Mode: Long Scroll (${width} x ${bodyHeight}px)`);
            pdfOptions.width = width;
            pdfOptions.height = `${bodyHeight}px`;
            pdfOptions.margin = { top: '0', right: '0', bottom: '0', left: '0' };
        }

        await page.pdf(pdfOptions);
        console.log(`PDF saved to: ${outputPath}`);

        await browser.close();

    } catch (error) {
        console.error('Error during PDF generation:', error);
        process.exit(1);
    }
})();
