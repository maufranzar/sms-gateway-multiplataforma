"""
Core SMS Engine - Versión simplificada y funcional
"""
import serial
import time
import asyncio
import logging
from typing import Optional, Dict, Any
from datetime import datetime
from dataclasses import dataclass
import re

from config import settings

# Configurar logging
logging.basicConfig(level=getattr(logging, settings.LOG_LEVEL))
logger = logging.getLogger(__name__)

@dataclass
class SMSResponse:
    success: bool
    reference_id: Optional[str] = None
    error_message: Optional[str] = None
    details: Optional[str] = None

class ATCommandError(Exception):
    """Excepción para errores de comandos AT"""
    pass

class SMSEngine:
    """Motor principal para gestión de SMS usando comandos AT"""
    
    def __init__(self):
        self.serial_connection: Optional[serial.Serial] = None
        self.is_connected = False
        
    async def connect(self) -> bool:
        """Establece conexión con el gateway SMS"""
        try:
            logger.info(f"Intentando conectar a {settings.SERIAL_PORT} a {settings.SERIAL_BAUDRATE} bps")
            
            self.serial_connection = serial.Serial(
                port=settings.SERIAL_PORT,
                baudrate=settings.SERIAL_BAUDRATE,
                timeout=settings.SERIAL_TIMEOUT
            )
            
            # Esperar estabilización
            await asyncio.sleep(2)
            
            # Verificar comunicación básica
            if await self._test_communication():
                self.is_connected = True
                await self._initialize_modem()
                logger.info("✅ Conexión establecida con el gateway SMS")
                return True
            else:
                raise ATCommandError("No se pudo establecer comunicación AT")
                
        except Exception as e:
            logger.error(f"❌ Error conectando al gateway: {e}")
            self.is_connected = False
            if self.serial_connection and self.serial_connection.is_open:
                self.serial_connection.close()
                self.serial_connection = None
            return False
    
    async def disconnect(self):
        """Cierra la conexión con el gateway"""
        if self.serial_connection and self.serial_connection.is_open:
            self.serial_connection.close()
        
        self.is_connected = False
        self.serial_connection = None
        logger.info("🔌 Conexión cerrada")
    
    async def _test_communication(self) -> bool:
        """Prueba la comunicación básica con AT"""
        try:
            response = await self._send_command("AT")
            return response is not None and "OK" in response
        except Exception as e:
            logger.error(f"Error en test de comunicación: {e}")
            return False
    
    async def _initialize_modem(self):
        """Inicializa el módem con configuraciones básicas"""
        init_commands = [
            "AT+CMGF=1",  # Modo texto para SMS
            "AT+CNMI=1,1,0,0,0",  # Configurar notificaciones simples
        ]
        
        for cmd in init_commands:
            try:
                await self._send_command(cmd)
                logger.debug(f"Comando inicialización OK: {cmd}")
            except Exception as e:
                logger.warning(f"Error en comando {cmd}: {e}")
    
    async def _send_command(self, command: str, wait_time: float = 2.0) -> Optional[str]:
        """Envía un comando AT y espera respuesta"""
        if not self.serial_connection or not self.serial_connection.is_open:
            raise ATCommandError("No hay conexión serial")
        
        try:
            # Limpiar buffer de entrada
            self.serial_connection.reset_input_buffer()
            
            # Enviar comando
            full_command = f"{command}\r\n"
            self.serial_connection.write(full_command.encode())
            logger.debug(f"📤 Enviado: {command}")
            
            # Esperar respuesta
            await asyncio.sleep(wait_time)
            
            response = ""
            max_attempts = 10
            attempts = 0
            
            while attempts < max_attempts:
                if self.serial_connection.in_waiting > 0:
                    data = self.serial_connection.read(self.serial_connection.in_waiting)
                    response += data.decode('utf-8', errors='ignore')
                    
                    # Si tenemos OK o ERROR, terminamos
                    if "OK" in response or "ERROR" in response:
                        break
                        
                await asyncio.sleep(0.1)
                attempts += 1
            
            logger.debug(f"📥 Respuesta: {response.strip()}")
            
            if "ERROR" in response:
                raise ATCommandError(f"Comando falló: {response.strip()}")
            
            return response.strip()
                    
        except Exception as e:
            logger.error(f"❌ Error enviando comando {command}: {e}")
            raise ATCommandError(f"Error en comando: {e}")
    
    async def send_sms(self, phone_number: str, message: str) -> SMSResponse:
        """Envía un SMS usando comandos AT"""
        if not self.is_connected:
            return SMSResponse(
                success=False, 
                error_message="Gateway no conectado"
            )
        
        try:
            # Limpiar mensaje de caracteres problemáticos
            clean_message = message.encode('ascii', errors='ignore').decode('ascii')
            if len(clean_message) > 160:
                clean_message = clean_message[:160]
            
            logger.info(f"📤 Enviando SMS a {phone_number}: {clean_message}")
            
            # Iniciar envío de SMS
            response = await self._send_command(f'AT+CMGS="{phone_number}"', wait_time=1.0)
            
            if not response or ">" not in response:
                raise ATCommandError("No se recibió prompt para mensaje")
            
            # Enviar mensaje + Ctrl+Z
            if self.serial_connection:
                self.serial_connection.write(clean_message.encode('ascii'))
                self.serial_connection.write(bytes([26]))  # Ctrl+Z
                
                # Esperar confirmación de envío
                await asyncio.sleep(5.0)
                
                send_response = ""
                max_attempts = 20
                attempts = 0
                
                while attempts < max_attempts:
                    if self.serial_connection.in_waiting > 0:
                        data = self.serial_connection.read(self.serial_connection.in_waiting)
                        send_response += data.decode('utf-8', errors='ignore')
                        
                        # Si tenemos respuesta completa, terminamos
                        if "OK" in send_response or "ERROR" in send_response or "+CMS ERROR" in send_response:
                            break
                            
                    await asyncio.sleep(0.2)
                    attempts += 1
            
            # Extraer reference ID
            reference_id = None
            if send_response:
                reference_match = re.search(r'\+CMGS:\s*(\d+)', send_response)
                reference_id = reference_match.group(1) if reference_match else None
            
            if "OK" in send_response and reference_id:
                logger.info(f"✅ SMS enviado exitosamente. Referencia: {reference_id}")
                return SMSResponse(
                    success=True,
                    reference_id=reference_id,
                    details=send_response.strip()
                )
            elif "+CMS ERROR" in send_response or "ERROR" in send_response:
                error_match = re.search(r'\+CMS ERROR:\s*(\d+)', send_response)
                error_code = error_match.group(1) if error_match else "desconocido"
                raise ATCommandError(f"Error CMS {error_code}: {send_response.strip()}")
            else:
                raise ATCommandError(f"Envío falló - respuesta inesperada: {send_response}")
                
        except Exception as e:
            logger.error(f"❌ Error enviando SMS: {e}")
            return SMSResponse(
                success=False,
                error_message=str(e)
            )
    
    async def get_signal_strength(self) -> Optional[int]:
        """Obtiene la fuerza de señal"""
        try:
            response = await self._send_command("AT+CSQ")
            if response:
                # Formato: +CSQ: 31,99
                match = re.search(r'\+CSQ:\s*(\d+),\d+', response)
                if match:
                    signal = int(match.group(1))
                    return signal if signal != 99 else None
            return None
        except Exception as e:
            logger.error(f"Error obteniendo señal: {e}")
            return None
    
    async def get_network_info(self) -> Dict[str, Any]:
        """Obtiene información de la red"""
        try:
            info = {}
            
            # Registro de red
            try:
                creg_response = await self._send_command("AT+CREG?")
                if creg_response:
                    creg_match = re.search(r'\+CREG:\s*\d+,(\d+)(?:,"([^"]+)","([^"]+)")?', creg_response)
                    if creg_match:
                        info['network_status'] = creg_match.group(1)
                        info['lac'] = creg_match.group(2) if creg_match.group(2) else "N/A"
                        info['cell_id'] = creg_match.group(3) if creg_match.group(3) else "N/A"
            except:
                info['network_status'] = "Error"
            
            # Operador
            try:
                cops_response = await self._send_command("AT+COPS?")
                if cops_response:
                    cops_match = re.search(r'\+COPS:\s*\d+,\d+,"([^"]+)"', cops_response)
                    if cops_match:
                        info['operator'] = cops_match.group(1)
                    else:
                        info['operator'] = "Desconocido"
                else:
                    info['operator'] = "Error"
            except:
                info['operator'] = "Error"
            
            # Fuerza de señal
            info['signal_strength'] = await self.get_signal_strength()
            
            # SMSC
            try:
                smsc_response = await self._send_command("AT+CSCA?")
                if smsc_response:
                    smsc_match = re.search(r'\+CSCA:\s*"([^"]+)"', smsc_response)
                    info['smsc'] = smsc_match.group(1) if smsc_match else "N/A"
                else:
                    info['smsc'] = "Error"
            except:
                info['smsc'] = "Error"
            
            return info
            
        except Exception as e:
            logger.error(f"Error obteniendo info de red: {e}")
            return {"error": str(e)}

# Instancia global del motor SMS
sms_engine = SMSEngine()
