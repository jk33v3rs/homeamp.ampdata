// Player Overrides JavaScript
// Manage per-player configuration overrides

const API_BASE = '/api';
let currentPlayer = null;
let currentOverrides = [];

// Search for player
async function searchPlayer() {
    const searchInput = document.getElementById('player-search').value.trim();
    
    if (!searchInput) {
        alert('Please enter a player name or UUID');
        return;
    }
    
    try {
        // Try to load player from Mojang API
        let playerData;
        
        // Check if input is UUID format
        const uuidRegex = /^[0-9a-f]{8}-?[0-9a-f]{4}-?[0-9a-f]{4}-?[0-9a-f]{4}-?[0-9a-f]{12}$/i;
        if (uuidRegex.test(searchInput)) {
            // UUID search
            playerData = await fetchPlayerByUuid(searchInput);
        } else {
            // Name search
            playerData = await fetchPlayerByName(searchInput);
        }
        
        if (playerData) {
            currentPlayer = playerData;
            displayPlayerInfo(playerData);
            await loadPlayerOverrides(playerData.uuid);
        } else {
            alert('Player not found');
        }
        
    } catch (error) {
        console.error('Error searching player:', error);
        alert('Failed to search for player');
    }
}

// Fetch player by UUID
async function fetchPlayerByUuid(uuid) {
    try {
        const response = await fetch(`https://sessionserver.mojang.com/session/minecraft/profile/${uuid.replace(/-/g, '')}`);
        if (response.ok) {
            const data = await response.json();
            return {
                uuid: formatUuid(data.id),
                name: data.name
            };
        }
        return null;
    } catch (error) {
        console.error('Error fetching by UUID:', error);
        return null;
    }
}

// Fetch player by name
async function fetchPlayerByName(name) {
    try {
        const response = await fetch(`https://api.mojang.com/users/profiles/minecraft/${name}`);
        if (response.ok) {
            const data = await response.json();
            return {
                uuid: formatUuid(data.id),
                name: data.name
            };
        }
        return null;
    } catch (error) {
        console.error('Error fetching by name:', error);
        return null;
    }
}

// Format UUID with dashes
function formatUuid(uuid) {
    if (uuid.includes('-')) return uuid;
    return `${uuid.substr(0, 8)}-${uuid.substr(8, 4)}-${uuid.substr(12, 4)}-${uuid.substr(16, 4)}-${uuid.substr(20)}`;
}

// Display player info
function displayPlayerInfo(player) {
    document.getElementById('player-info').style.display = 'block';
    document.getElementById('player-avatar').src = `https://crafatar.com/avatars/${player.uuid}?size=64`;
    document.getElementById('player-name').textContent = player.name;
    document.getElementById('player-uuid').textContent = player.uuid;
}

// Load player overrides
async function loadPlayerOverrides(playerUuid) {
    try {
        const response = await fetch(`${API_BASE}/config/rules?scope=PLAYER&player_uuid=${playerUuid}`);
        const data = await response.json();
        
        currentOverrides = data.rules || [];
        renderOverrides();
        
    } catch (error) {
        console.error('Error loading overrides:', error);
        currentOverrides = [];
        renderOverrides();
    }
}

// Render overrides
function renderOverrides() {
    const container = document.getElementById('override-list');
    
    if (currentOverrides.length === 0) {
        container.innerHTML = '<p style="color: #718096; text-align: center;">No overrides configured for this player</p>';
        return;
    }
    
    container.innerHTML = '';
    currentOverrides.forEach(override => {
        const div = document.createElement('div');
        div.className = 'override-item';
        
        div.innerHTML = `
            <div class="override-header">
                <div>
                    <strong>${override.plugin_name}</strong> - ${override.config_key}
                    ${override.instance_name ? `<span style="color: #718096; font-size: 0.85em;"> (${override.instance_name})</span>` : ''}
                </div>
                <button class="remove-btn" onclick="removeOverride(${override.rule_id})">✕ Remove</button>
            </div>
            <div class="override-value">${JSON.stringify(override.config_value)}</div>
        `;
        
        container.appendChild(div);
    });
}

// Add player override
async function addPlayerOverride() {
    if (!currentPlayer) {
        alert('Please search for a player first');
        return;
    }
    
    const instanceId = document.getElementById('override-instance').value;
    const pluginId = document.getElementById('override-plugin').value;
    const configKey = document.getElementById('override-key').value;
    const configValue = document.getElementById('override-value').value;
    
    if (!pluginId || !configKey || !configValue) {
        alert('Please fill in all required fields');
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
        
        const requestBody = {
            plugin_id: pluginId,
            config_key: configKey,
            config_value: parsedValue,
            scope: 'PLAYER',
            player_uuid: currentPlayer.uuid
        };
        
        if (instanceId) {
            requestBody.instance_id = instanceId;
        }
        
        const response = await fetch(`${API_BASE}/config/rules`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(requestBody)
        });
        
        if (response.ok) {
            alert('Override added successfully!');
            document.getElementById('override-instance').value = '';
            document.getElementById('override-plugin').value = '';
            document.getElementById('override-key').value = '';
            document.getElementById('override-value').value = '';
            await loadPlayerOverrides(currentPlayer.uuid);
        } else {
            const error = await response.json();
            alert(`Failed to add override: ${error.detail || 'Unknown error'}`);
        }
        
    } catch (error) {
        console.error('Error adding override:', error);
        alert('Failed to add override');
    }
}

// Remove override
async function removeOverride(ruleId) {
    if (!confirm('Are you sure you want to remove this override?')) return;
    
    try {
        const response = await fetch(`${API_BASE}/config/rules/${ruleId}`, {
            method: 'DELETE'
        });
        
        if (response.ok) {
            alert('Override removed successfully!');
            await loadPlayerOverrides(currentPlayer.uuid);
        }
        
    } catch (error) {
        console.error('Error removing override:', error);
        alert('Failed to remove override');
    }
}

// Load instances and plugins for dropdowns
async function loadDropdowns() {
    try {
        // Load instances
        const instancesResp = await fetch(`${API_BASE}/instances`);
        const instancesData = await instancesResp.json();
        
        const instanceSelect = document.getElementById('override-instance');
        instanceSelect.innerHTML = '<option value="">All instances (global override)</option>';
        
        instancesData.instances.forEach(instance => {
            const option = document.createElement('option');
            option.value = instance.instance_id;
            option.textContent = instance.instance_name;
            instanceSelect.appendChild(option);
        });
        
        // Load plugins
        const pluginsResp = await fetch(`${API_BASE}/plugins`);
        const pluginsData = await pluginsResp.json();
        
        const pluginSelect = document.getElementById('override-plugin');
        pluginSelect.innerHTML = '<option value="">Select plugin...</option>';
        
        pluginsData.plugins.forEach(plugin => {
            const option = document.createElement('option');
            option.value = plugin.plugin_id;
            option.textContent = plugin.plugin_name;
            pluginSelect.appendChild(option);
        });
        
    } catch (error) {
        console.error('Error loading dropdowns:', error);
    }
}

// Initialize
loadDropdowns();
