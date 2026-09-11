import os
import json
import pandas as pd
import streamlit as st
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

DB_FILE = "luz_config_actual.json"

# ==========================================
# CONFIGURACIÓN DE SEGURIDAD DEL ADMINISTRADOR
# ==========================================
# Puedes cambiar esta clave por la contraseña secreta que prefieras usar
ADMIN_PASSWORD = "admin123_luz"

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

st.set_page_config(page_title="Sistema de Luz - Comunidad", layout="wide")

if "datos_app" not in st.session_state:
    st.session_state.datos_app = cargar_datos_disco()

if "historial_undo" not in st.session_state:
    st.session_state.historial_undo = []

if "historial_redo" not in st.session_state:
    st.session_state.historial_redo = []

# Estado de autenticación del administrador
if "admin_autenticado" not in st.session_state:
    st.session_state.admin_autenticado = False

def registrar_estado():
    import copy
    st.session_state.historial_undo.append(copy.deepcopy(st.session_state.datos_app))
    st.session_state.historial_redo.clear()

datos_actuales = st.session_state.datos_app

# --- MOTOR MATEMÁTICO ---
def calcular_resultados_comunidad(state_data):
    precio_u = state_data["precio_unitario"]
    cargos = state_data["cargos_fijos_globales"]
    medidores = state_data["medidores"]
    
    agua_kwh_diff = 0.0
    if "AGUA" in medidores:
        agua_vals = medidores["AGUA"]
        agua_kwh_diff = max(0.0, agua_vals["actual"] - agua_vals["anterior"])
    agua_monto_total = agua_kwh_diff * precio_u
    
    suma_tipos_activos = sum(int(m["tipo"]) for name, m in medidores.items() if name != "AGUA")
    if suma_tipos_activos == 0:
        suma_tipos_activos = 1

    resultados = []
    for nombre, vals in medidores.items():
        dif = max(0.0, vals["actual"] - vals["anterior"])
        consumo_soles = dif * precio_u
        tipo_val = int(vals["tipo"])
        
        if tipo_val == 0 or nombre == "AGUA":
            cf_val = mant_val = ap_val = er_val = afianza_val = agua_val = 0.0
        else:
            cf_val = (cargos["CF"] / suma_tipos_activos) * tipo_val
            mant_val = (cargos["MANT"] / suma_tipos_activos) * tipo_val
            ap_val = (cargos["AP"] / suma_tipos_activos) * tipo_val
            er_val = (cargos["ER"] / suma_tipos_activos) * tipo_val
            afianza_val = (cargos["Afianza"] / suma_tipos_activos) * tipo_val
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
    return resultados

# --- BARRA LATERAL ---
st.sidebar.title("📌 Menú de Navegación")
modo = st.sidebar.radio("Seleccione la sección:", ["🏠 Portal del Vecino (Ingresar Lectura)", "🔐 Panel de Administración"])

# ==========================================
# MODO 1: PORTAL DEL VECINO (PÚBLICO)
# ==========================================
if modo == "🏠 Portal del Vecino (Ingresar Lectura)":
    st.title("💡 Portal de Registro de Consumo - Vecinos")
    st.markdown(f"**Periodo Actual:** `{datos_actuales.get('periodo', 'MES ACTUAL')}`")
    st.markdown("Bienvenido. Seleccione su nombre o medidor, ingrese su lectura actual y descargue su recibo de forma privada.")
    
    lista_usuarios = [k for k, v in datos_actuales["medidores"].items() if v["tipo"] > 0 or k == "AGUA"]
    vecino_seleccionado = st.selectbox("👤 Seleccione su Medidor / Nombre:", lista_usuarios)
    
    if vecino_seleccionado:
        info_actual = datos_actuales["medidores"][vecino_seleccionado]
        st.info(f"Lectura Anterior registrada para **{vecino_seleccionado}**: `{info_actual['anterior']}` kW")
        
        with st.form("form_lectura_vecino"):
            nueva_lectura = st.number_input("🔢 Ingrese su Lectura Actual (kWh):", value=float(info_actual["actual"]), format="%.2f")
            btn_guardar_lectura = st.form_submit_button("💾 Guardar y Calcular mi Recibo")
            
            if btn_guardar_lectura:
                registrar_estado()
                datos_actuales["medidores"][vecino_seleccionado]["actual"] = float(nueva_lectura)
                guardar_datos_disco(datos_actuales)
                st.success("¡Lectura guardada con éxito! Su recibo ha sido actualizado.")
        
        resultados_calculados = calcular_resultados_comunidad(datos_actuales)
        datos_vecino = next((item for item in resultados_calculados if item["Medidor"] == vecino_seleccionado), None)
        
        if datos_vecino:
            st.markdown("---")
            st.markdown(f"### 📄 Su Recibo Detallado - {vecino_seleccionado}")
            
            df_detalle_vecino = pd.DataFrame([
                {"Concepto": k, "Monto ($)": v} 
                for k, v in datos_vecino["Detalle_Completo"].items() 
                if not (isinstance(v, (int, float)) and v == 0 and k not in ["Lectura Anterior", "Lectura Actual"])
            ])
            st.dataframe(df_detalle_vecino, use_container_width=True, hide_index=True)
            
            st.markdown(f"### 💰 Total a Pagar: `$ {datos_vecino['TOTAL']:,.2f}`")
            
            def generar_pdf_privado(periodo, persona, datos_completos):
                pdf_filename = f"Recibo_{persona}_{periodo.replace(' ', '_')}.pdf"
                doc = SimpleDocTemplate(pdf_filename, pagesize=letter, rightMargin=40, leftMargin=40, topMargin=40, bottomMargin=40)
                story = []
                styles = getSampleStyleSheet()
                
                title_style = ParagraphStyle('TitleStyle', parent=styles['Heading1'], fontSize=15, textColor=colors.HexColor('#1f4e79'), alignment=1, spaceAfter=10)
                subtitle_style = ParagraphStyle('SubTitleStyle', parent=styles['Normal'], fontSize=10, textColor=colors.HexColor('#555555'), alignment=1, spaceAfter=15)
                body_style = ParagraphStyle('BodyStyle', parent=styles['Normal'], fontSize=9, textColor=colors.HexColor('#333333'))
                
                story.append(Paragraph(f"RECIBO DE CONSUMO DE LUZ", title_style))
                story.append(Paragraph(f"<b>Periodo:</b> {periodo} &nbsp;&nbsp;|&nbsp;&nbsp; <b>Medidor / Propietario:</b> {persona}", subtitle_style))
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
                story.append(Paragraph("<i>* Recibo personal generado automáticamente. Gracias por su puntualidad.</i>", body_style))
                doc.build(story)
                return pdf_filename

            if st.button("📥 Descargar Mi Recibo en PDF"):
                pdf_path = generar_pdf_privado(datos_actuales.get("periodo", "MES"), vecino_seleccionado, datos_vecino["Detalle_Completo"])
                with open(pdf_path, "rb") as pdf_file:
                    st.download_button(
                        label=f"Confirmar Descarga de Recibo ({vecino_seleccionado})",
                        data=pdf_file,
                        file_name=pdf_path,
                        mime="application/pdf"
                    )

# ==========================================
# MODO 2: PANEL DE ADMINISTRACIÓN (PROTEGIDO)
# ==========================================
else:
    st.title("🔐 Panel de Administración - Acceso Restringido")
    
    # Validar si ya está autenticado
    if not st.session_state.admin_autenticado:
        st.warning("Esta sección está protegida. Por favor ingresa tu contraseña de administrador.")
        with st.form("form_login_admin"):
            password_ingresada = st.text_input("Contraseña de Administrador:", type="password")
            btn_login = st.form_submit_button("Ingresar al Panel")
            
            if btn_login:
                if password_ingresada == ADMIN_PASSWORD:
                    st.session_state.admin_autenticado = True
                    st.success("¡Acceso concedido!")
                    st.rerun()
                else:
                    st.error("Contraseña incorrecta. Acceso denegado.")
    else:
        # Botón para cerrar sesión de administrador si se desea
        if st.sidebar.button("🔒 Cerrar Sesión Admin"):
            st.session_state.admin_autenticado = False
            st.rerun()

        col_ctrl1, col_ctrl2, col_ctrl3, col_ctrl4 = st.columns([1, 1, 2, 2])

        with col_ctrl1:
            if st.button("↩️ Deshacer", use_container_width=True):
                if st.session_state.historial_undo:
                    import copy
                    st.session_state.historial_redo.append(copy.deepcopy(st.session_state.datos_app))
                    st.session_state.datos_app = st.session_state.historial_undo.pop()
                    st.rerun()

        with col_ctrl2:
            if st.button("🔁 Rehacer", use_container_width=True):
                if st.session_state.historial_redo:
                    import copy
                    st.session_state.historial_undo.append(copy.deepcopy(st.session_state.datos_app))
                    st.session_state.datos_app = st.session_state.historial_redo.pop()
                    st.rerun()

        with col_ctrl3:
            if st.button("🔄 Pasar Actual ➔ Anterior (Nuevo Mes)", use_container_width=True):
                registrar_estado()
                for nombre, vals in st.session_state.datos_app["medidores"].items():
                    vals["anterior"] = vals["actual"]
                guardar_datos_disco(st.session_state.datos_app)
                st.success("¡Lecturas actuales pasadas a anteriores correctamente!")
                st.rerun()

        with col_ctrl4:
            if st.button("💾 Guardar Cambios en Disco", use_container_width=True):
                guardar_datos_disco(st.session_state.datos_app)
                st.success("¡Guardado permanente exitoso!")

        st.markdown("---")

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

        with st.expander("➕ Agregar Nuevo Usuario / Medidor a la Comunidad"):
            with st.form("form_nuevo_usuario_admin"):
                col_u1, col_u2, col_u3, col_u4, col_u5 = st.columns(5)
                with col_u1:
                    nuevo_nombre = st.text_input("Nombre / Medidor").strip().upper()
                with col_u2:
                    nuevo_tipo = st.number_input("Tipo (0=Inactivo, 1, 2...)", min_value=0, value=1, step=1)
                with col_u3:
                    nuevo_anterior = st.number_input("Lectura Anterior", value=0.0, format="%.2f")
                with col_u4:
                    nuevo_actual = st.number_input("Lectura Actual", value=0.0, format="%.2f")
                with col_u5:
                    nuevo_mant_com = st.number_input("Maint. Comunal", value=0.0, format="%.2f")
                    
                if st.form_submit_button("Registrar Usuario"):
                    if not nuevo_nombre:
                        st.error("Ingresa un nombre válido.")
                    elif nuevo_nombre in datos_actuales["medidores"]:
                        st.error("El usuario ya existe.")
                    else:
                        registrar_estado()
                        datos_actuales["medidores"][nuevo_nombre] = {
                            "tipo": int(nuevo_tipo), "anterior": float(nuevo_anterior),
                            "actual": float(nuevo_actual), "mant_com": float(nuevo_mant_com)
                        }
                        guardar_datos_disco(datos_actuales)
                        st.success("¡Usuario registrado!")
                        st.rerun()

        st.markdown("### 📊 Control General de Lecturas (Admin)")
        df_medidores = pd.DataFrame.from_dict(datos_actuales["medidores"], orient='index')
        df_medidores.index.name = "MEDIDOR"
        df_medidores.reset_index(inplace=True)

        edited_df = st.data_editor(df_medidores, num_rows="dynamic", use_container_width=True, key="editor_admin")

        nuevos_medidores = {}
        for _, row in edited_df.iterrows():
            nombre = row["MEDIDOR"]
            if pd.isna(nombre) or str(nombre).strip() == "":
                continue
            nuevos_medidores[str(nombre).strip().upper()] = {
                "tipo": int(row["tipo"]) if not pd.isna(row["tipo"]) else 0,
                "anterior": float(row["anterior"]) if not pd.isna(row["anterior"]) else 0.0,
                "actual": float(row["actual"]) if not pd.isna(row["actual"]) else 0.0,
                "mant_com": float(row["mant_com"]) if not pd.isna(row["mant_com"]) else 0.0
            }

        st.session_state.datos_app["medidores"] = nuevos_medidores
        st.session_state.datos_app["periodo"] = periodo_nombre
        st.session_state.datos_app["precio_unitario"] = precio_unitario
        st.session_state.datos_app["cargos_fijos_globales"] = cargos_actualizados

        resultados_globales = calcular_resultados_comunidad(st.session_state.datos_app)
        df_resumen = pd.DataFrame(resultados_globales)
        st.markdown("### 📋 Resumen Global de Toda la Comunidad")
        st.dataframe(df_resumen[["Medidor", "Diferencia kW", "Consumo ($)", "Subtotal", "TOTAL"]], use_container_width=True)