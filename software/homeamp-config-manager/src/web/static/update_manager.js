/**
 * Update Manager JavaScript
 * Handles plugin update checking, approval, and deployment
 */

// Constants
const UPDATE_MANAGER_POLL_INTERVAL = 60000; // 60 seconds
let updatePollingTimer = null;

// ====================
// Initialization
// ====================

function loadUpdateManager() {
    console.log('Loading Update Manager...');
    
    // Set up event listeners
    document.getElementById('check-updates-btn')?.addEventListener('click', triggerManualUpdateCheck);
    document.getElementById('select-all-updates')?.addEventListener('change', toggleSelectAllUpdates);
    document.getElementById('approve-deploy-btn')?.addEventListener('click', approveSelectedUpdates);
    document.getElementById('update-selected-btn')?.addEventListener('click', updateSelectedOnly);
    document.getElementById('reject-all-btn')?.addEventListener('click', rejectSelectedUpdates);
    
    // Load initial data
    fetchAvailableUpdates();
    
    // Start polling for updates
    startUpdateManagerPolling();
}

// ====================
// API Functions
// ====================

async function fetchAvailableUpdates() {
    try {
        const response = await fetch('/api/updates/available');
        if (!response.ok) throw new Error('Failed to fetch updates');
        
        const updates = await response.json();
        renderUpdatesTable(updates);
        
        return updates;
    } catch (error) {
        console.error('Error fetching updates:', error);
        return [];
    }
}

async function triggerManualUpdateCheck() {
    try {
        const btn = document.getElementById('check-updates-btn');
        btn.disabled = true;
        btn.textContent = 'Checking...';
        
        const response = await fetch('/api/updates/check', { method: 'POST' });
        if (!response.ok) throw new Error('Failed to check updates');
        
        const result = await response.json();
        
        // Update last check time
        const lastCheckEl = document.getElementById('last-check-time');
        lastCheckEl.textContent = `Last checked: ${new Date().toLocaleString()}`;
        
        // Refresh updates list
        await fetchAvailableUpdates();
        
        alert(`Checked ${result.checked} plugins, found ${result.updates_found} updates`);
        
    } catch (error) {
        console.error('Error checking updates:', error);
        alert('Failed to check for updates');
    } finally {
        const btn = document.getElementById('check-updates-btn');
        btn.disabled = false;
        btn.textContent = 'Check for Updates';
    }
}

async function approveUpdatesAPI(pluginIds, scope, targetInstances = null, targetServer = null, targetTag = null) {
    try {
        const response = await fetch('/api/updates/approve', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                plugin_ids: pluginIds,
                deployment_scope: scope,
                target_instances: targetInstances,
                target_server: targetServer,
                target_tag: targetTag
            })
        });
        
        if (!response.ok) throw new Error('Failed to approve updates');
        
        return await response.json();
    } catch (error) {
        console.error('Error approving updates:', error);
        throw error;
    }
}

async function rejectUpdatesAPI(pluginIds, skipVersion = false) {
    try {
        const response = await fetch('/api/updates/reject', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                plugin_ids: pluginIds,
                skip_version: skipVersion
            })
        });
        
        if (!response.ok) throw new Error('Failed to reject updates');
        
        return await response.json();
    } catch (error) {
        console.error('Error rejecting updates:', error);
        throw error;
    }
}

async function pollUpdateStatus(pluginName) {
    try {
        const response = await fetch(`/api/updates/status/${encodeURIComponent(pluginName)}`);
        if (!response.ok) throw new Error('Failed to fetch update status');
        
        return await response.json();
    } catch (error) {
        console.error('Error polling update status:', error);
        return null;
    }
}

// ====================
// UI Rendering
// ====================

function renderUpdatesTable(updates) {
    const tbody = document.getElementById('updates-table-body');
    
    if (!updates || updates.length === 0) {
        tbody.innerHTML = '<tr><td colspan="8" class="no-data">No updates available</td></tr>';
        return;
    }
    
    tbody.innerHTML = updates.map(update => `
        <tr class="plugin-update-row" data-plugin-id="${update.plugin_id}">
            <td><input type="checkbox" class="plugin-update-checkbox" value="${update.plugin_id}" /></td>
            <td><strong>${escapeHtml(update.plugin_name)}</strong></td>
            <td>${escapeHtml(update.current_version)}</td>
            <td><span class="version-badge">${escapeHtml(update.latest_version)}</span></td>
            <td>${escapeHtml(update.source)}</td>
            <td>${update.affected_instances.length} instances</td>
            <td>${update.release_date ? new Date(update.release_date).toLocaleDateString() : 'Unknown'}</td>
            <td>
                ${update.changelog_url ? `<a href="${escapeHtml(update.changelog_url)}" target="_blank" class="btn-link">Changelog</a>` : ''}
            </td>
        </tr>
    `).join('');
}

// ====================
// Event Handlers
// ====================

function toggleSelectAllUpdates(event) {
    const checked = event.target.checked;
    const checkboxes = document.querySelectorAll('.plugin-update-checkbox');
    checkboxes.forEach(cb => cb.checked = checked);
}

function getSelectedPluginIds() {
    const checkboxes = document.querySelectorAll('.plugin-update-checkbox:checked');
    return Array.from(checkboxes).map(cb => parseInt(cb.value));
}

function getDeploymentScope() {
    const radioButtons = document.querySelectorAll('input[name="deployment-scope"]');
    for (const radio of radioButtons) {
        if (radio.checked) {
            return radio.value;
        }
    }
    return 'all'; // default
}

async function approveSelectedUpdates() {
    const pluginIds = getSelectedPluginIds();
    
    if (pluginIds.length === 0) {
        alert('Please select at least one plugin to approve');
        return;
    }
    
    const scope = getDeploymentScope();
    
    const confirmMsg = `Approve updates for ${pluginIds.length} plugin(s) with scope: ${scope}?`;
    if (!confirm(confirmMsg)) return;
    
    try {
        const result = await approveUpdatesAPI(pluginIds, scope);
        alert(`Approved ${result.approved} update(s), queued ${result.queued_for_deployment.length} deployment(s)`);
        
        // Refresh updates list
        await fetchAvailableUpdates();
        
        // Clear selections
        document.getElementById('select-all-updates').checked = false;
        
    } catch (error) {
        alert('Failed to approve updates');
    }
}

async function updateSelectedOnly() {
    const pluginIds = getSelectedPluginIds();
    
    if (pluginIds.length === 0) {
        alert('Please select at least one plugin to update');
        return;
    }
    
    const scope = getDeploymentScope();
    
    // Same as approve, but could have different logic later
    await approveSelectedUpdates();
}

async function rejectSelectedUpdates() {
    const pluginIds = getSelectedPluginIds();
    
    if (pluginIds.length === 0) {
        alert('Please select at least one plugin to reject');
        return;
    }
    
    const skipVersion = confirm('Skip this version in future checks?');
    
    try {
        const result = await rejectUpdatesAPI(pluginIds, skipVersion);
        alert(`Rejected ${result.rejected} update(s)`);
        
        // Refresh updates list
        await fetchAvailableUpdates();
        
        // Clear selections
        document.getElementById('select-all-updates').checked = false;
        
    } catch (error) {
        alert('Failed to reject updates');
    }
}

// ====================
// Progress Monitoring
// ====================

function showUpdateProgress(show = true) {
    const statusSection = document.getElementById('update-status-section');
    statusSection.style.display = show ? 'block' : 'none';
}

function updateProgressBar(percentage, message) {
    const progressBar = document.getElementById('update-progress-bar');
    const statusText = document.getElementById('update-status-text');
    
    progressBar.style.width = `${percentage}%`;
    statusText.textContent = message;
}

// ====================
// Polling
// ====================

function startUpdateManagerPolling() {
    if (updatePollingTimer) {
        clearInterval(updatePollingTimer);
    }
    
    updatePollingTimer = setInterval(() => {
        // Only refresh if view is active
        const view = document.getElementById('update-manager-view');
        if (view && view.style.display !== 'none') {
            fetchAvailableUpdates();
        }
    }, UPDATE_MANAGER_POLL_INTERVAL);
}

function stopUpdateManagerPolling() {
    if (updatePollingTimer) {
        clearInterval(updatePollingTimer);
        updatePollingTimer = null;
    }
}

// ====================
// Utility Functions
// ====================

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Initialize when view is loaded
if (document.getElementById('update-manager-view')) {
    // Wait for DOM to be ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', loadUpdateManager);
    } else {
        loadUpdateManager();
    }
}

// ====================
// Module Export for app.js
// ====================

window.updateManagerModule = {
    init: async function(params) {
        console.log('Update Manager module initialized');
        loadUpdateManager();
    },
    refresh: async function() {
        console.log('Update Manager refresh');
        await fetchAvailableUpdates();
    },
    cleanup: async function() {
        console.log('Update Manager cleanup');
        stopUpdateManagerPolling();
    }
};

