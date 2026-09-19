let scanningTabs = new Set();
const CACHE_TTL = 3600 * 1000; // 1 hour

async function getCachedResult(cacheKey) {
    return new Promise((resolve) => {
        chrome.storage.local.get(['scanCache'], (data) => {
            const cache = data.scanCache || {};
            const cachedItem = cache[cacheKey];
            if (cachedItem && Date.now() - cachedItem.timestamp < CACHE_TTL) {
                resolve(cachedItem.result);
            } else {
                resolve(null);
            }
        });
    });
}

function setCacheResult(cacheKey, result) {
    chrome.storage.local.get(['scanCache'], (data) => {
        const cache = data.scanCache || {};
        cache[cacheKey] = {
            result: result,
            timestamp: Date.now()
        };
        // very simple cleanup if too big
        if (Object.keys(cache).length > 100) {
            const oldest = Object.keys(cache).sort((a,b) => cache[a].timestamp - cache[b].timestamp)[0];
            delete cache[oldest];
        }
        chrome.storage.local.set({ scanCache: cache });
    });
}

chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
    
    if (request.action === "behaviorAlert") {
        console.log("Phát hiện hành vi rủi ro:", request.alert);
        chrome.tabs.update(sender.tab.id, { 
            url: chrome.runtime.getURL("warning.html") + 
                 "?url=" + encodeURIComponent(sender.tab.url) + 
                 "&score=99&reasons=" + encodeURIComponent(JSON.stringify(["[Behavioral] Paste mật khẩu hoặc OTP vào website không xác định."]))
        });
        return true;
    }

    if (request.action === "scanDOMResult") {
        (async () => {
                        const tabId = sender.tab.id;
            const tabUrl = sender.tab.url;
            
            // Fast fail internal
            if (!tabUrl.startsWith('http')) return;
            
            try {
                const data = await chrome.storage.local.get({ allowedUrls: [] });
                                
                try {
                    const urlObj = new URL(tabUrl);
                    if (data.allowedUrls.includes(urlObj.hostname)) {
                        return; // user whitelisted
                    }
                } catch(e) {}
                
                const cacheKey = tabUrl + '|' + JSON.stringify(request.data || {});
                let responseData = await getCachedResult(cacheKey);
                                
                if (!responseData) {
                                        try {
                        const res = await fetch("https://scam-website-u49m.vercel.app/api/v1/scan", {
                            method: "POST",
                            headers: { "Content-Type": "application/json" },
                            body: JSON.stringify({
                                schema_version: 1,
                                url: tabUrl,
                                page: request.data
                            })
                        });
                        
                        responseData = await res.json();
                                                setCacheResult(cacheKey, responseData);
                    } catch (err) {
                        console.error("Scan failed - degraded mode", err.message);
                        return;
                    }
                }
                
                                
                // Nếu trang có rủi ro tiềm ẩn (nhưng chưa đủ điểm đấm thành dangerous),
                // hoặc trang nhạy cảm chứa password, Kích hoạt Deep Vision AI
                if (responseData && responseData.risk_score >= 20 && responseData.risk_score < 70) {
                    try {
                        let dataUrl = await chrome.tabs.captureVisibleTab(sender.tab.windowId, {format: "jpeg", quality: 20});
                        let visionRes = await fetch("https://scam-website-u49m.vercel.app/api/v1/scan/vision", {
                            method: "POST",
                            headers: { "Content-Type": "application/json" },
                            body: JSON.stringify({ url: tabUrl, screenshot: dataUrl })
                        });
                        let vData = await visionRes.json();
                        if (vData.risk_score >= 70) {
                            responseData.level = "dangerous";
                            responseData.risk_score = 95;
                            responseData.reasons.push(vData.reason);
                        }
                    } catch(e) {
                         // Lỗi capture (VD tab không active hoặc lỗi net), cho qua mềm
                    }
                }
                
                if (responseData && responseData.level === "dangerous") {

                    const warningsUrl = chrome.runtime.getURL("warning.html") + 
                        "?url=" + encodeURIComponent(tabUrl) +
                        "&score=" + responseData.risk_score +
                        "&reasons=" + encodeURIComponent(JSON.stringify(responseData.reasons));
                                        chrome.tabs.update(tabId, { url: warningsUrl });
                }
            } catch(err) {
                console.error('MAIN WORKER ERR:', err);
            }
        })();
        return true; // prevent channel close
    }
});
