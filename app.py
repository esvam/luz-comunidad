# ==========================================
# MODO 1: PORTAL DEL VECINO
# ==========================================
if modo == "🏠 Portal del Vecino (Ingresar Lectura)":
    st.title("💡 Portal de Registro de Consumo - Vecinos")
    st.markdown(f"**Periodo Actual:** `{datos_actuales.get('periodo', 'MES ACTUAL')}`")
    
    if not datos_actuales.get("periodo_habilitado", False):
        st.warning("⏳ El periodo actual **aún no ha sido habilitado** por la administración. Por favor espere a que se habiliten los registros.")
    else:
        st.success("🟢 El periodo de registro de lecturas se encuentra **Habilitado**.")
        lista_usuarios = [k for k, v in datos_actuales["medidores"].items() if v["tipo"] > 0 or k == "AGUA"]
        vecino_seleccionado = st.selectbox("👤 Seleccione su Medidor / Nombre:", lista_usuarios)
        
        if vecino_seleccionado:
            info_actual = datos_actuales["medidores"][vecino_seleccionado]
            lectura_anterior = float(info_actual['anterior'])
            
            # (NOTA: Se removió la línea st.info que mostraba la lectura anterior en pantalla)
            
            with st.form("form_lectura_vecino"):
                # El campo inicia en 0.0 o vacío para que ingresen su lectura sin ver la anterior
                nueva_lectura = st.number_input("🔢 Ingrese su Lectura Actual (kWh):", value=0.0, format="%.2f")
                btn_guardar_lectura = st.form_submit_button("💾 Guardar mi Medición")
                
                if btn_guardar_lectura:
                    if nueva_lectura == lectura_anterior or nueva_lectura < lectura_anterior:
                        datos_actuales["medidores"][vecino_seleccionado]["lectura_guardada"] = False
                        guardar_datos_disco(datos_actuales)
                        st.error("❌ Error de seguridad: La lectura actual debe ser mayor que la lectura anterior.")
                        st.stop()
                    else:
                        registrar_estado()
                        datos_actuales["medidores"][vecino_seleccionado]["actual"] = float(nueva_lectura)
                        datos_actuales["medidores"][vecino_seleccionado]["lectura_guardada"] = True
                        guardar_datos_disco(datos_actuales)
                        st.success("¡Lectura registrada correctamente! Ya puede descargar su recibo abajo.")
            
            lectura_actual_guardada = float(info_actual["actual"])
            if info_actual.get("lectura_guardada", False) and lectura_actual_guardada > lectura_anterior:
                st.success("✅ Medición válida registrada para este periodo. Su recibo está listo para descarga privada.")
                
                resultados_calculados = calcular_resultados_comunidad(datos_actuales)
                datos_vecino = next((item for item in resultados_calculados if item["Medidor"] == vecino_seleccionado), None)
                
                if datos_vecino:
                    def generar_pdf_privado(periodo, persona, datos_completos):
                        pdf_filename = f"Recibo_{persona}_{periodo.replace(' ', '_')}.pdf"
                        doc = SimpleDocTemplate(pdf_filename, pagesize=letter, rightMargin=40, leftMargin=40, topMargin=40, bottomMargin=40)
                        story = []
                        styles = getSampleStyleSheet()
                        
                        title_style = ParagraphStyle('TitleStyle', parent=styles['Heading1'], fontSize=15, textColor=colors.HexColor('#1f4e79'), alignment=1, spaceAfter=10)
                        subtitle_style = ParagraphStyle('SubTitleStyle', parent=styles['Normal'], fontSize=10, textColor=colors.HexColor('#555555'), alignment=1, spaceAfter=15)
                        
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
                        story.append(Paragraph("<i>* Recibo personal generado automáticamente. Gracias por su puntualidad.</i>", ParagraphStyle('Body', parent=styles['Normal'], fontSize=9)))
                        doc.build(story)
                        return pdf_filename

                    col_dl1, col_dl2 = st.columns(2)
                    pdf_path = generar_pdf_privado(datos_actuales.get("periodo", "MES"), vecino_seleccionado, datos_vecino["Detalle_Completo"])
                    with open(pdf_path, "rb") as pdf_file:
                        with col_dl1:
                            st.download_button(
                                label="📥 Descargar Recibo en PDF",
                                data=pdf_file,
                                file_name=pdf_path,
                                mime="application/pdf"
                            )
                    
                    df_csv_vecino = pd.DataFrame([{"Concepto": k, "Monto ($)": v} for k, v in datos_vecino["Detalle_Completo"].items()])
                    csv_data = df_csv_vecino.to_csv(index=False).encode('utf-8')
                    with col_dl2:
                        st.download_button(
                            label="📊 Descargar Recibo en CSV",
                            data=csv_data,
                            file_name=f"Recibo_{vecino_seleccionado}.csv",
                            mime="text/csv"
                        )
            else:
                st.warning("⚠️ Debe ingresar su lectura actual del mes y guardarla para habilitar la descarga de su recibo.")
