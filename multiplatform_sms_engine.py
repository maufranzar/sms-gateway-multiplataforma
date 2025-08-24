"""
Motor SMS Multiplataforma
Versión que funciona en Windows, Linux y macOS
"""
import asyncio
import time
import serial
import logging
from dataclasses import dataclass
from typing import Optional
from datetime import datetime
from system_config import config_manager, get_system_info

@dataclass
class SMSResult:
    success: bool
    reference_id: Optional[str] = None
    error_message: Optional[str] = None

class MultiplatformSMSEngine:
    """Motor SMS que funciona en cualquier sistema operativo"""
    
    def __init__(self):
        self.serial_connection = None
        self.is_connected = False
        self.logger = logging.getLogger(__name__)
        logging.basicConfig(level=logging.INFO)
        self.config = config_manager.config
    
    async def connect(self, custom_port: str = None) -> bool:
        """Conecta al gateway con detección automática de puerto"""
        
        try:
            # Determinar puerto a usar
            port_to_use = custom_port or config_manager.get_serial_port()
            
            if not port_to_use:
                # Intentar detección automática
                system_info = get_system_info()
                detected_port = system_info['detected_modem']
                
                if detected_port:
                    port_to_use = detected_port
                    self.logger.info(f"🎯 Puerto detectado automáticamente: {port_to_use}")
                else:
                    # Probar puertos comunes
                    common_ports = system_info['default_ports'][:5]  # Probar los primeros 5
                    
                    for test_port in common_ports:
                        try:
                            test_conn = serial.Serial(test_port, timeout=2)
                            test_conn.close()
                            port_to_use = test_port
                            self.logger.info(f"🔍 Puerto encontrado por prueba: {port_to_use}")
                            break
                        except:
                            continue
            
            if not port_to_use:
                raise Exception("No se pudo encontrar un puerto serie válido")
            
            self.logger.info(f"🔌 Conectando a {port_to_use} @ {self.config['baud_rate']} bps")
            
            # Conectar al puerto serie
            self.serial_connection = serial.Serial(
                port=port_to_use,
                baudrate=self.config['baud_rate'],
                bytesize=serial.EIGHTBITS,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE,
                timeout=10,
                xonxoff=False,
                rtscts=False,
                dsrdtr=False
            )
            
            # Limpiar buffers
            self.serial_connection.reset_input_buffer()
            self.serial_connection.reset_output_buffer()
            
            # Test de conectividad
            await self._send_command("AT")
            
            # Configurar para SMS
            await self._configure_for_sms()
            
            self.is_connected = True
            
            # Guardar puerto exitoso en configuración
            if not custom_port:
                config_manager.config['serial_port'] = port_to_use
                config_manager.save_config()
            
            self.logger.info("✅ Gateway conectado exitosamente")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Error conectando: {e}")
            if self.serial_connection:
                try:
                    self.serial_connection.close()
                except:
                    pass
                self.serial_connection = None
            return False
    
    async def _configure_for_sms(self):
        """Configuración específica para SMS"""
        
        self.logger.info("⚙️ Configurando para SMS...")
        
        # Obtener SMSC de la configuración
        smsc = self.config.get('smsc_number', '+51997990000')
        
        config_commands = [
            ("AT+CMGF=1", "Modo texto"),
            ('AT+CSCS="GSM"', "Codificación GSM"),
            (f'AT+CSCA="{smsc}"', "Centro de mensajes"),
            ("AT+CSMP=17,167,0,0", "Parámetros de mensaje"),
            ("AT+CPMS=\"ME\",\"ME\",\"ME\"", "Almacenamiento"),
            ("AT+CNMI=1,1,0,0,0", "Notificaciones"),
        ]
        
        for command, description in config_commands:
            try:
                await self._send_command(command)
                self.logger.info(f"✅ {description}: OK")
            except Exception as e:
                self.logger.warning(f"⚠️ {description}: {e}")
    
    async def _send_command(self, command: str, timeout: float = 5.0) -> str:
        """Envía comando AT multiplataforma"""
        
        if not self.serial_connection:
            raise Exception("No hay conexión serial")
        
        try:
            # Limpiar buffer
            self.serial_connection.reset_input_buffer()
            
            # Enviar comando
            full_command = command + '\r\n'
            self.serial_connection.write(full_command.encode('utf-8'))
            
            # Leer respuesta
            response = ""
            start_time = time.time()
            
            while time.time() - start_time < timeout:
                if self.serial_connection.in_waiting > 0:
                    chunk = self.serial_connection.read(self.serial_connection.in_waiting)
                    response += chunk.decode('utf-8', errors='ignore')
                    
                    if 'OK\r\n' in response or 'ERROR' in response:
                        break
                
                await asyncio.sleep(0.1)
            
            if 'ERROR' in response:
                raise Exception(f"Comando falló: {command}\n{response}")
            
            return response
            
        except Exception as e:
            self.logger.error(f"❌ Error comando {command}: {e}")
            raise
    
    async def send_sms(self, phone_number: str, message: str) -> SMSResult:
        """Envía SMS multiplataforma"""
        
        if not self.is_connected:
            return SMSResult(success=False, error_message="Gateway no conectado")
        
        try:
            self.logger.info(f"📤 Enviando SMS a {phone_number}: {message}")
            
            # Limpiar mensaje
            clean_message = self._clean_message(message)
            
            # Envío
            reference_id = await self._send_sms_improved(phone_number, clean_message)
            
            if reference_id:
                self.logger.info(f"✅ SMS enviado. Referencia: {reference_id}")
                return SMSResult(success=True, reference_id=reference_id)
            else:
                return SMSResult(success=False, error_message="Sin referencia")
                
        except Exception as e:
            error_msg = str(e)
            self.logger.error(f"❌ Error enviando SMS: {error_msg}")
            return SMSResult(success=False, error_message=error_msg)
    
    def _clean_message(self, message: str) -> str:
        """Limpia mensaje para compatibilidad multiplataforma"""
        
        # Mapear caracteres especiales
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
        """Envío SMS mejorado para multiplataforma"""
        
        # Limpiar buffers
        self.serial_connection.reset_input_buffer()
        self.serial_connection.reset_output_buffer()
        
        # Paso 1: Comando CMGS
        cmgs_command = f'AT+CMGS="{phone_number}"'
        self.serial_connection.write((cmgs_command + '\r').encode())
        
        # Paso 2: Esperar prompt
        prompt_timeout = 15
        start_time = time.time()
        response_buffer = ""
        
        while time.time() - start_time < prompt_timeout:
            if self.serial_connection.in_waiting > 0:
                chunk = self.serial_connection.read(self.serial_connection.in_waiting)
                chunk_str = chunk.decode('utf-8', errors='ignore')
                response_buffer += chunk_str
                
                if '>' in response_buffer:
                    break
                
                if 'ERROR' in response_buffer:
                    raise Exception(f"Error en CMGS: {response_buffer}")
            
            await asyncio.sleep(0.2)
        
        if '>' not in response_buffer:
            raise Exception(f"Sin prompt. Respuesta: {response_buffer}")
        
        # Paso 3: Enviar mensaje
        message_with_ctrl_z = message + '\x1A'
        self.serial_connection.write(message_with_ctrl_z.encode('utf-8', errors='ignore'))
        
        # Paso 4: Esperar confirmación
        confirmation_timeout = 30
        start_time = time.time()
        confirmation_buffer = ""
        
        while time.time() - start_time < confirmation_timeout:
            if self.serial_connection.in_waiting > 0:
                chunk = self.serial_connection.read(self.serial_connection.in_waiting)
                chunk_str = chunk.decode('utf-8', errors='ignore')
                confirmation_buffer += chunk_str
                
                if '+CMGS:' in confirmation_buffer:
                    import re
                    ref_match = re.search(r'\+CMGS:\s*(\d+)', confirmation_buffer)
                    return ref_match.group(1) if ref_match else "SUCCESS"
                
                if 'ERROR' in confirmation_buffer:
                    raise Exception(f"Error SMS: {confirmation_buffer}")
            
            await asyncio.sleep(0.2)
        
        raise Exception(f"Timeout confirmación: {confirmation_buffer}")
    
    async def check_stored_messages(self):
        """Verifica mensajes almacenados"""
        
        try:
            response = await self._send_command('AT+CMGL="ALL"')
            messages = []
            
            lines = response.split('\n')
            i = 0
            
            while i < len(lines):
                line = lines[i].strip()
                
                if line.startswith('+CMGL:'):
                    if i + 1 < len(lines):
                        content = lines[i + 1].strip()
                        
                        parts = line.split(',')
                        if len(parts) >= 3:
                            sender = parts[2].strip().strip('"')
                            
                            messages.append({
                                'sender': sender,
                                'content': content,
                                'raw': line
                            })
                    i += 1
                i += 1
            
            return messages
            
        except Exception as e:
            self.logger.error(f"Error verificando mensajes: {e}")
            return []
    
    async def get_network_info(self):
        """Información de red"""
        
        try:
            info = {}
            
            # Operador
            try:
                operator_response = await self._send_command("AT+COPS?")
                if '+COPS:' in operator_response:
                    parts = operator_response.split(',')
                    if len(parts) >= 3:
                        info['operator'] = parts[2].strip().strip('"')
            except:
                info['operator'] = 'Unknown'
            
            # Señal
            try:
                signal_response = await self._send_command("AT+CSQ")
                if '+CSQ:' in signal_response:
                    signal_part = signal_response.split('+CSQ:')[1].split(',')[0].strip()
                    info['signal_strength'] = signal_part
            except:
                info['signal_strength'] = 'Unknown'
            
            return info
            
        except Exception as e:
            return {'operator': 'Error', 'signal_strength': 'Error'}
    
    async def get_sim_info(self):
        """Obtiene información de la SIM card insertada"""
        if not self.is_connected:
            return None
        
        sim_info = {}
        
        try:
            # Obtener IMSI (International Mobile Subscriber Identity)
            try:
                imsi_response = await self._send_command("AT+CIMI")
                if imsi_response:
                    lines = imsi_response.strip().split('\n')
                    for line in lines:
                        if line.strip() and not line.startswith('AT+') and line.strip() != 'OK':
                            sim_info['imsi'] = line.strip()
                            break
            except:
                pass
            
            # Obtener ICCID (SIM Card Serial Number)
            try:
                iccid_response = await self._send_command("AT+CCID")
                if iccid_response:
                    lines = iccid_response.strip().split('\n')
                    for line in lines:
                        if line.strip() and not line.startswith('AT+') and line.strip() != 'OK':
                            sim_info['iccid'] = line.strip()
                            break
            except:
                # Algunos módems usan AT+QCCID
                try:
                    iccid_response = await self._send_command("AT+QCCID")
                    if iccid_response:
                        lines = iccid_response.strip().split('\n')
                        for line in lines:
                            if '+QCCID:' in line:
                                iccid = line.split(':')[1].strip()
                                sim_info['iccid'] = iccid
                                break
                except:
                    pass
            
            # Obtener número de teléfono de la SIM
            try:
                phone_response = await self._send_command("AT+CNUM")
                if phone_response:
                    lines = phone_response.strip().split('\n')
                    for line in lines:
                        if '+CNUM:' in line:
                            # Formato: +CNUM: "","numero",tipo
                            parts = line.split(',')
                            if len(parts) >= 2:
                                phone_number = parts[1].strip('"').strip()
                                if phone_number:
                                    sim_info['phone_number'] = phone_number
                            break
            except:
                pass
            
            # Obtener operador de red
            try:
                operator_response = await self._send_command("AT+COPS?")
                if operator_response:
                    lines = operator_response.strip().split('\n')
                    for line in lines:
                        if '+COPS:' in line:
                            # Formato: +COPS: mode,format,"operator"
                            parts = line.split(',')
                            if len(parts) >= 3:
                                operator = parts[2].strip('"').strip()
                                if operator:
                                    sim_info['operator'] = operator
                            break
            except:
                pass
            
            # Obtener SMSC automáticamente
            try:
                smsc_response = await self._send_command("AT+CSCA?")
                if smsc_response:
                    lines = smsc_response.strip().split('\n')
                    for line in lines:
                        if '+CSCA:' in line:
                            # Formato: +CSCA: "numero",tipo
                            parts = line.split(',')
                            if len(parts) >= 1:
                                smsc = parts[0].split(':')[1].strip().strip('"')
                                if smsc:
                                    sim_info['smsc'] = smsc
                            break
            except:
                pass
            
            if sim_info:
                print(f"📱 Información de SIM detectada:")
                for key, value in sim_info.items():
                    print(f"   {key.upper()}: {value}")
            
            return sim_info
            
        except Exception as e:
            print(f"⚠️ Error obteniendo info de SIM: {e}")
            return None

    async def detect_and_save_sim_info(self):
        """Detecta información de SIM y la guarda en configuración"""
        sim_info = await self.get_sim_info()
        
        if sim_info:
            # Actualizar configuración con info de SIM
            try:
                from system_config import config_manager
                
                if 'imsi' in sim_info:
                    config_manager.config['sim_info']['imsi'] = sim_info['imsi']
                if 'iccid' in sim_info:
                    config_manager.config['sim_info']['iccid'] = sim_info['iccid']
                if 'phone_number' in sim_info:
                    config_manager.config['gateway_number'] = sim_info['phone_number']
                if 'operator' in sim_info:
                    config_manager.config['operator'] = sim_info['operator']
                if 'smsc' in sim_info:
                    config_manager.config['smsc_number'] = sim_info['smsc']
                
                config_manager.config['sim_info']['last_updated'] = datetime.now().isoformat()
                config_manager.save_config()
                
                print(f"✅ Configuración actualizada con información de SIM")
                return True
            except Exception as e:
                print(f"⚠️ Error guardando configuración: {e}")
        
        return False

    async def disconnect(self):
        """Desconecta del gateway"""
        
        if self.serial_connection:
            try:
                self.serial_connection.close()
                self.logger.info("🔌 Gateway desconectado")
            except:
                pass
        
        self.is_connected = False

# Test multiplataforma
async def test_multiplatform():
    """Test del motor multiplataforma"""
    
    print("🌐 === TEST MOTOR SMS MULTIPLATAFORMA ===\n")
    
    # Mostrar información del sistema
    system_info = get_system_info()
    print(f"💻 Sistema: {system_info['os'].upper()}")
    print(f"📱 Módem detectado: {system_info['detected_modem'] or 'Buscando...'}")
    
    print(f"\n📍 Puertos disponibles:")
    for port in system_info['available_ports']:
        emoji = "🎯" if port['is_huawei'] else "📞" if port['is_modem'] else "🔌"
        print(f"   {emoji} {port['device']}: {port['description']}")
    
    # Probar conexión
    engine = MultiplatformSMSEngine()
    
    print(f"\n🔗 Intentando conexión...")
    connected = await engine.connect()
    
    if connected:
        print(f"✅ Conectado exitosamente")
        
        # Información de red
        network_info = await engine.get_network_info()
        print(f"📡 Operador: {network_info.get('operator', 'N/A')}")
        print(f"📶 Señal: {network_info.get('signal_strength', 'N/A')}")
        
        # Test de envío
        print(f"\n📤 Test de envío...")
        result = await engine.send_sms("946467799", f"Test multiplataforma {time.strftime('%H:%M:%S')}")
        
        if result.success:
            print(f"✅ SMS enviado (Ref: {result.reference_id})")
        else:
            print(f"❌ Error: {result.error_message}")
        
        await engine.disconnect()
    else:
        print(f"❌ No se pudo conectar")

if __name__ == "__main__":
    asyncio.run(test_multiplatform())
