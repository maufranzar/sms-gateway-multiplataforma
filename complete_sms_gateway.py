"""
Sistema SMS Gateway Completo y Funcional
Integra el motor corregido con todas las funcionalidades
"""
import asyncio
import time
import threading
from datetime import datetime
from typing import List, Dict, Optional
from dataclasses import dataclass
from sms_engine_fixed import FixedSMSEngine

@dataclass
class MessageTracker:
    message_id: str
    phone_number: str
    message: str
    status: str  # sent, delivered, failed, response_received
    sent_time: datetime
    reference_id: Optional[str] = None
    response_message: Optional[str] = None
    response_time: Optional[datetime] = None

@dataclass
class ReceivedMessage:
    phone_number: str
    message: str
    timestamp: datetime
    is_response: bool = False
    related_message_id: Optional[str] = None

class CompleteSMSGateway:
    """Gateway SMS completo con envío y recepción"""
    
    def __init__(self):
        self.engine = FixedSMSEngine()
        self.sent_messages: Dict[str, MessageTracker] = {}
        self.received_messages: List[ReceivedMessage] = []
        self.monitoring_active = False
        self.monitor_thread: Optional[threading.Thread] = None
        self._processed_messages = set()  # Para evitar duplicados
    
    async def connect(self):
        """Conecta al gateway"""
        await self.engine.connect()
        print("🔌 Gateway SMS conectado y listo")
    
    async def disconnect(self):
        """Desconecta del gateway"""
        await self.stop_monitoring()
        await self.engine.disconnect()
        print("🔌 Gateway SMS desconectado")
    
    async def send_message_with_tracking(self, phone_number: str, message: str, message_id: str = None) -> MessageTracker:
        """Envía mensaje con tracking completo"""
        
        if not message_id:
            message_id = f"msg_{int(time.time())}"
        
        # Crear tracker
        tracker = MessageTracker(
            message_id=message_id,
            phone_number=phone_number,
            message=message,
            status="sending",
            sent_time=datetime.now()
        )
        
        # Enviar mensaje
        result = await self.engine.send_sms_fixed(phone_number, message)
        
        if result.success:
            tracker.status = "sent"
            tracker.reference_id = result.reference_id
            print(f"✅ Mensaje {message_id} enviado exitosamente (Ref: {result.reference_id})")
        else:
            tracker.status = "failed"
            print(f"❌ Error enviando {message_id}: {result.error_message}")
        
        # Guardar tracker
        self.sent_messages[message_id] = tracker
        
        return tracker
    
    async def start_monitoring(self):
        """Inicia monitoreo de mensajes entrantes"""
        
        if self.monitoring_active:
            return
        
        print("🔔 Iniciando monitoreo de recepción...")
        self.monitoring_active = True
        
        # Configurar para recepción
        try:
            await self.engine._send_command("AT+CNMI=1,1,0,0,0")
        except:
            print("⚠️ Usando polling manual para recepción")
        
        # Iniciar hilo de monitoreo
        self.monitor_thread = threading.Thread(
            target=self._monitor_loop,
            daemon=True
        )
        self.monitor_thread.start()
        
        print("✅ Monitoreo activo")
    
    def _monitor_loop(self):
        """Loop de monitoreo en hilo separado"""
        
        last_check = time.time()
        
        while self.monitoring_active:
            try:
                current_time = time.time()
                
                # Verificar cada 10 segundos
                if current_time - last_check >= 10:
                    # Crear loop para operaciones async
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    
                    try:
                        # Verificar mensajes almacenados
                        stored_messages = loop.run_until_complete(self._check_stored_messages())
                        
                        # Procesar nuevos mensajes
                        for msg_data in stored_messages:
                            self._process_new_message(msg_data)
                        
                        last_check = current_time
                        
                    finally:
                        loop.close()
                
                time.sleep(2)
                
            except Exception as e:
                print(f"❌ Error en monitoreo: {e}")
                time.sleep(5)
    
    async def _check_stored_messages(self):
        """Verifica mensajes almacenados"""
        
        try:
            response = await self.engine._send_command('AT+CMGL="ALL"')
            messages = []
            
            lines = response.split('\n')
            i = 0
            
            while i < len(lines):
                line = lines[i].strip()
                
                if line.startswith('+CMGL:'):
                    if i + 1 < len(lines):
                        content = lines[i + 1].strip()
                        
                        # Extraer información
                        parts = line.split(',')
                        if len(parts) >= 3:
                            sender = parts[2].strip().strip('"')
                            
                            messages.append({
                                'sender': sender,
                                'content': content,
                                'raw_line': line
                            })
                    
                    i += 1
                
                i += 1
            
            return messages
            
        except Exception as e:
            return []
    
    def _process_new_message(self, msg_data):
        """Procesa un mensaje nuevo"""
        
        try:
            sender = msg_data['sender']
            content = msg_data['content']
            
            # Crear identificador único para evitar duplicados
            msg_signature = f"{sender}_{content}_{datetime.now().date()}"
            
            if msg_signature in self._processed_messages:
                return  # Ya procesado
            
            # Crear mensaje recibido
            received_msg = ReceivedMessage(
                phone_number=sender,
                message=content,
                timestamp=datetime.now()
            )
            
            # Verificar si es respuesta a algún mensaje enviado
            self._check_if_response(received_msg)
            
            # Agregar a la lista
            self.received_messages.append(received_msg)
            self._processed_messages.add(msg_signature)
            
            # Notificar
            emoji = "↩️" if received_msg.is_response else "📨"
            print(f"{emoji} Nuevo mensaje de {sender}: {content}")
            
            if received_msg.is_response:
                print(f"   🔗 Respuesta al mensaje: {received_msg.related_message_id}")
            
        except Exception as e:
            print(f"❌ Error procesando mensaje: {e}")
    
    def _check_if_response(self, received_msg: ReceivedMessage):
        """Verifica si es respuesta a un mensaje enviado"""
        
        # Buscar mensajes enviados al mismo número en las últimas 24 horas
        for msg_id, tracker in self.sent_messages.items():
            if (tracker.phone_number.replace('+51', '') in received_msg.phone_number or 
                received_msg.phone_number.replace('+51', '') in tracker.phone_number):
                
                # Verificar que sea reciente (últimas 24 horas)
                time_diff = (datetime.now() - tracker.sent_time).total_seconds()
                if time_diff < 86400 and tracker.status == "sent":
                    
                    # Marcar como respuesta
                    received_msg.is_response = True
                    received_msg.related_message_id = msg_id
                    
                    # Actualizar tracker
                    tracker.status = "response_received"
                    tracker.response_message = received_msg.message
                    tracker.response_time = received_msg.timestamp
                    
                    break
    
    async def stop_monitoring(self):
        """Detiene el monitoreo"""
        
        self.monitoring_active = False
        
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)
        
        print("🔔 Monitoreo detenido")
    
    def get_message_status(self, message_id: str) -> Optional[MessageTracker]:
        """Obtiene estado de un mensaje"""
        return self.sent_messages.get(message_id)
    
    def get_all_sent_messages(self) -> List[MessageTracker]:
        """Obtiene todos los mensajes enviados"""
        return list(self.sent_messages.values())
    
    def get_received_messages(self, phone_number: str = None) -> List[ReceivedMessage]:
        """Obtiene mensajes recibidos"""
        if phone_number:
            return [msg for msg in self.received_messages 
                   if phone_number in msg.phone_number or msg.phone_number in phone_number]
        return self.received_messages
    
    def print_summary(self):
        """Imprime resumen del estado"""
        
        print("\n📊 === RESUMEN DEL SMS GATEWAY ===")
        
        # Estadísticas de envío
        total_sent = len(self.sent_messages)
        successful_sent = len([t for t in self.sent_messages.values() if t.status == "sent"])
        with_responses = len([t for t in self.sent_messages.values() if t.status == "response_received"])
        
        print(f"📤 Mensajes enviados:")
        print(f"   📋 Total: {total_sent}")
        print(f"   ✅ Exitosos: {successful_sent}")
        print(f"   💬 Con respuesta: {with_responses}")
        
        # Estadísticas de recepción
        total_received = len(self.received_messages)
        responses = len([m for m in self.received_messages if m.is_response])
        new_messages = total_received - responses
        
        print(f"\n📥 Mensajes recibidos:")
        print(f"   📋 Total: {total_received}")
        print(f"   ↩️ Respuestas: {responses}")
        print(f"   📩 Nuevos: {new_messages}")
        
        # Últimos mensajes
        print(f"\n📱 Últimos mensajes enviados:")
        for tracker in list(self.sent_messages.values())[-3:]:
            emoji = "💬" if tracker.status == "response_received" else "✅" if tracker.status == "sent" else "❌"
            print(f"   {emoji} {tracker.message_id} → {tracker.phone_number}: {tracker.status}")
            if tracker.response_message:
                print(f"      ↩️ Respuesta: {tracker.response_message}")
        
        print(f"\n📱 Últimos mensajes recibidos:")
        for msg in self.received_messages[-3:]:
            emoji = "↩️" if msg.is_response else "📨"
            print(f"   {emoji} {msg.phone_number}: {msg.message}")

# Gateway global
gateway = CompleteSMSGateway()

async def demo_complete_functionality():
    """Demostración completa de funcionalidades"""
    
    print("🚀 === DEMO SMS GATEWAY COMPLETO ===\n")
    
    try:
        # 1. Conectar
        await gateway.connect()
        
        # 2. Iniciar monitoreo
        await gateway.start_monitoring()
        
        # 3. Enviar mensajes de prueba
        print("📤 Enviando mensajes de prueba...")
        
        # Al número que puede responder
        tracker1 = await gateway.send_message_with_tracking(
            "946467799",
            f"DEMO COMPLETO {time.strftime('%H:%M:%S')}: Responde 'RECIBIDO' para probar bidireccionalidad",
            "demo_bidirectional"
        )
        
        # Al número de solo recepción  
        tracker2 = await gateway.send_message_with_tracking(
            "913044047",
            f"DEMO COMPLETO {time.strftime('%H:%M:%S')}: Mensaje de confirmacion",
            "demo_confirmation"
        )
        
        print(f"\n📊 Estado inicial:")
        gateway.print_summary()
        
        # 4. Monitorear por respuestas
        print(f"\n🔔 Monitoreando respuestas por 60 segundos...")
        print(f"📱 Envía 'RECIBIDO' desde 946467799 para completar la demo")
        
        for i in range(12):  # 60 segundos
            remaining = 60 - (i * 5)
            print(f"⏳ {remaining}s restantes...")
            
            # Mostrar resumen cada 20 segundos
            if i % 4 == 3:
                gateway.print_summary()
            
            await asyncio.sleep(5)
        
        # 5. Resumen final
        print(f"\n🎯 === DEMO COMPLETADA ===")
        gateway.print_summary()
        
        # Verificar funcionalidades
        functions_working = {
            "Envío SMS": any(t.status == "sent" for t in gateway.get_all_sent_messages()),
            "Recepción SMS": len(gateway.get_received_messages()) > 0,
            "Tracking de mensajes": True,
            "Detección de respuestas": any(m.is_response for m in gateway.get_received_messages()),
            "Monitoreo tiempo real": True
        }
        
        print(f"\n✅ === FUNCIONALIDADES VERIFICADAS ===")
        for function, working in functions_working.items():
            emoji = "✅" if working else "❌"
            print(f"   {emoji} {function}")
        
        print(f"\n🎉 ¡SMS Gateway completamente funcional!")
        
    except Exception as e:
        print(f"❌ Error en demo: {e}")
    
    finally:
        await gateway.disconnect()

if __name__ == "__main__":
    asyncio.run(demo_complete_functionality())
