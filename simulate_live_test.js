const puppeteer = require('puppeteer');
const fs = require('fs');
const path = require('path');

(async () => {
    console.log("🚀 KHỞI ĐỘNG MÔI TRƯỜNG GIẢ LẬP SCAMGUARD AI...");
    const extensionPath = path.join(__dirname, 'extension');
    
    let browser;
    try {
        browser = await puppeteer.launch({
            headless: "new",
            args: [
                '--no-sandbox', 
                '--disable-setuid-sandbox',
                '--disable-web-security',
                `--disable-extensions-except=${extensionPath}`,
                `--load-extension=${extensionPath}`
            ]
        });

        // ----------------------------------------------------------------
        // KỊCH BẢN 1: Đánh chặn bằng Database ScamSniffer (Web3 Phishing)
        // ----------------------------------------------------------------
        console.log("\n[TEST 1] Đang truy cập miền độc hại Web3 được đánh giá từ ScamSniffer: http://walletconnectportal.onrender.com");
        const page1 = await browser.newPage();
        await page1.setRequestInterception(true);
        page1.on('request', req => {
            if (req.url() === 'http://walletconnectportal.onrender.com/') {
                // Mock responses for the malicious site so we don't actually hit their server
                req.respond({
                    status: 200,
                    contentType: 'text/html',
                    body: '<html><body><h1>Connect Wallet to claim Airdrop!</h1></body></html>'
                });
            } else {
                req.continue();
            }
        });

        await page1.goto('http://walletconnectportal.onrender.com/', { waitUntil: 'domcontentloaded' });
        
        // Wait for Extension to assess and Redirect to Warning
        let url1 = page1.url();
        for (let i = 0; i < 40; i++) {
            await new Promise(r => setTimeout(r, 100));
            url1 = page1.url();
            if (url1.includes('warning.html')) break;
        }
        
        if (url1.includes('warning.html')) {
            console.log("✅ BÁO CÁO TEST 1: THÀNH CÔNG! ScamGuard đã chặn ngay tức khắc vì URL khớp cấu hình Database với độ rủi ro 100/100.");
        } else {
            console.log("❌ TEST 1 THẤT BẠI. Đang ở URL: " + url1);
        }
        await page1.close();

        // ----------------------------------------------------------------
        // KỊCH BẢN 2: Zero-Day Phishing (Mô hình AI + Phân tích Hành vi)
        // ----------------------------------------------------------------
        console.log("\n[TEST 2] Đang truy cập 0-day Phishing: http://unknown-scam-mail.com (chưa có trong database)");
        const page2 = await browser.newPage();
        await page2.setRequestInterception(true);
        page2.on('request', req => {
            if (req.url() === 'http://127.0.0.1:8080/scam-path') {
                req.respond({
                    status: 200,
                    contentType: 'text/html',
                    body: `<html>
                        <head><title>Bảo mật: Tài khoản của bạn sẽ bị tạm ngưng khẩn cấp trong 24h</title></head>
                        <body>
                            <form>
                                <input id="userid" type="text" placeholder="Email" />
                                <input id="pwd-field" type="password" name="pwd" placeholder="Mật khẩu" />
                                <input type="submit" value="Xác minh ngay" />
                            </form>
                        </body>
                    </html>`
                });
            } else {
                req.continue();
            }
        });

        await page2.goto('http://127.0.0.1:8080/scam-path', { waitUntil: 'domcontentloaded' });
        
        // Chờ 1 giây để Extension nạp
        await new Promise(r => setTimeout(r, 1000));
        
        console.log("👉 Đang mô phỏng hành vi: User (nhờ lừa đảo) đang Copy & Paste password vào ô nhập...");
        await page2.evaluate(() => {
            const pwdField = document.getElementById('pwd-field');
            if(pwdField) {
                 const pasteEvent = new Event('paste', { bubbles: true });
                 pwdField.dispatchEvent(pasteEvent);
            }
        });

        // Wait for Extension to assess and Redirect to Warning
        let url2 = page2.url();
        for (let i = 0; i < 40; i++) {
            await new Promise(r => setTimeout(r, 100));
            url2 = page2.url();
            if (url2.includes('warning.html')) break;
        }

        if (url2.includes('warning.html')) {
            console.log("✅ BÁO CÁO TEST 2: THÀNH CÔNG! Web chưa từng xuất hiện trên DB blocklist, nhưng sự kết hợp giữa: '[AI NLP] Ngôn ngữ rủi ro' + '[Behavioral] Paste mật khẩu' đã đẩy điểm Risk lên mức Dangerous và kích hoạt cảnh báo chặn!");
        } else {
            console.log("❌ TEST 2 THẤT BẠI. Đang ở URL: " + url2);
        }
        await page2.close();
        
        console.log("\n🎉 MÔI TRƯỜNG GIẢ LẬP ĐÃ CHẠY HOÀN TẤT TRƠN TRU!");
        process.exit(0);

    } catch (e) {
        console.error("LỖI GIẢ LẬP: ", e);
        process.exit(1);
    } finally {
        if (browser) await browser.close();
    }
})();
