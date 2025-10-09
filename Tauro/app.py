"""
TAURO Project - Flask Web Application
Servidor web para el análisis de reportes de carga marítima
"""

import os
import json
from flask import Flask, render_template, request, jsonify, send_from_directory
from werkzeug.utils import secure_filename
from pathlib import Path
import tempfile

# Importar nuestros scripts existentes
from create_cellmap import create_cellmap_from_excel
from extract_timesheet_events import extract_timesheet_events, extract_timesheet_events_from_data
from extract_report_header import extract_report_header
from basic_analyzer import analyze_events_basic
from maritime_chatbot import create_maritime_chatbot

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB max file size

# Configuración de carpetas
UPLOAD_FOLDER = Path(__file__).parent / "uploads"
OUTPUT_FOLDER = Path(__file__).parent / "output"
UPLOAD_FOLDER.mkdir(exist_ok=True)
OUTPUT_FOLDER.mkdir(exist_ok=True)

# Instancia global del chatbot
try:
    maritime_chatbot = create_maritime_chatbot()
    print("🤖 Chatbot marítimo inicializado correctamente")
except Exception as e:
    print(f"⚠️  Error inicializando chatbot: {e}")
    maritime_chatbot = None

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

ALLOWED_EXTENSIONS = {'xlsx', 'xlsm'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    """Página principal"""
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    """Procesar archivo Excel subido"""
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No se seleccionó archivo'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No se seleccionó archivo'}), 400
        
        if not allowed_file(file.filename):
            return jsonify({'error': 'Tipo de archivo no permitido. Use .xlsx o .xlsm'}), 400
        
        # Guardar archivo
        filename = secure_filename(file.filename)
        filepath = UPLOAD_FOLDER / filename
        file.save(str(filepath))
        
        # Crear cellmap
        print(f"🔄 Procesando archivo: {filename}")
        cellmap_output = OUTPUT_FOLDER / f"{Path(filename).stem}_cellmap.json"
        cellmap = create_cellmap_from_excel(str(filepath), str(cellmap_output))
        
        # Extraer datos de cabecera del reporte
        header_output = OUTPUT_FOLDER / f"{Path(filename).stem}_header.json"
        try:
            header_data = extract_report_header(str(cellmap_output))
            # Guardar datos de cabecera
            with open(header_output, 'w', encoding='utf-8') as f:
                json.dump(header_data, f, ensure_ascii=False, indent=2, default=str)
            print(f"✅ Datos de cabecera extraídos: {header_output.name}")
        except Exception as e:
            print(f"⚠️  Error extrayendo datos de cabecera: {e}")
            header_data = {}
        
        # Extraer eventos de timesheet usando el cellmap directamente
        events_output = OUTPUT_FOLDER / f"{Path(filename).stem}_events.json"
        
        try:
            # Usar la función extract_timesheet_events_from_data directamente
            events = extract_timesheet_events_from_data(cellmap)
            
            # Guardar eventos
            with open(events_output, 'w', encoding='utf-8') as f:
                json.dump(events, f, ensure_ascii=False, indent=2, default=str)
            
        except Exception as e:
            print(f"⚠️  Error extrayendo eventos: {e}")
            # Si falla la extracción de eventos, crear lista vacía
            events = []
            with open(events_output, 'w', encoding='utf-8') as f:
                json.dump(events, f, ensure_ascii=False, indent=2, default=str)
        
        # Extraer notas operacionales
        notes_output = OUTPUT_FOLDER / f"{Path(filename).stem}_notes.json"
        
        try:
            from extract_operational_notes import extract_operational_notes
            notes_data = extract_operational_notes(str(cellmap_output))
            
            # Guardar notas operacionales
            with open(notes_output, 'w', encoding='utf-8') as f:
                json.dump(notes_data, f, ensure_ascii=False, indent=2, default=str)
            
            print(f"✅ Notas operacionales extraídas: {notes_output.name}")
        except Exception as e:
            print(f"⚠️  Error extrayendo notas operacionales: {e}")
            notes_data = {}
            with open(notes_output, 'w', encoding='utf-8') as f:
                json.dump(notes_data, f, ensure_ascii=False, indent=2, default=str)
        
        # Limpiar archivo subido
        os.unlink(filepath)
        
        return jsonify({
            'success': True,
            'message': f'Archivo procesado exitosamente',
            'filename': filename,
            'cellmap_file': f"{Path(filename).stem}_cellmap.json",
            'events_file': f"{Path(filename).stem}_events.json",
            'header_file': f"{Path(filename).stem}_header.json",
            'notes_file': f"{Path(filename).stem}_notes.json"
        })
        
    except Exception as e:
        print(f"❌ Error procesando archivo: {str(e)}")
        return jsonify({'error': f'Error procesando archivo: {str(e)}'}), 500

@app.route('/cellmap/<filename>')
def get_cellmap(filename):
    """Obtener datos del cellmap"""
    try:
        filepath = OUTPUT_FOLDER / filename
        if not filepath.exists():
            return jsonify({'error': 'Archivo no encontrado'}), 404
        
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        return jsonify(data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/events/<filename>')
def get_events(filename):
    """Obtener eventos de timesheet"""
    try:
        filepath = OUTPUT_FOLDER / filename
        if not filepath.exists():
            return jsonify({'error': 'Archivo no encontrado'}), 404
        
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        return jsonify(data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/header/<filename>')
def get_header(filename):
    """Obtener datos de cabecera del reporte"""
    try:
        filepath = OUTPUT_FOLDER / filename
        if not filepath.exists():
            return jsonify({'error': 'Archivo no encontrado'}), 404
        
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        return jsonify(data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/notes/<filename>')
def get_notes(filename):
    """Obtener notas operacionales del reporte"""
    try:
        filepath = OUTPUT_FOLDER / filename
        if not filepath.exists():
            return jsonify({'error': 'Archivo de notas operacionales no encontrado'}), 404
        
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        print(f"📝 Notas operacionales cargadas: {filename}")
        return jsonify(data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/files')
def list_files():
    """Listar archivos procesados"""
    try:
        files = []
        for file_path in OUTPUT_FOLDER.glob("*_cellmap.json"):
            stem = file_path.stem.replace("_cellmap", "")
            events_file = OUTPUT_FOLDER / f"{stem}_events.json"
            header_file = OUTPUT_FOLDER / f"{stem}_header.json"
            
            files.append({
                'name': stem,
                'cellmap_file': file_path.name,
                'events_file': events_file.name if events_file.exists() else None,
                'header_file': header_file.name if header_file.exists() else None,
                'created': file_path.stat().st_mtime
            })
        
        # Ordenar por fecha de creación (más reciente primero)
        files.sort(key=lambda x: x['created'], reverse=True)
        
        return jsonify(files)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/analyze/<filename>')
def analyze_with_ai(filename):
    """Analizar eventos con IA"""
    try:
        # Buscar archivo de eventos
        events_file = OUTPUT_FOLDER / filename
        if not events_file.exists():
            return jsonify({'error': 'Archivo de eventos no encontrado'}), 404
        
        # Cargar eventos
        with open(events_file, 'r', encoding='utf-8') as f:
            events = json.load(f)
        
        if not events:
            return jsonify({'error': 'No hay eventos para analizar'}), 400
        
        # Obtener nombre original del archivo
        original_name = filename.replace('_events.json', '')
        
        print(f"📊 Iniciando análisis básico para: {original_name}")
        print(f"📋 Eventos a analizar: {len(events)}")
        
        # Usar análisis básico directamente
        analysis_result = analyze_events_basic(events, original_name)
        
        if analysis_result['success']:
            print(f"✅ Análisis básico completado")
            analysis_result['analysis_type'] = 'Basic'
            analysis_result['note'] = 'Análisis generado con lógica avanzada basada en patrones marítimos'
        else:
            print(f"❌ Error en análisis básico: {analysis_result.get('error')}")
            return jsonify(analysis_result), 500
        
        # Guardar análisis
        analysis_file = OUTPUT_FOLDER / f"{original_name}_analysis.json"
        with open(analysis_file, 'w', encoding='utf-8') as f:
            json.dump(analysis_result, f, ensure_ascii=False, indent=2, default=str)
        
        print(f"✅ Análisis guardado exitosamente")
        return jsonify(analysis_result)
            
    except Exception as e:
        print(f"❌ Error en endpoint de análisis: {str(e)}")
        return jsonify({'error': f'Error en análisis: {str(e)}'}), 500

@app.route('/analysis/<filename>')
def get_analysis(filename):
    """Obtener análisis IA guardado"""
    try:
        analysis_file = OUTPUT_FOLDER / filename
        if not analysis_file.exists():
            return jsonify({'error': 'Análisis no encontrado'}), 404
        
        with open(analysis_file, 'r', encoding='utf-8') as f:
            analysis = json.load(f)
        
        return jsonify(analysis)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/chat/load/<filename>')
def load_chat_data(filename):
    """Cargar datos para el chatbot"""
    if not maritime_chatbot:
        return jsonify({'error': 'Chatbot no disponible'}), 500
    
    try:
        # Obtener nombre original
        original_name = filename.replace('_events.json', '')
        
        # Buscar archivos de eventos, cellmap y header
        events_file = OUTPUT_FOLDER / filename
        cellmap_file = OUTPUT_FOLDER / f"{original_name}_cellmap.json"
        header_file = OUTPUT_FOLDER / f"{original_name}_header.json"
        
        if not events_file.exists():
            return jsonify({'error': 'Archivo de eventos no encontrado'}), 404
        
        # Cargar eventos
        with open(events_file, 'r', encoding='utf-8') as f:
            events = json.load(f)
        
        # Cargar cellmap si existe
        cellmap = {}
        if cellmap_file.exists():
            with open(cellmap_file, 'r', encoding='utf-8') as f:
                cellmap = json.load(f)
        
        # Cargar datos de cabecera si existen
        header_file = OUTPUT_FOLDER / f"{original_name}_header.json"
        header_data = {}
        if header_file.exists():
            with open(header_file, 'r', encoding='utf-8') as f:
                header_data = json.load(f)
            print(f"    Datos de cabecera cargados: {header_file.name}")
        
        # Cargar notas operacionales si existen
        notes_file = OUTPUT_FOLDER / f"{original_name}_notes.json"
        notes_data = {}
        if notes_file.exists():
            with open(notes_file, 'r', encoding='utf-8') as f:
                notes_data = json.load(f)
            print(f"    Notas operacionales cargadas: {notes_file.name}")
        
        # Cargar datos en el chatbot (incluyendo header_data y notes_data)
        result = maritime_chatbot.load_data_context(events, cellmap, original_name, header_data, notes_data)
        
        return jsonify({
            'success': True,
            'message': result,
            'data_info': maritime_chatbot.get_data_info()
        })
        
    except Exception as e:
        return jsonify({'error': f'Error cargando datos: {str(e)}'}), 500

@app.route('/chat', methods=['POST'])
def chat_with_bot():
    """Endpoint para chatear con el bot"""
    if not maritime_chatbot:
        return jsonify({'error': 'Chatbot no disponible'}), 500
    
    try:
        data = request.get_json()
        if not data or 'question' not in data:
            return jsonify({'error': 'Pregunta requerida'}), 400
        
        question = data['question'].strip()
        if not question:
            return jsonify({'error': 'Pregunta no puede estar vacía'}), 400
        
        # Procesar pregunta
        result = maritime_chatbot.chat(question)
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'error': f'Error en chat: {str(e)}'}), 500

@app.route('/chat/history')
def get_chat_history():
    """Obtener historial de conversación"""
    if not maritime_chatbot:
        return jsonify({'error': 'Chatbot no disponible'}), 500
    
    try:
        history = maritime_chatbot.get_conversation_history()
        return jsonify({
            'success': True,
            'history': history,
            'count': len(history)
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/chat/clear', methods=['POST'])
def clear_chat_history():
    """Limpiar historial de conversación"""
    if not maritime_chatbot:
        return jsonify({'error': 'Chatbot no disponible'}), 500
    
    try:
        result = maritime_chatbot.clear_conversation()
        return jsonify({
            'success': True,
            'message': result
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/chat/info')
def get_chat_info():
    """Obtener información sobre datos cargados"""
    if not maritime_chatbot:
        return jsonify({'error': 'Chatbot no disponible'}), 500
    
    try:
        info = maritime_chatbot.get_data_info()
        return jsonify({
            'success': True,
            'info': info
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    print("🚀 Iniciando TAURO Project Web Server...")
    print(f"📁 Carpeta de uploads: {UPLOAD_FOLDER}")
    print(f"📁 Carpeta de output: {OUTPUT_FOLDER}")
    app.run(debug=True, host='0.0.0.0', port=5000)
