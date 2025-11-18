// Config Editor JavaScript
// Edit config files with backup/restore functionality

const API_BASE = '/api';
let currentFileId = null;
let currentFileData = null;

// Get URL parameters
function getUrlParams() {
    const params = new URLSearchParams(window.location.search);
    return {
        id: params.get('id'),
        mode: params.get('mode') || 'edit'
    };
}

// Load file data
async function loadFile() {
    const params = getUrlParams();
    currentFileId = params.id;
    
    if (!currentFileId) {
        alert('No file ID provided');
        window.location.href = 'config_browser.html';
        return;
    }
    
    try {
        // Load file details
        const detailsResp = await fetch(`${API_BASE}/config/files/${currentFileId}`);
        const detailsData = await detailsResp.json();
        currentFileData = detailsData;
        
        // Load file content
        const contentResp = await fetch(`${API_BASE}/config/files/${currentFileId}/content`);
        const contentData = await contentResp.json();
        
        // Populate UI
        document.getElementById('file-name').textContent = detailsData.file_path;
        document.getElementById('file-instance').textContent = detailsData.instance_name;
        document.getElementById('file-plugin').textContent = detailsData.plugin_name || 'N/A';
        document.getElementById('file-type').textContent = detailsData.file_type;
        document.getElementById('file-size').textContent = formatFileSize(detailsData.file_size);
        document.getElementById('file-modified').textContent = formatDate(detailsData.last_modified_at);
        
        // Set editor content
        document.getElementById('file-content').value = contentData.content;
        
        // Load backups
        await loadBackups();
        
        // Set read-only if view mode
        if (params.mode === 'view') {
            document.getElementById('file-content').readOnly = true;
            document.getElementById('save-btn').disabled = true;
            document.getElementById('modify-key-input').disabled = true;
            document.getElementById('modify-value-input').disabled = true;
            document.getElementById('apply-modify-btn').disabled = true;
        }
        
    } catch (error) {
        console.error('Error loading file:', error);
        alert('Failed to load file');
    }
}

// Load backup history
async function loadBackups() {
    try {
        const response = await fetch(`${API_BASE}/config/files/${currentFileId}/backups`);
        const data = await response.json();
        
        const list = document.getElementById('backup-list');
        list.innerHTML = '';
        
        if (data.backups.length === 0) {
            list.innerHTML = '<p style="color: #718096; font-size: 0.9em;">No backups yet</p>';
            return;
        }
        
        data.backups.forEach(backup => {
            const item = document.createElement('div');
            item.className = 'backup-item';
            item.onclick = () => confirmRestore(backup.backup_id);
            
            const date = new Date(backup.created_at);
            const reason = backup.backup_reason || 'Manual';
            
            item.innerHTML = `
                <div style="font-weight: 600; font-size: 0.9em;">${date.toLocaleString()}</div>
                <div style="font-size: 0.85em; color: #718096;">${reason}</div>
            `;
            
            list.appendChild(item);
        });
        
    } catch (error) {
        console.error('Error loading backups:', error);
    }
}

// Create backup
async function createBackup() {
    try {
        const response = await fetch(`${API_BASE}/config/files/${currentFileId}/backup`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({reason: 'Manual backup from editor'})
        });
        
        const data = await response.json();
        alert('Backup created successfully!');
        await loadBackups();
        
    } catch (error) {
        console.error('Error creating backup:', error);
        alert('Failed to create backup');
    }
}

// Confirm restore
function confirmRestore(backupId) {
    if (confirm('Are you sure you want to restore this backup? Current changes will be lost.')) {
        restoreBackup(backupId);
    }
}

// Restore backup
async function restoreBackup(backupId) {
    try {
        const response = await fetch(`${API_BASE}/config/files/${currentFileId}/restore/${backupId}`, {
            method: 'POST'
        });
        
        if (response.ok) {
            alert('Backup restored successfully!');
            await loadFile();
        } else {
            const error = await response.json();
            alert(`Failed to restore: ${error.detail || 'Unknown error'}`);
        }
        
    } catch (error) {
        console.error('Error restoring backup:', error);
        alert('Failed to restore backup');
    }
}

// Save changes
async function saveChanges() {
    const content = document.getElementById('file-content').value;
    
    try {
        const response = await fetch(`${API_BASE}/config/files/${currentFileId}/content`, {
            method: 'PUT',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                content: content,
                create_backup: true,
                backup_reason: 'Before manual edit'
            })
        });
        
        if (response.ok) {
            alert('Changes saved successfully!');
            await loadFile();
        } else {
            const error = await response.json();
            alert(`Failed to save: ${error.detail || 'Unknown error'}`);
        }
        
    } catch (error) {
        console.error('Error saving changes:', error);
        alert('Failed to save changes');
    }
}

// Modify specific key
async function modifyKey() {
    const keyPath = document.getElementById('modify-key-input').value;
    const newValue = document.getElementById('modify-value-input').value;
    
    if (!keyPath) {
        alert('Please enter a key path');
        return;
    }
    
    try {
        // Parse new value as JSON if possible
        let parsedValue;
        try {
            parsedValue = JSON.parse(newValue);
        } catch {
            parsedValue = newValue;
        }
        
        const response = await fetch(`${API_BASE}/config/files/${currentFileId}/content`, {
            method: 'PUT',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                key_path: keyPath,
                value: parsedValue,
                create_backup: true,
                backup_reason: `Modify key: ${keyPath}`
            })
        });
        
        if (response.ok) {
            alert('Key modified successfully!');
            document.getElementById('modify-key-input').value = '';
            document.getElementById('modify-value-input').value = '';
            await loadFile();
        } else {
            const error = await response.json();
            alert(`Failed to modify: ${error.detail || 'Unknown error'}`);
        }
        
    } catch (error) {
        console.error('Error modifying key:', error);
        alert('Failed to modify key');
    }
}

// Go back to browser
function goBack() {
    window.location.href = 'config_browser.html';
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

// Initialize
loadFile();
