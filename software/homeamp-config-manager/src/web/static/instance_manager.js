/**
 * Instance Manager JavaScript
 * Displays and manages all Minecraft server instances
 */

// Constants
const INSTANCE_POLL_INTERVAL = 30000; // 30 seconds
let instancePollingTimer = null;
let allInstances = [];
let allTags = [];

// ====================
// Initialization
// ====================

function loadInstanceManager() {
    console.log('Loading Instance Manager...');
    
    // Set up event listeners
    document.getElementById('refresh-instances-btn')?.addEventListener('click', refreshInstances);
    document.getElementById('instance-filter-server')?.addEventListener('change', applyInstanceFilters);
    document.getElementById('instance-filter-status')?.addEventListener('change', applyInstanceFilters);
    document.getElementById('instance-filter-tag')?.addEventListener('change', applyInstanceFilters);
    document.getElementById('instance-search-input')?.addEventListener('input', applyInstanceFilters);
    
    // Modal close button
    const closeBtn = document.querySelector('#instance-details-modal .close');
    if (closeBtn) {
        closeBtn.addEventListener('click', closeInstanceModal);
    }
    
    // Load initial data
    Promise.all([
        fetchAllInstances(),
        fetchAllTags()
    ]).then(() => {
        populateFilters();
        renderInstancesTable(allInstances);
        updateSummaryCards(allInstances);
    });
    
    // Start polling
    startInstancePolling();
}

// ====================
// API Functions
// ====================

async function fetchAllInstances() {
    try {
        const response = await fetch('/api/instances');
        if (!response.ok) throw new Error('Failed to fetch instances');
        
        allInstances = await response.json();
        return allInstances;
    } catch (error) {
        console.error('Error fetching instances:', error);
        document.getElementById('instances-table-body').innerHTML = 
            '<tr><td colspan="8" class="error">Failed to load instances</td></tr>';
        return [];
    }
}

async function fetchAllTags() {
    try {
        const response = await fetch('/api/tags');
        if (!response.ok) throw new Error('Failed to fetch tags');
        
        allTags = await response.json();
        return allTags;
    } catch (error) {
        console.error('Error fetching tags:', error);
        return [];
    }
}

async function fetchInstanceDetails(instanceId) {
    try {
        const response = await fetch(`/api/instances/${instanceId}`);
        if (!response.ok) throw new Error('Failed to fetch instance details');
        
        return await response.json();
    } catch (error) {
        console.error('Error fetching instance details:', error);
        return null;
    }
}

// ====================
// UI Rendering
// ====================

function renderInstancesTable(instances) {
    const tbody = document.getElementById('instances-table-body');
    
    if (!instances || instances.length === 0) {
        tbody.innerHTML = '<tr><td colspan="8" class="no-data">No instances found</td></tr>';
        return;
    }
    
    tbody.innerHTML = instances.map(inst => {
        const statusClass = getStatusClass(inst.status);
        const lastSynced = inst.last_synced_at ? formatDateTime(inst.last_synced_at) : 'Never';
        const pluginCount = inst.plugin_count || 0;
        const tags = inst.tags ? inst.tags.split(',').map(t => `<span class="tag-badge">${escapeHtml(t)}</span>`).join(' ') : '-';
        
        return `
            <tr class="instance-row" data-instance-id="${inst.instance_id}">
                <td><strong>${escapeHtml(inst.instance_name)}</strong></td>
                <td>${escapeHtml(inst.server_name)}</td>
                <td>
                    <span class="status-badge ${statusClass}">
                        ${capitalizeFirst(inst.status || 'unknown')}
                    </span>
                </td>
                <td>${inst.player_count !== undefined ? `${inst.player_count}/${inst.max_players || '?'}` : '-'}</td>
                <td>${pluginCount} plugins</td>
                <td>${tags}</td>
                <td>${lastSynced}</td>
                <td class="action-buttons">
                    <button class="btn-small" onclick="viewInstanceDetails(${inst.instance_id})">
                        View Details
                    </button>
                </td>
            </tr>
        `;
    }).join('');
}

function updateSummaryCards(instances) {
    const total = instances.length;
    const online = instances.filter(i => i.status === 'online').length;
    const offline = instances.filter(i => i.status === 'offline').length;
    
    // Calculate total unique plugins across all instances
    const pluginSet = new Set();
    instances.forEach(inst => {
        if (inst.plugin_count) {
            // This is approximation - real count would need instance_plugins join
            pluginSet.add(inst.instance_id); // Placeholder
        }
    });
    
    document.getElementById('total-instances-count').textContent = total;
    document.getElementById('online-instances-count').textContent = online;
    document.getElementById('offline-instances-count').textContent = offline;
    document.getElementById('total-plugins-count').textContent = instances.reduce((sum, i) => sum + (i.plugin_count || 0), 0);
}

function populateFilters() {
    // Populate server filter
    const serverFilter = document.getElementById('instance-filter-server');
    if (serverFilter) {
        const servers = [...new Set(allInstances.map(i => i.server_name))].filter(Boolean);
        serverFilter.innerHTML = '<option value="">All Servers</option>' + 
            servers.map(s => `<option value="${escapeHtml(s)}">${escapeHtml(s)}</option>`).join('');
    }
    
    // Populate tag filter
    const tagFilter = document.getElementById('instance-filter-tag');
    if (tagFilter && allTags.length > 0) {
        tagFilter.innerHTML = '<option value="">All Tags</option>' + 
            allTags.map(t => `<option value="${escapeHtml(t.tag_name)}">${escapeHtml(t.tag_name)}</option>`).join('');
    }
}

async function viewInstanceDetails(instanceId) {
    try {
        const details = await fetchInstanceDetails(instanceId);
        if (!details) {
            alert('Failed to load instance details');
            return;
        }
        
        const modal = document.getElementById('instance-details-modal');
        const content = document.getElementById('instance-details-content');
        
        let html = '<div class="instance-details">';
        
        // Basic info
        html += `
            <div class="detail-section">
                <h4>Basic Information</h4>
                <p><strong>Instance Name:</strong> ${escapeHtml(details.instance_name)}</p>
                <p><strong>Server:</strong> ${escapeHtml(details.server_name)}</p>
                <p><strong>Status:</strong> <span class="status-badge ${getStatusClass(details.status)}">${capitalizeFirst(details.status || 'unknown')}</span></p>
                <p><strong>AMP Instance ID:</strong> ${escapeHtml(details.amp_instance_id)}</p>
                <p><strong>Base Path:</strong> <code>${escapeHtml(details.base_path || 'N/A')}</code></p>
                <p><strong>Last Synced:</strong> ${details.last_synced_at ? formatDateTime(details.last_synced_at) : 'Never'}</p>
            </div>
        `;
        
        // Server info (if available)
        if (details.player_count !== undefined || details.max_players) {
            html += `
                <div class="detail-section">
                    <h4>Server Status</h4>
                    <p><strong>Players:</strong> ${details.player_count || 0}/${details.max_players || '?'}</p>
                    <p><strong>Version:</strong> ${escapeHtml(details.server_version || 'Unknown')}</p>
                </div>
            `;
        }
        
        // Plugins (if available)
        if (details.plugins && details.plugins.length > 0) {
            html += `
                <div class="detail-section">
                    <h4>Installed Plugins (${details.plugins.length})</h4>
                    <table class="detail-table">
                        <thead>
                            <tr>
                                <th>Plugin</th>
                                <th>Version</th>
                                <th>Enabled</th>
                            </tr>
                        </thead>
                        <tbody>
            `;
            
            details.plugins.forEach(p => {
                html += `
                    <tr>
                        <td>${escapeHtml(p.plugin_name)}</td>
                        <td>${escapeHtml(p.version || 'Unknown')}</td>
                        <td>${p.enabled ? '✅' : '❌'}</td>
                    </tr>
                `;
            });
            
            html += `
                        </tbody>
                    </table>
                </div>
            `;
        }
        
        // Tags (if available)
        if (details.tags && details.tags.length > 0) {
            html += `
                <div class="detail-section">
                    <h4>Meta-Tags</h4>
                    <p>${details.tags.map(t => `<span class="tag-badge">${escapeHtml(t)}</span>`).join(' ')}</p>
                </div>
            `;
        }
        
        html += '</div>';
        
        content.innerHTML = html;
        modal.style.display = 'block';
        
    } catch (error) {
        console.error('Error loading instance details:', error);
        alert('Failed to load instance details');
    }
}

function closeInstanceModal() {
    const modal = document.getElementById('instance-details-modal');
    if (modal) {
        modal.style.display = 'none';
    }
}

// ====================
// Filtering
// ====================

function applyInstanceFilters() {
    const serverFilter = document.getElementById('instance-filter-server')?.value || '';
    const statusFilter = document.getElementById('instance-filter-status')?.value || '';
    const tagFilter = document.getElementById('instance-filter-tag')?.value || '';
    const searchTerm = document.getElementById('instance-search-input')?.value.toLowerCase() || '';
    
    let filtered = allInstances.filter(inst => {
        // Server filter
        if (serverFilter && inst.server_name !== serverFilter) return false;
        
        // Status filter
        if (statusFilter && inst.status !== statusFilter) return false;
        
        // Tag filter
        if (tagFilter && (!inst.tags || !inst.tags.split(',').includes(tagFilter))) return false;
        
        // Search filter
        if (searchTerm && !inst.instance_name.toLowerCase().includes(searchTerm)) return false;
        
        return true;
    });
    
    renderInstancesTable(filtered);
    updateSummaryCards(filtered);
}

// ====================
// Event Handlers
// ====================

async function refreshInstances() {
    const btn = document.getElementById('refresh-instances-btn');
    if (!btn) return;
    
    btn.disabled = true;
    btn.textContent = 'Refreshing...';
    
    try {
        await fetchAllInstances();
        applyInstanceFilters();
    } finally {
        btn.disabled = false;
        btn.textContent = 'Refresh';
    }
}

// ====================
// Polling
// ====================

function startInstancePolling() {
    if (instancePollingTimer) {
        clearInterval(instancePollingTimer);
    }
    
    instancePollingTimer = setInterval(() => {
        const view = document.getElementById('instance-manager-view');
        if (view && view.style.display !== 'none') {
            fetchAllInstances().then(() => applyInstanceFilters());
        }
    }, INSTANCE_POLL_INTERVAL);
}

function stopInstancePolling() {
    if (instancePollingTimer) {
        clearInterval(instancePollingTimer);
        instancePollingTimer = null;
    }
}

// ====================
// Utility Functions
// ====================

function getStatusClass(status) {
    const statusMap = {
        'online': 'status-online',
        'offline': 'status-offline',
        'starting': 'status-starting',
        'stopping': 'status-stopping',
        'unknown': 'status-unknown'
    };
    return statusMap[status] || 'status-unknown';
}

function formatDateTime(dateString) {
    if (!dateString) return '-';
    try {
        const date = new Date(dateString);
        return date.toLocaleString();
    } catch {
        return dateString;
    }
}

function capitalizeFirst(str) {
    if (!str) return '';
    return str.charAt(0).toUpperCase() + str.slice(1);
}

function escapeHtml(text) {
    if (text === null || text === undefined) return '';
    const div = document.createElement('div');
    div.textContent = String(text);
    return div.innerHTML;
}

// ====================
// Module Export for app.js
// ====================

window.instanceManagerModule = {
    init: async function(params) {
        console.log('Instance Manager module initialized');
        loadInstanceManager();
    },
    refresh: async function() {
        console.log('Instance Manager refresh');
        await fetchAllInstances();
        applyInstanceFilters();
    },
    cleanup: async function() {
        console.log('Instance Manager cleanup');
        stopInstancePolling();
        closeInstanceModal();
    }
};
