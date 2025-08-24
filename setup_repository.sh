#!/bin/bash

echo "🚀 Preparando SMS Gateway para repositorio privado..."

# Verificar si git está instalado
if ! command -v git &> /dev/null; then
    echo "❌ Git no está instalado. Por favor instala Git primero."
    exit 1
fi

# Inicializar repositorio si no existe
if [ ! -d ".git" ]; then
    echo "📁 Inicializando repositorio Git..."
    git init
else
    echo "📁 Repositorio Git ya existe"
fi

#!/bin/bash
# Script para preparar el proyecto para Git/GitHub
# Limpia archivos temporales y de desarrollo

echo "🧹 Preparando proyecto para GitHub..."

# Detener cualquier proceso del gateway
echo "� Deteniendo procesos del gateway..."
pkill -f "web_server_multiplatform.py" 2>/dev/null || true
pkill -f "server_" 2>/dev/null || true

# Limpiar archivos de caché de Python
echo "🗑️  Limpiando archivos temporales..."
find . -name "*.pyc" -delete
find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true

# Limpiar archivos de configuración local (contienen datos sensibles)
echo "🔒 Removiendo archivos de configuración local..."
rm -f gateway_config.json
rm -f config.json
rm -f .env
rm -f *.db
rm -f *.sqlite*
rm -f *.log

# Limpiar archivos de prueba con números reales
echo "📱 Removiendo archivos de prueba con números reales..."
rm -f test_real_*.py
rm -f *_working.py

# Crear requirements.txt actualizado
echo "📦 Actualizando requirements.txt..."
cat > requirements.txt << EOF
# SMS Gateway Multiplataforma - Dependencias
# Compatible con Python 3.7+

# Comunicación serie multiplataforma
pyserial>=3.5,<4.0

# Herramientas opcionales para desarrollo
pytest>=6.0.0
black>=21.0.0

# Nota: El sistema usa principalmente librerías estándar de Python
# para máxima compatibilidad multiplataforma
EOF

# Actualizar .gitignore
echo "🚫 Actualizando .gitignore..."
cat >> .gitignore << EOF

# Archivos específicos de desarrollo
*_working.py
*_backup.py
test_numbers.py
gammu-smsdrc
gammu_utils.py

# Configuraciones de desarrollo
venv/
.vscode/
*.code-workspace
EOF

# Mostrar estado final
echo "✅ Proyecto preparado para GitHub"
echo ""
echo "📋 Archivos principales del proyecto:"
ls -la *.py | grep -E "(web_server_multiplatform|multiplatform_sms_engine|system_config|install)" | head -10
echo ""
echo "📄 Documentación:"
ls -la *.md *.txt LICENSE
echo ""
echo "🎯 Listo para: git init && git add . && git commit"

# Agregar archivos al repositorio
echo "📦 Agregando archivos al repositorio..."
git add .

# Hacer commit inicial si no hay commits
if [ -z "$(git log --oneline 2>/dev/null)" ]; then
    echo "💾 Haciendo commit inicial..."
    git commit -m "🚀 Initial commit: SMS Gateway Multiplataforma

✨ Características:
- Compatible con Windows, Linux, macOS
- Detección automática de SIM cards
- Configuración flexible de operadores
- Interfaz web moderna
- Instalador automático
- Gestión inteligente de SIM intercambiables

🔧 Funcionalidades:
- Envío/recepción bidireccional SMS
- API REST completa
- Estadísticas en tiempo real
- Detección automática de puertos
- Configuración automática de SMSC

📱 Hardware soportado:
- Huawei E8278 HiLink (modo módem)
- Detección automática de SIM cards
- Soporte multi-operador"
else
    echo "📝 Haciendo commit de cambios..."
    git commit -m "📱 Update: Mejoras en gestión de SIM cards

- Detección automática de información de SIM
- Configuración adaptable por operador
- Documentación actualizada para intercambio de SIMs
- Sistema preparado para repositorio privado"
fi

echo ""
echo "✅ Repositorio preparado para subir a GitHub"
echo ""
echo "🔐 Para crear repositorio privado en GitHub:"
echo "   1. Ir a https://github.com/new"
echo "   2. Nombre: sms-gateway-multiplatform"
echo "   3. Marcar como 'Private'"
echo "   4. No inicializar con README (ya existe)"
echo ""
echo "🌐 Para subir el código:"
echo "   git remote add origin https://github.com/TU_USUARIO/sms-gateway-multiplatform.git"
echo "   git branch -M main"
echo "   git push -u origin main"
echo ""
echo "📱 El proyecto está listo para uso en producción!"
