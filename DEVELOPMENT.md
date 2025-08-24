# 🛠️ Guía de Desarrollo - SMS Gateway Multiplataforma

## Estructura del Proyecto

```
sms-gateway-multiplataforma/
├── 🎯 ARCHIVOS PRINCIPALES
│   ├── web_server_multiplatform.py    # Servidor web y API REST
│   ├── multiplatform_sms_engine.py    # Motor SMS core
│   └── system_config.py               # Configuración multiplataforma
│
├── 🚀 INSTALACIÓN
│   ├── install.py                     # Instalador automático
│   ├── requirements.txt               # Dependencias
│   └── QUICK_START.md                 # Guía rápida
│
├── 📱 ARCHIVOS LEGACY (compatibilidad)
│   ├── complete_sms_gateway.py        # Gateway completo v1
│   ├── sms_engine_*.py               # Versiones anteriores
│   └── server_*.py                   # Servidores de prueba
│
└── 📋 DOCUMENTACIÓN
    ├── README.md                      # Documentación principal
    ├── CHANGELOG.md                   # Historial de cambios
    └── LICENSE                        # Licencia MIT
```

## Variables de Entorno de Desarrollo

```bash
# Para desarrollo local
export SMS_DEBUG=True
export SMS_LOG_LEVEL=DEBUG
export SMS_PORT=8080
```

## Flujo de Desarrollo

### 1. Configuración inicial
```bash
git clone <tu-repo>
python install.py
cp gateway_config.example.json gateway_config.json
```

### 2. Desarrollo local
```bash
# Activar modo debug
python web_server_multiplatform.py --debug

# Ejecutar tests
python -m pytest test_*.py

# Limpiar antes de commit
./cleanup_for_github.sh
```

### 3. Testing multiplataforma
```bash
# Test específicos por OS
python test_advanced.py          # Test completo
python test_at_commands.py       # Test comandos AT
python test_reception.py         # Test recepción SMS
```

## API Endpoints para Desarrollo

```
GET  /api/system-info     # Info del sistema
POST /api/connect         # Conectar gateway
POST /api/send           # Enviar SMS
GET  /api/messages       # Historial mensajes
POST /api/test-port      # Probar puerto
```

## Configuración para Diferentes Entornos

### Desarrollo
```json
{
  "web_server": {
    "host": "localhost",
    "port": 8080
  },
  "debug": true
}
```

### Producción
```json
{
  "web_server": {
    "host": "0.0.0.0",
    "port": 80
  },
  "debug": false
}
```

## Nuevas Funcionalidades Sugeridas

### 🎯 Próximas características
- [ ] Soporte para múltiples módems simultáneos
- [ ] Base de datos SQLite para persistencia
- [ ] Integración con webhooks
- [ ] Dashboard con métricas avanzadas
- [ ] Soporte para MMS
- [ ] Integración con Telegram/WhatsApp
- [ ] Sistema de plantillas de mensajes
- [ ] Programación de envíos
- [ ] Balanceador de carga entre SIMs

### 🔧 Mejoras técnicas
- [ ] Docker containerization
- [ ] CI/CD pipeline
- [ ] Tests automatizados
- [ ] Documentación API con Swagger
- [ ] Logging estructurado
- [ ] Métricas con Prometheus
- [ ] Health checks avanzados

## Contribución

1. Fork del repositorio
2. Crear branch: `git checkout -b feature/nueva-funcionalidad`
3. Commit cambios: `git commit -am 'Add nueva funcionalidad'`
4. Push branch: `git push origin feature/nueva-funcionalidad`
5. Crear Pull Request

## Testing en Diferentes Sistemas

### Windows
```cmd
# Usar PowerShell como administrador
python install.py
python web_server_multiplatform.py
```

### Linux
```bash
sudo usermod -a -G dialout $USER
logout  # Importante!
python3 install.py
```

### macOS
```bash
brew install python
python3 install.py
```

## Depuración Común

### Puerto serie no detectado
```bash
# Linux
ls -la /dev/ttyUSB*
sudo dmesg | grep USB

# Windows  
# Device Manager > Ports (COM & LPT)

# macOS
ls -la /dev/tty.*
```

### Permisos de usuario
```bash
# Linux
groups $USER  # Debe incluir 'dialout'
sudo usermod -a -G dialout $USER
```

### Módem en modo incorrecto
```bash
# Verificar VID:PID
lsusb | grep Huawei
# 12d1:1506 = modo módem ✅
# 12d1:14db = modo HiLink ❌
```
