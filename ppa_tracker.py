import os
from datetime import date
import pandas as pd
import plotly.express as px
import streamlit as st

# --- Configuración de página ---
st.set_page_config(page_title="Seguimiento PPA", layout="wide")

# ================================
# 🧩 SISTEMA DE LOGIN BÁSICO
# ================================
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    st.title("🔐 Iniciar sesión")
    user = st.text_input("Usuario")
    pwd = st.text_input("Contraseña", type="password")

    if st.button("Entrar"):
        if user == "admin" and pwd == "1234":
            st.session_state.logged_in = True
            try:
                st.rerun()
            except AttributeError:
                st.experimental_rerun()
        else:
            st.error("Usuario o contraseña incorrectos.")
    st.stop()

# ================================
# 🚪 BOTÓN CERRAR SESIÓN
# ================================
col_logout = st.columns([9, 1])[1]
with col_logout:
    if st.button("🚪 Cerrar sesión"):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.success("✅ Sesión cerrada correctamente.")
        st.stop()

# ================================
# 📊 APLICACIÓN PRINCIPAL
# ================================
LEADS_FILE = "leads.csv"
OFFERS_FILE = "offers.csv"
CLIENTS_FILE = "clients.csv"
DOCS_DIR = "docs"
os.makedirs(DOCS_DIR, exist_ok=True)

def load_data(file, cols):
    if os.path.exists(file):
        df = pd.read_csv(file)
        for col in cols:
            if col not in df.columns:
                df[col] = ""
        return df
    else:
        return pd.DataFrame(columns=cols)

def save_uploaded_file(uploaded_file, entity, entity_id):
    file_path = os.path.join(DOCS_DIR, f"{entity}_{entity_id}_{uploaded_file.name}")
    with open(file_path, "wb") as f:
        f.write(uploaded_file.getbuffer())
    return file_path

def convert_df(df):
    return df.to_csv(index=False).encode("utf-8")

# --- Cargar datos ---
leads = load_data(LEADS_FILE, ["ID Lead", "ID Cliente", "Cliente", "Contacto", "Estado","Tecnologia", "Tipo PPA","Duracion",
                               "Fecha Alta", "Responsable", "Notas", "Docs"])
offers = load_data(OFFERS_FILE, ["ID Oferta", "ID Lead", "Fecha Oferta", "Precio EUR/MWh",
                                 "Volumen MWh", "Probabilidad (%)", "Estado", "Notas", "Docs"])
clients = load_data(CLIENTS_FILE, ["ID Cliente", "Nombre", "CIF/NIF", "Dirección", "Ciudad", "Provincia",
                                   "País", "Tipo", "Sector", "Notas", "Docs"])

st.title("📊 Seguimiento de Leads, Ofertas y Clientes PPA")

# ================================
# 🗂️ PESTAÑAS PRINCIPALES
# ================================
tabs = st.tabs([
    "👥 Clientes / Contrapartes",
    "➕ Añadir Lead",
    "➕ Añadir Oferta",
    "✏️ Editar Lead",
    "✏️ Editar Oferta",
    "📁 Ver Leads",
    "💼 Ver Ofertas",
    "📈 Dashboard"
])

# =======================
# TAB 1: CLIENTES / CONTRAPARTES
# =======================
with tabs[0]:
    st.header("👥 Gestión de Clientes / Contrapartes")
    with st.form("form_client"):
        nombre = st.text_input("Nombre o Razón Social")
        cif = st.text_input("CIF / NIF")
        direccion = st.text_input("Dirección")
        ciudad = st.text_input("Ciudad")
        provincia = st.text_input("Provincia")
        pais = "España"  # Fijo
        tipo = st.selectbox("Tipo de Cliente", ["Productor", "Consumidor", "Trader", "Otro"])
        sector = st.text_input("Sector")
        notas = st.text_area("Notas adicionales")
        submit_client = st.form_submit_button("Guardar Cliente")

        if submit_client:
            new_id = len(clients) + 1
            clients.loc[len(clients)] = [new_id, nombre, cif, direccion, ciudad, provincia, pais, tipo, sector, notas, ""]
            clients.to_csv(CLIENTS_FILE, index=False)
            st.success(f"✅ Cliente '{nombre}' añadido correctamente.")

    st.subheader("📋 Clientes Registrados (España)")
    filtro_nombre = st.text_input("Filtrar por nombre de cliente:")
    filtro_tipo = st.selectbox("Filtrar por tipo:", ["Todos"] + clients["Tipo"].dropna().unique().tolist())

    df = clients.copy()
    if filtro_nombre:
        df = df[df["Nombre"].str.contains(filtro_nombre, case=False, na=False)]
    if filtro_tipo != "Todos":
        df = df[df["Tipo"] == filtro_tipo]
    st.dataframe(df, use_container_width=True)

    st.download_button("⬇️ Descargar Clientes (CSV)", data=convert_df(df),
                       file_name="clientes.csv", mime="text/csv")

# =======================
# TAB 2: Añadir Lead
# =======================
with tabs[1]:
    st.header("➕ Añadir Lead")
    with st.form("form_lead"):
        cliente = st.selectbox("Cliente / Contraparte", clients["Nombre"]) if not clients.empty else st.text_input(
            "Cliente (no hay clientes aún)")
        cliente_id = clients.loc[clients["Nombre"] == cliente, "ID Cliente"].values[0] if not clients.empty else ""
        contacto = st.text_input("Contacto / Email")
        estado = st.selectbox("Estado", ["Nuevo", "En curso", "Negociación", "Cerrado Ganado", "Cerrado Perdido"])
        tecnologia = st.selectbox("Tecnología", ["Solar", "Eólica", "Solar+BESS", "Otro"])
        tipo = st.selectbox("Tipo PPA", ["Fijo", "Indexado", "Virtual", "Otro"])
        duracion = st.number_input("Duración (años)", min_value=5, max_value=15, value=10, step=1)
        fecha = st.date_input("Fecha Alta", value=date.today())
        resp = st.text_input("Responsable")
        notas = st.text_area("Notas")
        submit_lead = st.form_submit_button("Guardar Lead")

        if submit_lead:
            new_id = len(leads) + 1
            leads.loc[len(leads)] = [new_id, cliente_id, cliente, contacto, estado,tecnologia,tipo,duracion, fecha, resp, notas, ""]
            leads.to_csv(LEADS_FILE, index=False)
            st.success(f"✅ Lead {new_id} añadido con éxito")

# =======================
# TAB 3: Añadir Oferta
# =======================
with tabs[2]:
    st.header("➕ Añadir Oferta")
    with st.form("form_offer"):
        id_lead = st.number_input("ID Lead asociado", min_value=1, step=1)
        fecha = st.date_input("Fecha Oferta", value=date.today())
        precio = st.number_input("Precio (EUR/MWh)", min_value=0.0, step=0.1)
        volumen = st.number_input("Volumen (MWh)", min_value=0.0, step=100.0)
        prob = st.slider("Probabilidad (%)", 0, 100, 50)
        estado = st.selectbox("Estado Oferta", ["Enviada", "En negociación", "Aprobada", "Rechazada", "Cerrada"])
        notas = st.text_area("Notas")
        submit_offer = st.form_submit_button("Guardar Oferta")

        if submit_offer:
            new_id = 100 + len(offers) + 1
            offers.loc[len(offers)] = [new_id, id_lead, fecha, precio, volumen, prob, estado, notas, ""]
            offers.to_csv(OFFERS_FILE, index=False)
            st.success(f"✅ Oferta {new_id} añadida con éxito")

# =======================
# TAB 4: Editar Lead
# =======================
with tabs[3]:
    st.header("✏️ Editar Lead")
    if not leads.empty:
        lead_id = st.selectbox("Selecciona Lead por ID", leads["ID Lead"])
        lead_row = leads[leads["ID Lead"] == lead_id].iloc[0]

        cliente = st.text_input("Cliente", value=lead_row["Cliente"], key=f"edit_cliente_{lead_id}")
        contacto = st.text_input("Contacto", value=lead_row["Contacto"], key=f"edit_contacto_{lead_id}")
        estado = st.selectbox(
            "Estado",
            ["Nuevo", "En curso", "Negociación", "Cerrado Ganado", "Cerrado Perdido"],
            index=["Nuevo", "En curso", "Negociación", "Cerrado Ganado", "Cerrado Perdido"].index(lead_row["Estado"]),
            key=f"edit_estado_{lead_id}"
        )

        tecnologia = st.selectbox(
            "Tecnología",
            ["Solar", "Eólica", "Solar+BESS", "Otro"],
            index=["Solar", "Eólica", "Solar+BESS", "Otro"].index(lead_row.get("Tecnología", "Solar"))
        )

        tipo = st.selectbox(
            "Tipo PPA",
            ["Fijo", "Indexado", "Virtual", "Otro"],
            index=["Fijo", "Indexado", "Virtual", "Otro"].index(lead_row["Tipo PPA"]),
            key=f"edit_tipo_{lead_id}"
        )

        duracion = st.number_input(
            "Duración (años)",
            min_value=5,
            max_value=15,
            value=int(lead_row.get("Duración", 10)),
            step=1,
            key=f"edit_duracion_{lead_id}"
        )

        resp = st.text_input("Responsable", value=lead_row["Responsable"], key=f"edit_resp_{lead_id}")
        notas = st.text_area("Notas", value=lead_row["Notas"], key=f"edit_notas_{lead_id}")

        # Adjuntar nuevo documento
        uploaded = st.file_uploader(
            "Adjuntar documento (Contrato/KYC/etc)",
            type=["pdf", "docx", "xlsx"],
            key=f"upload_lead_{lead_id}"
        )

        # Lista de documentos existentes
        current_docs_list = [doc for doc in str(lead_row.get("Docs", "")).split(";") if doc]
        if current_docs_list:
            docs_to_delete = st.multiselect(
                "Borrar documentos existentes",
                options=current_docs_list,
                key=f"delete_docs_lead_{lead_id}"
            )
        else:
            docs_to_delete = []

        if st.button("💾 Guardar cambios Lead", key=f"save_lead_{lead_id}"):
            # Eliminar archivos seleccionados
            for doc in docs_to_delete:
                if os.path.exists(doc):
                    os.remove(doc)
            # Actualizar columna Docs
            remaining_docs = [d for d in current_docs_list if d not in docs_to_delete]

            # Agregar nuevo archivo si se sube
            if uploaded:
                file_path = save_uploaded_file(uploaded, "lead", lead_id)
                remaining_docs.append(file_path)

            leads.loc[
                leads["ID Lead"] == lead_id,
                ["Cliente", "Contacto", "Estado", "Tipo PPA","Duracion", "Responsable", "Notas", "Docs"]
            ] = [cliente, contacto, estado, tipo, duracion, resp, notas, ";".join(remaining_docs)]

            leads.to_csv(LEADS_FILE, index=False)
            st.success("✅ Lead actualizado")


# =======================
# TAB 5: Editar Oferta
# =======================
with tabs[4]:
    st.header("✏️ Editar Oferta")
    if not offers.empty:
        offer_id = st.selectbox("Selecciona Oferta por ID", offers["ID Oferta"])
        offer_row = offers[offers["ID Oferta"] == offer_id].iloc[0]

        precio = st.number_input(
            "Precio EUR/MWh",
            value=float(offer_row["Precio EUR/MWh"]),
            key=f"edit_precio_{offer_id}"
        )
        volumen = st.number_input(
            "Volumen MWh",
            value=float(offer_row["Volumen MWh"]),
            key=f"edit_volumen_{offer_id}"
        )
        prob = st.slider(
            "Probabilidad (%)",
            0, 100,
            int(offer_row["Probabilidad (%)"]),
            key=f"edit_prob_{offer_id}"
        )
        estado = st.selectbox(
            "Estado",
            ["Enviada", "En negociación", "Aprobada", "Rechazada", "Cerrada"],
            index=["Enviada", "En negociación", "Aprobada", "Rechazada", "Cerrada"].index(offer_row["Estado"]),
            key=f"edit_estado_offer_{offer_id}"
        )
        notas = st.text_area("Notas", value=offer_row["Notas"], key=f"edit_notas_offer_{offer_id}")

        # Adjuntar nuevo documento
        uploaded_offer = st.file_uploader(
            "Adjuntar documento Oferta (Contrato, etc)",
            type=["pdf", "docx", "xlsx"],
            key=f"upload_offer_{offer_id}"
        )

        # Lista de documentos existentes
        current_docs_list = [doc for doc in str(offer_row.get("Docs", "")).split(";") if doc]
        if current_docs_list:
            docs_to_delete = st.multiselect(
                "Borrar documentos existentes",
                options=current_docs_list,
                key=f"delete_docs_offer_{offer_id}"
            )
        else:
            docs_to_delete = []

        if st.button("💾 Guardar cambios Oferta", key=f"save_offer_{offer_id}"):
            # Eliminar archivos seleccionados
            for doc in docs_to_delete:
                if os.path.exists(doc):
                    os.remove(doc)
            # Actualizar columna Docs
            remaining_docs = [d for d in current_docs_list if d not in docs_to_delete]

            # Agregar nuevo archivo si se sube
            if uploaded_offer:
                file_path = save_uploaded_file(uploaded_offer, "offer", offer_id)
                remaining_docs.append(file_path)

            offers.loc[
                offers["ID Oferta"] == offer_id,
                ["Precio EUR/MWh", "Volumen MWh", "Probabilidad (%)", "Estado", "Notas", "Docs"]
            ] = [precio, volumen, prob, estado, notas, ";".join(remaining_docs)]

            offers.to_csv(OFFERS_FILE, index=False)
            st.success("✅ Oferta actualizada")



# =======================
# TAB 7: Ver Leads
# =======================
with tabs[5]:
    st.header("📁 Ver Leads")
    filtro_cliente = st.text_input(
        "Filtrar por Cliente (nombre):",
        key="filtro_cliente_leads"
    )
    filtro_estado = st.selectbox(
        "Filtrar por Estado:",
        ["Todos"] + leads["Estado"].dropna().unique().tolist(),
        key="filtro_estado_leads"
    )

    df = leads.copy()
    if filtro_cliente:
        df = df[df["Cliente"].str.contains(filtro_cliente, case=False, na=False)]
    if filtro_estado != "Todos":
        df = df[df["Estado"] == filtro_estado]

    st.dataframe(df.drop(columns=["Docs"]), use_container_width=True)

    st.subheader("📂 Documentación adjunta por Lead")
    for _, row in df.iterrows():
        docs = [doc for doc in str(row.get("Docs", "")).split(";") if doc and os.path.exists(doc)]
        if docs:
            st.markdown(f"### 👤 {row['Cliente']}")
            for i, doc in enumerate(docs):
                file_name = os.path.basename(doc)
                with open(doc, "rb") as f:
                    st.download_button(
                        label=f"📎 Descargar {file_name}",
                        data=f.read(),
                        file_name=file_name,
                        mime="application/octet-stream",
                        key=f"download_lead_{row['ID Lead']}_{i}_{file_name}"  # key único por documento
                    )

    st.download_button(
        "⬇️ Descargar Leads (CSV)",
        data=convert_df(df),
        file_name="leads_filtrados.csv",
        mime="text/csv",
        key="download_leads_csv"
    )


# =======================
# TAB 8: Ver Ofertas
# =======================
with tabs[6]:
    st.header("💼 Ver Ofertas")

    # Filtro por estado de la oferta
    filtro_estado_offer = st.selectbox(
        "Filtrar por Estado:",
        ["Todos"] + offers["Estado"].dropna().unique().tolist(),
        key="filtro_estado_offer"
    )

    # Hacer merge para obtener nombre del cliente
    df = offers.merge(leads[["ID Lead", "Cliente"]], on="ID Lead", how="left")

    # Filtro por cliente
    clientes_disponibles = ["Todos"] + sorted(df["Cliente"].dropna().unique().tolist())
    filtro_cliente = st.selectbox(
        "Filtrar por Cliente:",
        clientes_disponibles,
        key="filtro_cliente_offer"
    )

    # Aplicar filtros
    if filtro_estado_offer != "Todos":
        df = df[df["Estado"] == filtro_estado_offer]
    if filtro_cliente != "Todos":
        df = df[df["Cliente"] == filtro_cliente]

    # Mostrar dataframe incluyendo la columna Cliente
    st.dataframe(df.drop(columns=["Docs"]), use_container_width=True)

    st.subheader("📂 Documentación adjunta por Oferta")
    for _, row in df.iterrows():
        docs = [doc for doc in str(row.get("Docs", "")).split(";") if doc and os.path.exists(doc)]
        if docs:
            st.markdown(f"### 🧾 Oferta ID {row['ID Oferta']} — Lead {row['ID Lead']} — Cliente: {row['Cliente']}")
            for i, doc in enumerate(docs):
                file_name = os.path.basename(doc)
                with open(doc, "rb") as f:
                    st.download_button(
                        label=f"📎 Descargar {file_name}",
                        data=f.read(),
                        file_name=file_name,
                        mime="application/octet-stream",
                        key=f"download_offer_{row['ID Oferta']}_{i}_{file_name}"  # key único por documento
                    )

    st.download_button(
        "⬇️ Descargar Ofertas (CSV)",
        data=convert_df(df),
        file_name="ofertas_filtradas.csv",
        mime="text/csv",
        key="download_offers_csv"
    )



# =======================
# TAB 6: Dashboard (España)
# =======================
with tabs[7]:
    st.header("📈 Dashboard con filtros")
    col1, col2, col3 = st.columns(3)
    responsable_filtro = col1.selectbox("Responsable", ["Todos"] + sorted(
        leads["Responsable"].dropna().unique().tolist())) if not leads.empty else "Todos"
    estado_filtro_lead = col2.selectbox("Estado Lead",
                                        ["Todos"] + ["Nuevo", "En curso", "Negociación", "Cerrado Ganado",
                                                     "Cerrado Perdido"])
    estado_filtro_offer = col3.selectbox("Estado Oferta",
                                         ["Todos"] + ["Enviada", "En negociación", "Aprobada", "Rechazada", "Cerrada"])
    cliente_filtro = st.text_input("Buscar Cliente (contiene):")

    leads_filtrados = leads.copy()
    if responsable_filtro != "Todos":
        leads_filtrados = leads_filtrados[leads_filtrados["Responsable"] == responsable_filtro]
    if estado_filtro_lead != "Todos":
        leads_filtrados = leads_filtrados[leads_filtrados["Estado"] == estado_filtro_lead]
    if cliente_filtro:
        leads_filtrados = leads_filtrados[leads_filtrados["Cliente"].str.contains(cliente_filtro, case=False, na=False)]

    offers_filtrados = offers.copy()
    if estado_filtro_offer != "Todos":
        offers_filtrados = offers_filtrados[offers_filtrados["Estado"] == estado_filtro_offer]
    if not leads_filtrados.empty:
        offers_filtrados = offers_filtrados[offers_filtrados["ID Lead"].isin(leads_filtrados["ID Lead"])]

    col1, col2, col3 = st.columns(3)
    col1.metric("Total Leads", len(leads_filtrados))
    col2.metric("Total Ofertas", len(offers_filtrados))
    pipeline = 0
    if not offers_filtrados.empty:
        pipeline = (offers_filtrados["Precio EUR/MWh"] * offers_filtrados["Volumen MWh"]).sum()
    col3.metric("Pipeline Estimado (€)", round(pipeline, 2))

    st.subheader("📊 Gráficos")
    if not leads_filtrados.empty:
        fig_leads = px.bar(leads_filtrados.groupby("Estado").size().reset_index(name="Cantidad"), x="Estado",
                           y="Cantidad", color="Estado")
        st.plotly_chart(fig_leads, use_container_width=True)
    if not offers_filtrados.empty:
        fig_offers = px.bar(offers_filtrados.groupby("Estado").size().reset_index(name="Cantidad"), x="Estado",
                            y="Cantidad", color="Estado")
        st.plotly_chart(fig_offers, use_container_width=True)
