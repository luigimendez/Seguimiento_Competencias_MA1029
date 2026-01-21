import streamlit as st
import pandas as pd
import os
from io import BytesIO
from fpdf import FPDF

# ---------------- CONFIGURACIÓN GENERAL ----------------
DATA_EST = "estudiantes.csv"
DATA_ACT = "actividades.csv"

COMPETENCIAS = ["SING0101", "SING0301", "SEG0603"]
ELEMENTOS = 5
NIVELES = ["No aplica", "Incipiente", "Básico", "Sólido", "Destacado"]
VALORES = {"Incipiente": 0, "Básico": 1, "Sólido": 2, "Destacado": 3}
ACTIVIDADES = [f"A{i+1}" for i in range(8)]

# ---------------- FUNCIONES BASE ----------------
def cargar_csv(path, cols):
    if os.path.exists(path):
        return pd.read_csv(path)
    return pd.DataFrame(columns=cols)

def guardar_csv(df, path):
    df.to_csv(path, index=False)

def calcular_porcentaje(df_est, competencia):
    total, maximo = 0, 0
    for _, row in df_est.iterrows():
        for e in range(1, ELEMENTOS + 1):
            val = row[f"{competencia}_E{e}"]
            if val != "No aplica":
                total += VALORES[val]
                maximo += 3
    return round((total / maximo) * 100, 2) if maximo > 0 else 0

# ---------------- PDF MULTIPÁGINA ----------------
def generar_pdf_tabla(df, titulo):
    pdf = FPDF(orientation="L", unit="mm", format="A4")
    pdf.set_auto_page_break(auto=True, margin=10)
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 14)
    pdf.cell(0, 10, titulo, ln=True, align="C")
    pdf.ln(4)
    pdf.set_font("Helvetica", size=7)

    col_width = 277 / len(df.columns)

    for col in df.columns:
        pdf.multi_cell(col_width, 6, col, border=1, align="C", ln=3)
    pdf.ln()

    for _, row in df.iterrows():
        for item in row:
            pdf.multi_cell(col_width, 6, str(item), border=1, align="C", ln=3)
        pdf.ln()

    buffer = BytesIO()
    pdf.output(buffer)
    buffer.seek(0)
    return buffer

# ---------------- CARGA DE DATOS ----------------
df_est = cargar_csv(DATA_EST, ["Estudiante", "Grupo"])
df_act_cols = ["Estudiante", "Grupo", "Actividad"] + [
    f"{c}_E{e}" for c in COMPETENCIAS for e in range(1, ELEMENTOS + 1)
]
df_act = cargar_csv(DATA_ACT, df_act_cols)

# ---------------- INTERFAZ ----------------
st.title("📊 Dashboard de Seguimiento de Competencias")

seccion = st.sidebar.radio(
    "Secciones",
    ["Registrar Estudiante", "Captura Actividad", "Seguimiento de Logro", "Cierre de Semestre"]
)

# =====================================================
# 1️⃣ REGISTRAR ESTUDIANTE
# =====================================================
if seccion == "Registrar Estudiante":
    st.header("Registrar Estudiante")

    grupo = st.text_input("Grupo")
    estudiante = st.text_input("Nombre del estudiante")

    if st.button("Registrar"):
        if grupo and estudiante:
            nuevo = pd.DataFrame([[estudiante, grupo]], columns=df_est.columns)
            df_est = pd.concat([df_est, nuevo], ignore_index=True)
            guardar_csv(df_est, DATA_EST)
            st.success("Estudiante registrado correctamente")

    st.subheader("Listado por grupo")
    grupo_sel = st.selectbox("Selecciona grupo", sorted(df_est["Grupo"].unique()))
    st.dataframe(df_est[df_est["Grupo"] == grupo_sel])

# =====================================================
# 2️⃣ CAPTURA ACTIVIDAD
# =====================================================
elif seccion == "Captura Actividad":
    st.header("Captura de Actividad")

    grupo = st.selectbox("Grupo", sorted(df_est["Grupo"].unique()))
    estudiantes = df_est[df_est["Grupo"] == grupo]["Estudiante"].tolist()
    estudiante = st.selectbox("Estudiante", estudiantes)
    actividad = st.selectbox("Actividad", ACTIVIDADES)

    registro = {"Estudiante": estudiante, "Grupo": grupo, "Actividad": actividad}

    for c in COMPETENCIAS:
        st.subheader(f"Competencia {c}")
        for e in range(1, ELEMENTOS + 1):
            registro[f"{c}_E{e}"] = st.selectbox(
                f"Elemento {e}", NIVELES, key=f"{c}_{e}"
            )

    if st.button("Guardar actividad"):
        df_act = pd.concat([df_act, pd.DataFrame([registro])], ignore_index=True)
        guardar_csv(df_act, DATA_ACT)
        st.success("Actividad guardada")

# =====================================================
# 3️⃣ SEGUIMIENTO DE LOGRO
# =====================================================
elif seccion == "Seguimiento de Logro":
    st.header("Seguimiento de Logro")

    grupo = st.selectbox("Grupo", sorted(df_est["Grupo"].unique()))
    estudiantes = df_est[df_est["Grupo"] == grupo]["Estudiante"].tolist()
    estudiante = st.selectbox("Estudiante", ["Todos"] + estudiantes)

    df_filtrado = df_act[df_act["Grupo"] == grupo]
    if estudiante != "Todos":
        df_filtrado = df_filtrado[df_filtrado["Estudiante"] == estudiante]

    st.subheader("Tabla completa de evidencias")
    st.dataframe(df_filtrado)

    st.subheader("Exportaciones")
    excel_buffer = BytesIO()
    df_filtrado.to_excel(excel_buffer, index=False)
    excel_buffer.seek(0)

    st.download_button(
        "⬇️ Descargar Excel",
        data=excel_buffer,
        file_name="seguimiento.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

    pdf_buffer = generar_pdf_tabla(df_filtrado, "Seguimiento de Logro")
    st.download_button(
        "📄 Descargar PDF",
        data=pdf_buffer,
        file_name="seguimiento.pdf",
        mime="application/pdf"
    )

# =====================================================
# 4️⃣ CIERRE DE SEMESTRE
# =====================================================
elif seccion == "Cierre de Semestre":
    st.header("⚠️ Cierre de Semestre")

    opcion = st.radio(
        "Tipo de borrado",
        ["Borrar TODO", "Borrar un grupo", "Borrar un estudiante"]
    )

    if opcion == "Borrar TODO" and st.button("Confirmar borrado total"):
        df_est = df_est.iloc[0:0]
        df_act = df_act.iloc[0:0]
        guardar_csv(df_est, DATA_EST)
        guardar_csv(df_act, DATA_ACT)
        st.success("Todo eliminado. Listo para nuevo semestre.")

    elif opcion == "Borrar un grupo":
        grupo = st.selectbox("Grupo", df_est["Grupo"].unique())
        if st.button("Borrar grupo"):
            df_est = df_est[df_est["Grupo"] != grupo]
            df_act = df_act[df_act["Grupo"] != grupo]
            guardar_csv(df_est, DATA_EST)
            guardar_csv(df_act, DATA_ACT)
            st.success("Grupo eliminado")

    elif opcion == "Borrar un estudiante":
        estudiante = st.selectbox("Estudiante", df_est["Estudiante"].unique())
        if st.button("Borrar estudiante"):
            df_est = df_est[df_est["Estudiante"] != estudiante]
            df_act = df_act[df_act["Estudiante"] != estudiante]
            guardar_csv(df_est, DATA_EST)
            guardar_csv(df_act, DATA_ACT)
            st.success("Estudiante eliminado")
