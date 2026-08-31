async function renderNodes(container) {
    const { t } = I18n;
    let _nodes = [], _cities = [];
    let _sortCol = null, _sortDir = 1;
    let _filter = '', _page = 1;
    const PAGE_SIZE = 20;

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
        const term = _filter.toLowerCase();
        const visible = term
            ? _nodes.filter(n => [n.name, n.city, n.node_type, n.status].some(v => v?.toLowerCase().includes(term)))
            : _nodes;
        const sorted     = sortArray(visible, _sortCol, _sortDir);
        const totalPages = Math.max(1, Math.ceil(sorted.length / PAGE_SIZE));
        _page = Math.min(_page, totalPages);
        const start    = (_page - 1) * PAGE_SIZE;
        const pageData = sorted.slice(start, start + PAGE_SIZE);

        const countEl = document.getElementById("nodes-count");
        if (countEl) {
            if (totalPages > 1) {
                countEl.textContent = `${t('records_showing')} ${sorted.length === 0 ? 0 : start + 1}–${Math.min(start + PAGE_SIZE, sorted.length)} ${t('records_of')} ${sorted.length} ${t('records_nodes')}`;
            } else {
                countEl.textContent = _filter
                    ? `${t('records_showing')} ${sorted.length} ${t('records_of')} ${_nodes.length} ${t('records_nodes')}`
                    : `${t('records_showing')} ${_nodes.length} ${t('records_nodes')}`;
            }
        }

        const paginEl = document.getElementById("nodes-pagination");
        if (paginEl) {
            paginEl.innerHTML = totalPages <= 1 ? "" : `
                <button class="btn btn-outline btn-sm" id="btn-prev-nodes" ${_page === 1 ? "disabled" : ""}>${t('btn_prev')}</button>
                <span class="page-info">${_page} / ${totalPages}</span>
                <button class="btn btn-outline btn-sm" id="btn-next-nodes" ${_page === totalPages ? "disabled" : ""}>${t('btn_next')}</button>`;
            document.getElementById("btn-prev-nodes")?.addEventListener("click", () => { _page--; renderRows(); });
            document.getElementById("btn-next-nodes")?.addEventListener("click", () => { _page++; renderRows(); });
        }

        tbody.innerHTML = pageData.length === 0
            ? `<tr><td colspan="7" class="empty-msg">${t("nodes_empty")}</td></tr>`
            : pageData.map(n => `
                <tr>
                    <td>${n.id}</td>
                    <td>${n.name}</td>
                    <td>${n.city}</td>
                    <td><span class="badge badge-${typeClass(n.node_type)}">${n.node_type}</span></td>
                    <td><span class="badge badge-${statusClass(n.status)}">${n.status}</span></td>
                    <td>${n.created_at}</td>
                    <td class="row-actions">
                        <button class="btn btn-sm btn-outline btn-edit-node" data-id="${n.id}" title="${t('btn_edit')}">✏️</button>
                        <button class="btn btn-sm btn-danger btn-delete-node" data-id="${n.id}" data-name="${n.name}" title="${t('btn_delete')}">🗑️</button>
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
                t("confirm_delete_node").replace("{name}", btn.dataset.name),
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
                <input type="search" id="nodes-search" class="search-input" placeholder="${t('search_placeholder')}">
                <a href="${API.exportNodesUrl()}" class="btn btn-outline" download>${t("btn_export_csv")}</a>
            </div>
            <p class="records-count" id="nodes-count"></p>
            <div class="table-wrapper">
                <table class="data-table">
                    <thead id="nodes-thead"></thead>
                    <tbody id="nodes-tbody"></tbody>
                </table>
            </div>
            <div id="nodes-pagination" class="pagination"></div>
        `;

        document.getElementById("btn-new-node").onclick = () => showNodeForm(null, _cities, reload);
        document.getElementById("nodes-search").addEventListener("input", debounce(e => {
            _filter = e.target.value;
            _page = 1;
            renderRows();
        }, 250));
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

    const topOffset = (document.querySelector('.topbar')?.offsetHeight ?? 56) + 16;
    window.scrollTo({ top: area.getBoundingClientRect().top + window.pageYOffset - topOffset, behavior: 'smooth' });
    area.querySelector('input')?.focus();

    const closeForm = () => { area.innerHTML = ""; document.removeEventListener("keydown", onEscape); };
    const onEscape  = (e) => { if (e.key === "Escape") closeForm(); };
    document.addEventListener("keydown", onEscape);

    document.getElementById("btn-cancel-node").onclick = closeForm;
    document.getElementById("node-form").onsubmit = async (e) => {
        e.preventDefault();
        const fd   = new FormData(e.target);

        let firstInvalid = null;
        ["name", "city"].forEach(field => {
            const input = e.target.querySelector(`[name="${field}"]`);
            const empty = !fd.get(field)?.trim();
            input.style.borderColor = empty ? "var(--danger)" : "";
            if (empty) {
                firstInvalid = firstInvalid ?? input;
                input.addEventListener("input", () => { input.style.borderColor = ""; }, { once: true });
            }
        });
        if (firstInvalid) { firstInvalid.focus(); return; }

        const body = Object.fromEntries(fd.entries());
        try {
            if (isEdit) {
                await API.updateNode(node.id, body);
                showToast(`"${body.name}" ${t("msg_node_updated")}`);
            } else {
                await API.createNode(body);
                showToast(`"${body.name}" ${t("msg_node_created")}`);
            }
            closeForm();
            onSave();
        } catch (err) {
            document.getElementById("node-error").textContent = err.message;
            if (err.message.includes("nombre") || err.message.includes("name")) {
                const nameInput = document.querySelector('#node-form input[name="name"]');
                if (nameInput) {
                    nameInput.style.borderColor = 'var(--danger)';
                    nameInput.focus();
                    nameInput.addEventListener('input', () => { nameInput.style.borderColor = ''; }, { once: true });
                }
            }
        }
    };
}
