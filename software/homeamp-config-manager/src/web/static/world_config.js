// World Config JavaScript
// Manage world-specific configuration rules

const API_BASE = '/api';
let allWorlds = [];
let selectedWorldId = null;
let currentRules = [];

// Load worlds
async function loadWorlds() {
    try {
        const response = await fetch(`${API_BASE}/worlds`);
        const data = await response.json();
        
        allWorlds = data.worlds;
        renderWorldList();
        
    } catch (error) {
        console.error('Error loading worlds:', error);
    }
}

// Render world list
function renderWorldList() {
    const container = document.getElementById('world-list');
    container.innerHTML = '';
    
    if (allWorlds.length === 0) {
        container.innerHTML = '<p style="color: #718096; text-align: center;">No worlds registered yet</p>';
        return;
    }
    
    allWorlds.forEach(world => {
        const div = document.createElement('div');
        div.className = 'world-item';
        div.onclick = () => selectWorld(world.world_id);
        
        const typeColors = {
            'normal': '#10b981',
            'nether': '#ef4444',
            'end': '#8b5cf6',
            'custom': '#f59e0b'
        };
        
        const typeColor = typeColors[world.world_type] || '#718096';
        
        div.innerHTML = `
            <div class="world-name">${world.world_name}</div>
            <span class="world-type-badge" style="background-color: ${typeColor};">
                ${world.world_type}
            </span>
        `;
        
        container.appendChild(div);
    });
}

// Select world
async function selectWorld(worldId) {
    selectedWorldId = worldId;
    
    // Update UI
    document.querySelectorAll('.world-item').forEach(item => item.classList.remove('active'));
    event.currentTarget.classList.add('active');
    
    // Load rules for this world
    await loadWorldRules(worldId);
}

// Load world rules
async function loadWorldRules(worldId) {
    try {
        const response = await fetch(`${API_BASE}/config/rules?scope=WORLD&world_id=${worldId}`);
        const data = await response.json();
        
        currentRules = data.rules || [];
        renderRules();
        
    } catch (error) {
        console.error('Error loading world rules:', error);
        currentRules = [];
        renderRules();
    }
}

// Render rules
function renderRules() {
    const container = document.getElementById('rule-list');
    
    if (currentRules.length === 0) {
        container.innerHTML = '<p style="color: #718096; text-align: center;">No rules configured for this world</p>';
        return;
    }
    
    container.innerHTML = '';
    currentRules.forEach(rule => {
        const div = document.createElement('div');
        div.className = 'rule-item';
        
        div.innerHTML = `
            <div class="rule-header">
                <strong>${rule.plugin_name}</strong> - ${rule.config_key}
                <button class="delete-btn" onclick="deleteRule(${rule.rule_id})">✕</button>
            </div>
            <div class="rule-value">${JSON.stringify(rule.config_value)}</div>
        `;
        
        container.appendChild(div);
    });
}

// Add world config rule
async function addWorldConfigRule() {
    if (!selectedWorldId) {
        alert('Please select a world first');
        return;
    }
    
    const pluginId = document.getElementById('rule-plugin').value;
    const configKey = document.getElementById('rule-key').value;
    const configValue = document.getElementById('rule-value').value;
    
    if (!pluginId || !configKey || !configValue) {
        alert('Please fill in all fields');
        return;
    }
    
    try {
        // Parse value as JSON if possible
        let parsedValue;
        try {
            parsedValue = JSON.parse(configValue);
        } catch {
            parsedValue = configValue;
        }
        
        const response = await fetch(`${API_BASE}/config/rules`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                plugin_id: pluginId,
                config_key: configKey,
                config_value: parsedValue,
                scope: 'WORLD',
                world_id: selectedWorldId
            })
        });
        
        if (response.ok) {
            alert('Rule added successfully!');
            document.getElementById('rule-key').value = '';
            document.getElementById('rule-value').value = '';
            await loadWorldRules(selectedWorldId);
        } else {
            const error = await response.json();
            alert(`Failed to add rule: ${error.detail || 'Unknown error'}`);
        }
        
    } catch (error) {
        console.error('Error adding rule:', error);
        alert('Failed to add rule');
    }
}

// Delete rule
async function deleteRule(ruleId) {
    if (!confirm('Are you sure you want to delete this rule?')) return;
    
    try {
        const response = await fetch(`${API_BASE}/config/rules/${ruleId}`, {
            method: 'DELETE'
        });
        
        if (response.ok) {
            alert('Rule deleted successfully!');
            await loadWorldRules(selectedWorldId);
        }
        
    } catch (error) {
        console.error('Error deleting rule:', error);
        alert('Failed to delete rule');
    }
}

// Load plugins for dropdown
async function loadPlugins() {
    try {
        const response = await fetch(`${API_BASE}/plugins`);
        const data = await response.json();
        
        const select = document.getElementById('rule-plugin');
        select.innerHTML = '<option value="">Select plugin...</option>';
        
        data.plugins.forEach(plugin => {
            const option = document.createElement('option');
            option.value = plugin.plugin_id;
            option.textContent = plugin.plugin_name;
            select.appendChild(option);
        });
        
    } catch (error) {
        console.error('Error loading plugins:', error);
    }
}

// Initialize
loadWorlds();
loadPlugins();
