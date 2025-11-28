// HomeAMP V2.0 - Datapacks Component

let datapacksTable = null;

async function loadDatapacks() {
  try {
    const response = await API.getDatapacks();
    const datapacks = response.data || [];

    if (datapacksTable) {
      datapacksTable.destroy();
    }

    const tbody = document.querySelector("#datapacks-table tbody");
    tbody.innerHTML = "";

    datapacks.forEach((datapack) => {
      const row = `
                <tr>
                    <td><strong>${datapack.datapack_name}</strong></td>
                    <td><span class="badge bg-info">${
                      datapack.category
                    }</span></td>
                    <td>${datapack.version}</td>
                    <td><span class="badge bg-secondary">${
                      datapack.instance_count || 0
                    }</span></td>
                    <td>
                        <button class="btn btn-sm btn-primary" onclick="viewDatapack('${
                          datapack.datapack_id
                        }')">
                            <i data-feather="eye" class="icon-sm"></i>
                        </button>
                        <button class="btn btn-sm btn-success" onclick="assignDatapack('${
                          datapack.datapack_id
                        }')">
                            <i data-feather="plus" class="icon-sm"></i> Assign
                        </button>
                    </td>
                </tr>
            `;
      tbody.innerHTML += row;
    });

    datapacksTable = $("#datapacks-table").DataTable({
      pageLength: 25,
      order: [[0, "asc"]],
    });

    feather.replace();
  } catch (error) {
    console.error("Failed to load datapacks:", error);
  }
}

async function viewDatapack(id) {
  try {
    const response = await API.getDatapack(id);
    const datapack = response.data;

    showToast(`Viewing datapack ${datapack.datapack_name}`, "info");
    // TODO: Show datapack detail modal
  } catch (error) {
    console.error("Failed to view datapack:", error);
  }
}

function assignDatapack(id) {
  showToast("Datapack assignment modal would open here", "info");
  // TODO: Show instance selection modal
}
