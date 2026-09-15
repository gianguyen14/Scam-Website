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

        const res = await fetch("http://127.0.0.1:8000/api/v1/scan", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                schema_version: 1,
                url: tab.url,
                page: {}
            })
        });

        if (!res.ok) throw new Error(`Backend error ${res.status}`);

        const data = await res.json();
        
        let reasonsHtml = '';
        if (data.reasons && data.reasons.length > 0) {
            reasonsHtml = '<ul style="padding-left: 20px; font-size: 11px;">' + 
                          data.reasons.map(r => `<li>${r}</li>`).join('') + 
                          '</ul>';
        }

        statusMsg.innerHTML = `
            Score: <span class="${data.level}">${data.risk_score}/100</span><br>
            Status: <span class="${data.level}">${data.level.toUpperCase()}</span>
            ${reasonsHtml}
        `;
    } catch (err) {
        statusMsg.innerHTML = `<span class="error">Fail-safe: Backend unavailable or error. (${err.message})</span>`;
    }
});
