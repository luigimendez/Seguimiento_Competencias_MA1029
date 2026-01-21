import streamlit as st
import pandas as pd
import os

# =============================
# CONFIGURACIÓN GENERAL
# =============================
DATA_FILE = "datos_competencias.csv"

COMPETENCIAS = ["SING0101", "SING0301", "SEG0603"]
ELEMENTOS = 5
NIVELES = ["No aplica", "Incipiente", "Básico", "Sólido", "Destacado"]
VALORES = {"Incipiente": 0, "Básico": 1, "Sólido": 2, "Destacado": 3}
ACTIVIDADES = [f"A{i+1}" for i in range(8)]

st.set_page_config(page_title="Seguimiento de Competencias", layout="wide")

# =============================
# FUNCIONES DE DATOS
# =============================
def cargar_datos():
    if os.path.exists(DATA_FILE):
        return pd.read_csv(DATA_FILE)
    else:
        columnas = ["Grupo", "Estudiante", "Actividad"]
        for c in COMPETENCIAS:
            for e in range(1, ELEMENTOS + 1):
                columnas.append(f"{c}_E{e}")
        return pd.DataFrame(columns=columnas)

def guardar_datos(df):
    df.to_csv(DATA_FILE, index=False)

def calcular_porcentaje(df_est, competencia):
    puntos = 0
    max_puntos = 0
    for _, row in df_est.iterrows():
        for e in range(1, ELEMENTOS + 1):
            val = row[f"{competencia}_E{e}"]
            if pd.notna(val) and val != "No aplica":
                puntos += VALORES[val]
                max_puntos += max(VALORES.values())
    if max_puntos == 0:
        return 0
    return round((puntos / max_puntos) * 100, 2)

def semaforo(p):
    if p >= 75:
        return "🟢 Destacado"
    elif p >= 50:
        return "🟡 Sólido"
    elif p >= 25:
        return "🟠 Básico"
    return "🔴 Incipiente"

# =============================
# CARGA DE DATOS
# =============================
df = cargar_datos()

# =============================
# MENÚ PRINCIPAL
# =============================
st.sidebar.title("Menú")
seccion = st.sidebar.radio(
    "Selecciona una sección",
    ["Registrar Estudiante", "Captura Actividad", "Seguimiento de Logro", "Cierre de Semestre"]
)

# ======================================================
# 1. REGISTRAR ESTUDIANTE
# ======================================================
if seccion == "Registrar Estudiante":
    st.header("Registrar Estudiante")

    grupo = st.text_input("Grupo")
    estudiante = st.text_input("Nombre del estudiante")

    if st.button("Registrar"):
        if grupo and estudiante:
            nueva = {
                "Grupo": grupo,
                "Estudiante": estudiante,
                "Actividad": ""
            }
            for c in COMPETENCIAS:
                for e in range(1, ELEMENTOS + 1):
                    nueva[f"{c}_E{e}"] = "No aplica"

            df = pd.concat([df, pd.DataFrame([nueva])], ignore_index=True)
            guardar_datos(df)
            st.success("Estudiante registrado correctamente")
        else:
            st.warning("Completa grupo y nombre")

    st.subheader("Estudiantes registrados")
    if not df.empty:
        grupos = sorted(df["Grupo"].dropna().unique())
        grupo_sel = st.selectbox("Selecciona grupo", grupos)

        tabla = df[df["Grupo"] == grupo_sel][["Grupo", "Estudiante"]].drop_duplicates()
        st.dataframe(tabla, use_container_width=True)

# ======================================================
# 2. CAPTURA ACTIVIDAD
# ======================================================
elif seccion == "Captura Actividad":
    st.header("Captura de Actividad")

    if df.empty:
        st.warning("Primero registra estudiantes")
    else:
        grupos = sorted(df["Grupo"].dropna().unique())
        grupo_sel = st.selectbox("Grupo", grupos)

        estudiantes = sorted(
            df[df["Grupo"] == grupo_sel]["Estudiante"].dropna().unique()
        )
        est_sel = st.selectbox("Estudiante", estudiantes)
        act_sel = st.selectbox("Actividad", ACTIVIDADES)

        datos = {"Grupo": grupo_sel, "Estudiante": est_sel, "Actividad": act_sel}

        for c in COMPETENCIAS:
            st.subheader(f"Competencia {c}")
            for e in range(1, ELEMENTOS + 1):
                datos[f"{c}_E{e}"] = st.selectbox(
                    f"Elemento {e}",
                    NIVELES,
                    key=f"{c}_{e}_{act_sel}"
                )

        if st.button("Guardar actividad"):
            existe = (
                (df["Grupo"] == grupo_sel) &
                (df["Estudiante"] == est_sel) &
                (df["Actividad"] == act_sel)
            )

            if existe.any():
                df.loc[existe, :] = pd.DataFrame([datos])
            else:
                df = pd.concat([df, pd.DataFrame([datos])], ignore_index=True)

            guardar_datos(df)
            st.success("Actividad guardada")

# ======================================================
# 3. SEGUIMIENTO DE LOGRO
# ======================================================
elif seccion == "Seguimiento de Logro":
    st.header("Seguimiento de Logro")

    if df.empty:
        st.warning("Primero registra estudiantes")
    else:
        grupos = sorted(df["Grupo"].dropna().unique())
        grupo_sel = st.selectbox("Grupo", grupos)

        df_g = df[df["Grupo"] == grupo_sel]

        estudiantes = ["Todos"] + sorted(df_g["Estudiante"].dropna().unique())
        est_sel = st.selectbox("Estudiante", estudiantes)

        if est_sel != "Todos":
            df_f = df_g[df_g["Estudiante"] == est_sel]
        else:
            df_f = df_g

        st.subheader("Tabla completa de evidencias")
        st.dataframe(df_f, use_container_width=True)

        st.subheader("Resultados por competencia")
        resultados = {}
        for c in COMPETENCIAS:
            resultados[c] = calcular_porcentaje(df_f, c)

        col1, col2 = st.columns(2)
        with col1:
            st.bar_chart(pd.DataFrame.from_dict(
                resultados, orient="index", columns=["Porcentaje"]
            ))
        with col2:
            for c, p in resultados.items():
                st.write(f"{c}: {p}% {semaforo(p)}")

        # EXPORTACIÓN SEGURA (CSV)
        csv = df_f.to_csv(index=False).encode("utf-8")
        st.download_button(
            "⬇️ Descargar tabla (CSV - Excel)",
            data=csv,
            file_name="seguimiento.csv",
            mime="text/csv"
        )

# ======================================================
# 4. CIERRE DE SEMESTRE
# ======================================================
elif seccion == "Cierre de Semestre":
    st.header("Cierre de Semestre")

    opcion = st.radio(
        "Selecciona una opción",
        ["Borrar TODO (estudiantes y actividades)", "Borrar solo un estudiante"]
    )

    if opcion == "Borrar TODO (estudiantes y actividades)":
        if st.button("⚠️ Confirmar borrado total"):
            df = df.iloc[0:0]
            guardar_datos(df)
            st.success("Todos los datos fueron eliminados")

    else:
        if not df.empty:
            grupos = sorted(df["Grupo"].dropna().unique())
            grupo_sel = st.selectbox("Grupo", grupos)

            estudiantes = sorted(
                df[df["Grupo"] == grupo_sel]["Estudiante"].dropna().unique()
            )
            est_sel = st.selectbox("Estudiante", estudiantes)

            if st.button("⚠️ Borrar estudiante"):
                df = df[~(
                    (df["Grupo"] == grupo_sel) &
                    (df["Estudiante"] == est_sel)
                )]
                guardar_datos(df)
                st.success("Estudiante eliminado")
