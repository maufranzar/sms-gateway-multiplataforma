"""
Verificador Completo de Gateway SMS
Obtiene toda la información disponible del dispositivo
"""
import asyncio
from sms_engine_ultra_simple import SMSEngine

async def complete_gateway_info():
    """Obtiene información completa del gateway"""
    
    engine = SMSEngine()
    await engine.connect()
    
    print("🔍 === INFORMACIÓN COMPLETA DEL GATEWAY ===\n")
    
    # Comandos de información básica
    info_commands = [
        ("AT+CGMI", "Fabricante"),
        ("AT+CGMM", "Modelo"),
        ("AT+CGMR", "Revisión del firmware"),
        ("AT+CGSN", "IMEI"),
        ("AT+CIMI", "IMSI"),
        ("AT+CCID", "ICC-ID (SIM)"),
        ("AT+CNUM", "Número propio"),
        ("AT+COPS?", "Operador actual"),
        ("AT+CREG?", "Registro de red"),
        ("AT+CGREG?", "Registro GPRS"),
        ("AT+CSQ", "Calidad de señal"),
        ("AT+CPMS?", "Configuración de almacenamiento"),
        ("AT+CNMI?", "Configuración de notificaciones"),
        ("AT+CSMS?", "Capacidades SMS"),
        ("AT+CSCS?", "Conjunto de caracteres"),
        ("AT+CMGF?", "Formato de mensaje"),
    ]
    
    gateway_info = {}
    
    for command, description in info_commands:
        try:
            response = await engine._send_command(command)
            gateway_info[command] = response.strip()
            print(f"✅ {description}:")
            print(f"   📋 {command}: {response.strip()}")
        except Exception as e:
            print(f"❌ {description} ({command}): {e}")
        print()
    
    # Verificar tarjeta SIM
    print("💳 === VERIFICACIÓN DE TARJETA SIM ===")
    try:
        sim_status = await engine._send_command("AT+CPIN?")
        print(f"🔐 Estado SIM: {sim_status.strip()}")
        
        if "READY" in sim_status:
            print("✅ SIM está lista")
            
            # Intentar obtener el número de diferentes maneras
            print("\n📞 === BÚSQUEDA DE NÚMERO PROPIO ===")
            
            # Método 1: AT+CNUM
            try:
                cnum = await engine._send_command("AT+CNUM")
                print(f"Método AT+CNUM: {cnum}")
            except:
                print("Método AT+CNUM: No disponible")
            
            # Método 2: Verificar en phonebook
            try:
                phonebook = await engine._send_command('AT+CPBR=1,250')
                print(f"Phonebook: {phonebook[:200]}...")
            except:
                print("Phonebook: No accesible")
            
            # Método 3: Información del operador
            try:
                operator_info = await engine._send_command("AT+COPS=3,0;+COPS?")
                print(f"Info operador: {operator_info}")
            except:
                print("Info operador: No disponible")
                
        else:
            print(f"⚠️ Problema con SIM: {sim_status}")
    
    except Exception as e:
        print(f"❌ Error verificando SIM: {e}")
    
    # Verificar capacidades SMS
    print("\n📱 === CAPACIDADES SMS ===")
    try:
        # Verificar modos de texto
        await engine._send_command("AT+CMGF=1")  # Modo texto
        text_support = await engine._send_command("AT+CMGF?")
        print(f"📝 Soporte modo texto: {text_support}")
        
        # Verificar conjuntos de caracteres
        charsets = await engine._send_command("AT+CSCS=?")
        print(f"🔤 Conjuntos disponibles: {charsets}")
        
        # Configurar UTF-8 si está disponible
        if "UTF-8" in charsets:
            await engine._send_command('AT+CSCS="UTF-8"')
            print("✅ UTF-8 configurado")
        
    except Exception as e:
        print(f"❌ Error verificando SMS: {e}")
    
    # Proponer número de prueba
    print("\n🧪 === SOLUCIÓN PARA PRUEBAS ===")
    print("Como el gateway no muestra su número propio:")
    print("1. 📞 Llama al gateway desde tu teléfono para ver el número")
    print("2. 📱 Envía un SMS al gateway desde tu teléfono")
    print("3. 🔍 Revisa la factura/portal del operador")
    print("4. 📧 Contacta al proveedor de la SIM")
    
    # Mostrar cómo enviar SMS al gateway
    print("\n📤 === CÓMO PROBAR RECEPCIÓN ===")
    print("Para probar que el gateway recibe SMS:")
    
    suggested_numbers = [
        "Envía desde tu número personal",
        "Usa otro teléfono disponible", 
        "Pide a alguien que envíe un SMS de prueba"
    ]
    
    for i, suggestion in enumerate(suggested_numbers, 1):
        print(f"{i}. {suggestion}")
    
    print(f"\n📋 El mensaje debe enviarse AL GATEWAY (no desde {gateway_info.get('AT+CNUM', 'número desconocido')})")
    
    await engine.disconnect()
    return gateway_info

async def test_with_manual_number():
    """Test permitiendo ingresar el número del gateway manualmente"""
    
    print("📞 === CONFIGURACIÓN MANUAL DEL NÚMERO ===")
    
    gateway_number = input("🔢 Ingresa el número del gateway (si lo conoces): ").strip()
    
    if not gateway_number:
        print("⚠️ Sin número específico, iniciando monitoreo general...")
        gateway_number = "DESCONOCIDO"
    
    print(f"\n📱 Configuración:")
    print(f"   🎯 Número del gateway: {gateway_number}")
    print(f"   📥 Para probar: Envía SMS AL número {gateway_number}")
    print(f"   📤 Desde: Cualquier teléfono que pueda enviar SMS")
    
    engine = SMSEngine()
    await engine.connect()
    
    print(f"\n🔔 Monitoreando mensajes por 60 segundos...")
    print(f"📱 Envía un SMS AL GATEWAY ahora")
    
    for i in range(12):
        remaining = 60 - (i * 5)
        print(f"⏳ {remaining}s restantes...")
        
        try:
            # Verificar todos los mensajes almacenados
            response = await engine._send_command('AT+CMGL="ALL"')
            
            if "+CMGL:" in response:
                print(f"\n🎉 ¡MENSAJES DETECTADOS!")
                print(f"📋 Respuesta completa:")
                print(response)
                
                # Analizar mensajes
                lines = response.split('\n')
                message_count = len([line for line in lines if line.startswith('+CMGL:')])
                print(f"\n📊 Total de mensajes en memoria: {message_count}")
                
            else:
                print(f"📋 Sin mensajes nuevos...")
                
        except Exception as e:
            print(f"❌ Error: {e}")
        
        await asyncio.sleep(5)
    
    await engine.disconnect()
    print("✅ Monitoreo completado")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "manual":
        asyncio.run(test_with_manual_number())
    else:
        asyncio.run(complete_gateway_info())
