import streamlit as st
from utils.gsheets import gsheets_manager
from datetime import datetime, date, time, timedelta
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from io import BytesIO

st.set_page_config(
    page_title="Panel Administrador - Mi Peluquería", 
    page_icon="👨‍💼",
    layout="wide"
)

def authenticate():
    """Sistema de autenticación simple"""
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
    
    if not st.session_state.authenticated:
        st.title("🔐 Acceso Administrador")
        
        with st.form("login_form"):
            username = st.text_input("Usuario", placeholder="Ingresa tu usuario")
            password = st.text_input("Contraseña", type="password", placeholder="Ingresa tu contraseña")
            
            submitted = st.form_submit_button("Ingresar", type="primary", use_container_width=True)
            
            if submitted:
                try:
                    if (username == st.secrets["admin"]["username"] and 
                        password == st.secrets["admin"]["password"]):
                        st.session_state.authenticated = True
                        st.rerun()
                    else:
                        st.error("❌ Credenciales incorrectas")
                except KeyError:
                    st.error("❌ Error de configuración: Verifica las credenciales en secrets.toml")
        st.stop()
    
    return True

def main():
    if not authenticate():
        return
    
    try:
        if not gsheets_manager.client:
            st.error("❌ Error de conexión con Google Sheets")
            return
    except AttributeError:
        st.error("❌ Error: gsheets_manager no está inicializado correctamente")
        return
    
    st.title("👨‍💼 Panel de Administración")
    st.markdown("---")
    
    # Sidebar optimizado para tablet
    with st.sidebar:
        st.header("🔧 Acciones Rápidas")
        
        if st.button("🔄 Actualizar Datos", use_container_width=True, type="secondary"):
            try:
                gsheets_manager.clear_cache()
                st.success("✅ Datos actualizados")
                st.rerun()
            except Exception as e:
                st.error(f"❌ Error al actualizar: {str(e)}")
        
        st.markdown("---")
        
        # Estadísticas rápidas
        try:
            citas_hoy = gsheets_manager.get_today_appointments()
            total_hoy = len(citas_hoy) if not citas_hoy.empty else 0
            st.metric("📅 Citas Hoy", total_hoy)
        except:
            st.metric("📅 Citas Hoy", 0)
        
        st.markdown("---")
        st.info("📱 **Modo Tablet Activado** - Interfaz optimizada")
        
        # Botón de logout
        if st.button("🚪 Cerrar Sesión", use_container_width=True, type="primary"):
            st.session_state.authenticated = False
            st.rerun()
    
    # Pestañas principales optimizadas para tablet
    tab1, tab2, tab3, tab4 = st.tabs(["📅 Citas de Hoy", "📊 Todas las Citas", "📈 Estadísticas", "⚙️ Configuración"])
    
    with tab1:
        st.subheader("📅 Citas del Día de Hoy")
        
        try:
            citas_hoy = gsheets_manager.get_today_appointments()
            
            if citas_hoy.empty:
                st.info("✅ No hay citas para hoy")
            else:
                # Métricas rápidas en fila para tablet
                cols = st.columns(4)
                metrics = [
                    ("Total", len(citas_hoy), ""),
                    ("Pendientes", len(citas_hoy[citas_hoy["Estado"] == "Agendada"]), "⏳"),
                    ("En Progreso", len(citas_hoy[citas_hoy["Estado"] == "En Progreso"]), "🔴"),
                    ("Completadas", len(citas_hoy[citas_hoy["Estado"] == "Completada"]), "✅")
                ]
                
                for (label, value, icon), col in zip(metrics, cols):
                    with col:
                        st.metric(f"{icon} {label}", value)
                
                st.markdown("---")
                
                # Lista de citas optimizada para tablet - MÁS INFORMACIÓN
                for _, cita in citas_hoy.iterrows():
                    with st.container():
                        # Usar columnas adaptativas para tablet
                        col1, col2, col3 = st.columns([3, 2, 2])
                        
                        with col1:
                            # INFORMACIÓN COMPLETA PARA TABLET
                            st.write(f"**👤 {cita.get('Cliente', 'N/A')}**")
                            st.caption(f"📞 {cita.get('Teléfono', 'N/A')}")
                            st.write(f"**🕒 Hora:** {cita.get('Hora_Cita', 'N/A')}")
                            st.write(f"**💇 Servicio:** {cita.get('Servicio', 'Consulta')}")
                            
                            # Mostrar notas si existen
                            notas = cita.get('Notas', '')
                            if notas and str(notas).strip() and str(notas).strip() != 'nan':
                                with st.expander("📝 Ver notas"):
                                    st.write(notas)
                        
                        with col2:
                            estado = cita.get("Estado", "Agendada")
                            color_estado = {
                                "Agendada": "🟡",
                                "En Progreso": "🔴", 
                                "Completada": "🟢",
                                "Cancelada": "⚫"
                            }.get(estado, "⚪")
                            st.write(f"**Estado:** {color_estado} {estado}")
                            
                            # Información adicional
                            if 'Fecha_Creacion' in cita:
                                fecha_creacion = cita['Fecha_Creacion']
                                if isinstance(fecha_creacion, str) and ' ' in fecha_creacion:
                                    hora_creacion = fecha_creacion.split(' ')[1][:5]
                                    st.caption(f"📋 Creada: {hora_creacion}")
                        
                        with col3:
                            cita_id = cita.get('ID')
                            if cita_id:
                                estado = cita.get("Estado", "Agendada")
                                
                                if estado == "Agendada":
                                    col_btn1, col_btn2 = st.columns(2)
                                    with col_btn1:
                                        if st.button("▶️ Iniciar", key=f"start_{cita_id}", use_container_width=True):
                                            try:
                                                gsheets_manager.update_appointment_status(cita_id, "En Progreso", datetime.now())
                                                st.success("✅ Cita iniciada")
                                                st.rerun()
                                            except Exception as e:
                                                st.error(f"❌ Error: {str(e)}")
                                    with col_btn2:
                                        if st.button("❌ Cancelar", key=f"cancel_{cita_id}", use_container_width=True):
                                            try:
                                                gsheets_manager.update_appointment_status(cita_id, "Cancelada")
                                                st.success("✅ Cita cancelada")
                                                st.rerun()
                                            except Exception as e:
                                                st.error(f"❌ Error: {str(e)}")
                                
                                elif estado == "En Progreso":
                                    if st.button("⏹️ Finalizar", key=f"end_{cita_id}", use_container_width=True):
                                        try:
                                            gsheets_manager.update_appointment_status(cita_id, "Completada", None, datetime.now())
                                            st.success("✅ Cita finalizada")
                                            st.rerun()
                                        except Exception as e:
                                            st.error(f"❌ Error: {str(e)}")
                                
                                elif estado in ["Completada", "Cancelada"]:
                                    st.info("✅ Acción completada")
                        
                        st.markdown("---")
                        
        except Exception as e:
            st.error(f"❌ Error al cargar citas de hoy: {str(e)}")
    
    with tab2:
        st.subheader("📊 Todas las Citas")
        
        try:
            df = gsheets_manager.get_all_appointments()
            
            if df.empty:
                st.info("📝 No hay citas registradas")
            else:
                # Filtros optimizados para tablet
                col1, col2, col3 = st.columns(3)
                with col1:
                    fecha_filtro = st.date_input("Filtrar por fecha", value=None)
                with col2:
                    try:
                        estados = ["Todos"] + list(df["Estado"].unique()) if "Estado" in df.columns else ["Todos"]
                        estado_filtro = st.selectbox("Filtrar por estado", estados)
                    except:
                        estado_filtro = "Todos"
                with col3:
                    cliente_filtro = st.text_input("Filtrar por cliente", placeholder="Nombre del cliente")
                
                # Aplicar filtros
                df_filtrado = df.copy()
                
                if fecha_filtro and "Fecha_Cita" in df_filtrado.columns:
                    try:
                        df_filtrado = df_filtrado[df_filtrado["Fecha_Cita"] == fecha_filtro.strftime("%Y-%m-%d")]
                    except:
                        pass
                
                if estado_filtro != "Todos" and "Estado" in df_filtrado.columns:
                    df_filtrado = df_filtrado[df_filtrado["Estado"] == estado_filtro]
                
                if cliente_filtro and "Cliente" in df_filtrado.columns:
                    df_filtrado = df_filtrado[df_filtrado["Cliente"].str.contains(cliente_filtro, case=False, na=False)]
                
                st.metric("Citas filtradas", len(df_filtrado))
                
                # Botones de exportación
                col_exp1, col_exp2, col_exp3 = st.columns(3)
                with col_exp1:
                    if st.button("📊 Exportar a CSV", use_container_width=True):
                        csv = df_filtrado.to_csv(index=False)
                        st.download_button(
                            "⬇️ Descargar CSV",
                            csv,
                            "citas_peluqueria.csv",
                            "text/csv",
                            use_container_width=True
                        )
                with col_exp2:
                    if st.button("📈 Exportar a Excel", use_container_width=True):
                        output = BytesIO()
                        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                            df_filtrado.to_excel(writer, index=False, sheet_name='Citas')
                        st.download_button(
                            "⬇️ Descargar Excel",
                            output.getvalue(),
                            "citas_peluqueria.xlsx",
                            "application/vnd.ms-excel",
                            use_container_width=True
                        )
                with col_exp3:
                    if st.button("🔄 Limpiar Filtros", use_container_width=True):
                        st.rerun()
                
                # Mostrar dataframe con columnas importantes para tablet
                columnas_mostrar = ['ID', 'Cliente', 'Teléfono', 'Fecha_Cita', 'Hora_Cita', 'Estado', 'Servicio']
                columnas_disponibles = [col for col in columnas_mostrar if col in df_filtrado.columns]
                
                st.dataframe(
                    df_filtrado[columnas_disponibles],
                    use_container_width=True,
                    height=400
                )
                
        except Exception as e:
            st.error(f"❌ Error al cargar todas las citas: {str(e)}")
    
    with tab3:
        st.subheader("📈 Estadísticas y Gráficos")
        
        try:
            df = gsheets_manager.get_all_appointments()
            
            if df.empty:
                st.info("📊 No hay datos suficientes para generar estadísticas")
            else:
                col1, col2 = st.columns(2)
                
                with col1:
                    # Gráfico de citas por día
                    st.subheader("📅 Citas por Día")
                    if 'Fecha_Cita' in df.columns:
                        citas_por_dia = df.groupby('Fecha_Cita').size().reset_index(name='Cantidad')
                        citas_por_dia = citas_por_dia.sort_values('Fecha_Cita').tail(10)  # Últimos 10 días
                        
                        fig_dias = px.bar(
                            citas_por_dia, 
                            x='Fecha_Cita', 
                            y='Cantidad',
                            title="Citas por Día (Últimos 10 días)",
                            color='Cantidad',
                            color_continuous_scale='blues'
                        )
                        st.plotly_chart(fig_dias, use_container_width=True)
                    else:
                        st.info("No hay datos de fechas para generar el gráfico")
                
                with col2:
                    # Gráfico de citas por estado
                    st.subheader("📊 Citas por Estado")
                    if 'Estado' in df.columns:
                        citas_por_estado = df['Estado'].value_counts().reset_index()
                        citas_por_estado.columns = ['Estado', 'Cantidad']
                        
                        fig_estados = px.pie(
                            citas_por_estado,
                            values='Cantidad',
                            names='Estado',
                            title="Distribución por Estado",
                            color='Estado',
                            color_discrete_map={
                                'Agendada': '#FFA726',
                                'En Progreso': '#EF5350',
                                'Completada': '#66BB6A',
                                'Cancelada': '#BDBDBD'
                            }
                        )
                        st.plotly_chart(fig_estados, use_container_width=True)
                    else:
                        st.info("No hay datos de estados para generar el gráfico")
                
                # Gráfico de servicios más populares
                st.subheader("💇 Servicios Más Populares")
                if 'Servicio' in df.columns:
                    servicios_populares = df['Servicio'].value_counts().head(8).reset_index()
                    servicios_populares.columns = ['Servicio', 'Cantidad']
                    
                    fig_servicios = px.bar(
                        servicios_populares,
                        x='Servicio',
                        y='Cantidad',
                        title="Servicios Más Solicitados",
                        color='Cantidad',
                        color_continuous_scale='viridis'
                    )
                    st.plotly_chart(fig_servicios, use_container_width=True)
                else:
                    st.info("No hay datos de servicios para generar el gráfico")
                    
        except Exception as e:
            st.error(f"❌ Error al generar estadísticas: {str(e)}")
    
    with tab4:
        st.subheader("⚙️ Configuración")
        
        try:
            config = gsheets_manager.get_configuracion()
            
            with st.form("config_form"):
                st.subheader("🕒 Horarios de Trabajo por Día")
                
                # Configuración por día - INCLUYENDO DOMINGO
                dias_semana = [
                    ("Lunes", "LUNES"),
                    ("Martes", "MARTES"),
                    ("Miércoles", "MIERCOLES"),
                    ("Jueves", "JUEVES"),
                    ("Viernes", "VIERNES"),
                    ("Sábado", "SABADO"),
                    ("Domingo", "DOMINGO")  # ✅ AGREGADO DOMINGO
                ]
                
                # Primera fila de días
                cols = st.columns(4)
                for i, (dia_nombre, dia_key) in enumerate(dias_semana[:4]):
                    with cols[i]:
                        horario_key = f"HORARIO_{dia_key}"
                        valor_actual = config.get(horario_key, "09:00-18:00")
                        nuevo_valor = st.text_input(
                            dia_nombre,
                            value=valor_actual,
                            placeholder="09:00-18:00",
                            help=f"Horario para {dia_nombre}"
                        )
                        config[horario_key] = nuevo_valor
                
                # Segunda fila de días
                cols = st.columns(4)
                for i, (dia_nombre, dia_key) in enumerate(dias_semana[4:]):
                    with cols[i]:
                        horario_key = f"HORARIO_{dia_key}"
                        valor_actual = config.get(horario_key, "09:00-14:00")
                        nuevo_valor = st.text_input(
                            dia_nombre,
                            value=valor_actual,
                            placeholder="09:00-14:00",
                            help=f"Horario para {dia_nombre}"
                        )
                        config[horario_key] = nuevo_valor
                
                st.subheader("⏱️ Configuración de Citas")
                duracion = st.number_input(
                    "Duración de cada cita (minutos)", 
                    value=int(config.get("DURACION_CITA", "30")), 
                    min_value=15, 
                    max_value=120, 
                    step=5
                )
                config["DURACION_CITA"] = str(duracion)
                
                st.subheader("📅 Días No Laborables")
                dias_no_laborables = st.text_area(
                    "Fechas no laborables (separar por comas)",
                    value=config.get("DIAS_NO_LABORABLES", ""),
                    placeholder="2024-12-25, 2024-01-01, 2024-04-02",
                    help="Formato: AAAA-MM-DD, separados por comas"
                )
                config["DIAS_NO_LABORABLES"] = dias_no_laborables
                
                submitted = st.form_submit_button("💾 Guardar Configuración", type="primary", use_container_width=True)
                
                if submitted:
                    try:
                        if gsheets_manager.update_configuracion(config):
                            st.success("✅ Configuración guardada correctamente")
                            st.rerun()
                        else:
                            st.error("❌ Error al guardar la configuración")
                    except Exception as e:
                        st.error(f"❌ Error: {str(e)}")
                        
        except Exception as e:
            st.error(f"❌ Error al cargar configuración: {str(e)}")

if __name__ == "__main__":
    main()
