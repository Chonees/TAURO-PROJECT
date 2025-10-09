#!/usr/bin/env python3
"""
Script para extraer notas operacionales de reportes marítimos.
Extrae información de Special Notes y General Notes de las hojas de tiempo,
incluyendo pumping time, pumping rate, condiciones climáticas, etc.
"""

import json
import sys
import re
from pathlib import Path
from typing import Dict, List, Any, Optional

def split_cell_reference(cell_ref: str) -> tuple:
    """Divide una referencia de celda como 'A9' en letra de columna y número de fila."""
    letters = ''.join([c for c in cell_ref if c.isalpha()])
    numbers = int(''.join([c for c in cell_ref if c.isdigit()]))
    return letters, numbers

def find_notes_structure(sheet_data: Dict[str, str]) -> Optional[Dict[str, Any]]:
    """Busca la estructura de Special Notes y General Notes."""
    structure = {
        'special_notes_found': False,
        'general_notes_found': False,
        'special_notes_col': None,
        'general_notes_col': None,
        'start_row': None
    }
    
    for cell_ref, value in sheet_data.items():
        if not value or not isinstance(value, str):
            continue
            
        value_clean = value.strip()
        col, row = split_cell_reference(cell_ref)
        
        # Buscar "Special Notes"
        if 'Special Notes' in value_clean:
            structure['special_notes_found'] = True
            structure['special_notes_col'] = col
            structure['start_row'] = row
        
        # Buscar "General Notes"
        elif 'General Notes' in value_clean:
            structure['general_notes_found'] = True
            structure['general_notes_col'] = col
            if not structure['start_row']:
                structure['start_row'] = row
    
    if structure['special_notes_found'] or structure['general_notes_found']:
        return structure
    return None

def extract_weather_conditions(sheet_data: Dict[str, str], structure: Dict[str, Any]) -> Dict[str, Any]:
    """Extrae condiciones climáticas basándose en la estructura de la tabla."""
    weather_info = {
        'weather_conditions': [],
        'sea_conditions': []
    }
    
    if not structure or not structure['start_row']:
        return weather_info
    
    # Buscar condiciones climáticas en las filas siguientes a Special Notes
    weather_keywords = ['Rain', 'Cloudy', 'Clear']
    sea_keywords = ['Rough', 'Choppy', 'Calm']
    
    # Buscar en un rango de filas después del encabezado
    for row_offset in range(1, 10):  # Buscar en las siguientes 10 filas
        current_row = structure['start_row'] + row_offset
        
        # Buscar en diferentes columnas
        for col_offset in ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J']:
            cell_ref = f"{col_offset}{current_row}"
            if cell_ref in sheet_data:
                value = sheet_data[cell_ref]
                if not value:
                    continue
                    
                value_clean = str(value).strip()
                
                # Buscar condiciones climáticas con X
                for condition in weather_keywords:
                    if condition in value_clean and 'X' in value_clean:
                        weather_info['weather_conditions'].append(condition.lower())
                
                # Buscar condiciones marítimas con X
                for condition in sea_keywords:
                    if condition in value_clean and 'X' in value_clean:
                        weather_info['sea_conditions'].append(condition.lower())
    
    return weather_info

def extract_timesheet_header(sheet_data: Dict[str, str]) -> Dict[str, Any]:
    """Extrae los datos de cabecera de la hoja de tiempo específica."""
    header_data = {}
    
    # Campos que buscamos en la cabecera de la hoja de tiempo
    header_fields = {
        'vessel': 'Vessel',
        'terminal': 'Terminal', 
        'location': 'Location',
        'product': 'Product',
        'date': 'Date',
        'file_no': 'File N'
    }
    
    print("  Extrayendo cabecera de hoja de tiempo...")
    
    # Buscar en las primeras filas (típicamente la cabecera está arriba)
    for cell_ref, value in sheet_data.items():
        if not value or not isinstance(value, str):
            continue
            
        col, row = split_cell_reference(cell_ref)
        
        # Solo buscar en las primeras 15 filas (cabecera)
        if row > 15:
            continue
            
        value_clean = str(value).strip()
        
        # Buscar cada campo de cabecera con formato "Campo: Valor"
        for field_key, field_name in header_fields.items():
            if field_key not in header_data and field_name in value_clean and ':' in value_clean:
                # Extraer el valor después de los dos puntos
                parts = value_clean.split(':', 1)
                if len(parts) > 1:
                    field_value = parts[1].strip()
                    if field_value and field_value != field_name and len(field_value) > 1:
                        header_data[field_key] = field_value
                        print(f"    Encontrado {field_name}: {field_value}")
                        
        # También buscar valores en celdas adyacentes cuando encontramos solo el nombre del campo
        for field_key, field_name in header_fields.items():
            if field_key not in header_data and value_clean == field_name:
                # Para la estructura específica que vemos: B3=Vessel, D3=Valor
                # Buscar específicamente en la columna D si estamos en la columna B
                if col == 'B':
                    target_cell = f"D{row}"
                    if target_cell in sheet_data and sheet_data[target_cell]:
                        target_value = str(sheet_data[target_cell]).strip()
                        if target_value and target_value != field_name and len(target_value) > 1:
                            if target_value not in header_fields.values():
                                header_data[field_key] = target_value
                                print(f"    Encontrado {field_name}: {target_value}")
                                continue
                
                # Si no está en B->D, buscar en otras celdas adyacentes
                adjacent_cells = [
                    f"{chr(ord(col) + 1)}{row}",  # Celda a la derecha
                    f"{chr(ord(col) + 2)}{row}",  # Dos celdas a la derecha
                    f"{chr(ord(col) + 3)}{row}",  # Tres celdas a la derecha
                    f"{col}{row + 1}",           # Celda abajo
                ]
                
                for adj_cell in adjacent_cells:
                    if adj_cell in sheet_data and sheet_data[adj_cell]:
                        adj_value = str(sheet_data[adj_cell]).strip()
                        if adj_value and adj_value != field_name and len(adj_value) > 1:
                            # Verificar que no sea otro nombre de campo
                            if adj_value not in header_fields.values():
                                header_data[field_key] = adj_value
                                print(f"    Encontrado {field_name} (adyacente): {adj_value}")
                                break
    
    print(f"    Cabecera extraída: {header_data}")
    return header_data

def extract_pumping_data(sheet_data: Dict[str, str], structure: Dict[str, Any]) -> Dict[str, Any]:
    """Extrae datos de bombeo basándose en la estructura de General Notes."""
    pumping_data = {}
    
    if not structure or not structure['start_row']:
        return pumping_data
    
    # Definir los campos que buscamos y su orden típico en la tabla
    field_patterns = [
        ('pumping_time', 'Pumping Time'),
        ('pumping_rate', 'Pumping Rate'),
        ('last_cargo', 'Last Cargo'),
        ('second_last', 'Second Last'),
        ('third_last', 'Third Last'),
        ('vessel_experience_factor', 'Vessel Experience Factor')
    ]
    
    # Buscar en un rango de filas después del encabezado General Notes
    for row_offset in range(1, 15):  # Buscar en las siguientes 15 filas
        current_row = structure['start_row'] + row_offset
        
        # Buscar en diferentes columnas (especialmente las de General Notes)
        for col_offset in ['G', 'H', 'I', 'J', 'K', 'L', 'M', 'N', 'O', 'P']:
            cell_ref = f"{col_offset}{current_row}"
            if cell_ref in sheet_data:
                value = sheet_data[cell_ref]
                if not value:
                    continue
                    
                value_clean = str(value).strip()
                
                # Buscar cada campo específico
                for field_key, field_name in field_patterns:
                    if field_name in value_clean:
                        # Si encontramos el nombre del campo, buscar el valor en celdas adyacentes
                        # Buscar en la celda de abajo (misma columna, fila siguiente)
                        value_cell_ref = f"{col_offset}{current_row + 1}"
                        if value_cell_ref in sheet_data:
                            field_value = sheet_data[value_cell_ref]
                            if field_value:
                                field_value_clean = str(field_value).strip()
                                
                                # Para pumping_time y pumping_rate, convertir a número
                                if field_key in ['pumping_time', 'pumping_rate']:
                                    try:
                                        # Buscar números (incluyendo negativos)
                                        num_match = re.search(r'(-?\d+[.,]?\d*)', field_value_clean)
                                        if num_match:
                                            pumping_data[field_key] = float(num_match.group(1).replace(',', '.'))
                                    except ValueError:
                                        pumping_data[field_key] = field_value_clean
                                else:
                                    # Para otros campos, guardar como texto
                                    pumping_data[field_key] = field_value_clean
    
    # Si no encontramos los valores con el método anterior, buscar números específicos
    if 'pumping_time' not in pumping_data or 'pumping_rate' not in pumping_data:
        # Buscar celdas que contengan solo números negativos
        for cell_ref, value in sheet_data.items():
            if not value:
                continue
            
            value_clean = str(value).strip()
            # Buscar números negativos específicos
            if re.match(r'^-?\d+[.,]?\d*$', value_clean):
                try:
                    num_value = float(value_clean.replace(',', '.'))
                    # Pumping Time típicamente está entre -50 y 0
                    if 'pumping_time' not in pumping_data and -50 < num_value < 0:
                        pumping_data['pumping_time'] = num_value
                    # Pumping Rate típicamente es un número más grande negativo
                    elif 'pumping_rate' not in pumping_data and num_value < -100:
                        pumping_data['pumping_rate'] = num_value
                except ValueError:
                    continue
    
    return pumping_data

def extract_remarks_and_notes(sheet_data: Dict[str, str]) -> Dict[str, Any]:
    """Extrae remarks y notas especiales."""
    notes_data = {
        'remarks': [],
        'special_notes': [],
        'general_notes': []
    }
    
    # Buscar remarks
    for cell, value in sheet_data.items():
        if not value or not isinstance(value, str):
            continue
            
        value_clean = value.strip()
        
        # Buscar sección de remarks
        if 'Remarks:' in value_clean or 'C.- Remarks:' in value_clean:
            # Extraer el contenido después de "Remarks:"
            if ':' in value_clean:
                remark_content = value_clean.split(':', 1)[1].strip()
                if remark_content and remark_content not in ['-', '']:
                    notes_data['remarks'].append(remark_content)
        
        # Buscar notas especiales
        if 'Special Notes' in value_clean:
            notes_data['special_notes'].append(value_clean)
        
        # Buscar notas generales
        if 'General Notes' in value_clean:
            notes_data['general_notes'].append(value_clean)
    
    return notes_data

def extract_vessel_information(sheet_data: Dict[str, str]) -> Dict[str, Any]:
    """Extrae información adicional del buque."""
    vessel_info = {}
    
    # Patrones para información del buque
    vessel_patterns = {
        'any_information_submitted': r'Any information as submitted above resulting from information obtained from Vessel.*?records[,\s]*cannot be guaranteed as accurate',
        'measurement_standards': r'API MPMS.*?Manual of Petroleum Measurement Standards.*?Chapter.*?Guidelines',
        'standard_procedure': r'PR-INS-\d+.*?Standard Procedure for Surveyors'
    }
    
    all_text = ' '.join([str(v) for v in sheet_data.values() if v])
    
    for field, pattern in vessel_patterns.items():
        matches = re.findall(pattern, all_text, re.IGNORECASE | re.DOTALL)
        if matches:
            vessel_info[field] = matches[0].strip()
    
    return vessel_info

def find_timesheet_with_notes(data: Dict[str, Any]) -> Optional[str]:
    """Busca la hoja de tiempo que contiene las notas operacionales."""
    for sheet_name, sheet_data in data.items():
        if not isinstance(sheet_data, dict):
            continue
            
        # Buscar hojas que contengan "Special Notes" o "General Notes"
        sheet_text = ' '.join([str(v) for v in sheet_data.values() if v])
        if any(keyword in sheet_text for keyword in ['Special Notes', 'General Notes', 'Pumping Time', 'Weather conditions']):
            return sheet_name
    
    return None

def extract_operational_notes(cellmap_file: str) -> Dict[str, Any]:
    """
    Extrae notas operacionales del reporte desde un archivo cellmap JSON.
    
    Args:
        cellmap_file: Ruta al archivo JSON con el mapeo de celdas
        
    Returns:
        Diccionario con las notas operacionales extraídas
    """
    try:
        with open(cellmap_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception as e:
        print(f"Error al leer el archivo {cellmap_file}: {e}")
        return {}
    
    notes_data = {
        'weather_conditions': {},
        'pumping_data': {},
        'remarks_and_notes': {},
        'vessel_information': {},
        'source_sheet': None,
        'raw_notes_data': {}
    }
    
    # Buscar la hoja que contiene las notas operacionales
    notes_sheet_name = find_timesheet_with_notes(data)
    
    if not notes_sheet_name:
        print("No se encontró hoja con notas operacionales en el archivo")
        return notes_data
    
    notes_sheet = data[notes_sheet_name]
    notes_data['source_sheet'] = notes_sheet_name
    notes_data['raw_notes_data'] = notes_sheet
    
    print(f"Procesando notas operacionales de la hoja: {notes_sheet_name}")
    
    # Identificar la estructura de la tabla de notas
    structure = find_notes_structure(notes_sheet)
    if structure:
        print(f"  Estructura encontrada: Special Notes={structure['special_notes_found']}, General Notes={structure['general_notes_found']}")
    
    # Extraer diferentes tipos de información usando la estructura
    notes_data['timesheet_header'] = extract_timesheet_header(notes_sheet)
    notes_data['weather_conditions'] = extract_weather_conditions(notes_sheet, structure)
    notes_data['pumping_data'] = extract_pumping_data(notes_sheet, structure)
    notes_data['remarks_and_notes'] = extract_remarks_and_notes(notes_sheet)
    notes_data['vessel_information'] = extract_vessel_information(notes_sheet)
    notes_data['table_structure'] = structure
    
    return notes_data

def save_notes_data(notes_data: Dict[str, Any], output_file: str):
    """Guarda las notas operacionales en un archivo JSON."""
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(notes_data, f, indent=2, ensure_ascii=False)
        print(f"Notas operacionales guardadas en: {output_file}")
    except Exception as e:
        print(f"Error al guardar el archivo {output_file}: {e}")

def main():
    if len(sys.argv) != 2:
        print("Uso: python extract_operational_notes.py <archivo_cellmap.json>")
        sys.exit(1)
    
    cellmap_file = sys.argv[1]
    
    if not Path(cellmap_file).exists():
        print(f"Error: El archivo {cellmap_file} no existe")
        sys.exit(1)
    
    print(f"Extrayendo notas operacionales de: {cellmap_file}")
    
    # Extraer notas operacionales
    notes_data = extract_operational_notes(cellmap_file)
    
    if not notes_data or not any(notes_data.values()):
        print("No se pudieron extraer notas operacionales")
        sys.exit(1)
    
    # Generar nombre del archivo de salida
    input_path = Path(cellmap_file)
    output_file = input_path.parent / f"{input_path.stem.replace('_cellmap', '')}_notes.json"
    
    # Guardar datos
    save_notes_data(notes_data, str(output_file))
    
    # Mostrar resumen
    print("\n=== RESUMEN DE NOTAS OPERACIONALES EXTRAÍDAS ===")
    print(f"Hoja fuente: {notes_data.get('source_sheet', 'N/A')}")
    
    if notes_data['weather_conditions']:
        print("Condiciones climáticas:")
        for section, conditions in notes_data['weather_conditions'].items():
            if conditions:
                if isinstance(conditions, list):
                    print(f"  - {section}: {', '.join(conditions)}")
                elif isinstance(conditions, dict):
                    print(f"  - {section}: {', '.join(conditions.keys())}")
                else:
                    print(f"  - {section}: {conditions}")
    
    if notes_data['pumping_data']:
        print("Datos de bombeo:")
        for key, value in notes_data['pumping_data'].items():
            print(f"  - {key}: {value}")
    
    if notes_data['remarks_and_notes']:
        print("Remarks y notas:")
        for section, content in notes_data['remarks_and_notes'].items():
            if content:
                print(f"  - {section}: {len(content)} elementos")
    
    if notes_data['vessel_information']:
        print("Información del buque:")
        for key, value in notes_data['vessel_information'].items():
            print(f"  - {key}: {value[:50]}..." if len(str(value)) > 50 else f"  - {key}: {value}")

if __name__ == "__main__":
    main()
