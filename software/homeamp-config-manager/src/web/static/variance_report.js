/**
 * Variance Report JavaScript
 * Displays and manages configuration variances across instances
 */

// Constants
const VARIANCE_POLL_INTERVAL = 30000; // 30 seconds
let variancePollingTimer = null;
let allVariances = [];
let filteredVariances = [];

// ====================
// Initialization
// ====================

function loadVarianceReport() {
    console.log('Loading Variance Report...');
    
    // Set up event listeners
    document.getElementById('refresh-variances-btn')?.addEventListener('click', refreshVariances);
    document.getElementById('select-all-variances')?.addEventListener('change', toggleSelectAllVariances);
    document.getElementById('apply-defaults-btn')?.addEventListener('click', applyDefaultsToSelected);
    document.getElementById('mark-intentional-btn')?.addEventListener('click', markSelectedAsIntentional);
    document.getElementById('sync-configs-btn')?.addEventListener('click', syncSelectedConfigs);
    
    // Filter listeners
    document.getElementById('variance-filter-server')?.addEventListener('change', applyFilters);
    document.getElementById('variance-filter-plugin')?.addEventListener('change', applyFilters);
    document.getElementById('variance-filter-status')?.addEventListener('change', applyFilters);
    
    // Load initial data
    fetchAllVariances();
    
    // Start polling
    startVariancePolling();
}

// ====================
// API Functions
// ====================

async function fetchAllVariances() {
    try {
        const response = await fetch('/api/variances/all');
        if (!response.ok) throw new Error('Failed to fetch variances');
        
        allVariances = await response.json();
        filteredVariances = [...allVariances];
        
        populateFilters();
        renderVariancesTable(filteredVariances);
        updateSummaryCards(filteredVariances);
        
        return allVariances;
    } catch (error) {
        console.error('Error fetching variances:', error);
        document.getElementById('variances-table-body').innerHTML = 
            '<tr><td colspan="8" class="error">Failed to load variances</td></tr>';
        return [];
    }
}

async function applyDefaultValue(pluginName, instanceId, configKey) {
    try {
        const response = await fetch(`/api/variances/${encodeURIComponent(pluginName)}/${instanceId}`, {
            method: 'DELETE',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ config_key: configKey })
        });
        
        if (!response.ok) throw new Error('Failed to apply default');
        
        return await response.json();
    } catch (error) {
        console.error('Error applying default:', error);
        throw error;
    }
}

async function markVarianceIntentional(varianceId, isIntentional = true) {
    try {
        const response = await fetch('/api/plugin-configurator/variances/mark', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ 
                variance_id: varianceId,
                is_intentional: isIntentional 
            })
        });
        
        if (!response.ok) throw new Error('Failed to mark variance');
        
        return await response.json();
    } catch (error) {
        console.error('Error marking variance:', error);
        throw error;
    }
}

// ====================
// UI Rendering
// ====================

function renderVariancesTable(variances) {
    const tbody = document.getElementById('variances-table-body');
    
    if (!variances || variances.length === 0) {
        tbody.innerHTML = '<tr><td colspan="8" class="no-data">No variances found</td></tr>';
        return;
    }
    
    tbody.innerHTML = variances.map(v => `
        <tr class="variance-row" data-variance-id="${v.id || v.variance_id}">
            <td><input type="checkbox" class="variance-checkbox" value="${v.id || v.variance_id}" /></td>
            <td><strong>${escapeHtml(v.plugin_name)}</strong></td>
            <td>${escapeHtml(v.instance_name || v.instance_id)}</td>
            <td><code>${escapeHtml(v.config_key)}</code></td>
            <td class="value-cell">${formatValue(v.baseline_value)}</td>
            <td class="value-cell">${formatValue(v.actual_value)}</td>
            <td>
                <span class="status-badge ${v.is_intentional ? 'intentional' : 'unintentional'}">
                    ${v.is_intentional ? 'Intentional' : 'Unintentional'}
                </span>
            </td>
            <td class="action-buttons">
                <button class="btn-small" onclick="applyDefaultToVariance('${escapeHtml(v.plugin_name)}', '${v.instance_id}', '${escapeHtml(v.config_key)}')">
                    Apply Default
                </button>
            </td>
        </tr>
    `).join('');
}

function updateSummaryCards(variances) {
    const total = variances.length;
    const unintentional = variances.filter(v => !v.is_intentional).length;
    const uniquePlugins = new Set(variances.map(v => v.plugin_name)).size;
    
    document.getElementById('total-variances').textContent = total;
    document.getElementById('unintentional-variances').textContent = unintentional;
    document.getElementById('plugins-with-variances').textContent = uniquePlugins;
}

function populateFilters() {
    // Populate server filter
    const serverFilter = document.getElementById('variance-filter-server');
    if (!serverFilter) return;
    
    const servers = new Set(allVariances.map(v => v.server_name).filter(s => s));
    
    // Clear existing options except first
    while (serverFilter.options.length > 1) {
        serverFilter.remove(1);
    }
    
    servers.forEach(server => {
        const option = document.createElement('option');
        option.value = server;
        option.textContent = server;
        serverFilter.appendChild(option);
    });
    
    // Populate plugin filter
    const pluginFilter = document.getElementById('variance-filter-plugin');
    if (!pluginFilter) return;
    
    const plugins = new Set(allVariances.map(v => v.plugin_name).filter(p => p));
    
    // Clear existing options except first
    while (pluginFilter.options.length > 1) {
        pluginFilter.remove(1);
    }
    
    plugins.forEach(plugin => {
        const option = document.createElement('option');
        option.value = plugin;
        option.textContent = plugin;
        pluginFilter.appendChild(option);
    });
}

// ====================
// Filtering
// ====================

function applyFilters() {
    const serverFilter = document.getElementById('variance-filter-server')?.value || '';
    const pluginFilter = document.getElementById('variance-filter-plugin')?.value || '';
    const statusFilter = document.getElementById('variance-filter-status')?.value || '';
    
    filteredVariances = allVariances.filter(v => {
        if (serverFilter && v.server_name !== serverFilter) return false;
        if (pluginFilter && v.plugin_name !== pluginFilter) return false;
        if (statusFilter === 'intentional' && !v.is_intentional) return false;
        if (statusFilter === 'unintentional' && v.is_intentional) return false;
        return true;
    });
    
    renderVariancesTable(filteredVariances);
    updateSummaryCards(filteredVariances);
}

// ====================
// Event Handlers
// ====================

function toggleSelectAllVariances(event) {
    const checked = event.target.checked;
    const checkboxes = document.querySelectorAll('.variance-checkbox');
    checkboxes.forEach(cb => cb.checked = checked);
}

function getSelectedVarianceIds() {
    const checkboxes = document.querySelectorAll('.variance-checkbox:checked');
    return Array.from(checkboxes).map(cb => parseInt(cb.value));
}

async function refreshVariances() {
    const btn = document.getElementById('refresh-variances-btn');
    if (!btn) return;
    
    btn.disabled = true;
    btn.textContent = 'Refreshing...';
    
    try {
        await fetchAllVariances();
        applyFilters();
    } finally {
        btn.disabled = false;
        btn.textContent = 'Refresh';
    }
}

async function applyDefaultsToSelected() {
    const selectedIds = getSelectedVarianceIds();
    
    if (selectedIds.length === 0) {
        alert('Please select at least one variance to apply defaults');
        return;
    }
    
    if (!confirm(`Apply default values to ${selectedIds.length} variance(s)?`)) return;
    
    let successCount = 0;
    let failCount = 0;
    
    for (const id of selectedIds) {
        const variance = allVariances.find(v => (v.id || v.variance_id) === id);
        if (!variance) continue;
        
        try {
            await applyDefaultValue(variance.plugin_name, variance.instance_id, variance.config_key);
            successCount++;
        } catch (error) {
            failCount++;
        }
    }
    
    alert(`Applied defaults: ${successCount} succeeded, ${failCount} failed`);
    
    // Refresh data
    await fetchAllVariances();
    applyFilters();
    
    // Clear selections
    const selectAll = document.getElementById('select-all-variances');
    if (selectAll) selectAll.checked = false;
}

async function markSelectedAsIntentional() {
    const selectedIds = getSelectedVarianceIds();
    
    if (selectedIds.length === 0) {
        alert('Please select at least one variance to mark');
        return;
    }
    
    if (!confirm(`Mark ${selectedIds.length} variance(s) as intentional?`)) return;
    
    let successCount = 0;
    
    for (const id of selectedIds) {
        try {
            await markVarianceIntentional(id, true);
            successCount++;
        } catch (error) {
            console.error(`Failed to mark variance ${id}:`, error);
        }
    }
    
    alert(`Marked ${successCount} variance(s) as intentional`);
    
    // Refresh data
    await fetchAllVariances();
    applyFilters();
    
    // Clear selections
    const selectAll = document.getElementById('select-all-variances');
    if (selectAll) selectAll.checked = false;
}

async function syncSelectedConfigs() {
    const selectedIds = getSelectedVarianceIds();
    
    if (selectedIds.length === 0) {
        alert('Please select at least one variance to sync');
        return;
    }
    
    alert('Config sync will deploy baseline configs to selected instances');
}

async function applyDefaultToVariance(pluginName, instanceId, configKey) {
    if (!confirm(`Apply default value for ${configKey}?`)) return;
    
    try {
        await applyDefaultValue(pluginName, instanceId, configKey);
        alert('Default value applied successfully');
        
        // Refresh data
        await fetchAllVariances();
        applyFilters();
    } catch (error) {
        alert('Failed to apply default value');
    }
}

// ====================
// Polling
// ====================

function startVariancePolling() {
    if (variancePollingTimer) {
        clearInterval(variancePollingTimer);
    }
    
    variancePollingTimer = setInterval(() => {
        const view = document.getElementById('variance-report-view');
        if (view && view.style.display !== 'none') {
            fetchAllVariances().then(() => applyFilters());
        }
    }, VARIANCE_POLL_INTERVAL);
}

function stopVariancePolling() {
    if (variancePollingTimer) {
        clearInterval(variancePollingTimer);
        variancePollingTimer = null;
    }
}

// ====================
// Utility Functions
// ====================

function formatValue(value) {
    if (value === null || value === undefined) return '<em>null</em>';
    if (typeof value === 'boolean') return value ? 'true' : 'false';
    if (typeof value === 'string' && value.length > 50) {
        return `<span title="${escapeHtml(value)}">${escapeHtml(value.substring(0, 47))}...</span>`;
    }
    return escapeHtml(String(value));
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// ====================
// Module Export for app.js
// ====================

window.varianceReportModule = {
    init: async function(params) {
        console.log('Variance Report module initialized');
        loadVarianceReport();
    },
    refresh: async function() {
        console.log('Variance Report refresh');
        await fetchAllVariances();
        applyFilters();
    },
    cleanup: async function() {
        console.log('Variance Report cleanup');
        stopVariancePolling();
    }
};
