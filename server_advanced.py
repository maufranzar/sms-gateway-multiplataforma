"""
Servidor SMS Gateway Avanzado - Con Recepción y Estados
"""
import asyncio
import json
import urllib.parse
from http.server import HTTPServer, BaseHTTPRequestHandler
from socketserver import ThreadingMixIn
from datetime import datetime
from advanced_sms_engine import advanced_sms_engine, print_status_summary

class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
    """Servidor HTTP con soporte para múltiples threads"""
    daemon_threads = True

class AdvancedSMSHandler(BaseHTTPRequestHandler):
    
    def do_GET(self):
        """Maneja peticiones GET"""
        if self.path == '/':
            self._serve_dashboard()
        elif self.path == '/api/status':
            self._api_get_status()
        elif self.path.startswith('/api/message/'):
            message_id = self.path.split('/')[-1]
            self._api_get_message_status(message_id)
        elif self.path == '/api/received':
            self._api_get_received_messages()
        elif self.path == '/api/stored':
            self._api_get_stored_messages()
        elif self.path == '/dashboard':
            self._serve_live_dashboard()
        else:
            self._send_error(404, "Endpoint no encontrado")
    
    def do_POST(self):
        """Maneja peticiones POST"""
        if self.path == '/api/send':
            self._api_send_sms()
        elif self.path == '/api/start_monitoring':
            self._api_start_monitoring()
        elif self.path == '/api/stop_monitoring':
            self._api_stop_monitoring()
        else:
            self._send_error(404, "Endpoint no encontrado")
    
    def _serve_dashboard(self):
        """Sirve dashboard principal"""
        html = """
<!DOCTYPE html>
<html>
<head>
    <title>SMS Gateway Avanzado</title>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: Arial, sans-serif; background: #f5f5f5; }
        .container { max-width: 1200px; margin: 0 auto; padding: 20px; }
        .header { background: #2c3e50; color: white; padding: 20px; border-radius: 8px; margin-bottom: 20px; }
        .card { background: white; border-radius: 8px; padding: 20px; margin-bottom: 20px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        .grid { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }
        .form-group { margin-bottom: 15px; }
        label { display: block; margin-bottom: 5px; font-weight: bold; }
        input, textarea, select { width: 100%; padding: 8px; border: 1px solid #ddd; border-radius: 4px; }
        button { background: #3498db; color: white; padding: 10px 20px; border: none; border-radius: 4px; cursor: pointer; }
        button:hover { background: #2980b9; }
        button.danger { background: #e74c3c; }
        button.danger:hover { background: #c0392b; }
        button.success { background: #27ae60; }
        button.success:hover { background: #229954; }
        .status { padding: 10px; border-radius: 4px; margin: 10px 0; }
        .status.success { background: #d4edda; color: #155724; }
        .status.error { background: #f8d7da; color: #721c24; }
        .status.info { background: #d1ecf1; color: #0c5460; }
        .message-list { max-height: 400px; overflow-y: auto; }
        .message-item { border: 1px solid #ddd; padding: 10px; margin: 5px 0; border-radius: 4px; }
        .message-sent { background: #e3f2fd; }
        .message-received { background: #f3e5f5; }
        .message-response { background: #e8f5e8; }
        .auto-refresh { margin: 10px 0; }
        .stats { display: grid; grid-template-columns: repeat(4, 1fr); gap: 10px; }
        .stat-card { text-align: center; padding: 15px; background: #ecf0f1; border-radius: 4px; }
        .monitoring-status { font-size: 18px; margin: 10px 0; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📱 SMS Gateway Avanzado</h1>
            <p>Control completo de mensajes SMS - Envío, Recepción y Estados</p>
            <div class="monitoring-status">
                🔔 Estado de Monitoreo: <span id="monitoring-status">Verificando...</span>
            </div>
        </div>

        <div class="grid">
            <!-- Panel de Envío -->
            <div class="card">
                <h2>📤 Enviar Mensaje</h2>
                <form id="send-form">
                    <div class="form-group">
                        <label>Número de teléfono:</label>
                        <input type="tel" id="phone" placeholder="913044047" required>
                    </div>
                    <div class="form-group">
                        <label>Mensaje:</label>
                        <textarea id="message" rows="3" placeholder="Tu mensaje aquí..." required></textarea>
                    </div>
                    <div class="form-group">
                        <label>ID del mensaje (opcional):</label>
                        <input type="text" id="message-id" placeholder="Se genera automáticamente">
                    </div>
                    <button type="submit">📤 Enviar con Tracking</button>
                </form>
                <div id="send-status"></div>
            </div>

            <!-- Panel de Control -->
            <div class="card">
                <h2>⚙️ Control del Sistema</h2>
                <div class="form-group">
                    <button id="start-monitoring" class="success">🔔 Iniciar Monitoreo</button>
                    <button id="stop-monitoring" class="danger">⏹️ Detener Monitoreo</button>
                </div>
                <div class="form-group">
                    <button id="refresh-data">🔄 Actualizar Datos</button>
                    <button id="check-stored">📋 Verificar Almacenados</button>
                </div>
                <div class="auto-refresh">
                    <label>
                        <input type="checkbox" id="auto-refresh"> Auto-actualizar cada 5s
                    </label>
                </div>
            </div>
        </div>

        <!-- Estadísticas -->
        <div class="card">
            <h2>📊 Estadísticas</h2>
            <div class="stats" id="stats">
                <div class="stat-card">
                    <div>Enviados</div>
                    <div id="stat-sent">0</div>
                </div>
                <div class="stat-card">
                    <div>Entregados</div>
                    <div id="stat-delivered">0</div>
                </div>
                <div class="stat-card">
                    <div>Recibidos</div>
                    <div id="stat-received">0</div>
                </div>
                <div class="stat-card">
                    <div>Respuestas</div>
                    <div id="stat-responses">0</div>
                </div>
            </div>
        </div>

        <div class="grid">
            <!-- Estados de Mensajes -->
            <div class="card">
                <h2>📋 Estados de Mensajes Enviados</h2>
                <div class="message-list" id="sent-messages">
                    <p>Cargando estados...</p>
                </div>
            </div>

            <!-- Mensajes Recibidos -->
            <div class="card">
                <h2>📥 Mensajes Recibidos</h2>
                <div class="message-list" id="received-messages">
                    <p>Cargando mensajes...</p>
                </div>
            </div>
        </div>
    </div>

    <script>
        let autoRefreshInterval;

        // Inicialización
        document.addEventListener('DOMContentLoaded', function() {
            refreshAllData();
            setupEventListeners();
        });

        function setupEventListeners() {
            // Formulario de envío
            document.getElementById('send-form').addEventListener('submit', sendMessage);
            
            // Botones de control
            document.getElementById('start-monitoring').addEventListener('click', startMonitoring);
            document.getElementById('stop-monitoring').addEventListener('click', stopMonitoring);
            document.getElementById('refresh-data').addEventListener('click', refreshAllData);
            document.getElementById('check-stored').addEventListener('click', checkStoredMessages);
            
            // Auto-refresh
            document.getElementById('auto-refresh').addEventListener('change', toggleAutoRefresh);
        }

        async function sendMessage(e) {
            e.preventDefault();
            
            const phone = document.getElementById('phone').value;
            const message = document.getElementById('message').value;
            const messageId = document.getElementById('message-id').value;
            
            const statusDiv = document.getElementById('send-status');
            statusDiv.innerHTML = '<div class="status info">Enviando mensaje...</div>';
            
            try {
                const response = await fetch('/api/send', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        phone_number: phone,
                        message: message,
                        message_id: messageId || undefined
                    })
                });
                
                const result = await response.json();
                
                if (result.success) {
                    statusDiv.innerHTML = `<div class="status success">✅ Mensaje enviado. ID: ${result.message_id}, Ref: ${result.reference_id}</div>`;
                    document.getElementById('send-form').reset();
                    setTimeout(refreshAllData, 1000);
                } else {
                    statusDiv.innerHTML = `<div class="status error">❌ Error: ${result.error}</div>`;
                }
                
            } catch (error) {
                statusDiv.innerHTML = `<div class="status error">❌ Error de conexión: ${error.message}</div>`;
            }
        }

        async function startMonitoring() {
            try {
                const response = await fetch('/api/start_monitoring', { method: 'POST' });
                const result = await response.json();
                updateMonitoringStatus(true);
                showNotification(result.message, 'success');
            } catch (error) {
                showNotification('Error iniciando monitoreo: ' + error.message, 'error');
            }
        }

        async function stopMonitoring() {
            try {
                const response = await fetch('/api/stop_monitoring', { method: 'POST' });
                const result = await response.json();
                updateMonitoringStatus(false);
                showNotification(result.message, 'info');
            } catch (error) {
                showNotification('Error deteniendo monitoreo: ' + error.message, 'error');
            }
        }

        async function refreshAllData() {
            await Promise.all([
                loadSentMessages(),
                loadReceivedMessages(),
                updateStats()
            ]);
        }

        async function loadSentMessages() {
            try {
                const response = await fetch('/api/status');
                const data = await response.json();
                
                const container = document.getElementById('sent-messages');
                if (data.messages.length === 0) {
                    container.innerHTML = '<p>No hay mensajes enviados</p>';
                    return;
                }
                
                container.innerHTML = data.messages.map(msg => `
                    <div class="message-item message-sent">
                        <strong>📱 ${msg.phone_number}</strong> 
                        <span class="status ${getStatusClass(msg.status)}">${getStatusEmoji(msg.status)} ${msg.status}</span>
                        <div>${msg.message}</div>
                        <small>ID: ${msg.message_id} | Enviado: ${formatTime(msg.sent_time)}</small>
                        ${msg.response_message ? `<div style="margin-top: 5px; padding: 5px; background: #e8f5e8; border-radius: 3px;">💬 Respuesta: ${msg.response_message}</div>` : ''}
                    </div>
                `).join('');
                
            } catch (error) {
                document.getElementById('sent-messages').innerHTML = `<p>Error cargando mensajes: ${error.message}</p>`;
            }
        }

        async function loadReceivedMessages() {
            try {
                const response = await fetch('/api/received');
                const data = await response.json();
                
                const container = document.getElementById('received-messages');
                if (data.messages.length === 0) {
                    container.innerHTML = '<p>No hay mensajes recibidos</p>';
                    return;
                }
                
                container.innerHTML = data.messages.map(msg => `
                    <div class="message-item ${msg.is_response ? 'message-response' : 'message-received'}">
                        <strong>📱 ${msg.phone_number}</strong>
                        ${msg.is_response ? '↩️ Respuesta' : '📨 Mensaje'}
                        <div>${msg.message}</div>
                        <small>Recibido: ${formatTime(msg.timestamp)}</small>
                        ${msg.related_sent_id ? `<small> | Relacionado: ${msg.related_sent_id}</small>` : ''}
                    </div>
                `).join('');
                
            } catch (error) {
                document.getElementById('received-messages').innerHTML = `<p>Error cargando mensajes: ${error.message}</p>`;
            }
        }

        async function updateStats() {
            try {
                const [statusResponse, receivedResponse] = await Promise.all([
                    fetch('/api/status'),
                    fetch('/api/received')
                ]);
                
                const statusData = await statusResponse.json();
                const receivedData = await receivedResponse.json();
                
                const stats = {
                    sent: statusData.messages.length,
                    delivered: statusData.messages.filter(m => m.status === 'delivered').length,
                    received: receivedData.messages.length,
                    responses: receivedData.messages.filter(m => m.is_response).length
                };
                
                document.getElementById('stat-sent').textContent = stats.sent;
                document.getElementById('stat-delivered').textContent = stats.delivered;
                document.getElementById('stat-received').textContent = stats.received;
                document.getElementById('stat-responses').textContent = stats.responses;
                
            } catch (error) {
                console.error('Error actualizando estadísticas:', error);
            }
        }

        async function checkStoredMessages() {
            try {
                const response = await fetch('/api/stored');
                const data = await response.json();
                alert(`Mensajes almacenados en gateway: ${data.messages.length}`);
            } catch (error) {
                alert('Error verificando mensajes: ' + error.message);
            }
        }

        function toggleAutoRefresh() {
            const checkbox = document.getElementById('auto-refresh');
            if (checkbox.checked) {
                autoRefreshInterval = setInterval(refreshAllData, 5000);
            } else {
                clearInterval(autoRefreshInterval);
            }
        }

        function updateMonitoringStatus(active) {
            const status = document.getElementById('monitoring-status');
            status.textContent = active ? 'Activo 🟢' : 'Inactivo 🔴';
        }

        function getStatusClass(status) {
            const classes = {
                'pending': 'info',
                'sent': 'info',
                'delivered': 'success',
                'failed': 'error',
                'response_received': 'success'
            };
            return classes[status] || 'info';
        }

        function getStatusEmoji(status) {
            const emojis = {
                'pending': '⏳',
                'sent': '📤',
                'delivered': '✅',
                'failed': '❌',
                'response_received': '💬'
            };
            return emojis[status] || '📋';
        }

        function formatTime(timeStr) {
            if (!timeStr) return 'N/A';
            const date = new Date(timeStr);
            return date.toLocaleString();
        }

        function showNotification(message, type) {
            // Crear notificación temporal
            const notification = document.createElement('div');
            notification.className = `status ${type}`;
            notification.textContent = message;
            notification.style.position = 'fixed';
            notification.style.top = '20px';
            notification.style.right = '20px';
            notification.style.zIndex = '1000';
            notification.style.minWidth = '300px';
            
            document.body.appendChild(notification);
            
            setTimeout(() => {
                document.body.removeChild(notification);
            }, 3000);
        }
    </script>
</body>
</html>
        """
        self._send_html(html)
    
    def _api_send_sms(self):
        """API para enviar SMS con tracking"""
        try:
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode('utf-8'))
            
            phone_number = data.get('phone_number')
            message = data.get('message')
            message_id = data.get('message_id')
            
            if not phone_number or not message:
                self._send_json({'success': False, 'error': 'Faltan datos requeridos'})
                return
            
            # Ejecutar envío en loop de asyncio
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            try:
                status = loop.run_until_complete(
                    advanced_sms_engine.send_sms_with_tracking(phone_number, message, message_id)
                )
                
                response = {
                    'success': True,
                    'message_id': status.message_id,
                    'status': status.status,
                    'reference_id': status.operator_reference
                }
                
            finally:
                loop.close()
            
            self._send_json(response)
            
        except Exception as e:
            self._send_json({'success': False, 'error': str(e)})
    
    def _api_get_status(self):
        """API para obtener estados de mensajes"""
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            try:
                statuses = loop.run_until_complete(advanced_sms_engine.get_all_statuses())
                
                messages = []
                for status in statuses:
                    messages.append({
                        'message_id': status.message_id,
                        'phone_number': status.phone_number,
                        'message': status.message,
                        'status': status.status,
                        'sent_time': status.sent_time.isoformat() if status.sent_time else None,
                        'delivered_time': status.delivered_time.isoformat() if status.delivered_time else None,
                        'response_time': status.response_time.isoformat() if status.response_time else None,
                        'response_message': status.response_message,
                        'operator_reference': status.operator_reference
                    })
                
                self._send_json({
                    'success': True,
                    'messages': messages,
                    'total': len(messages)
                })
                
            finally:
                loop.close()
                
        except Exception as e:
            self._send_json({'success': False, 'error': str(e)})
    
    def _api_get_received_messages(self):
        """API para obtener mensajes recibidos"""
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            try:
                received = loop.run_until_complete(advanced_sms_engine.get_received_messages())
                
                messages = []
                for msg in received:
                    messages.append({
                        'phone_number': msg.phone_number,
                        'message': msg.message,
                        'timestamp': msg.timestamp.isoformat(),
                        'is_response': msg.is_response,
                        'related_sent_id': msg.related_sent_id
                    })
                
                self._send_json({
                    'success': True,
                    'messages': messages,
                    'total': len(messages)
                })
                
            finally:
                loop.close()
                
        except Exception as e:
            self._send_json({'success': False, 'error': str(e)})
    
    def _api_get_stored_messages(self):
        """API para verificar mensajes almacenados"""
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            try:
                stored = loop.run_until_complete(advanced_sms_engine.check_stored_messages())
                
                self._send_json({
                    'success': True,
                    'messages': stored,
                    'total': len(stored)
                })
                
            finally:
                loop.close()
                
        except Exception as e:
            self._send_json({'success': False, 'error': str(e)})
    
    def _api_start_monitoring(self):
        """API para iniciar monitoreo"""
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            try:
                loop.run_until_complete(advanced_sms_engine.start_message_monitoring())
                self._send_json({
                    'success': True,
                    'message': 'Monitoreo de mensajes iniciado'
                })
                
            finally:
                loop.close()
                
        except Exception as e:
            self._send_json({'success': False, 'error': str(e)})
    
    def _api_stop_monitoring(self):
        """API para detener monitoreo"""
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            try:
                loop.run_until_complete(advanced_sms_engine.stop_monitoring())
                self._send_json({
                    'success': True,
                    'message': 'Monitoreo de mensajes detenido'
                })
                
            finally:
                loop.close()
                
        except Exception as e:
            self._send_json({'success': False, 'error': str(e)})
    
    def _send_json(self, data):
        """Envía respuesta JSON"""
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(data, ensure_ascii=False).encode('utf-8'))
    
    def _send_html(self, html):
        """Envía respuesta HTML"""
        self.send_response(200)
        self.send_header('Content-type', 'text/html; charset=utf-8')
        self.end_headers()
        self.wfile.write(html.encode('utf-8'))
    
    def _send_error(self, code, message):
        """Envía error"""
        self.send_response(code)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps({'error': message}).encode('utf-8'))
    
    def log_message(self, format, *args):
        """Personalizar logging"""
        print(f"🌐 {self.address_string()} - {format % args}")

async def initialize_gateway():
    """Inicializa el gateway SMS"""
    print("🔧 Inicializando SMS Gateway Avanzado...")
    
    try:
        await advanced_sms_engine.connect()
        print("✅ Gateway conectado")
        
        # Iniciar monitoreo automático
        await advanced_sms_engine.start_message_monitoring()
        print("🔔 Monitoreo de mensajes iniciado")
        
        return True
        
    except Exception as e:
        print(f"❌ Error inicializando: {e}")
        return False

def run_server():
    """Ejecuta el servidor"""
    server_address = ('', 8000)
    httpd = ThreadedHTTPServer(server_address, AdvancedSMSHandler)
    
    print("🚀 === SMS GATEWAY AVANZADO ===")
    print("🌐 Servidor ejecutándose en http://localhost:8000")
    print("📱 Funciones disponibles:")
    print("   ✅ Envío de SMS con tracking")
    print("   📥 Recepción automática de mensajes")
    print("   📊 Estados de entrega en tiempo real")
    print("   💬 Detección de respuestas")
    print("   📋 Dashboard web interactivo")
    print("\n🔧 Endpoints API:")
    print("   POST /api/send - Enviar SMS")
    print("   GET  /api/status - Estados de mensajes")
    print("   GET  /api/received - Mensajes recibidos")
    print("   GET  /api/stored - Mensajes almacenados")
    print("   POST /api/start_monitoring - Iniciar monitoreo")
    print("   POST /api/stop_monitoring - Detener monitoreo")
    print("\nPresiona Ctrl+C para detener")
    
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n🛑 Deteniendo servidor...")
        asyncio.run(advanced_sms_engine.stop_monitoring())
        asyncio.run(advanced_sms_engine.disconnect())
        httpd.shutdown()
        print("✅ Servidor detenido correctamente")

if __name__ == "__main__":
    # Inicializar gateway
    if asyncio.run(initialize_gateway()):
        run_server()
    else:
        print("❌ No se pudo inicializar el gateway")
