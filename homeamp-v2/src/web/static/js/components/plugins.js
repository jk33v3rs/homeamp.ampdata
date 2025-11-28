// HomeAMP V2.0 - Plugins Component

let pluginsTable = null;

async function loadPlugins() {
  try {
    const response = await API.getPlugins();
    const plugins = response.data || [];

    if (pluginsTable) {
      pluginsTable.destroy();
    }

    const tbody = document.querySelector("#plugins-table tbody");
    tbody.innerHTML = "";

    plugins.forEach((plugin) => {
      const hasUpdate =
        plugin.latest_version &&
        plugin.latest_version !== plugin.current_version;

      const row = `
                <tr>
                    <td>
                        <strong>${plugin.plugin_name}</strong>
                        ${
                          plugin.is_premium
                            ? '<span class="badge bg-warning ms-2">Premium</span>'
                            : ""
                        }
                    </td>
                    <td><span class="badge bg-info">${
                      plugin.platform
                    }</span></td>
                    <td>${plugin.current_version || "Unknown"}</td>
                    <td>
                        ${plugin.latest_version || "N/A"}
                        ${
                          hasUpdate
                            ? '<i data-feather="alert-circle" class="icon-sm text-warning ms-1"></i>'
                            : ""
                        }
                    </td>
                    <td><span class="badge bg-secondary">${
                      plugin.install_count || 0
                    }</span></td>
                    <td>
                        <button class="btn btn-sm btn-primary" onclick="viewPlugin('${
                          plugin.plugin_id
                        }')">
                            <i data-feather="eye" class="icon-sm"></i>
                        </button>
                    </td>
                </tr>
            `;
      tbody.innerHTML += row;
    });

    pluginsTable = $("#plugins-table").DataTable({
      pageLength: 25,
      order: [[0, "asc"]],
    });

    feather.replace();
  } catch (error) {
    console.error("Failed to load plugins:", error);
  }
}

async function viewPlugin(id) {
  try {
    const response = await API.getPlugin(id);
    const plugin = response.data;

    showToast(`Viewing ${plugin.plugin_name}`, "info");
    // TODO: Show plugin detail modal
  } catch (error) {
    console.error("Failed to view plugin:", error);
  }
}
