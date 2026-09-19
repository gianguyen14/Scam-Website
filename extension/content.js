

// --- MÔ-ĐUN PHÂN TÍCH HÀNH VI (Behavioral Analysis) ---
let userBehavior = {
    rapidScroll: false,
    pasteInSensitiveField: false,
    abnormalInteractions: 0
};

// Theo dõi hành vi paste vào input ẩn/nhạy cảm
document.addEventListener('paste', (e) => {
    if (e.target.tagName === 'INPUT') {
        const type = e.target.type.toLowerCase();
        if (type === 'password' || type === 'tel' || e.target.name.toLowerCase().includes('otp')) {
            userBehavior.pasteInSensitiveField = true;
            console.log("[Behavioral] Phát hiện paste dữ liệu nhạy cảm");
            // Gửi cảnh báo phụ lên background
            chrome.runtime.sendMessage({ 
                action: 'behaviorAlert', 
                alert: 'paste_sensitive',
                url: window.location.href
            });
        }
    }
});

let scrollCount = 0;
document.addEventListener('scroll', () => {
    scrollCount++;
    if (scrollCount > 50) { 
        userBehavior.rapidScroll = true; 
    }
    // Giảm dần count để chỉ bắt cuộn thực sự nhanh
    setTimeout(() => { if(scrollCount > 0) scrollCount--; }, 100);
}, {passive: true});


// --- MÔ-ĐUN ADVANCED VISION (DOM Structural Hashing) ---
// Phishing site thường copy nguyên cấu trúc thẻ HTML của site gốc.
// Hàm này trích xuất cấu trúc DOM (chỉ lấy TÊN THẺ, bỏ qua nội dung/chữ)
function getDOMTreeHash(node, maxDepth, currentDepth=0) {
    if (currentDepth > maxDepth || !node) return "";
    let hash = node.nodeName + "|";
    for (let i = 0; i < node.childNodes.length; i++) {
        let child = node.childNodes[i];
        if (child.nodeType === 1) { // ELEMENT_NODE
            // Bỏ qua các thẻ ít ý nghĩa cấu trúc giao diện
            if (!['SCRIPT', 'STYLE', 'META', 'LINK', 'NOSCRIPT'].includes(child.nodeName)) {
                hash += getDOMTreeHash(child, maxDepth, currentDepth + 1);
            }
        }
    }
    return hash;
}

// Băm chuỗi bằng thuật toán FNV-1a (nhẹ, nhanh trên trình duyệt)
function fnv1aHash(str) {
    let hash = 2166136261;
    for (let i = 0; i < str.length; i++) {
        hash ^= str.charCodeAt(i);
        hash += (hash << 1) + (hash << 4) + (hash << 7) + (hash << 8) + (hash << 24);
    }
    return hash >>> 0;
}

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

    
    // Thêm đặc trưng từ Advanced Vision & Behavioral
    data.dom_hash = fnv1aHash(getDOMTreeHash(document.body, 10)).toString(16);
    data.behavior = userBehavior;

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
