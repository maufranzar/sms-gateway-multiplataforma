#!/usr/bin/env python3
"""
Script para probar recepción de SMS y estados
"""
import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sms_engine_ultra_simple import sms_engine

async def check_stored_messages():
    """Verifica mensajes almacenados en el gateway"""
    print("🔍 Verificando mensajes en el gateway...")
    
    try:
        if not sms_engine.is_connected:
            print("📡 Conectando al gateway...")
            await sms_engine.connect()
        
        # Listar todos los mensajes
        print("\n📋 Listando mensajes almacenados...")
        response = await sms_engine._send_command('AT+CMGL="ALL"')
        print(f"Respuesta: {response}")
        
        # Verificar configuración de notificaciones
        print("\n🔔 Verificando configuración de notificaciones...")
        response = await sms_engine._send_command('AT+CNMI?')
        print(f"Configuración actual: {response}")
        
        # Verificar memoria disponible
        print("\n💾 Verificando memoria SMS...")
        response = await sms_engine._send_command('AT+CPMS?')
        print(f"Estado memoria: {response}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        await sms_engine.disconnect()

async def test_message_delivery_status():
    """Prueba obtener estado de entrega de mensajes"""
    print("\n📊 Probando estado de entrega...")
    
    try:
        if not sms_engine.is_connected:
            await sms_engine.connect()
        
        # Configurar reporte de entrega
        print("⚙️ Configurando reportes de entrega...")
        response = await sms_engine._send_command('AT+CSMP=17,167,0,0')
        print(f"Configuración SMS: {response}")
        
        # Verificar soporte de delivery reports
        response = await sms_engine._send_command('AT+CNMI=?')
        print(f"Capacidades de notificación: {response}")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    print("🧪 === PRUEBA DE RECEPCIÓN Y ESTADOS ===")
    
    # Verificar mensajes almacenados
    asyncio.run(check_stored_messages())
    
    # Probar configuración de delivery reports
    asyncio.run(test_message_delivery_status())
