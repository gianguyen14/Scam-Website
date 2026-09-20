const puppeteer = require('puppeteer');
const path = require('path');

(async () => {
    const extensionPath = path.join(__dirname, 'extension');
    const browser = await puppeteer.launch({
        headless: "new",
        args: [
            '--no-sandbox', 
            '--disable-web-security',
            `--disable-extensions-except=${extensionPath}`,
            `--load-extension=${extensionPath}`
        ]
    });

    const runScenario = async (name, mockUrl, mockHtml) => {
        console.log(`\n--- RUNNING SCENARIO: ${name} ---`);
        const page = await browser.newPage();
        await page.setRequestInterception(true);
        page.on('request', req => {
            if (req.url() === mockUrl) {
                req.respond({ status: 200, contentType: 'text/html', body: mockHtml });
            } else {
                req.continue();
            }
        });

        await page.goto(mockUrl, { waitUntil: 'domcontentloaded' });
        
        let finalUrl = page.url();
        for (let i = 0; i < 30; i++) {
            await new Promise(r => setTimeout(r, 100));
            finalUrl = page.url();
            
            if (finalUrl.includes('warning.html')) break;
        }
        
        let apiLog = await page.evaluate(() => {
            return new Promise((resolve) => {
                chrome.storage.local.get(['scanHistory'], (db) => {
                    if (db.scanHistory && db.scanHistory.length > 0) {
                        resolve(db.scanHistory[0]);
                    } else resolve(null);
                });
            });
        });
        console.log("-> Backend Trả về: ", apiLog ? apiLog.score + ' (' + apiLog.level + ')' : "Không có response từ backend");

        }

        if (finalUrl.includes('warning.html')) {
            const urlObj = new URL(finalUrl);
            const score = urlObj.searchParams.get('score');
            const reasons = JSON.parse(decodeURIComponent(urlObj.searchParams.get('reasons') || '[]'));
            console.log(`[BLOCKED] Score: ${score}/100`);
            console.log(`[REASONS]: \n - ${reasons.join('\n - ')}`);
        } else {
            console.log(`[PASSED] URL: ${finalUrl}`);
        }
        await page.close();
    };

    // Scenario 1: Web3 Crypto Drainer
    await runScenario(
        "Web3 Crypto Drainer",
        "http://127.0.0.1:8080/claim-airdrop",
        `<html><body>
            <h2>Airdrop Allocation</h2>
            <label>Verify Wallet:</label>
            <input type="text" placeholder="Enter secret recovery phrase to continue" />
            <button>Connect</button>
        </body></html>`
    );

    // Scenario 2: Giả mạo cơ quan nhà nước (Phạt Nguội)
    await runScenario(
        "Fake Traffic Police (Phạt Nguội)",
        "http://127.0.0.1:8080/tra-cuu-phat-nguoi",
        `<html><body>
            <h1>Cổng thông tin Cục cảnh sát giao thông</h1>
            <p>Tra cứu phạt nguội vi phạm. Yêu cầu nộp phạt khẩn cấp.</p>
            <input type="text" placeholder="Biển số xe" />
        </body></html>`
    );

    // Scenario 3: Trộm danh tính thẻ (CVV Scam)
    await runScenario(
        "Credit Card Identity Theft",
        "http://127.0.0.1:8080/verify-account",
        `<html><body>
            <center>Tài khoản bị khóa tạm thời</center>
            <form>
                Số thẻ: <input type="text" />
                Mã bảo mật CVV: <input type="password" />
            </form>
        </body></html>`
    );

    await browser.close();
})();
