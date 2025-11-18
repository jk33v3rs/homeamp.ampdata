// Hierarchy Viewer JavaScript
// Interactive config hierarchy resolution

const API_BASE = '/api';

// Load initial data
async function loadDropdowns() {
    try {
        // Load plugins
        const pluginsResp = await fetch(`${API_BASE}/plugins`);
        const pluginsData = await pluginsResp.json();
        
        const pluginSelect = document.getElementById('query-plugin');
        pluginsData.plugins.forEach(plugin => {
            const option = document.createElement('option');
            option.value = plugin.plugin_id;
            option.textContent = plugin.plugin_name;
            pluginSelect.appendChild(option);
        });
        
        // Load instances
        const instancesResp = await fetch(`${API_BASE}/instances`);
        const instancesData = await instancesResp.json();
        
        const instanceSelect = document.getElementById('query-instance');
        instancesData.instances.forEach(instance => {
            const option = document.createElement('option');
            option.value = instance.instance_id;
            option.textContent = instance.instance_name;
            instanceSelect.appendChild(option);
        });
    } catch (error) {
        console.error('Error loading dropdowns:', error);
    }
}

// Resolve hierarchy
async function resolveHierarchy() {
    const pluginId = document.getElementById('query-plugin').value;
    const configKey = document.getElementById('query-key').value;
    const instanceId = document.getElementById('query-instance').value;
    const worldName = document.getElementById('query-world').value;
    const rankName = document.getElementById('query-rank').value;
    const playerUuid = document.getElementById('query-player').value;
    
    if (!pluginId || !configKey || !instanceId) {
        alert('Please fill in Plugin, Config Key, and Instance fields');
        return;
    }
    
    try {
        // Build query params
        const params = new URLSearchParams({
            plugin_id: pluginId,
            config_key: configKey,
            instance_id: instanceId
        });
        
        if (worldName) params.append('world_name', worldName);
        if (rankName) params.append('rank_name', rankName);
        if (playerUuid) params.append('player_uuid', playerUuid);
        
        const response = await fetch(`${API_BASE}/config/hierarchy?${params}`);
        const data = await response.json();
        
        displayResults(data);
    } catch (error) {
        console.error('Error resolving hierarchy:', error);
        alert('Failed to resolve config hierarchy');
    }
}

// Display resolution results
function displayResults(data) {
    const resultPanel = document.getElementById('result-panel');
    resultPanel.style.display = 'block';
    
    // Show effective value
    const valueDisplay = document.getElementById('effective-value');
    valueDisplay.textContent = JSON.stringify(data.resolved_value, null, 2);
    
    // Show source badge
    const sourceBadge = document.getElementById('source-badge');
    sourceBadge.textContent = data.source_scope;
    sourceBadge.className = `source-badge source-${data.source_scope.split(':')[0]}`;
    
    // Render resolution chain
    renderChain(data.resolution_chain);
    
    // Scroll to results
    resultPanel.scrollIntoView({behavior: 'smooth'});
}

// Render resolution chain
function renderChain(chain) {
    const container = document.getElementById('chain-container');
    container.innerHTML = '';
    
    if (!chain || chain.length === 0) {
        container.innerHTML = '<p style="color: #718096;">No resolution chain available</p>';
        return;
    }
    
    chain.forEach((item, index) => {
        const div = document.createElement('div');
        div.className = 'chain-item';
        
        if (item.overridden) {
            div.classList.add('overridden');
        } else if (index === chain.length - 1) {
            div.classList.add('active');
        }
        
        let scopeText = item.scope;
        if (item.server) scopeText += ` (${item.server})`;
        if (item.tag) scopeText += ` (${item.tag})`;
        if (item.world) scopeText += ` (${item.world})`;
        if (item.rank) scopeText += ` (${item.rank})`;
        if (item.player_uuid) scopeText += ` (${item.player_uuid})`;
        
        div.innerHTML = `
            <div class="scope">${scopeText}</div>
            <div class="value-display">${JSON.stringify(item.value)}</div>
            ${item.overridden ? '<div style="color: #ef4444; font-size: 0.85em; margin-top: 5px;">Overridden by higher priority</div>' : ''}
        `;
        
        container.appendChild(div);
    });
}

// Initialize
loadDropdowns();
