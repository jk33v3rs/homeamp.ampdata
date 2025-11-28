// HomeAMP V2.0 - Dashboard Component

let pluginChart = null;

async function loadDashboard() {
  await Promise.all([
    loadDashboardStats(),
    loadNetworkStatus(),
    loadRecentActivity(),
    loadPluginChart(),
    loadApprovalQueue(),
  ]);
}

async function loadDashboardStats() {
  try {
    const response = await API.getDashboardSummary();
    const stats = response.data;

    // Total Instances
    document.getElementById("stat-instances").textContent =
      stats.total_instances || 0;
    document.getElementById("stat-instances-detail").textContent = `${
      stats.active_instances || 0
    } active, ${stats.production_instances || 0} production`;

    // Active Plugins
    document.getElementById("stat-plugins").textContent =
      stats.total_plugins || 0;
    document.getElementById("stat-plugins-detail").textContent = `${
      stats.plugins_with_updates || 0
    } with updates`;

    // Updates Available
    document.getElementById("stat-updates").textContent =
      stats.available_updates || 0;
    document.getElementById("stat-updates-detail").textContent = `${
      stats.pending_deployments || 0
    } pending deployments`;

    // Config Variances
    document.getElementById("stat-variances").textContent =
      stats.config_variances || 0;
    document.getElementById("stat-variances-detail").textContent = `${
      stats.unresolved_variances || 0
    } unresolved`;
  } catch (error) {
    console.error("Failed to load dashboard stats:", error);
  }
}

async function loadNetworkStatus() {
  const container = document.getElementById("network-status-container");
  setLoading("network-status-container");

  try {
    const response = await API.getNetworkStatus();
    const servers = response.data?.servers || [];

    if (servers.length === 0) {
      container.innerHTML = '<p class="text-muted">No servers found</p>';
      return;
    }

    let html = "";
    for (const server of servers) {
      html += `
                <div class="server-group mb-3">
                    <div class="server-group-title">${server.server_name}</div>
                    <div class="card server-card ${
                      server.online ? "" : "offline"
                    }">
                        <div class="card-body">
                            <div class="d-flex justify-content-between align-items-center mb-2">
                                <h6 class="mb-0">${server.server_host}</h6>
                                <span class="badge ${
                                  server.online ? "bg-success" : "bg-danger"
                                }">
                                    ${server.online ? "Online" : "Offline"}
                                </span>
                            </div>
                            <small class="text-muted">
                                ${server.instance_count} instances • 
                                ${server.production_count} production
                            </small>
            `;

      if (server.instances && server.instances.length > 0) {
        html += '<div class="mt-3">';
        server.instances.forEach((instance) => {
          html += `
                        <div class="instance-status">
                            <div>
                                <span class="instance-status-indicator ${
                                  instance.is_active ? "online" : "offline"
                                }"></span>
                                <span>${instance.instance_name}</span>
                                ${
                                  instance.is_production
                                    ? '<span class="badge bg-danger badge-sm ms-2">PROD</span>'
                                    : ""
                                }
                            </div>
                            <small class="text-muted">${instance.platform} ${
            instance.version
          }</small>
                        </div>
                    `;
        });
        html += "</div>";
      }

      html += `
                        </div>
                    </div>
                </div>
            `;
    }

    container.innerHTML = html;
  } catch (error) {
    container.innerHTML =
      '<p class="text-danger">Failed to load network status</p>';
    console.error("Failed to load network status:", error);
  }
}

async function loadRecentActivity() {
  const container = document.getElementById("recent-activity-container");
  setLoading("recent-activity-container");

  try {
    const response = await API.getRecentActivity();
    const activities = response.data?.activities || [];

    if (activities.length === 0) {
      container.innerHTML = '<p class="text-muted">No recent activity</p>';
      return;
    }

    let html = '<div class="timeline">';
    activities.forEach((activity) => {
      const iconClass =
        {
          deployment: "deploy",
          update: "update",
          config: "config",
          error: "error",
        }[activity.type] || "config";

      html += `
                <div class="activity-item d-flex align-items-start">
                    <div class="activity-icon ${iconClass}">
                        <i data-feather="${getActivityIcon(
                          activity.type
                        )}" class="icon-sm"></i>
                    </div>
                    <div class="flex-grow-1">
                        <div>${activity.message}</div>
                        <div class="activity-time">${formatDate(
                          activity.timestamp
                        )}</div>
                    </div>
                </div>
            `;
    });
    html += "</div>";

    container.innerHTML = html;
    feather.replace();
  } catch (error) {
    container.innerHTML = '<p class="text-danger">Failed to load activity</p>';
    console.error("Failed to load recent activity:", error);
  }
}

async function loadPluginChart() {
  try {
    const response = await API.getPluginSummary();
    const data = response.data;

    const ctx = document.getElementById("plugin-chart").getContext("2d");

    if (pluginChart) {
      pluginChart.destroy();
    }

    pluginChart = new Chart(ctx, {
      type: "doughnut",
      data: {
        labels: data.platforms?.map((p) => p.platform) || [],
        datasets: [
          {
            data: data.platforms?.map((p) => p.count) || [],
            backgroundColor: [
              "#0d6efd",
              "#198754",
              "#ffc107",
              "#dc3545",
              "#0dcaf0",
              "#6c757d",
            ],
          },
        ],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: {
            position: "bottom",
          },
          title: {
            display: false,
          },
        },
      },
    });
  } catch (error) {
    console.error("Failed to load plugin chart:", error);
  }
}

async function loadApprovalQueue() {
  const container = document.getElementById("approval-queue-container");
  setLoading("approval-queue-container");

  try {
    const response = await API.getApprovalQueue();
    const approvals = response.data?.approvals || [];

    if (approvals.length === 0) {
      container.innerHTML = '<p class="text-muted">No pending approvals</p>';
      return;
    }

    let html = "";
    approvals.slice(0, 5).forEach((approval) => {
      const progress =
        (approval.approved_count / approval.required_approvals) * 100;
      html += `
                <div class="approval-item">
                    <div class="d-flex justify-content-between align-items-start mb-2">
                        <div>
                            <strong>${approval.title}</strong>
                            <br>
                            <small class="text-muted">${approval.requester}</small>
                        </div>
                        <span class="badge bg-warning">${approval.approved_count}/${approval.required_approvals}</span>
                    </div>
                    <div class="progress vote-progress">
                        <div class="progress-bar" role="progressbar" 
                             style="width: ${progress}%" 
                             aria-valuenow="${progress}" 
                             aria-valuemin="0" 
                             aria-valuemax="100"></div>
                    </div>
                </div>
            `;
    });

    container.innerHTML = html;
  } catch (error) {
    container.innerHTML = '<p class="text-danger">Failed to load approvals</p>';
    console.error("Failed to load approval queue:", error);
  }
}

function getActivityIcon(type) {
  const icons = {
    deployment: "upload-cloud",
    update: "download-cloud",
    config: "settings",
    error: "alert-circle",
    scan: "refresh-cw",
    approval: "check-circle",
  };
  return icons[type] || "activity";
}
