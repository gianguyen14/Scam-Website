
// Phase 2: DOM Scanner (Privacy First)

function scanDOM() {
    const data = {
        title: document.title || "",
        has_password: false,
        has_otp: false,
        has_email: false,
        has_phone: false,
        has_credit_card: false,
        has_login_form: false,
        external_form_action: false,
        iframe_count: 0,
        hidden_iframe_count: 0,
        download_link_count: 0,
        button_labels: [], // avoid too many, just keep a few text snippets
        form_count: 0,
        external_link_count: 0
    };

    // Form scanning
    const forms = document.querySelectorAll('form');
    data.form_count = forms.length;
    
    forms.forEach(form => {
        // Check for external action
        if (form.action) {
            try {
                const actionUrl = new URL(form.action, window.location.href);
                if (actionUrl.hostname && actionUrl.hostname !== window.location.hostname) {
                    data.external_form_action = true;
                }
            } catch(e) {}
        }
    });

    // Input fields scanning
    const inputs = document.querySelectorAll('input, select, textarea');
    inputs.forEach(input => {
        const type = (input.getAttribute('type') || '').toLowerCase();
        const name = (input.getAttribute('name') || '').toLowerCase();
        const id = (input.getAttribute('id') || '').toLowerCase();
        const placeholder = (input.getAttribute('placeholder') || '').toLowerCase();
        
        const combinedString = `${type} ${name} ${id} ${placeholder}`;

        if (type === 'password' || combinedString.includes('password') || combinedString.includes('pwd')) {
            data.has_password = true;
            data.has_login_form = true;
        }

        if (combinedString.includes('otp') || combinedString.includes('one time password') || combinedString.includes('verification code') || combinedString.includes('mfa')) {
            data.has_otp = true;
        }

        if (type === 'email' || combinedString.includes('email') || combinedString.includes('e-mail')) {
            data.has_email = true;
        }

        if (type === 'tel' || combinedString.includes('phone') || combinedString.includes('mobile')) {
            data.has_phone = true;
        }

        if (combinedString.includes('card') || combinedString.includes('ccv') || combinedString.includes('cvv') || combinedString.includes('credit')) {
            data.has_credit_card = true;
        }
    });

    // iFrames
    const iframes = document.querySelectorAll('iframe');
    data.iframe_count = iframes.length;
    iframes.forEach(iframe => {
        const style = window.getComputedStyle(iframe);
        if (style.display === 'none' || style.visibility === 'hidden' || iframe.width === '0' || iframe.height === '0' || style.opacity === '0') {
            data.hidden_iframe_count++;
        }
    });

    // Links
    const links = document.querySelectorAll('a');
    links.forEach(a => {
        const href = a.getAttribute('href');
        if (href) {
            // Check download link
            if (a.hasAttribute('download') || href.match(/\.(zip|exe|apk|dmg|tar|gz|sh|bat)$/i)) {
                data.download_link_count++;
            }
            
            // Check external
            try {
                const url = new URL(href, window.location.href);
                if (url.hostname && url.hostname !== window.location.hostname && !href.startsWith('mailto:') && !href.startsWith('tel:')) {
                    data.external_link_count++;
                }
            } catch(e) {}
        }
    });

    // Buttons
    const buttons = document.querySelectorAll('button, input[type="submit"], input[type="button"]');
    let btnCount = 0;
    buttons.forEach(btn => {
        if (btnCount < 10) {
            const text = (btn.textContent || btn.innerText || btn.value || '').trim();
            if (text) {
                data.button_labels.push(text);
                btnCount++;
            }
        }
    });

    // DO NOT Read input.value in accordance with privacy rules.
    return data;
}

chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
    if (request.action === "scanDOM") {
        sendResponse(scanDOM());
    }
});


// Trigger scan on load
chrome.runtime.sendMessage({ action: 'scanDOMResult', data: scanDOM() });
