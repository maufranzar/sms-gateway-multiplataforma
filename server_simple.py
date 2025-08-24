#!/usr/bin/env python3
"""
Servidor web básico para el SMS Gateway
Funciona sin FastAPI para evitar problemas de compatibilidad
"""
import json
import asyncio
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import threading
import logging

from config import settings
from database import create_tables, get_db_sync
from models import SMSMessage, Device, MessageStatus, MessageType
from sms_engine import sms_engine

# Configurar logging
logging.basicConfig(level=getattr(logging, settings.LOG_LEVEL))
logger = logging.getLogger(__name__)

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
            elif path == '/messages':
                self.send_messages()
            elif path == '/network-info':
                self.send_network_info()
            elif path == '/devices':
                self.send_devices()
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
            elif path == '/devices':
                self.create_device()
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
                input, textarea { width: 100%; padding: 8px; margin: 5px 0; border: 1px solid #ddd; border-radius: 4px; }
                button { background: #007bff; color: white; padding: 10px 20px; border: none; border-radius: 4px; cursor: pointer; }
                button:hover { background: #0056b3; }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>🚀 SMS Gateway</h1>
                <div class="status">
                    ✅ Sistema Funcionando
                </div>
                
                <div class="info">
                    <h3>📡 Información del Sistema</h3>
                    <p><strong>Dispositivo:</strong> Huawei E8278 HiLink</p>
                    <p><strong>Puerto:</strong> /dev/ttyUSB0 @ 9600 bps</p>
                    <p><strong>Operador:</strong> Claro Perú</p>
                    <p><strong>Servidor:</strong> http://localhost:8000</p>
                </div>
                
                <div class="info">
                    <h3>🔗 Endpoints</h3>
                    <div class="endpoint"><a href="/status">📊 Estado del Gateway</a></div>
                    <div class="endpoint"><a href="/messages">📨 Lista de Mensajes</a></div>
                    <div class="endpoint"><a href="/network-info">🌐 Información de Red</a></div>
                    <div class="endpoint"><a href="/devices">📱 Dispositivos</a></div>
                </div>
                
                <div class="test-form">
                    <h3>📤 Enviar SMS de Prueba</h3>
                    <form id="smsForm">
                        <input type="text" id="phone" placeholder="Número de teléfono (ej: 913044047)" required>
                        <textarea id="message" placeholder="Mensaje a enviar" rows="3" required></textarea>
                        <button type="submit">Enviar SMS</button>
                    </form>
                    <div id="result" style="margin-top: 15px;"></div>
                </div>
            </div>
            
            <script>
                document.getElementById('smsForm').addEventListener('submit', function(e) {
                    e.preventDefault();
                    
                    const phone = document.getElementById('phone').value;
                    const message = document.getElementById('message').value;
                    const resultDiv = document.getElementById('result');
                    
                    resultDiv.innerHTML = '<p style="color: orange;">📤 Enviando...</p>';
                    
                    fetch('/send-sms', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                        },
                        body: JSON.stringify({
                            phone_number: phone,
                            message: message,
                            message_type: 'command'
                        })
                    })
                    .then(response => response.json())
                    .then(data => {
                        if (data.error) {
                            resultDiv.innerHTML = '<p style="color: red;">❌ Error: ' + data.error + '</p>';
                        } else {
                            resultDiv.innerHTML = '<p style="color: green;">✅ SMS enviado. ID: ' + data.id + '</p>';
                        }
                    })
                    .catch(error => {
                        resultDiv.innerHTML = '<p style="color: red;">❌ Error: ' + error + '</p>';
                    });
                });
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
            if sms_engine.is_connected:
                network_info = asyncio.run(sms_engine.get_network_info())
            else:
                network_info = {"error": "Gateway no conectado"}
            
            status = {
                "connected": sms_engine.is_connected,
                "timestamp": datetime.now().isoformat(),
                "network": network_info,
                "port": settings.SERIAL_PORT,
                "baudrate": settings.SERIAL_BAUDRATE
            }
            
            self.send_json_response(status)
        except Exception as e:
            self.send_error_response(str(e))
    
    def send_messages(self):
        """Envía la lista de mensajes"""
        try:
            db = get_db_sync()
            messages = db.query(SMSMessage).order_by(SMSMessage.created_at.desc()).limit(20).all()
            
            result = []
            for msg in messages:
                result.append({
                    "id": msg.id,
                    "phone_number": msg.phone_number,
                    "message": msg.message,
                    "status": msg.status.value,
                    "reference_id": msg.reference_id,
                    "created_at": msg.created_at.isoformat() if msg.created_at else None,
                    "sent_at": msg.sent_at.isoformat() if msg.sent_at else None,
                    "error_message": msg.error_message
                })
            
            db.close()
            self.send_json_response(result)
        except Exception as e:
            self.send_error_response(str(e))
    
    def send_network_info(self):
        """Envía información de red"""
        try:
            if not sms_engine.is_connected:
                connected = asyncio.run(sms_engine.connect())
                if not connected:
                    self.send_error_response("No se pudo conectar al gateway")
                    return
            
            info = asyncio.run(sms_engine.get_network_info())
            self.send_json_response(info)
        except Exception as e:
            self.send_error_response(str(e))
    
    def send_devices(self):
        """Envía lista de dispositivos"""
        try:
            db = get_db_sync()
            devices = db.query(Device).filter(Device.is_active == True).all()
            
            result = []
            for device in devices:
                result.append({
                    "id": device.id,
                    "phone_number": device.phone_number,
                    "name": device.name,
                    "description": device.description,
                    "is_active": device.is_active,
                    "created_at": device.created_at.isoformat() if device.created_at else None
                })
            
            db.close()
            self.send_json_response(result)
        except Exception as e:
            self.send_error_response(str(e))
    
    def send_sms(self):
        """Envía un SMS"""
        try:
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode('utf-8'))
            
            phone_number = data.get('phone_number')
            message = data.get('message')
            
            if not phone_number or not message:
                self.send_error_response("phone_number y message son requeridos")
                return
            
            # Crear registro en base de datos
            db = get_db_sync()
            db_message = SMSMessage(
                phone_number=phone_number,
                message=message,
                message_type=MessageType.COMMAND,
                status=MessageStatus.PENDING
            )
            db.add(db_message)
            db.commit()
            db.refresh(db_message)
            message_id = db_message.id
            db.close()
            
            # Enviar SMS en background
            threading.Thread(
                target=self.process_sms_background,
                args=(message_id, phone_number, message),
                daemon=True
            ).start()
            
            response = {
                "id": message_id,
                "phone_number": phone_number,
                "message": message,
                "status": "pending"
            }
            
            self.send_json_response(response)
            
        except Exception as e:
            self.send_error_response(str(e))
    
    def process_sms_background(self, message_id: int, phone_number: str, message: str):
        """Procesa el envío de SMS en background"""
        try:
            # Conectar si no está conectado
            if not sms_engine.is_connected:
                connected = asyncio.run(sms_engine.connect())
                if not connected:
                    self.update_message_status(message_id, MessageStatus.FAILED, "No se pudo conectar al gateway")
                    return
            
            # Enviar SMS
            result = asyncio.run(sms_engine.send_sms(phone_number, message))
            
            if result.success:
                self.update_message_status(message_id, MessageStatus.SENT, None, result.reference_id)
            else:
                self.update_message_status(message_id, MessageStatus.FAILED, result.error_message)
                
        except Exception as e:
            logger.error(f"Error en background SMS {message_id}: {e}")
            self.update_message_status(message_id, MessageStatus.FAILED, str(e))
    
    def update_message_status(self, message_id: int, status: MessageStatus, error_message: str = None, reference_id: str = None):
        """Actualiza el estado de un mensaje"""
        try:
            db = get_db_sync()
            message = db.query(SMSMessage).filter(SMSMessage.id == message_id).first()
            if message:
                message.status = status
                if error_message:
                    message.error_message = error_message
                if reference_id:
                    message.reference_id = reference_id
                if status == MessageStatus.SENT:
                    message.sent_at = datetime.now()
                db.commit()
            db.close()
        except Exception as e:
            logger.error(f"Error actualizando mensaje {message_id}: {e}")
    
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
        self.send_header('Content-type', 'application/json; charset=utf-8')
        self.end_headers()
        error_data = {"error": "Endpoint no encontrado"}
        self.wfile.write(json.dumps(error_data, ensure_ascii=False).encode('utf-8'))
    
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
    # Inicializar base de datos
    create_tables()
    logger.info("✅ Base de datos inicializada")
    
    # Crear servidor
    server_address = (settings.HOST, settings.PORT)
    httpd = HTTPServer(server_address, SMSGatewayHandler)
    
    logger.info(f"🚀 Servidor iniciado en http://{settings.HOST}:{settings.PORT}")
    logger.info(f"📡 Gateway SMS configurado en {settings.SERIAL_PORT}")
    
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        logger.info("🔌 Cerrando servidor...")
        asyncio.run(sms_engine.disconnect())
        httpd.shutdown()

if __name__ == "__main__":
    start_server()
