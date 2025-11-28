// HomeAMP V2.0 - Updates Component

let updatesTable = null;

async function loadUpdates() {
  try {
    const response = await API.getAvailableUpdates();
    const updates = response.data || [];

    if (updatesTable) {
      updatesTable.destroy();
    }

    const tbody = document.querySelector("#updates-table tbody");
    tbody.innerHTML = "";

    updates.forEach((update) => {
      const row = `
                <tr>
                    <td><strong>${update.plugin_name}</strong></td>
                    <td>${update.current_version}</td>
                    <td>${update.latest_version}</td>
                    <td><span class="badge bg-info">${update.source}</span></td>
                    <td>
                        <button class="btn btn-sm btn-success" onclick="approveUpdate('${update.plugin_id}')">
                            <i data-feather="check" class="icon-sm"></i> Approve
                        </button>
                        <button class="btn btn-sm btn-danger" onclick="rejectUpdate('${update.plugin_id}')">
                            <i data-feather="x" class="icon-sm"></i> Reject
                        </button>
                    </td>
                </tr>
            `;
      tbody.innerHTML += row;
    });

    updatesTable = $("#updates-table").DataTable({
      pageLength: 25,
      order: [[0, "asc"]],
    });

    feather.replace();
  } catch (error) {
    console.error("Failed to load updates:", error);
  }
}

async function checkUpdates() {
  try {
    showToast("Checking for updates...", "info");
    await API.checkUpdates();
    showToast("Update check complete", "success");
    loadUpdates();
  } catch (error) {
    console.error("Failed to check updates:", error);
  }
}

async function approveUpdate(pluginId) {
  try {
    await API.approveUpdate({ plugin_id: pluginId });
    showToast("Update approved", "success");
    loadUpdates();
  } catch (error) {
    console.error("Failed to approve update:", error);
  }
}

async function rejectUpdate(pluginId) {
  try {
    await API.rejectUpdate({ plugin_id: pluginId });
    showToast("Update rejected", "info");
    loadUpdates();
  } catch (error) {
    console.error("Failed to reject update:", error);
  }
}
