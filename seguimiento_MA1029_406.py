# =====================================================
# DASHBOARD DE SEGUIMIENTO DE COMPETENCIAS
# VERSIÓN FINAL – STREAMLIT CLOUD SAFE
# =====================================================

import streamlit as st
import pandas as pd
import os

# =====================================================
# CONFIGURACIÓN GENERAL
# =====================================================
DATA_EST = "estudiantes.csv"
DATA_ACT = "actividades.csv"

COMPETENCIAS = ["SING0101", "SING0301", "SEG0603"]
ELEMENTOS = 5
NIVELES = ["No aplica", "Incipiente", "Básico", "Sólido", "Destacado"]
VALORES = {"Incipiente": 0, "Básico": 1, "Sólido": 2, "Destacado": 3}
ACTIVIDADES = [f"A{i+1}" for i in range(8)]

# =====================================================
# FUNCIONES
# =====================================================
def cargar_csv(path, columnas):
    if os.path.exists(path):
        return pd.read_csv(path)
    return pd.DataFrame(columns=columnas)

def guardar_csv(df, path):
    df.to_csv(path, index=False)

# =====================================================
# CARGA DE DATOS
# =====================================================
df_est = cargar_csv(DATA_EST, ["Estudiante", "Grupo"])

columnas_act = ["Estudiante", "Grupo", "Actividad"] + [
    f"{c}_E{e}" for c in COMPETENCIAS for e in range(1, ELEMENTOS + 1)
]
df_act = cargar_csv(DATA_ACT, columnas_act)

# =====================================================
# INTERFAZ
# =====================================================
st.title("📊 Seguimiento de Competencias")

menu = st.sidebar.radio(
    "Menú",
    ["Registrar Estudiante", "Captura Actividad", "Seguimiento de Logro", "Cierre de Semestre"]
)

# =====================================================
# REGISTRAR ESTUDIANTE
# =====================================================
if menu == "Registrar Estudiante":
    st.header("Registrar Estudiante")

    grupo = st.text_input("Grupo")
    estudiante = st.text_input("Nombre del estudiante")

    if st.button("Registrar"):
        if grupo and estudiante:
            df_est = pd.concat(
                [df_est, pd.DataFrame([[estudiante, grupo]], columns=df_est.columns)],
                ignore_index=True
            )
            guardar_csv(df_est, DATA_EST)
            st.success("Estudiante registrado")
        else:
            st.warning("Completa todos los campos")

    if not df_est.empty:
        grupo_sel = st.selectbox("Grupo", sorted(df_est["Grupo"].unique()))
        st.dataframe(df_est[df_est["Grupo"] == grupo_sel])

# =====================================================
# CAPTURA DE ACTIVIDAD
# =====================================================
elif menu == "Captura Actividad":
    st.header("Captura de Actividad")

    if df_est.empty:
        st.warning("Primero registra estudiantes")
    else:
        grupo = st.selectbox("Grupo", sorted(df_est["Grupo"].unique()))
        estudiantes = df_est[df_est["Grupo"] == grupo]["Estudiante"].tolist()
        estudiante = st.selectbox("Estudiante", estudiantes)
        actividad = st.selectbox("Actividad", ACTIVIDADES)

        registro = {"Estudiante": estudiante, "Grupo": grupo, "Actividad": actividad}

        for c in COMPETENCIAS:
            st.subheader(c)
            for e in range(1, ELEMENTOS + 1):
                registro[f"{c}_E{e}"] = st.selectbox(
                    f"Elemento {e}", NIVELES, key=f"{c}{e}"
                )

        if st.button("Guardar actividad"):
            df_act = pd.concat([df_act, pd.DataFrame([registro])], ignore_index=True)
            guardar_csv(df_act, DATA_ACT)
            st.success("Actividad guardada")

# =====================================================
# SEGUIMIENTO DE LOGRO (🔥 ZONA CORREGIDA)
# =====================================================
elif menu == "Seguimiento de Logro":
    st.header("Seguimiento de Logro")

    if df_act.empty:
        st.info("No hay actividades registradas")
    else:
        grupo = st.selectbox("Grupo", sorted(df_est["Grupo"].unique()))
        estudiantes = df_est[df_est["Grupo"] == grupo]["Estudiante"].tolist()
        estudiante = st.selectbox("Estudiante", ["Todos"] + estudiantes)

        df_f = df_act[df_act["Grupo"] == grupo]
        if estudiante != "Todos":
            df_f = df_f[df_f["Estudiante"] == estudiante]

        st.subheader("Tabla completa")
        st.dataframe(df_f)

        # 🔥 DESCARGA SEGURA EN CSV
        csv = df_f.to_csv(index=False).encode("utf-8")

        st.download_button(
            "⬇️ Descargar reporte (CSV – Excel compatible)",
            data=csv,
            file_name="seguimiento_competencias.csv",
            mime="text/csv"
        )

# =====================================================
# CIERRE DE SEMESTRE
# =====================================================
elif menu == "Cierre de Semestre":
    st.header("Cierre de Semestre")

    opcion = st.radio(
        "Acción",
        ["Borrar TODO", "Borrar grupo", "Borrar estudiante"]
    )

    if opcion == "Borrar TODO" and st.button("Confirmar"):
        df_est = df_est.iloc[0:0]
        df_act = df_act.iloc[0:0]
        guardar_csv(df_est, DATA_EST)
        guardar_csv(df_act, DATA_ACT)
        st.success("Sistema reiniciado")

    elif opcion == "Borrar grupo":
        grupo = st.selectbox("Grupo", df_est["Grupo"].unique())
        if st.button("Borrar grupo"):
            df_est = df_est[df_est["Grupo"] != grupo]
            df_act = df_act[df_act["Grupo"] != grupo]
            guardar_csv(df_est, DATA_EST)
            guardar_csv(df_act, DATA_ACT)
            st.success("Grupo eliminado")

    elif opcion == "Borrar estudiante":
        estudiante = st.selectbox("Estudiante", df_est["Estudiante"].unique())
        if st.button("Borrar estudiante"):
            df_est = df_est[df_est["Estudiante"] != estudiante]
            df_act = df_act[df_act["Estudiante"] != estudiante]
            guardar_csv(df_est, DATA_EST)
            guardar_csv(df_act, DATA_ACT)
            st.success("Estudiante eliminado")
