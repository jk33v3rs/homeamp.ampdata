// HomeAMP V2.0 - Instances Component

let instancesTable = null;

async function loadInstances() {
  try {
    const response = await API.getInstances();
    const instances = response.data || [];

    if (instancesTable) {
      instancesTable.destroy();
    }

    const tbody = document.querySelector("#instances-table tbody");
    tbody.innerHTML = "";

    instances.forEach((instance) => {
      const row = `
                <tr>
                    <td>
                        <strong>${instance.instance_name}</strong>
                        ${
                          instance.is_production
                            ? '<span class="badge bg-danger ms-2">PROD</span>'
                            : ""
                        }
                    </td>
                    <td>${instance.server_name}</td>
                    <td>${instance.platform}</td>
                    <td>${instance.version || "Unknown"}</td>
                    <td>${instance.plugin_count || 0}</td>
                    <td>
                        <span class="badge ${
                          instance.is_active ? "bg-success" : "bg-secondary"
                        }">
                            ${instance.is_active ? "Active" : "Inactive"}
                        </span>
                    </td>
                    <td>
                        <button class="btn btn-sm btn-primary" onclick="viewInstance('${
                          instance.instance_id
                        }')">
                            <i data-feather="eye" class="icon-sm"></i>
                        </button>
                    </td>
                </tr>
            `;
      tbody.innerHTML += row;
    });

    instancesTable = $("#instances-table").DataTable({
      pageLength: 25,
      order: [[0, "asc"]],
    });

    feather.replace();
  } catch (error) {
    console.error("Failed to load instances:", error);
  }
}

async function viewInstance(id) {
  try {
    const response = await API.getInstance(id);
    const instance = response.data;

    showToast(`Viewing ${instance.instance_name}`, "info");
    // TODO: Show instance detail modal
  } catch (error) {
    console.error("Failed to view instance:", error);
  }
}

function triggerScan() {
  showToast("Scan triggered - check back in a few minutes", "success");
  // TODO: Implement scan trigger
}
