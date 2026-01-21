import streamlit as st
import pandas as pd
import os
from io import BytesIO

# ================= CONFIGURACIÓN =================
DATA_EST = "estudiantes.csv"
DATA_ACT = "actividades.csv"

COMPETENCIAS = ["SING0101", "SING0301", "SEG0603"]
ELEMENTOS = 5
NIVELES = ["No aplica", "Incipiente", "Básico", "Sólido", "Destacado"]
VALORES = {"Incipiente": 0, "Básico": 1, "Sólido": 2, "Destacado": 3}
ACTIVIDADES = [f"A{i+1}" for i in range(8)]

# ================= FUNCIONES =================
def cargar_csv(path, cols):
    if os.path.exists(path):
        return pd.read_csv(path)
    return pd.DataFrame(columns=cols)

def guardar_csv(df, path):
    df.to_csv(path, index=False)

def calcular_porcentaje(df_est, competencia):
    puntos, maximo = 0, 0
    for _, row in df_est.iterrows():
        for e in range(1, ELEMENTOS + 1):
            val = row[f"{competencia}_E{e}"]
            if val != "No aplica":
                puntos += VALORES[val]
                maximo += 3
    return round((puntos / maximo) * 100, 2) if maximo > 0 else 0

# ================= CARGA DATOS =================
df_est = cargar_csv(DATA_EST, ["Estudiante", "Grupo"])

cols_act = ["Estudiante", "Grupo", "Actividad"] + [
    f"{c}_E{e}" for c in COMPETENCIAS for e in range(1, ELEMENTOS + 1)
]
df_act = cargar_csv(DATA_ACT, cols_act)

# ================= INTERFAZ =================
st.title("📊 Dashboard de Seguimiento de Competencias")

menu = st.sidebar.radio(
    "Secciones",
    ["Registrar Estudiante", "Captura Actividad", "Seguimiento de Logro", "Cierre de Semestre"]
)

# =============== REGISTRAR ESTUDIANTE ===============
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

    if not df_est.empty:
        grupo_sel = st.selectbox("Grupo", sorted(df_est["Grupo"].unique()))
        st.dataframe(df_est[df_est["Grupo"] == grupo_sel])

# =============== CAPTURA ACTIVIDAD ===============
elif menu == "Captura Actividad":
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

# =============== SEGUIMIENTO ===============
elif menu == "Seguimiento de Logro":
    st.header("Seguimiento de Logro")

    grupo = st.selectbox("Grupo", sorted(df_est["Grupo"].unique()))
    estudiantes = df_est[df_est["Grupo"] == grupo]["Estudiante"].tolist()
    estudiante = st.selectbox("Estudiante", ["Todos"] + estudiantes)

    df_f = df_act[df_act["Grupo"] == grupo]
    if estudiante != "Todos":
        df_f = df_f[df_f["Estudiante"] == estudiante]

    st.subheader("Tabla completa de evidencias")
    st.dataframe(df_f)

    excel = BytesIO()
    df_f.to_excel(excel, index=False)
    excel.seek(0)

    st.download_button(
        "⬇️ Descargar Excel",
        data=excel,
        file_name="seguimiento.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

# =============== CIERRE SEMESTRE ===============
elif menu == "Cierre de Semestre":
    st.header("⚠️ Cierre de Semestre")

    opcion = st.radio(
        "Tipo de borrado",
        ["Borrar TODO", "Borrar un grupo", "Borrar un estudiante"]
    )

    if opcion == "Borrar TODO" and st.button("Confirmar"):
        df_est = df_est.iloc[0:0]
        df_act = df_act.iloc[0:0]
        guardar_csv(df_est, DATA_EST)
        guardar_csv(df_act, DATA_ACT)
        st.success("Sistema listo para nuevo semestre")

    elif opcion == "Borrar un grupo":
        grupo = st.selectbox("Grupo", df_est["Grupo"].unique())
        if st.button("Borrar grupo"):
            df_est = df_est[df_est["Grupo"] != grupo]
            df_act = df_act[df_act["Grupo"] != grupo]
            guardar_csv(df_est, DATA_EST)
            guardar_csv(df_act, DATA_ACT)
            st.success("Grupo eliminado")

    elif opcion == "Borrar un estudiante":
        est = st.selectbox("Estudiante", df_est["Estudiante"].unique())
        if st.button("Borrar estudiante"):
            df_est = df_est[df_est["Estudiante"] != est]
            df_act = df_act[df_act["Estudiante"] != est]
            guardar_csv(df_est, DATA_EST)
            guardar_csv(df_act, DATA_ACT)
            st.success("Estudiante eliminado")
