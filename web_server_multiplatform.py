"""
Servidor Web SMS Gateway Multiplataforma
Interfaz web completa que funciona en Windows, Linux y macOS
"""
import asyncio
import json
import threading
import time
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler
from socketserver import ThreadingMixIn
from urllib.parse import parse_qs, urlparse
from multiplatform_sms_engine import MultiplatformSMSEngine
from system_config import config_manager, get_system_info

class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
    daemon_threads = True

class SMSGatewayHandler(BaseHTTPRequestHandler):
    
    def do_GET(self):
        """Maneja peticiones GET"""
        parsed_url = urlparse(self.path)
        path = parsed_url.path
        
        if path == '/':
            self._serve_main_interface()
        elif path == '/api/system-info':
            self._api_system_info()
        elif path == '/api/config':
            self._api_get_config()
        elif path == '/api/status':
            self._api_get_status()
        elif path == '/api/messages':
            self._api_get_messages()
        elif path == '/setup':
            self._serve_setup_page()
        else:
            self._send_error(404, "Página no encontrada")
    
    def do_POST(self):
        """Maneja peticiones POST"""
        parsed_url = urlparse(self.path)
        path = parsed_url.path
        
        if path == '/api/send':
            self._api_send_sms()
        elif path == '/api/connect':
            self._api_connect()
        elif path == '/api/disconnect':
            self._api_disconnect()
        elif path == '/api/config':
            self._api_save_config()
        elif path == '/api/test-port':
            self._api_test_port()
        else:
            self._send_error(404, "Endpoint no encontrado")
    
    def _serve_main_interface(self):
        """Sirve la interfaz principal"""
        html = """
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>SMS Gateway Multiplataforma</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: #f0f2f5; }
        .container { max-width: 1400px; margin: 0 auto; padding: 20px; }
        
        .header { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; border-radius: 12px; margin-bottom: 20px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }
        .header h1 { font-size: 2.5em; margin-bottom: 10px; }
        .header .subtitle { opacity: 0.9; font-size: 1.1em; }
        
        .status-bar { background: white; padding: 15px; border-radius: 8px; margin-bottom: 20px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); display: flex; justify-content: space-between; align-items: center; }
        .status-indicator { display: flex; align-items: center; gap: 10px; }
        .status-dot { width: 12px; height: 12px; border-radius: 50%; }
        .status-dot.connected { background: #4CAF50; }
        .status-dot.disconnected { background: #f44336; }
        
        .grid { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-bottom: 20px; }
        .card { background: white; border-radius: 12px; padding: 20px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); }
        .card h2 { color: #333; margin-bottom: 20px; font-size: 1.4em; }
        
        .form-group { margin-bottom: 15px; }
        .form-group label { display: block; margin-bottom: 5px; font-weight: 600; color: #555; }
        .form-group input, .form-group textarea, .form-group select { width: 100%; padding: 12px; border: 2px solid #e1e5e9; border-radius: 8px; font-size: 14px; transition: border-color 0.3s; }
        .form-group input:focus, .form-group textarea:focus, .form-group select:focus { outline: none; border-color: #667eea; }
        
        .btn { background: #667eea; color: white; padding: 12px 24px; border: none; border-radius: 8px; cursor: pointer; font-size: 14px; font-weight: 600; transition: all 0.3s; display: inline-flex; align-items: center; gap: 8px; }
        .btn:hover { background: #5a6fd8; transform: translateY(-1px); }
        .btn:disabled { background: #ccc; cursor: not-allowed; transform: none; }
        .btn.success { background: #4CAF50; }
        .btn.success:hover { background: #45a049; }
        .btn.danger { background: #f44336; }
        .btn.danger:hover { background: #da190b; }
        .btn.warning { background: #ff9800; }
        .btn.warning:hover { background: #e68900; }
        
        .alert { padding: 15px; border-radius: 8px; margin: 15px 0; }
        .alert.success { background: #d4edda; color: #155724; border: 1px solid #c3e6cb; }
        .alert.error { background: #f8d7da; color: #721c24; border: 1px solid #f5c6cb; }
        .alert.info { background: #d1ecf1; color: #0c5460; border: 1px solid #bee5eb; }
        .alert.warning { background: #fff3cd; color: #856404; border: 1px solid #ffeaa7; }
        
        .message-list { max-height: 400px; overflow-y: auto; }
        .message-item { border: 1px solid #e1e5e9; padding: 15px; margin: 10px 0; border-radius: 8px; }
        .message-item.sent { background: #e3f2fd; border-left: 4px solid #2196F3; }
        .message-item.received { background: #f3e5f5; border-left: 4px solid #9c27b0; }
        .message-item.response { background: #e8f5e8; border-left: 4px solid #4CAF50; }
        
        .system-info { background: #f8f9fa; padding: 15px; border-radius: 8px; margin: 15px 0; }
        .system-info h3 { margin-bottom: 10px; color: #333; }
        .system-info .info-item { display: flex; justify-content: space-between; padding: 5px 0; border-bottom: 1px solid #e9ecef; }
        .system-info .info-item:last-child { border-bottom: none; }
        
        .port-list { max-height: 200px; overflow-y: auto; }
        .port-item { display: flex; justify-content: space-between; align-items: center; padding: 10px; border: 1px solid #e1e5e9; border-radius: 6px; margin: 5px 0; }
        .port-item.huawei { background: #e8f5e8; border-color: #4CAF50; }
        .port-item.modem { background: #fff3e0; border-color: #ff9800; }
        
        .stats { display: grid; grid-template-columns: repeat(4, 1fr); gap: 15px; margin: 20px 0; }
        .stat-card { background: white; padding: 20px; border-radius: 8px; text-align: center; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        .stat-number { font-size: 2em; font-weight: bold; color: #667eea; }
        .stat-label { color: #666; margin-top: 5px; }
        
        .loading { display: inline-block; width: 20px; height: 20px; border: 3px solid #f3f3f3; border-top: 3px solid #667eea; border-radius: 50%; animation: spin 1s linear infinite; }
        @keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
        
        @media (max-width: 768px) {
            .grid { grid-template-columns: 1fr; }
            .stats { grid-template-columns: repeat(2, 1fr); }
        }
    </style>
</head>
<body>
    <div class="container">
        <!-- Header -->
        <div class="header">
            <h1>📱 SMS Gateway Multiplataforma</h1>
            <p class="subtitle">Control completo de mensajes SMS - Compatible con Windows, Linux y macOS</p>
        </div>

        <!-- Status Bar -->
        <div class="status-bar">
            <div class="status-indicator">
                <div class="status-dot" id="connection-status"></div>
                <span id="connection-text">Verificando conexión...</span>
            </div>
            <div>
                <span id="system-info">Detectando sistema...</span>
            </div>
        </div>

        <!-- Main Grid -->
        <div class="grid">
            <!-- Connection & Setup -->
            <div class="card">
                <h2>🔧 Configuración del Sistema</h2>
                
                <div class="system-info" id="system-details">
                    <div class="loading"></div> Cargando información del sistema...
                </div>

                <div class="form-group">
                    <label>Puerto Serie:</label>
                    <select id="port-select">
                        <option value="">Auto-detectar</option>
                    </select>
                </div>

                <div class="form-group">
                    <label>Velocidad (bps):</label>
                    <select id="baud-rate">
                        <option value="9600">9600</option>
                        <option value="19200">19200</option>
                        <option value="38400">38400</option>
                        <option value="115200">115200</option>
                    </select>
                </div>

                <div class="form-group">
                    <label>Centro de Mensajes (SMSC):</label>
                    <input type="text" id="smsc-number" placeholder="+51997990000">
                </div>

                <div style="display: flex; gap: 10px;">
                    <button class="btn success" id="connect-btn">🔌 Conectar</button>
                    <button class="btn danger" id="disconnect-btn" disabled>🔌 Desconectar</button>
                    <button class="btn warning" id="test-port-btn">🧪 Probar Puerto</button>
                </div>

                <div id="connection-result"></div>
            </div>

            <!-- Send SMS -->
            <div class="card">
                <h2>📤 Enviar Mensaje</h2>
                
                <form id="send-form">
                    <div class="form-group">
                        <label>Número de Teléfono:</label>
                        <input type="tel" id="phone-number" placeholder="946467799" required>
                    </div>

                    <div class="form-group">
                        <label>Mensaje:</label>
                        <textarea id="message-text" rows="4" placeholder="Escribe tu mensaje aquí..." required></textarea>
                        <small style="color: #666;">Caracteres restantes: <span id="char-count">160</span></small>
                    </div>

                    <button type="submit" class="btn">📤 Enviar SMS</button>
                </form>

                <div id="send-result"></div>
            </div>
        </div>

        <!-- Statistics -->
        <div class="stats">
            <div class="stat-card">
                <div class="stat-number" id="stat-sent">0</div>
                <div class="stat-label">Enviados</div>
            </div>
            <div class="stat-card">
                <div class="stat-number" id="stat-received">0</div>
                <div class="stat-label">Recibidos</div>
            </div>
            <div class="stat-card">
                <div class="stat-number" id="stat-responses">0</div>
                <div class="stat-label">Respuestas</div>
            </div>
            <div class="stat-card">
                <div class="stat-number" id="stat-success-rate">0%</div>
                <div class="stat-label">Éxito</div>
            </div>
        </div>

        <!-- Messages -->
        <div class="grid">
            <!-- Sent Messages -->
            <div class="card">
                <h2>📤 Mensajes Enviados</h2>
                <div class="message-list" id="sent-messages">
                    <p style="text-align: center; color: #666; padding: 20px;">No hay mensajes enviados</p>
                </div>
            </div>

            <!-- Received Messages -->
            <div class="card">
                <h2>📥 Mensajes Recibidos</h2>
                <div class="message-list" id="received-messages">
                    <p style="text-align: center; color: #666; padding: 20px;">No hay mensajes recibidos</p>
                </div>
            </div>
        </div>
    </div>

    <script>
        // Estado global
        let connected = false;
        let autoRefreshInterval;

        // Inicialización
        document.addEventListener('DOMContentLoaded', function() {
            loadSystemInfo();
            loadConfig();
            setupEventListeners();
            startAutoRefresh();
        });

        function setupEventListeners() {
            // Formulario de envío
            document.getElementById('send-form').addEventListener('submit', sendMessage);
            
            // Botones de conexión
            document.getElementById('connect-btn').addEventListener('click', connectGateway);
            document.getElementById('disconnect-btn').addEventListener('click', disconnectGateway);
            document.getElementById('test-port-btn').addEventListener('click', testPort);
            
            // Contador de caracteres
            document.getElementById('message-text').addEventListener('input', updateCharCount);
            
            // Cambios en configuración
            document.getElementById('port-select').addEventListener('change', saveConfig);
            document.getElementById('baud-rate').addEventListener('change', saveConfig);
            document.getElementById('smsc-number').addEventListener('change', saveConfig);
        }

        async function loadSystemInfo() {
            try {
                const response = await fetch('/api/system-info');
                const data = await response.json();
                
                // Actualizar información del sistema
                const systemInfo = document.getElementById('system-info');
                systemInfo.textContent = `${data.os.toUpperCase()} - Python ${data.python_version}`;
                
                // Mostrar detalles del sistema
                const systemDetails = document.getElementById('system-details');
                systemDetails.innerHTML = `
                    <h3>🖥️ Información del Sistema</h3>
                    <div class="info-item">
                        <span>Sistema Operativo:</span>
                        <span>${data.platform}</span>
                    </div>
                    <div class="info-item">
                        <span>Python:</span>
                        <span>${data.python_version}</span>
                    </div>
                    <div class="info-item">
                        <span>Módem Detectado:</span>
                        <span>${data.detected_modem || 'No encontrado'}</span>
                    </div>
                    <div class="info-item">
                        <span>Puertos Disponibles:</span>
                        <span>${data.available_ports.length}</span>
                    </div>
                `;
                
                // Llenar lista de puertos
                const portSelect = document.getElementById('port-select');
                portSelect.innerHTML = '<option value="">Auto-detectar</option>';
                
                data.available_ports.forEach(port => {
                    const option = document.createElement('option');
                    option.value = port.device;
                    option.textContent = `${port.device} - ${port.description}`;
                    if (port.is_huawei) option.textContent += ' (Huawei ✓)';
                    if (port.is_modem) option.textContent += ' (Módem ✓)';
                    portSelect.appendChild(option);
                });
                
            } catch (error) {
                console.error('Error cargando info del sistema:', error);
                showAlert('error', 'Error cargando información del sistema');
            }
        }

        async function loadConfig() {
            try {
                const response = await fetch('/api/config');
                const config = await response.json();
                
                document.getElementById('port-select').value = config.serial_port || '';
                document.getElementById('baud-rate').value = config.baud_rate || 9600;
                document.getElementById('smsc-number').value = config.smsc_number || '+51997990000';
                
            } catch (error) {
                console.error('Error cargando configuración:', error);
            }
        }

        async function saveConfig() {
            const config = {
                serial_port: document.getElementById('port-select').value,
                baud_rate: parseInt(document.getElementById('baud-rate').value),
                smsc_number: document.getElementById('smsc-number').value
            };
            
            try {
                await fetch('/api/config', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(config)
                });
            } catch (error) {
                console.error('Error guardando configuración:', error);
            }
        }

        async function connectGateway() {
            const connectBtn = document.getElementById('connect-btn');
            const resultDiv = document.getElementById('connection-result');
            
            connectBtn.disabled = true;
            connectBtn.innerHTML = '<div class="loading"></div> Conectando...';
            
            try {
                const response = await fetch('/api/connect', { method: 'POST' });
                const result = await response.json();
                
                if (result.success) {
                    connected = true;
                    updateConnectionStatus(true);
                    showAlert('success', `Conectado exitosamente al puerto ${result.port}`, resultDiv);
                    document.getElementById('disconnect-btn').disabled = false;
                } else {
                    showAlert('error', `Error conectando: ${result.error}`, resultDiv);
                }
                
            } catch (error) {
                showAlert('error', `Error de conexión: ${error.message}`, resultDiv);
            } finally {
                connectBtn.disabled = false;
                connectBtn.innerHTML = '🔌 Conectar';
            }
        }

        async function disconnectGateway() {
            try {
                await fetch('/api/disconnect', { method: 'POST' });
                connected = false;
                updateConnectionStatus(false);
                document.getElementById('disconnect-btn').disabled = true;
                showAlert('info', 'Desconectado del gateway', document.getElementById('connection-result'));
            } catch (error) {
                console.error('Error desconectando:', error);
            }
        }

        async function testPort() {
            const port = document.getElementById('port-select').value;
            const testBtn = document.getElementById('test-port-btn');
            
            testBtn.disabled = true;
            testBtn.innerHTML = '<div class="loading"></div> Probando...';
            
            try {
                const response = await fetch('/api/test-port', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ port: port })
                });
                
                const result = await response.json();
                
                if (result.success) {
                    showAlert('success', `Puerto ${result.port} funciona correctamente`, document.getElementById('connection-result'));
                } else {
                    showAlert('error', `Error probando puerto: ${result.error}`, document.getElementById('connection-result'));
                }
                
            } catch (error) {
                showAlert('error', `Error en prueba: ${error.message}`, document.getElementById('connection-result'));
            } finally {
                testBtn.disabled = false;
                testBtn.innerHTML = '🧪 Probar Puerto';
            }
        }

        async function sendMessage(event) {
            event.preventDefault();
            
            if (!connected) {
                showAlert('warning', 'Conecta el gateway antes de enviar mensajes', document.getElementById('send-result'));
                return;
            }
            
            const phoneNumber = document.getElementById('phone-number').value;
            const messageText = document.getElementById('message-text').value;
            const resultDiv = document.getElementById('send-result');
            
            try {
                const response = await fetch('/api/send', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        phone_number: phoneNumber,
                        message: messageText
                    })
                });
                
                const result = await response.json();
                
                if (result.success) {
                    showAlert('success', `Mensaje enviado exitosamente (Ref: ${result.reference_id})`, resultDiv);
                    document.getElementById('send-form').reset();
                    updateCharCount();
                    refreshMessages();
                } else {
                    showAlert('error', `Error enviando mensaje: ${result.error}`, resultDiv);
                }
                
            } catch (error) {
                showAlert('error', `Error de conexión: ${error.message}`, resultDiv);
            }
        }

        function updateCharCount() {
            const messageText = document.getElementById('message-text').value;
            const remaining = 160 - messageText.length;
            document.getElementById('char-count').textContent = remaining;
            document.getElementById('char-count').style.color = remaining < 0 ? '#f44336' : '#666';
        }

        function updateConnectionStatus(isConnected) {
            const statusDot = document.getElementById('connection-status');
            const statusText = document.getElementById('connection-text');
            
            if (isConnected) {
                statusDot.className = 'status-dot connected';
                statusText.textContent = 'Gateway Conectado';
            } else {
                statusDot.className = 'status-dot disconnected';
                statusText.textContent = 'Gateway Desconectado';
            }
        }

        async function refreshMessages() {
            // Implementar carga de mensajes
            try {
                const response = await fetch('/api/messages');
                const data = await response.json();
                
                // Actualizar estadísticas
                document.getElementById('stat-sent').textContent = data.sent.length;
                document.getElementById('stat-received').textContent = data.received.length;
                document.getElementById('stat-responses').textContent = data.received.filter(m => m.is_response).length;
                
                const successRate = data.sent.length > 0 ? 
                    Math.round((data.sent.filter(m => m.success).length / data.sent.length) * 100) : 0;
                document.getElementById('stat-success-rate').textContent = successRate + '%';
                
                // Actualizar listas de mensajes
                updateMessageList('sent-messages', data.sent, 'sent');
                updateMessageList('received-messages', data.received, 'received');
                
            } catch (error) {
                console.error('Error actualizando mensajes:', error);
            }
        }

        function updateMessageList(containerId, messages, type) {
            const container = document.getElementById(containerId);
            
            if (messages.length === 0) {
                container.innerHTML = `<p style="text-align: center; color: #666; padding: 20px;">No hay mensajes ${type === 'sent' ? 'enviados' : 'recibidos'}</p>`;
                return;
            }
            
            container.innerHTML = messages.map(msg => {
                const time = new Date(msg.timestamp || msg.sent_time).toLocaleString();
                
                if (type === 'sent') {
                    return `
                        <div class="message-item sent">
                            <div style="display: flex; justify-content: space-between; margin-bottom: 5px;">
                                <strong>📱 ${msg.phone_number}</strong>
                                <span style="color: #666; font-size: 0.9em;">${time}</span>
                            </div>
                            <div style="margin-bottom: 5px;">${msg.message}</div>
                            <div style="font-size: 0.8em; color: #666;">
                                Estado: ${msg.success ? '✅ Enviado' : '❌ Error'} 
                                ${msg.reference_id ? `| Ref: ${msg.reference_id}` : ''}
                            </div>
                        </div>
                    `;
                } else {
                    return `
                        <div class="message-item ${msg.is_response ? 'response' : 'received'}">
                            <div style="display: flex; justify-content: space-between; margin-bottom: 5px;">
                                <strong>${msg.is_response ? '↩️' : '📨'} ${msg.phone_number}</strong>
                                <span style="color: #666; font-size: 0.9em;">${time}</span>
                            </div>
                            <div>${msg.message}</div>
                            ${msg.is_response ? '<div style="font-size: 0.8em; color: #4CAF50;">Respuesta detectada</div>' : ''}
                        </div>
                    `;
                }
            }).join('');
        }

        function showAlert(type, message, container = null) {
            const alertDiv = document.createElement('div');
            alertDiv.className = `alert ${type}`;
            alertDiv.textContent = message;
            
            if (container) {
                container.innerHTML = '';
                container.appendChild(alertDiv);
            } else {
                document.body.appendChild(alertDiv);
                setTimeout(() => alertDiv.remove(), 5000);
            }
        }

        function startAutoRefresh() {
            // Refrescar cada 10 segundos
            autoRefreshInterval = setInterval(refreshMessages, 10000);
            // Carga inicial
            setTimeout(refreshMessages, 1000);
        }

        // Cleanup al cerrar
        window.addEventListener('beforeunload', function() {
            if (autoRefreshInterval) {
                clearInterval(autoRefreshInterval);
            }
        });
    </script>
</body>
</html>
        """
        self._send_html(html)
    
    def _api_system_info(self):
        """API para información del sistema"""
        try:
            system_info = get_system_info()
            self._send_json(system_info)
        except Exception as e:
            self._send_json({'error': str(e)})
    
    def _api_get_config(self):
        """API para obtener configuración"""
        self._send_json(config_manager.config)
    
    def _api_save_config(self):
        """API para guardar configuración"""
        try:
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            new_config = json.loads(post_data.decode('utf-8'))
            
            # Actualizar configuración
            config_manager.config.update(new_config)
            config_manager.save_config()
            
            self._send_json({'success': True})
        except Exception as e:
            self._send_json({'success': False, 'error': str(e)})
    
    def _api_connect(self):
        """API para conectar al gateway"""
        try:
            # Usar el motor global
            if not hasattr(server_instance, 'engine'):
                server_instance.engine = MultiplatformSMSEngine()
            
            # Conectar en hilo separado
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            try:
                connected = loop.run_until_complete(server_instance.engine.connect())
                
                if connected:
                    port = config_manager.get_serial_port()
                    self._send_json({
                        'success': True,
                        'port': port,
                        'message': 'Gateway conectado exitosamente'
                    })
                else:
                    self._send_json({
                        'success': False,
                        'error': 'No se pudo conectar al gateway'
                    })
                    
            finally:
                loop.close()
                
        except Exception as e:
            self._send_json({'success': False, 'error': str(e)})
    
    def _api_disconnect(self):
        """API para desconectar el gateway"""
        try:
            if hasattr(server_instance, 'engine'):
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                
                try:
                    loop.run_until_complete(server_instance.engine.disconnect())
                finally:
                    loop.close()
            
            self._send_json({'success': True})
        except Exception as e:
            self._send_json({'success': False, 'error': str(e)})
    
    def _api_send_sms(self):
        """API para enviar SMS"""
        try:
            if not hasattr(server_instance, 'engine') or not server_instance.engine.is_connected:
                self._send_json({'success': False, 'error': 'Gateway no conectado'})
                return
            
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode('utf-8'))
            
            phone_number = data.get('phone_number')
            message = data.get('message')
            
            if not phone_number or not message:
                self._send_json({'success': False, 'error': 'Datos incompletos'})
                return
            
            # Enviar SMS
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            try:
                result = loop.run_until_complete(
                    server_instance.engine.send_sms(phone_number, message)
                )
                
                # Guardar en historial
                if not hasattr(server_instance, 'sent_messages'):
                    server_instance.sent_messages = []
                
                server_instance.sent_messages.append({
                    'phone_number': phone_number,
                    'message': message,
                    'success': result.success,
                    'reference_id': result.reference_id,
                    'timestamp': datetime.now().isoformat(),
                    'error': result.error_message
                })
                
                self._send_json({
                    'success': result.success,
                    'reference_id': result.reference_id,
                    'error': result.error_message
                })
                
            finally:
                loop.close()
                
        except Exception as e:
            self._send_json({'success': False, 'error': str(e)})
    
    def _api_test_port(self):
        """API para probar puerto"""
        try:
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode('utf-8'))
            
            port = data.get('port')
            
            # Crear engine temporal para prueba
            test_engine = MultiplatformSMSEngine()
            
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            try:
                connected = loop.run_until_complete(test_engine.connect(port))
                
                if connected:
                    loop.run_until_complete(test_engine.disconnect())
                    self._send_json({'success': True, 'port': port})
                else:
                    self._send_json({'success': False, 'error': 'No se pudo conectar'})
                    
            finally:
                loop.close()
                
        except Exception as e:
            self._send_json({'success': False, 'error': str(e)})
    
    def _api_get_messages(self):
        """API para obtener mensajes"""
        try:
            # Mensajes enviados
            sent_messages = getattr(server_instance, 'sent_messages', [])
            
            # Mensajes recibidos (simular por ahora)
            received_messages = getattr(server_instance, 'received_messages', [])
            
            # Verificar mensajes almacenados si hay conexión
            if (hasattr(server_instance, 'engine') and 
                server_instance.engine.is_connected):
                
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                
                try:
                    stored = loop.run_until_complete(
                        server_instance.engine.check_stored_messages()
                    )
                    
                    # Convertir a formato de recibidos
                    for msg in stored:
                        # Evitar duplicados
                        if not any(r['message'] == msg['content'] and 
                                 r['phone_number'] == msg['sender'] 
                                 for r in received_messages):
                            
                            received_messages.append({
                                'phone_number': msg['sender'],
                                'message': msg['content'],
                                'timestamp': datetime.now().isoformat(),
                                'is_response': False
                            })
                    
                    # Guardar para próximas consultas
                    server_instance.received_messages = received_messages
                    
                finally:
                    loop.close()
            
            self._send_json({
                'sent': sent_messages,
                'received': received_messages
            })
            
        except Exception as e:
            self._send_json({'sent': [], 'received': [], 'error': str(e)})
    
    def _api_get_status(self):
        """API para obtener estado del gateway"""
        try:
            is_connected = (hasattr(server_instance, 'engine') and 
                          server_instance.engine.is_connected)
            
            status = {
                'connected': is_connected,
                'port': config_manager.get_serial_port(),
                'config': config_manager.config
            }
            
            if is_connected:
                # Obtener info de red
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                
                try:
                    network_info = loop.run_until_complete(
                        server_instance.engine.get_network_info()
                    )
                    status['network'] = network_info
                finally:
                    loop.close()
            
            self._send_json(status)
            
        except Exception as e:
            self._send_json({'connected': False, 'error': str(e)})
    
    def _send_json(self, data):
        """Envía respuesta JSON"""
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
        self.wfile.write(json.dumps(data, ensure_ascii=False).encode('utf-8'))
    
    def _send_html(self, html):
        """Envía respuesta HTML"""
        self.send_response(200)
        self.send_header('Content-type', 'text/html; charset=utf-8')
        self.end_headers()
        self.wfile.write(html.encode('utf-8'))
    
    def _send_error(self, code, message):
        """Envía error HTTP"""
        self.send_response(code)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps({'error': message}).encode('utf-8'))
    
    def log_message(self, format, *args):
        """Log personalizado"""
        print(f"🌐 {self.address_string()} - {format % args}")

# Instancia global del servidor
server_instance = None

def run_server():
    """Ejecuta el servidor web"""
    global server_instance
    
    # Configuración del servidor
    host = config_manager.config['web_server']['host']
    port = config_manager.config['web_server']['port']
    
    server_address = (host, port)
    httpd = ThreadedHTTPServer(server_address, SMSGatewayHandler)
    server_instance = httpd
    
    # Inicializar atributos
    server_instance.sent_messages = []
    server_instance.received_messages = []
    
    print("🚀 === SMS GATEWAY MULTIPLATAFORMA ===")
    print(f"🌐 Servidor web: http://localhost:{port}")
    print(f"💻 Sistema: {get_system_info()['os'].upper()}")
    print(f"📱 Puerto detectado: {get_system_info()['detected_modem'] or 'Auto-detectar'}")
    print("\n🔧 Funciones disponibles:")
    print("   ✅ Detección automática de puertos")
    print("   ✅ Configuración multiplataforma")
    print("   ✅ Interfaz web responsive")
    print("   ✅ Envío y recepción SMS")
    print("   ✅ Estadísticas en tiempo real")
    print(f"\nPresiona Ctrl+C para detener")
    
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print(f"\n🛑 Deteniendo servidor...")
        
        # Desconectar gateway si está conectado
        if hasattr(server_instance, 'engine') and server_instance.engine.is_connected:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                loop.run_until_complete(server_instance.engine.disconnect())
            finally:
                loop.close()
        
        httpd.shutdown()
        print("✅ Servidor detenido correctamente")

if __name__ == "__main__":
    run_server()
