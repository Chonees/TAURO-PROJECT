#!/usr/bin/env python3
"""
TAURO Project - Servidor de Desarrollo
Script para iniciar el servidor web de desarrollo
"""

import os
import sys
from pathlib import Path

# Agregar el directorio actual al path para importar módulos
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

def main():
    """Función principal para iniciar el servidor"""
    print("🚀 TAURO PROJECT - Servidor Web")
    print("=" * 50)
    print("📋 Sistema de Análisis de Reportes de Carga Marítima")
    print("🌐 Interfaz Web Dark Theme")
    print("=" * 50)
    
    # Verificar que los archivos necesarios existen
    required_files = [
        'create_cellmap.py',
        'extract_timesheet_events.py',
        'app.py',
        'templates/index.html',
        'static/css/style.css',
        'static/js/app.js'
    ]
    
    missing_files = []
    for file in required_files:
        if not (current_dir / file).exists():
            missing_files.append(file)
    
    if missing_files:
        print("❌ Archivos faltantes:")
        for file in missing_files:
            print(f"   - {file}")
        print("\nPor favor asegúrate de que todos los archivos estén presentes.")
        return
    
    print("✅ Todos los archivos necesarios están presentes")
    print("\n📁 Estructura del proyecto:")
    print(f"   📂 Directorio base: {current_dir}")
    print(f"   📂 Templates: {current_dir / 'templates'}")
    print(f"   📂 Static: {current_dir / 'static'}")
    print(f"   📂 Uploads: {current_dir / 'uploads'}")
    print(f"   📂 Output: {current_dir / 'output'}")
    
    print("\n🔧 Configuración del servidor:")
    print("   🌐 Host: 0.0.0.0 (accesible desde la red local)")
    print("   🔌 Puerto: 5000")
    print("   🐛 Debug: Activado")
    
    print("\n📖 Instrucciones de uso:")
    print("   1. Abre tu navegador web")
    print("   2. Navega a: http://localhost:5000")
    print("   3. Arrastra un archivo Excel (.xlsx o .xlsm)")
    print("   4. Visualiza el mapeo completo y eventos de tiempo")
    
    print("\n🛑 Para detener el servidor: Ctrl+C")
    print("=" * 50)
    
    # Importar y ejecutar la aplicación Flask
    try:
        from app import app
        app.run(debug=True, host='0.0.0.0', port=5000)
    except ImportError as e:
        print(f"❌ Error importando la aplicación: {e}")
        print("Asegúrate de que app.py esté presente y sea válido.")
    except Exception as e:
        print(f"❌ Error iniciando el servidor: {e}")

if __name__ == '__main__':
    main()
