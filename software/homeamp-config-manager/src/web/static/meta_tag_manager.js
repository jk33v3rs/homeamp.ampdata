// Meta Tag Manager JavaScript
// Manage meta tags and instance assignments

const API_BASE = '/api';
let allTags = [];
let currentTagId = null;

// Load tags
async function loadTags() {
    try {
        const response = await fetch(`${API_BASE}/meta-tags`);
        const data = await response.json();
        
        allTags = data.tags;
        renderTagList();
    } catch (error) {
        console.error('Error loading tags:', error);
    }
}

// Render tag list
function renderTagList() {
    const container = document.getElementById('tag-list');
    container.innerHTML = '';
    
    if (allTags.length === 0) {
        container.innerHTML = '<p style="color: #718096; text-align: center;">No tags created yet</p>';
        return;
    }
    
    allTags.forEach(tag => {
        const div = document.createElement('div');
        div.className = 'tag-item';
        div.onclick = () => selectTag(tag.tag_id);
        
        div.innerHTML = `
            <div class="tag-name">${tag.tag_name}</div>
            <div class="tag-description">${tag.tag_description || 'No description'}</div>
        `;
        
        container.appendChild(div);
    });
}

// Select tag
async function selectTag(tagId) {
    currentTagId = tagId;
    
    // Update UI
    document.querySelectorAll('.tag-item').forEach(item => item.classList.remove('active'));
    event.currentTarget.classList.add('active');
    
    // Show details panel
    document.getElementById('empty-state').style.display = 'none';
    document.getElementById('tag-details').style.display = 'block';
    
    // Load tag details
    const tag = allTags.find(t => t.tag_id === tagId);
    document.getElementById('detail-tag-name').textContent = tag.tag_name;
    document.getElementById('detail-tag-description').textContent = tag.tag_description || 'No description';
    
    // Load instances
    await loadTagInstances(tagId);
    await loadAvailableInstances();
}

// Load tag instances
async function loadTagInstances(tagId) {
    try {
        const response = await fetch(`${API_BASE}/tags/${allTags.find(t => t.tag_id === tagId).tag_name}/instances`);
        const data = await response.json();
        
        const container = document.getElementById('instance-grid');
        const count = document.getElementById('instance-count');
        
        count.textContent = data.instances.length;
        
        if (data.instances.length === 0) {
            container.innerHTML = '<p style="color: #718096; grid-column: 1/-1; text-align: center;">No instances assigned</p>';
            return;
        }
        
        container.innerHTML = '';
        data.instances.forEach(instance => {
            const div = document.createElement('div');
            div.className = 'instance-badge';
            div.innerHTML = `
                <span>${instance.instance_name}</span>
                <button class="remove-btn" onclick="removeInstance(${instance.instance_id})">✕</button>
            `;
            container.appendChild(div);
        });
    } catch (error) {
        console.error('Error loading tag instances:', error);
    }
}

// Load available instances
async function loadAvailableInstances() {
    try {
        const response = await fetch(`${API_BASE}/instances`);
        const data = await response.json();
        
        const select = document.getElementById('assign-instance-select');
        select.innerHTML = '<option value="">Select instance...</option>';
        
        data.instances.forEach(instance => {
            const option = document.createElement('option');
            option.value = instance.instance_id;
            option.textContent = instance.instance_name;
            select.appendChild(option);
        });
    } catch (error) {
        console.error('Error loading instances:', error);
    }
}

// Create tag
async function createTag() {
    const name = document.getElementById('new-tag-name').value;
    const description = document.getElementById('new-tag-description').value;
    
    if (!name) {
        alert('Please enter a tag name');
        return;
    }
    
    try {
        const response = await fetch(`${API_BASE}/meta-tags`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                tag_name: name,
                tag_description: description
            })
        });
        
        if (response.ok) {
            document.getElementById('new-tag-name').value = '';
            document.getElementById('new-tag-description').value = '';
            await loadTags();
        }
    } catch (error) {
        console.error('Error creating tag:', error);
        alert('Failed to create tag');
    }
}

// Delete tag
async function deleteTag() {
    if (!confirm('Are you sure you want to delete this tag?')) return;
    
    try {
        const response = await fetch(`${API_BASE}/meta-tags/${currentTagId}`, {
            method: 'DELETE'
        });
        
        if (response.ok) {
            currentTagId = null;
            document.getElementById('empty-state').style.display = 'block';
            document.getElementById('tag-details').style.display = 'none';
            await loadTags();
        }
    } catch (error) {
        console.error('Error deleting tag:', error);
        alert('Failed to delete tag');
    }
}

// Assign instance
async function assignInstance() {
    const instanceId = document.getElementById('assign-instance-select').value;
    
    if (!instanceId) {
        alert('Please select an instance');
        return;
    }
    
    try {
        const response = await fetch(`${API_BASE}/instances/${instanceId}/meta-tags`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({tag_id: currentTagId})
        });
        
        if (response.ok) {
            await loadTagInstances(currentTagId);
        }
    } catch (error) {
        console.error('Error assigning instance:', error);
        alert('Failed to assign instance');
    }
}

// Remove instance
async function removeInstance(instanceId) {
    try {
        const response = await fetch(`${API_BASE}/instances/${instanceId}/meta-tags/${currentTagId}`, {
            method: 'DELETE'
        });
        
        if (response.ok) {
            await loadTagInstances(currentTagId);
        }
    } catch (error) {
        console.error('Error removing instance:', error);
        alert('Failed to remove instance');
    }
}

// Initialize
loadTags();
