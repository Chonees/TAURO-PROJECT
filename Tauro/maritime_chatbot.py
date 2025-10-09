"""
TAURO Project - Maritime Chatbot
Chatbot inteligente para consultas específicas sobre datos marítimos
"""

import os
import json
from typing import List, Dict, Any, Optional
from datetime import datetime
import openai
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

class MaritimeChatbot:
    """
    Chatbot especializado en datos marítimos y hojas de tiempo
    """
    
    def __init__(self):
        """Inicializar el chatbot con configuración de OpenAI"""
        self.api_key = os.getenv('OPENAI_API_KEY')
        self.model = os.getenv('OPENAI_MODEL', 'gpt-4o-mini')
        self.max_tokens = int(os.getenv('OPENAI_MAX_TOKENS', '1500'))
        self.temperature = float(os.getenv('OPENAI_TEMPERATURE', '0.7'))
        
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY no encontrada en variables de entorno")
        
        # Configurar OpenAI
        openai.api_key = self.api_key
        
        # Historial de conversación
        self.conversation_history = []
        self.current_data_context = None
        self.current_filename = None
    
    def load_data_context(self, events: List[Dict[str, Any]], cellmap: Dict[str, Any], filename: str, header_data: Dict[str, Any] = None, notes_data: Dict[str, Any] = None):
        """Cargar contexto de datos para el chatbot"""
        self.current_data_context = {
            'events': events,
            'cellmap': cellmap,
            'header_data': header_data,
            'notes_data': notes_data,
            'filename': filename,
            'loaded_at': datetime.now().isoformat()
        }
        self.current_filename = filename
        
        # Preparar resumen de datos para contexto
        self.data_summary = self._prepare_data_summary(events, cellmap, header_data, notes_data)
        
        # Reiniciar conversación con nuevo contexto
        self.conversation_history = []
        
        header_info = ""
        if header_data:
            header_info = f" | Tipo: {header_data.get('report_type', 'N/A')}"
            if header_data.get('vessels', {}).get('barge'):
                header_info += f" | Barcaza: {', '.join(header_data['vessels']['barge'])}"
        
        # Información sobre notas operacionales
        notes_info = ""
        if notes_data:
            vessel_name = "N/A"
            if notes_data.get('timesheet_header', {}).get('vessel'):
                vessel_name = notes_data['timesheet_header']['vessel']
            notes_info = f" | Embarcación: {vessel_name}"
            
            # Agregar info de datos de bombeo si están disponibles
            if notes_data.get('pumping_data'):
                pump_data = notes_data['pumping_data']
                if pump_data.get('pumping_time') or pump_data.get('pumping_rate'):
                    notes_info += " | Datos de bombeo disponibles"
            
            # Agregar info de condiciones si están disponibles
            if notes_data.get('weather_conditions'):
                weather = notes_data['weather_conditions']
                if weather.get('weather_conditions') or weather.get('sea_conditions'):
                    notes_info += " | Condiciones operacionales disponibles"
        
        welcome_message = f"""¡Hola! Soy tu asistente especializado en REPORTES MARÍTIMOS COMPLETOS.

He cargado el reporte: {filename}
📊 {len(events)} eventos registrados en TIME LOG
📅 Período: {self.data_summary['date_range']['start']} a {self.data_summary['date_range']['end']}{header_info}{notes_info}

Tengo acceso completo a:
• 📋 Datos de cabecera del reporte (embarcaciones, productos, referencias)
• ⏰ TIME LOG cronológico de eventos del inspector
• 📝 Notas operacionales (datos de bombeo, condiciones climáticas)
• 🚢 Información específica de cada embarcación

Preguntas que puedo responder:
• "¿Cuál fue la primera tarea registrada?" (TIME LOG detallado)
• "¿Qué embarcación tiene datos de bombeo?" (Notas operacionales)
• "¿Cuáles fueron las condiciones climáticas?" (Special Notes)
• "¿Cuál fue el tiempo y tasa de bombeo?" (General Notes)
• "¿En qué terminal se realizó la operación?" (Cabecera específica)
• "¿Qué producto se manejó?" (Información de la hoja)
• "¿Quién fue el inspector?" (Datos del reporte)
• "¿Qué eventos ocurrieron a las X horas?" (TIME LOG cronológico)
• "¿Cuánto duró la operación?" (Análisis completo)
• "Dame un resumen completo del reporte" (Toda la información)

¡Pregúntame lo que necesites sobre este reporte marítimo!"""
        
        return welcome_message
    
    def chat(self, user_question: str) -> Dict[str, Any]:
        """
        Procesar pregunta del usuario y generar respuesta
        """
        if not self.current_data_context:
            return {
                'success': False,
                'error': 'No hay datos cargados. Por favor, procesa un archivo Excel primero.',
                'response': None
            }
        
        try:
            # Agregar pregunta al historial
            self.conversation_history.append({
                'role': 'user',
                'content': user_question,
                'timestamp': datetime.now().isoformat()
            })
            
            # Crear prompt con contexto
            system_prompt = self._create_system_prompt()
            messages = self._build_conversation_messages(system_prompt, user_question)
            
            # Llamar a OpenAI
            response = openai.ChatCompletion.create(
                model=self.model,
                messages=messages,
                max_tokens=self.max_tokens,
                temperature=self.temperature
            )
            
            # Procesar respuesta
            bot_response = response.choices[0].message.content
            
            # Agregar respuesta al historial
            self.conversation_history.append({
                'role': 'assistant',
                'content': bot_response,
                'timestamp': datetime.now().isoformat()
            })
            
            return {
                'success': True,
                'response': bot_response,
                'filename': self.current_filename,
                'timestamp': datetime.now().isoformat(),
                'conversation_length': len(self.conversation_history)
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Error en chatbot: {str(e)}',
                'response': None
            }
    
    def _prepare_data_summary(self, events: List[Dict], cellmap: Dict, header_data: Dict = None, notes_data: Dict = None) -> Dict[str, Any]:
        """Preparar resumen de datos para contexto del chatbot"""
        
        # Estadísticas de eventos
        total_events = len(events)
        sheets = list(set(event.get('Sheet', 'Unknown') for event in events))
        
        # Fechas
        dates = [event.get('Date') for event in events if event.get('Date')]
        date_range = {
            'start': min(dates) if dates else None,
            'end': max(dates) if dates else None,
            'total_days': len(set(dates)) if dates else 0
        }
        
        # Categorización de eventos BILINGÜE (Español/Inglés)
        event_types = {}
        for event in events:
            event_text = str(event.get('Event', '')).lower()
            
            # Patrones de ALIJE/TRANSFERENCIA (Ship-to-Ship Transfer) - BILINGÜE
            alije_patterns = [
                # Inglés
                'barges', 'barge', 'cast off', 'approach', 'line on board', 'all fast', 
                'hoses connected', 'alongside', 'mooring', 'unmoor', 'berth', 'departure',
                'first line', 'last line', 'ship to ship', 'transfer',
                # Español
                'barcazas', 'barcaza', 'atraque', 'desatraque', 'amarre', 'desamarre',
                'aproximación', 'acercamiento', 'transferencia', 'alije', 'mangueras conectadas',
                'primera línea', 'última línea', 'buque a buque'
            ]
            
            # Patrones de CARGA/LOADING - BILINGÜE
            carga_patterns = [
                # Inglés
                'loading', 'load', 'cargo loading', 'start loading', 'finish loading',
                'loading completed', 'loading operation',
                # Español
                'carga', 'cargar', 'cargando', 'inicio carga', 'fin carga', 
                'carga completada', 'operación de carga'
            ]
            
            # Patrones de DESCARGA/DISCHARGE - BILINGÜE
            descarga_patterns = [
                # Inglés
                'discharge', 'unload', 'unloading', 'cargo discharge', 'discharge completed',
                # Español
                'descarga', 'descargar', 'descargando', 'descarga completada'
            ]
            
            # Patrones de MUESTREO/SAMPLING - BILINGÜE
            muestreo_patterns = [
                # Inglés
                'sample', 'sampling', 'samples taken', 'sample collection', 'laboratory sample',
                # Español
                'muestra', 'muestras', 'muestreo', 'toma de muestras', 'recolección muestras',
                'muestra laboratorio'
            ]
            
            # Patrones de INSPECCIÓN/INSPECTION - BILINGÜE
            inspeccion_patterns = [
                # Inglés
                'inspection', 'inspections', 'survey', 'check', 'verification', 'examine',
                'tank inspection', 'cargo inspection', 'safety inspection',
                # Español
                'inspección', 'inspecciones', 'verificación', 'revisión', 'chequeo',
                'inspección tanques', 'inspección carga', 'inspección seguridad'
            ]
            
            # Patrones de OPERACIONES DE TANQUE - BILINGÜE
            tanque_patterns = [
                # Inglés
                'tank', 'tanks', 'cargo tank', 'pump', 'pumping', 'valve', 'pipeline',
                'manifold', 'cargo system', 'tank cleaning', 'tank preparation',
                # Español
                'tanque', 'tanques', 'tanque carga', 'bomba', 'bombeo', 'válvula',
                'tubería', 'colector', 'sistema carga', 'limpieza tanque', 'preparación tanque'
            ]
            
            # Patrones de LLEGADA/SALIDA - BILINGÜE
            llegada_patterns = [
                # Inglés
                'arrival', 'arrive', 'departure', 'depart', 'eta', 'etd', 'pilot on board',
                'pilot off', 'tug', 'tugboat', 'escort',
                # Español
                'llegada', 'llegar', 'salida', 'salir', 'práctico a bordo', 'práctico fuera',
                'remolcador', 'escolta'
            ]
            
            # Clasificación por prioridad
            if any(pattern in event_text for pattern in alije_patterns):
                event_types['Alije/Transferencia'] = event_types.get('Alije/Transferencia', 0) + 1
            elif any(pattern in event_text for pattern in carga_patterns):
                event_types['Carga'] = event_types.get('Carga', 0) + 1
            elif any(pattern in event_text for pattern in descarga_patterns):
                event_types['Descarga'] = event_types.get('Descarga', 0) + 1
            elif any(pattern in event_text for pattern in muestreo_patterns):
                event_types['Muestreo'] = event_types.get('Muestreo', 0) + 1
            elif any(pattern in event_text for pattern in inspeccion_patterns):
                event_types['Inspección'] = event_types.get('Inspección', 0) + 1
            elif any(pattern in event_text for pattern in tanque_patterns):
                event_types['Operaciones de Tanque'] = event_types.get('Operaciones de Tanque', 0) + 1
            elif any(pattern in event_text for pattern in llegada_patterns):
                event_types['Llegada/Salida'] = event_types.get('Llegada/Salida', 0) + 1
            else:
                event_types['Otros'] = event_types.get('Otros', 0) + 1
        
        # Información de hojas
        sheet_info = {}
        for sheet in sheets:
            sheet_events = [e for e in events if e.get('Sheet') == sheet]
            sheet_info[sheet] = {
                'events_count': len(sheet_events),
                'sample_events': sheet_events[:3]  # Primeros 3 eventos como muestra
            }
        
        return {
            'total_events': total_events,
            'sheets': sheets,
            'date_range': date_range,
            'event_types': event_types,
            'sheet_info': sheet_info,
            'cellmap_sheets': list(cellmap.keys()) if cellmap else [],
            'header_data': header_data,
            'notes_data': notes_data
        }
    
    def _create_system_prompt(self) -> str:
        """Crear prompt del sistema con contexto de datos"""
        
        summary = self.data_summary
        
        # Información del header si está disponible
        header_context = ""
        if summary.get('header_data'):
            header = summary['header_data']
            header_context = f"""

INFORMACIÓN DEL REPORTE:
Tipo de reporte: {header.get('report_type', 'N/A')}
"""
            
            # Información de embarcaciones
            if header.get('vessels'):
                vessels = header['vessels']
                if vessels.get('barge'):
                    header_context += f"Barcazas: {', '.join(vessels['barge'])}\n"
                if vessels.get('tanker'):
                    header_context += f"Buques tanque: {', '.join(vessels['tanker'])}\n"
                if vessels.get('voyage'):
                    header_context += f"Viaje #: {vessels['voyage']}\n"
            
            # Información de productos
            if header.get('products', {}).get('products'):
                header_context += f"Productos: {', '.join(header['products']['products'])}\n"
            
            # Referencias comerciales
            if header.get('commercial_references'):
                header_context += "Referencias comerciales:\n"
                for ref in header['commercial_references']:
                    company = ref.get('company', '').replace('\n', ' ').strip()
                    reference = ref.get('reference', '')
                    if company and reference and reference != 'N/A':
                        header_context += f"  - {company}: {reference}\n"
            
            # Datos operacionales
            if header.get('operational_data'):
                op_data = header['operational_data']
                if op_data.get('file_number'):
                    header_context += f"Número de archivo: {op_data['file_number']}\n"
                if op_data.get('terminal'):
                    header_context += f"Terminal: {op_data['terminal']}\n"
                if op_data.get('inspector'):
                    header_context += f"Inspector: {op_data['inspector']}\n"
                if op_data.get('revised_by'):
                    header_context += f"Revisado por: {op_data['revised_by']}\n"
                if op_data.get('approved_by'):
                    header_context += f"Aprobado por: {op_data['approved_by']}\n"
                if op_data.get('operation_date'):
                    header_context += f"Fecha de operación: {op_data['operation_date']}\n"
                if op_data.get('report_date'):
                    header_context += f"Fecha de emisión del reporte: {op_data['report_date']}\n"
        
        # Información de notas operacionales si está disponible
        notes_context = ""
        if summary.get('notes_data'):
            notes = summary['notes_data']
            notes_context = f"""

DATOS DE LA HOJA DE TIEMPO ESPECÍFICA:
(La misma hoja que contiene el TIME LOG de eventos)
"""
            
            # Información específica de la hoja de tiempo
            if notes.get('timesheet_header'):
                ts_header = notes['timesheet_header']
                notes_context += "Información de cabecera de esta hoja de tiempo:\n"
                if ts_header.get('vessel'):
                    notes_context += f"  - Embarcación: {ts_header['vessel']}\n"
                if ts_header.get('terminal'):
                    notes_context += f"  - Terminal: {ts_header['terminal']}\n"
                if ts_header.get('location'):
                    notes_context += f"  - Ubicación: {ts_header['location']}\n"
                if ts_header.get('product'):
                    notes_context += f"  - Producto: {ts_header['product']}\n"
                if ts_header.get('date'):
                    notes_context += f"  - Fecha: {ts_header['date']}\n"
                if ts_header.get('file_no'):
                    notes_context += f"  - Archivo N°: {ts_header['file_no']}\n"
                notes_context += "\n"
            
            # Datos de bombeo
            if notes.get('pumping_data'):
                pump_data = notes['pumping_data']
                vessel_info = ""
                if notes.get('timesheet_header', {}).get('vessel'):
                    vessel_info = f" para {notes['timesheet_header']['vessel']}"
                
                notes_context += f"Datos de bombeo{vessel_info} (sección General Notes de esta hoja de tiempo):\n"
                if pump_data.get('pumping_time'):
                    notes_context += f"  - Tiempo de bombeo: {pump_data['pumping_time']} horas\n"
                if pump_data.get('pumping_rate'):
                    notes_context += f"  - Tasa de bombeo: {pump_data['pumping_rate']} m³/h (metros cúbicos por hora)\n"
                if pump_data.get('last_cargo'):
                    notes_context += f"  - Última carga: {pump_data['last_cargo']}\n"
                if pump_data.get('vessel_experience_factor'):
                    notes_context += f"  - Factor de experiencia del buque: {pump_data['vessel_experience_factor']}\n"
            
            # Condiciones climáticas
            if notes.get('weather_conditions'):
                weather = notes['weather_conditions']
                vessel_info = ""
                if notes.get('timesheet_header', {}).get('vessel'):
                    vessel_info = f" durante operaciones de {notes['timesheet_header']['vessel']}"
                
                if weather.get('weather_conditions'):
                    conditions = weather['weather_conditions']
                    if conditions:
                        notes_context += f"Condiciones climáticas{vessel_info} (sección Special Notes): {', '.join(conditions)}\n"
                if weather.get('sea_conditions'):
                    sea_conditions = weather['sea_conditions']
                    if sea_conditions:
                        notes_context += f"Condiciones marítimas{vessel_info} (sección Special Notes): {', '.join(sea_conditions)}\n"
            
            # Remarks
            if notes.get('remarks_and_notes', {}).get('remarks'):
                remarks = notes['remarks_and_notes']['remarks']
                if remarks:
                    notes_context += f"Observaciones: {'; '.join(remarks)}\n"
        
        system_prompt = f"""Eres un asistente especializado en análisis de REPORTES MARÍTIMOS completos que incluyen:
1. TIME LOGS (registros cronológicos de tiempo) de INSPECTORES MARÍTIMOS
2. DATOS DE CABECERA del reporte (embarcaciones, productos, referencias comerciales, etc.)
3. NOTAS OPERACIONALES (condiciones climáticas, datos de bombeo, observaciones, etc.)

CAPACIDAD BILINGÜE:
Puedes procesar y entender reportes en ESPAÑOL e INGLÉS indistintamente. Los reportes marítimos pueden contener terminología en ambos idiomas.

CONTEXTO ESPECÍFICO:
Estás analizando un REPORTE MARÍTIMO COMPLETO que incluye:
- Datos de cabecera con información del reporte, embarcaciones, productos y referencias
- HOJA DE TIEMPO específica que contiene TANTO:
  * TIME LOG cronológico de eventos del inspector marítimo
  * NOTAS OPERACIONALES (Special Notes y General Notes) con datos de bombeo y condiciones
- Ambos (eventos y notas operacionales) pertenecen a la MISMA hoja de tiempo del mismo reporte

IMPORTANTE SOBRE LA ESTRUCTURA:
- El TIME LOG y las NOTAS OPERACIONALES están en la MISMA HOJA DE TIEMPO
- Los datos de bombeo (Pumping Time, Pumping Rate) están en la sección "General Notes" de esa hoja
- Las condiciones climáticas están en la sección "Special Notes" de esa hoja
- Todo corresponde a la misma embarcación y operación específica

CRÍTICO - RELACIÓN TIME LOG Y EVENTOS:
- Los EVENTOS son exactamente el TIME LOG cronológico del inspector
- Cuando dices "TIME LOG" te refieres a los eventos registrados cronológicamente
- NO son dos cosas separadas: TIME LOG = EVENTOS = registro cronológico del inspector
- Los eventos contienen fecha, hora y descripción de cada actividad registrada
- Tienes acceso completo a todos los eventos detallados del TIME LOG

IMPORTANTE SOBRE UNIDADES:
- Tiempo de bombeo: Se expresa en HORAS
- Tasa de bombeo: Se expresa en m³/h (metros cúbicos por hora) o CBM/h (cubic meters per hour)
- Los valores negativos en bombeo indican operaciones de descarga
- Siempre especifica las unidades correctas cuando menciones datos de bombeo{header_context}{notes_context}

DATOS DEL TIME LOG:
Archivo: {self.current_filename}
Total de eventos registrados: {summary['total_events']}
Período de inspección: {summary['date_range']['start']} a {summary['date_range']['end']} ({summary['date_range']['total_days']} días)
Hojas del reporte: {', '.join(summary['sheets'])}"

TIPOS DE EVENTOS EN EL TIME LOG:
"""
        
        for event_type, count in summary['event_types'].items():
            system_prompt += f"- {event_type}: {count} eventos\n"
        
        system_prompt += f"""
INFORMACIÓN POR HOJA:
"""
        
        for sheet, info in summary['sheet_info'].items():
            system_prompt += f"- {sheet}: {info['events_count']} eventos\n"
        
        system_prompt += """
NATURALEZA DE LOS DATOS:
Los eventos que analizas provienen del script extract_timesheet_events.py que extrae:
- Eventos cronológicos con fecha, hora y descripción
- Actividades de carga/descarga de petróleo
- OPERACIONES DE ALIJE (Ship-to-Ship Transfer): transferencias entre buques y barcazas
- Inspecciones y verificaciones de seguridad
- Muestreos y análisis de calidad
- Llegadas/salidas de buques y remolcadores
- Operaciones de conexión de mangueras y líneas
- Certificaciones y documentación

TIPOS DE OPERACIONES MARÍTIMAS (BILINGÜE):

1. **ALIJE/TRANSFERENCIA (Ship-to-Ship Transfer)**:
   - Cast off / Desatraque: Separación de barcazas
   - Approach / Aproximación: Acercamiento de barcazas  
   - Mooring / Amarre: Aseguramiento de barcazas
   - First/Last line / Primera/Última línea: Líneas de amarre
   - All fast / Todo firme: Barcazas aseguradas
   - Hoses connected / Mangueras conectadas: Conexión sistema carga
   - Tank inspections / Inspección tanques: Verificación tanques

2. **CARGA DIRECTA (Direct Loading)**:
   - Loading operations / Operaciones de carga: Carga en terminal
   - Sampling / Muestreo: Toma de muestras de producto
   - Laboratory analysis / Análisis laboratorio: Verificación calidad
   - Cargo operations / Operaciones de carga: Manejo de producto

3. **DESCARGA (Discharge)**:
   - Unloading / Descarga: Operaciones de descarga
   - Discharge operations / Operaciones descarga: Transferencia producto

4. **INSPECCIONES (Inspections)**:
   - Tank inspection / Inspección tanques: Verificación tanques
   - Safety inspection / Inspección seguridad: Verificación seguridad
   - Cargo inspection / Inspección carga: Verificación producto

5. **LLEGADAS/SALIDAS (Arrivals/Departures)**:
   - Arrival / Llegada: Llegada de buques/remolcadores
   - Departure / Salida: Salida de buques/remolcadores
   - Pilot on board / Práctico a bordo: Embarque práctico

INSTRUCCIONES ESPECÍFICAS:
1. SIEMPRE recuerda que tienes acceso a un REPORTE MARÍTIMO COMPLETO:
   - DATOS DE CABECERA: información del reporte, embarcaciones, productos, referencias
   - TIME LOG: eventos cronológicos del inspector marítimo
2. Los eventos están en orden cronológico y documentan la operación completa
3. Cada evento tiene: Fecha, Hora, Descripción, Hoja de origen
4. TIENES ACCESO COMPLETO a todos los eventos detallados cuando sea necesario
5. TIENES ACCESO COMPLETO a los datos de cabecera del reporte
6. Puedes identificar la PRIMERA y ÚLTIMA actividad registrada con precisión
7. Puedes explicar la SECUENCIA completa de operaciones
8. Puedes identificar el TIPO DE OPERACIÓN basado en descripciones reales Y datos de cabecera
9. Puedes responder sobre eventos en horas específicas
10. Puedes proporcionar contexto completo usando cabecera + time log
11. Mantén contexto de que es un REPORTE DE INSPECTOR PROFESIONAL COMPLETO

MANEJO BILINGÜE:
- Reconoce terminología en ESPAÑOL e INGLÉS automáticamente
- Traduce conceptos entre idiomas cuando sea necesario
- Entiende que "BARGES CAST OFF" = "BARCAZAS SE SEPARAN"
- Entiende que "LOADING OPERATIONS" = "OPERACIONES DE CARGA"
- Entiende que "TANK INSPECTIONS" = "INSPECCIONES DE TANQUES"
- Responde en el idioma que prefiera el usuario
- Mantén consistencia técnica en ambos idiomas

EJEMPLOS DE PREGUNTAS QUE DEBES RESPONDER CORRECTAMENTE:
- "¿Cuál fue la primera tarea registrada?" → Busca el evento más temprano cronológicamente en el TIME LOG
- "¿De qué tipo de operación estamos hablando?" → Usa datos de cabecera Y eventos del TIME LOG
- "¿Qué embarcaciones participaron?" → Usa datos de cabecera + información específica de la hoja de tiempo
- "¿Qué productos se manejaron?" → Usa datos de cabecera + información específica de la hoja de tiempo
- "¿Cuáles son las referencias comerciales?" → Usa datos de cabecera (empresas y referencias)
- "¿Quién fue el inspector?" → Usa datos operacionales de cabecera
- "¿En qué terminal se realizó?" → Usa información específica de la hoja de tiempo
- "¿Cuándo comenzó la operación?" → Identifica el primer evento en el TIME LOG
- "¿Qué hizo el inspector a las X horas?" → Busca eventos específicos en esa hora en el TIME LOG
- "¿Cuánto duró la inspección?" → Calcula tiempo entre primer y último evento del TIME LOG
- "Dame detalles del TIME LOG" → Proporciona eventos cronológicos detallados con fecha, hora y descripción
- "¿Cuánto tiempo duró el bombeo?" → Usa datos de bombeo de General Notes (16.8 horas)
- "Dame un resumen completo" → Combina cabecera + TIME LOG + notas operacionales

IMPORTANTE: 
- Estás analizando un REPORTE MARÍTIMO COMPLETO con acceso a TODOS los datos
- TIME LOG = EVENTOS = registro cronológico completo del inspector
- Tienes acceso detallado a cada evento con fecha, hora y descripción
- Puedes responder sobre cualquier actividad específica registrada en el TIME LOG
- Combina información de cabecera + TIME LOG + notas operacionales para respuestas completas
- NUNCA digas que no tienes detalles de los eventos - los tienes todos disponibles
"""
        
        return system_prompt
    
    def _build_conversation_messages(self, system_prompt: str, user_question: str) -> List[Dict]:
        """Construir mensajes para la conversación"""
        
        messages = [
            {
                'role': 'system',
                'content': system_prompt
            }
        ]
        
        # Agregar historial de conversación (últimas 10 interacciones)
        recent_history = self.conversation_history[-10:] if len(self.conversation_history) > 10 else self.conversation_history
        
        for msg in recent_history[:-1]:  # Excluir la última pregunta que ya se agregará
            messages.append({
                'role': msg['role'],
                'content': msg['content']
            })
        
        # Agregar pregunta actual con contexto adicional si es necesario
        enhanced_question = self._enhance_question_with_context(user_question)
        
        # Agregar contexto completo de eventos si es relevante
        if self._needs_detailed_events(user_question):
            enhanced_question += self._get_detailed_events_context()
        
        messages.append({
            'role': 'user',
            'content': enhanced_question
        })
        
        return messages
    
    def _enhance_question_with_context(self, question: str) -> str:
        """Mejorar la pregunta con contexto adicional si es necesario"""
        
        # Agregar contexto de eventos específicos para preguntas sobre secuencia
        if any(word in question.lower() for word in ['primera', 'primer', 'último', 'final', 'comenzó', 'terminó']):
            # Obtener muestra de eventos ordenados cronológicamente
            events = self.current_data_context['events']
            sorted_events = sorted(events, key=lambda x: (x.get('Date', ''), x.get('Time', '')))
            
            first_events = sorted_events[:3]  # Primeros 3 eventos
            last_events = sorted_events[-3:]  # Últimos 3 eventos
            
            context = f"\n\nCONTEXTO DE SECUENCIA:"
            context += f"\nPrimeros eventos registrados:"
            for i, event in enumerate(first_events, 1):
                context += f"\n{i}. {event.get('Date', 'N/A')} {event.get('Time', 'N/A')} - {event.get('Event', 'N/A')}"
            
            context += f"\nÚltimos eventos registrados:"
            for i, event in enumerate(last_events, 1):
                context += f"\n{i}. {event.get('Date', 'N/A')} {event.get('Time', 'N/A')} - {event.get('Event', 'N/A')}"
            
            question += context
        
        # Si pregunta sobre tipo de operación, agregar contexto de categorías
        if any(word in question.lower() for word in ['tipo', 'operación', 'clase', 'qué']):
            question += f"\n\nCONTEXTO DE OPERACIÓN: Este es un TIME LOG de inspector marítimo con {self.data_summary['total_events']} eventos registrados"
            question += f"\nCategorías identificadas: {', '.join(self.data_summary['event_types'].keys())}"
        
        # Si pregunta sobre fechas específicas, agregar contexto
        if any(word in question.lower() for word in ['cuándo', 'fecha', 'día', 'hora', 'tiempo']):
            question += f"\n\nCONTEXTO TEMPORAL: Período de inspección del {self.data_summary['date_range']['start']} al {self.data_summary['date_range']['end']}"
        
        return question
    
    def _needs_detailed_events(self, question: str) -> bool:
        """Determinar si la pregunta necesita acceso a eventos detallados"""
        keywords = [
            'primera', 'primer', 'último', 'final', 'comenzó', 'terminó',
            'cuál', 'qué', 'cuándo', 'hora', 'tiempo', 'evento', 'actividad',
            'tarea', 'operación', 'secuencia', 'cronología', 'detalle',
            'específico', 'exacto', 'descripción'
        ]
        return any(keyword in question.lower() for keyword in keywords)
    
    def _get_detailed_events_context(self) -> str:
        """Obtener contexto detallado de todos los eventos"""
        if not self.current_data_context or not self.current_data_context['events']:
            return ""
        
        events = self.current_data_context['events']
        
        # Ordenar eventos cronológicamente
        sorted_events = sorted(events, key=lambda x: (x.get('Date', ''), x.get('Time', '')))
        
        context = f"\n\n=== EVENTOS DETALLADOS DEL TIME LOG ===\n"
        context += f"Total de eventos: {len(sorted_events)}\n\n"
        
        for i, event in enumerate(sorted_events, 1):
            date = event.get('Date', 'N/A')
            time = event.get('Time', 'N/A')
            description = event.get('Event', 'N/A')
            sheet = event.get('Sheet', 'N/A')
            
            context += f"EVENTO {i}:\n"
            context += f"  Fecha: {date}\n"
            context += f"  Hora: {time}\n"
            context += f"  Descripción: {description}\n"
            context += f"  Hoja: {sheet}\n\n"
        
        context += "=== FIN DE EVENTOS DETALLADOS ===\n"
        context += "Usa esta información detallada para responder la pregunta específica del usuario."
        
        return context
    
    def get_conversation_history(self) -> List[Dict]:
        """Obtener historial de conversación"""
        return self.conversation_history
    
    def clear_conversation(self):
        """Limpiar historial de conversación"""
        self.conversation_history = []
        return "✅ Historial de conversación limpiado"
    
    def get_data_info(self) -> Dict[str, Any]:
        """Obtener información sobre los datos cargados"""
        if not self.current_data_context:
            return {'error': 'No hay datos cargados'}
        
        return {
            'filename': self.current_filename,
            'events_count': len(self.current_data_context['events']),
            'sheets': self.data_summary['sheets'],
            'date_range': self.data_summary['date_range'],
            'event_types': self.data_summary['event_types'],
            'loaded_at': self.current_data_context['loaded_at']
        }

def create_maritime_chatbot() -> MaritimeChatbot:
    """
    Función helper para crear instancia del chatbot
    """
    try:
        return MaritimeChatbot()
    except Exception as e:
        raise ValueError(f"Error creando chatbot: {str(e)}")
