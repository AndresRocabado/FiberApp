async function renderReports(container) {
    const { t } = I18n;
    container.innerHTML = `<div class="loading">...</div>`;

    const report = await API.getReport();

    container.innerHTML = `
        <h1 class="page-title">${t("reports_title")}</h1>

        <h2 class="section-title">${t("reports_summary")}</h2>
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
                <span class="metric-value">${report.total_fiber_km.toFixed(2)} km</span>
            </div>
            <div class="metric-card accent">
                <span class="metric-label">${t("metric_active_links")}</span>
                <span class="metric-value">${report.active_links}</span>
            </div>
            <div class="metric-card danger">
                <span class="metric-label">${t("metric_inactive_links")}</span>
                <span class="metric-value">${report.inactive_links}</span>
            </div>
            <div class="metric-card warning">
                <span class="metric-label">${t("metric_maintenance")}</span>
                <span class="metric-value">${report.maintenance_links}</span>
            </div>
        </div>

        <div class="section-divider"></div>

        <h2 class="section-title">${t("report_nodes_by_city")}</h2>
        <div class="table-wrapper">
            <table class="data-table">
                <thead>
                    <tr>
                        <th>${t("lbl_city")}</th>
                        <th>${t("col_city_count")}</th>
                    </tr>
                </thead>
                <tbody>
                    ${Object.entries(report.nodes_by_city)
                        .sort((a, b) => b[1] - a[1])
                        .map(([city, count]) => `
                            <tr>
                                <td>${city}</td>
                                <td>${count}</td>
                            </tr>`).join("")
                    }
                </tbody>
            </table>
        </div>

        <div class="section-divider"></div>

        <h2 class="section-title">${t("report_export")}</h2>
        <div class="export-buttons">
            <a href="${API.exportNodesUrl()}"  class="btn btn-outline" download>${t("btn_export_nodes")}</a>
            <a href="${API.exportLinksUrl()}"  class="btn btn-outline" download>${t("btn_export_links")}</a>
            <a href="${API.exportReportUrl()}" class="btn btn-outline" download>${t("btn_export_report")}</a>
        </div>
    `;
}
