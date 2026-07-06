import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import altair as alt
import pandas as pd
import streamlit as st

from database.schema import initialize_database
from src.models.link import LinkStatus
from src.models.node import NodeType, OperationalStatus
from src.services.link_service import LinkService
from src.services.node_service import NodeService
from src.services.report_service import ReportService
from src.utils.csv_exporter import (
    export_links_to_csv,
    export_nodes_to_csv,
    export_report_to_csv,
)

initialize_database()

st.set_page_config(
    page_title="Fiber Network Management",
    page_icon="fiber_icon",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------------------------
# i18n
# ---------------------------------------------------------------------------

if "lang" not in st.session_state:
    st.session_state["lang"] = "es"

if st.session_state["lang"] == "en":
    from locales.en import STRINGS as _STRINGS
else:
    from locales.es import STRINGS as _STRINGS


def T(key: str) -> str:
    return _STRINGS.get(key, key)


# ---------------------------------------------------------------------------
# Services & constants
# ---------------------------------------------------------------------------

node_service   = NodeService()
link_service   = LinkService()
report_service = ReportService()

NODE_TYPES    = [e.value for e in NodeType]
NODE_STATUSES = [e.value for e in OperationalStatus]
LINK_STATUSES = [e.value for e in LinkStatus]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def nodes_to_df(nodes):
    if not nodes:
        return pd.DataFrame()
    return pd.DataFrame([{
        T("col_id"):      n.id,
        T("col_name"):    n.name,
        T("col_city"):    n.city,
        T("col_type"):    n.node_type.value,
        T("col_status"):  n.status.value,
        T("col_created"): n.created_at,
    } for n in nodes])


def links_to_df(links):
    if not links:
        return pd.DataFrame()
    return pd.DataFrame([{
        T("col_id"):          lnk.id,
        T("col_name"):        lnk.name or "",
        T("col_origin"):      lnk.origin_node_name or lnk.origin_node_id,
        T("col_destination"): lnk.destination_node_name or lnk.destination_node_id,
        T("col_distance"):    lnk.distance_km,
        T("col_capacity"):    lnk.capacity_gbps,
        T("col_status"):      lnk.status.value,
        T("col_created"):     lnk.created_at,
    } for lnk in links])


def _link_label(lnk) -> str:
    route = f"{lnk.origin_node_name} -> {lnk.destination_node_name}"
    if lnk.name:
        return f"{lnk.id} - {lnk.name} ({route})"
    return f"{lnk.id} - {route}"


def _status_colors() -> dict:
    return {
        T("status_active"):      "#28a745",
        T("status_inactive"):    "#dc3545",
        T("status_maintenance"): "#ffc107",
    }


def render_link_status_chart(report):
    sc         = _status_colors()
    col_status = T("chart_col_status")
    col_count  = T("chart_col_count")
    rows = [
        {col_status: T("status_active"),      col_count: report.active_links},
        {col_status: T("status_inactive"),     col_count: report.inactive_links},
        {col_status: T("status_maintenance"),  col_count: report.maintenance_links},
    ]
    df = pd.DataFrame([r for r in rows if r[col_count] > 0])
    if df.empty:
        st.info(T("chart_no_links"))
        return

    chart = (
        alt.Chart(df)
        .mark_bar()
        .encode(
            x=alt.X(col_status, sort=list(sc.keys())),
            y=col_count,
            color=alt.Color(
                col_status,
                scale=alt.Scale(
                    domain=list(sc.keys()),
                    range=list(sc.values()),
                ),
                legend=None,
            ),
        )
    )
    st.altair_chart(chart, use_container_width=True)


def _node_label(node):
    return f"{node.id} - {node.name} ({node.city})"


# ---------------------------------------------------------------------------
# Sidebar navigation
# ---------------------------------------------------------------------------

st.sidebar.title(T("app_title"))
st.sidebar.markdown("---")

lang_choice = st.sidebar.selectbox(
    T("lang_label"),
    ["Español", "English"],
    index=0 if st.session_state["lang"] == "es" else 1,
)
new_lang = "es" if lang_choice == "Español" else "en"
if new_lang != st.session_state["lang"]:
    st.session_state["lang"] = new_lang
    st.rerun()

st.sidebar.markdown("---")

_NAV_PAGES = ["dashboard", "nodes", "links", "reports"]
_nav_labels = [T("nav_dashboard"), T("nav_nodes"), T("nav_links"), T("nav_reports")]

page_idx = st.sidebar.radio(
    T("nav_label"),
    range(len(_NAV_PAGES)),
    format_func=lambda i: _nav_labels[i],
)

st.sidebar.markdown("---")
st.sidebar.caption(T("app_version"))


# ---------------------------------------------------------------------------
# Dashboard
# ---------------------------------------------------------------------------

def page_dashboard():
    st.title(T("dashboard_title"))

    report = report_service.generate_report()

    col1, col2, col3, col4 = st.columns(4)
    col1.metric(T("metric_total_nodes"),  report.total_nodes)
    col2.metric(T("metric_total_links"),  report.total_links)
    col3.metric(T("metric_total_fiber"),  f"{report.total_fiber_km:.2f}")
    col4.metric(T("metric_active_links"), report.active_links)

    st.markdown("---")

    col_left, col_right = st.columns(2)

    with col_left:
        st.subheader(T("chart_nodes_by_city"))
        if report.nodes_by_city:
            col_city  = T("chart_col_city")
            col_nodes = T("chart_col_nodes")
            df = pd.DataFrame(
                list(report.nodes_by_city.items()),
                columns=[col_city, col_nodes],
            )
            chart = (
                alt.Chart(df)
                .mark_bar()
                .encode(
                    x=alt.X(col_city, sort="-y"),
                    y=alt.Y(col_nodes, scale=alt.Scale(domainMin=0)),
                )
            )
            st.altair_chart(chart, use_container_width=True)
        else:
            st.info(T("chart_no_nodes"))

    with col_right:
        st.subheader(T("chart_link_status"))
        render_link_status_chart(report)


# ---------------------------------------------------------------------------
# Nodes
# ---------------------------------------------------------------------------

def page_nodes():
    st.title(T("nodes_title"))

    tab_list, tab_create, tab_edit, tab_delete = st.tabs([
        T("tab_list"), T("tab_create"), T("tab_edit"), T("tab_delete"),
    ])

    with tab_list:
        nodes = node_service.get_all_nodes()
        df    = nodes_to_df(nodes)
        if not df.empty:
            st.dataframe(df, use_container_width=True, hide_index=True)
            st.download_button(
                label=T("btn_export_csv"),
                data=export_nodes_to_csv(nodes),
                file_name="nodos.csv",
                mime="text/csv",
            )
        else:
            st.info(T("nodes_empty"))

    with tab_create:
        st.subheader(T("create_node_title"))

        if "create_node_msg" in st.session_state:
            st.success(st.session_state.pop("create_node_msg"))

        existing_cities  = node_service.get_all_cities()
        opt_new          = T("opt_new_city")
        city_opts_create = existing_cities + [opt_new]
        sel_city_create  = st.selectbox(
            T("lbl_city"),
            city_opts_create,
            index=len(city_opts_create) - 1 if not existing_cities else 0,
            key="create_city_sel",
        )
        if sel_city_create == opt_new:
            city_create = st.text_input(
                T("lbl_city"), placeholder=T("placeholder_new_city"), key="create_city_txt"
            )
        else:
            city_create = sel_city_create

        with st.form("form_create_node", clear_on_submit=True):
            name      = st.text_input(T("lbl_name"))
            node_type = st.selectbox(T("lbl_node_type"), NODE_TYPES)
            status    = st.selectbox(T("lbl_op_status"), NODE_STATUSES)
            submitted = st.form_submit_button(T("btn_create_node"))

        if submitted:
            try:
                node = node_service.create_node(name, city_create, node_type, status)
                st.session_state["create_node_msg"] = T("msg_node_created").format(
                    name=node.name, id=node.id
                )
                st.rerun()
            except ValueError as exc:
                st.error(str(exc))

    with tab_edit:
        st.subheader(T("edit_node_title"))

        if "edit_node_msg" in st.session_state:
            st.success(st.session_state.pop("edit_node_msg"))

        nodes = node_service.get_all_nodes()
        if not nodes:
            st.info(T("nodes_no_edit"))
        else:
            labels = {_node_label(n): n for n in nodes}
            chosen = st.selectbox(T("lbl_select_node"), list(labels.keys()), key="sel_edit_node")
            sel    = labels[chosen]

            existing_cities = node_service.get_all_cities()
            if sel.city not in existing_cities:
                existing_cities = [sel.city] + existing_cities
            opt_new        = T("opt_new_city")
            city_opts_edit = existing_cities + [opt_new]
            default_idx    = existing_cities.index(sel.city) if sel.city in existing_cities else 0

            sel_city_edit = st.selectbox(
                T("lbl_city"),
                city_opts_edit,
                index=default_idx,
                key=f"edit_city_sel_{sel.id}",
            )
            if sel_city_edit == opt_new:
                city_edit = st.text_input(
                    T("lbl_city"), placeholder=T("placeholder_new_city"), key=f"edit_city_txt_{sel.id}"
                )
            else:
                city_edit = sel_city_edit

            with st.form("form_edit_node"):
                name      = st.text_input(T("lbl_name_edit"),   value=sel.name)
                node_type = st.selectbox(T("lbl_node_type"),     NODE_TYPES,    index=NODE_TYPES.index(sel.node_type.value))
                status    = st.selectbox(T("lbl_status_edit"),   NODE_STATUSES, index=NODE_STATUSES.index(sel.status.value))
                submitted = st.form_submit_button(T("btn_save"))

            if submitted:
                try:
                    updated = node_service.update_node(sel.id, name, city_edit, node_type, status)
                    st.session_state["edit_node_msg"] = T("msg_node_updated").format(name=updated.name)
                    st.rerun()
                except ValueError as exc:
                    st.error(str(exc))

    with tab_delete:
        st.subheader(T("delete_node_title"))
        nodes = node_service.get_all_nodes()
        if not nodes:
            st.info(T("nodes_no_delete"))
        else:
            labels = {_node_label(n): n.id for n in nodes}
            chosen = st.selectbox(T("lbl_select_node_del"), list(labels.keys()), key="sel_del_node")
            st.warning(T("warn_irreversible"))

            if st.button(T("btn_delete_node"), type="primary", key="btn_del_node"):
                try:
                    node_service.delete_node(labels[chosen])
                    st.success(T("msg_node_deleted"))
                    st.rerun()
                except Exception as exc:
                    st.error(str(exc))


# ---------------------------------------------------------------------------
# Links
# ---------------------------------------------------------------------------

def page_links():
    st.title(T("links_title"))

    all_nodes = node_service.get_all_nodes()

    if len(all_nodes) < 2:
        st.warning(T("warn_need_2_nodes"))
        return

    tab_list, tab_create, tab_edit, tab_delete = st.tabs([
        T("tab_list"), T("tab_create"), T("tab_edit"), T("tab_delete"),
    ])

    node_map    = {_node_label(n): n.id for n in all_nodes}
    node_labels = list(node_map.keys())

    def find_label(node_id: int) -> str:
        for lbl, nid in node_map.items():
            if nid == node_id:
                return lbl
        return node_labels[0]

    with tab_list:
        links = link_service.get_all_links()
        df    = links_to_df(links)
        if not df.empty:
            st.dataframe(df, use_container_width=True, hide_index=True)
            st.download_button(
                label=T("btn_export_csv"),
                data=export_links_to_csv(links),
                file_name="enlaces.csv",
                mime="text/csv",
            )
        else:
            st.info(T("links_empty"))

    with tab_create:
        st.subheader(T("create_link_title"))
        with st.form("form_create_link", clear_on_submit=True):
            name        = st.text_input(T("lbl_link_name"))
            origin      = st.selectbox(T("lbl_origin_node"), node_labels, key="c_origin")
            destination = st.selectbox(T("lbl_dest_node"),   node_labels, index=1, key="c_dest")
            distance    = st.number_input(T("lbl_distance"), min_value=0.01, value=1.0,  step=0.1,  format="%.2f")
            capacity    = st.number_input(T("lbl_capacity"), min_value=0.01, value=10.0, step=1.0,  format="%.1f")
            status      = st.selectbox(T("lbl_link_status"), LINK_STATUSES)
            submitted   = st.form_submit_button(T("btn_create_link"))

        if submitted:
            try:
                lnk = link_service.create_link(
                    node_map[origin], node_map[destination],
                    distance, capacity, status, name,
                )
                st.success(T("msg_link_created").format(id=lnk.id))
            except ValueError as exc:
                st.error(str(exc))

    with tab_edit:
        st.subheader(T("edit_link_title"))
        links = link_service.get_all_links()
        if not links:
            st.info(T("links_no_edit"))
        else:
            link_opts = {_link_label(lnk): lnk for lnk in links}
            chosen    = st.selectbox(T("lbl_select_link"), list(link_opts.keys()), key="sel_edit_link")
            sel       = link_opts[chosen]

            orig_lbl  = find_label(sel.origin_node_id)
            dest_lbl  = find_label(sel.destination_node_id)

            with st.form("form_edit_link"):
                name        = st.text_input(T("lbl_link_name_edit"),   value=sel.name or "")
                origin      = st.selectbox(T("lbl_origin_node_edit"),  node_labels, index=node_labels.index(orig_lbl))
                destination = st.selectbox(T("lbl_dest_node_edit"),    node_labels, index=node_labels.index(dest_lbl))
                distance    = st.number_input(T("lbl_distance_edit"),  min_value=0.01, value=float(sel.distance_km),   step=0.1,  format="%.2f")
                capacity    = st.number_input(T("lbl_capacity_edit"),  min_value=0.01, value=float(sel.capacity_gbps), step=1.0,  format="%.1f")
                status      = st.selectbox(T("lbl_link_status"),       LINK_STATUSES, index=LINK_STATUSES.index(sel.status.value))
                submitted   = st.form_submit_button(T("btn_save"))

            if submitted:
                try:
                    updated = link_service.update_link(
                        sel.id, node_map[origin], node_map[destination],
                        distance, capacity, status, name,
                    )
                    st.success(T("msg_link_updated").format(id=updated.id))
                except ValueError as exc:
                    st.error(str(exc))

    with tab_delete:
        st.subheader(T("delete_link_title"))
        links = link_service.get_all_links()
        if not links:
            st.info(T("links_no_delete"))
        else:
            link_opts = {_link_label(lnk): lnk.id for lnk in links}
            chosen    = st.selectbox(T("lbl_select_link_del"), list(link_opts.keys()), key="sel_del_link")
            st.warning(T("warn_irreversible"))

            if st.button(T("btn_delete_link"), type="primary", key="btn_del_link"):
                try:
                    link_service.delete_link(link_opts[chosen])
                    st.success(T("msg_link_deleted"))
                    st.rerun()
                except Exception as exc:
                    st.error(str(exc))


# ---------------------------------------------------------------------------
# Reports
# ---------------------------------------------------------------------------

def page_reports():
    st.title(T("reports_title"))

    report = report_service.generate_report()

    st.subheader(T("reports_summary"))
    c1, c2, c3 = st.columns(3)
    c1.metric(T("metric_total_nodes"), report.total_nodes)
    c2.metric(T("metric_total_links"), report.total_links)
    c3.metric(T("metric_total_fiber"), f"{report.total_fiber_km:.2f} km")

    c4, c5, c6 = st.columns(3)
    c4.metric(T("metric_active_links"),    report.active_links)
    c5.metric(T("metric_inactive_links"),  report.inactive_links)
    c6.metric(T("metric_maintenance"),     report.maintenance_links)

    st.markdown("---")

    if report.nodes_by_city:
        st.subheader(T("report_nodes_by_city"))
        city_df = pd.DataFrame(
            list(report.nodes_by_city.items()),
            columns=[T("chart_col_city"), T("col_city_count")],
        )
        st.dataframe(city_df, use_container_width=True, hide_index=True)

    st.markdown("---")
    st.subheader(T("report_export"))

    nodes = node_service.get_all_nodes()
    links = link_service.get_all_links()

    col_n, col_l, col_r = st.columns(3)
    with col_n:
        if nodes:
            st.download_button(
                T("btn_export_nodes"),
                data=export_nodes_to_csv(nodes),
                file_name="nodos.csv",
                mime="text/csv",
            )
        else:
            st.info(T("report_no_nodes"))

    with col_l:
        if links:
            st.download_button(
                T("btn_export_links"),
                data=export_links_to_csv(links),
                file_name="enlaces.csv",
                mime="text/csv",
            )
        else:
            st.info(T("report_no_links"))

    with col_r:
        st.download_button(
            T("btn_export_report"),
            data=export_report_to_csv(report),
            file_name="reporte_red.csv",
            mime="text/csv",
        )


# ---------------------------------------------------------------------------
# Router
# ---------------------------------------------------------------------------

if page_idx == 0:
    page_dashboard()
elif page_idx == 1:
    page_nodes()
elif page_idx == 2:
    page_links()
elif page_idx == 3:
    page_reports()
