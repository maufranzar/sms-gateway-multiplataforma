#!/bin/bash
# Script de limpieza del proyecto antes de subir a GitHub
# Elimina archivos temporales y datos sensibles

echo "🧹 Limpiando proyecto SMS Gateway..."

# Eliminar archivos temporales de Python
find . -name "*.pyc" -delete
find . -name "__pycache__" -type d -exec rm -rf {} +
find . -name "*.pyo" -delete

# Eliminar configuraciones específicas del usuario
rm -f gateway_config.json
rm -f *.log
rm -f *.db
rm -f *.sqlite*

# Eliminar archivos de entorno virtual si existen
rm -rf venv/
rm -rf .env

# Eliminar archivos de prueba con datos reales
rm -f test_real_*.py
rm -f real_numbers.py

# Crear estructura de directorios necesarios
mkdir -p logs/

echo "✅ Proyecto limpio y listo para GitHub"
echo "📋 Archivos incluidos:"
find . -type f -name "*.py" -o -name "*.md" -o -name "*.json" -o -name "*.txt" -o -name "*.sh" -o -name "*.bat" | sort
