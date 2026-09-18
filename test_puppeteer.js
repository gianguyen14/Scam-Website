const puppeteer = require('puppeteer');
const http = require('http');
const fs = require('fs');
const path = require('path');

const server = http.createServer((req, res) => {
    let filePath = path.join(__dirname, 'test-sites', 'fixtures', req.url === '/' ? 'benign.html' : req.url);
    if (fs.existsSync(filePath)) {
        res.writeHead(200, { 'Content-Type': 'text/html' });
        res.end(fs.readFileSync(filePath));
    } else {
        res.writeHead(404);
        res.end();
    }
});

server.listen(8080, async () => {
    console.log("Fixture server running on 8080");
    
    const extensionPath = path.join(__dirname, 'extension');
    
    let browser;
    try {
        browser = await puppeteer.launch({
            headless: "new",
            args: [
                '--no-sandbox', '--disable-web-security', 
                '--disable-setuid-sandbox',
                `--disable-extensions-except=${extensionPath}`,
                `--load-extension=${extensionPath}`
            ]
        });

        
        // Find extension background worker
        browser.on('targetcreated', async target => {
            if (target.type() === 'service_worker') {
                const worker = await target.worker();
                worker.on('console', msg => console.log('WORKER LOG:', msg.text()));
            }
        });
        
        const targets = await browser.targets();
        targets.forEach(async target => {
            if (target.type() === 'service_worker') {
                const worker = await target.worker();
                worker.on('console', msg => console.log('WORKER LOG:', msg.text()));
            }
        });
        
        const page1 = await browser.newPage();

        page1.on('console', msg => console.log('PAGE LOG:', msg.text()));
        page1.on('pageerror', error => console.log('PAGE ERROR:', error.message));

        console.log("Going to phishing page...");
        await page1.goto('http://127.0.0.1:8080/phishing.html', { waitUntil: 'load' });
        
        // Wait maximum 5 seconds for the URL to change to the WARNING page.
        // background.js uses chrome.tabs.update() !
        let finalUrl = page1.url();
        for (let i = 0; i < 50; i++) {
            await new Promise(r => setTimeout(r, 100)); // 100ms
            finalUrl = page1.url();
            if (finalUrl.includes('warning.html')) {
                break;
            }
        }
        
        if (!finalUrl.includes('warning.html')) {
             throw new Error("Phishing page didn't redirect to warning.html. Still at: " + finalUrl);
        }
        
        console.log("Warning Page E2E PASS");
        
        // Let's verify privacy by checking a log dumped by FastAPI
        if (fs.existsSync('payload.log')) {
             const payload = fs.readFileSync('payload.log', 'utf8');
             if (payload.includes('SECRET_PASSWORD') || payload.includes('123456')) {
                 throw new Error("PRIVACY VIOLATION: Sensitive data was found in backend payload!");
             }
        } else {
             throw new Error("Backend did not dump payload.");
        }
        console.log("Privacy Test PASS");

        console.log("All E2E Tests Pass");
        process.exit(0);
    } catch (e) {
        console.error("E2E FAIL:", e);
        process.exit(1);
    } finally {
        if (browser) await browser.close();
        server.close();
    }
});
