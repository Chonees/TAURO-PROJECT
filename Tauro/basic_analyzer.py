"""
TAURO Project - Basic Analyzer (Bilingüe)
Análisis básico de eventos de hojas de tiempo SIN IA
Soporte completo para español e inglés
"""

import json
from typing import List, Dict, Any
from datetime import datetime
from collections import Counter

class BasicTimeSheetAnalyzer:
    """
    Analizador básico para eventos de hojas de tiempo marítimas
    """
    
    def analyze_timesheet_events(self, events: List[Dict[str, Any]], filename: str = "") -> Dict[str, Any]:
        """
        Analizar eventos de hojas de tiempo con lógica básica
        """
        if not events:
            return {
                'success': False,
                'error': 'No hay eventos para analizar',
                'analysis': None
            }
        
        try:
            # Análisis básico
            analysis = self._perform_basic_analysis(events, filename)
            
            return {
                'success': True,
                'analysis': analysis,
                'events_count': len(events),
                'filename': filename,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Error en análisis básico: {str(e)}',
                'analysis': None
            }
    
    def _perform_basic_analysis(self, events: List[Dict[str, Any]], filename: str) -> Dict[str, Any]:
        """Realizar análisis básico de eventos"""
        
        # Estadísticas básicas
        total_events = len(events)
        sheets = list(set(event.get('Sheet', 'Unknown') for event in events))
        
        # Análisis de fechas
        dates = [event.get('Date') for event in events if event.get('Date')]
        date_range = self._analyze_dates(dates)
        
        # Categorización de eventos
        event_categories = self._categorize_events(events)
        
        # Análisis temporal
        time_analysis = self._analyze_timeline(events)
        
        # Generar reporte estructurado
        sections = {
            'resumen_ejecutivo': self._generate_executive_summary(
                total_events, sheets, date_range, event_categories, filename
            ),
            'analisis_temporal': self._generate_time_analysis(time_analysis, date_range),
            'eventos_criticos': self._identify_critical_events(events, event_categories),
            'recomendaciones': self._generate_recommendations(event_categories, time_analysis),
            'estadisticas': self._generate_statistics(events, event_categories)
        }
        
        return {
            'sections': sections,
            'full_text': self._combine_sections(sections),
            'metadata': {
                'total_events': total_events,
                'sheets_processed': len(sheets),
                'date_range': date_range,
                'categories_found': len(event_categories)
            }
        }
    
    def _analyze_dates(self, dates: List[str]) -> Dict[str, Any]:
        """Analizar rango de fechas"""
        if not dates:
            return {'start_date': None, 'end_date': None, 'duration_days': 0}
        
        valid_dates = [d for d in dates if d and d.strip()]
        if not valid_dates:
            return {'start_date': None, 'end_date': None, 'duration_days': 0}
        
        valid_dates.sort()
        return {
            'start_date': valid_dates[0],
            'end_date': valid_dates[-1],
            'duration_days': len(set(valid_dates)),
            'total_dates': len(valid_dates)
        }
    
    def _categorize_events(self, events: List[Dict[str, Any]]) -> Dict[str, List[Dict]]:
        """Categorizar eventos por tipo - BILINGÜE (Español/Inglés)"""
        categories = {
            'Alije/Transferencia': [],
            'Carga': [],
            'Descarga': [],
            'Llegada/Salida': [],
            'Muestreo': [],
            'Inspección': [],
            'Operaciones de Tanque': [],
            'Limpieza': [],
            'Certificación': [],
            'Otros': []
        }
        
        for event in events:
            event_text = str(event.get('Event', '')).lower()
            categorized = False
            
            # Patrones de categorización BILINGÜE
            patterns = {
                'Alije/Transferencia': [
                    # Inglés
                    'barges', 'barge', 'cast off', 'approach', 'line on board', 'all fast',
                    'hoses connected', 'alongside', 'mooring', 'unmoor', 'berth', 'departure',
                    'first line', 'last line', 'ship to ship', 'transfer',
                    # Español
                    'barcazas', 'barcaza', 'atraque', 'desatraque', 'amarre', 'desamarre',
                    'aproximación', 'acercamiento', 'transferencia', 'alije', 'mangueras conectadas',
                    'primera línea', 'última línea', 'buque a buque'
                ],
                'Carga': [
                    # Inglés
                    'loading', 'load', 'cargo loading', 'start loading', 'finish loading',
                    'loading completed', 'loading operation',
                    # Español
                    'carga', 'cargar', 'cargando', 'inicio carga', 'fin carga',
                    'carga completada', 'operación de carga', 'embarque'
                ],
                'Descarga': [
                    # Inglés
                    'discharge', 'unload', 'unloading', 'cargo discharge', 'discharge completed',
                    # Español
                    'descarga', 'descargar', 'descargando', 'descarga completada', 'desembarque'
                ],
                'Llegada/Salida': [
                    # Inglés
                    'arrival', 'arrive', 'departure', 'depart', 'eta', 'etd', 'pilot on board',
                    'pilot off', 'tug', 'tugboat', 'escort', 'anchor',
                    # Español
                    'llegada', 'llegar', 'salida', 'salir', 'práctico a bordo', 'práctico fuera',
                    'remolcador', 'escolta', 'ancla', 'fondeo'
                ],
                'Muestreo': [
                    # Inglés
                    'sample', 'sampling', 'samples taken', 'sample collection', 'laboratory sample',
                    # Español
                    'muestra', 'muestras', 'muestreo', 'toma de muestras', 'recolección muestras',
                    'muestra laboratorio'
                ],
                'Inspección': [
                    # Inglés
                    'inspection', 'inspections', 'survey', 'check', 'verification', 'examine',
                    'tank inspection', 'cargo inspection', 'safety inspection',
                    # Español
                    'inspección', 'inspecciones', 'verificación', 'revisión', 'chequeo',
                    'inspección tanques', 'inspección carga', 'inspección seguridad', 'verificar'
                ],
                'Operaciones de Tanque': [
                    # Inglés
                    'tank', 'tanks', 'cargo tank', 'pump', 'pumping', 'valve', 'pipeline',
                    'manifold', 'cargo system', 'tank cleaning', 'tank preparation',
                    # Español
                    'tanque', 'tanques', 'tanque carga', 'bomba', 'bombeo', 'válvula',
                    'tubería', 'colector', 'sistema carga', 'limpieza tanque', 'preparación tanque'
                ],
                'Limpieza': [
                    # Inglés
                    'cleaning', 'wash', 'clean', 'tank cleaning', 'cargo cleaning',
                    # Español
                    'limpieza', 'lavado', 'limpiar', 'limpieza tanque', 'limpieza carga'
                ],
                'Certificación': [
                    # Inglés
                    'certificate', 'certification', 'cert', 'document', 'documentation',
                    # Español
                    'certificado', 'certificación', 'documento', 'documentación'
                ]
            }
            
            for category, keywords in patterns.items():
                if any(keyword in event_text for keyword in keywords):
                    categories[category].append(event)
                    categorized = True
                    break
            
            if not categorized:
                categories['Otros'].append(event)
        
        # Filtrar categorías vacías
        return {k: v for k, v in categories.items() if v}
    
    def _analyze_timeline(self, events: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analizar cronología de eventos"""
        timeline = []
        
        for event in events:
            date = event.get('Date', '')
            time = event.get('Time', '')
            event_name = event.get('Event', '')
            
            if date and event_name:
                timeline.append({
                    'datetime': f"{date} {time}".strip(),
                    'event': event_name,
                    'date': date,
                    'time': time
                })
        
        # Ordenar por fecha
        timeline.sort(key=lambda x: x['date'])
        
        return {
            'chronological_events': timeline,
            'first_event': timeline[0] if timeline else None,
            'last_event': timeline[-1] if timeline else None,
            'total_timeline_events': len(timeline)
        }
    
    def _generate_executive_summary(self, total_events: int, sheets: List[str], 
                                  date_range: Dict, categories: Dict, filename: str) -> str:
        """Generar resumen ejecutivo"""
        
        duration = date_range.get('duration_days', 0)
        start_date = date_range.get('start_date', 'N/A')
        end_date = date_range.get('end_date', 'N/A')
        
        summary = f"""
**RESUMEN EJECUTIVO - {filename}**

Se procesó exitosamente un reporte de operaciones marítimas conteniendo {total_events} eventos 
distribuidos en {len(sheets)} hojas de trabajo.

**Período de Operación:**
- Fecha inicio: {start_date}
- Fecha fin: {end_date}
- Duración: {duration} días

**Tipos de Operaciones Identificadas:**
"""
        
        for category, events in categories.items():
            summary += f"- {category}: {len(events)} eventos\n"
        
        summary += f"""
**Hojas Procesadas:**
{', '.join(sheets)}

La operación muestra un registro completo de actividades marítimas con eventos 
bien documentados a lo largo del período especificado.
        """
        
        return summary.strip()
    
    def _generate_time_analysis(self, time_analysis: Dict, date_range: Dict) -> str:
        """Generar análisis temporal"""
        
        timeline = time_analysis.get('chronological_events', [])
        first_event = time_analysis.get('first_event')
        last_event = time_analysis.get('last_event')
        
        analysis = f"""
**ANÁLISIS TEMPORAL**

**Cronología de Operaciones:**
- Primer evento registrado: {first_event['event'] if first_event else 'N/A'}
- Último evento registrado: {last_event['event'] if last_event else 'N/A'}
- Total de eventos con timestamp: {len(timeline)}

**Distribución Temporal:**
- Período total: {date_range.get('duration_days', 0)} días
- Promedio de eventos por día: {len(timeline) / max(date_range.get('duration_days', 1), 1):.1f}

**Secuencia de Operaciones:**
"""
        
        # Mostrar primeros 5 eventos de la cronología
        for i, event in enumerate(timeline[:5]):
            analysis += f"{i+1}. {event['datetime']} - {event['event']}\n"
        
        if len(timeline) > 5:
            analysis += f"... y {len(timeline) - 5} eventos adicionales\n"
        
        return analysis.strip()
    
    def _identify_critical_events(self, events: List[Dict], categories: Dict) -> str:
        """Identificar eventos críticos"""
        
        critical = """
**EVENTOS CRÍTICOS IDENTIFICADOS**

**Eventos de Carga/Descarga:**
"""
        
        # Eventos de carga
        if 'Carga' in categories:
            critical += f"- Se registraron {len(categories['Carga'])} eventos de carga\n"
            for event in categories['Carga'][:3]:  # Primeros 3
                critical += f"  • {event.get('Date', 'N/A')} - {event.get('Event', 'N/A')}\n"
        
        # Eventos de descarga
        if 'Descarga' in categories:
            critical += f"- Se registraron {len(categories['Descarga'])} eventos de descarga\n"
            for event in categories['Descarga'][:3]:  # Primeros 3
                critical += f"  • {event.get('Date', 'N/A')} - {event.get('Event', 'N/A')}\n"
        
        # Eventos de inspección
        if 'Inspección' in categories:
            critical += f"\n**Eventos de Inspección:**\n"
            critical += f"- Se realizaron {len(categories['Inspección'])} inspecciones\n"
        
        # Eventos de certificación
        if 'Certificación' in categories:
            critical += f"\n**Certificaciones:**\n"
            critical += f"- Se emitieron {len(categories['Certificación'])} certificados\n"
        
        return critical.strip()
    
    def _generate_recommendations(self, categories: Dict, time_analysis: Dict) -> str:
        """Generar recomendaciones"""
        
        recommendations = """
**RECOMENDACIONES OPERACIONALES**

**Documentación:**
- ✅ El registro de eventos está completo y bien estructurado
- ✅ Se mantiene trazabilidad temporal de las operaciones

**Eficiencia Operacional:**
"""
        
        total_events = sum(len(events) for events in categories.values())
        
        if total_events > 20:
            recommendations += "- Operación compleja con múltiples actividades bien documentadas\n"
        elif total_events > 10:
            recommendations += "- Operación estándar con documentación adecuada\n"
        else:
            recommendations += "- Operación simple con eventos básicos registrados\n"
        
        recommendations += """
**Cumplimiento:**
- Verificar que todos los certificados requeridos estén presentes
- Confirmar que las inspecciones se realizaron según protocolo
- Validar que los tiempos de carga/descarga estén dentro de parámetros

**Mejoras Sugeridas:**
- Mantener la consistencia en el formato de registro de eventos
- Asegurar que todos los eventos incluyan fecha y hora precisas
- Considerar agregar más detalles en eventos críticos
        """
        
        return recommendations.strip()
    
    def _generate_statistics(self, events: List[Dict], categories: Dict) -> str:
        """Generar estadísticas detalladas"""
        
        stats = """
**ESTADÍSTICAS DETALLADAS**

**Distribución por Categorías:**
"""
        
        total = len(events)
        for category, category_events in categories.items():
            percentage = (len(category_events) / total) * 100
            stats += f"- {category}: {len(category_events)} eventos ({percentage:.1f}%)\n"
        
        # Análisis por hojas
        sheets_count = Counter(event.get('Sheet', 'Unknown') for event in events)
        stats += f"\n**Distribución por Hojas:**\n"
        for sheet, count in sheets_count.most_common():
            percentage = (count / total) * 100
            stats += f"- {sheet}: {count} eventos ({percentage:.1f}%)\n"
        
        return stats.strip()
    
    def _combine_sections(self, sections: Dict[str, str]) -> str:
        """Combinar todas las secciones en un texto completo"""
        
        full_text = ""
        for section_name, content in sections.items():
            full_text += f"\n{content}\n\n"
        
        return full_text.strip()

def analyze_events_basic(events: List[Dict[str, Any]], filename: str = "") -> Dict[str, Any]:
    """
    Función helper para análisis básico sin IA
    """
    try:
        analyzer = BasicTimeSheetAnalyzer()
        return analyzer.analyze_timesheet_events(events, filename)
    except Exception as e:
        return {
            'success': False,
            'error': f'Error en análisis básico: {str(e)}',
            'analysis': None
        }
