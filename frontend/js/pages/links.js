async function renderLinks(container) {
    const { t } = I18n;
    let _links = [], _nodes = [];
    let _sortCol = null, _sortDir = 1;
    let _filter = '';

    const COLS = [
        { key: "id",                    label: () => t("col_id") },
        { key: "name",                  label: () => t("col_name") },
        { key: "origin_node_name",      label: () => t("col_origin") },
        { key: "destination_node_name", label: () => t("col_destination") },
        { key: "distance_km",           label: () => t("col_distance") },
        { key: "capacity_gbps",         label: () => t("col_capacity") },
        { key: "status",                label: () => t("col_status") },
        { key: "created_at",            label: () => t("col_created") },
    ];

    function renderHeaders() {
        const thead = document.getElementById("links-thead");
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
        const tbody = document.getElementById("links-tbody");
        const term = _filter.toLowerCase();
        const visible = term
            ? _links.filter(lnk => [lnk.name, lnk.origin_node_name, lnk.destination_node_name, lnk.status].some(v => v?.toLowerCase().includes(term)))
            : _links;
        const sorted = sortArray(visible, _sortCol, _sortDir);
        const countEl = document.getElementById("links-count");
        if (countEl) {
            countEl.textContent = _filter
                ? `${t('records_showing')} ${sorted.length} ${t('records_of')} ${_links.length} ${t('records_links')}`
                : `${t('records_showing')} ${_links.length} ${t('records_links')}`;
        }
        tbody.innerHTML = sorted.length === 0
            ? `<tr><td colspan="9" class="empty-msg">${t("links_empty")}</td></tr>`
            : sorted.map(lnk => `
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
                        <button class="btn btn-sm btn-outline btn-edit-link" data-id="${lnk.id}" title="${t('btn_edit')}">✏️</button>
                        <button class="btn btn-sm btn-danger btn-delete-link" data-id="${lnk.id}" data-name="${lnk.name ?? '#' + lnk.id}" title="${t('btn_delete')}">🗑️</button>
                    </td>
                </tr>`).join("");

        tbody.querySelectorAll(".btn-edit-link").forEach(btn => {
            btn.onclick = async () => {
                const lnk = await API.getLink(+btn.dataset.id);
                showLinkForm(lnk, _nodes, reload);
            };
        });
        tbody.querySelectorAll(".btn-delete-link").forEach(btn => {
            btn.onclick = () => confirmDelete(
                t("confirm_delete_link").replace("{name}", btn.dataset.name),
                async () => { await API.deleteLink(+btn.dataset.id); showToast(t("msg_link_deleted")); reload(); }
            );
        });
    }

    async function reload() {
        [_links, _nodes] = await Promise.all([API.getLinks(), API.getNodes()]);
        renderHeaders();
        renderRows();
    }

    async function draw() {
        [_links, _nodes] = await Promise.all([API.getLinks(), API.getNodes()]);

        if (_nodes.length < 2) {
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
                <input type="search" id="links-search" class="search-input" placeholder="${t('search_placeholder')}">
                <a href="${API.exportLinksUrl()}" class="btn btn-outline" download>${t("btn_export_csv")}</a>
            </div>
            <p class="records-count" id="links-count"></p>
            <div class="table-wrapper">
                <table class="data-table">
                    <thead id="links-thead"></thead>
                    <tbody id="links-tbody"></tbody>
                </table>
            </div>
        `;

        document.getElementById("btn-new-link").onclick = () => showLinkForm(null, _nodes, reload);
        document.getElementById("links-search").addEventListener("input", e => {
            _filter = e.target.value;
            renderRows();
        });
        renderHeaders();
        renderRows();
    }

    await draw();
}

function showLinkForm(link, nodes, onSave) {
    const { t } = I18n;
    const isEdit      = link !== null;
    const area        = document.getElementById("link-form-area");
    const LINK_STATUS = [
        { value: "Activo",        label: t("status_active") },
        { value: "Inactivo",      label: t("status_inactive") },
        { value: "Mantenimiento", label: t("status_maintenance") },
    ];

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
                            ${LINK_STATUS.map(s => `<option value="${s.value}" ${isEdit && link.status === s.value ? "selected" : ""}>${s.label}</option>`).join("")}
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

    const topOffset = (document.querySelector('.topbar')?.offsetHeight ?? 56) + 16;
    window.scrollTo({ top: area.getBoundingClientRect().top + window.pageYOffset - topOffset, behavior: 'smooth' });
    area.querySelector('input')?.focus();

    const closeForm = () => { area.innerHTML = ""; document.removeEventListener("keydown", onEscape); };
    const onEscape  = (e) => { if (e.key === "Escape") closeForm(); };
    document.addEventListener("keydown", onEscape);

    document.getElementById("btn-cancel-link").onclick = closeForm;
    document.getElementById("link-form").onsubmit = async (e) => {
        e.preventDefault();
        const fd = new FormData(e.target);

        let firstInvalid = null;
        ["distance_km", "capacity_gbps"].forEach(field => {
            const input = e.target.querySelector(`[name="${field}"]`);
            const val   = parseFloat(fd.get(field));
            const bad   = isNaN(val) || val <= 0;
            input.style.borderColor = bad ? "var(--danger)" : "";
            if (bad) {
                firstInvalid = firstInvalid ?? input;
                input.addEventListener("input", () => { input.style.borderColor = ""; }, { once: true });
            }
        });
        if (firstInvalid) { firstInvalid.focus(); return; }

        const body = {
            origin_node_id:      +fd.get("origin_node_id"),
            destination_node_id: +fd.get("destination_node_id"),
            distance_km:         +fd.get("distance_km"),
            capacity_gbps:       +fd.get("capacity_gbps"),
            status:              fd.get("status"),
            name:                fd.get("name") || null,
        };
        const label = body.name ? `"${body.name}" ` : '';
        try {
            if (isEdit) {
                await API.updateLink(link.id, body);
                showToast(`${label}${t("msg_link_updated")}`);
            } else {
                await API.createLink(body);
                showToast(`${label}${t("msg_link_created")}`);
            }
            closeForm();
            onSave();
        } catch (err) {
            document.getElementById("link-error").textContent = err.message;
        }
    };
}
