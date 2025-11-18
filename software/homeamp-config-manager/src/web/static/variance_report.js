// Variance Report JavaScript
// Display and filter config variance data

const API_BASE = '/api';
let allVariance = [];
let currentFilter = '';

// Load variance data
async function loadVariance() {
    try {
        const response = await fetch(`${API_BASE}/config/variance`);
        const data = await response.json();
        
        allVariance = data.variance;
        
        updateStats();
        renderVariance();
    } catch (error) {
        console.error('Error loading variance:', error);
        showError('Failed to load variance report');
    }
}

// Update statistics
function updateStats() {
    const counts = {
        NONE: 0,
        VARIABLE: 0,
        META_TAG: 0,
        INSTANCE: 0,
        DRIFT: 0
    };
    
    allVariance.forEach(v => {
        const classification = v.variance_classification;
        if (counts.hasOwnProperty(classification)) {
            counts[classification]++;
        }
    });
    
    document.getElementById('count-NONE').textContent = counts.NONE;
    document.getElementById('count-VARIABLE').textContent = counts.VARIABLE;
    document.getElementById('count-META_TAG').textContent = counts.META_TAG;
    document.getElementById('count-INSTANCE').textContent = counts.INSTANCE;
    document.getElementById('count-DRIFT').textContent = counts.DRIFT;
}

// Filter by classification
function filterByClassification(classification) {
    currentFilter = classification;
    
    // Update active tab
    document.querySelectorAll('.tab').forEach(tab => {
        tab.classList.remove('active');
        if (tab.dataset.classification === classification) {
            tab.classList.add('active');
        }
    });
    
    renderVariance();
}

// Render variance cards
function renderVariance() {
    const grid = document.getElementById('variance-grid');
    grid.innerHTML = '';
    
    const filtered = currentFilter
        ? allVariance.filter(v => v.variance_classification === currentFilter)
        : allVariance;
    
    if (filtered.length === 0) {
        grid.innerHTML = `
            <div style="text-align: center; padding: 40px; color: #718096;">
                No variance found for this filter
            </div>
        `;
        return;
    }
    
    filtered.forEach(variance => {
        const card = createVarianceCard(variance);
        grid.appendChild(card);
    });
}

// Create variance card
function createVarianceCard(variance) {
    const div = document.createElement('div');
    div.className = `variance-card ${variance.variance_classification}`;
    
    div.innerHTML = `
        <div class="variance-header">
            <h3>${variance.plugin_id} - ${variance.config_file}.${variance.config_key}</h3>
            <span class="classification-badge badge-${variance.variance_classification}">
                ${variance.variance_classification}
            </span>
        </div>
        
        <div class="variance-details">
            <div class="detail-row">
                <span class="label">Unique Values:</span>
                <span class="value">${variance.unique_values_count}</span>
            </div>
            <div class="detail-row">
                <span class="label">Instances Affected:</span>
                <span class="value">${variance.instance_count}</span>
            </div>
        </div>
        
        <div class="variance-values">
            <strong style="font-size: 0.9em; color: #2d3748; display: block; margin-bottom: 10px;">
                Values by Instance:
            </strong>
            ${renderValueList(variance)}
        </div>
    `;
    
    return div;
}

// Render value list
function renderValueList(variance) {
    // This would be populated from actual variance details
    // For now, showing placeholder
    return `
        <div class="value-item">
            <span class="instance-label">Multiple instances</span>
            See full details for value breakdown
        </div>
    `;
}

// Show error
function showError(message) {
    const grid = document.getElementById('variance-grid');
    grid.innerHTML = `
        <div style="text-align: center; padding: 40px; color: #ef4444;">
            ${message}
        </div>
    `;
}

// Initialize
loadVariance();
