import streamlit as st
from utils.gsheets import gsheets_manager
from datetime import datetime, date, time, timedelta
import pandas as pd

st.set_page_config(
    page_title="Agendar Cita - Mi Peluquería",
    page_icon="📋",
    layout="centered"
)

def mostrar_horarios_disponibles(horarios):
    """Muestra horarios disponibles en formato de botones optimizado para móvil"""
    if not horarios:
        st.warning("❌ No hay horarios disponibles para esta fecha")
        return None
    
    st.success(f"✅ {len(horarios)} horarios disponibles")
    
    # Organizar horarios en columnas para móvil
    cols_per_row = 2  # Solo 2 columnas para móvil
    horarios_ordenados = sorted(horarios)
    
    # Mostrar horarios como botones
    hora_seleccionada = None
    
    for i in range(0, len(horarios_ordenados), cols_per_row):
        cols = st.columns(cols_per_row)
        for j, horario in enumerate(horarios_ordenados[i:i + cols_per_row]):
            with cols[j]:
                # Botón más grande y visible para móvil
                if st.button(
                    f"🕒 {horario}",
                    key=f"hora_{horario}",
                    use_container_width=True,
                    type="primary" if st.session_state.get('hora_seleccionada') == horario else "secondary"
                ):
                    st.session_state.hora_seleccionada = horario
                    st.rerun()
    
    # Mostrar selección actual de forma prominente
    if st.session_state.get('hora_seleccionada'):
        st.markdown("---")
        st.success(f"⏰ **Horario seleccionado:** **{st.session_state.hora_seleccionada}**")
        return st.session_state.hora_seleccionada
    
    return None

def main():
    st.title("📋 Agendar Cita")
    st.markdown("---")
    
    # Inicializar variables de sesión
    if 'hora_seleccionada' not in st.session_state:
        st.session_state.hora_seleccionada = None
    if 'cita_agendada' not in st.session_state:
        st.session_state.cita_agendada = False
    if 'mostrar_horarios' not in st.session_state:
        st.session_state.mostrar_horarios = False
    if 'busqueda_realizada' not in st.session_state:
        st.session_state.busqueda_realizada = False
    
    # Si ya se agendó una cita, mostrar mensaje de éxito
    if st.session_state.cita_agendada:
        st.success("🎉 ¡Cita agendada exitosamente!")
        datos = st.session_state.get('datos_cita', {})
        
        st.subheader("📋 Resumen de tu Cita")
        st.info(f"""
        **👤 Cliente:** {datos.get('nombre', '')}  
        **📞 Teléfono:** {datos.get('Teléfono', '')}  
        **📧 Correo:** {datos.get('correo', 'No proporcionado')}  
        **📅 Fecha:** {datos.get('fecha', '')}  
        **🕒 Hora:** {datos.get('hora', '')}  
        **💇 Servicio:** {datos.get('servicio', '')}  
        **📝 Notas:** {datos.get('notas', 'Ninguna')}
        """)
        
        st.info("💡 **Recordatorio:** Por favor, llega 5 minutos antes de tu cita.")
        
        if st.button("📅 Agendar Nueva Cita", type="primary", use_container_width=True):
            st.session_state.hora_seleccionada = None
            st.session_state.cita_agendada = False
            st.session_state.mostrar_horarios = False
            st.session_state.busqueda_realizada = False
            st.session_state.datos_cita = None
            st.rerun()
        return
    
    # Verificar conexión
    try:
        if not gsheets_manager.client:
            st.error("❌ Error de conexión. Por favor, intenta más tarde.")
            return
    except:
        st.error("❌ Error de conexión. Por favor, intenta más tarde.")
        return
    
    # FORMULARIO PRINCIPAL - OPTIMIZADO PARA MÓVIL
    with st.form("formulario_principal"):
        st.subheader("👤 Información Personal")
        
        nombre = st.text_input(
            "Nombre completo *", 
            placeholder="Juan Pérez",
            help="Ingresa tu nombre completo"
        )
        
        telefono = st.text_input(
            "Teléfono *", 
            placeholder="809-123-4567",
            help="Tu número de teléfono"
        )
        
        correo = st.text_input(
            "Correo electrónico", 
            placeholder="ejemplo@email.com",
            help="Opcional - para confirmación"
        )
        
        st.subheader("📅 Información de la Cita")
        
        # Selector de fecha optimizado para móvil
        fecha = st.date_input(
            "Fecha deseada *",
            min_value=datetime.now().date(),
            max_value=datetime.now().date() + timedelta(days=60),
            value=datetime.now().date(),
            help="Selecciona la fecha para tu cita"
        )
        
        # Botón para buscar horarios - CON INDICADOR VISUAL
        buscar_horarios = st.form_submit_button(
            "🔍 Buscar Horarios Disponibles", 
            type="primary" if st.session_state.busqueda_realizada else "secondary",
            use_container_width=True
        )
    
    # Procesar búsqueda de horarios
    if buscar_horarios:
        if not nombre or not telefono:
            st.error("❌ Por favor completa tu nombre y teléfono antes de buscar horarios")
        else:
            with st.spinner("Buscando horarios disponibles..."):
                try:
                    horarios_disponibles = gsheets_manager.get_available_slots(fecha)
                    st.session_state.mostrar_horarios = True
                    st.session_state.busqueda_realizada = True
                    st.session_state.datos_basicos = {
                        'nombre': nombre,
                        'Teléfono': telefono,
                        'correo': correo,
                        'fecha': fecha.strftime("%Y-%m-%d")
                    }
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ Error al buscar horarios: {str(e)}")
    
    # Mostrar indicador de búsqueda realizada
    if st.session_state.busqueda_realizada:
        st.info("🔍 **Búsqueda realizada** - Selecciona un horario disponible")
    
    # Mostrar horarios si están disponibles
    hora_seleccionada = None
    if st.session_state.mostrar_horarios:
        st.markdown("---")
        st.subheader("🕒 Horarios Disponibles")
        
        try:
            horarios_disponibles = gsheets_manager.get_available_slots(
                datetime.strptime(st.session_state.datos_basicos['fecha'], "%Y-%m-%d").date()
            )
            hora_seleccionada = mostrar_horarios_disponibles(horarios_disponibles)
        except Exception as e:
            st.error(f"❌ Error al cargar horarios: {str(e)}")
    
    # FORMULARIO DE SERVICIO (solo si hay hora seleccionada)
    if st.session_state.hora_seleccionada:
        st.markdown("---")
        st.subheader("💇 Información del Servicio")
        
        with st.form("formulario_servicio"):
            servicio = st.selectbox(
                "Servicio *",
                options=[
                    "💇 Corte de cabello",
                    "🧔 Afeitado", 
                    "✂️ Corte y barba",
                    "🎨 Tinte",
                    "💇‍♂️ Peinado",
                    "🔧 Otro"
                ],
                help="Selecciona el servicio que necesitas"
            )
            
            # CUADRO DE TEXTO PARA NOTAS - OPCIONAL
            notas = st.text_area(
                "Notas adicionales", 
                placeholder="Opcional: detalles específicos, preferencias, etc...",
                height=80,
                help="Opcional - información adicional sobre tu cita"
            )
            
            # Términos y condiciones
            acepta_terminos = st.checkbox(
                "Acepto los términos y condiciones *",
                help="Debes aceptar para agendar la cita"
            )
            
            # Botones optimizados para móvil
            col1, col2 = st.columns([2, 1])
            with col1:
                confirmar = st.form_submit_button(
                    "✅ Confirmar Cita", 
                    type="primary",
                    use_container_width=True
                )
            
            with col2:
                if st.form_submit_button("🔄 Cambiar", use_container_width=True):
                    st.session_state.hora_seleccionada = None
                    st.rerun()
            
            if confirmar:
                # Validaciones finales
                errores = []
                
                if not acepta_terminos:
                    errores.append("❌ Debes aceptar los términos y condiciones")
                
                if errores:
                    for error in errores:
                        st.error(error)
                else:
                    # Preparar datos de la cita
                    appointment_data = {
                        "cliente": st.session_state.datos_basicos['nombre'],
                        "correo": st.session_state.datos_basicos['correo'],
                        "Teléfono": st.session_state.datos_basicos['Teléfono'],
                        "fecha_cita": st.session_state.datos_basicos['fecha'],
                        "hora_cita": st.session_state.hora_seleccionada,
                        "servicio": servicio.replace("🔧 ", "").replace("💇 ", "").replace("🧔 ", "").replace("✂️ ", "").replace("🎨 ", "").replace("💇‍♂️ ", ""),
                        "notas": notas if notas else ""
                    }
                    
                    # Crear la cita
                    with st.spinner("Agendando tu cita..."):
                        try:
                            if gsheets_manager.create_appointment(appointment_data):
                                st.session_state.cita_agendada = True
                                st.session_state.datos_cita = {
                                    'nombre': st.session_state.datos_basicos['nombre'],
                                    'Teléfono': st.session_state.datos_basicos['Teléfono'],
                                    'correo': st.session_state.datos_basicos['correo'],
                                    'fecha': st.session_state.datos_basicos['fecha'],
                                    'hora': st.session_state.hora_seleccionada,
                                    'servicio': servicio,
                                    'notas': notas if notas else "Ninguna"
                                }
                                st.rerun()
                            else:
                                st.error("❌ Error al agendar la cita. Por favor, intenta nuevamente.")
                        except Exception as e:
                            st.error(f"❌ Error al agendar la cita: {str(e)}")

    # Información adicional optimizada para móvil
    st.markdown("---")
    st.subheader("ℹ️ Información Importante")
    
    with st.expander("📞 Contacto y Políticas"):
        st.markdown("""
        **📞 Teléfono:** (809) 578-9858  
        **🕒 Política de Cancelación:**
        - Cancela con al menos 2 horas de anticipación
        - Cancelaciones frecuentes pueden afectar futuras reservas
        """)
    
    with st.expander("⏰ Horarios de Trabajo"):
        st.markdown("""
        **Lunes a Viernes:** 9:00 AM - 6:00 PM  
        **Sábados:** 9:00 AM - 6:00 PM  
        **Domingos:** 9:00 AM - 2:00 PM
        """)
    
    with st.expander("💡 Recomendaciones"):
        st.markdown("""
        - ✅ Llega 5 minutos antes de tu cita
        - 📸 Trae fotos de referencia si tienes un estilo específico
        - ⏱️ Citas tienen duración de 30-45 minutos
        - 🔄 Para cambios mayores, agenda cita separada
        """)

if __name__ == "__main__":
    main()