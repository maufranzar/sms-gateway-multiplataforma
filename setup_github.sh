#!/bin/bash
# Script para conectar con repositorio de GitHub
# Mauricio Franco - maufranzar@gmail.com

echo "🔗 Configuración de GitHub para SMS Gateway Multiplataforma"
echo "👤 Usuario: Mauricio Franco (maufranzar@gmail.com)"
echo ""

echo "📋 Opciones para subir a GitHub:"
echo ""
echo "1️⃣  NUEVO REPOSITORIO PRIVADO (Recomendado)"
echo "   - Crear repositorio nuevo en GitHub"
echo "   - Mantener código privado"
echo "   - Control total del proyecto"
echo ""
echo "2️⃣  REPOSITORIO EXISTENTE"
echo "   - Conectar a repositorio ya existente"
echo "   - Actualizar código existente"
echo ""

echo "🚀 Para crear NUEVO repositorio privado:"
echo "1. Ve a: https://github.com/new"
echo "2. Nombre del repositorio: sms-gateway-multiplataforma"
echo "3. Descripción: SMS Gateway multiplataforma para Huawei E8278 con gestión inteligente de SIM cards"
echo "4. Marca como 'Private' ✅"
echo "5. NO inicializar con README (ya tenemos archivos)"
echo "6. Crea el repositorio"
echo ""

echo "📝 Comandos para conectar con GitHub:"
echo ""
echo "# Para repositorio NUEVO:"
echo "git remote add origin https://github.com/maufranzar/sms-gateway-multiplataforma.git"
echo "git branch -M main"
echo "git push -u origin main"
echo ""

echo "# Para repositorio EXISTENTE (cambia 'nombre-repo'):"
echo "git remote add origin https://github.com/maufranzar/nombre-repo.git"
echo "git branch -M main"
echo "git push -u origin main"
echo ""

echo "🔐 Autenticación GitHub:"
echo "- Usa tu token personal de GitHub en lugar de contraseña"
echo "- O configura SSH keys para acceso más fácil"
echo ""

echo "✅ Estado actual del repositorio local:"
git log --oneline -3
echo ""
git remote -v
echo ""

echo "📁 Archivos listos para subir:"
echo "$(git ls-tree --name-only HEAD | wc -l) archivos en total"
echo ""

echo "🎯 Próximos pasos recomendados:"
echo "1. Crear repositorio privado en GitHub"
echo "2. Copiar y ejecutar comandos de conexión"
echo "3. Verificar subida exitosa"
echo "4. Clonar en otro ordenador para probar"
