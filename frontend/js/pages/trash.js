async function renderTrash(container) {
    const { t } = I18n;
    container.innerHTML = `<div class="loading">...</div>`;

    let deletedNodes = [], deletedLinks = [];
    try {
        [deletedNodes, deletedLinks] = await Promise.all([
            API.getDeletedNodes(),
            API.getDeletedLinks(),
        ]);
    } catch (err) {
        container.innerHTML = `<p class="empty-msg">${err.message}</p>`;
        return;
    }

    container.innerHTML = `
        <h1 class="page-title">${t("trash_title")}</h1>

        <h2 class="section-title">🗑️ ${t("trash_nodes")}</h2>
        <div class="table-wrapper" id="trash-nodes-wrap">
            ${renderDeletedNodes(deletedNodes, t)}
        </div>

        <h2 class="section-title">🗑️ ${t("trash_links")}</h2>
        <div class="table-wrapper" id="trash-links-wrap">
            ${renderDeletedLinks(deletedLinks, t)}
        </div>
    `;

    container.querySelectorAll(".btn-restore-node").forEach(btn => {
        btn.onclick = async () => {
            try {
                const node = await API.restoreNode(+btn.dataset.id);
                showToast(`"${node.name}" ${t("msg_node_restored")}`);
                const wrap = document.getElementById("trash-nodes-wrap");
                const updated = await API.getDeletedNodes();
                wrap.innerHTML = renderDeletedNodes(updated, t);
                attachNodeRestoreHandlers(container, t);
            } catch (err) { showToast(err.message); }
        };
    });

    container.querySelectorAll(".btn-restore-link").forEach(btn => {
        btn.onclick = async () => {
            try {
                const lnk = await API.restoreLink(+btn.dataset.id);
                showToast(`${lnk.name ? `"${lnk.name}" ` : ""}${t("msg_link_restored")}`);
                const wrap = document.getElementById("trash-links-wrap");
                const updated = await API.getDeletedLinks();
                wrap.innerHTML = renderDeletedLinks(updated, t);
                attachLinkRestoreHandlers(container, t);
            } catch (err) { showToast(err.message); }
        };
    });
}

function renderDeletedNodes(nodes, t) {
    if (!nodes.length) return `<p class="empty-msg">${t("trash_empty")}</p>`;
    return `
        <table class="data-table">
            <thead><tr>
                <th>${t("col_id")}</th>
                <th>${t("col_name")}</th>
                <th>${t("col_city")}</th>
                <th>${t("col_type")}</th>
                <th>${t("col_status")}</th>
                <th>${t("col_deleted")}</th>
                <th></th>
            </tr></thead>
            <tbody>
                ${nodes.map(n => `
                    <tr>
                        <td>${n.id}</td>
                        <td>${n.name}</td>
                        <td>${n.city}</td>
                        <td><span class="badge badge-${typeClass(n.node_type)}">${n.node_type}</span></td>
                        <td><span class="badge badge-${statusClass(n.status)}">${n.status}</span></td>
                        <td class="text-muted">${n.deleted_at ?? ""}</td>
                        <td class="row-actions">
                            <button class="btn btn-sm btn-primary btn-restore-node" data-id="${n.id}">${t("btn_restore")}</button>
                        </td>
                    </tr>`).join("")}
            </tbody>
        </table>`;
}

function renderDeletedLinks(links, t) {
    if (!links.length) return `<p class="empty-msg">${t("trash_empty")}</p>`;
    return `
        <table class="data-table">
            <thead><tr>
                <th>${t("col_id")}</th>
                <th>${t("col_name")}</th>
                <th>${t("col_origin")}</th>
                <th>${t("col_destination")}</th>
                <th>${t("col_status")}</th>
                <th>${t("col_deleted")}</th>
                <th></th>
            </tr></thead>
            <tbody>
                ${links.map(lnk => `
                    <tr>
                        <td>${lnk.id}</td>
                        <td>${lnk.name ?? ""}</td>
                        <td>${lnk.origin_node_name ?? lnk.origin_node_id}</td>
                        <td>${lnk.destination_node_name ?? lnk.destination_node_id}</td>
                        <td><span class="badge badge-${statusClass(lnk.status)}">${lnk.status}</span></td>
                        <td class="text-muted">${lnk.deleted_at ?? ""}</td>
                        <td class="row-actions">
                            <button class="btn btn-sm btn-primary btn-restore-link" data-id="${lnk.id}">${t("btn_restore")}</button>
                        </td>
                    </tr>`).join("")}
            </tbody>
        </table>`;
}

function attachNodeRestoreHandlers(container, t) {
    container.querySelectorAll(".btn-restore-node").forEach(btn => {
        btn.onclick = async () => {
            try {
                const node = await API.restoreNode(+btn.dataset.id);
                showToast(`"${node.name}" ${t("msg_node_restored")}`);
                const wrap = document.getElementById("trash-nodes-wrap");
                const updated = await API.getDeletedNodes();
                wrap.innerHTML = renderDeletedNodes(updated, t);
                attachNodeRestoreHandlers(container, t);
            } catch (err) { showToast(err.message); }
        };
    });
}

function attachLinkRestoreHandlers(container, t) {
    container.querySelectorAll(".btn-restore-link").forEach(btn => {
        btn.onclick = async () => {
            try {
                const lnk = await API.restoreLink(+btn.dataset.id);
                showToast(`${lnk.name ? `"${lnk.name}" ` : ""}${t("msg_link_restored")}`);
                const wrap = document.getElementById("trash-links-wrap");
                const updated = await API.getDeletedLinks();
                wrap.innerHTML = renderDeletedLinks(updated, t);
                attachLinkRestoreHandlers(container, t);
            } catch (err) { showToast(err.message); }
        };
    });
}
