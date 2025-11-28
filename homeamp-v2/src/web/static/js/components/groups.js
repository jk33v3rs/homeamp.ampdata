// HomeAMP V2.0 - Groups Component

async function loadGroups() {
  const container = document.getElementById("groups-container");
  setLoading("groups-container");

  try {
    const response = await API.getGroups();
    const groups = response.data || [];

    if (groups.length === 0) {
      container.innerHTML = '<p class="text-muted">No groups found</p>';
      return;
    }

    let html = '<div class="row g-3">';
    groups.forEach((group) => {
      html += `
                <div class="col-md-4">
                    <div class="card">
                        <div class="card-body">
                            <h5 class="card-title">${group.group_name}</h5>
                            <p class="card-text text-muted">${
                              group.description || "No description"
                            }</p>
                            <p class="mb-2">
                                <span class="badge bg-info">${
                                  group.group_type
                                }</span>
                                <span class="badge bg-secondary">${
                                  group.instance_count || 0
                                } instances</span>
                            </p>
                            <button class="btn btn-sm btn-primary" onclick="viewGroup('${
                              group.group_id
                            }')">
                                <i data-feather="eye" class="icon-sm"></i> View
                            </button>
                            <button class="btn btn-sm btn-danger" onclick="deleteGroup('${
                              group.group_id
                            }')">
                                <i data-feather="trash-2" class="icon-sm"></i> Delete
                            </button>
                        </div>
                    </div>
                </div>
            `;
    });
    html += "</div>";

    container.innerHTML = html;
    feather.replace();
  } catch (error) {
    container.innerHTML = '<p class="text-danger">Failed to load groups</p>';
    console.error("Failed to load groups:", error);
  }
}

async function viewGroup(id) {
  try {
    const response = await API.getGroup(id);
    const group = response.data;

    showToast(`Viewing group ${group.group_name}`, "info");
    // TODO: Show group detail modal
  } catch (error) {
    console.error("Failed to view group:", error);
  }
}

async function deleteGroup(id) {
  if (!confirm("Are you sure you want to delete this group?")) return;

  try {
    await API.deleteGroup(id);
    showToast("Group deleted", "success");
    loadGroups();
  } catch (error) {
    console.error("Failed to delete group:", error);
  }
}
