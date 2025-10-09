#!/usr/bin/env python3
"""
Script para extraer datos de cabecera/cubierta de reportes marítimos.
Extrae información relevante como tipo de inspección, embarcaciones, productos,
referencias comerciales, terminal, inspector, fechas, etc.
"""

import json
import sys
import re
from pathlib import Path
from typing import Dict, List, Any, Optional

def extract_vessel_info(text: str) -> Dict[str, str]:
    """Extrae información de embarcaciones del texto."""
    vessel_info = {}
    
    # Patrones para diferentes tipos de embarcaciones
    patterns = {
        'tanker': r'M/T\s*["\']([^"\']+)["\']',
        'barge': r'Barge\s*["\']([^"\']+)["\']',
        'voyage': r'Voy\s*#?\s*(\d+)',
    }
    
    for vessel_type, pattern in patterns.items():
        matches = re.findall(pattern, text, re.IGNORECASE)
        if matches:
            if vessel_type == 'voyage':
                vessel_info[vessel_type] = matches[0]
            else:
                vessel_info[vessel_type] = matches
    
    return vessel_info

def extract_product_info(text: str) -> Dict[str, Any]:
    """Extrae información de productos del texto."""
    product_info = {}
    
    # Patrones para productos y cantidades
    quantity_pattern = r'(\d+[,.]?\d*)\s*(CBM|MT|BBL|LT)'
    product_pattern = r'(GAS OIL|GASOIL|DIESEL|FUEL OIL|CRUDE OIL|GASOLINE|JET FUEL)'
    bol_pattern = r'BOL\s*(\d+)'
    
    # Buscar cantidades
    quantities = re.findall(quantity_pattern, text, re.IGNORECASE)
    if quantities:
        product_info['quantities'] = [{'amount': q[0], 'unit': q[1]} for q in quantities]
    
    # Buscar productos
    products = re.findall(product_pattern, text, re.IGNORECASE)
    if products:
        product_info['products'] = list(set(products))
    
    # Buscar BOL
    bols = re.findall(bol_pattern, text, re.IGNORECASE)
    if bols:
        product_info['bol_numbers'] = bols
    
    return product_info

def extract_commercial_refs(text: str) -> List[Dict[str, str]]:
    """Extrae referencias comerciales del texto."""
    refs = []
    
    # Patrón para referencias comerciales
    ref_pattern = r'([A-Z][A-Z\s&]+)\s*-\s*\(Ref\.\s*#\s*([^)]+)\)'
    
    matches = re.findall(ref_pattern, text)
    for company, ref_num in matches:
        refs.append({
            'company': company.strip(),
            'reference': ref_num.strip()
        })
    
    return refs

def extract_operational_data(sheet_data: Dict[str, str]) -> Dict[str, Any]:
    """Extrae datos operacionales de la hoja."""
    operational_data = {}
    
    # Mapeo de campos conocidos
    field_mapping = {
        'file_number': ['File N°', 'File No'],
        'terminal': ['Terminal'],
        'inspector': ['Inspector', 'Surveyor'],
        'revised_by': ['Revised by'],
        'approved_by': ['Approved by'],
        'operation_date': ['Date of Operation completed'],
        'report_date': ['Date of Report Issuing'],
        'note': ['NOTE']
    }
    
    for cell, value in sheet_data.items():
        if not value or not isinstance(value, str):
            continue
            
        value_clean = value.strip()
        
        # Buscar campos específicos
        for field_key, field_names in field_mapping.items():
            for field_name in field_names:
                if value_clean.startswith(field_name + ':'):
                    # Extraer el valor después de los dos puntos
                    field_value = value_clean.split(':', 1)[1].strip()
                    operational_data[field_key] = field_value
                    break
    
    return operational_data

def extract_report_header(cellmap_file: str) -> Dict[str, Any]:
    """
    Extrae datos de cabecera del reporte desde un archivo cellmap JSON.
    
    Args:
        cellmap_file: Ruta al archivo JSON con el mapeo de celdas
        
    Returns:
        Diccionario con los datos extraídos de la cabecera
    """
    try:
        with open(cellmap_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception as e:
        print(f"Error al leer el archivo {cellmap_file}: {e}")
        return {}
    
    header_data = {
        'report_type': None,
        'vessels': {},
        'products': {},
        'commercial_references': [],
        'operational_data': {},
        'raw_cubierta_data': {}
    }
    
    # Buscar la hoja "Cubierta" o similar
    cubierta_sheet = None
    for sheet_name, sheet_data in data.items():
        if 'cubierta' in sheet_name.lower() or 'cover' in sheet_name.lower():
            cubierta_sheet = sheet_data
            header_data['raw_cubierta_data'] = sheet_data
            break
    
    if not cubierta_sheet:
        print("No se encontró hoja 'Cubierta' en el archivo")
        return header_data
    
    # Concatenar todo el texto para análisis
    all_text = ' '.join([str(v) for v in cubierta_sheet.values() if v])
    
    # Extraer tipo de reporte
    if 'A2' in cubierta_sheet:
        header_data['report_type'] = cubierta_sheet['A2']
    
    # Extraer información de embarcaciones
    header_data['vessels'] = extract_vessel_info(all_text)
    
    # Extraer información de productos
    header_data['products'] = extract_product_info(all_text)
    
    # Extraer referencias comerciales
    header_data['commercial_references'] = extract_commercial_refs(all_text)
    
    # Extraer datos operacionales
    header_data['operational_data'] = extract_operational_data(cubierta_sheet)
    
    return header_data

def save_header_data(header_data: Dict[str, Any], output_file: str):
    """Guarda los datos de cabecera en un archivo JSON."""
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(header_data, f, indent=2, ensure_ascii=False)
        print(f"Datos de cabecera guardados en: {output_file}")
    except Exception as e:
        print(f"Error al guardar el archivo {output_file}: {e}")

def main():
    if len(sys.argv) != 2:
        print("Uso: python extract_report_header.py <archivo_cellmap.json>")
        sys.exit(1)
    
    cellmap_file = sys.argv[1]
    
    if not Path(cellmap_file).exists():
        print(f"Error: El archivo {cellmap_file} no existe")
        sys.exit(1)
    
    print(f"Extrayendo datos de cabecera de: {cellmap_file}")
    
    # Extraer datos de cabecera
    header_data = extract_report_header(cellmap_file)
    
    if not header_data or not any(header_data.values()):
        print("No se pudieron extraer datos de cabecera")
        sys.exit(1)
    
    # Generar nombre del archivo de salida
    input_path = Path(cellmap_file)
    output_file = input_path.parent / f"{input_path.stem.replace('_cellmap', '')}_header.json"
    
    # Guardar datos
    save_header_data(header_data, str(output_file))
    
    # Mostrar resumen
    print("\n=== RESUMEN DE DATOS EXTRAÍDOS ===")
    print(f"Tipo de reporte: {header_data.get('report_type', 'N/A')}")
    
    if header_data['vessels']:
        print("Embarcaciones:")
        for vessel_type, vessels in header_data['vessels'].items():
            print(f"  - {vessel_type}: {vessels}")
    
    if header_data['products']:
        print("Productos:")
        for key, value in header_data['products'].items():
            print(f"  - {key}: {value}")
    
    if header_data['commercial_references']:
        print("Referencias comerciales:")
        for ref in header_data['commercial_references']:
            print(f"  - {ref['company']}: {ref['reference']}")
    
    if header_data['operational_data']:
        print("Datos operacionales:")
        for key, value in header_data['operational_data'].items():
            print(f"  - {key}: {value}")

if __name__ == "__main__":
    main()
