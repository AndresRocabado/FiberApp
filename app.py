import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

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
        "ID":     n.id,
        "Nombre": n.name,
        "Ciudad": n.city,
        "Tipo":   n.node_type.value,
        "Estado": n.status.value,
        "Creado": n.created_at,
    } for n in nodes])


def links_to_df(links):
    if not links:
        return pd.DataFrame()
    return pd.DataFrame([{
        "ID":              lnk.id,
        "Nombre":          lnk.name or "",
        "Origen":          lnk.origin_node_name or lnk.origin_node_id,
        "Destino":         lnk.destination_node_name or lnk.destination_node_id,
        "Distancia (km)":  lnk.distance_km,
        "Capacidad (Gbps)": lnk.capacity_gbps,
        "Estado":          lnk.status.value,
        "Creado":          lnk.created_at,
    } for lnk in links])


def _link_label(lnk) -> str:
    route = f"{lnk.origin_node_name} -> {lnk.destination_node_name}"
    if lnk.name:
        return f"{lnk.id} - {lnk.name} ({route})"
    return f"{lnk.id} - {route}"


def _node_label(node):
    return f"{node.id} - {node.name} ({node.city})"


# ---------------------------------------------------------------------------
# Sidebar navigation
# ---------------------------------------------------------------------------

st.sidebar.title("Fiber Network System")
st.sidebar.markdown("---")
page = st.sidebar.radio(
    "Navegacion",
    ["Dashboard", "Gestion de Nodos", "Gestion de Enlaces", "Reportes"],
)
st.sidebar.markdown("---")
st.sidebar.caption("Fiber Network Management v1.0")


# ---------------------------------------------------------------------------
# Dashboard
# ---------------------------------------------------------------------------

def page_dashboard():
    st.title("Dashboard - Fiber Network")

    report = report_service.generate_report()

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Nodos",       report.total_nodes)
    col2.metric("Total Enlaces",     report.total_links)
    col3.metric("Fibra Total (km)",  f"{report.total_fiber_km:.2f}")
    col4.metric("Enlaces Activos",   report.active_links)

    st.markdown("---")

    col_left, col_right = st.columns(2)

    with col_left:
        st.subheader("Nodos por Ciudad")
        if report.nodes_by_city:
            df = pd.DataFrame(
                list(report.nodes_by_city.items()),
                columns=["Ciudad", "Nodos"],
            )
            st.bar_chart(df.set_index("Ciudad"))
        else:
            st.info("Sin datos de nodos")

    with col_right:
        st.subheader("Estado de Enlaces")
        status_data = {
            "Activo":        report.active_links,
            "Inactivo":      report.inactive_links,
            "Mantenimiento": report.maintenance_links,
        }
        df = pd.DataFrame(
            [(k, v) for k, v in status_data.items() if v > 0],
            columns=["Estado", "Cantidad"],
        )
        if not df.empty:
            st.bar_chart(df.set_index("Estado"))
        else:
            st.info("Sin datos de enlaces")


# ---------------------------------------------------------------------------
# Nodes
# ---------------------------------------------------------------------------

def page_nodes():
    st.title("Gestion de Nodos")

    tab_list, tab_create, tab_edit, tab_delete = st.tabs(
        ["Lista", "Crear", "Editar", "Eliminar"]
    )

    with tab_list:
        nodes = node_service.get_all_nodes()
        df    = nodes_to_df(nodes)
        if not df.empty:
            st.dataframe(df, use_container_width=True, hide_index=True)
            st.download_button(
                label="Exportar CSV",
                data=export_nodes_to_csv(nodes),
                file_name="nodos.csv",
                mime="text/csv",
            )
        else:
            st.info("No hay nodos registrados. Crea uno en la pestana 'Crear'.")

    with tab_create:
        st.subheader("Crear Nuevo Nodo")

        if "create_node_msg" in st.session_state:
            st.success(st.session_state.pop("create_node_msg"))

        existing_cities = node_service.get_all_cities()
        city_opts_create = existing_cities + ["-- Escribir nueva ciudad --"]
        sel_city_create = st.selectbox(
            "Ciudad *",
            city_opts_create,
            index=len(city_opts_create) - 1 if not existing_cities else 0,
            key="create_city_sel",
        )
        if sel_city_create == "-- Escribir nueva ciudad --":
            city_create = st.text_input("Ciudad *", placeholder="Escribir nueva ciudad...", key="create_city_txt")
        else:
            city_create = sel_city_create

        with st.form("form_create_node", clear_on_submit=True):
            name      = st.text_input("Nombre *")
            node_type = st.selectbox("Tipo de Nodo", NODE_TYPES)
            status    = st.selectbox("Estado Operativo", NODE_STATUSES)
            submitted = st.form_submit_button("Crear Nodo")

        if submitted:
            try:
                node = node_service.create_node(name, city_create, node_type, status)
                st.session_state["create_node_msg"] = f"Nodo '{node.name}' creado correctamente (ID {node.id})"
                st.rerun()
            except ValueError as exc:
                st.error(str(exc))

    with tab_edit:
        st.subheader("Editar Nodo")

        if "edit_node_msg" in st.session_state:
            st.success(st.session_state.pop("edit_node_msg"))

        nodes = node_service.get_all_nodes()
        if not nodes:
            st.info("No hay nodos para editar")
        else:
            labels  = {_node_label(n): n for n in nodes}
            chosen  = st.selectbox("Seleccionar Nodo", list(labels.keys()), key="sel_edit_node")
            sel     = labels[chosen]

            existing_cities = node_service.get_all_cities()
            if sel.city not in existing_cities:
                existing_cities = [sel.city] + existing_cities
            city_opts_edit = existing_cities + ["-- Escribir nueva ciudad --"]
            default_city_idx = existing_cities.index(sel.city) if sel.city in existing_cities else 0

            sel_city_edit = st.selectbox(
                "Ciudad *",
                city_opts_edit,
                index=default_city_idx,
                key=f"edit_city_sel_{sel.id}",
            )
            if sel_city_edit == "-- Escribir nueva ciudad --":
                city_edit = st.text_input("Ciudad *", placeholder="Escribir nueva ciudad...", key=f"edit_city_txt_{sel.id}")
            else:
                city_edit = sel_city_edit

            with st.form("form_edit_node"):
                name      = st.text_input("Nombre",      value=sel.name)
                node_type = st.selectbox("Tipo de Nodo", NODE_TYPES, index=NODE_TYPES.index(sel.node_type.value))
                status    = st.selectbox("Estado",       NODE_STATUSES, index=NODE_STATUSES.index(sel.status.value))
                submitted = st.form_submit_button("Guardar Cambios")

            if submitted:
                try:
                    updated = node_service.update_node(sel.id, name, city_edit, node_type, status)
                    st.session_state["edit_node_msg"] = f"Nodo '{updated.name}' actualizado correctamente"
                    st.rerun()
                except ValueError as exc:
                    st.error(str(exc))

    with tab_delete:
        st.subheader("Eliminar Nodo")
        nodes = node_service.get_all_nodes()
        if not nodes:
            st.info("No hay nodos para eliminar")
        else:
            labels  = {_node_label(n): n.id for n in nodes}
            chosen  = st.selectbox("Seleccionar Nodo a Eliminar", list(labels.keys()), key="sel_del_node")
            st.warning("Esta accion es irreversible.")

            if st.button("Eliminar Nodo", type="primary", key="btn_del_node"):
                try:
                    node_service.delete_node(labels[chosen])
                    st.success("Nodo eliminado correctamente")
                    st.rerun()
                except Exception as exc:
                    st.error(str(exc))


# ---------------------------------------------------------------------------
# Links
# ---------------------------------------------------------------------------

def page_links():
    st.title("Gestion de Enlaces de Fibra")

    all_nodes = node_service.get_all_nodes()

    if len(all_nodes) < 2:
        st.warning(
            "Necesitas al menos 2 nodos para gestionar enlaces. "
            "Ve a 'Gestion de Nodos' primero."
        )
        return

    tab_list, tab_create, tab_edit, tab_delete = st.tabs(
        ["Lista", "Crear", "Editar", "Eliminar"]
    )

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
                label="Exportar CSV",
                data=export_links_to_csv(links),
                file_name="enlaces.csv",
                mime="text/csv",
            )
        else:
            st.info("No hay enlaces registrados. Crea uno en la pestana 'Crear'.")

    with tab_create:
        st.subheader("Crear Nuevo Enlace")
        with st.form("form_create_link", clear_on_submit=True):
            name        = st.text_input("Nombre del enlace")
            origin      = st.selectbox("Nodo Origen *",   node_labels, key="c_origin")
            destination = st.selectbox("Nodo Destino *",  node_labels, index=1, key="c_dest")
            distance    = st.number_input("Distancia (km) *",    min_value=0.01, value=1.0,  step=0.1,  format="%.2f")
            capacity    = st.number_input("Capacidad (Gbps) *",  min_value=0.01, value=10.0, step=1.0,  format="%.1f")
            status      = st.selectbox("Estado", LINK_STATUSES)
            submitted   = st.form_submit_button("Crear Enlace")

        if submitted:
            try:
                lnk = link_service.create_link(
                    node_map[origin], node_map[destination],
                    distance, capacity, status, name,
                )
                st.success(f"Enlace ID {lnk.id} creado correctamente")
            except ValueError as exc:
                st.error(str(exc))

    with tab_edit:
        st.subheader("Editar Enlace")
        links = link_service.get_all_links()
        if not links:
            st.info("No hay enlaces para editar")
        else:
            link_opts = {_link_label(lnk): lnk for lnk in links}
            chosen = st.selectbox("Seleccionar Enlace", list(link_opts.keys()), key="sel_edit_link")
            sel    = link_opts[chosen]

            orig_lbl = find_label(sel.origin_node_id)
            dest_lbl = find_label(sel.destination_node_id)

            with st.form("form_edit_link"):
                name        = st.text_input("Nombre del enlace", value=sel.name or "")
                origin      = st.selectbox("Nodo Origen",   node_labels, index=node_labels.index(orig_lbl))
                destination = st.selectbox("Nodo Destino",  node_labels, index=node_labels.index(dest_lbl))
                distance    = st.number_input("Distancia (km)",    min_value=0.01, value=float(sel.distance_km),    step=0.1,  format="%.2f")
                capacity    = st.number_input("Capacidad (Gbps)",  min_value=0.01, value=float(sel.capacity_gbps),  step=1.0,  format="%.1f")
                status      = st.selectbox("Estado", LINK_STATUSES, index=LINK_STATUSES.index(sel.status.value))
                submitted   = st.form_submit_button("Guardar Cambios")

            if submitted:
                try:
                    updated = link_service.update_link(
                        sel.id, node_map[origin], node_map[destination],
                        distance, capacity, status, name,
                    )
                    st.success(f"Enlace ID {updated.id} actualizado correctamente")
                except ValueError as exc:
                    st.error(str(exc))

    with tab_delete:
        st.subheader("Eliminar Enlace")
        links = link_service.get_all_links()
        if not links:
            st.info("No hay enlaces para eliminar")
        else:
            link_opts = {_link_label(lnk): lnk.id for lnk in links}
            chosen = st.selectbox("Seleccionar Enlace a Eliminar", list(link_opts.keys()), key="sel_del_link")
            st.warning("Esta accion es irreversible.")

            if st.button("Eliminar Enlace", type="primary", key="btn_del_link"):
                try:
                    link_service.delete_link(link_opts[chosen])
                    st.success("Enlace eliminado correctamente")
                    st.rerun()
                except Exception as exc:
                    st.error(str(exc))


# ---------------------------------------------------------------------------
# Reports
# ---------------------------------------------------------------------------

def page_reports():
    st.title("Reportes de Red")

    report = report_service.generate_report()

    st.subheader("Resumen General")
    c1, c2, c3 = st.columns(3)
    c1.metric("Total Nodos",      report.total_nodes)
    c2.metric("Total Enlaces",    report.total_links)
    c3.metric("Fibra Total (km)", f"{report.total_fiber_km:.2f} km")

    c4, c5, c6 = st.columns(3)
    c4.metric("Enlaces Activos",          report.active_links)
    c5.metric("Enlaces Inactivos",        report.inactive_links)
    c6.metric("En Mantenimiento",         report.maintenance_links)

    st.markdown("---")

    if report.nodes_by_city:
        st.subheader("Nodos por Ciudad")
        city_df = pd.DataFrame(
            list(report.nodes_by_city.items()),
            columns=["Ciudad", "Cantidad de Nodos"],
        )
        st.dataframe(city_df, use_container_width=True, hide_index=True)

    st.markdown("---")
    st.subheader("Exportar Datos")

    nodes = node_service.get_all_nodes()
    links = link_service.get_all_links()

    col_n, col_l, col_r = st.columns(3)
    with col_n:
        if nodes:
            st.download_button(
                "Exportar Nodos CSV",
                data=export_nodes_to_csv(nodes),
                file_name="nodos.csv",
                mime="text/csv",
            )
        else:
            st.info("Sin nodos")

    with col_l:
        if links:
            st.download_button(
                "Exportar Enlaces CSV",
                data=export_links_to_csv(links),
                file_name="enlaces.csv",
                mime="text/csv",
            )
        else:
            st.info("Sin enlaces")

    with col_r:
        st.download_button(
            "Exportar Reporte CSV",
            data=export_report_to_csv(report),
            file_name="reporte_red.csv",
            mime="text/csv",
        )


# ---------------------------------------------------------------------------
# Router
# ---------------------------------------------------------------------------

if page == "Dashboard":
    page_dashboard()
elif page == "Gestion de Nodos":
    page_nodes()
elif page == "Gestion de Enlaces":
    page_links()
elif page == "Reportes":
    page_reports()
