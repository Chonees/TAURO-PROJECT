/**
 * TAURO Project - Frontend JavaScript
 * Maneja la interfaz de usuario para el análisis de reportes marítimos
 */

class TauroApp {
    constructor() {
        this.currentData = null;
        this.currentFilename = null;
        this.init();
    }

    init() {
        this.setupEventListeners();
        this.loadFileHistory();
    }

    setupEventListeners() {
        // Upload area events
        const uploadArea = document.getElementById('uploadArea');
        const fileInput = document.getElementById('fileInput');

        uploadArea.addEventListener('click', () => fileInput.click());
        uploadArea.addEventListener('dragover', this.handleDragOver.bind(this));
        uploadArea.addEventListener('dragleave', this.handleDragLeave.bind(this));
        uploadArea.addEventListener('drop', this.handleDrop.bind(this));

        fileInput.addEventListener('change', this.handleFileSelect.bind(this));

        // Action buttons
        document.getElementById('showCellmapBtn').addEventListener('click', this.showCellmap.bind(this));
        document.getElementById('showEventsBtn').addEventListener('click', this.showEvents.bind(this));
        document.getElementById('analyzeAIBtn').addEventListener('click', this.analyzeWithAI.bind(this));
        document.getElementById('chatBotBtn').addEventListener('click', this.openChatBot.bind(this));

        // Chat buttons
        document.getElementById('sendChatBtn').addEventListener('click', this.sendChatMessage.bind(this));
        document.getElementById('clearChatBtn').addEventListener('click', this.clearChat.bind(this));
        document.getElementById('closeChatBtn').addEventListener('click', this.closeChat.bind(this));

        // Chat input
        document.getElementById('chatInput').addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                this.sendChatMessage();
            }
        });

        // Modal close
        document.getElementById('closeErrorModal').addEventListener('click', this.closeErrorModal.bind(this));
    }

    handleDragOver(e) {
        e.preventDefault();
        document.getElementById('uploadArea').classList.add('dragover');
    }

    handleDragLeave(e) {
        e.preventDefault();
        document.getElementById('uploadArea').classList.remove('dragover');
    }

    handleDrop(e) {
        e.preventDefault();
        document.getElementById('uploadArea').classList.remove('dragover');
        
        const files = e.dataTransfer.files;
        if (files.length > 0) {
            this.processFile(files[0]);
        }
    }

    handleFileSelect(e) {
        const files = e.target.files;
        if (files.length > 0) {
            this.processFile(files[0]);
        }
    }

    async processFile(file) {
        // Validar tipo de archivo
        const allowedTypes = ['application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', 
                             'application/vnd.ms-excel.sheet.macroEnabled.12'];
        
        if (!allowedTypes.includes(file.type) && !file.name.match(/\.(xlsx|xlsm)$/i)) {
            this.showError('Tipo de archivo no válido. Por favor selecciona un archivo .xlsx o .xlsm');
            return;
        }

        // Validar tamaño (50MB max)
        if (file.size > 50 * 1024 * 1024) {
            this.showError('El archivo es demasiado grande. Tamaño máximo: 50MB');
            return;
        }

        this.showLoading(true);
        this.showProgress(true);

        try {
            const formData = new FormData();
            formData.append('file', file);

            const response = await fetch('/upload', {
                method: 'POST',
                body: formData
            });

            const result = await response.json();

            if (response.ok) {
                this.handleUploadSuccess(result);
            } else {
                this.showError(result.error || 'Error procesando el archivo');
            }
        } catch (error) {
            console.error('Error:', error);
            this.showError('Error de conexión. Por favor intenta nuevamente.');
        } finally {
            this.showLoading(false);
            this.showProgress(false);
        }
    }

    handleUploadSuccess(result) {
        this.currentFilename = result.filename;
        
        // Mostrar sección de resultados
        document.getElementById('resultsSection').style.display = 'block';
        document.getElementById('resultsSection').classList.add('fade-in');
        
        // Actualizar historial
        this.loadFileHistory();
        
        // Scroll to results
        document.getElementById('resultsSection').scrollIntoView({ 
            behavior: 'smooth' 
        });
    }


    async showCellmap() {
        if (!this.currentFilename) return;
        
        const cellmapFile = this.currentFilename.replace(/\.[^/.]+$/, "") + "_cellmap.json";
        
        try {
            const response = await fetch(`/cellmap/${cellmapFile}`);
            const data = await response.json();
            
            if (response.ok) {
                this.displayCellmap(data);
            } else {
                this.showError(data.error || 'Error cargando el cellmap');
            }
        } catch (error) {
            console.error('Error:', error);
            this.showError('Error cargando los datos');
        }
    }

    displayCellmap(data) {
        const dataDisplay = document.getElementById('dataDisplay');
        const sheets = Object.keys(data);
        
        let html = `
            <div class="data-header">
                <h3><i class="fas fa-table"></i> Mapeo Completo de Celdas</h3>
                <p>Total de hojas: ${sheets.length}</p>
            </div>
        `;
        
        if (sheets.length > 1) {
            html += '<div class="sheet-tabs">';
            sheets.forEach((sheet, index) => {
                html += `<button class="sheet-tab ${index === 0 ? 'active' : ''}" 
                         onclick="app.switchSheet('${sheet}')">${sheet}</button>`;
            });
            html += '</div>';
        }
        
        html += '<div class="data-content">';
        
        sheets.forEach((sheet, index) => {
            const sheetData = data[sheet];
            const cells = Object.entries(sheetData);
            
            html += `
                <div class="sheet-content" id="sheet-${sheet}" 
                     style="display: ${index === 0 ? 'block' : 'none'}">
                    <h4>Hoja: ${sheet} (${cells.length} celdas)</h4>
                    <div style="max-height: 400px; overflow: auto;">
                        <table class="data-table">
                            <thead>
                                <tr>
                                    <th>Celda</th>
                                    <th>Valor</th>
                                </tr>
                            </thead>
                            <tbody>
            `;
            
            cells.forEach(([cell, value]) => {
                html += `
                    <tr>
                        <td><strong>${cell}</strong></td>
                        <td>${this.formatCellValue(value)}</td>
                    </tr>
                `;
            });
            
            html += `
                            </tbody>
                        </table>
                    </div>
                </div>
            `;
        });
        
        html += '</div>';
        dataDisplay.innerHTML = html;
    }

    async showEvents() {
        if (!this.currentFilename) return;
        
        const eventsFile = this.currentFilename.replace(/\.[^/.]+$/, "") + "_events.json";
        
        try {
            const response = await fetch(`/events/${eventsFile}`);
            const data = await response.json();
            
            if (response.ok) {
                this.displayEvents(data);
            } else {
                this.showError(data.error || 'Error cargando los eventos');
            }
        } catch (error) {
            console.error('Error:', error);
            this.showError('Error cargando los datos');
        }
    }

    displayEvents(events) {
        const dataDisplay = document.getElementById('dataDisplay');
        
        // Agrupar eventos por hoja
        const eventsBySheet = {};
        events.forEach(event => {
            if (!eventsBySheet[event.Sheet]) {
                eventsBySheet[event.Sheet] = [];
            }
            eventsBySheet[event.Sheet].push(event);
        });
        
        const sheets = Object.keys(eventsBySheet);
        
        let html = `
            <div class="data-header">
                <h3><i class="fas fa-clock"></i> Eventos de Hojas de Tiempo</h3>
                <p>Total de eventos: ${events.length}</p>
            </div>
        `;
        
        if (sheets.length > 1) {
            html += '<div class="sheet-tabs">';
            sheets.forEach((sheet, index) => {
                html += `<button class="sheet-tab ${index === 0 ? 'active' : ''}" 
                         onclick="app.switchSheet('${sheet}')">${sheet} (${eventsBySheet[sheet].length})</button>`;
            });
            html += '</div>';
        }
        
        html += '<div class="data-content">';
        
        sheets.forEach((sheet, index) => {
            const sheetEvents = eventsBySheet[sheet];
            
            html += `
                <div class="sheet-content" id="sheet-${sheet}" 
                     style="display: ${index === 0 ? 'block' : 'none'}">
                    <h4>Hoja: ${sheet} (${sheetEvents.length} eventos)</h4>
                    <div style="max-height: 400px; overflow: auto;">
                        <table class="data-table">
                            <thead>
                                <tr>
                                    <th>Evento</th>
                                    <th>Fecha</th>
                                    <th>Hora</th>
                                    <th>Formato</th>
                                    <th>Fila</th>
                                </tr>
                            </thead>
                            <tbody>
            `;
            
            sheetEvents.forEach(event => {
                html += `
                    <tr>
                        <td><strong>${event.Event}</strong></td>
                        <td>${event.Date || '-'}</td>
                        <td>${event.Time || '-'}</td>
                        <td><span class="badge badge-${event.Section}">${event.Section}</span></td>
                        <td>${event.Row}</td>
                    </tr>
                `;
            });
            
            html += `
                            </tbody>
                        </table>
                    </div>
                </div>
            `;
        });
        
        html += '</div>';
        dataDisplay.innerHTML = html;
        
        // Agregar estilos para badges
        if (!document.getElementById('badge-styles')) {
            const style = document.createElement('style');
            style.id = 'badge-styles';
            style.textContent = `
                .badge {
                    padding: 0.25rem 0.5rem;
                    border-radius: 12px;
                    font-size: 0.75rem;
                    font-weight: 600;
                    text-transform: uppercase;
                }
                .badge-english {
                    background: var(--accent-primary);
                    color: var(--bg-primary);
                }
                .badge-spanish {
                    background: var(--accent-success);
                    color: var(--bg-primary);
                }
            `;
            document.head.appendChild(style);
        }
    }

    switchSheet(sheetName) {
        // Ocultar todas las hojas
        document.querySelectorAll('.sheet-content').forEach(content => {
            content.style.display = 'none';
        });
        
        // Mostrar la hoja seleccionada
        const targetSheet = document.getElementById(`sheet-${sheetName}`);
        if (targetSheet) {
            targetSheet.style.display = 'block';
        }
        
        // Actualizar tabs activos
        document.querySelectorAll('.sheet-tab').forEach(tab => {
            tab.classList.remove('active');
        });
        event.target.classList.add('active');
    }

    async loadFileHistory() {
        try {
            const response = await fetch('/files');
            const files = await response.json();
            
            if (response.ok) {
                this.displayFileHistory(files);
            }
        } catch (error) {
            console.error('Error loading file history:', error);
        }
    }

    displayFileHistory(files) {
        const filesList = document.getElementById('filesList');
        
        if (files.length === 0) {
            filesList.innerHTML = '<p class="text-muted">No hay archivos procesados aún.</p>';
            return;
        }
        
        let html = '';
        files.forEach(file => {
            const date = new Date(file.created * 1000).toLocaleString('es-ES');
            html += `
                <div class="file-item">
                    <div class="file-info">
                        <h4>${file.name}</h4>
                        <p>Procesado: ${date}</p>
                    </div>
                    <div class="file-actions">
                        <button class="btn btn-small btn-secondary" 
                                onclick="app.loadFile('${file.name}', '${file.cellmap_file}', 'cellmap')">
                            <i class="fas fa-table"></i> Cellmap
                        </button>
                        ${file.events_file ? `
                            <button class="btn btn-small btn-secondary" 
                                    onclick="app.loadFile('${file.name}', '${file.events_file}', 'events')">
                                <i class="fas fa-clock"></i> Eventos
                            </button>
                        ` : ''}
                    </div>
                </div>
            `;
        });
        
        filesList.innerHTML = html;
    }

    async loadFile(filename, dataFile, type) {
        this.currentFilename = filename;
        
        // Mostrar sección de resultados
        document.getElementById('resultsSection').style.display = 'block';
        
        if (type === 'cellmap') {
            await this.loadCellmapFile(dataFile);
        } else if (type === 'events') {
            await this.loadEventsFile(dataFile);
        }
        
        // Scroll to results
        document.getElementById('resultsSection').scrollIntoView({ 
            behavior: 'smooth' 
        });
    }

    async loadCellmapFile(filename) {
        try {
            const response = await fetch(`/cellmap/${filename}`);
            const data = await response.json();
            
            if (response.ok) {
                this.displayCellmap(data);
            } else {
                this.showError(data.error || 'Error cargando el archivo');
            }
        } catch (error) {
            console.error('Error:', error);
            this.showError('Error cargando los datos');
        }
    }

    async loadEventsFile(filename) {
        try {
            const response = await fetch(`/events/${filename}`);
            const data = await response.json();
            
            if (response.ok) {
                this.displayEvents(data);
            } else {
                this.showError(data.error || 'Error cargando el archivo');
            }
        } catch (error) {
            console.error('Error:', error);
            this.showError('Error cargando los datos');
        }
    }

    formatCellValue(value) {
        if (value === null || value === undefined) {
            return '<em class="text-muted">null</em>';
        }
        
        if (typeof value === 'string' && value.length > 100) {
            return value.substring(0, 100) + '...';
        }
        
        return String(value);
    }

    showProgress(show) {
        const progressContainer = document.getElementById('progressContainer');
        if (show) {
            progressContainer.style.display = 'block';
            // Simular progreso
            let progress = 0;
            const interval = setInterval(() => {
                progress += Math.random() * 15;
                if (progress > 90) progress = 90;
                document.getElementById('progressFill').style.width = progress + '%';
            }, 200);
            
            // Guardar interval para limpiarlo después
            this.progressInterval = interval;
        } else {
            progressContainer.style.display = 'none';
            if (this.progressInterval) {
                clearInterval(this.progressInterval);
            }
            document.getElementById('progressFill').style.width = '100%';
            setTimeout(() => {
                document.getElementById('progressFill').style.width = '0%';
            }, 500);
        }
    }

    showLoading(show) {
        document.getElementById('loadingOverlay').style.display = show ? 'flex' : 'none';
    }

    showError(message) {
        document.getElementById('errorMessage').textContent = message;
        document.getElementById('errorModal').style.display = 'flex';
    }

    closeErrorModal() {
        document.getElementById('errorModal').style.display = 'none';
    }

    async analyzeWithAI() {
        if (!this.currentFilename) return;
        
        const eventsFile = this.currentFilename.replace(/\.[^/.]+$/, "") + "_events.json";
        
        try {
            this.showLoading(true);
            
            const response = await fetch(`/analyze/${eventsFile}`);
            const result = await response.json();
            
            if (response.ok && result.success) {
                this.displayAIAnalysis(result);
            } else {
                this.showError(result.error || 'Error en análisis automático');
            }
        } catch (error) {
            console.error('Error:', error);
            this.showError('Error conectando con el servicio de análisis');
        } finally {
            this.showLoading(false);
        }
    }

    displayAIAnalysis(analysisResult) {
        const dataDisplay = document.getElementById('dataDisplay');
        const analysis = analysisResult.analysis;
        
        let html = `
            <div class="data-header">
                <h3><i class="fas fa-chart-line"></i> Análisis Automático de Hojas de Tiempo</h3>
                <div class="analysis-meta">
                    <span><i class="fas fa-file"></i> ${analysisResult.filename}</span>
                    <span><i class="fas fa-calendar"></i> ${new Date(analysisResult.timestamp).toLocaleString()}</span>
                    <span><i class="fas fa-list"></i> ${analysisResult.events_count} eventos</span>
                </div>
            </div>
            <div class="data-content">
        `;
        
        if (analysis && analysis.sections) {
            // Mostrar secciones estructuradas
            for (const [sectionName, sectionContent] of Object.entries(analysis.sections)) {
                html += `
                    <div class="analysis-section">
                        <h4><i class="fas fa-chevron-right"></i> ${this.formatSectionName(sectionName)}</h4>
                        <div class="analysis-content">
                            ${this.formatAnalysisContent(sectionContent)}
                        </div>
                    </div>
                `;
            }
        } else {
            // Mostrar texto completo si no hay secciones
            html += `
                <div class="analysis-section">
                    <h4><i class="fas fa-robot"></i> Análisis Completo</h4>
                    <div class="analysis-content">
                        ${this.formatAnalysisContent(analysis.full_text || 'No se pudo generar análisis')}
                    </div>
                </div>
            `;
        }
        
        html += `
            </div>
            <div class="analysis-footer">
                <small><i class="fas fa-info-circle"></i> Análisis generado automáticamente - Basado en patrones marítimos</small>
            </div>
        `;
        
        dataDisplay.innerHTML = html;
    }

    formatSectionName(sectionName) {
        const names = {
            'resumen': 'Resumen Ejecutivo',
            'análisis': 'Análisis Detallado', 
            'eventos': 'Eventos Críticos',
            'recomendaciones': 'Recomendaciones',
            'riesgos': 'Riesgos Identificados',
            'general': 'Análisis General'
        };
        
        return names[sectionName] || sectionName.charAt(0).toUpperCase() + sectionName.slice(1);
    }

    formatAnalysisContent(content) {
        if (!content) return '';
        
        // Convertir saltos de línea a párrafos
        return content
            .split('\n')
            .filter(line => line.trim())
            .map(line => `<p>${line.trim()}</p>`)
            .join('');
    }

    // === CHATBOT METHODS ===

    async openChatBot() {
        if (!this.currentFilename) {
            this.showError('Por favor, procesa un archivo Excel primero para usar el chatbot');
            return;
        }

        // Mostrar sección de chat
        document.getElementById('chatSection').style.display = 'block';
        document.getElementById('chatSection').scrollIntoView({ behavior: 'smooth' });

        // Cargar datos en el chatbot
        await this.loadChatData();
    }

    async loadChatData() {
        const eventsFile = this.currentFilename.replace(/\.[^/.]+$/, "") + "_events.json";
        
        try {
            const response = await fetch(`/chat/load/${eventsFile}`);
            const result = await response.json();
            
            if (response.ok && result.success) {
                // Actualizar info del chat
                const chatInfo = document.getElementById('chatInfo');
                const info = result.data_info;
                chatInfo.innerHTML = `
                    <p><i class="fas fa-check-circle"></i> 
                    <strong>${info.filename}</strong> cargado - 
                    ${info.events_count} eventos disponibles 
                    (${info.date_range.start} a ${info.date_range.end})</p>
                `;
                
                // Habilitar input
                document.getElementById('chatInput').disabled = false;
                document.getElementById('sendChatBtn').disabled = false;
                
                // Mensaje de bienvenida
                this.addChatMessage('bot', `¡Hola! Soy tu asistente especializado en TIME LOGS de inspectores marítimos.\n\nHe cargado el reporte: **${info.filename}**\n📊 ${info.events_count} eventos registrados\n📅 Período: ${info.date_range.start} a ${info.date_range.end}\n\n**Preguntas que puedo responder:**\n• "¿Cuál fue la primera tarea registrada?"\n• "¿De qué tipo de operación estamos hablando?"\n• "¿Qué eventos ocurrieron a las X horas?"\n• "¿Cuánto duró la operación?"\n• "¿Qué inspecciones se realizaron?"`);
                
            } else {
                this.showError(result.error || 'Error cargando datos para el chat');
            }
        } catch (error) {
            console.error('Error:', error);
            this.showError('Error conectando con el chatbot');
        }
    }

    async sendChatMessage() {
        const input = document.getElementById('chatInput');
        const question = input.value.trim();
        
        if (!question) return;
        
        // Agregar mensaje del usuario
        this.addChatMessage('user', question);
        input.value = '';
        
        // Mostrar typing indicator
        this.showTypingIndicator();
        
        try {
            const response = await fetch('/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ question: question })
            });
            
            const result = await response.json();
            
            // Ocultar typing indicator
            this.hideTypingIndicator();
            
            if (response.ok && result.success) {
                this.addChatMessage('bot', result.response);
            } else {
                this.addChatMessage('bot', `Error: ${result.error || 'No pude procesar tu pregunta'}`);
            }
            
        } catch (error) {
            this.hideTypingIndicator();
            console.error('Error:', error);
            this.addChatMessage('bot', 'Error de conexión. Por favor intenta nuevamente.');
        }
    }

    addChatMessage(sender, message) {
        const messagesContainer = document.getElementById('chatMessages');
        const messageDiv = document.createElement('div');
        messageDiv.className = `chat-message ${sender}`;
        
        const now = new Date();
        const timeString = now.toLocaleTimeString('es-ES', { 
            hour: '2-digit', 
            minute: '2-digit' 
        });
        
        messageDiv.innerHTML = `
            <div class="message-bubble">${this.formatChatMessage(message)}</div>
            <div class="message-time">${timeString}</div>
        `;
        
        messagesContainer.appendChild(messageDiv);
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }

    formatChatMessage(message) {
        // Convertir saltos de línea a <br>
        return message
            .replace(/\n/g, '<br>')
            .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>') // **texto** -> <strong>texto</strong>
            .replace(/\*(.*?)\*/g, '<em>$1</em>'); // *texto* -> <em>texto</em>
    }

    showTypingIndicator() {
        const messagesContainer = document.getElementById('chatMessages');
        const typingDiv = document.createElement('div');
        typingDiv.className = 'chat-message bot';
        typingDiv.id = 'typingIndicator';
        
        typingDiv.innerHTML = `
            <div class="message-bubble">
                <div class="chat-typing">
                    <span>Escribiendo</span>
                    <div class="typing-dots">
                        <div class="typing-dot"></div>
                        <div class="typing-dot"></div>
                        <div class="typing-dot"></div>
                    </div>
                </div>
            </div>
        `;
        
        messagesContainer.appendChild(typingDiv);
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }

    hideTypingIndicator() {
        const typingIndicator = document.getElementById('typingIndicator');
        if (typingIndicator) {
            typingIndicator.remove();
        }
    }

    async clearChat() {
        try {
            const response = await fetch('/chat/clear', { method: 'POST' });
            const result = await response.json();
            
            if (response.ok && result.success) {
                document.getElementById('chatMessages').innerHTML = '';
                this.addChatMessage('bot', '¡Historial limpiado! ¿En qué puedo ayudarte?');
            } else {
                this.showError(result.error || 'Error limpiando el chat');
            }
        } catch (error) {
            console.error('Error:', error);
            this.showError('Error limpiando el chat');
        }
    }

    closeChat() {
        document.getElementById('chatSection').style.display = 'none';
    }
}

// Inicializar la aplicación cuando se carga la página
const app = new TauroApp();

// Hacer la instancia global para acceso desde HTML
window.app = app;
