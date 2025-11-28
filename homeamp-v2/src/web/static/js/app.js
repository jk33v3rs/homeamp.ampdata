// HomeAMP V2.0 - Main Application

// Current View
let currentView = "dashboard";

// Initialize App
document.addEventListener("DOMContentLoaded", function () {
  initializeApp();
});

function initializeApp() {
  // Setup Navigation
  setupNavigation();

  // Setup Theme Toggle
  setupThemeToggle();

  // Setup Global Refresh
  document
    .getElementById("global-refresh")
    .addEventListener("click", refreshCurrentView);

  // Load Initial View
  loadView("dashboard");

  // Check for pending approvals
  updateApprovalBadge();
  setInterval(updateApprovalBadge, 60000); // Check every minute
}

// Navigation
function setupNavigation() {
  document.querySelectorAll("[data-view]").forEach((link) => {
    link.addEventListener("click", function (e) {
      e.preventDefault();
      const view = this.getAttribute("data-view");
      loadView(view);
    });
  });
}

function loadView(viewName) {
  // Hide all views
  document.querySelectorAll(".view-container").forEach((view) => {
    view.classList.add("d-none");
  });

  // Show selected view
  const view = document.getElementById(`${viewName}-view`);
  if (view) {
    view.classList.remove("d-none");
    currentView = viewName;

    // Update breadcrumb
    updateBreadcrumb(viewName);

    // Update active nav link
    updateActiveNav(viewName);

    // Load view data
    loadViewData(viewName);
  }
}

function updateBreadcrumb(viewName) {
  const breadcrumb = document.getElementById("breadcrumb");
  const titles = {
    dashboard: "Dashboard",
    instances: "Instances",
    plugins: "Plugin Catalog",
    deployments: "Deployment Queue",
    updates: "Available Updates",
    approvals: "Approval Workflow",
    audit: "Audit Log",
    groups: "Instance Groups",
    datapacks: "Datapacks",
    tags: "Tag Management",
    settings: "Settings",
    "config-browser": "Config Browser",
    "config-editor": "Config Editor",
    variances: "Variance Detection",
    hierarchy: "Config Hierarchy",
  };

  breadcrumb.innerHTML = `<li class="breadcrumb-item active">${
    titles[viewName] || viewName
  }</li>`;
}

function updateActiveNav(viewName) {
  document.querySelectorAll(".nav-link").forEach((link) => {
    link.classList.remove("active");
    if (link.getAttribute("data-view") === viewName) {
      link.classList.add("active");
    }
  });
}

function loadViewData(viewName) {
  switch (viewName) {
    case "dashboard":
      loadDashboard();
      break;
    case "instances":
      loadInstances();
      break;
    case "plugins":
      loadPlugins();
      break;
    case "deployments":
      loadDeployments();
      break;
    case "updates":
      loadUpdates();
      break;
    case "approvals":
      loadApprovals();
      break;
    case "audit":
      loadAuditLog();
      break;
    case "groups":
      loadGroups();
      break;
    case "datapacks":
      loadDatapacks();
      break;
    case "tags":
      loadTags();
      break;
  }
}

function refreshCurrentView() {
  const btn = document.getElementById("global-refresh");
  const icon = btn.querySelector("i");
  icon.classList.add("rotate");

  loadViewData(currentView);

  setTimeout(() => {
    icon.classList.remove("rotate");
  }, 1000);
}

// Theme Toggle
function setupThemeToggle() {
  const toggle = document.getElementById("theme-toggle");
  const icon = document.getElementById("theme-icon");

  toggle.addEventListener("click", function () {
    const html = document.documentElement;
    const currentTheme = html.getAttribute("data-bs-theme");
    const newTheme = currentTheme === "dark" ? "light" : "dark";

    html.setAttribute("data-bs-theme", newTheme);
    localStorage.setItem("theme", newTheme);

    // Update icon
    icon.setAttribute("data-feather", newTheme === "dark" ? "sun" : "moon");
    feather.replace();
  });
}

function initTheme() {
  const savedTheme = localStorage.getItem("theme") || "light";
  document.documentElement.setAttribute("data-bs-theme", savedTheme);

  const icon = document.getElementById("theme-icon");
  if (icon) {
    icon.setAttribute("data-feather", savedTheme === "dark" ? "sun" : "moon");
  }
}

// Approval Badge
async function updateApprovalBadge() {
  try {
    const response = await API.getPendingApprovals();
    const count = response.data?.length || 0;
    const badge = document.getElementById("approval-count");

    if (count > 0) {
      badge.textContent = count;
      badge.style.display = "inline";
    } else {
      badge.style.display = "none";
    }
  } catch (error) {
    console.error("Failed to update approval badge:", error);
  }
}

// Add CSS for rotate animation
const style = document.createElement("style");
style.textContent = `
    .rotate {
        animation: rotate 1s linear;
    }
    
    @keyframes rotate {
        from {
            transform: rotate(0deg);
        }
        to {
            transform: rotate(360deg);
        }
    }
`;
document.head.appendChild(style);
