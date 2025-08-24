"""
Configuración Multiplataforma del SMS Gateway
Detecta automáticamente puertos serie y permite configuració        # Configuración por defecto
        self.config = {
            'serial_port': '',
            'baud_rate': 9600,
            'timeout': 10,
            'smsc_number': '',  # Se detectará automáticamente de la SIM
            'gateway_number': '',  # Número de la SIM actual (se detectará)
            'operator': '',  # Operador de la SIM (se detectará)
            'web_server': {
                'host': 'localhost',
                'port': 8080
            },
            'sim_info': {
                'iccid': '',  # ID único de la SIM
                'imsi': '',   # Identificador del suscriptor
                'last_updated': ''
            }
        } os
import platform
import serial.tools.list_ports
from typing import List, Dict, Optional
import json

class SystemConfig:
    """Configuración del sistema para diferentes OS"""
    
    @staticmethod
    def detect_os() -> str:
        """Detecta el sistema operativo"""
        return platform.system().lower()
    
    @staticmethod
    def get_default_ports() -> List[str]:
        """Obtiene puertos serie por defecto según el OS"""
        
        os_type = SystemConfig.detect_os()
        
        if os_type == "windows":
            # Windows: COM1, COM2, etc.
            return [f"COM{i}" for i in range(1, 20)]
        elif os_type == "linux":
            # Linux: /dev/ttyUSB0, /dev/ttyACM0, etc.
            return [f"/dev/ttyUSB{i}" for i in range(0, 10)] + \
                   [f"/dev/ttyACM{i}" for i in range(0, 10)]
        elif os_type == "darwin":  # macOS
            # macOS: /dev/tty.usbserial-*, /dev/tty.usbmodem*
            return [f"/dev/tty.usbserial-{i}" for i in range(0, 10)] + \
                   [f"/dev/tty.usbmodem{i}" for i in range(0, 10)]
        else:
            return []
    
    @staticmethod
    def scan_available_ports() -> List[Dict]:
        """Escanea puertos serie disponibles"""
        
        ports = []
        
        try:
            # Usar pyserial para detectar puertos
            available_ports = serial.tools.list_ports.comports()
            
            for port in available_ports:
                port_info = {
                    'device': port.device,
                    'description': port.description,
                    'hwid': port.hwid,
                    'manufacturer': getattr(port, 'manufacturer', 'Unknown'),
                    'product': getattr(port, 'product', 'Unknown'),
                    'vid': getattr(port, 'vid', None),
                    'pid': getattr(port, 'pid', None),
                    'is_huawei': False,
                    'is_modem': False
                }
                
                # Detectar si es Huawei
                if port.hwid and ('12d1' in port.hwid.lower() or 'huawei' in port.description.lower()):
                    port_info['is_huawei'] = True
                
                # Detectar si es un módem
                description_lower = port.description.lower()
                if any(keyword in description_lower for keyword in ['modem', 'mobile', 'gsm', 'lte', '3g', '4g']):
                    port_info['is_modem'] = True
                
                ports.append(port_info)
        
        except Exception as e:
            print(f"Error escaneando puertos: {e}")
        
        return ports
    
    @staticmethod
    def find_huawei_modem() -> Optional[str]:
        """Busca específicamente el módem Huawei"""
        
        ports = SystemConfig.scan_available_ports()
        
        # Prioridad 1: Huawei con VID:PID específico (12d1:1506)
        for port in ports:
            if port['vid'] == 0x12d1 and port['pid'] == 0x1506:
                return port['device']
        
        # Prioridad 2: Cualquier dispositivo Huawei
        for port in ports:
            if port['is_huawei']:
                return port['device']
        
        # Prioridad 3: Cualquier módem
        for port in ports:
            if port['is_modem']:
                return port['device']
        
        return None

class ConfigManager:
    """Gestor de configuración del gateway"""
    
    def __init__(self, config_file: str = "gateway_config.json"):
        self.config_file = config_file
        self.config = self.load_config()
    
    def load_config(self) -> Dict:
        """Carga configuración desde archivo"""
        
        default_config = {
            'serial_port': None,
            'baud_rate': 9600,
            'auto_detect': True,
            'smsc_number': '+51997990000',  # Claro Perú por defecto
            'gateway_number': '997507384',
            'test_numbers': {
                'response_capable': '946467799',
                'receive_only': '913044047'
            },
            'monitoring': {
                'enabled': True,
                'check_interval': 10
            },
            'web_server': {
                'host': '0.0.0.0',
                'port': 8000
            }
        }
        
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    loaded_config = json.load(f)
                    # Combinar con valores por defecto
                    default_config.update(loaded_config)
        except Exception as e:
            print(f"Error cargando configuración: {e}")
        
        return default_config
    
    def save_config(self):
        """Guarda configuración a archivo"""
        
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Error guardando configuración: {e}")
    
    def get_serial_port(self) -> Optional[str]:
        """Obtiene el puerto serie a usar"""
        
        if self.config['auto_detect']:
            # Detectar automáticamente
            detected = SystemConfig.find_huawei_modem()
            if detected:
                self.config['serial_port'] = detected
                self.save_config()
                return detected
        
        # Usar puerto configurado manualmente
        return self.config.get('serial_port')
    
    def set_serial_port(self, port: str):
        """Configura puerto serie manualmente"""
        self.config['serial_port'] = port
        self.config['auto_detect'] = False
        self.save_config()
    
    def enable_auto_detect(self):
        """Habilita detección automática"""
        self.config['auto_detect'] = True
        self.save_config()

# Instancia global del gestor de configuración
config_manager = ConfigManager()

def get_system_info() -> Dict:
    """Obtiene información completa del sistema"""
    
    return {
        'os': SystemConfig.detect_os(),
        'platform': platform.platform(),
        'python_version': platform.python_version(),
        'available_ports': SystemConfig.scan_available_ports(),
        'detected_modem': SystemConfig.find_huawei_modem(),
        'default_ports': SystemConfig.get_default_ports(),
        'current_config': config_manager.config
    }

if __name__ == "__main__":
    # Test de detección
    print("🔍 === DETECCIÓN DEL SISTEMA ===\n")
    
    system_info = get_system_info()
    
    print(f"💻 Sistema operativo: {system_info['os']}")
    print(f"🐍 Python: {system_info['python_version']}")
    print(f"📡 Módem detectado: {system_info['detected_modem'] or 'No encontrado'}")
    
    print(f"\n📱 Puertos disponibles:")
    for port in system_info['available_ports']:
        emoji = "🎯" if port['is_huawei'] else "📞" if port['is_modem'] else "🔌"
        print(f"   {emoji} {port['device']}: {port['description']}")
        if port['is_huawei']:
            print(f"      ✅ Huawei detectado (VID:{port['vid']:04x}, PID:{port['pid']:04x})")
    
    print(f"\n⚙️ Configuración actual:")
    config = system_info['current_config']
    print(f"   📍 Puerto: {config.get('serial_port', 'Auto-detectar')}")
    print(f"   ⚡ Velocidad: {config['baud_rate']} bps")
    print(f"   🔍 Auto-detectar: {'Sí' if config['auto_detect'] else 'No'}")
    print(f"   🌐 Servidor web: {config['web_server']['host']}:{config['web_server']['port']}")
