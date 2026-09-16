let scanningTabs = new Set();
const CACHE_TTL = 3600 * 1000; // 1 hour

async function getCachedResult(url) {
    return new Promise((resolve) => {
        chrome.storage.local.get(['scanCache'], (data) => {
            const cache = data.scanCache || {};
            const cachedItem = cache[url];
            if (cachedItem && Date.now() - cachedItem.timestamp < CACHE_TTL) {
                resolve(cachedItem.result);
            } else {
                resolve(null);
            }
        });
    });
}

function setCacheResult(url, result) {
    chrome.storage.local.get(['scanCache'], (data) => {
        const cache = data.scanCache || {};
        cache[url] = {
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
    if (request.action === "scanDOMResult") {
        const tabId = sender.tab.id;
        const tabUrl = sender.tab.url;
        
        // Fast fail internal
        if (tabUrl.startsWith("chrome") || tabUrl.startsWith("edge")) return;
        
        chrome.storage.local.get({ allowedUrls: [] }, async (data) => {
            try {
                const urlObj = new URL(tabUrl);
                if (data.allowedUrls.includes(urlObj.hostname)) {
                    return; // user whitelisted
                }
            } catch(e) {}
            
            // Check cache
            let responseData = await getCachedResult(tabUrl);
            
            if (!responseData) {
                try {
                    const res = await fetch("http://127.0.0.1:8000/api/v1/scan", {
                        method: "POST",
                        headers: { "Content-Type": "application/json" },
                        body: JSON.stringify({
                            schema_version: 1,
                            url: tabUrl,
                            page: request.data
                        })
                    });
                    
                    responseData = await res.json();
                    setCacheResult(tabUrl, responseData);
                } catch (err) {
                    console.error("Scan failed - degraded mode", err);
                    return;
                }
            }
            
            if (responseData && responseData.level === "dangerous") {
                const warningsUrl = chrome.runtime.getURL("warning.html") + 
                    "?url=" + encodeURIComponent(tabUrl) +
                    "&score=" + responseData.risk_score +
                    "&reasons=" + encodeURIComponent(JSON.stringify(responseData.reasons));
                chrome.tabs.update(tabId, { url: warningsUrl });
            }
        });
    }
});
