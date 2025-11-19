/**
 * Application Entry Point and View Management
 * Phase 2 implementation
 */

// ====================
// Application State
// ====================

const appState = {
    currentView: 'dashboard',
    previousView: null,
    viewHistory: [],
    breadcrumbs: ['Dashboard']
};

// View registry
const views = {
    'dashboard': {
        name: 'Dashboard',
        module: () => window.dashboardModule,
        container: '#dashboard-view'
    },
    'plugin-configurator': {
        name: 'Plugin Configurator',
        module: () => window.pluginConfiguratorModule,
        container: '#plugin-configurator-view'
    },
    'update-manager': {
        name: 'Update Manager',
        module: () => window.updateManagerModule,
        container: '#update-manager-view'
    },
    'variance-report': {
        name: 'Variance Report',
        module: () => window.varianceReportModule,
        container: '#variance-report-view'
    },
    'deployment-queue': {
        name: 'Deployment Queue',
        module: () => window.deploymentQueueModule,
        container: '#deployment-queue-view'
    },
    'instance-manager': {
        name: 'Instance Manager',
        module: () => window.instanceManagerModule,
        container: '#instance-manager-view'
    },
    'audit-log': {
        name: 'Audit Log',
        module: () => window.auditLogModule,
        container: '#audit-log-view'
    },
    'settings': {
        name: 'Settings',
        module: () => window.settingsModule,
        container: '#settings-view'
    }
};

// ====================
// View Navigation
// ====================

/**
 * Switch to a different view
 * @param {string} viewId - The view identifier
 * @param {object} params - Optional parameters for the view
 */
async function switchView(viewId, params = {}) {
    console.log(`Switching to view: ${viewId}`, params);

    // Validate view exists
    if (!views[viewId]) {
        console.error(`Unknown view: ${viewId}`);
        return;
    }

    // Store previous view
    appState.previousView = appState.currentView;
    appState.viewHistory.push(appState.currentView);

    // Cleanup current view
    await cleanupCurrentView();

    // Hide all view containers
    document.querySelectorAll('.view-container').forEach(container => {
        container.classList.remove('active');
        container.style.display = 'none';
    });

    // Show target view container
    const targetContainer = document.querySelector(views[viewId].container);
    if (targetContainer) {
        targetContainer.style.display = 'block';
        targetContainer.classList.add('active');
    }

    // Update navigation state
    updateNavigation(viewId);
    updateBreadcrumbs(viewId, params);

    // Initialize new view
    appState.currentView = viewId;
    await initializeView(viewId, params);
}

/**
 * Navigate back to previous view
 */
async function goBack() {
    if (appState.viewHistory.length > 0) {
        const previousView = appState.viewHistory.pop();
        await switchView(previousView);
    }
}

/**
 * Navigate to a specific view with breadcrumb context
 * @param {string} viewId - View identifier
 * @param {object} context - Breadcrumb context (e.g., server name, plugin name)
 */
async function navigateWithContext(viewId, context = {}) {
    await switchView(viewId, context);
}

// ====================
// View Lifecycle Management
// ====================

/**
 * Initialize a view and call its init function
 */
async function initializeView(viewId, params) {
    const view = views[viewId];
    if (!view) return;

    try {
        const module = view.module();
        if (module && typeof module.init === 'function') {
            console.log(`Initializing ${viewId} view`);
            await module.init(params);
        }
    } catch (error) {
        console.error(`Failed to initialize ${viewId}:`, error);
        showError(`Failed to load ${view.name}`);
    }
}

/**
 * Cleanup current view before switching
 */
async function cleanupCurrentView() {
    const currentViewId = appState.currentView;
    if (!currentViewId) return;

    const view = views[currentViewId];
    if (!view) return;

    try {
        const module = view.module();
        if (module && typeof module.cleanup === 'function') {
            console.log(`Cleaning up ${currentViewId} view`);
            await module.cleanup();
        }

        // Stop polling if dashboard
        if (currentViewId === 'dashboard' && module?.stopPolling) {
            module.stopPolling();
        }
    } catch (error) {
        console.error(`Failed to cleanup ${currentViewId}:`, error);
    }
}

// ====================
// UI Updates
// ====================

/**
 * Update navigation bar active state
 */
function updateNavigation(viewId) {
    // Remove active class from all nav links
    document.querySelectorAll('.nav-link').forEach(link => {
        link.classList.remove('active');
    });

    // Add active class to current view
    const activeLink = document.querySelector(`.nav-link[data-view="${viewId}"]`);
    if (activeLink) {
        activeLink.classList.add('active');
    }
}

/**
 * Update breadcrumb navigation
 */
function updateBreadcrumbs(viewId, params) {
    const breadcrumbContainer = document.getElementById('breadcrumb-nav');
    if (!breadcrumbContainer) return;

    const view = views[viewId];
    if (!view) return;

    // Build breadcrumb trail
    let breadcrumbs = [view.name];

    // Add context-specific breadcrumbs
    if (params.serverName) {
        breadcrumbs.push(params.serverName);
    }
    if (params.instanceName) {
        breadcrumbs.push(params.instanceName);
    }
    if (params.pluginName) {
        breadcrumbs.push(params.pluginName);
    }

    appState.breadcrumbs = breadcrumbs;

    // Render breadcrumbs
    const html = breadcrumbs.map((crumb, index) => {
        if (index === breadcrumbs.length - 1) {
            return `<span class="breadcrumb-current">${escapeHtml(crumb)}</span>`;
        }
        return `<span class="breadcrumb-item">${escapeHtml(crumb)}</span>`;
    }).join(' <span class="breadcrumb-separator">›</span> ');

    breadcrumbContainer.innerHTML = html;
}

/**
 * Update page title
 */
function updatePageTitle(title) {
    document.title = `${title} - ArchiveSMP Config Manager`;
}

// ====================
// Event Handlers
// ====================

/**
 * Attach navigation link handlers
 */
function attachNavigationHandlers() {
    document.querySelectorAll('.nav-link').forEach(link => {
        link.addEventListener('click', async (e) => {
            e.preventDefault();
            const viewId = e.currentTarget.dataset.view;
            if (viewId) {
                await switchView(viewId);
            }
        });
    });

    // Back button
    const backBtn = document.getElementById('back-btn');
    if (backBtn) {
        backBtn.addEventListener('click', async (e) => {
            e.preventDefault();
            await goBack();
        });
    }

    // Refresh button (global)
    const refreshBtn = document.getElementById('global-refresh-btn');
    if (refreshBtn) {
        refreshBtn.addEventListener('click', async (e) => {
            e.preventDefault();
            await refreshCurrentView();
        });
    }
}

/**
 * Refresh the current view
 */
async function refreshCurrentView() {
    const currentViewId = appState.currentView;
    if (!currentViewId) return;

    const view = views[currentViewId];
    if (!view) return;

    try {
        const module = view.module();
        if (module && typeof module.refresh === 'function') {
            console.log(`Refreshing ${currentViewId} view`);
            await module.refresh();
        }
    } catch (error) {
        console.error(`Failed to refresh ${currentViewId}:`, error);
        showError(`Failed to refresh ${view.name}`);
    }
}

// ====================
// Deep Linking
// ====================

/**
 * Parse URL hash for deep linking
 */
function parseUrlHash() {
    const hash = window.location.hash.slice(1); // Remove #
    if (!hash) return { view: 'dashboard', params: {} };

    const parts = hash.split('/');
    const view = parts[0] || 'dashboard';
    const params = {};

    // Parse query string params
    if (parts.length > 1) {
        const queryString = parts.slice(1).join('/');
        const urlParams = new URLSearchParams(queryString);
        urlParams.forEach((value, key) => {
            params[key] = value;
        });
    }

    return { view, params };
}

/**
 * Update URL hash when view changes
 */
function updateUrlHash(viewId, params = {}) {
    let hash = `#${viewId}`;

    // Add params as query string
    const queryParams = new URLSearchParams(params);
    const queryString = queryParams.toString();
    if (queryString) {
        hash += `/${queryString}`;
    }

    window.location.hash = hash;
}

/**
 * Handle hash change events (browser back/forward)
 */
function handleHashChange() {
    const { view, params } = parseUrlHash();
    if (view !== appState.currentView) {
        switchView(view, params);
    }
}

// ====================
// Global Error Handling
// ====================

function showError(message) {
    console.error(message);
    // TODO: Implement toast notification system
    const errorContainer = document.getElementById('global-error');
    if (errorContainer) {
        errorContainer.textContent = message;
        errorContainer.style.display = 'block';
        setTimeout(() => {
            errorContainer.style.display = 'none';
        }, 5000);
    }
}

function showSuccess(message) {
    console.log(message);
    // TODO: Implement toast notification system
    const successContainer = document.getElementById('global-success');
    if (successContainer) {
        successContainer.textContent = message;
        successContainer.style.display = 'block';
        setTimeout(() => {
            successContainer.style.display = 'none';
        }, 3000);
    }
}

function showWarning(message) {
    console.warn(message);
    // TODO: Implement toast notification system
}

// ====================
// Utility Functions
// ====================

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// ====================
// Application Initialization
// ====================

/**
 * Initialize the application
 */
async function initApp() {
    console.log('Initializing ArchiveSMP Config Manager');

    // Attach global event handlers
    attachNavigationHandlers();

    // Handle browser back/forward
    window.addEventListener('hashchange', handleHashChange);

    // Parse URL hash for initial view
    const { view, params } = parseUrlHash();

    // Load initial view
    await switchView(view, params);

    console.log('Application initialized');
}

// ====================
// Start Application
// ====================

// Wait for DOM ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initApp);
} else {
    initApp();
}

// Export for debugging
window.appModule = {
    switchView,
    goBack,
    navigateWithContext,
    refreshCurrentView,
    state: appState
};
