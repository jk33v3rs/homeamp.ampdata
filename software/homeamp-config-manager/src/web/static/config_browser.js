// Config Browser JavaScript
// Manages config file listing and filtering

const API_BASE = '/api';
let allConfigFiles = [];
let filteredFiles = [];

// Load initial data
async function loadConfigFiles() {
    try {
        const response = await fetch(`${API_BASE}/config/files`);
        const data = await response.json();
        
        allConfigFiles = data.config_files;
        filteredFiles = allConfigFiles;
        
        updateStats();
        populateFilters();
        renderConfigTable();
    } catch (error) {
        console.error('Error loading config files:', error);
        showError('Failed to load config files');
    }
}

// Update statistics
function updateStats() {
    const instances = new Set(allConfigFiles.map(f => f.instance_id));
    const plugins = new Set(allConfigFiles.map(f => f.plugin_id));
    
    document.getElementById('total-files').textContent = allConfigFiles.length;
    document.getElementById('total-instances').textContent = instances.size;
    document.getElementById('total-plugins').textContent = plugins.size;
}

// Populate filter dropdowns
function populateFilters() {
    const instances = [...new Set(allConfigFiles.map(f => ({
        id: f.instance_id,
        name: f.instance_name
    })))];
    
    const plugins = [...new Set(allConfigFiles.map(f => ({
        id: f.plugin_id,
        name: f.plugin_name
    })))];
    
    const instanceSelect = document.getElementById('filter-instance');
    instances.forEach(inst => {
        const option = document.createElement('option');
        option.value = inst.id;
        option.textContent = inst.name;
        instanceSelect.appendChild(option);
    });
    
    const pluginSelect = document.getElementById('filter-plugin');
    plugins.forEach(plugin => {
        const option = document.createElement('option');
        option.value = plugin.id;
        option.textContent = plugin.name;
        pluginSelect.appendChild(option);
    });
}

// Render config file table
function renderConfigTable() {
    const tbody = document.getElementById('config-table-body');
    tbody.innerHTML = '';
    
    if (filteredFiles.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="7" style="text-align: center; padding: 40px; color: #718096;">
                    No config files found matching filters
                </td>
            </tr>
        `;
        return;
    }
    
    filteredFiles.forEach(file => {
        const row = document.createElement('tr');
        row.innerHTML = `
            <td>${file.instance_name}</td>
            <td>${file.plugin_name || '-'}</td>
            <td style="font-family: 'Courier New', monospace; font-size: 0.85em;">${file.file_path}</td>
            <td><span class="file-type-badge file-type-${file.file_type}">${file.file_type}</span></td>
            <td>${formatFileSize(file.file_size)}</td>
            <td>${formatDate(file.last_modified_at)}</td>
            <td>
                <button class="action-btn btn-view" onclick="viewFile(${file.config_file_id})">👁️ View</button>
                <button class="action-btn btn-edit" onclick="editFile(${file.config_file_id})">✏️ Edit</button>
                <button class="action-btn btn-backup" onclick="backupFile(${file.config_file_id})">💾 Backup</button>
            </td>
        `;
        tbody.appendChild(row);
    });
}

// Apply filters
function applyFilters() {
    const instanceFilter = document.getElementById('filter-instance').value;
    const pluginFilter = document.getElementById('filter-plugin').value;
    const typeFilter = document.getElementById('filter-type').value;
    const searchFilter = document.getElementById('filter-search').value.toLowerCase();
    
    filteredFiles = allConfigFiles.filter(file => {
        if (instanceFilter && file.instance_id != instanceFilter) return false;
        if (pluginFilter && file.plugin_id !== pluginFilter) return false;
        if (typeFilter && file.file_type !== typeFilter) return false;
        if (searchFilter && !file.file_path.toLowerCase().includes(searchFilter)) return false;
        return true;
    });
    
    renderConfigTable();
}

// File actions
function viewFile(fileId) {
    window.location.href = `config_editor.html?id=${fileId}&mode=view`;
}

function editFile(fileId) {
    window.location.href = `config_editor.html?id=${fileId}&mode=edit`;
}

async function backupFile(fileId) {
    try {
        const response = await fetch(`${API_BASE}/config/files/${fileId}/backup`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({reason: 'manual'})
        });
        
        const data = await response.json();
        alert(`Backup created successfully!\nBackup ID: ${data.backup_id}`);
    } catch (error) {
        console.error('Error creating backup:', error);
        alert('Failed to create backup');
    }
}

// Utility functions
function formatFileSize(bytes) {
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
    return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
}

function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleDateString() + ' ' + date.toLocaleTimeString();
}

function showError(message) {
    const tbody = document.getElementById('config-table-body');
    tbody.innerHTML = `
        <tr>
            <td colspan="7" style="text-align: center; padding: 40px; color: #ef4444;">
                ${message}
            </td>
        </tr>
    `;
}

// Event listeners
document.getElementById('filter-instance').addEventListener('change', applyFilters);
document.getElementById('filter-plugin').addEventListener('change', applyFilters);
document.getElementById('filter-type').addEventListener('change', applyFilters);
document.getElementById('filter-search').addEventListener('input', applyFilters);

// Initialize
loadConfigFiles();
