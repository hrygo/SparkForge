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
            // Match A4 margins for consistency
            pdfOptions.margin = { top: '20mm', right: '15mm', bottom: '20mm', left: '15mm' };
        } else {
            // Calculate flexible height
            const bodyHeight = await page.evaluate(() => document.body.scrollHeight + 50);
            console.log(`Mode: Long Scroll (${width} x ${bodyHeight}px)`);
            pdfOptions.width = width;
            pdfOptions.height = `${bodyHeight}px`;
            pdfOptions.margin = { top: '0', right: '0', bottom: '0', left: '0' };
        }

        await page.pdf(pdfOptions);

        await browser.close();
        console.log(`PDF saved to: ${outputPath}`);

    } catch (error) {
        console.error('Error during PDF generation:', error);
        process.exit(1);
    }
})();
