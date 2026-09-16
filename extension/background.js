let scanningTabs = new Set();

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
                
                const responseData = await res.json();
                
                if (responseData.level === "dangerous") {
                    const warningsUrl = chrome.runtime.getURL("warning.html") + 
                        "?url=" + encodeURIComponent(tabUrl) +
                        "&score=" + responseData.risk_score +
                        "&reasons=" + encodeURIComponent(JSON.stringify(responseData.reasons));
                    chrome.tabs.update(tabId, { url: warningsUrl });
                }
            } catch (err) {
                console.error("Scan failed config", err);
            }
        });
    }
});
