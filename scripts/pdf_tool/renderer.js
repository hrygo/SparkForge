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
const width = args[2] || '210mm'; // Default to A4 width

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
            await page.waitForSelector('.mermaid svg', { timeout: 5000 });
            console.log('Mermaid diagrams rendered.');
        } catch (e) {
            console.log('No Mermaid diagrams found or timed out. Proceeding...');
        }

        // Calculate flexible height
        const bodyHeight = await page.evaluate(() => document.body.scrollHeight + 50);
        console.log(`Generating PDF: ${width} x ${bodyHeight}px`);

        await page.pdf({
            path: outputPath,
            width: width,
            height: `${bodyHeight}px`,
            printBackground: true,
            displayHeaderFooter: false,
            margin: { top: '0', right: '0', bottom: '0', left: '0' }
        });

        await browser.close();
        console.log(`PDF saved to: ${outputPath}`);

    } catch (error) {
        console.error('Error during PDF generation:', error);
        process.exit(1);
    }
})();
