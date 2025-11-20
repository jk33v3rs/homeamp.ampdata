/**
 * Audit Log JavaScript
 * Displays system events and activity history
 */

// Constants
const AUDIT_PAGE_SIZE = 50;
let currentPage = 1;
let totalPages = 1;
let allAuditEvents = [];
let auditLogInstances = [];

// ====================
// Initialization
// ====================

function loadAuditLog() {
    console.log('Loading Audit Log...');
    
    // Set up event listeners
    document.getElementById('apply-audit-filters-btn')?.addEventListener('click', applyAuditFilters);
    document.getElementById('export-audit-log-btn')?.addEventListener('click', exportAuditLog);
    document.getElementById('audit-prev-page-btn')?.addEventListener('click', previousPage);
    document.getElementById('audit-next-page-btn')?.addEventListener('click', nextPage);
    
    // Modal close button
    const closeBtn = document.querySelector('#audit-details-modal .close');
    if (closeBtn) {
        closeBtn.addEventListener('click', closeAuditModal);
    }
    
    // Set default date range (last 7 days)
    const endDate = new Date();
    const startDate = new Date();
    startDate.setDate(startDate.getDate() - 7);
    
    const startInput = document.getElementById('audit-filter-start-date');
    const endInput = document.getElementById('audit-filter-end-date');
    
    if (startInput) startInput.value = startDate.toISOString().split('T')[0];
    if (endInput) endInput.value = endDate.toISOString().split('T')[0];
    
    // Load initial data
    Promise.all([
        fetchAuditEvents(),
        fetchAllInstances()
    ]).then(() => {
        populateInstanceFilter();
    });
}

// ====================
// API Functions
// ====================

async function fetchAuditEvents(filters = {}) {
    try {
        // Build query params
        const params = new URLSearchParams();
        params.append('page', currentPage.toString());
        params.append('page_size', AUDIT_PAGE_SIZE.toString());
        
        if (filters.event_type) params.append('event_type', filters.event_type);
        if (filters.instance_id) params.append('instance_id', filters.instance_id);
        if (filters.user) params.append('user', filters.user);
        if (filters.start_date) params.append('start_date', filters.start_date);
        if (filters.end_date) params.append('end_date', filters.end_date);
        
        const response = await fetch(`/api/audit-log/events?${params}`);
        if (!response.ok) throw new Error('Failed to fetch audit events');
        
        const data = await response.json();
        allAuditEvents = data.events || [];
        totalPages = data.total_pages || 1;
        
        renderAuditTable(allAuditEvents);
        updatePagination();
        
        return allAuditEvents;
    } catch (error) {
        console.error('Error fetching audit events:', error);
        document.getElementById('audit-log-table-body').innerHTML = 
            '<tr><td colspan="6" class="error">Failed to load audit events</td></tr>';
        return [];
    }
}

async function fetchAllInstances() {
    try {
        const response = await fetch('/api/dashboard/instances');
        if (!response.ok) throw new Error('Failed to fetch instances');
        
        auditLogInstances = await response.json();
        return auditLogInstances;
    } catch (error) {
        console.error('Error fetching instances:', error);
        return [];
    }
}

// ====================
// UI Rendering
// ====================

function renderAuditTable(events) {
    const tbody = document.getElementById('audit-log-table-body');
    
    if (!events || events.length === 0) {
        tbody.innerHTML = '<tr><td colspan="6" class="no-data">No audit events found</td></tr>';
        return;
    }
    
    tbody.innerHTML = events.map(event => {
        const timestamp = formatDateTime(event.timestamp);
        const eventTypeClass = getEventTypeClass(event.event_type);
        
        return `
            <tr class="audit-row">
                <td>${timestamp}</td>
                <td>
                    <span class="event-type-badge ${eventTypeClass}">
                        ${formatEventType(event.event_type)}
                    </span>
                </td>
                <td>${escapeHtml(event.instance_name || event.instance_id || '-')}</td>
                <td>${escapeHtml(event.user || 'System')}</td>
                <td>${escapeHtml(event.description || '-')}</td>
                <td class="action-buttons">
                    ${event.details ? `<button class="btn-small" onclick="viewAuditDetails(${event.event_id})">View</button>` : '-'}
                </td>
            </tr>
        `;
    }).join('');
}

function populateInstanceFilter() {
    const filter = document.getElementById('audit-filter-instance');
    if (!filter || auditLogInstances.length === 0) return;
    
    filter.innerHTML = '<option value="">All Instances</option>' + 
        auditLogInstances.map(inst => 
            `<option value="${inst.instance_id}">${escapeHtml(inst.instance_name)}</option>`
        ).join('');
}

function updatePagination() {
    const prevBtn = document.getElementById('audit-prev-page-btn');
    const nextBtn = document.getElementById('audit-next-page-btn');
    const pageInfo = document.getElementById('audit-page-info');
    
    if (prevBtn) prevBtn.disabled = currentPage <= 1;
    if (nextBtn) nextBtn.disabled = currentPage >= totalPages;
    if (pageInfo) pageInfo.textContent = `Page ${currentPage} of ${totalPages}`;
}

async function viewAuditDetails(eventId) {
    try {
        const event = allAuditEvents.find(e => e.event_id === eventId);
        if (!event) {
            alert('Event not found');
            return;
        }
        
        const modal = document.getElementById('audit-details-modal');
        const content = document.getElementById('audit-details-content');
        
        let html = '<div class="audit-details">';
        
        html += `
            <p><strong>Event ID:</strong> ${event.event_id}</p>
            <p><strong>Timestamp:</strong> ${formatDateTime(event.timestamp)}</p>
            <p><strong>Event Type:</strong> ${formatEventType(event.event_type)}</p>
            <p><strong>Instance:</strong> ${escapeHtml(event.instance_name || event.instance_id || 'N/A')}</p>
            <p><strong>User:</strong> ${escapeHtml(event.user || 'System')}</p>
            <p><strong>Description:</strong> ${escapeHtml(event.description || '-')}</p>
        `;
        
        if (event.details) {
            html += '<h4>Details:</h4>';
            html += '<pre>' + escapeHtml(JSON.stringify(event.details, null, 2)) + '</pre>';
        }
        
        html += '</div>';
        
        content.innerHTML = html;
        modal.style.display = 'block';
        
    } catch (error) {
        console.error('Error loading event details:', error);
        alert('Failed to load event details');
    }
}

function closeAuditModal() {
    const modal = document.getElementById('audit-details-modal');
    if (modal) {
        modal.style.display = 'none';
    }
}

// ====================
// Filtering and Pagination
// ====================

function applyAuditFilters() {
    currentPage = 1; // Reset to first page
    
    const filters = {
        event_type: document.getElementById('audit-filter-event-type')?.value || null,
        instance_id: document.getElementById('audit-filter-instance')?.value || null,
        user: document.getElementById('audit-filter-user')?.value || null,
        start_date: document.getElementById('audit-filter-start-date')?.value || null,
        end_date: document.getElementById('audit-filter-end-date')?.value || null
    };
    
    fetchAuditEvents(filters);
}

function previousPage() {
    if (currentPage > 1) {
        currentPage--;
        applyAuditFilters();
    }
}

function nextPage() {
    if (currentPage < totalPages) {
        currentPage++;
        applyAuditFilters();
    }
}

// ====================
// Export
// ====================

async function exportAuditLog() {
    try {
        const filters = {
            event_type: document.getElementById('audit-filter-event-type')?.value || null,
            instance_id: document.getElementById('audit-filter-instance')?.value || null,
            user: document.getElementById('audit-filter-user')?.value || null,
            start_date: document.getElementById('audit-filter-start-date')?.value || null,
            end_date: document.getElementById('audit-filter-end-date')?.value || null
        };
        
        // Build query params
        const params = new URLSearchParams();
        if (filters.event_type) params.append('event_type', filters.event_type);
        if (filters.instance_id) params.append('instance_id', filters.instance_id);
        if (filters.user) params.append('user', filters.user);
        if (filters.start_date) params.append('start_date', filters.start_date);
        if (filters.end_date) params.append('end_date', filters.end_date);
        
        const response = await fetch(`/api/audit-log/export?${params}`);
        if (!response.ok) throw new Error('Failed to export audit log');
        
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `audit_log_${new Date().toISOString().split('T')[0]}.csv`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        window.URL.revokeObjectURL(url);
        
    } catch (error) {
        console.error('Error exporting audit log:', error);
        alert('Failed to export audit log');
    }
}

// ====================
// Utility Functions
// ====================

function getEventTypeClass(eventType) {
    const classMap = {
        'config_change': 'event-config',
        'deployment': 'event-deployment',
        'plugin_update': 'event-update',
        'sync': 'event-sync',
        'approval': 'event-approval',
        'rejection': 'event-rejection'
    };
    return classMap[eventType] || 'event-default';
}

function formatEventType(eventType) {
    if (!eventType) return 'Unknown';
    return eventType.split('_').map(word => 
        word.charAt(0).toUpperCase() + word.slice(1)
    ).join(' ');
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

function escapeHtml(text) {
    if (text === null || text === undefined) return '';
    const div = document.createElement('div');
    div.textContent = String(text);
    return div.innerHTML;
}

// ====================
// Module Export for app.js
// ====================

window.auditLogModule = {
    init: async function(params) {
        console.log('Audit Log module initialized');
        loadAuditLog();
    },
    refresh: async function() {
        console.log('Audit Log refresh');
        applyAuditFilters();
    },
    cleanup: async function() {
        console.log('Audit Log cleanup');
        closeAuditModal();
    }
};
