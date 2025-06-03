# main.py (parte 1)
import streamlit as st
import pandas as pd
import sqlite3
import os
import matplotlib.pyplot as plt
import base64
import streamlit.components.v1

DB_PATH = "db/candidatos.db"

# Crear conexión a la base de datos
def conectar_db():
    if not os.path.exists("db"):
        os.makedirs("db")
    return sqlite3.connect(DB_PATH)

# Guardar DataFrame en SQLite
def guardar_en_db(df):
    conn = conectar_db()
    df.to_sql("candidatos", conn, if_exists="replace", index=False)
    conn.close()

# Leer datos desde SQLite
def leer_desde_db():
    conn = conectar_db()
    df = pd.read_sql("SELECT * FROM candidatos", conn)
    conn.close()
    return df

# Interfaz Streamlit
st.title("Sistema de Gestión de Candidatos - Grupo Modelo")

archivo = st.file_uploader("Sube el archivo Excel", type=["xlsx"])
if not os.path.exists("db"):
    os.makedirs("db")


if archivo:
    try:
        df_raw = pd.read_excel(archivo, sheet_name=0)
        if not df_raw.empty:
            df_raw.columns = df_raw.iloc[0]
            df_raw = df_raw[1:]
            df_raw = df_raw.reset_index(drop=True)
            guardar_en_db(df_raw)
            st.success("Archivo cargado y guardado en base de datos.")
        else:
            st.warning("El archivo Excel está vacío.")
    except Exception as e:
        st.error(f"Ocurrió un error al leer el archivo Excel: {e}")

# Mostrar datos guardados
if os.path.exists(DB_PATH):
    st.subheader("Vista previa de candidatos desde la base de datos")
    df_db = leer_desde_db()
    st.dataframe(df_db)

# Crear carpeta dentro del proyecto para documentos del candidato
def crear_carpeta_candidato(id_candidato, nombre):
    carpeta_base = os.path.join(".", "documentos_candidatos")
    if not os.path.exists(carpeta_base):
        os.makedirs(carpeta_base)
    
    nombre_seguro = nombre.replace(" ", "_").replace("/", "-").upper()
    carpeta_candidato = os.path.join(carpeta_base, f"{id_candidato}-{nombre_seguro}")
    os.makedirs(carpeta_candidato, exist_ok=True)
    return carpeta_candidato

# ---------------------------
# PARTE 2: FILTROS Y BÚSQUEDA
# ---------------------------

st.subheader("🔍 Filtros de búsqueda")

# Copia segura del DataFrame desde BD
df_filtrado = df_db.copy()

# Filtro por agencia
agencias = df_filtrado["AGENCIA"].dropna().unique().tolist()
agencia_sel = st.multiselect("Filtrar por agencia:", agencias)
if agencia_sel:
    df_filtrado = df_filtrado[df_filtrado["AGENCIA"].isin(agencia_sel)]

# Filtro por puesto
puestos = df_filtrado["PUESTO"].dropna().unique().tolist()
puesto_sel = st.multiselect("Filtrar por puesto:", puestos)
if puesto_sel:
    df_filtrado = df_filtrado[df_filtrado["PUESTO"].isin(puesto_sel)]

# Filtro por estatus
estatus = df_filtrado["ESTATUS"].dropna().unique().tolist()
estatus_sel = st.multiselect("Filtrar por estatus:", estatus)
if estatus_sel:
    df_filtrado = df_filtrado[df_filtrado["ESTATUS"].isin(estatus_sel)]

# Filtro por nombre
nombre_busqueda = st.text_input("Buscar por nombre (coincidencia parcial):").strip().lower()
if nombre_busqueda:
    df_filtrado = df_filtrado[df_filtrado["NOMBRE"].str.lower().str.contains(nombre_busqueda)]

# Mostrar resultado filtrado
st.subheader("📋 Resultados filtrados")
def resaltar_filas_por_estatus(row):
    estatus = str(row["ESTATUS"]).strip().upper()
    color = "#0e1117"  # blanco por defecto

    if estatus == "CONTRATADO":
        color = "#1c7e21"  # verde claro
    elif estatus == "BAJA":
        color = "#9e2a20"  # rojo claro
    elif estatus == "NO APTO":
        color = "#7825a1"  # morado suave
    elif estatus == "EN ESPERA":
        color = "#e747bf"  # morado suave
    elif estatus == "EN BANCA":
        color = "#1a5f91"  # azul muy claro
    elif estatus == "NO CONTESTA":
        color = "#9e8628"  # amarillo claro

    return [f"background-color: {color}"] * len(row)

st.dataframe(df_filtrado.style.apply(resaltar_filas_por_estatus, axis=1))


st.subheader("✏️ Editar un candidato")

# Mostrar ID + Nombre
opciones_editar = [f"{i} - {row['NOMBRE']}" for i, row in df_db.iterrows()]
seleccion_editar = st.selectbox("✏️ Selecciona un candidato para editar:", opciones_editar)
id_seleccionado = int(seleccion_editar.split(" - ")[0])
registro = df_db.loc[id_seleccionado]

# Crear carpeta del candidato (si no existe)
carpeta_actual = crear_carpeta_candidato(id_seleccionado, registro["NOMBRE"])


with st.form("form_editar"):
    nuevo_nombre = st.text_input("Nombre", registro["NOMBRE"])
    nueva_edad = st.number_input("Edad", value=int(registro["EDAD"]), min_value=0, max_value=100)
    nuevo_telefono = st.text_input("Teléfono", registro["TELEFONO"])
    nuevo_puesto = st.text_input("Puesto", registro["PUESTO"])
    nuevo_estatus = st.text_input("Estatus", registro["ESTATUS"])

    enviar = st.form_submit_button("Guardar cambios")

if enviar:
    df_db.at[id_seleccionado, "NOMBRE"] = nuevo_nombre
    df_db.at[id_seleccionado, "EDAD"] = nueva_edad
    df_db.at[id_seleccionado, "TELEFONO"] = nuevo_telefono
    df_db.at[id_seleccionado, "PUESTO"] = nuevo_puesto
    df_db.at[id_seleccionado, "ESTATUS"] = nuevo_estatus

    guardar_en_db(df_db)
    st.success("✅ Candidato actualizado correctamente. Recarga la página para ver los cambios.")


    # -----------------------------
# 📁 Documentos del candidato
# -----------------------------
with st.expander("📁 Documentos del candidato (PDF y Word)"):
    st.markdown("Puedes subir archivos en formato `.pdf` o `.docx`. Usa los campos correspondientes.")

    # Ruta base por ID
    carpeta_actual = os.path.join(".", "documentos", str(id_seleccionado))
    os.makedirs(carpeta_actual, exist_ok=True)

    nomenclatura = {
        "MX01 - Acta": "MX01 - Acta",
        "MX02 - Clabe Interbancaria": "MX02 - Clabe Interbancaria",
        "MX03 - Comprobante Domicilio": "MX03 - Comprobante Domicilio",
        "MX04 - CURP": "MX04 - CURP",
        "MX05 - RFC": "MX05 - RFC",
        "MX06 - IMSS": "MX06 - IMSS",
        "Contrato": "Contrato"
    }

    for clave, etiqueta in nomenclatura.items():
        archivo = st.file_uploader(f"📄 Subir {etiqueta}", type=["pdf", "docx"], key=f"{clave}_{id_seleccionado}")
        if archivo:
            ruta_guardado = os.path.join(carpeta_actual, f"{clave}.{archivo.name.split('.')[-1]}")
            with open(ruta_guardado, "wb") as f:
                f.write(archivo.read())
            st.success(f"{etiqueta} cargado correctamente.")

    # Mostrar archivos ya existentes
   
        archivos_subidos = []
if os.path.exists(carpeta_actual):
    archivos_subidos = os.listdir(carpeta_actual)

    if archivos_subidos:
        st.markdown("### 📚 Documentos cargados:")
        for archivo in archivos_subidos:
            ruta = os.path.join(carpeta_actual, archivo)
            col1, col2 = st.columns([3, 1])
            with col1:
                with open(ruta, "rb") as f:
                    st.download_button(
                        label=f"⬇️ {archivo}",
                        data=f.read(),
                        file_name=archivo,
                        key=f"descarga_{archivo}"
                    )
            with col2:
                if st.button("🗑️ Eliminar", key=f"eliminar_{archivo}"):
                    os.remove(ruta)
                    st.warning(f"Archivo '{archivo}' eliminado.")
                    st.experimental_rerun()






# Mostrar ID + Nombre para borrar
opciones_borrar = [f"{i} - {row['NOMBRE']}" for i, row in df_db.iterrows()]
seleccion_borrar = st.selectbox("🗑️ Selecciona un candidato para eliminar:", opciones_borrar, key="eliminar")
id_borrar = int(seleccion_borrar.split(" - ")[0])


if st.button("Eliminar candidato"):
    df_db = df_db.drop(index=id_borrar).reset_index(drop=True)
    guardar_en_db(df_db)
    st.warning("⚠️ Candidato eliminado. Recarga la página para ver los cambios.")

with st.expander("➕ Agregar nuevo candidato"):
    with st.form("form_insertar"):
        agencia_nueva = st.text_input("Agencia")
        puesto_nuevo = st.text_input("Puesto")
        nombre_nuevo = st.text_input("Nombre completo")
        edad_nueva = st.number_input("Edad", min_value=0, max_value=100, value=25)
        telefono_nuevo = st.text_input("Teléfono")
        trabajo_anterior = st.text_input("Trabajo anterior")
        fuente_reclutamiento = st.text_input("Fuente de reclutamiento")
        entrevista = st.text_input("Entrevista")
        prueba_medica = st.text_input("Prueba médica")
        prueba_manejo = st.text_input("Prueba de manejo")
        comentarios = st.text_area("Comentarios")
        estatus = st.text_input("Estatus")
        motivo_rechazo = st.text_input("Motivo de rechazo")

        guardar_nuevo = st.form_submit_button("Agregar candidato")

if guardar_nuevo:
    nuevo = {
        "AGENCIA": agencia_nueva,
        "PUESTO": puesto_nuevo,
        "NOMBRE": nombre_nuevo,
        "EDAD": edad_nueva,
        "TELEFONO": telefono_nuevo,
        "TRABAJO ANTERIOR": trabajo_anterior,
        "FUENTE DE RECLUTAMIENTO": fuente_reclutamiento,
        "ENTREVISTA": entrevista,
        "PRUEBA MEDICA": prueba_medica,
        "PRUEBA DE MANEJO": prueba_manejo,
        "COMENTARIOS": comentarios,
        "ESTATUS": estatus,
        "MOTIVO DE RECHAZO": motivo_rechazo
    }

    df_db = pd.concat([df_db, pd.DataFrame([nuevo])], ignore_index=True)
    guardar_en_db(df_db)
    st.success("✅ Candidato agregado correctamente. Recarga la página para verlo en la lista.")

# -----------------------------
# 📊 Gráfica global (todos los datos)
# -----------------------------
st.subheader("📊 Gráfica global de estatus")

# Normalizar los estatus
df_limpio = df_db.copy()
df_limpio["ESTATUS"] = df_limpio["ESTATUS"].fillna("SIN ESTATUS").str.strip().str.upper()

# Correcciones comunes (errores y variantes)
df_limpio["ESTATUS"] = df_limpio["ESTATUS"].replace({
    "RECHAZDO": "RECHAZADO",
    "EN BANCA": "EN BANCA",
    "NO ASISTIO A CITA": "NO ASISTIÓ A CITA",
    "NO CONTESTA": "NO CONTESTÓ"
})

conteo_global = df_limpio["ESTATUS"].value_counts()

# Evitar que estatus válidos caigan en "OTROS" innecesariamente
estatus_validos = [
    "CONTRATADO", "RECHAZADO", "NO APTO", "BAJA", "EN BANCA",
    "EN PROCESO", "PENDIENTE", "NO ASISTIÓ A CITA", "NO CONTESTÓ", "SIN ESTATUS"
]

# Reetiquetar los menos comunes como "OTROS" solo si no están en lista
conteo_agrupado = conteo_global.copy()
conteo_agrupado = conteo_agrupado.rename(lambda x: x if x in estatus_validos else "OTROS")
conteo_agrupado = conteo_agrupado.groupby(conteo_agrupado.index).sum()

# Colores por estatus
colores_personalizados = {
    "CONTRATADO": "#00FF00",
    "RECHAZADO": "#FF0000",
    "NO APTO": "#ff9900",
    "BAJA": "#990000",
    "EN BANCA": "#0000FF",
    "EN PROCESO": "#9900FF",
    "PENDIENTE": "#FFFF00",
    "NO ASISTIÓ A CITA": "#ff66cc",
    "NO CONTESTÓ": "#ffcc00",
    "SIN ESTATUS": "#999999",
    "OTROS": "#cccccc"
}

colores_global = [colores_personalizados.get(est, "#cccccc") for est in conteo_agrupado.index]

# Gráfica de pastel
# Gráfica de barras horizontal con porcentajes
fig1, ax1 = plt.subplots(figsize=(8, 6))
conteo_global_sorted = conteo_global.sort_values()
total = conteo_global_sorted.sum()

# Barras horizontales
bars = ax1.barh(
    conteo_global_sorted.index,
    conteo_global_sorted.values,
    color=[colores_personalizados.get(est, "#cccccc") for est in conteo_global_sorted.index]
)

# Agregar porcentajes al final de cada barra
for bar in bars:
    width = bar.get_width()
    porcentaje = f"{(width / total) * 100:.1f}%"
    ax1.text(width + 1, bar.get_y() + bar.get_height() / 2, porcentaje, va='center')

ax1.set_xlabel("Cantidad de candidatos")
ax1.set_title("Distribución global por estatus")
plt.tight_layout()
st.pyplot(fig1)

# -----------------------------
# 📊 Gráfica filtrada (solo lo que el usuario filtró)
# -----------------------------
if not df_filtrado.empty and not df_filtrado.equals(df_db):
    st.subheader("📊 Gráfica filtrada de estatus")

    conteo_filtrado = df_filtrado["ESTATUS"].fillna("SIN ESTATUS").str.strip().str.upper().replace({
        "RECHAZDO": "RECHAZADO",
        "NO ASISTIO A CITA": "NO ASISTIÓ A CITA",
        "NO CONTESTA": "NO CONTESTÓ"
    }).value_counts()

    colores_filtrados = [colores_personalizados.get(est, "#cccccc") for est in conteo_filtrado.index]

    # Explosión suave para separar los segmentos
    explode = [0.05] * len(conteo_filtrado)

    fig2, ax2 = plt.subplots(figsize=(8, 6))  # Aumentar tamaño
    ax2.pie(
        conteo_filtrado,
        labels=conteo_filtrado.index,
        colors=colores_filtrados,
        autopct="%1.1f%%",
        startangle=90,
        explode=explode
    )
    ax2.axis("equal")
    plt.tight_layout()
    st.pyplot(fig2)


# -----------------------------
# ⚠️ Zona protegida para reiniciar base de datos
# -----------------------------
with st.expander("⚠️ Zona de reinicio de base de datos"):
    st.markdown("🔒 Esta área permite borrar todos los datos cargados. Usa con precaución.")

    contraseña = st.text_input("Ingresa la contraseña para acceder:", type="password")

    if contraseña == "1234":
        if st.button("🗑️ Borrar todos los datos"):
            try:
                conn = conectar_db()
                cursor = conn.cursor()
                cursor.execute("DELETE FROM candidatos")
                conn.commit()
                conn.close()

                st.success("✅ Todos los datos han sido eliminados correctamente.")
                st.experimental_rerun()
            except Exception as e:
                st.error(f"❌ Error al borrar datos: {e}")
    elif contraseña != "":
        st.error("❌ Contraseña incorrecta.")
