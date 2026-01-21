# =====================================================
# DASHBOARD DE SEGUIMIENTO DE COMPETENCIAS
# =====================================================

import streamlit as st
import pandas as pd
import os
from io import BytesIO

# ----- PDF -----
from reportlab.lib.pagesizes import letter, landscape
from reportlab.platypus import (
    SimpleDocTemplate, Table, TableStyle,
    Paragraph, PageBreak
)
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors

# =====================================================
# CONFIGURACIÓN GENERAL
# =====================================================

COMPETENCIAS = ["SING0101", "SING0301", "SEG0603"]
ELEMENTOS = 5
NIVELES = ["No aplica", "Incipiente", "Básico", "Sólido", "Destacado"]

VALORES = {
    "Incipiente": 0,
    "Básico": 1,
    "Sólido": 2,
    "Destacado": 3
}

ACTIVIDADES = [f"A{i+1}" for i in range(8)]

ARCH_EST = "estudiantes.csv"
ARCH_ACT = "actividades.csv"

# =====================================================
# FUNCIONES DE DATOS
# =====================================================

def cargar_estudiantes():
    if os.path.exists(ARCH_EST):
        return pd.read_csv(ARCH_EST)
    return pd.DataFrame(columns=["Estudiante", "Grupo"])

def guardar_estudiantes(df):
    df.to_csv(ARCH_EST, index=False)

def cargar_actividades():
    if os.path.exists(ARCH_ACT):
        return pd.read_csv(ARCH_ACT)

    columnas = ["Estudiante", "Grupo", "Actividad"]
    for c in COMPETENCIAS:
        for e in range(1, ELEMENTOS + 1):
            columnas.append(f"{c}_E{e}")

    return pd.DataFrame(columns=columnas)

def guardar_actividades(df):
    df.to_csv(ARCH_ACT, index=False)

# =====================================================
# CÁLCULOS (No aplica NO cuenta)
# =====================================================

def porcentaje_competencia(df, competencia):
    total = 0
    maximo = 0

    for _, row in df.iterrows():
        for e in range(1, ELEMENTOS + 1):
            val = row[f"{competencia}_E{e}"]
            if val != "No aplica":
                total += VALORES.get(val, 0)
                maximo += max(VALORES.values())

    return (total / maximo * 100) if maximo > 0 else 0

# =====================================================
# PDF COMPLETO (COLUMNAS + FILAS)
# =====================================================

def generar_pdf_tabla(df, titulo):
    buffer = BytesIO()
    page_width, page_height = landscape(letter)

    doc = SimpleDocTemplate(
        buffer,
        pagesize=(page_width, page_height),
        leftMargin=15,
        rightMargin=15,
        topMargin=20,
        bottomMargin=20
    )

    styles = getSampleStyleSheet()
    elementos = [Paragraph(f"<b>{titulo}</b>", styles["Title"])]

    data = [df.columns.tolist()] + df.values.tolist()

    num_cols = len(df.columns)
    col_width = (page_width - 30) / num_cols
    col_widths = [col_width] * num_cols

    filas_por_pagina = 18

    for i in range(0, len(data), filas_por_pagina):
        bloque = data[i:i + filas_por_pagina]

        tabla = Table(
            bloque,
            colWidths=col_widths,
            repeatRows=1
        )

        tabla.setStyle(TableStyle([
            ("GRID", (0, 0), (-1, -1), 0.4, colors.black),
            ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("FONTSIZE", (0, 0), (-1, -1), 6),
            ("TOPPADDING", (0, 0), (-1, -1), 3),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ]))

        elementos.append(tabla)
        elementos.append(PageBreak())

    doc.build(elementos)
    buffer.seek(0)
    return buffer

# =====================================================
# FUNCIONES DE BORRADO (CIERRE DE SEMESTRE)
# =====================================================

def borrar_todo():
    if os.path.exists(ARCH_EST):
        os.remove(ARCH_EST)
    if os.path.exists(ARCH_ACT):
        os.remove(ARCH_ACT)

def borrar_grupo(grupo):
    df_e = cargar_estudiantes()
    df_a = cargar_actividades()

    df_e = df_e[df_e["Grupo"] != grupo]
    df_a = df_a[df_a["Grupo"] != grupo]

    guardar_estudiantes(df_e)
    guardar_actividades(df_a)

def borrar_estudiante(nombre):
    df_e = cargar_estudiantes()
    df_a = cargar_actividades()

    df_e = df_e[df_e["Estudiante"] != nombre]
    df_a = df_a[df_a["Estudiante"] != nombre]

    guardar_estudiantes(df_e)
    guardar_actividades(df_a)

# =====================================================
# INTERFAZ STREAMLIT
# =====================================================

st.title("📊 Dashboard de Seguimiento de Competencias")

seccion = st.sidebar.radio(
    "Secciones",
    [
        "Registrar Estudiante",
        "Captura Actividad",
        "Seguimiento de Logro",
        "Cierre de Semestre"
    ]
)

df_estudiantes = cargar_estudiantes()
df_actividades = cargar_actividades()

# =====================================================
# 1️⃣ REGISTRAR ESTUDIANTE
# =====================================================

if seccion == "Registrar Estudiante":
    st.header("Registrar Estudiante")

    grupo = st.text_input("Grupo")
    estudiante = st.text_input("Nombre del estudiante")

    if st.button("Registrar estudiante"):
        if grupo and estudiante:
            df_estudiantes = pd.concat(
                [df_estudiantes, pd.DataFrame([{
                    "Grupo": grupo,
                    "Estudiante": estudiante
                }])],
                ignore_index=True
            )
            guardar_estudiantes(df_estudiantes)
            st.success("Estudiante registrado correctamente")

    if not df_estudiantes.empty:
        st.subheader("Listado por grupo")
        grupo_sel = st.selectbox(
            "Selecciona grupo",
            sorted(df_estudiantes["Grupo"].unique())
        )
        st.dataframe(df_estudiantes[df_estudiantes["Grupo"] == grupo_sel])

# =====================================================
# 2️⃣ CAPTURA DE ACTIVIDAD
# =====================================================

elif seccion == "Captura Actividad":
    st.header("Captura de Actividad")

    if df_estudiantes.empty:
        st.warning("Primero registra estudiantes")
    else:
        grupo_sel = st.selectbox(
            "Grupo",
            sorted(df_estudiantes["Grupo"].unique())
        )

        estudiantes = df_estudiantes[
            df_estudiantes["Grupo"] == grupo_sel
        ]["Estudiante"].tolist()

        estudiante = st.selectbox("Estudiante", estudiantes)
        actividad = st.selectbox("Actividad", ACTIVIDADES)

        registro = {
            "Estudiante": estudiante,
            "Grupo": grupo_sel,
            "Actividad": actividad
        }

        for c in COMPETENCIAS:
            st.subheader(f"Competencia {c}")
            for e in range(1, ELEMENTOS + 1):
                registro[f"{c}_E{e}"] = st.selectbox(
                    f"Elemento {e}",
                    NIVELES,
                    key=f"{c}_{e}"
                )

        if st.button("Guardar actividad"):
            existe = (
                (df_actividades["Estudiante"] == estudiante) &
                (df_actividades["Actividad"] == actividad)
            )

            if existe.any():
                df_actividades.loc[existe, :] = pd.DataFrame([registro])
            else:
                df_actividades = pd.concat(
                    [df_actividades, pd.DataFrame([registro])],
                    ignore_index=True
                )

            guardar_actividades(df_actividades)
            st.success("Actividad guardada correctamente")

# =====================================================
# 3️⃣ SEGUIMIENTO DE LOGRO
# =====================================================

elif seccion == "Seguimiento de Logro":
    st.header("Seguimiento de Logro")

    grupo_sel = st.selectbox(
        "Grupo",
        sorted(df_estudiantes["Grupo"].unique())
    )

    estudiantes = df_estudiantes[
        df_estudiantes["Grupo"] == grupo_sel
    ]["Estudiante"].tolist()

    estudiante_sel = st.selectbox(
        "Estudiante",
        ["Todos"] + estudiantes
    )

    if estudiante_sel == "Todos":
        df_filtro = df_actividades[df_actividades["Grupo"] == grupo_sel]
    else:
        df_filtro = df_actividades[
            (df_actividades["Grupo"] == grupo_sel) &
            (df_actividades["Estudiante"] == estudiante_sel)
        ]

    if not df_filtro.empty:
        st.subheader("Porcentaje de logro por competencia")

        resultados = {
            c: porcentaje_competencia(df_filtro, c)
            for c in COMPETENCIAS
        }

        st.bar_chart(
            pd.DataFrame.from_dict(
                resultados, orient="index", columns=["% Logro"]
            )
        )

        st.subheader("Tabla completa de evidencias")
        st.dataframe(df_filtro)

        # ---- Excel ----
        excel_buffer = BytesIO()
        with pd.ExcelWriter(excel_buffer) as writer:
            df_filtro.to_excel(writer, index=False, sheet_name="Detalle")
        excel_buffer.seek(0)

        st.download_button(
            "📥 Descargar Excel",
            data=excel_buffer,
            file_name="seguimiento_competencias.xlsx"
        )

        # ---- PDF ----
        pdf_buffer = generar_pdf_tabla(
            df_filtro,
            f"Seguimiento de Logro - Grupo {grupo_sel}"
        )

        st.download_button(
            "📄 Descargar PDF",
            data=pdf_buffer,
            file_name="seguimiento_competencias.pdf",
            mime="application/pdf"
        )
    else:
        st.info("No hay registros para mostrar")

# =====================================================
# 4️⃣ CIERRE DE SEMESTRE
# =====================================================

else:
    st.header("⚠️ Cierre de Semestre")

    opcion = st.radio(
        "Tipo de borrado",
        [
            "Borrado total (nuevo semestre)",
            "Borrar un grupo completo",
            "Borrar un estudiante específico"
        ]
    )

    if opcion == "Borrado total (nuevo semestre)":
        st.warning("Esto eliminará TODOS los datos.")
        if st.button("Confirmar borrado total"):
            borrar_todo()
            st.success("Sistema reiniciado")
            st.experimental_rerun()

    elif opcion == "Borrar un grupo completo":
        grupo = st.selectbox(
            "Grupo",
            sorted(df_estudiantes["Grupo"].unique())
        )
        if st.button("Borrar grupo"):
            borrar_grupo(grupo)
            st.success("Grupo eliminado")
            st.experimental_rerun()

    elif opcion == "Borrar un estudiante específico":
        estudiante = st.selectbox(
            "Estudiante",
            sorted(df_estudiantes["Estudiante"].unique())
        )
        if st.button("Borrar estudiante"):
            borrar_estudiante(estudiante)
            st.success("Estudiante eliminado")
            st.experimental_rerun()