import json
import re
from datetime import datetime
from typing import List, Dict, Any, Tuple, Optional

def split_cell_reference(cell_ref: str) -> Tuple[str, int]:
    """
    Divide una referencia de celda como 'A9' en letra de columna y número de fila.
    Retorna: (columna, fila)
    """
    letters = ''.join([c for c in cell_ref if c.isalpha()])
    numbers = int(''.join([c for c in cell_ref if c.isdigit()]))
    return letters, numbers

def format_time(time_value: Any) -> Optional[str]:
    """
    Formatea el valor de tiempo a formato HH:MM.
    Maneja diferentes formatos de entrada.
    """
    if time_value is None:
        return None
    
    time_str = str(time_value).strip()
    
    # Si ya está en formato HH:MM o HH:MM/HH:MM
    if ':' in time_str:
        return time_str
    
    # Si es un número (como 2130, 730, etc.)
    if time_str.isdigit():
        if len(time_str) <= 2:
            # Números como 730 -> 07:30
            return f"{int(time_str):02d}:00"
        elif len(time_str) == 3:
            # 730 -> 07:30
            hours = int(time_str[0])
            minutes = int(time_str[1:])
            return f"{hours:02d}:{minutes:02d}"
        elif len(time_str) == 4:
            # 2130 -> 21:30
            hours = int(time_str[:2])
            minutes = int(time_str[2:])
            return f"{hours:02d}:{minutes:02d}"
    
    return time_str

def format_date(date_value: Any) -> Optional[str]:
    """
    Formatea el valor de fecha a formato YYYY-MM-DD.
    """
    if date_value is None:
        return None
    
    date_str = str(date_value).strip()
    
    # Si contiene fecha y hora, extraer solo la fecha
    if ' ' in date_str:
        date_str = date_str.split(' ')[0]
    
    return date_str

def find_timesheet_headers(data: Dict[str, Any]) -> List[Dict[str, str]]:
    """
    Busca todas las secciones de hojas de tiempo en el JSON.
    Retorna una lista de diccionarios con las posiciones de los encabezados.
    """
    header_sections = []
    
    # Buscar patrones de encabezados
    for cell_ref, value in data.items():
        if not isinstance(value, str):
            continue
            
        value_clean = value.strip().lower()
        
        # Patrón 1: Event, Date, Time (formato inglés)
        if value_clean == "event":
            col_event, row = split_cell_reference(cell_ref)
            
            # Buscar Date y Time en la misma fila
            date_found = False
            time_found = False
            col_date = None
            col_time = None
            
            for other_cell, other_value in data.items():
                if isinstance(other_value, str):
                    other_col, other_row = split_cell_reference(other_cell)
                    if other_row == row:
                        if other_value.strip().lower() == "date":
                            col_date = other_col
                            date_found = True
                        elif other_value.strip().lower() == "time":
                            col_time = other_col
                            time_found = True
            
            if date_found and time_found:
                header_sections.append({
                    'format': 'english',
                    'event_col': col_event,
                    'date_col': col_date,
                    'time_col': col_time,
                    'start_row': row + 1
                })
        
        # Patrón 2: DATE, HRS, EVENT (formato español)
        elif value_clean == "date" and cell_ref.startswith('A'):
            col_date, row = split_cell_reference(cell_ref)
            
            # Buscar HRS y EVENT en la misma fila
            hrs_found = False
            event_found = False
            col_time = None
            col_event = None
            
            for other_cell, other_value in data.items():
                if isinstance(other_value, str):
                    other_col, other_row = split_cell_reference(other_cell)
                    if other_row == row:
                        if other_value.strip().lower() in ["hrs", "time"]:
                            col_time = other_col
                            hrs_found = True
                        elif other_value.strip().lower() == "event":
                            col_event = other_col
                            event_found = True
            
            if hrs_found and event_found:
                header_sections.append({
                    'format': 'spanish',
                    'event_col': col_event,
                    'date_col': col_date,
                    'time_col': col_time,
                    'start_row': row + 1
                })
    
    return header_sections

def extract_events_from_section(data: Dict[str, Any], section: Dict[str, str]) -> List[Dict[str, Any]]:
    """
    Extrae eventos de una sección específica de la hoja de tiempo.
    """
    events = []
    row = section['start_row']
    
    while True:
        # Construir referencias de celdas para la fila actual
        event_cell = f"{section['event_col']}{row}"
        date_cell = f"{section['date_col']}{row}"
        time_cell = f"{section['time_col']}{row}"
        
        # Verificar si existe la celda de evento
        if event_cell not in data:
            break
            
        event_value = data.get(event_cell)
        date_value = data.get(date_cell)
        time_value = data.get(time_cell)
        
        # Si no hay evento, terminar
        if not event_value or (isinstance(event_value, str) and not event_value.strip()):
            break
        
        # Crear el evento
        event = {
            "Event": str(event_value).strip(),
            "Date": format_date(date_value),
            "Time": format_time(time_value),
            "Section": section['format'],
            "Row": row
        }
        
        events.append(event)
        row += 1
    
    return events

def extract_timesheet_events(json_file_path: str) -> List[Dict[str, Any]]:
    """
    Función principal que extrae todos los eventos de las hojas de tiempo desde un archivo.
    """
    # Cargar el JSON
    with open(json_file_path, 'r', encoding='utf-8') as file:
        data = json.load(file)
    
    return extract_timesheet_events_from_data(data)

def extract_timesheet_events_from_data(data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Función principal que extrae todos los eventos de las hojas de tiempo desde datos en memoria.
    """
    all_events = []
    
    # Procesar cada hoja en el JSON
    for sheet_name, sheet_data in data.items():
        print(f"Procesando hoja: {sheet_name}")
        
        # Buscar secciones de hojas de tiempo en esta hoja
        header_sections = find_timesheet_headers(sheet_data)
        
        print(f"  Encontradas {len(header_sections)} secciones de eventos")
        
        # Extraer eventos de cada sección
        for i, section in enumerate(header_sections):
            print(f"  Procesando sección {i+1} (formato: {section['format']})")
            section_events = extract_events_from_section(sheet_data, section)
            
            # Agregar información de la hoja y sección
            for event in section_events:
                event['Sheet'] = sheet_name
                event['Section_Number'] = i + 1
            
            all_events.extend(section_events)
            print(f"    Extraídos {len(section_events)} eventos")
    
    return all_events

def save_events_to_json(events: List[Dict[str, Any]], output_path: str):
    """
    Guarda los eventos extraídos en un archivo JSON.
    """
    with open(output_path, 'w', encoding='utf-8') as file:
        json.dump(events, file, indent=2, ensure_ascii=False)

def main():
    # Rutas de archivos
    input_file = r"c:\Users\Admin\Desktop\TAURO PROYECT\Tauro\output\15006 A2 -BL 04 HAFNIA ANDESINE to  AZ 108 & 112 FINAL REPORT_cellmap.json"
    output_file = r"c:\Users\Admin\Desktop\TAURO PROYECT\Tauro\output\ALIJE_events.json"
    
    try:
        print("Iniciando extracción de eventos de hojas de tiempo...")
        print(f"Archivo de entrada: {input_file}")
        
        # Extraer eventos
        events = extract_timesheet_events(input_file)
        
        print(f"\nTotal de eventos extraídos: {len(events)}")
        
        # Guardar resultados
        save_events_to_json(events, output_file)
        print(f"Eventos guardados en: {output_file}")
        
        # Mostrar algunos ejemplos
        if events:
            print("\n--- Primeros 5 eventos ---")
            for i, event in enumerate(events[:5]):
                print(f"{i+1}. {event['Event']} | {event['Date']} | {event['Time']} | Hoja: {event['Sheet']}")
        
        # Estadísticas por hoja
        sheets = {}
        for event in events:
            sheet = event['Sheet']
            if sheet not in sheets:
                sheets[sheet] = 0
            sheets[sheet] += 1
        
        print(f"\n--- Eventos por hoja ---")
        for sheet, count in sheets.items():
            print(f"{sheet}: {count} eventos")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
