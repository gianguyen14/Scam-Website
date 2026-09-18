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

        const res = await fetch("http://127.0.0.1:8000/api/v1/scan", {
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
    } catch (err) {
        statusMsg.textContent = `Fail-safe: Backend unavailable or error. (${err.message})`;
        statusMsg.className = "error";
    }
});
