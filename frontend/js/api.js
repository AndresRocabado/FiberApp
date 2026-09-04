const API = (() => {
    async function request(method, path, body = null) {
        const opts = {
            method,
            headers: { "Content-Type": "application/json" },
        };
        const token = localStorage.getItem("token");
        if (token) opts.headers["Authorization"] = `Bearer ${token}`;
        if (body !== null) opts.body = JSON.stringify(body);

        const res = await fetch(`/api${path}`, opts);

        if (res.status === 401) {
            localStorage.removeItem("token");
            document.getElementById("login-overlay").hidden = false;
            document.getElementById("page-content").innerHTML = "";
            throw new Error("Sesión expirada. Iniciá sesión nuevamente.");
        }

        if (res.status === 204) return null;
        const data = await res.json();
        if (!res.ok) throw new Error(data.detail ?? "Error");
        return data;
    }

    return {
        // Auth
        login: (body) => fetch("/api/auth/login", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(body),
        }).then(async res => {
            const data = await res.json();
            if (!res.ok) throw new Error(data.detail ?? "Error");
            return data;
        }),

        // Nodes
        getNodes:    ()           => request("GET",    "/nodes"),
        getCities:   ()           => request("GET",    "/nodes/cities"),
        getNode:     (id)         => request("GET",    `/nodes/${id}`),
        createNode:  (body)       => request("POST",   "/nodes", body),
        updateNode:  (id, body)   => request("PUT",    `/nodes/${id}`, body),
        deleteNode:  (id)         => request("DELETE", `/nodes/${id}`),

        // Links
        getLinks:    ()           => request("GET",    "/links"),
        getLink:     (id)         => request("GET",    `/links/${id}`),
        createLink:  (body)       => request("POST",   "/links", body),
        updateLink:  (id, body)   => request("PUT",    `/links/${id}`, body),
        deleteLink:  (id)         => request("DELETE", `/links/${id}`),

        // Trash
        getDeletedNodes:  ()   => request("GET", "/nodes/deleted"),
        restoreNode:      (id) => request("PUT", `/nodes/${id}/restore`),
        getDeletedLinks:  ()   => request("GET", "/links/deleted"),
        restoreLink:      (id) => request("PUT", `/links/${id}/restore`),

        // Reports
        getReport:   ()           => request("GET",    "/reports"),

        // Exports (direct download links)
        exportNodesUrl:  () => "/api/nodes/export/csv",
        exportLinksUrl:  () => "/api/links/export/csv",
        exportReportUrl: () => "/api/reports/export/csv",
    };
})();
