document.addEventListener("DOMContentLoaded", async () => {
    const urlContainer = document.getElementById("url-container");
    const statusMsg = document.getElementById("status-msg");

    try {
        let [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
        if (!tab || !tab.url) {
            urlContainer.textContent = "No active URL context.";
            statusMsg.textContent = "Cannot scan this page.";
            return;
        }

        urlContainer.textContent = tab.url;

        // Skip internal/chrome URLs
        if (tab.url.startsWith("chrome://") || tab.url.startsWith("edge://")) {
            statusMsg.textContent = "Internal browser page.";
            return;
        }

        // Get DOM metrics from content script
        let pageDOM = {};
        try {
            pageDOM = await chrome.tabs.sendMessage(tab.id, {action: "scanDOM"});
        } catch(e) {
            console.log("Could not ping content script, maybe not injected yet or restricted page.", e);
        }

        const res = await fetch("https://www.gianguyen14.tech/api/v1/scan", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                schema_version: 1,
                url: tab.url,
                page: pageDOM
            })
        });

        if (!res.ok) throw new Error(`Backend error ${res.status}`);

        const data = await res.json();
        
        statusMsg.innerHTML = ""; // Clear
        const scoreLine = document.createElement("div");
        scoreLine.textContent = `Score: ${data.risk_score}/100`;
        scoreLine.className = data.level;
        
        const statusLine = document.createElement("div");
        statusLine.textContent = `Status: ${data.level.toUpperCase()}`;
        statusLine.className = data.level;
        
        statusMsg.appendChild(scoreLine);
        statusMsg.appendChild(statusLine);

        if (data.reasons && data.reasons.length > 0) {
            const ul = document.createElement("ul");
            ul.style.paddingLeft = "20px";
            ul.style.fontSize = "11px";
            data.reasons.forEach(r => {
                const li = document.createElement("li");
                li.textContent = r;
                ul.appendChild(li);
            });
            statusMsg.appendChild(ul);
        }

        // Tích hợp Local Dashboard
        chrome.storage.local.get({ scanHistory: [], totalScans: 0 }, (db) => {
            document.getElementById("total-scans").textContent = db.totalScans;
            const historyContainer = document.getElementById("history-container");
            historyContainer.innerHTML = '<div style="font-weight:bold; font-size:12px; margin-bottom:5px; color:#4b5563">Lịch sử quét gần đây</div>';
            
            db.scanHistory.slice(0, 10).forEach(item => {
                let div = document.createElement("div");
                div.className = "history-item";
                
                let domainSpan = document.createElement("span");
                domainSpan.textContent = item.domain.length > 25 ? item.domain.substring(0, 25) + '...' : item.domain;
                domainSpan.title = item.url;
                
                let scoreSpan = document.createElement("span");
                scoreSpan.className = item.level;
                scoreSpan.textContent = item.score + "/100";
                
                div.appendChild(domainSpan);
                div.appendChild(scoreSpan);
                historyContainer.appendChild(div);
            });
        });

    } catch (err) {
        statusMsg.textContent = `Fail-safe: Backend unavailable or error. (${err.message})`;
        statusMsg.className = "error";
    }
});
