document.addEventListener("DOMContentLoaded", () => {
    const btnVerify = document.getElementById("btn-verify");
    const resultDiv = document.getElementById("verify-result");
    
    if (btnVerify) {
        btnVerify.addEventListener("click", async () => {
            resultDiv.innerHTML = "Verifying...";
            try {
                const res = await apiRequest('/api/audit/verify/');
                if (res.is_valid) {
                    resultDiv.innerHTML = `<div class="success-msg">Chain is valid! Block count: ${res.block_count}</div>`;
                } else {
                    resultDiv.innerHTML = `<div class="error-msg">Chain is invalid! Issue at block ${res.invalid_block}</div>`;
                }
            } catch (err) {
                resultDiv.innerHTML = `<div class="error-msg">Error: ${err.message}</div>`;
            }
        });
    }

    async function loadLogs() {
        const tbody = document.getElementById("audit-tbody");
        if (!tbody) return;
        try {
            const data = await apiRequest('/api/audit/logs/');
            const results = data.results || data;
            tbody.innerHTML = '';
            
            results.forEach(log => {
                let badgeClass = 'badge-blue';
                if(log.event_type.includes('login')) badgeClass = 'badge-green';
                if(log.event_type.includes('grant')) badgeClass = 'badge-purple';
                if(log.event_type.includes('policy')) badgeClass = 'badge-yellow';

                tbody.innerHTML += `
                    <tr>
                        <td>${log.id || log.block_number || '-'}</td>
                        <td>${new Date(log.timestamp).toLocaleString()}</td>
                        <td><span class="badge ${badgeClass}">${log.event_type}</span></td>
                        <td>${log.details || 'N/A'}</td>
                        <td title="${log.hash || ''}">${(log.hash || '').substring(0, 16)}...</td>
                    </tr>
                `;
            });
        } catch (err) {
            tbody.innerHTML = `<tr><td colspan="5" class="error-msg">Error: ${err.message}</td></tr>`;
        }
    }
    
    loadLogs();
});
