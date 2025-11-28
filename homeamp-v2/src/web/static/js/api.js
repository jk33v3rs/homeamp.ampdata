// HomeAMP V2.0 - API Client

const API_BASE = "/api";

// API Client
const API = {
  // Dashboard
  getDashboardSummary: () => axios.get(`${API_BASE}/dashboard/summary`),
  getNetworkStatus: () => axios.get(`${API_BASE}/dashboard/network-status`),
  getPluginSummary: () => axios.get(`${API_BASE}/dashboard/plugin-summary`),
  getRecentActivity: () => axios.get(`${API_BASE}/dashboard/recent-activity`),
  getApprovalQueue: () => axios.get(`${API_BASE}/dashboard/approval-queue`),
  getVarianceSummary: () => axios.get(`${API_BASE}/dashboard/variance-summary`),

  // Instances
  getInstances: (params) => axios.get(`${API_BASE}/instances`, { params }),
  getInstance: (id) => axios.get(`${API_BASE}/instances/${id}`),
  getInstancePlugins: (id) => axios.get(`${API_BASE}/instances/${id}/plugins`),

  // Plugins
  getPlugins: (params) => axios.get(`${API_BASE}/plugins`, { params }),
  getPlugin: (id) => axios.get(`${API_BASE}/plugins/${id}`),
  getPluginConfigs: (id) => axios.get(`${API_BASE}/plugins/${id}/configs`),

  // Deployments
  getDeployments: (params) => axios.get(`${API_BASE}/deployments`, { params }),
  getDeployment: (id) => axios.get(`${API_BASE}/deployments/${id}`),
  createDeployment: (data) => axios.post(`${API_BASE}/deployments`, data),
  executeDeployment: (id) => axios.put(`${API_BASE}/deployments/${id}/execute`),

  // Updates
  getAvailableUpdates: () => axios.get(`${API_BASE}/updates/available`),
  checkUpdates: () => axios.post(`${API_BASE}/updates/check`),
  approveUpdate: (data) => axios.post(`${API_BASE}/updates/approve`, data),
  rejectUpdate: (data) => axios.post(`${API_BASE}/updates/reject`, data),
  getUpdateStatus: (pluginId) =>
    axios.get(`${API_BASE}/updates/${pluginId}/status`),

  // Approvals
  getPendingApprovals: () => axios.get(`${API_BASE}/approvals/pending`),
  getApprovalRequests: (params) =>
    axios.get(`${API_BASE}/approvals/requests`, { params }),
  getApproval: (id) => axios.get(`${API_BASE}/approvals/${id}`),
  getApprovalVotes: (id) => axios.get(`${API_BASE}/approvals/${id}/votes`),
  castVote: (id, vote) => axios.post(`${API_BASE}/approvals/${id}/vote`, vote),
  cancelApproval: (id) => axios.delete(`${API_BASE}/approvals/${id}/cancel`),

  // Audit
  getAuditEvents: (params) => axios.get(`${API_BASE}/audit/events`, { params }),
  getRecentAuditEvents: (limit) =>
    axios.get(`${API_BASE}/audit/recent`, { params: { limit } }),
  getEntityAudit: (type, id) =>
    axios.get(`${API_BASE}/audit/entity/${type}/${id}`),
  getUserAudit: (username) => axios.get(`${API_BASE}/audit/user/${username}`),

  // Groups
  getGroups: (params) => axios.get(`${API_BASE}/groups`, { params }),
  getGroup: (id) => axios.get(`${API_BASE}/groups/${id}`),
  getGroupInstances: (id) => axios.get(`${API_BASE}/groups/${id}/instances`),
  createGroup: (data) => axios.post(`${API_BASE}/groups`, data),
  deleteGroup: (id) => axios.delete(`${API_BASE}/groups/${id}`),
  addInstanceToGroup: (groupId, instanceId) =>
    axios.post(`${API_BASE}/groups/${groupId}/instances`, {
      instance_id: instanceId,
    }),
  removeInstanceFromGroup: (groupId, instanceId) =>
    axios.delete(`${API_BASE}/groups/${groupId}/instances/${instanceId}`),

  // Datapacks
  getDatapacks: (params) => axios.get(`${API_BASE}/datapacks`, { params }),
  getDatapack: (id) => axios.get(`${API_BASE}/datapacks/${id}`),
  getDatapackVersions: (id) =>
    axios.get(`${API_BASE}/datapacks/${id}/versions`),
  getInstanceDatapacks: (instanceId) =>
    axios.get(`${API_BASE}/datapacks/instances/${instanceId}`),
  createDatapack: (data) => axios.post(`${API_BASE}/datapacks`, data),
  assignDatapack: (datapackId, instanceId, data) =>
    axios.post(
      `${API_BASE}/datapacks/${datapackId}/instances/${instanceId}`,
      data
    ),
  removeDatapack: (datapackId, instanceId) =>
    axios.delete(`${API_BASE}/datapacks/${datapackId}/instances/${instanceId}`),

  // Tags
  getTags: (params) => axios.get(`${API_BASE}/tags`, { params }),
  getTag: (id) => axios.get(`${API_BASE}/tags/${id}`),
  getTagEntities: (id) => axios.get(`${API_BASE}/tags/${id}/entities`),
  getTagHierarchy: (id) => axios.get(`${API_BASE}/tags/${id}/hierarchy`),
  getEntityTags: (type, id) =>
    axios.get(`${API_BASE}/tags/entity/${type}/${id}`),
  createTag: (data) => axios.post(`${API_BASE}/tags`, data),
  deleteTag: (id) => axios.delete(`${API_BASE}/tags/${id}`),

  // Config
  getGlobalConfigs: (params) =>
    axios.get(`${API_BASE}/config/global`, { params }),
  resolveConfig: (params) =>
    axios.get(`${API_BASE}/config/resolve`, { params }),
  getVariances: (params) =>
    axios.get(`${API_BASE}/config/variances`, { params }),
  getConfigVariables: (params) =>
    axios.get(`${API_BASE}/config/variables`, { params }),
  getConfigHierarchy: (pluginName) =>
    axios.get(`${API_BASE}/config/hierarchy/${pluginName}`),
};

// Error Handler
axios.interceptors.response.use(
  (response) => response,
  (error) => {
    const message =
      error.response?.data?.detail || error.message || "An error occurred";
    showToast(message, "error");
    return Promise.reject(error);
  }
);

// Toast Notification
function showToast(message, type = "info") {
  const bgColors = {
    success: "linear-gradient(to right, #00b09b, #96c93d)",
    error: "linear-gradient(to right, #ff5f6d, #ffc371)",
    warning: "linear-gradient(to right, #f7b733, #fc4a1a)",
    info: "linear-gradient(to right, #4facfe, #00f2fe)",
  };

  Toastify({
    text: message,
    duration: 3000,
    close: true,
    gravity: "top",
    position: "right",
    style: {
      background: bgColors[type] || bgColors.info,
    },
  }).showToast();
}

// Loading State
function setLoading(elementId, loading = true) {
  const element = document.getElementById(elementId);
  if (!element) return;

  if (loading) {
    element.innerHTML =
      '<div class="text-center py-5"><div class="spinner-border text-primary" role="status"><span class="visually-hidden">Loading...</span></div></div>';
  }
}

// Format Date
function formatDate(dateString) {
  const date = new Date(dateString);
  const now = new Date();
  const diff = now - date;
  const seconds = Math.floor(diff / 1000);
  const minutes = Math.floor(seconds / 60);
  const hours = Math.floor(minutes / 60);
  const days = Math.floor(hours / 24);

  if (days > 7) {
    return date.toLocaleDateString();
  } else if (days > 0) {
    return `${days}d ago`;
  } else if (hours > 0) {
    return `${hours}h ago`;
  } else if (minutes > 0) {
    return `${minutes}m ago`;
  } else {
    return "Just now";
  }
}

// Format Number
function formatNumber(num) {
  if (num >= 1000000) {
    return (num / 1000000).toFixed(1) + "M";
  } else if (num >= 1000) {
    return (num / 1000).toFixed(1) + "K";
  }
  return num.toString();
}
