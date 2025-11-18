// Rank Config JavaScript
// Manage rank-specific configuration rules (LuckPerms integration)

const API_BASE = '/api';
let allRanks = [];
let selectedRankId = null;
let currentRules = [];

// Load ranks
async function loadRanks() {
    try {
        const response = await fetch(`${API_BASE}/ranks`);
        const data = await response.json();
        
        allRanks = data.ranks;
        renderRankList();
        
    } catch (error) {
        console.error('Error loading ranks:', error);
    }
}

// Render rank list
function renderRankList() {
    const container = document.getElementById('rank-list');
    container.innerHTML = '';
    
    if (allRanks.length === 0) {
        container.innerHTML = '<p style="color: #718096; text-align: center;">No ranks registered yet</p>';
        return;
    }
    
    // Sort by priority (higher priority first)
    allRanks.sort((a, b) => b.priority - a.priority);
    
    allRanks.forEach(rank => {
        const div = document.createElement('div');
        div.className = 'rank-item';
        div.onclick = () => selectRank(rank.rank_id);
        
        div.innerHTML = `
            <div class="rank-name">${rank.rank_name}</div>
            <span class="rank-priority-badge">Priority: ${rank.priority}</span>
        `;
        
        container.appendChild(div);
    });
}

// Select rank
async function selectRank(rankId) {
    selectedRankId = rankId;
    
    // Update UI
    document.querySelectorAll('.rank-item').forEach(item => item.classList.remove('active'));
    event.currentTarget.classList.add('active');
    
    // Load rules for this rank
    await loadRankRules(rankId);
}

// Load rank rules
async function loadRankRules(rankId) {
    try {
        const response = await fetch(`${API_BASE}/config/rules?scope=RANK&rank_id=${rankId}`);
        const data = await response.json();
        
        currentRules = data.rules || [];
        renderRules();
        
    } catch (error) {
        console.error('Error loading rank rules:', error);
        currentRules = [];
        renderRules();
    }
}

// Render rules
function renderRules() {
    const container = document.getElementById('rule-list');
    
    if (currentRules.length === 0) {
        container.innerHTML = '<p style="color: #718096; text-align: center;">No rules configured for this rank</p>';
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

// Add rank config rule
async function addRankConfigRule() {
    if (!selectedRankId) {
        alert('Please select a rank first');
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
                scope: 'RANK',
                rank_id: selectedRankId
            })
        });
        
        if (response.ok) {
            alert('Rule added successfully!');
            document.getElementById('rule-key').value = '';
            document.getElementById('rule-value').value = '';
            await loadRankRules(selectedRankId);
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
            await loadRankRules(selectedRankId);
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
loadRanks();
loadPlugins();
