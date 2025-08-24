# 🚀 Instalación Rápida - SMS Gateway Multiplataforma

## Para usar en otro ordenador (Instalación desde GitHub)

### 1. Clonar el repositorio
```bash
git clone https://github.com/maufranzar/sms-gateway-multiplataforma.git
cd sms-gateway-multiplataforma
```

### 2. Instalación automática
```bash
# Ejecutar instalador (detecta OS automáticamente)
python install.py
```

### 3. Inicio rápido
```bash
# Opción 1: Script directo
python web_server_multiplatform.py

# Opción 2: Scripts de sistema
./run_gateway.sh      # Linux/macOS
run_gateway.bat       # Windows
```

### 4. Acceder a la interfaz
- Abrir navegador: **http://localhost:8080**
- Conectar módem Huawei E8278
- Presionar "Conectar" en la interfaz
- ¡Listo para enviar SMS!

## Verificación rápida del hardware

```bash
# Linux: verificar módem conectado
lsusb | grep Huawei

# Verificar puerto serie
python -c "from system_config import SystemConfig; print(SystemConfig().scan_available_ports())"
```

## Cambio de SIM cards

1. Detener gateway (Ctrl+C)
2. Cambiar SIM físicamente
3. Reiniciar gateway
4. Sistema detecta automáticamente nueva configuración

## Dependencias mínimas

- Python 3.7+
- pyserial
- Módem Huawei E8278

## Compatibilidad

✅ Windows 10/11  
✅ Linux (Ubuntu, Debian, Fedora, etc.)  
✅ macOS (10.14+)  
✅ Huawei E8278 en modo módem  
✅ Cualquier operador (detección automática SMSC)
