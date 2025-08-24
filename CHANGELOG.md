# 📱 SMS Gateway Multiplataforma - Changelog

## [v2.0.0] - 2024-08-22 - Versión Multiplataforma

### ✨ Nuevas Características
- **Compatibilidad multiplataforma**: Windows, Linux, macOS
- **Detección automática de SIM**: IMSI, ICCID, número de teléfono, operador
- **Configuración adaptable**: SMSC automático según operador
- **Interfaz web moderna**: Diseño responsive y estadísticas en tiempo real
- **Instalador automático**: Configuración de permisos y dependencias
- **Gestión flexible de SIMs**: Intercambio automático sin reconfiguración

### 🔧 Mejoras Técnicas
- Motor SMS optimizado para múltiples sistemas operativos
- Sistema de configuración JSON centralizado
- Detección automática de puertos serie
- Manejo robusto de errores y timeouts
- API REST completa para integración

### 📱 Gestión de SIM Cards
- Detección automática de información de SIM (IMSI, ICCID)
- Configuración automática de SMSC por operador
- Guardado de perfiles de SIM para intercambio rápido
- Historial de SIMs utilizadas

### 🌐 Interfaz Web
- Dashboard moderno con estadísticas en tiempo real
- Configuración visual de puerto y SMSC
- Envío de SMS con contador de caracteres
- Visualización de mensajes enviados y recibidos
- Estado de conexión en tiempo real

### 📦 Instalación y Distribución
- Script de instalación automática (`install.py`)
- Configuración automática de permisos de usuario
- Scripts de ejecución para cada sistema operativo
- Documentación completa multiplataforma

### 🔐 Seguridad y Configuración
- Configuración local sin datos sensibles en código
- Detección automática de hardware sin configuración manual
- Permisos mínimos necesarios por sistema operativo

---

## [v1.0.0] - 2024-08-20 - Versión Base

### ✨ Características Iniciales
- Envío de SMS básico con Huawei E8278
- Comunicación bidireccional
- Tracking de mensajes con referencias
- Detección de respuestas automáticas
- Interfaz web básica

### 🔧 Funcionalidades Base
- Motor SMS con comandos AT
- Base de datos SQLite para historial
- API REST básica
- Configuración manual de puerto serie

### 📱 Hardware Soportado
- Huawei E8278 HiLink en modo módem
- Puerto serie Linux (/dev/ttyUSB0)
- Configuración manual de SMSC

### Números de Prueba Iniciales
- Gateway: 997507384
- Bidireccional: 946467799
- Solo recepción: 913044047

### Mensajes de Prueba Exitosos
- Referencias: #42, #43, #44, #45
- Comando "motor" funcional
- Respuesta "ok" detectada correctamente
