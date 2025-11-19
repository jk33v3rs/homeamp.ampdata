/**
 * Deployment Queue JavaScript
 * Displays and manages config deployment queue and history
 */

// Constants
const DEPLOYMENT_POLL_INTERVAL = 5000; // 5 seconds for active deployments
let deploymentPollingTimer = null;
let allDeployments = [];

// ====================
// Initialization
// ====================

function loadDeploymentQueue() {
    console.log('Loading Deployment Queue...');
    
    // Set up event listeners
    document.getElementById('refresh-deployments-btn')?.addEventListener('click', refreshDeployments);
    document.getElementById('deployment-filter-status')?.addEventListener('change', applyDeploymentFilters);
    
    // Modal close button
    const closeBtn = document.querySelector('#deployment-details-modal .close');
    if (closeBtn) {
        closeBtn.addEventListener('click', closeDeploymentModal);
    }
    
    // Load initial data
    fetchDeploymentQueue();
    
    // Start polling
    startDeploymentPolling();
}

// ====================
// API Functions
// ====================

async function fetchDeploymentQueue(status = null) {
    try {
        let url = '/api/deployment/queue';
        if (status) {
            url += `?status=${encodeURIComponent(status)}`;
        }
        
        const response = await fetch(url);
        if (!response.ok) throw new Error('Failed to fetch deployment queue');
        
        allDeployments = await response.json();
        renderDeploymentsTable(allDeployments);
        
        return allDeployments;
    } catch (error) {
        console.error('Error fetching deployment queue:', error);
        document.getElementById('deployments-table-body').innerHTML = 
            '<tr><td colspan="8" class="error">Failed to load deployments</td></tr>';
        return [];
    }
}

async function fetchDeploymentLogs(deploymentId) {
    try {
        const response = await fetch(`/api/deployment/logs/${deploymentId}`);
        if (!response.ok) throw new Error('Failed to fetch deployment logs');
        
        return await response.json();
    } catch (error) {
        console.error('Error fetching deployment logs:', error);
        return [];
    }
}

async function fetchDeploymentStatus(deploymentId) {
    try {
        const response = await fetch(`/api/deployment/status/${deploymentId}`);
        if (!response.ok) throw new Error('Failed to fetch deployment status');
        
        return await response.json();
    } catch (error) {
        console.error('Error fetching deployment status:', error);
        return null;
    }
}

// ====================
// UI Rendering
// ====================

function renderDeploymentsTable(deployments) {
    const tbody = document.getElementById('deployments-table-body');
    
    if (!deployments || deployments.length === 0) {
        tbody.innerHTML = '<tr><td colspan="8" class="no-data">No deployments found</td></tr>';
        return;
    }
    
    tbody.innerHTML = deployments.map(d => {
        const createdDate = d.created_at ? new Date(d.created_at).toLocaleString() : 'Unknown';
        const updatedDate = d.updated_at ? new Date(d.updated_at).toLocaleString() : '-';
        
        return `
            <tr class="deployment-row" data-deployment-id="${d.deployment_id}">
                <td>${d.deployment_id}</td>
                <td><strong>${escapeHtml(d.plugin_name)}</strong></td>
                <td>${d.instance_count || 0} instances</td>
                <td>
                    <span class="status-badge status-${d.status}">
                        ${capitalizeFirst(d.status)}
                    </span>
                </td>
                <td>${createdDate}</td>
                <td>${updatedDate}</td>
                <td>
                    <div class="progress-bar-mini">
                        <div class="progress-fill" style="width: 0%;"></div>
                    </div>
                </td>
                <td class="action-buttons">
                    <button class="btn-small" onclick="viewDeploymentDetails(${d.deployment_id})">
                        View Details
                    </button>
                </td>
            </tr>
        `;
    }).join('');
    
    // Update progress bars for active deployments
    deployments.forEach(d => {
        if (d.status === 'processing' || d.status === 'pending') {
            updateDeploymentProgress(d.deployment_id);
        }
    });
}

async function updateDeploymentProgress(deploymentId) {
    try {
        const status = await fetchDeploymentStatus(deploymentId);
        if (!status) return;
        
        const row = document.querySelector(`tr[data-deployment-id="${deploymentId}"]`);
        if (!row) return;
        
        const progressFill = row.querySelector('.progress-fill');
        if (progressFill && status.progress !== undefined) {
            progressFill.style.width = `${status.progress}%`;
        }
        
        // Update status badge if changed
        const statusBadge = row.querySelector('.status-badge');
        if (statusBadge && status.status) {
            statusBadge.className = `status-badge status-${status.status}`;
            statusBadge.textContent = capitalizeFirst(status.status);
        }
    } catch (error) {
        console.error(`Error updating progress for deployment ${deploymentId}:`, error);
    }
}

async function viewDeploymentDetails(deploymentId) {
    try {
        const [status, logs] = await Promise.all([
            fetchDeploymentStatus(deploymentId),
            fetchDeploymentLogs(deploymentId)
        ]);
        
        const modal = document.getElementById('deployment-details-modal');
        const content = document.getElementById('deployment-details-content');
        
        let html = '<div class="deployment-details">';
        
        // Status overview
        if (status) {
            html += `
                <div class="detail-section">
                    <h4>Deployment Status</h4>
                    <p><strong>Plugin:</strong> ${escapeHtml(status.plugin_name)}</p>
                    <p><strong>Status:</strong> <span class="status-badge status-${status.status}">${capitalizeFirst(status.status)}</span></p>
                    <p><strong>Progress:</strong> ${status.completed}/${status.total_instances} instances (${status.progress}%)</p>
                    <p><strong>Created:</strong> ${new Date(status.created_at).toLocaleString()}</p>
                    ${status.updated_at ? `<p><strong>Updated:</strong> ${new Date(status.updated_at).toLocaleString()}</p>` : ''}
                </div>
            `;
        }
        
        // Deployment logs
        if (logs && logs.length > 0) {
            html += `
                <div class="detail-section">
                    <h4>Deployment Logs (${logs.length} entries)</h4>
                    <table class="log-table">
                        <thead>
                            <tr>
                                <th>Instance</th>
                                <th>Status</th>
                                <th>Message</th>
                                <th>Timestamp</th>
                            </tr>
                        </thead>
                        <tbody>
            `;
            
            logs.forEach(log => {
                html += `
                    <tr>
                        <td>${escapeHtml(log.instance_name || log.instance_id)}</td>
                        <td><span class="status-badge status-${log.status}">${capitalizeFirst(log.status)}</span></td>
                        <td>${escapeHtml(log.message || '-')}</td>
                        <td>${new Date(log.timestamp).toLocaleString()}</td>
                    </tr>
                `;
            });
            
            html += `
                        </tbody>
                    </table>
                </div>
            `;
        } else {
            html += '<p><em>No deployment logs available</em></p>';
        }
        
        html += '</div>';
        
        content.innerHTML = html;
        modal.style.display = 'block';
        
    } catch (error) {
        console.error('Error loading deployment details:', error);
        alert('Failed to load deployment details');
    }
}

function closeDeploymentModal() {
    const modal = document.getElementById('deployment-details-modal');
    if (modal) {
        modal.style.display = 'none';
    }
}

// ====================
// Filtering
// ====================

function applyDeploymentFilters() {
    const statusFilter = document.getElementById('deployment-filter-status')?.value || '';
    fetchDeploymentQueue(statusFilter || null);
}

// ====================
// Event Handlers
// ====================

async function refreshDeployments() {
    const btn = document.getElementById('refresh-deployments-btn');
    if (!btn) return;
    
    btn.disabled = true;
    btn.textContent = 'Refreshing...';
    
    try {
        await fetchDeploymentQueue();
    } finally {
        btn.disabled = false;
        btn.textContent = 'Refresh';
    }
}

// ====================
// Polling
// ====================

function startDeploymentPolling() {
    if (deploymentPollingTimer) {
        clearInterval(deploymentPollingTimer);
    }
    
    deploymentPollingTimer = setInterval(() => {
        const view = document.getElementById('deployment-queue-view');
        if (view && view.style.display !== 'none') {
            fetchDeploymentQueue();
        }
    }, DEPLOYMENT_POLL_INTERVAL);
}

function stopDeploymentPolling() {
    if (deploymentPollingTimer) {
        clearInterval(deploymentPollingTimer);
        deploymentPollingTimer = null;
    }
}

// ====================
// Utility Functions
// ====================

function capitalizeFirst(str) {
    if (!str) return '';
    return str.charAt(0).toUpperCase() + str.slice(1);
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// ====================
// Module Export for app.js
// ====================

window.deploymentQueueModule = {
    init: async function(params) {
        console.log('Deployment Queue module initialized');
        loadDeploymentQueue();
    },
    refresh: async function() {
        console.log('Deployment Queue refresh');
        await fetchDeploymentQueue();
    },
    cleanup: async function() {
        console.log('Deployment Queue cleanup');
        stopDeploymentPolling();
        closeDeploymentModal();
    }
};
