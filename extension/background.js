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
                                                setCacheResult(cacheKey, responseData);
                    } catch (err) {
                        console.error("Scan failed - degraded mode", err.message);
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
            } catch(err) {
                console.error('MAIN WORKER ERR:', err);
            }
        })();
        return true; // prevent channel close
    }
});
