/**
 * Stub modules for remaining views
 * These provide basic init/refresh/cleanup functions for views that aren't fully implemented yet
 */

// Variance Report Module
window.varianceReportModule = {
    init: async function(params) {
        console.log('Variance Report view loaded (stub)');
        document.getElementById('variance-report-view').innerHTML = `
            <div class="view-header">
                <h2>Variance Report</h2>
                <p>Configuration variances across all instances</p>
            </div>
            <div class="placeholder-content">
                <p>📊 This view will show all configuration variances detected by the agent.</p>
                <ul>
                    <li>List all variances grouped by plugin</li>
                    <li>Mark variances as intentional or to-be-fixed</li>
                    <li>Quick apply defaults or sync configs</li>
                    <li>Filter by server, instance, or meta-tag</li>
                </ul>
                <p><em>API endpoint ready:</em> <code>GET /api/plugin-configurator/plugins/{id}/variances</code></p>
            </div>
        `;
    },
    refresh: async function() {
        console.log('Variance Report refresh (stub)');
    },
    cleanup: async function() {
        console.log('Variance Report cleanup (stub)');
    }
};

// Settings Module
window.settingsModule = {
    init: async function(params) {
        console.log('Settings view loaded (stub)');
        document.getElementById('settings-view').innerHTML = `
            <h2>Settings</h2>
            <p>This view will show system settings and configuration options.</p>
            <p><em>To be implemented in Phase 3</em></p>
        `;
    },
    refresh: async function() {
        console.log('Settings refresh (stub)');
    },
    cleanup: async function() {
        console.log('Settings cleanup (stub)');
    }
};

console.log('Stub view modules loaded');
