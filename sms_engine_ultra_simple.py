"""
Motor SMS ultra-simple sin dependencias externas
"""
import serial
import time
import asyncio
import logging
import re
from dataclasses import dataclass
from typing import Optional, Dict, Any

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class SMSResponse:
    success: bool
    reference_id: Optional[str] = None
    error_message: Optional[str] = None
    details: Optional[str] = None

class SMSEngine:
    """Motor SMS ultra-simple"""
    
    def __init__(self):
        self.serial_connection: Optional[serial.Serial] = None
        self.is_connected = False
        self.port = "/dev/ttyUSB0"
        self.baudrate = 9600
        self.timeout = 10
        
    async def connect(self) -> bool:
        """Conecta al gateway SMS"""
        try:
            logger.info(f"🔌 Conectando a {self.port} @ {self.baudrate} bps")
            
            # Cerrar conexión existente si la hay
            if self.serial_connection and self.serial_connection.is_open:
                self.serial_connection.close()
            
            self.serial_connection = serial.Serial(
                port=self.port,
                baudrate=self.baudrate,
                timeout=self.timeout
            )
            
            # Esperar estabilización
            await asyncio.sleep(2)
            
            # Probar comunicación
            if await self._test_at():
                self.is_connected = True
                await self._init_modem()
                logger.info("✅ Gateway conectado exitosamente")
                return True
            else:
                raise Exception("No se pudo establecer comunicación AT")
                
        except Exception as e:
            logger.error(f"❌ Error conectando: {e}")
            self.is_connected = False
            if self.serial_connection and self.serial_connection.is_open:
                self.serial_connection.close()
                self.serial_connection = None
            return False
    
    async def disconnect(self):
        """Desconecta del gateway"""
        if self.serial_connection and self.serial_connection.is_open:
            self.serial_connection.close()
        self.is_connected = False
        self.serial_connection = None
        logger.info("🔌 Gateway desconectado")
    
    async def _test_at(self) -> bool:
        """Prueba comando AT básico"""
        try:
            response = await self._send_command("AT", 2)
            return "OK" in response
        except:
            return False
    
    async def _init_modem(self):
        """Inicializa el módem"""
        try:
            await self._send_command("AT+CMGF=1")  # Modo texto
            logger.debug("📟 Módem inicializado")
        except Exception as e:
            logger.warning(f"⚠️ Error inicializando módem: {e}")
    
    async def _send_command(self, command: str, wait_time: float = 2) -> str:
        """Envía comando AT y espera respuesta"""
        if not self.serial_connection or not self.serial_connection.is_open:
            raise Exception("No hay conexión serial")
        
        try:
            # Limpiar buffer
            self.serial_connection.reset_input_buffer()
            
            # Enviar comando
            cmd = f"{command}\r\n"
            self.serial_connection.write(cmd.encode())
            logger.debug(f"📤 {command}")
            
            # Esperar respuesta
            await asyncio.sleep(wait_time)
            
            response = ""
            attempts = 0
            max_attempts = 20
            
            while attempts < max_attempts:
                if self.serial_connection.in_waiting > 0:
                    data = self.serial_connection.read(self.serial_connection.in_waiting)
                    response += data.decode('utf-8', errors='ignore')
                    
                    if "OK" in response or "ERROR" in response or "+CMS ERROR" in response:
                        break
                        
                await asyncio.sleep(0.1)
                attempts += 1
            
            logger.debug(f"📥 {response.strip()}")
            
            if "ERROR" in response or "+CMS ERROR" in response:
                raise Exception(f"Comando falló: {response.strip()}")
            
            return response.strip()
            
        except Exception as e:
            logger.error(f"❌ Error comando {command}: {e}")
            raise
    
    async def send_sms(self, phone_number: str, message: str) -> SMSResponse:
        """Envía SMS"""
        if not self.is_connected:
            return SMSResponse(False, error_message="Gateway no conectado")
        
        try:
            # Limpiar mensaje
            clean_msg = message.encode('ascii', errors='ignore').decode('ascii')
            if len(clean_msg) > 160:
                clean_msg = clean_msg[:160]
            
            logger.info(f"📤 Enviando SMS a {phone_number}: {clean_msg}")
            
            # Comando para iniciar SMS
            response = await self._send_command(f'AT+CMGS="{phone_number}"', 1)
            
            if ">" not in response:
                raise Exception("No se recibió prompt (>) para el mensaje")
            
            # Enviar mensaje + Ctrl+Z
            self.serial_connection.write(clean_msg.encode('ascii'))
            self.serial_connection.write(bytes([26]))  # Ctrl+Z
            
            # Esperar confirmación
            await asyncio.sleep(5)
            
            send_response = ""
            attempts = 0
            max_attempts = 30
            
            while attempts < max_attempts:
                if self.serial_connection.in_waiting > 0:
                    data = self.serial_connection.read(self.serial_connection.in_waiting)
                    send_response += data.decode('utf-8', errors='ignore')
                    
                    if "OK" in send_response or "ERROR" in send_response or "+CMS ERROR" in send_response:
                        break
                        
                await asyncio.sleep(0.2)
                attempts += 1
            
            # Extraer referencia
            reference_id = None
            ref_match = re.search(r'\+CMGS:\s*(\d+)', send_response)
            if ref_match:
                reference_id = ref_match.group(1)
            
            if "OK" in send_response and reference_id:
                logger.info(f"✅ SMS enviado. Referencia: {reference_id}")
                return SMSResponse(True, reference_id=reference_id, details=send_response.strip())
            elif "+CMS ERROR" in send_response:
                error_match = re.search(r'\+CMS ERROR:\s*(\d+)', send_response)
                error_code = error_match.group(1) if error_match else "desconocido"
                error_msg = f"Error CMS {error_code}"
                logger.error(f"❌ {error_msg}")
                return SMSResponse(False, error_message=error_msg)
            else:
                error_msg = f"Respuesta inesperada: {send_response}"
                logger.error(f"❌ {error_msg}")
                return SMSResponse(False, error_message=error_msg)
                
        except Exception as e:
            logger.error(f"❌ Error enviando SMS: {e}")
            return SMSResponse(False, error_message=str(e))
    
    async def get_signal_strength(self) -> Optional[int]:
        """Obtiene fuerza de señal"""
        try:
            response = await self._send_command("AT+CSQ")
            match = re.search(r'\+CSQ:\s*(\d+),\d+', response)
            if match:
                signal = int(match.group(1))
                return signal if signal != 99 else None
        except:
            pass
        return None
    
    async def get_network_info(self) -> Dict[str, Any]:
        """Obtiene información de red"""
        info = {}
        
        try:
            # Red registration
            response = await self._send_command("AT+CREG?")
            match = re.search(r'\+CREG:\s*\d+,(\d+)(?:,"([^"]+)","([^"]+)")?', response)
            if match:
                info['network_status'] = match.group(1)
                info['lac'] = match.group(2) if match.group(2) else "N/A"
                info['cell_id'] = match.group(3) if match.group(3) else "N/A"
        except:
            info['network_status'] = "Error"
        
        try:
            # Operador
            response = await self._send_command("AT+COPS?")
            match = re.search(r'\+COPS:\s*\d+,\d+,"([^"]+)"', response)
            if match:
                info['operator'] = match.group(1)
            else:
                info['operator'] = "Desconocido"
        except:
            info['operator'] = "Error"
        
        try:
            # SMSC
            response = await self._send_command("AT+CSCA?")
            match = re.search(r'\+CSCA:\s*"([^"]+)"', response)
            if match:
                info['smsc'] = match.group(1)
            else:
                info['smsc'] = "N/A"
        except:
            info['smsc'] = "Error"
        
        # Señal
        info['signal_strength'] = await self.get_signal_strength()
        
        return info

# Instancia global
sms_engine = SMSEngine()
