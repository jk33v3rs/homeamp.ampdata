/**
 * Tag Manager Module
 * Manage meta-tags, categories, and instance assignments with drag-drop
 */

const TAG_MANAGER_POLL_INTERVAL = 60000; // 60 seconds
let tagManagerPollInterval = null;
let allTags = [];
let allCategories = [];
let allInstances = [];
let selectedInstances = [];

/**
 * Initialize Tag Manager view
 */
function loadTagManager() {
    console.log('[Tag Manager] Initializing view');
    
    // Attach event listeners
    document.getElementById('create-tag-btn')?.addEventListener('click', showCreateTagModal);
    document.getElementById('create-category-btn')?.addEventListener('click', showCreateCategoryModal);
    document.getElementById('refresh-tags-btn')?.addEventListener('click', () => {
        fetchAllTags();
        fetchAllCategories();
        fetchInstances();
    });
    
    // Modal buttons
    document.getElementById('save-tag-btn')?.addEventListener('click', saveTag);
    document.getElementById('save-category-btn')?.addEventListener('click', saveCategory);
    document.getElementById('cancel-tag-modal')?.addEventListener('click', closeTagModal);
    document.getElementById('cancel-category-modal')?.addEventListener('click', closeCategoryModal);
    
    // Bulk operations
    document.getElementById('assign-tags-bulk-btn')?.addEventListener('click', assignTagsBulk);
    document.getElementById('remove-tags-bulk-btn')?.addEventListener('click', removeTagsBulk);
    
    // Tab switching
    document.getElementById('tab-tag-list')?.addEventListener('click', () => switchTab('tag-list'));
    document.getElementById('tab-categories')?.addEventListener('click', () => switchTab('categories'));
    document.getElementById('tab-assignments')?.addEventListener('click', () => switchTab('assignments'));
    document.getElementById('tab-dependencies')?.addEventListener('click', () => switchTab('dependencies'));
    
    // Initial data load
    fetchAllTags();
    fetchAllCategories();
    fetchInstances();
    fetchTagDependencies();
    fetchTagConflicts();
    fetchUsageStats();
    
    // Start polling
    startTagManagerPolling();
}

function switchTab(tabName) {
    // Hide all tab contents
    document.querySelectorAll('.tag-tab-content').forEach(tab => tab.style.display = 'none');
    
    // Remove active class from all tabs
    document.querySelectorAll('.tag-tab').forEach(tab => tab.classList.remove('active'));
    
    // Show selected tab
    document.getElementById(`${tabName}-tab-content`).style.display = 'block';
    document.getElementById(`tab-${tabName}`).classList.add('active');
}

// ==================== Data Fetching ====================

async function fetchAllTags() {
    try {
        const response = await fetch('/api/tags/all');
        if (!response.ok) throw new Error('Failed to fetch tags');
        
        allTags = await response.json();
        console.log(`[Tag Manager] Fetched ${allTags.length} tags`);
        
        renderTagsTable();
    } catch (error) {
        console.error('[Tag Manager] Error fetching tags:', error);
        showError('Failed to load tags');
    }
}

async function fetchAllCategories() {
    try {
        const response = await fetch('/api/tags/categories');
        if (!response.ok) throw new Error('Failed to fetch categories');
        
        allCategories = await response.json();
        console.log(`[Tag Manager] Fetched ${allCategories.length} categories`);
        
        renderCategoriesTable();
        populateCategoryDropdowns();
    } catch (error) {
        console.error('[Tag Manager] Error fetching categories:', error);
        showError('Failed to load categories');
    }
}

async function fetchInstances() {
    try {
        const response = await fetch('/api/dashboard/instances');
        if (!response.ok) throw new Error('Failed to fetch instances');
        
        const data = await response.json();
        allInstances = data.instances || [];
        console.log(`[Tag Manager] Fetched ${allInstances.length} instances`);
        
        renderInstancesForAssignment();
    } catch (error) {
        console.error('[Tag Manager] Error fetching instances:', error);
    }
}

async function fetchTagDependencies() {
    try {
        const response = await fetch('/api/tags/dependencies');
        if (!response.ok) throw new Error('Failed to fetch dependencies');
        
        const dependencies = await response.json();
        renderDependenciesTable(dependencies);
    } catch (error) {
        console.error('[Tag Manager] Error fetching dependencies:', error);
    }
}

async function fetchTagConflicts() {
    try {
        const response = await fetch('/api/tags/conflicts');
        if (!response.ok) throw new Error('Failed to fetch conflicts');
        
        const conflicts = await response.json();
        renderConflictsTable(conflicts);
    } catch (error) {
        console.error('[Tag Manager] Error fetching conflicts:', error);
    }
}

async function fetchUsageStats() {
    try {
        const response = await fetch('/api/tags/usage-stats');
        if (!response.ok) throw new Error('Failed to fetch usage stats');
        
        const stats = await response.json();
        renderUsageStats(stats);
    } catch (error) {
        console.error('[Tag Manager] Error fetching usage stats:', error);
    }
}

// ==================== Rendering ====================

function renderTagsTable() {
    const tbody = document.getElementById('tags-table-body');
    if (!tbody) return;
    
    if (allTags.length === 0) {
        tbody.innerHTML = '<tr><td colspan="7">No tags found</td></tr>';
        return;
    }
    
    tbody.innerHTML = allTags.map(tag => `
        <tr draggable="true" data-tag-id="${tag.tag_id}" ondragstart="handleTagDragStart(event)">
            <td>
                ${tag.icon ? `<span class="tag-icon">${tag.icon}</span>` : ''}
                <span class="tag-badge" style="background-color: ${tag.color || '#6c757d'}">${tag.display_name}</span>
            </td>
            <td>${tag.category_display_name || tag.category_name}</td>
            <td>${tag.description || '-'}</td>
            <td>${tag.is_system_tag ? '<span class="badge badge-info">System</span>' : '<span class="badge badge-secondary">User</span>'}</td>
            <td class="usage-count" data-tag-id="${tag.tag_id}">-</td>
            <td>
                <button class="btn-small" onclick="editTag(${tag.tag_id})">Edit</button>
                <button class="btn-small btn-danger" onclick="deleteTag(${tag.tag_id}, '${tag.display_name}')">Delete</button>
            </td>
        </tr>
    `).join('');
}

function renderCategoriesTable() {
    const tbody = document.getElementById('categories-table-body');
    if (!tbody) return;
    
    if (allCategories.length === 0) {
        tbody.innerHTML = '<tr><td colspan="6">No categories found</td></tr>';
        return;
    }
    
    tbody.innerHTML = allCategories.map(cat => `
        <tr>
            <td>${cat.display_name}</td>
            <td>${cat.category_name}</td>
            <td>${cat.description || '-'}</td>
            <td>${cat.is_multiselect ? 'Yes' : 'No'}</td>
            <td>${cat.display_order}</td>
            <td>
                <button class="btn-small" onclick="editCategory(${cat.category_id})">Edit</button>
                <button class="btn-small btn-danger" onclick="deleteCategory(${cat.category_id}, '${cat.display_name}')">Delete</button>
            </td>
        </tr>
    `).join('');
}

function renderInstancesForAssignment() {
    const container = document.getElementById('instance-assignment-list');
    if (!container) return;
    
    container.innerHTML = allInstances.map(inst => `
        <div class="instance-card" data-instance-id="${inst.instance_id}" 
             ondrop="handleTagDrop(event)" ondragover="handleDragOver(event)">
            <h4>${inst.instance_name}</h4>
            <div class="instance-tags" id="tags-for-${inst.instance_id}">
                Loading tags...
            </div>
        </div>
    `).join('');
    
    // Fetch tags for each instance
    allInstances.forEach(inst => fetchInstanceTags(inst.instance_id));
}

async function fetchInstanceTags(instanceId) {
    try {
        const response = await fetch(`/api/tags/instances/${instanceId}`);
        if (!response.ok) throw new Error('Failed to fetch instance tags');
        
        const tags = await response.json();
        const container = document.getElementById(`tags-for-${instanceId}`);
        
        if (tags.length === 0) {
            container.innerHTML = '<span class="no-tags">No tags assigned</span>';
        } else {
            container.innerHTML = tags.map(tag => `
                <span class="tag-badge" style="background-color: ${tag.color || '#6c757d'}" 
                      data-tag-id="${tag.tag_id}">
                    ${tag.icon || ''} ${tag.display_name}
                    <button class="tag-remove-btn" onclick="removeTagFromInstance('${instanceId}', ${tag.tag_id})">×</button>
                </span>
            `).join('');
        }
    } catch (error) {
        console.error(`[Tag Manager] Error fetching tags for ${instanceId}:`, error);
    }
}

function renderDependenciesTable(dependencies) {
    const tbody = document.getElementById('dependencies-table-body');
    if (!tbody) return;
    
    if (dependencies.length === 0) {
        tbody.innerHTML = '<tr><td colspan="4">No dependencies defined</td></tr>';
        return;
    }
    
    tbody.innerHTML = dependencies.map(dep => `
        <tr>
            <td>${dep.dependent_tag_name}</td>
            <td>${dep.required_tag_name}</td>
            <td><span class="badge badge-${dep.dependency_type === 'required' ? 'danger' : 'warning'}">${dep.dependency_type}</span></td>
            <td>${dep.description || '-'}</td>
        </tr>
    `).join('');
}

function renderConflictsTable(conflicts) {
    const tbody = document.getElementById('conflicts-table-body');
    if (!tbody) return;
    
    if (conflicts.length === 0) {
        tbody.innerHTML = '<tr><td colspan="4">No conflicts defined</td></tr>';
        return;
    }
    
    tbody.innerHTML = conflicts.map(conf => `
        <tr>
            <td>${conf.tag_a_name}</td>
            <td>${conf.tag_b_name}</td>
            <td><span class="badge badge-${conf.conflict_severity === 'error' ? 'danger' : 'warning'}">${conf.conflict_severity}</span></td>
            <td>${conf.description || '-'}</td>
        </tr>
    `).join('');
}

function renderUsageStats(stats) {
    // Update usage counts in tags table
    stats.forEach(stat => {
        const cell = document.querySelector(`.usage-count[data-tag-id="${stat.tag_id}"]`);
        if (cell) {
            cell.textContent = stat.usage_count;
        }
    });
}

function populateCategoryDropdowns() {
    const selects = document.querySelectorAll('.category-selector');
    selects.forEach(select => {
        select.innerHTML = '<option value="">Select Category</option>' +
            allCategories.map(cat => `<option value="${cat.category_id}">${cat.display_name}</option>`).join('');
    });
}

// ==================== Drag and Drop ====================

function handleTagDragStart(event) {
    const tagId = event.currentTarget.getAttribute('data-tag-id');
    event.dataTransfer.setData('tag-id', tagId);
    event.dataTransfer.effectAllowed = 'copy';
}

function handleDragOver(event) {
    event.preventDefault();
    event.dataTransfer.dropEffect = 'copy';
    event.currentTarget.classList.add('drag-over');
}

async function handleTagDrop(event) {
    event.preventDefault();
    event.currentTarget.classList.remove('drag-over');
    
    const tagId = parseInt(event.dataTransfer.getData('tag-id'));
    const instanceId = event.currentTarget.getAttribute('data-instance-id');
    
    if (!tagId || !instanceId) return;
    
    await assignTagToInstance(instanceId, tagId);
}

// ==================== CRUD Operations ====================

async function assignTagToInstance(instanceId, tagId) {
    try {
        const response = await fetch('/api/tags/assign', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                instance_id: instanceId,
                tag_id: tagId,
                applied_by: 'web_ui'
            })
        });
        
        if (!response.ok) throw new Error('Failed to assign tag');
        
        // Refresh instance tags
        await fetchInstanceTags(instanceId);
        showSuccess('Tag assigned successfully');
    } catch (error) {
        console.error('[Tag Manager] Error assigning tag:', error);
        showError('Failed to assign tag');
    }
}

async function removeTagFromInstance(instanceId, tagId) {
    if (!confirm('Remove this tag from the instance?')) return;
    
    try {
        const response = await fetch(`/api/tags/assign/${instanceId}/${tagId}?removed_by=web_ui`, {
            method: 'DELETE'
        });
        
        if (!response.ok) throw new Error('Failed to remove tag');
        
        await fetchInstanceTags(instanceId);
        showSuccess('Tag removed successfully');
    } catch (error) {
        console.error('[Tag Manager] Error removing tag:', error);
        showError('Failed to remove tag');
    }
}

function showCreateTagModal() {
    document.getElementById('tag-modal-title').textContent = 'Create New Tag';
    document.getElementById('tag-form').reset();
    document.getElementById('tag-modal').style.display = 'block';
}

function showCreateCategoryModal() {
    document.getElementById('category-modal-title').textContent = 'Create New Category';
    document.getElementById('category-form').reset();
    document.getElementById('category-modal').style.display = 'block';
}

function closeTagModal() {
    document.getElementById('tag-modal').style.display = 'none';
}

function closeCategoryModal() {
    document.getElementById('category-modal').style.display = 'none';
}

async function saveTag() {
    const tagId = document.getElementById('tag-id-hidden').value;
    const formData = {
        category_id: parseInt(document.getElementById('tag-category-select').value),
        tag_name: document.getElementById('tag-name-input').value,
        display_name: document.getElementById('tag-display-name-input').value,
        description: document.getElementById('tag-description-input').value,
        icon: document.getElementById('tag-icon-input').value,
        color: document.getElementById('tag-color-input').value
    };
    
    try {
        const url = tagId ? `/api/tags/${tagId}` : '/api/tags/create';
        const method = tagId ? 'PUT' : 'POST';
        
        const response = await fetch(url, {
            method: method,
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(formData)
        });
        
        if (!response.ok) throw new Error('Failed to save tag');
        
        closeTagModal();
        await fetchAllTags();
        showSuccess(tagId ? 'Tag updated' : 'Tag created');
    } catch (error) {
        console.error('[Tag Manager] Error saving tag:', error);
        showError('Failed to save tag');
    }
}

async function saveCategory() {
    const categoryId = document.getElementById('category-id-hidden').value;
    const formData = {
        category_name: document.getElementById('category-name-input').value,
        display_name: document.getElementById('category-display-name-input').value,
        description: document.getElementById('category-description-input').value,
        is_multiselect: document.getElementById('category-multiselect').checked,
        is_required: document.getElementById('category-required').checked,
        display_order: parseInt(document.getElementById('category-order-input').value || '999'),
        icon: document.getElementById('category-icon-input').value,
        color: document.getElementById('category-color-input').value
    };
    
    try {
        const url = categoryId ? `/api/tags/categories/${categoryId}` : '/api/tags/categories';
        const method = categoryId ? 'PUT' : 'POST';
        
        const response = await fetch(url, {
            method: method,
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(formData)
        });
        
        if (!response.ok) throw new Error('Failed to save category');
        
        closeCategoryModal();
        await fetchAllCategories();
        showSuccess(categoryId ? 'Category updated' : 'Category created');
    } catch (error) {
        console.error('[Tag Manager] Error saving category:', error);
        showError('Failed to save category');
    }
}

async function deleteTag(tagId, tagName) {
    if (!confirm(`Delete tag "${tagName}"? (Will be deprecated if in use)`)) return;
    
    try {
        const response = await fetch(`/api/tags/${tagId}`, {method: 'DELETE'});
        if (!response.ok) throw new Error('Failed to delete tag');
        
        const result = await response.json();
        await fetchAllTags();
        showSuccess(result.message);
    } catch (error) {
        console.error('[Tag Manager] Error deleting tag:', error);
        showError('Failed to delete tag');
    }
}

async function deleteCategory(categoryId, categoryName) {
    if (!confirm(`Delete category "${categoryName}"?`)) return;
    
    try {
        const response = await fetch(`/api/tags/categories/${categoryId}`, {method: 'DELETE'});
        if (!response.ok) throw new Error('Failed to delete category');
        
        await fetchAllCategories();
        showSuccess('Category deleted');
    } catch (error) {
        console.error('[Tag Manager] Error deleting category:', error);
        showError(error.message);
    }
}

function editTag(tagId) {
    const tag = allTags.find(t => t.tag_id === tagId);
    if (!tag) return;
    
    document.getElementById('tag-modal-title').textContent = 'Edit Tag';
    document.getElementById('tag-id-hidden').value = tag.tag_id;
    document.getElementById('tag-category-select').value = tag.category_id;
    document.getElementById('tag-name-input').value = tag.tag_name;
    document.getElementById('tag-display-name-input').value = tag.display_name;
    document.getElementById('tag-description-input').value = tag.description || '';
    document.getElementById('tag-icon-input').value = tag.icon || '';
    document.getElementById('tag-color-input').value = tag.color || '#6c757d';
    
    document.getElementById('tag-modal').style.display = 'block';
}

function editCategory(categoryId) {
    const category = allCategories.find(c => c.category_id === categoryId);
    if (!category) return;
    
    document.getElementById('category-modal-title').textContent = 'Edit Category';
    document.getElementById('category-id-hidden').value = category.category_id;
    document.getElementById('category-name-input').value = category.category_name;
    document.getElementById('category-display-name-input').value = category.display_name;
    document.getElementById('category-description-input').value = category.description || '';
    document.getElementById('category-multiselect').checked = category.is_multiselect;
    document.getElementById('category-required').checked = category.is_required;
    document.getElementById('category-order-input').value = category.display_order;
    document.getElementById('category-icon-input').value = category.icon || '';
    document.getElementById('category-color-input').value = category.color || '';
    
    document.getElementById('category-modal').style.display = 'block';
}

// ==================== Polling ====================

function startTagManagerPolling() {
    if (tagManagerPollInterval) clearInterval(tagManagerPollInterval);
    
    tagManagerPollInterval = setInterval(() => {
        fetchUsageStats();
    }, TAG_MANAGER_POLL_INTERVAL);
}

function stopTagManagerPolling() {
    if (tagManagerPollInterval) {
        clearInterval(tagManagerPollInterval);
        tagManagerPollInterval = null;
    }
}

// ==================== Helper Functions ====================

function showSuccess(message) {
    // Placeholder for toast/notification
    console.log('[Tag Manager] SUCCESS:', message);
    alert(message);
}

function showError(message) {
    console.error('[Tag Manager] ERROR:', message);
    alert('Error: ' + message);
}

// ==================== Module Export ====================

window.tagManagerModule = {
    init: loadTagManager,
    refresh: () => {
        fetchAllTags();
        fetchAllCategories();
        fetchInstances();
    },
    cleanup: stopTagManagerPolling
};
