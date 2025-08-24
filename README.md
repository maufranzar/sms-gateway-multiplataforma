# � SMS Gateway Multiplataforma

Gateway SMS completo compatible con **Windows**, **Linux** y **macOS** para envío y recepción de mensajes a través de módem Huawei E8278.

## ✨ Características

- 🌐 **Interfaz web responsive** - Control completo desde el navegador
- 🔍 **Detección automática** - Encuentra automáticamente el módem conectado
- 📱 **Envío/Recepción SMS** - Bidireccional con seguimiento de estado
- 📊 **Estadísticas en tiempo real** - Monitoreo de mensajes y respuestas
- 🖥️ **Multiplataforma** - Windows, Linux, macOS
- ⚙️ **Configuración automática** - Puerto serie, SMSC y permisos

## 🚀 Instalación Rápida

### Opción 1: Instalador Automático (Recomendado)

```bash
# Descargar el proyecto
git clone https://github.com/tu-usuario/sms-gateway.git
cd sms-gateway

# Ejecutar instalador automático
python install.py
```

### Opción 2: Instalación Manual

#### Requisitos
- **Python 3.7+**
- **Módem Huawei E8278** en modo módem
- **Permisos de puerto serie** (Linux/macOS)

#### Dependencias
```bash
pip install pyserial>=3.5
```

## 🖥️ Instalación por Sistema Operativo

### 🐧 Linux (Ubuntu/Debian/Fedora)

```bash
# 1. Instalar dependencias
sudo apt update  # Ubuntu/Debian
sudo dnf update  # Fedora

sudo apt install python3 python3-pip  # Ubuntu/Debian
sudo dnf install python3 python3-pip  # Fedora

# 2. Instalar pyserial
pip3 install pyserial

# 3. Configurar permisos de usuario
sudo usermod -a -G dialout $USER
sudo usermod -a -G uucp $USER

# 4. Reiniciar sesión (importante!)
logout

# 5. Ejecutar gateway
python3 web_server_multiplatform.py
```

### 🍎 macOS

```bash
# 1. Instalar Homebrew (si no está instalado)
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# 2. Instalar Python
brew install python

# 3. Instalar dependencias
pip3 install pyserial

# 4. Ejecutar gateway
python3 web_server_multiplatform.py
```

### 🪟 Windows

```cmd
# 1. Instalar Python desde python.org (marcar "Add to PATH")

# 2. Abrir Command Prompt como Administrador

# 3. Instalar dependencias
pip install pyserial

# 4. Ejecutar gateway
python web_server_multiplatform.py
```

## 🔧 Configuración del Hardware

### Preparar Módem Huawei E8278

1. **Conectar el módem** vía USB
2. **Insertar SIM card** - El sistema detectará automáticamente la información
3. **Configurar en modo módem** (no HiLink):
   ```bash
   # Linux: verificar modo
   lsusb | grep Huawei
   # Debe mostrar: 12d1:1506 (modo módem)
   # Si muestra: 12d1:14db (modo HiLink), cambiar a módem
   ```

4. **Verificar puerto detectado**:
   - **Linux**: `/dev/ttyUSB0` o `/dev/ttyUSB1`
   - **macOS**: `/dev/tty.usbserial*` o `/dev/tty.usbmodem*`
   - **Windows**: `COM3`, `COM4`, etc.

### 📱 Gestión de SIM Cards

El sistema está diseñado para **intercambio flexible de SIM cards**:

- **Detección automática** del número de teléfono
- **Configuración automática** del SMSC según operador
- **Guardado de información** de cada SIM (IMSI, ICCID)
- **Historial de SIMs** utilizadas

#### ⚠️ Importante: Intercambio de SIM
```bash
# Al cambiar de SIM card:
1. Apagar el gateway
2. Cambiar la SIM en el módem
3. Reiniciar el gateway
4. El sistema detectará automáticamente la nueva SIM
```

### Configuración de Red (Automática)

El sistema detecta automáticamente:
```json
{
  "gateway_number": "999123456",      // Número de la SIM actual
  "smsc_number": "+51997990000",      // Centro de mensajes del operador
  "operator": "Claro Peru",           // Operador detectado
  "sim_info": {
    "imsi": "716010123456789",        // ID único del suscriptor
    "iccid": "8951071601012345678",   // ID único de la SIM card
    "last_updated": "2024-08-22T15:30:00"
  }
}
```

#### Operadores Soportados
- **Claro Perú**: SMSC +51997990000
- **Movistar Perú**: SMSC +51997990001  
- **Entel Perú**: SMSC +51997990002
- **Bitel Perú**: SMSC +51997990003
- **Otros operadores**: Detección automática
- **Puerto AT**: /dev/ttyUSB0
- **Velocidad**: 9600 bps
- **Operador**: Claro Perú
- **SMSC**: +51997990000

### Sistema Operativo
- **OS**: Debian Trixie
- **Usuario**: Miembro del grupo `dialout`
- **ModemManager**: Desactivado

## 🚀 Instalación

### 1. Clonar o descargar el proyecto
```bash
cd /home/mau/Dev/sms-gateway
```

### 2. Crear entorno virtual (recomendado)
```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Instalar dependencias
```bash
pip install -r requirements.txt
```

### 4. Configurar variables de entorno
Edita el archivo `.env` según tus necesidades:
```bash
SERIAL_PORT=/dev/ttyUSB0
SERIAL_BAUDRATE=9600
DATABASE_URL=sqlite:///./sms_gateway.db
HOST=0.0.0.0
PORT=8000
```

### 5. Inicializar la base de datos
```bash
python3 cli.py init
```

## 📱 Uso

### Iniciar el servidor API
```bash
python3 cli.py start
```

El servidor estará disponible en:
- **API**: http://localhost:8000
- **Documentación**: http://localhost:8000/docs
- **Estado**: http://localhost:8000/status

### CLI - Envío desde terminal
```bash
# Enviar SMS
python3 cli.py send 913044047 "Hola desde CLI"

# Probar conexión
python3 cli.py test

# Ver estado de mensajes
python3 cli.py status
```

### API REST - Envío programático

#### Enviar SMS
```bash
curl -X POST "http://localhost:8000/send-sms" \
     -H "Content-Type: application/json" \
     -d '{
       "phone_number": "913044047",
       "message": "Comando de prueba",
       "message_type": "command"
     }'
```

#### Ver mensajes
```bash
curl "http://localhost:8000/messages"
```

#### Estado del gateway
```bash
curl "http://localhost:8000/status"
```

## 🗂️ Estructura del Proyecto

```
sms-gateway/
├── main.py              # API REST con FastAPI
├── sms_engine.py        # Motor principal de SMS (comandos AT)
├── models.py            # Modelos de base de datos
├── database.py          # Configuración de SQLAlchemy
├── config.py            # Configuración de la aplicación
├── cli.py               # Interfaz de línea de comandos
├── test_at_commands.py  # Scripts de prueba
├── requirements.txt     # Dependencias Python
├── .env                 # Variables de entorno
└── README.md           # Esta documentación
```

## 🔄 Estados de Mensaje

- **PENDING**: Mensaje en cola para envío
- **SENDING**: Mensaje siendo enviado
- **SENT**: Mensaje enviado exitosamente
- **DELIVERED**: Mensaje entregado (cuando disponible)
- **FAILED**: Error en el envío
- **EXPIRED**: Mensaje expirado

## 📊 Monitoreo

### Interfaz Web
Visita http://localhost:8000 para ver:
- Estado de conexión del gateway
- Información de red
- Enlaces a documentación

### Logs
Los logs se guardan en `sms_gateway.log` y en consola:
```bash
tail -f sms_gateway.log
```

## 🛠️ Desarrollo

### Probar comandos AT directamente
```python
python3 test_at_commands.py
```

### Probar con gammu
```bash
gammu identify
gammu networkinfo
gammu sendsms TEXT 913044047 -text "Prueba gammu"
```

## 🔧 Troubleshooting

### Gateway no conecta
1. Verificar que el dispositivo esté en `/dev/ttyUSB0`
2. Confirmar permisos de usuario (grupo `dialout`)
3. Verificar que ModemManager esté desactivado
4. Comprobar que no hay otras aplicaciones usando el puerto

### Errores de permisos
```bash
sudo usermod -a -G dialout $USER
# Reiniciar sesión
```

### ModemManager interfiriendo
```bash
sudo systemctl stop ModemManager
sudo systemctl disable ModemManager
```

## 📞 Configuración de Red

Para forzar modo 3G (evitar SMS-over-IMS):
```bash
# Usando gammu o comando AT
AT^SYSCFG=2,2,3FFFFFFF,1,2
```

## 🤝 Contribuir

1. Fork del proyecto
2. Crear rama feature (`git checkout -b feature/nueva-funcionalidad`)
3. Commit de cambios (`git commit -m 'Agregar nueva funcionalidad'`)
4. Push a la rama (`git push origin feature/nueva-funcionalidad`)
5. Crear Pull Request

## 📄 Licencia

Este proyecto está bajo la Licencia MIT. Ver el archivo `LICENSE` para más detalles.

## 📧 Contacto

Para soporte o preguntas, crear un issue en el repositorio del proyecto.

---

**¡Disfruta enviando SMS con tu gateway Huawei E8278! 📱✨**
