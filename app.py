import os
import json
import pandas as pd
import streamlit as st
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

DB_FILE = "luz_config_actual.json"

def cargar_datos_disco():
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {
        "periodo": "SEPTIEMBRE 2026",
        "precio_unitario": 0.618,
        "cargos_fijos_globales": {"CF": 2.26, "MANT": 1.74, "AP": 60.48, "ER": 12.36, "Afianza": 0},
        "medidores": {
            "SOM": {"tipo": 1, "anterior": 0.0, "actual": 623.56, "mant_com": 0.0},
            "CIRILO": {"tipo": 0, "anterior": 678.21, "actual": 678.21, "mant_com": 0.0},
            "AGUA": {"tipo": 0, "anterior": 27420.7, "actual": 27548.3, "mant_com": 0.0},
            "MARCO": {"tipo": 2, "anterior": 20468.5, "actual": 20515.3, "mant_com": 0.0},
            "CLAUDIA": {"tipo": 0, "anterior": 21515.0, "actual": 21515.0, "mant_com": 0.0},
            "CHATO": {"tipo": 2, "anterior": 31023.5, "actual": 31222.33, "mant_com": 0.0},
            "LILIANA": {"tipo": 2, "anterior": 9129.8, "actual": 9129.8, "mant_com": 0.0},
            "HELGA": {"tipo": 1, "anterior": 1404.4, "actual": 1404.4, "mant_com": 100.0},
            "BRAN": {"tipo": 0, "anterior": 6810.7, "actual": 6810.7, "mant_com": 0.0},
            "SIU": {"tipo": 1, "anterior": 0.0, "actual": 18.57, "mant_com": 0.0},
            "EZE": {"tipo": 1, "anterior": 3414.6, "actual": 3543.5, "mant_com": 0.0},
            "QUINTA": {"tipo": 1, "anterior": 1916.79, "actual": 1936.03, "mant_com": 0.0},
            "SONIA": {"tipo": 1, "anterior": 6859.2, "actual": 6889.4, "mant_com": 0.0}
        }
    }

def guardar_datos_disco(data):
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

st.set_page_config(page_title="Control de Luz - Comunidad", layout="wide")

st.title("⚡ Cálculo de Consumo de Luz - Comunidad")

# Inicializar estados para historial de deshacer/rehacer manual
if "datos_app" not in st.session_state:
    st.session_state.datos_app = cargar_datos_disco()

if "historial_undo" not in st.session_state:
    st.session_state.historial_undo = []

if "historial_redo" not in st.session_state:
    st.session_state.historial_redo = []

def registrar_estado():
    # Guarda una copia profunda antes de un cambio importante
    import copy
    st.session_state.historial_undo.append(copy.deepcopy(st.session_state.datos_app))
    st.session_state.historial_redo.clear() # Limpiar rehacer al hacer nueva acción

datos_actuales = st.session_state.datos_app

# --- BOTONERA SUPERIOR DE CONTROL (Deshacer, Rehacer, Cierre de Mes) ---
col_ctrl1, col_ctrl2, col_ctrl3, col_ctrl4 = st.columns([1, 1, 2, 2])

with col_ctrl1:
    if st.button("↩️ Deshacer", use_container_width=True):
        if st.session_state.historial_undo:
            import copy
            st.session_state.historial_redo.append(copy.deepcopy(st.session_state.datos_app))
            st.session_state.datos_app = st.session_state.historial_undo.pop()
            st.rerun()
        else:
            st.toast("No hay acciones para deshacer.")

with col_ctrl2:
    if st.button("🔁 Rehacer", use_container_width=True):
        if st.session_state.historial_redo:
            import copy
            st.session_state.historial_undo.append(copy.deepcopy(st.session_state.datos_app))
            st.session_state.datos_app = st.session_state.historial_redo.pop()
            st.rerun()
        else:
            st.toast("No hay acciones para rehacer.")

with col_ctrl3:
    if st.button("🔄 Pasar Actual ➔ Anterior (Nuevo Mes)", use_container_width=True):
        registrar_estado()
        for nombre, vals in st.session_state.datos_app["medidores"].items():
            vals["anterior"] = vals["actual"] # El valor actual pasa a ser la nueva lectura anterior
        st.success("¡Lecturas actuales pasadas a anteriores correctamente!")
        st.rerun()

with col_ctrl4:
    if st.button("💾 Guardar Cambios en Disco", use_container_width=True):
        guardar_datos_disco(st.session_state.datos_app)
        st.success("¡Guardado permanente exitoso!")

st.markdown("---")

# Configuración general del periodo
col_p1, col_p2 = st.columns(2)
with col_p1:
    periodo_nombre = st.text_input("Periodo / Mes del Reporte", value=datos_actuales.get("periodo", "MES ACTUAL"))
with col_p2:
    precio_unitario = st.number_input("Precio Unitario por kW ($)", value=float(datos_actuales["precio_unitario"]), format="%.4f")

st.markdown("### ⚙️ Cargos Fijos Globales")
cf_cols = st.columns(5)
cargos_actualizados = {}
keys_cf = ["CF", "MANT", "AP", "ER", "Afianza"]
for i, k in enumerate(keys_cf):
    with cf_cols[i]:
        cargos_actualizados[k] = st.number_input(k, value=float(datos_actuales["cargos_fijos_globales"].get(k, 0)), format="%.4f")

st.markdown("### 📊 Lecturas de Medidores")

# Preparar DataFrame para la tabla editable
df_medidores = pd.DataFrame.from_dict(datos_actuales["medidores"], orient='index')
df_medidores.index.name = "MEDIDOR"
df_medidores.reset_index(inplace=True)

edited_df = st.data_editor(
    df_medidores, 
    num_rows="dynamic", 
    use_container_width=True, 
    key="editor_medidores"
)

# Actualizar el session_state con los cambios de la tabla
nuevos_medidores = {}
for _, row in edited_df.iterrows():
    nombre = row["MEDIDOR"]
    if pd.isna(nombre) or str(nombre).strip() == "":
        continue
    nuevos_medidores[str(nombre)] = {
        "tipo": int(row["tipo"]) if not pd.isna(row["tipo"]) else 0,
        "anterior": float(row["anterior"]) if not pd.isna(row["anterior"]) else 0.0,
        "actual": float(row["actual"]) if not pd.isna(row["actual"]) else 0.0,
        "mant_com": float(row["mant_com"]) if not pd.isna(row["mant_com"]) else 0.0
    }

st.session_state.datos_app["medidores"] = nuevos_medidores
st.session_state.datos_app["periodo"] = periodo_nombre
st.session_state.datos_app["precio_unitario"] = precio_unitario
st.session_state.datos_app["cargos_fijos_globales"] = cargos_actualizados

# --- CÁLCULOS ---
medidores_dict = st.session_state.datos_app["medidores"]

agua_kwh_diff = 0.0
if "AGUA" in medidores_dict:
    agua_vals = medidores_dict["AGUA"]
    agua_kwh_diff = max(0.0, agua_vals["actual"] - agua_vals["anterior"])
agua_monto_total = agua_kwh_diff * precio_unitario

suma_tipos_activos = sum(int(m["tipo"]) for name, m in medidores_dict.items() if name != "AGUA")
if suma_tipos_activos == 0:
    suma_tipos_activos = 1

resultados = []
for nombre, vals in medidores_dict.items():
    dif = max(0.0, vals["actual"] - vals["anterior"])
    consumo_soles = dif * precio_unitario
    tipo_val = int(vals["tipo"])
    
    if tipo_val == 0 or nombre == "AGUA":
        cf_val = mant_val = ap_val = er_val = afianza_val = agua_val = 0.0
    else:
        cf_val = (cargos_actualizados["CF"] / suma_tipos_activos) * tipo_val
        mant_val = (cargos_actualizados["MANT"] / suma_tipos_activos) * tipo_val
        ap_val = (cargos_actualizados["AP"] / suma_tipos_activos) * tipo_val
        er_val = (cargos_actualizados["ER"] / suma_tipos_activos) * tipo_val
        afianza_val = (cargos_actualizados["Afianza"] / suma_tipos_activos) * tipo_val
        agua_val = (agua_monto_total / suma_tipos_activos) * tipo_val

    if nombre == "AGUA":
        subtotal = consumo_soles
        igv = 0.0
        total_final = subtotal + vals["mant_com"]
    else:
        subtotal = consumo_soles + cf_val + mant_val + ap_val + er_val + agua_val + afianza_val
        igv = subtotal * 0.18
        total_final = subtotal + igv + vals["mant_com"]
    
    resultados.append({
        "Medidor": nombre,
        "Diferencia kW": round(dif, 2),
        "Consumo ($)": round(consumo_soles, 2),
        "Subtotal": round(subtotal, 2),
        "TOTAL": round(total_final, 2),
        "Detalle_Completo": {
            "Lectura Anterior": vals["anterior"],
            "Lectura Actual": vals["actual"],
            "Diferencia kW": round(dif, 2),
            "Costo Consumo": round(consumo_soles, 2),
            "Cargo Fijo (CF)": round(cf_val, 2),
            "Mantenimiento": round(mant_val, 2),
            "Alumbrado Público (AP)": round(ap_val, 2),
            "Electrificación Rural (ER)": round(er_val, 2),
            "Agua": round(agua_val, 2),
            "Afianza S.E.": round(afianza_val, 2),
            "Sub-Total": round(subtotal, 2),
            "IGV": round(igv, 2),
            "Mantenimiento Comunal": round(vals["mant_com"], 2),
            "TOTAL": round(total_final, 2)
        }
    })

df_resumen = pd.DataFrame(resultados)
st.markdown("### 📋 Resumen General del Mes")
st.dataframe(df_resumen, use_container_width=True)

# --- REPORTE PDF ---
st.markdown("### 📄 Generación de Recibo Individual en PDF")
persona_elegida = st.selectbox("Seleccione a la persona para generar su recibo:", list(medidores_dict.keys()))

def generar_pdf_individual(periodo, persona, datos_completos):
    pdf_filename = f"Recibo_{persona}_{periodo.replace(' ', '_')}.pdf"
    doc = SimpleDocTemplate(pdf_filename, pagesize=letter, rightMargin=40, leftMargin=40, topMargin=40, bottomMargin=40)
    story = []
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle('TitleStyle', parent=styles['Heading1'], fontSize=15, textColor=colors.HexColor('#1f4e79'), alignment=1, spaceAfter=10)
    subtitle_style = ParagraphStyle('SubTitleStyle', parent=styles['Normal'], fontSize=10, textColor=colors.HexColor('#555555'), alignment=1, spaceAfter=15)
    body_style = ParagraphStyle('BodyStyle', parent=styles['Normal'], fontSize=9, textColor=colors.HexColor('#333333'))
    
    story.append(Paragraph(f"RECIBO DE CONSUMO DE LUZ", title_style))
    story.append(Paragraph(f"<b>Periodo:</b> {periodo} &nbsp;&nbsp;|&nbsp;&nbsp; <b>Medidor / Persona:</b> {persona}", subtitle_style))
    story.append(Spacer(1, 5))
    
    elementos_tabla = [["Concepto", "Monto / Detalle"]]
    for k, v in datos_completos.items():
        if isinstance(v, (int, float)) and v == 0 and k not in ["Lectura Anterior", "Lectura Actual"]:
            continue
        elementos_tabla.append([str(k), f"{v:,.2f}" if isinstance(v, (int, float)) else str(v)])
        
    t = Table(elementos_tabla, colWidths=[240, 180])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (1,0), colors.HexColor('#1f4e79')),
        ('TEXTCOLOR', (0,0), (1,0), colors.white),
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0,0), (-1,0), 6),
        ('BACKGROUND', (0,1), (-1,-1), colors.HexColor('#f9f9f9')),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#dddddd')),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor('#fdfdfd')]),
        ('FONTNAME', (0,1), (-1,-1), 'Helvetica'),
        ('FONTSIZE', (0,0), (-1,-1), 9),
        ('BOTTOMPADDING', (0,1), (-1,-1), 5),
        ('TOPPADDING', (0,1), (-1,-1), 5),
    ]))
    
    story.append(t)
    story.append(Spacer(1, 15))
    story.append(Paragraph("<i>* Reporte automático generado para el periodo en curso. Gracias por su puntualidad.</i>", body_style))
    
    doc.build(story)
    return pdf_filename

if st.button("📥 Descargar Recibo PDF de la Persona"):
    fila_persona = next(item for item in resultados if item["Medidor"] == persona_elegida)
    pdf_path = generar_pdf_individual(periodo_nombre, persona_elegida, fila_persona["Detalle_Completo"])
    
    with open(pdf_path, "rb") as pdf_file:
        st.download_button(
            label=f"Descargar archivo para {persona_elegida}",
            data=pdf_file,
            file_name=pdf_path,
            mime="application/pdf"
        )
    st.success(f"Recibo generado limpiamente para {persona_elegida} (sin campos en cero).")