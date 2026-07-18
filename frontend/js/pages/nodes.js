async function renderNodes(container) {
    const { t } = I18n;
    let _nodes = [], _cities = [];
    let _sortCol = null, _sortDir = 1;

    const COLS = [
        { key: "id",         label: () => t("col_id") },
        { key: "name",       label: () => t("col_name") },
        { key: "city",       label: () => t("col_city") },
        { key: "node_type",  label: () => t("col_type") },
        { key: "status",     label: () => t("col_status") },
        { key: "created_at", label: () => t("col_created") },
    ];

    function renderHeaders() {
        const thead = document.getElementById("nodes-thead");
        thead.innerHTML = `<tr>
            ${COLS.map(c => `
                <th class="sortable${_sortCol === c.key ? (_sortDir === 1 ? " sort-asc" : " sort-desc") : ""}" data-col="${c.key}">
                    ${c.label()} <span class="sort-icon">${_sortCol === c.key ? (_sortDir === 1 ? "↑" : "↓") : "↕"}</span>
                </th>`).join("")}
            <th></th>
        </tr>`;
        thead.querySelectorAll(".sortable").forEach(th => {
            th.addEventListener("click", () => {
                if (_sortCol === th.dataset.col) _sortDir *= -1;
                else { _sortCol = th.dataset.col; _sortDir = 1; }
                renderHeaders();
                renderRows();
            });
        });
    }

    function renderRows() {
        const tbody = document.getElementById("nodes-tbody");
        const sorted = sortArray(_nodes, _sortCol, _sortDir);
        tbody.innerHTML = sorted.length === 0
            ? `<tr><td colspan="7" class="empty-msg">${t("nodes_empty")}</td></tr>`
            : sorted.map(n => `
                <tr>
                    <td>${n.id}</td>
                    <td>${n.name}</td>
                    <td>${n.city}</td>
                    <td>${n.node_type}</td>
                    <td><span class="badge badge-${statusClass(n.status)}">${n.status}</span></td>
                    <td>${n.created_at}</td>
                    <td class="row-actions">
                        <button class="btn btn-sm btn-outline btn-edit-node" data-id="${n.id}">✏️</button>
                        <button class="btn btn-sm btn-danger btn-delete-node" data-id="${n.id}">🗑️</button>
                    </td>
                </tr>`).join("");

        tbody.querySelectorAll(".btn-edit-node").forEach(btn => {
            btn.onclick = async () => {
                const node = await API.getNode(+btn.dataset.id);
                showNodeForm(node, _cities, reload);
            };
        });
        tbody.querySelectorAll(".btn-delete-node").forEach(btn => {
            btn.onclick = () => confirmDelete(
                t("confirm_delete_node"),
                async () => { await API.deleteNode(+btn.dataset.id); showToast(t("msg_node_deleted")); reload(); }
            );
        });
    }

    async function reload() {
        [_nodes, _cities] = await Promise.all([API.getNodes(), API.getCities()]);
        renderHeaders();
        renderRows();
    }

    async function draw() {
        [_nodes, _cities] = await Promise.all([API.getNodes(), API.getCities()]);

        container.innerHTML = `
            <div class="page-header">
                <h1 class="page-title">${t("nodes_title")}</h1>
                <button class="btn btn-primary" id="btn-new-node">+ ${t("node_new")}</button>
            </div>
            <div id="node-form-area"></div>
            <div class="table-toolbar">
                <a href="${API.exportNodesUrl()}" class="btn btn-outline" download>${t("btn_export_csv")}</a>
            </div>
            <div class="table-wrapper">
                <table class="data-table">
                    <thead id="nodes-thead"></thead>
                    <tbody id="nodes-tbody"></tbody>
                </table>
            </div>
        `;

        document.getElementById("btn-new-node").onclick = () => showNodeForm(null, _cities, reload);
        renderHeaders();
        renderRows();
    }

    await draw();
}

function showNodeForm(node, cities, onSave) {
    const { t } = I18n;
    const isEdit = node !== null;
    const area   = document.getElementById("node-form-area");

    const NODE_TYPES = [
        { value: "Central",      label: t("node_type_central") },
        { value: "Distribución", label: t("node_type_distribution") },
        { value: "Acceso",       label: t("node_type_access") },
        { value: "Terminal",     label: t("node_type_terminal") },
    ];
    const NODE_STATUSES = [
        { value: "Activo",        label: t("status_active") },
        { value: "Inactivo",      label: t("status_inactive") },
        { value: "Mantenimiento", label: t("status_maintenance") },
    ];

    area.innerHTML = `
        <div class="form-card">
            <h2>${isEdit ? t("btn_edit") : t("node_new")}</h2>
            <form id="node-form">
                <div class="form-grid">
                    <div class="form-group">
                        <label>${t("lbl_name")}</label>
                        <input name="name" required value="${isEdit ? node.name : ""}">
                    </div>
                    <div class="form-group">
                        <label>${t("lbl_city")}</label>
                        <input name="city" list="city-list" autocomplete="off" required value="${isEdit ? node.city : ""}">
                        <datalist id="city-list">
                            ${cities.map(c => `<option value="${c}">`).join("")}
                        </datalist>
                    </div>
                    <div class="form-group">
                        <label>${t("lbl_node_type")}</label>
                        <select name="node_type">
                            ${NODE_TYPES.map(tp => `<option value="${tp.value}" ${isEdit && node.node_type === tp.value ? "selected" : ""}>${tp.label}</option>`).join("")}
                        </select>
                    </div>
                    <div class="form-group">
                        <label>${t("lbl_op_status")}</label>
                        <select name="status">
                            ${NODE_STATUSES.map(s => `<option value="${s.value}" ${isEdit && node.status === s.value ? "selected" : ""}>${s.label}</option>`).join("")}
                        </select>
                    </div>
                </div>
                <div class="form-actions">
                    <button type="submit" class="btn btn-primary">${t("btn_save")}</button>
                    <button type="button" class="btn btn-outline" id="btn-cancel-node">${t("btn_cancel")}</button>
                </div>
                <p class="form-error" id="node-error"></p>
            </form>
        </div>
    `;

    document.getElementById("btn-cancel-node").onclick = () => area.innerHTML = "";
    document.getElementById("node-form").onsubmit = async (e) => {
        e.preventDefault();
        const fd   = new FormData(e.target);
        const body = Object.fromEntries(fd.entries());
        try {
            if (isEdit) {
                await API.updateNode(node.id, body);
                showToast(t("msg_node_updated"));
            } else {
                await API.createNode(body);
                showToast(t("msg_node_created"));
            }
            area.innerHTML = "";
            onSave();
        } catch (err) {
            document.getElementById("node-error").textContent = err.message;
        }
    };
}
