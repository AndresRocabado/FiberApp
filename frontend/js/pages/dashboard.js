async function renderDashboard(container) {
    const { t } = I18n;
    container.innerHTML = `<div class="loading">...</div>`;

    const [report, nodes, links] = await Promise.all([API.getReport(), API.getNodes(), API.getLinks()]);

    container.innerHTML = `
        <h1 class="page-title">Dashboard</h1>

        <div class="metrics-grid">
            <div class="metric-card">
                <span class="metric-label">${t("metric_total_nodes")}</span>
                <span class="metric-value">${report.total_nodes}</span>
            </div>
            <div class="metric-card">
                <span class="metric-label">${t("metric_total_links")}</span>
                <span class="metric-value">${report.total_links}</span>
            </div>
            <div class="metric-card">
                <span class="metric-label">${t("metric_total_fiber")}</span>
                <span class="metric-value">${report.total_fiber_km.toFixed(2)}</span>
            </div>
            <div class="metric-card accent">
                <span class="metric-label">${t("metric_active_links")}</span>
                <span class="metric-value">${report.active_links}</span>
            </div>
        </div>

        ${(() => {
            const connected = new Set(links.flatMap(l => [l.origin_node_id, l.destination_node_id]));
            const isolated  = nodes.filter(n => !connected.has(n.id));
            if (!isolated.length) return "";
            return `<div class="alert alert-warning isolated-alert">
                <strong>⚠ ${t("isolated_nodes_title")}:</strong> ${t("isolated_nodes_desc")}
                <ul class="isolated-list">${isolated.map(n => `<li>${n.name} <span class="isolated-city">(${n.city})</span></li>`).join("")}</ul>
            </div>`;
        })()}

        <div class="charts-grid">
            <div class="chart-card">
                <h2>${t("chart_nodes_by_city")}</h2>
                <canvas id="cityChart"></canvas>
            </div>
            <div class="chart-card">
                <h2>${t("chart_link_status")}</h2>
                <canvas id="statusChart"></canvas>
            </div>
        </div>
    `;

    // Nodes by city bar chart
    const cityLabels  = Object.keys(report.nodes_by_city);
    const cityValues  = Object.values(report.nodes_by_city);
    new Chart(document.getElementById("cityChart"), {
        type: "bar",
        data: {
            labels: cityLabels,
            datasets: [{
                data: cityValues,
                backgroundColor: "#4f8ef7",
                borderRadius: 6,
            }],
        },
        options: {
            plugins: { legend: { display: false } },
            scales: { y: { beginAtZero: true, ticks: { stepSize: 1 } } },
        },
    });

    // Link status doughnut chart
    const statusColors = {
        [t("status_active")]:      "#28a745",
        [t("status_inactive")]:    "#dc3545",
        [t("status_maintenance")]: "#ffc107",
    };
    new Chart(document.getElementById("statusChart"), {
        type: "doughnut",
        data: {
            labels: Object.keys(statusColors),
            datasets: [{
                data: [report.active_links, report.inactive_links, report.maintenance_links],
                backgroundColor: Object.values(statusColors),
                borderWidth: 2,
            }],
        },
        options: {
            plugins: { legend: { position: "bottom" } },
            cutout: "65%",
        },
    });
}
