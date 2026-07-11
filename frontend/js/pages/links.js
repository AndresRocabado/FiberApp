async function renderLinks(container) {
    const { t } = I18n;

    async function draw() {
        const [links, nodes] = await Promise.all([API.getLinks(), API.getNodes()]);

        if (nodes.length < 2) {
            container.innerHTML = `
                <h1 class="page-title">${t("links_title")}</h1>
                <div class="alert alert-warning">${t("warn_need_2_nodes") ?? "Se necesitan al menos 2 nodos."}</div>
            `;
            return;
        }

        container.innerHTML = `
            <div class="page-header">
                <h1 class="page-title">${t("links_title")}</h1>
                <button class="btn btn-primary" id="btn-new-link">+ ${t("link_new")}</button>
            </div>

            <div id="link-form-area"></div>

            <div class="table-toolbar">
                <a href="${API.exportLinksUrl()}" class="btn btn-outline" download>${t("btn_export_csv")}</a>
            </div>

            <div class="table-wrapper">
                <table class="data-table">
                    <thead>
                        <tr>
                            <th>${t("col_id")}</th>
                            <th>${t("col_name")}</th>
                            <th>${t("col_origin")}</th>
                            <th>${t("col_destination")}</th>
                            <th>${t("col_distance")}</th>
                            <th>${t("col_capacity")}</th>
                            <th>${t("col_status")}</th>
                            <th>${t("col_created")}</th>
                            <th></th>
                        </tr>
                    </thead>
                    <tbody>
                        ${links.length === 0
                            ? `<tr><td colspan="9" class="empty-msg">${t("links_empty")}</td></tr>`
                            : links.map(lnk => `
                                <tr>
                                    <td>${lnk.id}</td>
                                    <td>${lnk.name ?? ""}</td>
                                    <td>${lnk.origin_node_name ?? lnk.origin_node_id}</td>
                                    <td>${lnk.destination_node_name ?? lnk.destination_node_id}</td>
                                    <td>${lnk.distance_km.toFixed(2)}</td>
                                    <td>${lnk.capacity_gbps.toFixed(1)}</td>
                                    <td><span class="badge badge-${statusClass(lnk.status)}">${lnk.status}</span></td>
                                    <td>${lnk.created_at}</td>
                                    <td class="row-actions">
                                        <button class="btn btn-sm btn-outline btn-edit-link" data-id="${lnk.id}">✏️</button>
                                        <button class="btn btn-sm btn-danger btn-delete-link" data-id="${lnk.id}">🗑️</button>
                                    </td>
                                </tr>`).join("")
                        }
                    </tbody>
                </table>
            </div>
        `;

        document.getElementById("btn-new-link").onclick = () => showLinkForm(null, nodes, draw);
        document.querySelectorAll(".btn-edit-link").forEach(btn => {
            btn.onclick = async () => {
                const lnk = await API.getLink(+btn.dataset.id);
                showLinkForm(lnk, nodes, draw);
            };
        });
        document.querySelectorAll(".btn-delete-link").forEach(btn => {
            btn.onclick = () => confirmDelete(
                t("confirm_delete_link"),
                async () => { await API.deleteLink(+btn.dataset.id); showToast(t("msg_link_deleted")); draw(); }
            );
        });
    }

    await draw();
}

function showLinkForm(link, nodes, onSave) {
    const { t } = I18n;
    const isEdit      = link !== null;
    const area        = document.getElementById("link-form-area");
    const LINK_STATUS = ["Activo", "Inactivo", "Mantenimiento"];

    const nodeOptions = (selectedId) =>
        nodes.map(n => `<option value="${n.id}" ${n.id === selectedId ? "selected" : ""}>${n.id} - ${n.name} (${n.city})</option>`).join("");

    area.innerHTML = `
        <div class="form-card">
            <h2>${isEdit ? t("btn_edit") : t("link_new")}</h2>
            <form id="link-form">
                <div class="form-grid">
                    <div class="form-group">
                        <label>${t("lbl_link_name")}</label>
                        <input name="name" value="${isEdit ? (link.name ?? "") : ""}">
                    </div>
                    <div class="form-group">
                        <label>${t("lbl_link_status")}</label>
                        <select name="status">
                            ${LINK_STATUS.map(s => `<option ${isEdit && link.status === s ? "selected" : ""}>${s}</option>`).join("")}
                        </select>
                    </div>
                    <div class="form-group">
                        <label>${t("lbl_origin_node")}</label>
                        <select name="origin_node_id">
                            ${nodeOptions(isEdit ? link.origin_node_id : null)}
                        </select>
                    </div>
                    <div class="form-group">
                        <label>${t("lbl_dest_node")}</label>
                        <select name="destination_node_id">
                            ${nodeOptions(isEdit ? link.destination_node_id : null)}
                        </select>
                    </div>
                    <div class="form-group">
                        <label>${t("lbl_distance")}</label>
                        <input name="distance_km" type="number" min="0.01" step="0.01" required value="${isEdit ? link.distance_km : "1"}">
                    </div>
                    <div class="form-group">
                        <label>${t("lbl_capacity")}</label>
                        <input name="capacity_gbps" type="number" min="0.01" step="0.1" required value="${isEdit ? link.capacity_gbps : "10"}">
                    </div>
                </div>
                <div class="form-actions">
                    <button type="submit" class="btn btn-primary">${t("btn_save")}</button>
                    <button type="button" class="btn btn-outline" id="btn-cancel-link">${t("btn_cancel")}</button>
                </div>
                <p class="form-error" id="link-error"></p>
            </form>
        </div>
    `;

    document.getElementById("btn-cancel-link").onclick = () => area.innerHTML = "";
    document.getElementById("link-form").onsubmit = async (e) => {
        e.preventDefault();
        const fd   = new FormData(e.target);
        const body = {
            origin_node_id:      +fd.get("origin_node_id"),
            destination_node_id: +fd.get("destination_node_id"),
            distance_km:         +fd.get("distance_km"),
            capacity_gbps:       +fd.get("capacity_gbps"),
            status:              fd.get("status"),
            name:                fd.get("name") || null,
        };
        try {
            if (isEdit) {
                await API.updateLink(link.id, body);
                showToast(t("msg_link_updated"));
            } else {
                await API.createLink(body);
                showToast(t("msg_link_created"));
            }
            area.innerHTML = "";
            onSave();
        } catch (err) {
            document.getElementById("link-error").textContent = err.message;
        }
    };
}
