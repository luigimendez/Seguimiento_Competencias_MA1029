# =====================================================
# DASHBOARD DE SEGUIMIENTO DE COMPETENCIAS
# Versión estable para Streamlit Cloud
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
# FUNCIONES DE APOYO
# =====================================================
def cargar_csv(path, columnas):
    """Carga un CSV si existe, si no crea uno vacío"""
    if os.path.exists(path):
        return pd.read_csv(path)
    return pd.DataFrame(columns=columnas)

def guardar_csv(df, path):
    """Guarda DataFrame en CSV"""
    df.to_csv(path, index=False)

def calcular_porcentaje(df_est, competencia):
    """
    Calcula el porcentaje de logro por competencia
    IGNORA completamente los valores 'No aplica'
    """
    puntos = 0
    maximo = 0

    for _, row in df_est.iterrows():
        for e in range(1, ELEMENTOS + 1):
            valor = row[f"{competencia}_E{e}"]
            if valor != "No aplica":
                puntos += VALORES[valor]
                maximo += 3

    return round((puntos / maximo) * 100, 2) if maximo > 0 else 0

# =====================================================
# CARGA DE DATOS (PERSISTENTES)
# =====================================================
df_est = cargar_csv(DATA_EST, ["Estudiante", "Grupo"])

columnas_act = ["Estudiante", "Grupo", "Actividad"] + [
    f"{c}_E{e}" for c in COMPETENCIAS for e in range(1, ELEMENTOS + 1)
]
df_act = cargar_csv(DATA_ACT, columnas_act)

# =====================================================
# INTERFAZ GENERAL
# =====================================================
st.title("📊 Dashboard de Seguimiento de Competencias")

menu = st.sidebar.radio(
    "Secciones",
    [
        "Registrar Estudiante",
        "Captura Actividad",
        "Seguimiento de Logro",
        "Cierre de Semestre"
    ]
)

# =====================================================
# 1️⃣ REGISTRAR ESTUDIANTE
# =====================================================
if menu == "Registrar Estudiante":
    st.header("Registrar Estudiante")

    grupo = st.text_input("Grupo")
    estudiante = st.text_input("Nombre del estudiante")

    if st.button("Registrar estudiante"):
        if grupo and estudiante:
            nuevo = pd.DataFrame([[estudiante, grupo]], columns=df_est.columns)
            df_est = pd.concat([df_est, nuevo], ignore_index=True)
            guardar_csv(df_est, DATA_EST)
            st.success("Estudiante registrado correctamente")
        else:
            st.warning("Debes ingresar grupo y nombre del estudiante")

    st.subheader("Estudiantes registrados por grupo")
    if not df_est.empty:
        grupo_sel = st.selectbox(
            "Selecciona un grupo",
            sorted(df_est["Grupo"].unique())
        )
        st.dataframe(df_est[df_est["Grupo"] == grupo_sel])

# =====================================================
# 2️⃣ CAPTURA DE ACTIVIDAD
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

        registro = {
            "Estudiante": estudiante,
            "Grupo": grupo,
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
            df_act = pd.concat([df_act, pd.DataFrame([registro])], ignore_index=True)
            guardar_csv(df_act, DATA_ACT)
            st.success("Actividad guardada correctamente")

# =====================================================
# 3️⃣ SEGUIMIENTO DE LOGRO
# =====================================================
elif menu == "Seguimiento de Logro":
    st.header("Seguimiento de Logro")

    if df_act.empty:
        st.info("Aún no hay actividades registradas")
    else:
        grupo = st.selectbox(
            "Grupo",
            sorted(df_est["Grupo"].unique())
        )

        estudiantes = df_est[df_est["Grupo"] == grupo]["Estudiante"].tolist()
        estudiante = st.selectbox(
            "Estudiante",
            ["Todos"] + estudiantes
        )

        df_f = df_act[df_act["Grupo"] == grupo]
        if estudiante != "Todos":
            df_f = df_f[df_f["Estudiante"] == estudiante]

        st.subheader("Tabla completa de evidencias")
        st.dataframe(df_f)

        # ---------- DESCARGA EN CSV ----------
        csv = df_f.to_csv(index=False).encode("utf-8")

        st.download_button(
            "⬇️ Descargar CSV (abrible en Excel)",
            data=csv,
            file_name="seguimiento_competencias.csv",
            mime="text/csv"
        )

# =====================================================
# 4️⃣ CIERRE DE SEMESTRE
# =====================================================
elif menu == "Cierre de Semestre":
    st.header("⚠️ Cierre de Semestre")

    opcion = st.radio(
        "Tipo de borrado",
        [
            "Borrar TODO (nuevo semestre)",
            "Borrar un grupo",
            "Borrar un estudiante"
        ]
    )

    if opcion == "Borrar TODO (nuevo semestre)":
        if st.button("Confirmar borrado total"):
            df_est = df_est.iloc[0:0]
            df_act = df_act.iloc[0:0]
            guardar_csv(df_est, DATA_EST)
            guardar_csv(df_act, DATA_ACT)
            st.success("Sistema limpio para un nuevo semestre")

    elif opcion == "Borrar un grupo":
        grupo = st.selectbox("Grupo", df_est["Grupo"].unique())
        if st.button("Borrar grupo"):
            df_est = df_est[df_est["Grupo"] != grupo]
            df_act = df_act[df_act["Grupo"] != grupo]
            guardar_csv(df_est, DATA_EST)
            guardar_csv(df_act, DATA_ACT)
            st.success("Grupo eliminado correctamente")

    elif opcion == "Borrar un estudiante":
        estudiante = st.selectbox("Estudiante", df_est["Estudiante"].unique())
        if st.button("Borrar estudiante"):
            df_est = df_est[df_est["Estudiante"] != estudiante]
            df_act = df_act[df_act["Estudiante"] != estudiante]
            guardar_csv(df_est, DATA_EST)
            guardar_csv(df_act, DATA_ACT)
            st.success("Estudiante eliminado correctamente")
