"""
Servidor web ultra-simple sin dependencias externas
"""
import json
import asyncio
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse
import threading
import logging
import os
import sys

# Agregar el directorio actual al path para importar módulos locales
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Configuraciones simples sin pydantic
SERIAL_PORT = "/dev/ttyUSB0"
SERIAL_BAUDRATE = 9600
SERIAL_TIMEOUT = 10
HOST = "0.0.0.0"
PORT = 8000

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Importar motor SMS simple
try:
    from sms_engine_ultra_simple import sms_engine
except ImportError:
    logger.error("No se pudo importar sms_engine_ultra_simple")
    sys.exit(1)

class SMSGatewayHandler(BaseHTTPRequestHandler):
    """Manejador HTTP para el SMS Gateway"""
    
    def do_GET(self):
        """Maneja peticiones GET"""
        parsed_path = urlparse(self.path)
        path = parsed_path.path
        
        try:
            if path == '/':
                self.send_homepage()
            elif path == '/status':
                self.send_status()
            elif path == '/test-sms':
                self.send_test_page()
            else:
                self.send_404()
        except Exception as e:
            logger.error(f"Error en GET {path}: {e}")
            self.send_error_response(str(e))
    
    def do_POST(self):
        """Maneja peticiones POST"""
        parsed_path = urlparse(self.path)
        path = parsed_path.path
        
        try:
            if path == '/send-sms':
                self.send_sms()
            else:
                self.send_404()
        except Exception as e:
            logger.error(f"Error en POST {path}: {e}")
            self.send_error_response(str(e))
    
    def send_homepage(self):
        """Envía la página principal"""
        html = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>SMS Gateway</title>
            <meta charset="UTF-8">
            <style>
                body { font-family: Arial, sans-serif; margin: 40px; background: #f5f5f5; }
                .container { max-width: 800px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
                .status { padding: 15px; border-radius: 8px; margin: 15px 0; background-color: #d4edda; color: #155724; border: 1px solid #c3e6cb; }
                .info { background-color: #d1ecf1; color: #0c5460; border: 1px solid #bee5eb; padding: 15px; border-radius: 8px; margin: 15px 0; }
                h1 { color: #333; text-align: center; }
                h3 { color: #0c5460; }
                .endpoint { background: #f8f9fa; padding: 10px; border-left: 4px solid #007bff; margin: 5px 0; }
                a { color: #007bff; text-decoration: none; }
                a:hover { text-decoration: underline; }
                .test-form { background: #f8f9fa; padding: 20px; border-radius: 8px; margin: 20px 0; }
                input, textarea { width: 100%; padding: 8px; margin: 5px 0; border: 1px solid #ddd; border-radius: 4px; box-sizing: border-box; }
                button { background: #007bff; color: white; padding: 10px 20px; border: none; border-radius: 4px; cursor: pointer; margin: 5px 0; }
                button:hover { background: #0056b3; }
                #result { margin-top: 15px; padding: 10px; border-radius: 4px; }
                .success { background: #d4edda; color: #155724; border: 1px solid #c3e6cb; }
                .error { background: #f8d7da; color: #721c24; border: 1px solid #f5c6cb; }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>🚀 SMS Gateway Huawei E8278</h1>
                <div class="status">
                    ✅ Sistema Funcionando
                </div>
                
                <div class="info">
                    <h3>📡 Información del Sistema</h3>
                    <p><strong>Dispositivo:</strong> Huawei E8278 HiLink</p>
                    <p><strong>Puerto:</strong> /dev/ttyUSB0 @ 9600 bps</p>
                    <p><strong>Operador:</strong> Claro Perú (+51997990000)</p>
                    <p><strong>Servidor:</strong> http://localhost:8000</p>
                </div>
                
                <div class="info">
                    <h3>🔗 Endpoints Disponibles</h3>
                    <div class="endpoint"><a href="/status">📊 Estado del Gateway</a></div>
                    <div class="endpoint"><a href="/test-sms">📨 Formulario de Prueba</a></div>
                </div>
                
                <div class="test-form">
                    <h3>📤 Enviar SMS de Prueba</h3>
                    <form id="smsForm">
                        <input type="text" id="phone" placeholder="Número de teléfono (ej: 913044047)" required>
                        <textarea id="message" placeholder="Mensaje a enviar (máximo 160 caracteres)" rows="3" required maxlength="160"></textarea>
                        <button type="submit">Enviar SMS</button>
                        <button type="button" onclick="testConnection()">Probar Conexión</button>
                    </form>
                    <div id="result"></div>
                </div>
            </div>
            
            <script>
                document.getElementById('smsForm').addEventListener('submit', function(e) {
                    e.preventDefault();
                    
                    const phone = document.getElementById('phone').value;
                    const message = document.getElementById('message').value;
                    const resultDiv = document.getElementById('result');
                    
                    if (!phone || !message) {
                        resultDiv.innerHTML = '<div class="error">❌ Por favor complete todos los campos</div>';
                        return;
                    }
                    
                    resultDiv.innerHTML = '<p style="color: orange;">📤 Enviando SMS...</p>';
                    
                    fetch('/send-sms', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                        },
                        body: JSON.stringify({
                            phone_number: phone,
                            message: message
                        })
                    })
                    .then(response => response.json())
                    .then(data => {
                        if (data.error) {
                            resultDiv.innerHTML = '<div class="error">❌ Error: ' + data.error + '</div>';
                        } else {
                            resultDiv.innerHTML = '<div class="success">✅ SMS enviado exitosamente!<br>Referencia: ' + (data.reference || 'N/A') + '</div>';
                            document.getElementById('smsForm').reset();
                        }
                    })
                    .catch(error => {
                        resultDiv.innerHTML = '<div class="error">❌ Error de conexión: ' + error + '</div>';
                    });
                });
                
                function testConnection() {
                    const resultDiv = document.getElementById('result');
                    resultDiv.innerHTML = '<p style="color: orange;">🔧 Probando conexión...</p>';
                    
                    fetch('/status')
                    .then(response => response.json())
                    .then(data => {
                        if (data.connected) {
                            let networkInfo = '';
                            if (data.network && data.network.operator) {
                                networkInfo = '<br>Operador: ' + data.network.operator;
                                if (data.network.signal_strength) {
                                    networkInfo += '<br>Señal: ' + data.network.signal_strength + '/31';
                                }
                            }
                            resultDiv.innerHTML = '<div class="success">✅ Gateway conectado correctamente' + networkInfo + '</div>';
                        } else {
                            resultDiv.innerHTML = '<div class="error">❌ Gateway no conectado</div>';
                        }
                    })
                    .catch(error => {
                        resultDiv.innerHTML = '<div class="error">❌ Error verificando conexión: ' + error + '</div>';
                    });
                }
            </script>
        </body>
        </html>
        """
        
        self.send_response(200)
        self.send_header('Content-type', 'text/html; charset=utf-8')
        self.end_headers()
        self.wfile.write(html.encode('utf-8'))
    
    def send_test_page(self):
        """Envía página de prueba simplificada"""
        html = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Test SMS</title>
            <meta charset="UTF-8">
            <style>
                body { font-family: Arial, sans-serif; margin: 40px; }
                .form { max-width: 500px; margin: 0 auto; padding: 20px; border: 1px solid #ddd; border-radius: 8px; }
                input, textarea { width: 100%; padding: 10px; margin: 10px 0; border: 1px solid #ddd; border-radius: 4px; box-sizing: border-box; }
                button { width: 100%; padding: 10px; background: #007bff; color: white; border: none; border-radius: 4px; cursor: pointer; }
                button:hover { background: #0056b3; }
                #result { margin-top: 20px; padding: 10px; border-radius: 4px; }
            </style>
        </head>
        <body>
            <div class="form">
                <h2>📱 Enviar SMS</h2>
                <input type="text" id="phone" placeholder="Número (ej: 913044047)" required>
                <textarea id="message" placeholder="Mensaje" rows="4" required></textarea>
                <button onclick="sendSMS()">Enviar</button>
                <div id="result"></div>
            </div>
            
            <script>
                function sendSMS() {
                    const phone = document.getElementById('phone').value;
                    const message = document.getElementById('message').value;
                    const resultDiv = document.getElementById('result');
                    
                    if (!phone || !message) {
                        resultDiv.innerHTML = '<div style="color: red;">Completa todos los campos</div>';
                        return;
                    }
                    
                    resultDiv.innerHTML = '<div style="color: orange;">Enviando...</div>';
                    
                    fetch('/send-sms', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ phone_number: phone, message: message })
                    })
                    .then(response => response.json())
                    .then(data => {
                        if (data.error) {
                            resultDiv.innerHTML = '<div style="color: red;">Error: ' + data.error + '</div>';
                        } else {
                            resultDiv.innerHTML = '<div style="color: green;">✅ Enviado! Ref: ' + (data.reference || 'N/A') + '</div>';
                        }
                    })
                    .catch(error => {
                        resultDiv.innerHTML = '<div style="color: red;">Error: ' + error + '</div>';
                    });
                }
            </script>
        </body>
        </html>
        """
        
        self.send_response(200)
        self.send_header('Content-type', 'text/html; charset=utf-8')
        self.end_headers()
        self.wfile.write(html.encode('utf-8'))
    
    def send_status(self):
        """Envía el estado del gateway"""
        try:
            network_info = {}
            if sms_engine.is_connected:
                network_info = asyncio.run(sms_engine.get_network_info())
            else:
                # Intentar conectar
                connected = asyncio.run(sms_engine.connect())
                if connected:
                    network_info = asyncio.run(sms_engine.get_network_info())
            
            status = {
                "connected": sms_engine.is_connected,
                "timestamp": datetime.now().isoformat(),
                "network": network_info,
                "port": SERIAL_PORT,
                "baudrate": SERIAL_BAUDRATE
            }
            
            self.send_json_response(status)
        except Exception as e:
            self.send_error_response(str(e))
    
    def send_sms(self):
        """Envía un SMS"""
        try:
            content_length = int(self.headers.get('Content-Length', 0))
            if content_length == 0:
                self.send_error_response("No hay datos en la petición")
                return
                
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode('utf-8'))
            
            phone_number = data.get('phone_number', '').strip()
            message = data.get('message', '').strip()
            
            if not phone_number or not message:
                self.send_error_response("phone_number y message son requeridos")
                return
            
            # Limpiar mensaje
            clean_message = message.encode('ascii', errors='ignore').decode('ascii')
            if len(clean_message) > 160:
                clean_message = clean_message[:160]
            
            logger.info(f"📤 Solicitud SMS a {phone_number}: {clean_message}")
            
            # Enviar SMS en background
            threading.Thread(
                target=self.process_sms_background,
                args=(phone_number, clean_message),
                daemon=True
            ).start()
            
            response = {
                "success": True,
                "phone_number": phone_number,
                "message": clean_message,
                "status": "processing"
            }
            
            self.send_json_response(response)
            
        except json.JSONDecodeError:
            self.send_error_response("JSON inválido")
        except Exception as e:
            logger.error(f"Error en send_sms: {e}")
            self.send_error_response(str(e))
    
    def process_sms_background(self, phone_number: str, message: str):
        """Procesa el envío de SMS en background"""
        try:
            logger.info(f"🔄 Procesando SMS en background para {phone_number}")
            
            # Conectar si no está conectado
            if not sms_engine.is_connected:
                logger.info("📡 Conectando al gateway...")
                connected = asyncio.run(sms_engine.connect())
                if not connected:
                    logger.error("❌ No se pudo conectar al gateway")
                    return
            
            # Enviar SMS
            result = asyncio.run(sms_engine.send_sms(phone_number, message))
            
            if result.success:
                logger.info(f"✅ SMS enviado exitosamente. Referencia: {result.reference_id}")
            else:
                logger.error(f"❌ Error enviando SMS: {result.error_message}")
                
        except Exception as e:
            logger.error(f"❌ Error en background SMS: {e}")
    
    def send_json_response(self, data):
        """Envía una respuesta JSON"""
        self.send_response(200)
        self.send_header('Content-type', 'application/json; charset=utf-8')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
        self.wfile.write(json.dumps(data, default=str, ensure_ascii=False).encode('utf-8'))
    
    def send_error_response(self, error_message):
        """Envía una respuesta de error"""
        self.send_response(500)
        self.send_header('Content-type', 'application/json; charset=utf-8')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        error_data = {"error": error_message}
        self.wfile.write(json.dumps(error_data, ensure_ascii=False).encode('utf-8'))
    
    def send_404(self):
        """Envía error 404"""
        self.send_response(404)
        self.send_header('Content-type', 'text/html; charset=utf-8')
        self.end_headers()
        html = "<h1>404 - Página no encontrada</h1><a href='/'>Volver al inicio</a>"
        self.wfile.write(html.encode('utf-8'))
    
    def do_OPTIONS(self):
        """Maneja peticiones OPTIONS para CORS"""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
    
    def log_message(self, format, *args):
        """Sobrescribe el logging por defecto"""
        logger.info(f"{self.address_string()} - {format % args}")

def start_server():
    """Inicia el servidor HTTP"""
    # Crear servidor
    server_address = (HOST, PORT)
    httpd = HTTPServer(server_address, SMSGatewayHandler)
    
    logger.info(f"🚀 SMS Gateway iniciado en http://{HOST}:{PORT}")
    logger.info(f"📡 Puerto serie: {SERIAL_PORT} @ {SERIAL_BAUDRATE} bps")
    logger.info(f"🌐 Accede a http://localhost:{PORT} para la interfaz web")
    
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        logger.info("🔌 Cerrando servidor...")
        try:
            asyncio.run(sms_engine.disconnect())
        except:
            pass
        httpd.shutdown()

if __name__ == "__main__":
    start_server()
