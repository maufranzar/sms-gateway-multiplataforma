"""
SMS Gateway Avanzado - Recepción y Estados de Mensaje
"""
import asyncio
import threading
import time
import re
from datetime import datetime
from typing import List, Dict, Optional
from dataclasses import dataclass
from sms_engine_ultra_simple import SMSEngine

@dataclass
class ReceivedSMS:
    phone_number: str
    message: str
    timestamp: datetime
    is_response: bool = False
    related_sent_id: Optional[str] = None

@dataclass
class MessageStatus:
    message_id: str
    phone_number: str
    message: str
    status: str  # pending, sent, delivered, failed, response_received
    sent_time: Optional[datetime] = None
    delivered_time: Optional[datetime] = None
    response_time: Optional[datetime] = None
    response_message: Optional[str] = None
    operator_reference: Optional[str] = None

class AdvancedSMSEngine(SMSEngine):
    """Motor SMS con capacidades de recepción y tracking"""
    
    def __init__(self):
        super().__init__()
        self.message_tracker: Dict[str, MessageStatus] = {}
        self.received_messages: List[ReceivedSMS] = []
        self.monitoring_active = False
        self.monitor_thread: Optional[threading.Thread] = None
    
    async def send_sms_with_tracking(self, phone_number: str, message: str, message_id: str = None) -> MessageStatus:
        """Envía SMS con tracking completo"""
        if not message_id:
            message_id = f"msg_{int(time.time())}"
        
        # Crear registro de tracking
        status = MessageStatus(
            message_id=message_id,
            phone_number=phone_number,
            message=message,
            status="pending",
            sent_time=datetime.now()
        )
        self.message_tracker[message_id] = status
        
        # Enviar SMS
        result = await self.send_sms(phone_number, message)
        
        if result.success:
            status.status = "sent"
            status.operator_reference = result.reference_id
            print(f"✅ SMS {message_id} enviado. Ref: {result.reference_id}")
        else:
            status.status = "failed"
            print(f"❌ SMS {message_id} falló: {result.error_message}")
        
        return status
    
    async def start_message_monitoring(self):
        """Inicia monitoreo de mensajes entrantes"""
        if self.monitoring_active:
            return
        
        try:
            # Intentar diferentes configuraciones CNMI
            cnmi_configs = [
                "1,1,0,0,0",  # Configuración básica
                "0,0,0,0,0",  # Sin notificaciones (polling manual)
                "2,1,0,0,0",  # Almacenar y notificar
            ]
            
            cnmi_success = False
            for config in cnmi_configs:
                try:
                    await self._send_command(f"AT+CNMI={config}")
                    print(f"✅ Configuración CNMI exitosa: {config}")
                    cnmi_success = True
                    break
                except:
                    continue
            
            if not cnmi_success:
                print("⚠️ Usando modo polling manual")
            
            print("🔔 Monitoreo de mensajes activado")
            
            self.monitoring_active = True
            self.monitor_thread = threading.Thread(
                target=self._monitor_loop,
                daemon=True
            )
            self.monitor_thread.start()
            
        except Exception as e:
            print(f"❌ Error iniciando monitoreo: {e}")
            # Continuar con polling manual
            self.monitoring_active = True
            self.monitor_thread = threading.Thread(
                target=self._monitor_loop,  # Usar el mismo loop
                daemon=True
            )
            self.monitor_thread.start()
    
    def _polling_loop(self):
        """Loop de polling manual para verificar mensajes"""
        last_check_time = time.time()
        
        while self.monitoring_active and self.is_connected:
            try:
                current_time = time.time()
                
                # Verificar cada 10 segundos
                if current_time - last_check_time >= 10:
                    # Crear un nuevo loop para las operaciones async
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    
                    try:
                        # Verificar mensajes almacenados
                        stored_messages = loop.run_until_complete(self.check_stored_messages())
                        
                        # Procesar mensajes nuevos
                        for msg in stored_messages:
                            self._process_stored_message(msg)
                        
                        last_check_time = current_time
                        
                    finally:
                        loop.close()
                
                time.sleep(2)
                
            except Exception as e:
                print(f"❌ Error en polling: {e}")
                time.sleep(5)
    
    def _process_stored_message(self, msg_data):
        """Procesa un mensaje almacenado como si fuera entrante"""
        try:
            received_msg = ReceivedSMS(
                phone_number=msg_data['sender'],
                message=msg_data['message'],
                timestamp=datetime.now()
            )
            
            # Verificar si es respuesta
            self._check_if_response(received_msg)
            
            # Evitar duplicados
            msg_signature = f"{received_msg.phone_number}_{received_msg.message}_{received_msg.timestamp.date()}"
            if not hasattr(self, '_processed_messages'):
                self._processed_messages = set()
            
            if msg_signature not in self._processed_messages:
                self.received_messages.append(received_msg)
                self._processed_messages.add(msg_signature)
                print(f"📥 SMS detectado de {received_msg.phone_number}: {received_msg.message}")
            
        except Exception as e:
            print(f"❌ Error procesando mensaje almacenado: {e}")
    
    def _monitor_loop(self):
        """Loop de monitoreo en hilo separado"""
        buffer = ""
        
        while self.monitoring_active and self.is_connected:
            try:
                if self.serial_connection and self.serial_connection.in_waiting > 0:
                    data = self.serial_connection.read(self.serial_connection.in_waiting)
                    buffer += data.decode('utf-8', errors='ignore')
                    
                    # Procesar líneas completas
                    while '\n' in buffer:
                        line, buffer = buffer.split('\n', 1)
                        line = line.strip()
                        
                        if line.startswith('+CMT:'):
                            # Mensaje SMS entrante
                            self._process_incoming_sms(line, buffer)
                        elif line.startswith('+CDS:'):
                            # Reporte de entrega
                            self._process_delivery_report(line)
                
                time.sleep(0.5)
                
            except Exception as e:
                print(f"❌ Error en monitoreo: {e}")
                time.sleep(2)
    
    def _process_incoming_sms(self, header_line: str, buffer: str):
        """Procesa SMS entrante"""
        try:
            # Extraer número del header: +CMT: "+5199999999",,"21/08/22,19:30:15-05"
            phone_match = re.search(r'\+CMT:\s*"([^"]+)"', header_line)
            if phone_match:
                phone_number = phone_match.group(1)
                
                # El mensaje está en la siguiente línea del buffer
                message_lines = buffer.split('\n')
                message_text = message_lines[0] if message_lines else ""
                
                # Crear registro de mensaje recibido
                received_msg = ReceivedSMS(
                    phone_number=phone_number,
                    message=message_text,
                    timestamp=datetime.now()
                )
                
                # Verificar si es respuesta a un mensaje enviado
                self._check_if_response(received_msg)
                
                self.received_messages.append(received_msg)
                print(f"📥 SMS recibido de {phone_number}: {message_text}")
                
        except Exception as e:
            print(f"❌ Error procesando SMS entrante: {e}")
    
    def _check_if_response(self, received_msg: ReceivedSMS):
        """Verifica si el mensaje es respuesta a uno enviado"""
        # Buscar mensajes enviados al mismo número en las últimas 24 horas
        for msg_id, status in self.message_tracker.items():
            if (status.phone_number == received_msg.phone_number and 
                status.status == "sent" and
                status.sent_time and
                (datetime.now() - status.sent_time).total_seconds() < 86400):
                
                # Marcar como respuesta recibida
                status.status = "response_received"
                status.response_time = received_msg.timestamp
                status.response_message = received_msg.message
                received_msg.is_response = True
                received_msg.related_sent_id = msg_id
                
                print(f"💬 Respuesta recibida para mensaje {msg_id}")
                break
    
    def _process_delivery_report(self, line: str):
        """Procesa reporte de entrega"""
        try:
            # +CDS: <fo>,<mr>,<ra>,<tora>,<scts>,<dt>,<st>
            print(f"📨 Reporte de entrega: {line}")
            
            # Extraer referencia del mensaje
            parts = line.replace('+CDS:', '').split(',')
            if len(parts) >= 2:
                message_ref = parts[1].strip()
                
                # Buscar mensaje por referencia
                for status in self.message_tracker.values():
                    if status.operator_reference == message_ref:
                        status.status = "delivered"
                        status.delivered_time = datetime.now()
                        print(f"✅ Mensaje {status.message_id} entregado")
                        break
                        
        except Exception as e:
            print(f"❌ Error procesando reporte: {e}")
    
    async def get_message_status(self, message_id: str) -> Optional[MessageStatus]:
        """Obtiene estado de un mensaje"""
        return self.message_tracker.get(message_id)
    
    async def get_all_statuses(self) -> List[MessageStatus]:
        """Obtiene todos los estados de mensajes"""
        return list(self.message_tracker.values())
    
    async def get_received_messages(self, phone_number: Optional[str] = None) -> List[ReceivedSMS]:
        """Obtiene mensajes recibidos"""
        if phone_number:
            return [msg for msg in self.received_messages if msg.phone_number == phone_number]
        return self.received_messages
    
    async def check_stored_messages(self) -> List[Dict]:
        """Verifica mensajes almacenados en el gateway"""
        try:
            response = await self._send_command('AT+CMGL="ALL"')
            messages = []
            
            # Parsear respuesta de mensajes almacenados
            lines = response.split('\n')
            i = 0
            while i < len(lines):
                line = lines[i].strip()
                if line.startswith('+CMGL:'):
                    # +CMGL: <index>,<stat>,<oa>,<alpha>,<scts>
                    parts = line.split(',')
                    if len(parts) >= 3:
                        index = parts[0].replace('+CMGL:', '').strip()
                        status = parts[1].strip().strip('"')
                        sender = parts[2].strip().strip('"')
                        
                        # El mensaje está en la siguiente línea
                        if i + 1 < len(lines):
                            message_text = lines[i + 1].strip()
                            messages.append({
                                'index': index,
                                'status': status,
                                'sender': sender,
                                'message': message_text
                            })
                i += 1
            
            return messages
            
        except Exception as e:
            print(f"❌ Error verificando mensajes: {e}")
            return []
    
    async def stop_monitoring(self):
        """Detiene el monitoreo"""
        self.monitoring_active = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)
        print("🔔 Monitoreo detenido")

# Instancia global avanzada
advanced_sms_engine = AdvancedSMSEngine()

# Función de utilidad para mostrar estadísticas
def print_status_summary():
    """Muestra resumen de estados"""
    print("\n📊 === RESUMEN DE ESTADOS ===")
    
    for msg_id, status in advanced_sms_engine.message_tracker.items():
        print(f"🔹 {msg_id}: {status.status}")
        print(f"   📱 Para: {status.phone_number}")
        print(f"   💬 Mensaje: {status.message[:50]}...")
        if status.operator_reference:
            print(f"   📋 Ref: {status.operator_reference}")
        if status.response_message:
            print(f"   💬 Respuesta: {status.response_message}")
        print()
    
    print(f"📥 Mensajes recibidos: {len(advanced_sms_engine.received_messages)}")
    for msg in advanced_sms_engine.received_messages[-5:]:  # Últimos 5
        indicator = "↩️" if msg.is_response else "📨"
        print(f"   {indicator} {msg.phone_number}: {msg.message[:30]}...")

if __name__ == "__main__":
    async def demo():
        """Demostración de funciones avanzadas"""
        print("🚀 === DEMO SMS AVANZADO ===")
        
        # Conectar
        await advanced_sms_engine.connect()
        
        # Iniciar monitoreo
        await advanced_sms_engine.start_message_monitoring()
        
        # Enviar mensaje con tracking
        status = await advanced_sms_engine.send_sms_with_tracking(
            "913044047", 
            "Mensaje con tracking - responde OK",
            "test_001"
        )
        
        print(f"Estado inicial: {status.status}")
        
        # Verificar mensajes almacenados
        stored = await advanced_sms_engine.check_stored_messages()
        print(f"Mensajes almacenados: {len(stored)}")
        
        # Esperar unos segundos para posibles respuestas
        print("⏳ Esperando respuestas por 30 segundos...")
        await asyncio.sleep(30)
        
        # Mostrar resumen
        print_status_summary()
        
        # Limpiar
        await advanced_sms_engine.stop_monitoring()
        await advanced_sms_engine.disconnect()
    
    asyncio.run(demo())
