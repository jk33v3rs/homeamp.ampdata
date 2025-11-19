/**
 * Plugin Configurator View - YAML editor and variance management
 * Phase 2 implementation
 */

// ====================
// State Management
// ====================

let configuratorState = {
    plugins: [],
    selectedPlugin: null,
    selectedInstance: null,
    currentYaml: '',
    originalYaml: '',
    isDirty: false,
    variances: [],
    metaTags: [],
    yamlEditor: null
};

// ====================
// API Functions
// ====================

/**
 * Fetch all plugins for selection
 */
async function fetchPlugins(search = '', category = null, hasVariances = null) {
    try {
        let url = '/api/plugin-configurator/plugins?';
        if (search) url += `search=${encodeURIComponent(search)}&`;
        if (category) url += `category=${encodeURIComponent(category)}&`;
        if (hasVariances !== null) url += `has_variances=${hasVariances}&`;

        const response = await fetch(url);
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        const data = await response.json();
        configuratorState.plugins = data;
        return data;
    } catch (error) {
        console.error('Failed to fetch plugins:', error);
        showError('Failed to load plugin list');
        return [];
    }
}

/**
 * Fetch plugin details including meta tags
 */
async function fetchPluginDetails(pluginId) {
    try {
        const response = await fetch(`/api/plugin-configurator/plugins/${pluginId}`);
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        const data = await response.json();
        configuratorState.selectedPlugin = data;
        return data;
    } catch (error) {
        console.error('Failed to fetch plugin details:', error);
        showError('Failed to load plugin details');
        return null;
    }
}

/**
 * Fetch YAML config for plugin (baseline or instance)
 */
async function fetchPluginConfig(pluginId, instanceId = null) {
    try {
        let url = `/api/plugin-configurator/plugins/${pluginId}/config`;
        if (instanceId) url += `?instance_id=${instanceId}`;

        const response = await fetch(url);
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        const data = await response.json();
        configuratorState.currentYaml = data.yaml_content;
        configuratorState.originalYaml = data.yaml_content;
        configuratorState.isDirty = false;
        return data;
    } catch (error) {
        console.error('Failed to fetch plugin config:', error);
        showError('Failed to load configuration');
        return null;
    }
}

/**
 * Fetch variances for plugin
 */
async function fetchPluginVariances(pluginId) {
    try {
        const response = await fetch(`/api/plugin-configurator/plugins/${pluginId}/variances`);
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        const data = await response.json();
        configuratorState.variances = data;
        return data;
    } catch (error) {
        console.error('Failed to fetch variances:', error);
        showError('Failed to load variances');
        return [];
    }
}

/**
 * Fetch plugin instances
 */
async function fetchPluginInstances(pluginId) {
    try {
        const response = await fetch(`/api/plugin-configurator/plugins/${pluginId}/instances`);
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        return await response.json();
    } catch (error) {
        console.error('Failed to fetch plugin instances:', error);
        return [];
    }
}

/**
 * Fetch all meta tags
 */
async function fetchMetaTags() {
    try {
        const response = await fetch('/api/plugin-configurator/meta-tags');
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        const data = await response.json();
        configuratorState.metaTags = data;
        return data;
    } catch (error) {
        console.error('Failed to fetch meta tags:', error);
        return [];
    }
}

/**
 * Save YAML config
 */
async function savePluginConfig(pluginId, instanceId, yamlContent, commitMessage) {
    try {
        const response = await fetch(`/api/plugin-configurator/plugins/${pluginId}/save`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                plugin_id: pluginId,
                instance_id: instanceId,
                yaml_content: yamlContent,
                commit_message: commitMessage
            })
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Save failed');
        }

        const data = await response.json();
        configuratorState.originalYaml = yamlContent;
        configuratorState.isDirty = false;
        showSuccess('Configuration saved successfully');
        return data;
    } catch (error) {
        console.error('Failed to save config:', error);
        showError(`Failed to save: ${error.message}`);
        throw error;
    }
}

/**
 * Deploy config to multiple instances
 */
async function deployPluginConfig(pluginId, targetInstances, yamlContent, notes) {
    try {
        const response = await fetch(`/api/plugin-configurator/plugins/${pluginId}/deploy`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                plugin_id: pluginId,
                target_instances: targetInstances,
                yaml_content: yamlContent,
                deployment_notes: notes
            })
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Deployment failed');
        }

        const data = await response.json();
        showSuccess(`Deployment queued for ${data.target_count} instances`);
        return data;
    } catch (error) {
        console.error('Failed to deploy config:', error);
        showError(`Failed to deploy: ${error.message}`);
        throw error;
    }
}

/**
 * Assign meta tags to plugin
 */
async function assignMetaTags(pluginId, tagIds) {
    try {
        const response = await fetch(`/api/plugin-configurator/plugins/${pluginId}/tags`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                plugin_id: pluginId,
                tag_ids: tagIds
            })
        });

        if (!response.ok) throw new Error('Failed to assign tags');
        const data = await response.json();
        showSuccess('Tags updated');
        return data;
    } catch (error) {
        console.error('Failed to assign tags:', error);
        showError('Failed to update tags');
        throw error;
    }
}

/**
 * Mark variance as intentional/unintentional
 */
async function markVariance(varianceId, isIntentional, reason) {
    try {
        const response = await fetch('/api/plugin-configurator/variances/mark', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                variance_id: varianceId,
                is_intentional: isIntentional,
                reason: reason
            })
        });

        if (!response.ok) throw new Error('Failed to mark variance');
        const data = await response.json();
        showSuccess('Variance status updated');
        return data;
    } catch (error) {
        console.error('Failed to mark variance:', error);
        showError('Failed to update variance');
        throw error;
    }
}

// ====================
// Rendering Functions
// ====================

/**
 * Render plugin list
 */
function renderPluginList() {
    const container = document.getElementById('plugin-list');
    if (!container) return;

    if (configuratorState.plugins.length === 0) {
        container.innerHTML = '<p class="no-data">No plugins found</p>';
        return;
    }

    const html = configuratorState.plugins.map(plugin => {
        const badges = [];
        if (plugin.has_variances) badges.push('<span class="badge badge-warning">Variances</span>');
        if (plugin.update_available) badges.push('<span class="badge badge-info">Update</span>');
        if (!plugin.has_baseline) badges.push('<span class="badge badge-danger">No Baseline</span>');

        return `
            <div class="plugin-item ${configuratorState.selectedPlugin?.plugin_id === plugin.plugin_id ? 'active' : ''}" 
                 data-plugin-id="${plugin.plugin_id}">
                <div class="plugin-name">${escapeHtml(plugin.friendly_name || plugin.plugin_name)}</div>
                <div class="plugin-meta">
                    ${plugin.category ? `<span class="category">${escapeHtml(plugin.category)}</span>` : ''}
                    <span class="instance-count">${plugin.total_instances} instances</span>
                </div>
                <div class="plugin-badges">${badges.join(' ')}</div>
            </div>
        `;
    }).join('');

    container.innerHTML = html;
    attachPluginListHandlers();
}

/**
 * Render plugin meta tags
 */
function renderPluginTags() {
    const container = document.getElementById('plugin-tags');
    if (!container || !configuratorState.selectedPlugin) return;

    const tags = configuratorState.selectedPlugin.meta_tags || [];

    if (tags.length === 0) {
        container.innerHTML = '<p class="no-tags">No tags assigned</p>';
        return;
    }

    const html = tags.map(tag => `
        <div class="tag-bubble" style="background-color: ${tag.color || '#00d4ff'}">
            ${escapeHtml(tag.tag_name)}
            <span class="remove-tag" data-tag-id="${tag.tag_id}">×</span>
        </div>
    `).join('');

    container.innerHTML = html;
    attachTagRemoveHandlers();
}

/**
 * Render YAML editor content
 */
function renderYamlEditor(yamlContent) {
    const container = document.getElementById('yaml-editor-container');
    if (!container) return;

    // Simple textarea for now (will replace with CodeMirror/Monaco)
    if (!configuratorState.yamlEditor) {
        const textarea = document.createElement('textarea');
        textarea.id = 'yaml-editor';
        textarea.className = 'yaml-textarea';
        textarea.style.width = '100%';
        textarea.style.minHeight = '400px';
        textarea.style.fontFamily = 'Monaco, Courier New, monospace';
        textarea.style.fontSize = '14px';
        container.appendChild(textarea);
        configuratorState.yamlEditor = textarea;

        // Track changes
        textarea.addEventListener('input', () => {
            configuratorState.currentYaml = textarea.value;
            configuratorState.isDirty = textarea.value !== configuratorState.originalYaml;
            updateSaveButtonState();
        });
    }

    configuratorState.yamlEditor.value = yamlContent;
}

/**
 * Render variance list
 */
function renderVarianceList() {
    const container = document.getElementById('variance-list');
    if (!container) return;

    if (configuratorState.variances.length === 0) {
        container.innerHTML = '<p class="no-data">No variances detected</p>';
        return;
    }

    const html = `
        <table class="variance-table">
            <thead>
                <tr>
                    <th>Instance</th>
                    <th>Config Key</th>
                    <th>Expected</th>
                    <th>Actual</th>
                    <th>Status</th>
                    <th>Actions</th>
                </tr>
            </thead>
            <tbody>
                ${configuratorState.variances.map(v => `
                    <tr class="${v.is_intentional ? 'intentional' : 'unintentional'}">
                        <td>${escapeHtml(v.instance_name)} <span class="server-name">(${escapeHtml(v.server_name)})</span></td>
                        <td><code>${escapeHtml(v.config_key)}</code></td>
                        <td><code>${escapeHtml(JSON.stringify(v.expected_value))}</code></td>
                        <td><code>${escapeHtml(JSON.stringify(v.actual_value))}</code></td>
                        <td>
                            ${v.is_intentional 
                                ? '<span class="status-badge intentional">Intentional</span>' 
                                : '<span class="status-badge unintentional">Unintentional</span>'}
                        </td>
                        <td>
                            <button class="btn-sm mark-intentional" data-variance-id="${v.variance_id}" 
                                    data-current-status="${v.is_intentional}">
                                ${v.is_intentional ? 'Mark Unintentional' : 'Mark Intentional'}
                            </button>
                        </td>
                    </tr>
                `).join('')}
            </tbody>
        </table>
    `;

    container.innerHTML = html;
    attachVarianceHandlers();
}

/**
 * Update plugin name header
 */
function updatePluginNameHeader() {
    const header = document.getElementById('current-plugin-name');
    if (!header) return;

    if (configuratorState.selectedPlugin) {
        const name = configuratorState.selectedPlugin.friendly_name || configuratorState.selectedPlugin.plugin_name;
        header.textContent = name;
    } else {
        header.textContent = 'No plugin selected';
    }
}

/**
 * Update save button state based on dirty flag
 */
function updateSaveButtonState() {
    const saveBtn = document.getElementById('save-config-btn');
    if (saveBtn) {
        saveBtn.disabled = !configuratorState.isDirty;
        saveBtn.textContent = configuratorState.isDirty ? 'Save Configuration *' : 'Save Configuration';
    }
}

// ====================
// Event Handlers
// ====================

/**
 * Attach plugin list click handlers
 */
function attachPluginListHandlers() {
    document.querySelectorAll('.plugin-item').forEach(item => {
        item.addEventListener('click', async () => {
            const pluginId = parseInt(item.dataset.pluginId);
            await selectPlugin(pluginId);
        });
    });
}

/**
 * Attach tag remove handlers
 */
function attachTagRemoveHandlers() {
    document.querySelectorAll('.remove-tag').forEach(btn => {
        btn.addEventListener('click', async (e) => {
            e.stopPropagation();
            const tagId = parseInt(btn.dataset.tagId);
            await removeTag(tagId);
        });
    });
}

/**
 * Attach variance action handlers
 */
function attachVarianceHandlers() {
    document.querySelectorAll('.mark-intentional').forEach(btn => {
        btn.addEventListener('click', async () => {
            const varianceId = parseInt(btn.dataset.varianceId);
            const currentStatus = btn.dataset.currentStatus === 'true';
            const newStatus = !currentStatus;
            
            const reason = prompt(`${newStatus ? 'Mark intentional' : 'Mark unintentional'} - Reason (optional):`);
            if (reason === null) return; // Cancelled

            await markVariance(varianceId, newStatus, reason);
            await refreshVariances();
        });
    });
}

/**
 * Select a plugin and load its config
 */
async function selectPlugin(pluginId) {
    // Fetch plugin details
    const details = await fetchPluginDetails(pluginId);
    if (!details) return;

    // Fetch baseline config
    const config = await fetchPluginConfig(pluginId, null);
    if (config) {
        renderYamlEditor(config.yaml_content);
    }

    // Fetch variances
    await fetchPluginVariances(pluginId);

    // Render UI
    updatePluginNameHeader();
    renderPluginTags();
    renderVarianceList();
    renderPluginList(); // Re-render to highlight selected
}

/**
 * Remove tag from plugin
 */
async function removeTag(tagId) {
    if (!configuratorState.selectedPlugin) return;

    const currentTags = configuratorState.selectedPlugin.meta_tags.map(t => t.tag_id);
    const newTags = currentTags.filter(id => id !== tagId);

    await assignMetaTags(configuratorState.selectedPlugin.plugin_id, newTags);
    await fetchPluginDetails(configuratorState.selectedPlugin.plugin_id); // Refresh
    renderPluginTags();
}

/**
 * Refresh variances
 */
async function refreshVariances() {
    if (!configuratorState.selectedPlugin) return;
    await fetchPluginVariances(configuratorState.selectedPlugin.plugin_id);
    renderVarianceList();
}

/**
 * Save config handler
 */
async function handleSaveConfig() {
    if (!configuratorState.selectedPlugin || !configuratorState.isDirty) return;

    const commitMessage = prompt('Commit message (optional):');
    if (commitMessage === null) return; // Cancelled

    await savePluginConfig(
        configuratorState.selectedPlugin.plugin_id,
        configuratorState.selectedInstance, // null = baseline
        configuratorState.currentYaml,
        commitMessage
    );
}

/**
 * Deploy config handler
 */
async function handleDeployConfig() {
    if (!configuratorState.selectedPlugin) {
        showWarning('Please select a plugin first');
        return;
    }

    // Simple deployment to all instances for now
    // TODO: Show instance selection modal for granular control
    const confirmDeploy = confirm(
        `Deploy ${configuratorState.selectedPlugin.plugin_name} config to all instances?\n\n` +
        `This will queue deployment to ${configuratorState.selectedPlugin.total_instances} instances.`
    );

    if (!confirmDeploy) return;

    const notes = prompt('Deployment notes (optional):');
    if (notes === null) return; // Cancelled

    try {
        // Get all instance IDs for this plugin
        const instances = await fetchPluginInstances(configuratorState.selectedPlugin.plugin_id);
        const instanceIds = instances.map(i => i.instance_id);

        await deployPluginConfig(
            configuratorState.selectedPlugin.plugin_id,
            instanceIds,
            configuratorState.currentYaml,
            notes
        );
    } catch (error) {
        console.error('Deployment failed:', error);
    }
}

/**
 * Validate YAML handler
 */
function handleValidateYaml() {
    const yamlContent = configuratorState.currentYaml;
    const errorContainer = document.getElementById('yaml-validation-errors');

    try {
        // Simple YAML validation (will be improved with yaml library)
        if (!yamlContent.trim()) {
            throw new Error('YAML content is empty');
        }

        // Check for basic YAML structure issues
        const lines = yamlContent.split('\n');
        for (let i = 0; i < lines.length; i++) {
            const line = lines[i];
            // Check for tabs (YAML doesn't allow tabs)
            if (line.includes('\t')) {
                throw new Error(`Line ${i + 1}: YAML does not allow tab characters`);
            }
        }

        if (errorContainer) {
            errorContainer.style.display = 'none';
        }
        showSuccess('YAML syntax is valid');
    } catch (error) {
        if (errorContainer) {
            errorContainer.textContent = error.message;
            errorContainer.style.display = 'block';
        }
        showError(`YAML validation failed: ${error.message}`);
    }
}

/**
 * Format YAML handler
 */
function handleFormatYaml() {
    // TODO: Implement YAML formatting
    showWarning('YAML formatting not yet implemented');
}

/**
 * Revert changes handler
 */
function handleRevertChanges() {
    if (!configuratorState.isDirty) return;

    if (confirm('Revert all changes to last saved version?')) {
        configuratorState.currentYaml = configuratorState.originalYaml;
        configuratorState.isDirty = false;
        renderYamlEditor(configuratorState.originalYaml);
        updateSaveButtonState();
        showSuccess('Changes reverted');
    }
}

/**
 * Plugin search handler
 */
async function handlePluginSearch(searchTerm) {
    await fetchPlugins(searchTerm);
    renderPluginList();
}

// ====================
// Initialization
// ====================

async function initPluginConfigurator() {
    console.log('Initializing Plugin Configurator view');

    // Attach button handlers
    const saveBtn = document.getElementById('save-config-btn');
    const deployBtn = document.getElementById('deploy-config-btn');
    const validateBtn = document.getElementById('validate-yaml-btn');
    const formatBtn = document.getElementById('format-yaml-btn');
    const revertBtn = document.getElementById('revert-changes-btn');
    const searchInput = document.getElementById('plugin-search');

    if (saveBtn) saveBtn.addEventListener('click', handleSaveConfig);
    if (deployBtn) deployBtn.addEventListener('click', handleDeployConfig);
    if (validateBtn) validateBtn.addEventListener('click', handleValidateYaml);
    if (formatBtn) formatBtn.addEventListener('click', handleFormatYaml);
    if (revertBtn) revertBtn.addEventListener('click', handleRevertChanges);
    if (searchInput) {
        searchInput.addEventListener('input', (e) => {
            handlePluginSearch(e.target.value);
        });
    }

    // Load initial data
    await fetchPlugins();
    await fetchMetaTags();

    // Render
    renderPluginList();
}

// ====================
// Utility Functions
// ====================

// Placeholder patterns supported in configs
const PLACEHOLDER_PATTERNS = ['%SERVER_NAME%', '%INSTANCE_NAME%', '%INSTANCE_SHORT%'];

/**
 * Resolve placeholders in YAML content
 * Client-side preview - actual resolution happens server-side during deployment
 */
function resolvePlaceholders(yamlContent, instanceData) {
    let resolved = yamlContent;

    if (instanceData.server_name) {
        resolved = resolved.replace(/%SERVER_NAME%/g, instanceData.server_name);
    }
    if (instanceData.instance_name) {
        resolved = resolved.replace(/%INSTANCE_NAME%/g, instanceData.instance_name);
    }
    if (instanceData.instance_short) {
        resolved = resolved.replace(/%INSTANCE_SHORT%/g, instanceData.instance_short);
    }

    return resolved;
}

/**
 * Show placeholder preview for selected instance
 */
function showPlaceholderPreview(instanceData) {
    const yaml = configuratorState.currentYaml;
    const resolved = resolvePlaceholders(yaml, instanceData);

    // TODO: Show in modal or side panel
    console.log('Placeholder preview for', instanceData.instance_name);
    console.log('Resolved YAML:', resolved);
}

function escapeHtml(text) {
    if (text === null || text === undefined) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function showError(message) {
    console.error(message);
    // TODO: Implement toast notification
}

function showSuccess(message) {
    console.log(message);
    // TODO: Implement toast notification
}

function showWarning(message) {
    console.warn(message);
    // TODO: Implement toast notification
}

// Export for use by app.js
window.pluginConfiguratorModule = {
    init: initPluginConfigurator,
    refresh: async () => {
        await fetchPlugins();
        renderPluginList();
        if (configuratorState.selectedPlugin) {
            await refreshVariances();
        }
    }
};
