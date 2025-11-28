// HomeAMP V2.0 - Approvals Component

let approvalsTable = null;

async function loadApprovals() {
  try {
    const response = await API.getPendingApprovals();
    const approvals = response.data || [];

    if (approvalsTable) {
      approvalsTable.destroy();
    }

    const tbody = document.querySelector("#approvals-table tbody");
    tbody.innerHTML = "";

    approvals.forEach((approval) => {
      const statusBadge =
        {
          pending: "bg-warning",
          approved: "bg-success",
          rejected: "bg-danger",
          cancelled: "bg-secondary",
        }[approval.status] || "bg-secondary";

      const row = `
                <tr>
                    <td><strong>${approval.title}</strong></td>
                    <td><span class="badge bg-info">${
                      approval.request_type
                    }</span></td>
                    <td>${approval.requester}</td>
                    <td><span class="badge bg-secondary">${
                      approval.approved_count
                    }/${approval.required_approvals}</span></td>
                    <td><span class="badge ${statusBadge}">${
        approval.status
      }</span></td>
                    <td>
                        ${
                          approval.status === "pending"
                            ? `
                            <button class="btn btn-sm btn-success" onclick="castApprovalVote('${approval.approval_id}', true)">
                                <i data-feather="thumbs-up" class="icon-sm"></i>
                            </button>
                            <button class="btn btn-sm btn-danger" onclick="castApprovalVote('${approval.approval_id}', false)">
                                <i data-feather="thumbs-down" class="icon-sm"></i>
                            </button>
                        `
                            : ""
                        }
                        <button class="btn btn-sm btn-primary" onclick="viewApproval('${
                          approval.approval_id
                        }')">
                            <i data-feather="eye" class="icon-sm"></i>
                        </button>
                    </td>
                </tr>
            `;
      tbody.innerHTML += row;
    });

    approvalsTable = $("#approvals-table").DataTable({
      pageLength: 25,
      order: [[0, "asc"]],
    });

    feather.replace();
  } catch (error) {
    console.error("Failed to load approvals:", error);
  }
}

async function castApprovalVote(approvalId, approved) {
  try {
    await API.castVote(approvalId, { approved });
    showToast(`Vote cast: ${approved ? "Approved" : "Rejected"}`, "success");
    loadApprovals();
    updateApprovalBadge();
  } catch (error) {
    console.error("Failed to cast vote:", error);
  }
}

async function viewApproval(id) {
  try {
    const response = await API.getApproval(id);
    const approval = response.data;

    showToast(`Viewing approval ${id}`, "info");
    // TODO: Show approval detail modal
  } catch (error) {
    console.error("Failed to view approval:", error);
  }
}
