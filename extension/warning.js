document.addEventListener("DOMContentLoaded", () => {
    const params = new URLSearchParams(window.location.search);
    const score = params.get('score');
    const reasons = params.get('reasons');
    const originalUrl = params.get('url');

    document.getElementById('risk-score').textContent = score || 'N/A';
    
    if (reasons) {
        try {
            const reasonsList = JSON.parse(reasons);
            const ul = document.getElementById('reasons-list');
            reasonsList.forEach(r => {
                const li = document.createElement('li');
                li.textContent = r;
                ul.appendChild(li);
            });
        } catch(e) {}
    }

    document.getElementById('btn-back').addEventListener('click', () => {
        window.history.length > 2 ? window.history.back() : window.close();
    });

    document.getElementById('btn-continue').addEventListener('click', () => {
        // Option 1: save to allowlist and redirect back
        chrome.storage.local.get({ allowedUrls: [] }, (data) => {
            const urlObj = new URL(originalUrl);
            data.allowedUrls.push(urlObj.hostname);
            chrome.storage.local.set({ allowedUrls: data.allowedUrls }, () => {
                window.location.href = originalUrl;
            });
        });
    });
});
