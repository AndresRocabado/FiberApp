const API = (() => {
    async function send(method, path, body = null) {
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
        return res;
    }

    async function request(method, path, body = null) {
        const res = await send(method, path, body);
        if (res.status === 204) return null;
        const data = await res.json();
        if (!res.ok) throw new Error(data.detail ?? "Error");
        return data;
    }

    // Plain <a href> downloads can't send the Authorization header, so fetch the file and save it as a blob
    async function download(path) {
        const res = await send("GET", path);
        if (!res.ok) {
            const data = await res.json().catch(() => ({}));
            throw new Error(data.detail ?? "Error");
        }
        const match    = /filename="?([^";]+)"?/.exec(res.headers.get("Content-Disposition") ?? "");
        const url      = URL.createObjectURL(await res.blob());
        const a        = document.createElement("a");
        a.href         = url;
        a.download     = match ? match[1] : "export.csv";
        a.click();
        URL.revokeObjectURL(url);
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

        // Exports — kind is "nodes", "links" or "reports"
        exportCsv:   (kind)       => download(`/${kind}/export/csv`),
    };
})();
