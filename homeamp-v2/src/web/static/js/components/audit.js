// HomeAMP V2.0 - Audit Log Component

let auditTable = null;

async function loadAuditLog() {
  try {
    const response = await API.getRecentAuditEvents(100);
    const events = response.data || [];

    if (auditTable) {
      auditTable.destroy();
    }

    const tbody = document.querySelector("#audit-table tbody");
    tbody.innerHTML = "";

    events.forEach((event) => {
      const row = `
                <tr>
                    <td>${formatDate(event.timestamp)}</td>
                    <td>${event.username || "System"}</td>
                    <td><span class="badge bg-info">${event.action}</span></td>
                    <td>${event.entity_type}:${event.entity_id}</td>
                    <td><small>${event.details || "-"}</small></td>
                </tr>
            `;
      tbody.innerHTML += row;
    });

    auditTable = $("#audit-table").DataTable({
      pageLength: 25,
      order: [[0, "desc"]],
    });

    feather.replace();
  } catch (error) {
    console.error("Failed to load audit log:", error);
  }
}
