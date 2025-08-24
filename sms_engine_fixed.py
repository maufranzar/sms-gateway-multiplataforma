"""
Motor SMS Corregido - Solucionando problemas de envío
Versión optimizada para el Huawei E8278
"""
import asyncio
import time
import serial
import logging
from dataclasses import dataclass
from typing import Optional

@dataclass
class SMSResult:
    success: bool
    reference_id: Optional[str] = None
    error_message: Optional[str] = None

class FixedSMSEngine:
    """Motor SMS con configuración optimizada para envío"""
    
    def __init__(self):
        self.serial_connection = None
        self.is_connected = False
        self.logger = logging.getLogger(__name__)
        logging.basicConfig(level=logging.INFO)
    
    async def connect(self):
        """Conecta al gateway con configuración optimizada"""
        
        try:
            self.logger.info("🔌 Conectando con configuración optimizada...")
            
            # Conectar al puerto serie
            self.serial_connection = serial.Serial(
                port='/dev/ttyUSB0',
                baudrate=9600,
                bytesize=serial.EIGHTBITS,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE,
                timeout=10,  # Timeout más largo
                xonxoff=False,
                rtscts=False,
                dsrdtr=False
            )
            
            # Limpiar buffer
            self.serial_connection.reset_input_buffer()
            self.serial_connection.reset_output_buffer()
            
            # Test de conectividad
            await self._send_command("AT")
            
            # Configuración optimizada paso a paso
            await self._configure_for_sms()
            
            self.is_connected = True
            self.logger.info("✅ Gateway conectado y configurado")
            
        except Exception as e:
            self.logger.error(f"❌ Error conectando: {e}")
            if self.serial_connection:
                self.serial_connection.close()
            raise
    
    async def _configure_for_sms(self):
        """Configuración específica para SMS"""
        
        self.logger.info("⚙️ Configurando para SMS...")
        
        # Configuraciones en orden específico
        config_commands = [
            ("AT+CMGF=1", "Modo texto"),
            ('AT+CSCS="GSM"', "Codificación GSM"),
            ('AT+CSCA="+51997990000"', "Centro de mensajes Claro"),
            ("AT+CSMP=17,167,0,0", "Parámetros de mensaje"),
            ("AT+CPMS=\"ME\",\"ME\",\"ME\"", "Almacenamiento en memoria"),
            ("AT+CNMI=1,1,0,0,0", "Notificaciones básicas"),
        ]
        
        for command, description in config_commands:
            try:
                response = await self._send_command(command)
                self.logger.info(f"✅ {description}: OK")
            except Exception as e:
                self.logger.warning(f"⚠️ {description}: {e}")
                # Continuar con las demás configuraciones
    
    async def _send_command(self, command: str, timeout: float = 5.0) -> str:
        """Envía comando AT con timeout configurable"""
        
        if not self.serial_connection:
            raise Exception("No hay conexión serial")
        
        try:
            # Limpiar buffer de entrada
            self.serial_connection.reset_input_buffer()
            
            # Enviar comando
            full_command = command + '\r\n'
            self.serial_connection.write(full_command.encode('utf-8'))
            
            # Leer respuesta con timeout
            response = ""
            start_time = time.time()
            
            while time.time() - start_time < timeout:
                if self.serial_connection.in_waiting > 0:
                    chunk = self.serial_connection.read(self.serial_connection.in_waiting)
                    response += chunk.decode('utf-8', errors='ignore')
                    
                    # Verificar si la respuesta está completa
                    if 'OK\r\n' in response or 'ERROR' in response or '+CMS ERROR:' in response or '+CME ERROR:' in response:
                        break
                
                await asyncio.sleep(0.1)
            
            # Verificar errores
            if 'ERROR' in response:
                raise Exception(f"Comando falló: {command}\n{response}")
            
            if 'OK' not in response and command != "AT":
                raise Exception(f"Respuesta incompleta: {command}\n{response}")
            
            return response
            
        except Exception as e:
            self.logger.error(f"❌ Error comando {command}: {e}")
            raise
    
    async def send_sms_fixed(self, phone_number: str, message: str) -> SMSResult:
        """Método de envío SMS corregido"""
        
        if not self.is_connected:
            return SMSResult(success=False, error_message="Gateway no conectado")
        
        try:
            self.logger.info(f"📤 Enviando SMS a {phone_number}: {message}")
            
            # Limpiar caracteres problemáticos
            clean_message = self._clean_message(message)
            
            # Método de envío mejorado
            reference_id = await self._send_sms_improved(phone_number, clean_message)
            
            if reference_id:
                self.logger.info(f"✅ SMS enviado exitosamente. Referencia: {reference_id}")
                return SMSResult(success=True, reference_id=reference_id)
            else:
                return SMSResult(success=False, error_message="No se obtuvo referencia")
                
        except Exception as e:
            error_msg = str(e)
            self.logger.error(f"❌ Error enviando SMS: {error_msg}")
            return SMSResult(success=False, error_message=error_msg)
    
    def _clean_message(self, message: str) -> str:
        """Limpia el mensaje para evitar problemas de codificación"""
        
        # Remover caracteres problemáticos
        import unicodedata
        
        # Normalizar unicode
        normalized = unicodedata.normalize('NFKD', message)
        
        # Convertir a ASCII ignorando caracteres especiales
        ascii_message = normalized.encode('ascii', 'ignore').decode('ascii')
        
        # Mapear caracteres especiales comunes
        replacements = {
            'ñ': 'n', 'Ñ': 'N',
            'á': 'a', 'é': 'e', 'í': 'i', 'ó': 'o', 'ú': 'u',
            'Á': 'A', 'É': 'E', 'Í': 'I', 'Ó': 'O', 'Ú': 'U',
            '🧪': 'TEST', '📱': '', '💬': '', '✅': 'OK', '❌': 'ERROR'
        }
        
        clean_message = message
        for original, replacement in replacements.items():
            clean_message = clean_message.replace(original, replacement)
        
        # Limitar longitud
        if len(clean_message) > 160:
            clean_message = clean_message[:157] + "..."
        
        return clean_message
    
    async def _send_sms_improved(self, phone_number: str, message: str) -> Optional[str]:
        """Método mejorado de envío SMS"""
        
        # Limpiar buffers
        self.serial_connection.reset_input_buffer()
        self.serial_connection.reset_output_buffer()
        
        # Paso 1: Enviar comando CMGS
        cmgs_command = f'AT+CMGS="{phone_number}"'
        self.serial_connection.write((cmgs_command + '\r').encode())
        
        # Paso 2: Esperar prompt '>' con timeout más largo
        prompt_received = False
        prompt_timeout = 15  # 15 segundos para el prompt
        start_time = time.time()
        response_buffer = ""
        
        while time.time() - start_time < prompt_timeout:
            if self.serial_connection.in_waiting > 0:
                chunk = self.serial_connection.read(self.serial_connection.in_waiting)
                chunk_str = chunk.decode('utf-8', errors='ignore')
                response_buffer += chunk_str
                
                self.logger.info(f"📥 Respuesta parcial: {repr(chunk_str)}")
                
                if '>' in response_buffer:
                    prompt_received = True
                    self.logger.info("✅ Prompt '>' recibido")
                    break
                
                if 'ERROR' in response_buffer:
                    raise Exception(f"Error en comando CMGS: {response_buffer}")
            
            await asyncio.sleep(0.2)
        
        if not prompt_received:
            raise Exception(f"No se recibió prompt '>'. Respuesta: {response_buffer}")
        
        # Paso 3: Enviar mensaje con Ctrl+Z
        message_with_ctrl_z = message + '\x1A'  # Ctrl+Z
        self.serial_connection.write(message_with_ctrl_z.encode('utf-8', errors='ignore'))
        
        # Paso 4: Esperar confirmación
        confirmation_timeout = 30  # 30 segundos para confirmación
        start_time = time.time()
        confirmation_buffer = ""
        
        while time.time() - start_time < confirmation_timeout:
            if self.serial_connection.in_waiting > 0:
                chunk = self.serial_connection.read(self.serial_connection.in_waiting)
                chunk_str = chunk.decode('utf-8', errors='ignore')
                confirmation_buffer += chunk_str
                
                self.logger.info(f"📥 Confirmación: {repr(chunk_str)}")
                
                # Buscar confirmación exitosa
                if '+CMGS:' in confirmation_buffer:
                    # Extraer referencia
                    import re
                    ref_match = re.search(r'\+CMGS:\s*(\d+)', confirmation_buffer)
                    if ref_match:
                        return ref_match.group(1)
                    else:
                        return "SUCCESS"
                
                # Verificar errores
                if '+CMS ERROR:' in confirmation_buffer or '+CME ERROR:' in confirmation_buffer:
                    raise Exception(f"Error SMS: {confirmation_buffer}")
            
            await asyncio.sleep(0.2)
        
        raise Exception(f"Timeout esperando confirmación. Buffer: {confirmation_buffer}")
    
    async def get_network_info(self):
        """Obtiene información de red"""
        
        try:
            info = {}
            
            # Operador
            operator_response = await self._send_command("AT+COPS?")
            if '+COPS:' in operator_response:
                parts = operator_response.split(',')
                if len(parts) >= 3:
                    info['operator'] = parts[2].strip().strip('"')
            
            # Señal
            signal_response = await self._send_command("AT+CSQ")
            if '+CSQ:' in signal_response:
                signal_part = signal_response.split('+CSQ:')[1].split(',')[0].strip()
                info['signal_strength'] = signal_part
            
            return info
            
        except Exception as e:
            self.logger.error(f"Error obteniendo info de red: {e}")
            return {}
    
    async def disconnect(self):
        """Desconecta del gateway"""
        
        if self.serial_connection:
            try:
                self.serial_connection.close()
                self.logger.info("🔌 Gateway desconectado")
            except:
                pass
        
        self.is_connected = False

# Test del motor corregido
async def test_fixed_engine():
    """Test del motor SMS corregido"""
    
    print("🔧 === TEST MOTOR SMS CORREGIDO ===\n")
    
    engine = FixedSMSEngine()
    
    try:
        # Conectar
        await engine.connect()
        
        # Mostrar info de red
        network_info = await engine.get_network_info()
        print(f"📡 Red: {network_info.get('operator', 'N/A')}")
        print(f"📶 Señal: {network_info.get('signal_strength', 'N/A')}")
        print()
        
        # Test 1: Envío a número que puede responder
        print("📤 Test 1: Enviando a 946467799...")
        result1 = await engine.send_sms_fixed(
            "946467799", 
            f"TEST CORREGIDO {time.strftime('%H:%M:%S')} - Responde para confirmar"
        )
        
        if result1.success:
            print(f"✅ Éxito! Ref: {result1.reference_id}")
        else:
            print(f"❌ Error: {result1.error_message}")
        
        # Test 2: Envío a número de solo recepción
        print(f"\n📤 Test 2: Enviando a 913044047...")
        result2 = await engine.send_sms_fixed(
            "913044047",
            f"RECEPCION TEST {time.strftime('%H:%M:%S')}"
        )
        
        if result2.success:
            print(f"✅ Éxito! Ref: {result2.reference_id}")
        else:
            print(f"❌ Error: {result2.error_message}")
        
        # Resumen
        print(f"\n📊 === RESUMEN ===")
        print(f"✅ Envío a 946467799: {'OK' if result1.success else 'FALLO'}")
        print(f"✅ Envío a 913044047: {'OK' if result2.success else 'FALLO'}")
        
        if result1.success or result2.success:
            print(f"\n🎉 ¡PROBLEMA DE ENVÍO SOLUCIONADO!")
            print(f"💡 Ahora puedes usar este motor para envíos confiables")
        else:
            print(f"\n⚠️ Aún hay problemas de envío que requieren más diagnóstico")
    
    except Exception as e:
        print(f"❌ Error en test: {e}")
    
    finally:
        await engine.disconnect()

if __name__ == "__main__":
    asyncio.run(test_fixed_engine())
