import gspread
import pandas as pd
from datetime import datetime, date, time, timedelta
from google.oauth2.service_account import Credentials
import streamlit as st
import json

class GoogleSheetsManager:
    def __init__(self):
        self.client = None
        self.spreadsheet = None
        self._cached_appointments = None
        self._cache_time = None
        self._initialize_client()
    
    def _initialize_client(self):
        """Inicializa el cliente de Google Sheets"""
        try:
            scope = [
                "https://spreadsheets.google.com/feeds",
                "https://www.googleapis.com/auth/drive"
            ]
            
            # SOLO usar secrets de Streamlit (más seguro para deploy)
            if 'gsheets_credentials' in st.secrets:
                creds_dict = dict(st.secrets['gsheets_credentials'])
                creds = Credentials.from_service_account_info(creds_dict, scopes=scope)
            else:
                # Para desarrollo local, puedes mantener el archivo JSON
                # Pero en producción solo usará secrets
                raise Exception("No se encontraron credenciales en secrets.toml")
            
            self.client = gspread.authorize(creds)
            
            # ABRIR LA HOJA DE CÁLCULO POR ID ESPECÍFICO
            spreadsheet_id = "17ww3br45_saSqSaTceLcoCMKTq4CzMOa1hgoGV2xZMM"
            self.spreadsheet = self.client.open_by_key(spreadsheet_id)
                
            self._initialize_sheet_references()
            print("✅ Conectado a Google Sheets correctamente")
            
        except Exception as e:
            print(f"❌ Error al conectar con Google Sheets: {str(e)}")
            self.client = None
    
    def _initialize_sheet_references(self):
        """Inicializa las referencias a las hojas existentes"""
        try:
            # Hoja de CITAS (ya existe en tu estructura)
            self.citas_sheet = self.spreadsheet.worksheet("Citas")
            
            # Hoja de CONFIGURACIÓN de horarios (ya existe en tu estructura)
            self.horarios_config_sheet = self.spreadsheet.worksheet("Horarios_Config")
            
        except gspread.WorksheetNotFound as e:
            print(f"❌ No se encontró una hoja necesaria: {e}")
            # Intentar crear las hojas si no existen
            self._create_missing_sheets()
    
    def _create_missing_sheets(self):
        """Crea las hojas necesarias si no existen"""
        try:
            # Verificar y crear hoja Citas si no existe
            try:
                self.citas_sheet = self.spreadsheet.worksheet("Citas")
            except gspread.WorksheetNotFound:
                self.citas_sheet = self.spreadsheet.add_worksheet(
                    title="Citas", 
                    rows="1000", 
                    cols="13"
                )
                # Encabezados para citas (según tu estructura)
                headers = [
                    "ID", "Cliente", "Correo", "Teléfono", "Fecha_Cita", 
                    "Hora_Cita", "Estado", "Hora_Inicio", "Hora_Fin", 
                    "Servicio", "Notas", "Fecha_Creacion", "Ultima_Actualizacion"
                ]
                self.citas_sheet.append_row(headers)
            
            # Verificar y crear hoja Horarios_Config si no existe
            try:
                self.horarios_config_sheet = self.spreadsheet.worksheet("Horarios_Config")
            except gspread.WorksheetNotFound:
                self.horarios_config_sheet = self.spreadsheet.add_worksheet(
                    title="Horarios_Config", 
                    rows="50", 
                    cols="3"
                )
                # Configuración por defecto INCLUYENDO DOMINGO
                default_config = [
                    ["Tipo", "Valor", "Descripcion"],
                    ["HORARIO_LUNES", "09:00-18:00", "Horario para Lunes"],
                    ["HORARIO_MARTES", "09:00-18:00", "Horario para Martes"],
                    ["HORARIO_MIERCOLES", "09:00-18:00", "Horario para Miércoles"],
                    ["HORARIO_JUEVES", "09:00-18:00", "Horario para Jueves"],
                    ["HORARIO_VIERNES", "09:00-18:00", "Horario para Viernes"],
                    ["HORARIO_SABADO", "09:00-18:00", "Horario para Sábado"],
                    ["HORARIO_DOMINGO", "09:00-14:00", "Horario para Domingo"],  # ✅ DOMINGO INCLUIDO
                    ["DURACION_CITA", "30", "Duración de cada cita en minutos"],
                    ["DIAS_NO_LABORABLES", "", "Días festivos separados por comas"]
                ]
                for row in default_config:
                    self.horarios_config_sheet.append_row(row)
                    
        except Exception as e:
            print(f"❌ Error al crear hojas: {e}")
    
    def clear_cache(self):
        """Limpia la cache de citas"""
        self._cached_appointments = None
        self._cache_time = None
    
    def get_all_appointments(self):
        """Obtiene todas las citas con cache"""
        try:
            # Verificar cache (5 minutos)
            if (self._cached_appointments is not None and 
                self._cache_time and 
                (datetime.now() - self._cache_time).seconds < 300):
                return self._cached_appointments
            
            data = self.citas_sheet.get_all_records()
            df = pd.DataFrame(data)
            
            # CORRECCIÓN: Manejar DataFrame vacío correctamente
            if df.empty:
                self._cached_appointments = pd.DataFrame()
                self._cache_time = datetime.now()
                return self._cached_appointments
            
            # Asegurar que las columnas de fecha sean strings
            if 'Fecha_Cita' in df.columns:
                df['Fecha_Cita'] = df['Fecha_Cita'].astype(str)
            if 'Hora_Cita' in df.columns:
                df['Hora_Cita'] = df['Hora_Cita'].astype(str)
            
            # Filtrar filas vacías (basado en ID o Cliente)
            if 'ID' in df.columns:
                df = df[df['ID'].astype(str).str.strip() != '']
            elif 'Cliente' in df.columns:
                df = df[df['Cliente'].astype(str).str.strip() != '']
            
            self._cached_appointments = df
            self._cache_time = datetime.now()
            
            return df
            
        except Exception as e:
            print(f"Error en get_all_appointments: {e}")
            return pd.DataFrame()
    
    def get_today_appointments(self):
        """Obtiene las citas para el día de hoy"""
        try:
            df = self.get_all_appointments()
            
            # CORRECCIÓN: Verificar correctamente el DataFrame
            if df is None or df.empty:
                return pd.DataFrame()
            
            today = datetime.now().strftime("%Y-%m-%d")
            
            if 'Fecha_Cita' in df.columns:
                # Filtrar citas de hoy
                citas_hoy = df[df['Fecha_Cita'] == today]
                return citas_hoy
            
            return pd.DataFrame()
            
        except Exception as e:
            print(f"Error en get_today_appointments: {e}")
            return pd.DataFrame()
    
    def get_available_slots(self, fecha):
        """Obtiene horarios disponibles para una fecha específica"""
        try:
            citas_existentes = self.get_all_appointments()
            fecha_str = fecha.strftime("%Y-%m-%d")
            
            # CORRECCIÓN: Verificar correctamente el DataFrame
            if citas_existentes is None or citas_existentes.empty:
                citas_fecha = []
            else:
                if 'Fecha_Cita' in citas_existentes.columns and 'Hora_Cita' in citas_existentes.columns:
                    # Filtrar por fecha y obtener horarios
                    citas_filtradas = citas_existentes[citas_existentes['Fecha_Cita'] == fecha_str]
                    citas_fecha = citas_filtradas['Hora_Cita'].tolist()
                else:
                    citas_fecha = []
            
            # Obtener configuración de horarios
            config = self.get_configuracion()
            
            # Determinar día de la semana
            dia_semana = fecha.strftime("%A").lower()
            
            # Mapear días en español
            dias_map = {
                'monday': 'LUNES',
                'tuesday': 'MARTES', 
                'wednesday': 'MIERCOLES',
                'thursday': 'JUEVES',
                'friday': 'VIERNES',
                'saturday': 'SABADO',
                'sunday': 'DOMINGO'  # ✅ DOMINGO INCLUIDO
            }
            
            dia_config = dias_map.get(dia_semana, 'LUNES')
            horario_key = f"HORARIO_{dia_config}"
            
            # Obtener horario específico del día
            horario_config = config.get(horario_key, "09:00-18:00")
            
            # Generar horarios basados en la configuración
            horarios_disponibles = self._generate_time_slots(horario_config, config)
            
            # Filtrar horarios ocupados
            horarios_disponibles = [h for h in horarios_disponibles if h not in citas_fecha]
            
            return horarios_disponibles
            
        except Exception as e:
            print(f"Error en get_available_slots: {e}")
            # Slots por defecto en caso de error
            return [
                "09:00", "09:30", "10:00", "10:30", "11:00", "11:30",
                "14:00", "14:30", "15:00", "15:30", "16:00", "16:30", "17:00"
            ]
    
    def _generate_time_slots(self, horario_config, config):
        """Genera slots de tiempo basados en la configuración"""
        try:
            # Parsear horario (formato: "09:00-18:00")
            if "-" in horario_config:
                inicio_str, fin_str = horario_config.split("-")
                inicio = datetime.strptime(inicio_str.strip(), "%H:%M")
                fin = datetime.strptime(fin_str.strip(), "%H:%M")
            else:
                # Horario por defecto
                inicio = datetime.strptime("09:00", "%H:%M")
                fin = datetime.strptime("18:00", "%H:%M")
            
            # Duración de cita (minutos)
            duracion = int(config.get("DURACION_CITA", "30"))
            
            # Generar slots
            slots = []
            current_time = inicio
            
            while current_time + timedelta(minutes=duracion) <= fin:
                slot_str = current_time.strftime("%H:%M")
                slots.append(slot_str)
                current_time += timedelta(minutes=duracion)
            
            return slots
            
        except Exception as e:
            print(f"Error en _generate_time_slots: {e}")
            # Slots por defecto
            return [
                "09:00", "09:30", "10:00", "10:30", "11:00", "11:30",
                "14:00", "14:30", "15:00", "15:30", "16:00", "16:30", "17:00"
            ]
    
    def create_appointment(self, appointment_data):
        """Crea una nueva cita - CORREGIDO para tu estructura"""
        try:
            # Obtener el próximo ID
            next_id = self._get_next_appointment_id()
            
            # Preparar datos para la fila en el ORDEN CORRECTO de tu hoja
            nueva_cita = [
                next_id,  # ID
                appointment_data.get("cliente", ""),  # Cliente
                appointment_data.get("correo", ""),  # Correo
                appointment_data.get("Teléfono", ""),  # Teléfono
                appointment_data.get("fecha_cita", ""),  # Fecha_Cita
                appointment_data.get("hora_cita", ""),  # Hora_Cita
                "Agendada",  # Estado
                "",  # Hora_Inicio (vacío)
                "",  # Hora_Fin (vacío)
                appointment_data.get("servicio", ""),  # Servicio
                appointment_data.get("notas", ""),  # Notas
                datetime.now().strftime("%Y-%m-%d %H:%M:%S"),  # Fecha_Creacion
                datetime.now().strftime("%Y-%m-%d %H:%M:%S")   # Ultima_Actualizacion
            ]
            
            # Agregar a la hoja
            self.citas_sheet.append_row(nueva_cita)
            
            # Limpiar cache
            self.clear_cache()
            
            print(f"✅ Cita creada exitosamente - ID: {next_id}")
            return True
            
        except Exception as e:
            print(f"❌ Error en create_appointment: {e}")
            return False
    
    def _get_next_appointment_id(self):
        """Obtiene el próximo ID disponible"""
        try:
            df = self.get_all_appointments()
            if df.empty or 'ID' not in df.columns:
                return 1
            
            # Encontrar el máximo ID actual
            max_id = 0
            for id_val in df['ID']:
                try:
                    id_num = int(id_val)
                    if id_num > max_id:
                        max_id = id_num
                except (ValueError, TypeError):
                    continue
            
            return max_id + 1
            
        except Exception as e:
            print(f"Error en _get_next_appointment_id: {e}")
            # Si hay error, usar timestamp como fallback
            return int(datetime.now().timestamp())
    
    def update_appointment_status(self, cita_id, nuevo_estado, hora_inicio=None, hora_fin=None):
        """Actualiza el estado de una cita"""
        try:
            # Encontrar la fila con el ID
            cell = self.citas_sheet.find(str(cita_id))
            
            if cell:
                # Las columnas en tu hoja (basado en tu estructura):
                # ID=1, Cliente=2, Correo=3, Teléfono=4, Fecha_Cita=5, Hora_Cita=6, 
                # Estado=7, Hora_Inicio=8, Hora_Fin=9, Servicio=10, Notas=11, 
                # Fecha_Creacion=12, Ultima_Actualizacion=13
                
                # Actualizar estado (columna 7)
                self.citas_sheet.update_cell(cell.row, 7, nuevo_estado)
                
                # Actualizar horas si se proporcionan
                if hora_inicio and nuevo_estado == "En Progreso":
                    self.citas_sheet.update_cell(cell.row, 8, hora_inicio.strftime("%H:%M"))
                
                if hora_fin and nuevo_estado == "Completada":
                    self.citas_sheet.update_cell(cell.row, 9, hora_fin.strftime("%H:%M"))
                
                # Actualizar última actualización
                self.citas_sheet.update_cell(cell.row, 13, datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
                
                # Limpiar cache
                self.clear_cache()
                
                return True
            return False
            
        except Exception as e:
            print(f"Error en update_appointment_status: {e}")
            return False
    
    def get_configuracion(self):
        """Obtiene la configuración actual desde Horarios_Config"""
        try:
            data = self.horarios_config_sheet.get_all_records()
            config_dict = {}
            
            for row in data:
                if 'Tipo' in row and 'Valor' in row:
                    config_dict[row['Tipo']] = row['Valor']
            
            # Asegurar valores por defecto INCLUYENDO DOMINGO
            defaults = {
                "HORARIO_LUNES": "09:00-18:00",
                "HORARIO_MARTES": "09:00-18:00",
                "HORARIO_MIERCOLES": "09:00-18:00", 
                "HORARIO_JUEVES": "09:00-18:00",
                "HORARIO_VIERNES": "09:00-18:00",
                "HORARIO_SABADO": "09:00-18:00",
                "HORARIO_DOMINGO": "09:00-14:00",  # ✅ DOMINGO INCLUIDO
                "DURACION_CITA": "30",
                "DIAS_NO_LABORABLES": ""
            }
            
            for key, default_value in defaults.items():
                if key not in config_dict:
                    config_dict[key] = default_value
            
            return config_dict
            
        except Exception as e:
            print(f"Error en get_configuracion: {e}")
            # Configuración por defecto INCLUYENDO DOMINGO
            return {
                "HORARIO_LUNES": "09:00-18:00",
                "HORARIO_MARTES": "09:00-18:00",
                "HORARIO_MIERCOLES": "09:00-18:00",
                "HORARIO_JUEVES": "09:00-18:00",
                "HORARIO_VIERNES": "09:00-18:00",
                "HORARIO_SABADO": "09:00-18:00",
                "HORARIO_DOMINGO": "09:00-14:00",  # ✅ DOMINGO INCLUIDO
                "DURACION_CITA": "30",
                "DIAS_NO_LABORABLES": ""
            }
    
    def update_configuracion(self, nueva_config):
        """Actualiza la configuración en Horarios_Config"""
        try:
            # Obtener configuración actual
            config_actual = self.get_configuracion()
            
            # Actualizar valores
            for key, value in nueva_config.items():
                config_actual[key] = value
            
            # Limpiar y reescribir la hoja
            self.horarios_config_sheet.clear()
            
            # Agregar encabezados
            self.horarios_config_sheet.append_row(["Tipo", "Valor", "Descripcion"])
            
            # Agregar configuración INCLUYENDO DOMINGO
            config_items = [
                ("HORARIO_LUNES", "Horario para Lunes"),
                ("HORARIO_MARTES", "Horario para Martes"),
                ("HORARIO_MIERCOLES", "Horario para Miércoles"),
                ("HORARIO_JUEVES", "Horario para Jueves"),
                ("HORARIO_VIERNES", "Horario para Viernes"),
                ("HORARIO_SABADO", "Horario para Sábado"),
                ("HORARIO_DOMINGO", "Horario para Domingo"),  # ✅ DOMINGO INCLUIDO
                ("DURACION_CITA", "Duración de cada cita en minutos"),
                ("DIAS_NO_LABORABLES", "Días festivos separados por comas (YYYY-MM-DD)")
            ]
            
            for key, descripcion in config_items:
                valor = config_actual.get(key, "")
                self.horarios_config_sheet.append_row([key, valor, descripcion])
            
            return True
            
        except Exception as e:
            print(f"Error en update_configuracion: {e}")
            return False

# Instancia global del manager
gsheets_manager = GoogleSheetsManager()

# Funciones legacy para compatibilidad
def obtener_citas_existentes():
    """Función legacy para compatibilidad"""
    return gsheets_manager.get_all_appointments()

def guardar_cita(nombre, telefono, correo, fecha, hora):
    """Función legacy para compatibilidad"""
    appointment_data = {
        "cliente": nombre,
        "Teléfono": telefono,
        "correo": correo,
        "fecha_cita": fecha,
        "hora_cita": hora,
        "servicio": "Corte de cabello",
        "notas": ""
    }
    return gsheets_manager.create_appointment(appointment_data)
