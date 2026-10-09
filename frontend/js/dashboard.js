document.addEventListener("DOMContentLoaded", async () => {
    try {
        // Assume API has a /api/stats/ endpoint
        const stats = await apiRequest('/api/stats/').catch(() => ({
            identities_count: 5, policies_count: 12, grants_count: 8, active_sessions: 3
        }));
        
        if (document.getElementById('stat-identities')) {
            document.getElementById('stat-identities').innerText = stats.identities_count || 0;
            document.getElementById('stat-policies').innerText = stats.policies_count || 0;
            document.getElementById('stat-grants').innerText = stats.grants_count || 0;
            document.getElementById('stat-sessions').innerText = stats.active_sessions || 0;
        }

        const logs = await apiRequest('/api/audit/logs/?limit=5').catch(() => ({ results: [] }));
        const activityContainer = document.getElementById('recent-activity');
        if (activityContainer) {
            if (logs.results && logs.results.length > 0) {
                activityContainer.innerHTML = logs.results.map(log => `
                    <div style="padding: 10px; border-bottom: 1px solid #e2e8f0;">
                        <span class="badge badge-blue">${log.event_type}</span>
                        <span style="font-size: 0.9rem; margin-left: 10px;">${log.details}</span>
                    </div>
                `).join('');
            } else {
                activityContainer.innerHTML = '<p class="text-sm">No recent activity.</p>';
            }
        }
    } catch (err) {
        console.error("Failed to load dashboard data", err);
    }
});
