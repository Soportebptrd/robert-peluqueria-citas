import streamlit as st
from utils.gsheets import gsheets_manager
from datetime import datetime, date, time
import pandas as pd

# Configuración de la página
st.set_page_config(
    page_title="💈 Mi Peluquería - Sistema de Citas",
    page_icon="💈",
    layout="wide",
    initial_sidebar_state="expanded"
)

def main():
    # Sidebar con información general
    with st.sidebar:
        st.image("https://img.icons8.com/color/96/000000/barber-pole.png", width=80)
        st.title("💈 Mi Peluquería")
        st.markdown("---")
        
        # Mostrar estadísticas rápidas (con manejo de errores)
        try:
            citas_hoy = gsheets_manager.get_today_appointments()
            if citas_hoy is not None and not citas_hoy.empty and 'Estado' in citas_hoy.columns:
                total_citas = len(citas_hoy)
                citas_pendientes = len(citas_hoy[citas_hoy["Estado"] == "Agendada"])
                citas_en_progreso = len(citas_hoy[citas_hoy["Estado"] == "En Progreso"])
                
                st.metric("📅 Citas Hoy", total_citas)
                col1, col2 = st.columns(2)
                col1.metric("⏳ Pendientes", citas_pendientes)
                col2.metric("🔴 En Progreso", citas_en_progreso)
            else:
                st.metric("📅 Citas Hoy", 0)
                st.info("No hay citas para hoy")
        except Exception as e:
            st.metric("📅 Citas Hoy", 0)
            st.info("Cargando estadísticas...")
        
        st.markdown("---")
        st.markdown("### Navegación")
        st.page_link("app.py", label="🏠 Inicio", icon="🏠")
        st.page_link("pages/1_📋_Agendar_Cita.py", label="📋 Agendar Cita", icon="📋")
        st.page_link("pages/2_👨‍💼_Panel_Administrador.py", label="👨‍💼 Panel Admin", icon="👨‍💼")
    
    # Página principal
    st.title("💈 Bienvenido a Mi Peluquería")
    st.markdown("---")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("🎯 Sistema de Gestión de Citas")
        st.markdown("""
        ### ¡Bienvenido a nuestro sistema de citas!
        
        **Para clientes:**
        📋 **Agenda tu cita** - Encuentra horarios disponibles y reserva tu turno
        ✉️ **Recibe confirmación** - Tu cita queda registrada inmediatamente
        
        **Para el administrador:**
        👨‍💼 **Panel de control** - Gestiona todas las citas del día
        ⏱️ **Control de tiempos** - Registra inicio y fin de cada servicio
        ⚙️ **Configura horarios** - Define tu disponibilidad fácilmente
        📊 **Reportes detallados** - Analiza tu productividad
        """)
        
        # Botones de acción principales
        col_btn1, col_btn2 = st.columns(2)
        with col_btn1:
            if st.button("📋 Agendar Nueva Cita", type="primary", use_container_width=True):
                st.switch_page("pages/1_📋_Agendar_Cita.py")
        with col_btn2:
            if st.button("👨‍💼 Panel Administrador", type="secondary", use_container_width=True):
                st.switch_page("pages/2_👨‍💼_Panel_Administrador.py")
    
    with col2:
        st.subheader("📅 Próximas Citas Hoy")
        try:
            citas_hoy = gsheets_manager.get_today_appointments()
            if citas_hoy is not None and not citas_hoy.empty and 'Cliente' in citas_hoy.columns and 'Hora_Cita' in citas_hoy.columns:
                # Ordenar por hora
                citas_hoy = citas_hoy.sort_values('Hora_Cita')
                for _, cita in citas_hoy.head(5).iterrows():
                    status_color = {
                        "Agendada": "🟡",
                        "En Progreso": "🔴", 
                        "Completada": "🟢",
                        "Cancelada": "⚫"
                    }.get(cita.get("Estado", "Agendada"), "⚪")
                    
                    st.write(f"{status_color} **{cita['Hora_Cita']}** - {cita['Cliente']}")
                    st.caption(f"Servicio: {cita.get('Servicio', 'No especificado')}")
                    st.markdown("---")
                
                if len(citas_hoy) > 5:
                    st.caption(f"Y {len(citas_hoy) - 5} citas más...")
            else:
                st.info("✅ No hay citas para hoy")
        except Exception as e:
            st.info("✅ No hay citas para hoy")
    
    # Información de contacto
    st.markdown("---")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("### 🕒 Horarios")
        st.markdown("""
        Lunes a Viernes: 9:00 - 18:00  
        Sábados: 9:00 - 14:00  
        Domingos: Cerrado
        """)
    
    with col2:
        st.markdown("### 📍 Ubicación")
        st.markdown("""
        Av. Principal #123  
        Ciudad, Estado  
        Tel: (555) 123-4567
        """)
    
    with col3:
        st.markdown("### 💻 Soporte")
        st.markdown("""
        ¿Necesitas ayuda?  
        Contacta al administrador  
        admin@peluqueria.com
        """)

if __name__ == "__main__":
    main()