/**
 * Dashboard View - Network Overview and Approval Queue
 * Phase 2 implementation
 */

// ====================
// State Management
// ====================

let dashboardState = {
    approvalQueue: [],
    networkStatus: null,
    pluginSummary: null,
    recentActivity: [],
    selectedApprovals: new Set(),
    pollingInterval: null,
    lastRefresh: null
};

// ====================
// API Functions
// ====================

/**
 * Fetch approval queue (pending plugin updates + config deployments)
 */
async function fetchApprovalQueue() {
    try {
        const response = await fetch('/api/dashboard/approval-queue');
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        const data = await response.json();
        dashboardState.approvalQueue = data.items;
        dashboardState.lastRefresh = new Date();
        return data;
    } catch (error) {
        console.error('Failed to fetch approval queue:', error);
        showError('Failed to load approval queue');
        return { items: [], count: 0 };
    }
}

/**
 * Fetch network status (online/offline instances, variance count)
 */
async function fetchNetworkStatus() {
    try {
        const response = await fetch('/api/dashboard/network-status');
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        const data = await response.json();
        dashboardState.networkStatus = data;
        return data;
    } catch (error) {
        console.error('Failed to fetch network status:', error);
        showError('Failed to load network status');
        return null;
    }
}

/**
 * Fetch plugin summary (total, needs update, up-to-date)
 */
async function fetchPluginSummary() {
    try {
        const response = await fetch('/api/dashboard/plugin-summary');
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        const data = await response.json();
        dashboardState.pluginSummary = data;
        return data;
    } catch (error) {
        console.error('Failed to fetch plugin summary:', error);
        showError('Failed to load plugin summary');
        return null;
    }
}

/**
 * Fetch recent activity log
 */
async function fetchRecentActivity(limit = 10) {
    try {
        const response = await fetch(`/api/dashboard/recent-activity?limit=${limit}`);
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        const data = await response.json();
        dashboardState.recentActivity = data;
        return data;
    } catch (error) {
        console.error('Failed to fetch recent activity:', error);
        showError('Failed to load recent activity');
        return [];
    }
}

/**
 * Approve selected items (plugin updates or deployments)
 */
async function approveSelected() {
    const selected = Array.from(dashboardState.selectedApprovals);
    if (selected.length === 0) {
        showWarning('No items selected');
        return;
    }

    try {
        // Group by type
        const pluginUpdates = selected.filter(id => id.startsWith('plugin-'));
        const deployments = selected.filter(id => id.startsWith('deploy-'));

        // Approve plugin updates
        if (pluginUpdates.length > 0) {
            const pluginIds = pluginUpdates.map(id => parseInt(id.replace('plugin-', '')));
            const response = await fetch('/api/plugin-updates/approve-batch', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ update_ids: pluginIds })
            });
            if (!response.ok) throw new Error('Failed to approve plugin updates');
        }

        // Approve deployments
        if (deployments.length > 0) {
            const deploymentIds = deployments.map(id => parseInt(id.replace('deploy-', '')));
            const response = await fetch('/api/deployments/approve-batch', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ deployment_ids: deploymentIds })
            });
            if (!response.ok) throw new Error('Failed to approve deployments');
        }

        showSuccess(`Approved ${selected.length} item(s)`);
        dashboardState.selectedApprovals.clear();
        await refreshDashboard();
    } catch (error) {
        console.error('Failed to approve items:', error);
        showError('Failed to approve selected items');
    }
}

/**
 * Reject selected items
 */
async function rejectSelected() {
    const selected = Array.from(dashboardState.selectedApprovals);
    if (selected.length === 0) {
        showWarning('No items selected');
        return;
    }

    try {
        const pluginUpdates = selected.filter(id => id.startsWith('plugin-'));
        const deployments = selected.filter(id => id.startsWith('deploy-'));

        if (pluginUpdates.length > 0) {
            const pluginIds = pluginUpdates.map(id => parseInt(id.replace('plugin-', '')));
            const response = await fetch('/api/plugin-updates/reject-batch', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ update_ids: pluginIds })
            });
            if (!response.ok) throw new Error('Failed to reject plugin updates');
        }

        if (deployments.length > 0) {
            const deploymentIds = deployments.map(id => parseInt(id.replace('deploy-', '')));
            const response = await fetch('/api/deployments/reject-batch', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ deployment_ids: deploymentIds })
            });
            if (!response.ok) throw new Error('Failed to reject deployments');
        }

        showSuccess(`Rejected ${selected.length} item(s)`);
        dashboardState.selectedApprovals.clear();
        await refreshDashboard();
    } catch (error) {
        console.error('Failed to reject items:', error);
        showError('Failed to reject selected items');
    }
}

// ====================
// Rendering Functions
// ====================

/**
 * Render approval queue table
 */
function renderApprovalQueue() {
    const container = document.getElementById('approval-queue-items');
    if (!container) return;

    if (dashboardState.approvalQueue.length === 0) {
        container.innerHTML = '<p class="no-data">No pending approvals</p>';
        return;
    }

    const html = `
        <table class="approval-queue-table">
            <thead>
                <tr>
                    <th><input type="checkbox" id="select-all-approvals"></th>
                    <th>Type</th>
                    <th>Item</th>
                    <th>Instances</th>
                    <th>Details</th>
                    <th>Timestamp</th>
                </tr>
            </thead>
            <tbody>
                ${dashboardState.approvalQueue.map(item => `
                    <tr class="approval-item" data-id="${item.id}">
                        <td><input type="checkbox" class="approval-checkbox" data-id="${item.id}"></td>
                        <td><span class="approval-type ${item.approval_type}">${item.approval_type}</span></td>
                        <td>${escapeHtml(item.item_name)}</td>
                        <td>${item.instance_count}</td>
                        <td class="approval-details">${escapeHtml(item.details)}</td>
                        <td>${formatTimestamp(item.timestamp)}</td>
                    </tr>
                `).join('')}
            </tbody>
        </table>
    `;

    container.innerHTML = html;
    attachApprovalCheckboxListeners();
}

/**
 * Render network status cards
 */
function renderNetworkStatus() {
    const container = document.getElementById('network-status-cards');
    if (!container || !dashboardState.networkStatus) return;

    const { online, offline, total, variance_count, servers } = dashboardState.networkStatus;

    const html = `
        <div class="status-card">
            <div class="card-icon online-icon">🟢</div>
            <div class="card-content">
                <div class="card-value">${online}</div>
                <div class="card-label">Online</div>
            </div>
        </div>
        <div class="status-card">
            <div class="card-icon offline-icon">🔴</div>
            <div class="card-content">
                <div class="card-value">${offline}</div>
                <div class="card-label">Offline</div>
            </div>
        </div>
        <div class="status-card">
            <div class="card-icon total-icon">📊</div>
            <div class="card-content">
                <div class="card-value">${total}</div>
                <div class="card-label">Total Instances</div>
            </div>
        </div>
        <div class="status-card ${variance_count > 0 ? 'warning' : ''}">
            <div class="card-icon variance-icon">⚠️</div>
            <div class="card-content">
                <div class="card-value">${variance_count}</div>
                <div class="card-label">Unintentional Variances</div>
            </div>
        </div>
    `;

    container.innerHTML = html;

    // Render per-server breakdown
    renderServerBreakdown(servers);
}

/**
 * Render per-server instance breakdown
 */
function renderServerBreakdown(servers) {
    const container = document.getElementById('server-breakdown');
    if (!container) return;

    const html = `
        <table class="server-breakdown-table">
            <thead>
                <tr>
                    <th>Server</th>
                    <th>Online</th>
                    <th>Offline</th>
                    <th>Total</th>
                </tr>
            </thead>
            <tbody>
                ${servers.map(server => `
                    <tr>
                        <td><strong>${escapeHtml(server.server_name)}</strong></td>
                        <td><span class="status-badge online">${server.online}</span></td>
                        <td><span class="status-badge offline">${server.offline}</span></td>
                        <td>${server.total}</td>
                    </tr>
                `).join('')}
            </tbody>
        </table>
    `;

    container.innerHTML = html;
}

/**
 * Render plugin summary
 */
function renderPluginSummary() {
    const container = document.getElementById('plugin-summary-cards');
    if (!container || !dashboardState.pluginSummary) return;

    const { total_plugins, needs_update, up_to_date } = dashboardState.pluginSummary;

    const html = `
        <div class="plugin-stat-card">
            <div class="stat-value">${total_plugins}</div>
            <div class="stat-label">Total Plugins</div>
        </div>
        <div class="plugin-stat-card ${needs_update > 0 ? 'warning' : ''}">
            <div class="stat-value">${needs_update}</div>
            <div class="stat-label">Updates Available</div>
        </div>
        <div class="plugin-stat-card success">
            <div class="stat-value">${up_to_date}</div>
            <div class="stat-label">Up to Date</div>
        </div>
    `;

    container.innerHTML = html;
}

/**
 * Render recent activity log
 */
function renderRecentActivity() {
    const container = document.getElementById('recent-activity-list');
    if (!container) return;

    if (dashboardState.recentActivity.length === 0) {
        container.innerHTML = '<p class="no-data">No recent activity</p>';
        return;
    }

    const html = `
        <ul class="activity-list">
            ${dashboardState.recentActivity.map(entry => `
                <li class="activity-entry">
                    <div class="activity-timestamp">${formatTimestamp(entry.timestamp)}</div>
                    <div class="activity-description">${escapeHtml(entry.description)}</div>
                    <div class="activity-user">${escapeHtml(entry.user || 'System')}</div>
                </li>
            `).join('')}
        </ul>
    `;

    container.innerHTML = html;
}

/**
 * Render last refresh timestamp
 */
function renderLastRefresh() {
    const container = document.getElementById('last-refresh-time');
    if (!container) return;

    if (dashboardState.lastRefresh) {
        container.textContent = `Last updated: ${formatTimestamp(dashboardState.lastRefresh)}`;
    }
}

// ====================
// Event Handlers
// ====================

/**
 * Attach checkbox listeners for approval queue
 */
function attachApprovalCheckboxListeners() {
    // Select all checkbox
    const selectAll = document.getElementById('select-all-approvals');
    if (selectAll) {
        selectAll.addEventListener('change', (e) => {
            const checkboxes = document.querySelectorAll('.approval-checkbox');
            checkboxes.forEach(cb => {
                cb.checked = e.target.checked;
                if (e.target.checked) {
                    dashboardState.selectedApprovals.add(cb.dataset.id);
                } else {
                    dashboardState.selectedApprovals.delete(cb.dataset.id);
                }
            });
            updateBatchActionButtons();
        });
    }

    // Individual checkboxes
    const checkboxes = document.querySelectorAll('.approval-checkbox');
    checkboxes.forEach(cb => {
        cb.addEventListener('change', (e) => {
            if (e.target.checked) {
                dashboardState.selectedApprovals.add(e.target.dataset.id);
            } else {
                dashboardState.selectedApprovals.delete(e.target.dataset.id);
            }
            updateBatchActionButtons();
        });
    });
}

/**
 * Update batch action button states
 */
function updateBatchActionButtons() {
    const approveBtn = document.getElementById('approve-selected-btn');
    const rejectBtn = document.getElementById('reject-selected-btn');
    const count = dashboardState.selectedApprovals.size;

    if (approveBtn) approveBtn.disabled = count === 0;
    if (rejectBtn) rejectBtn.disabled = count === 0;

    // Update button text with count
    if (approveBtn) approveBtn.textContent = count > 0 ? `Approve (${count})` : 'Approve';
    if (rejectBtn) rejectBtn.textContent = count > 0 ? `Reject (${count})` : 'Reject';
}

// ====================
// Initialization and Polling
// ====================

/**
 * Refresh all dashboard data
 */
async function refreshDashboard() {
    await Promise.all([
        fetchApprovalQueue(),
        fetchNetworkStatus(),
        fetchPluginSummary(),
        fetchRecentActivity()
    ]);

    renderApprovalQueue();
    renderNetworkStatus();
    renderPluginSummary();
    renderRecentActivity();
    renderLastRefresh();
}

/**
 * Start auto-refresh polling (30 seconds)
 */
function startDashboardPolling() {
    if (dashboardState.pollingInterval) {
        clearInterval(dashboardState.pollingInterval);
    }
    dashboardState.pollingInterval = setInterval(refreshDashboard, 30000);
}

/**
 * Stop auto-refresh polling
 */
function stopDashboardPolling() {
    if (dashboardState.pollingInterval) {
        clearInterval(dashboardState.pollingInterval);
        dashboardState.pollingInterval = null;
    }
}

/**
 * Initialize dashboard view
 */
async function initDashboard() {
    console.log('Initializing dashboard view');

    // Attach button handlers
    const approveBtn = document.getElementById('approve-selected-btn');
    const rejectBtn = document.getElementById('reject-selected-btn');
    const refreshBtn = document.getElementById('dashboard-refresh-btn');

    if (approveBtn) approveBtn.addEventListener('click', approveSelected);
    if (rejectBtn) rejectBtn.addEventListener('click', rejectSelected);
    if (refreshBtn) refreshBtn.addEventListener('click', refreshDashboard);

    // Initial load
    await refreshDashboard();

    // Start polling
    startDashboardPolling();
}

// ====================
// Utility Functions
// ====================

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function formatTimestamp(timestamp) {
    const date = new Date(timestamp);
    const now = new Date();
    const diffMs = now - date;
    const diffMins = Math.floor(diffMs / 60000);

    if (diffMins < 1) return 'Just now';
    if (diffMins < 60) return `${diffMins}m ago`;
    if (diffMins < 1440) return `${Math.floor(diffMins / 60)}h ago`;
    return date.toLocaleDateString() + ' ' + date.toLocaleTimeString();
}

function showError(message) {
    console.error(message);
    // TODO: Implement toast notification system
}

function showWarning(message) {
    console.warn(message);
    // TODO: Implement toast notification system
}

function showSuccess(message) {
    console.log(message);
    // TODO: Implement toast notification system
}

// Export for use by app.js
window.dashboardModule = {
    init: initDashboard,
    refresh: refreshDashboard,
    stopPolling: stopDashboardPolling
};
