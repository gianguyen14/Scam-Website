
const fs = require('fs');
const jsdom = require('jsdom');
const { JSDOM } = jsdom;

const contentJS = fs.readFileSync('extension/content.js', 'utf8');

function testSite(htmlFile) {
    const html = fs.readFileSync(htmlFile, 'utf8');
    const dom = new JSDOM(html, { url: "http://localhost/", runScripts: "dangerously" });
    const window = dom.window;
    
    // Setup mock chrome API
    window.chrome = {
        runtime: {
            onMessage: { addListener: () => {} }
        }
    };
    
    // Inject and execute
    const script = dom.window.document.createElement("script");
    script.textContent = contentJS + "\nwindow.scanDOMResult = scanDOM();";
    dom.window.document.body.appendChild(script);
    
    return window.scanDOMResult;
}

try {
    const fakeBank = testSite('test-sites/fake-bank/index.html');
    console.log(fakeBank);
    if (!fakeBank.has_password) throw new Error("Missing password");
    if (!fakeBank.has_otp) throw new Error("Missing OTP");
    if (!fakeBank.external_form_action) throw new Error("Missing external form action");
    if (fakeBank.hidden_iframe_count !== 1) throw new Error("Missing hidden iframe");
    if (!fakeBank.button_labels.includes("Login Now")) throw new Error("Missing button label");
    
    console.log("PASS: Phase 2 DOM Scanner Tests");
} catch(e) {
    console.error("FAIL:", e);
    process.exit(1);
}
