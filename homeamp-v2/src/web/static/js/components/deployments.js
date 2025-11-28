// HomeAMP V2.0 - Deployments Component

let deploymentsTable = null;

async function loadDeployments() {
  try {
    const response = await API.getDeployments();
    const deployments = response.data || [];

    if (deploymentsTable) {
      deploymentsTable.destroy();
    }

    const tbody = document.querySelector("#deployments-table tbody");
    tbody.innerHTML = "";

    deployments.forEach((deployment) => {
      const statusBadge =
        {
          pending: "bg-warning",
          in_progress: "bg-info",
          completed: "bg-success",
          failed: "bg-danger",
          cancelled: "bg-secondary",
        }[deployment.status] || "bg-secondary";

      const row = `
                <tr>
                    <td>${deployment.instance_name}</td>
                    <td><span class="badge bg-info">${
                      deployment.deployment_type
                    }</span></td>
                    <td><span class="badge ${statusBadge}">${
        deployment.status
      }</span></td>
                    <td>${formatDate(deployment.created_at)}</td>
                    <td>
                        ${
                          deployment.status === "pending"
                            ? `
                            <button class="btn btn-sm btn-success" onclick="executeDeployment('${deployment.deployment_id}')">
                                <i data-feather="play" class="icon-sm"></i>
                            </button>
                        `
                            : ""
                        }
                        <button class="btn btn-sm btn-primary" onclick="viewDeployment('${
                          deployment.deployment_id
                        }')">
                            <i data-feather="eye" class="icon-sm"></i>
                        </button>
                    </td>
                </tr>
            `;
      tbody.innerHTML += row;
    });

    deploymentsTable = $("#deployments-table").DataTable({
      pageLength: 25,
      order: [[3, "desc"]],
    });

    feather.replace();
  } catch (error) {
    console.error("Failed to load deployments:", error);
  }
}

async function executeDeployment(id) {
  try {
    await API.executeDeployment(id);
    showToast("Deployment started", "success");
    loadDeployments();
  } catch (error) {
    console.error("Failed to execute deployment:", error);
  }
}

async function viewDeployment(id) {
  try {
    const response = await API.getDeployment(id);
    const deployment = response.data;

    showToast(`Viewing deployment ${id}`, "info");
    // TODO: Show deployment detail modal
  } catch (error) {
    console.error("Failed to view deployment:", error);
  }
}
