"""
Verificador de Mensajes Recibidos
Verifica si el gateway detectó el mensaje "ok" enviado
"""
import asyncio
from sms_engine_ultra_simple import SMSEngine

async def check_received_messages():
    """Verifica mensajes recibidos en el gateway"""
    
    print("📥 === VERIFICANDO MENSAJES RECIBIDOS ===\n")
    
    engine = SMSEngine()
    await engine.connect()
    
    try:
        print("🔍 Verificando todos los mensajes en memoria del gateway...")
        
        # Verificar todas las ubicaciones de almacenamiento
        storage_locations = ["SM", "ME", "MT"]
        all_messages = []
        
        for location in storage_locations:
            print(f"\n📍 Verificando ubicación: {location}")
            
            try:
                # Seleccionar ubicación
                await engine._send_command(f'AT+CPMS="{location}"')
                
                # Obtener capacidad
                capacity_response = await engine._send_command("AT+CPMS?")
                print(f"💾 Capacidad: {capacity_response.strip()}")
                
                # Listar todos los mensajes
                messages_response = await engine._send_command('AT+CMGL="ALL"')
                print(f"📋 Respuesta: {messages_response.strip()}")
                
                # Parsear mensajes
                lines = messages_response.split('\n')
                message_count = 0
                
                i = 0
                while i < len(lines):
                    line = lines[i].strip()
                    
                    if line.startswith('+CMGL:'):
                        message_count += 1
                        print(f"\n📨 Mensaje #{message_count}:")
                        print(f"   📋 Header: {line}")
                        
                        # El contenido del mensaje está en la siguiente línea
                        if i + 1 < len(lines):
                            content = lines[i + 1].strip()
                            print(f"   💬 Contenido: {content}")
                            
                            # Extraer información del header
                            import re
                            # +CMGL: <index>,<stat>,<oa/da>,<alpha>,<scts>
                            parts = line.split(',')
                            if len(parts) >= 3:
                                index = parts[0].replace('+CMGL:', '').strip()
                                status = parts[1].strip().strip('"')
                                sender = parts[2].strip().strip('"')
                                
                                message_info = {
                                    'location': location,
                                    'index': index,
                                    'status': status,
                                    'sender': sender,
                                    'content': content
                                }
                                
                                all_messages.append(message_info)
                                
                                # Verificar si es del número 946467799
                                if '946467799' in sender or sender in '946467799':
                                    print(f"   🎯 ¡MENSAJE DEL NÚMERO DE PRUEBA DETECTADO!")
                                    print(f"   📱 De: {sender}")
                                    print(f"   💬 Mensaje: {content}")
                                    
                                    if 'ok' in content.lower():
                                        print(f"   ✅ ¡Contiene 'OK' como esperado!")
                        
                        i += 1  # Saltar la línea del contenido
                    
                    i += 1
                
                print(f"\n📊 Total en {location}: {message_count} mensajes")
                
            except Exception as e:
                print(f"❌ Error en {location}: {e}")
        
        # Resumen final
        print(f"\n📊 === RESUMEN TOTAL ===")
        print(f"📥 Total de mensajes encontrados: {len(all_messages)}")
        
        if all_messages:
            print(f"\n📱 Todos los mensajes:")
            for i, msg in enumerate(all_messages, 1):
                print(f"   {i}. [{msg['location']}] {msg['sender']}: {msg['content']}")
                if '946467799' in msg['sender']:
                    print(f"      🎯 ¡Este es del número de prueba!")
        else:
            print(f"ℹ️ No se encontraron mensajes en ninguna ubicación")
            print(f"💡 Posibles causas:")
            print(f"   • El mensaje no llegó al gateway")
            print(f"   • Está en una ubicación no verificada")
            print(f"   • Se eliminó automáticamente")
        
        # Verificar configuración actual
        print(f"\n⚙️ === CONFIGURACIÓN ACTUAL ===")
        
        config_commands = [
            ("AT+CPMS?", "Almacenamiento actual"),
            ("AT+CNMI?", "Notificaciones"),
            ("AT+CMGF?", "Formato de mensaje"),
            ("AT+CSCS?", "Codificación"),
        ]
        
        for cmd, desc in config_commands:
            try:
                response = await engine._send_command(cmd)
                print(f"📋 {desc}: {response.strip()}")
            except Exception as e:
                print(f"❌ {desc}: {e}")
        
        # Sugerencias
        print(f"\n💡 === PRÓXIMOS PASOS ===")
        
        if all_messages:
            print(f"✅ El gateway SÍ puede recibir mensajes")
            if any('946467799' in msg['sender'] for msg in all_messages):
                print(f"🎯 ¡El mensaje 'ok' fue recibido correctamente!")
                print(f"📱 Sistema de recepción funcionando")
            else:
                print(f"📤 Intenta enviar otro mensaje desde 946467799")
        else:
            print(f"🔧 Troubleshooting necesario:")
            print(f"   1. Verifica que 997507384 sea el número correcto del gateway")
            print(f"   2. Envía otro SMS de prueba")
            print(f"   3. Verifica la configuración de la SIM")
    
    finally:
        await engine.disconnect()

async def send_test_from_gateway():
    """Intenta enviar un mensaje simple para verificar envío"""
    
    print("📤 === TEST DE ENVÍO SIMPLE ===\n")
    
    engine = SMSEngine()
    await engine.connect()
    
    try:
        # Configuración mínima
        print("⚙️ Configurando gateway para envío...")
        
        await engine._send_command("AT+CMGF=1")  # Modo texto
        await engine._send_command('AT+CSCS="GSM"')  # Codificación
        
        # Verificar SMSC
        smsc = await engine._send_command("AT+CSCA?")
        print(f"📞 SMSC actual: {smsc.strip()}")
        
        # Intentar envío simple
        print(f"\n📤 Intentando envío simple a 946467799...")
        
        result = await engine.send_sms("946467799", "Test simple " + str(int(asyncio.get_event_loop().time())))
        
        if result.success:
            print(f"✅ ¡Envío exitoso!")
            print(f"🔢 Referencia: {result.reference_id}")
        else:
            print(f"❌ Error en envío: {result.error_message}")
            
            # Mostrar detalles del error
            print(f"\n🔍 Diagnóstico del error:")
            print(f"   📋 Error: {result.error_message}")
            print(f"   💡 El problema está en el envío, no en la recepción")
    
    finally:
        await engine.disconnect()

async def monitor_live():
    """Monitoreo en vivo para detectar mensajes"""
    
    print("🔔 === MONITOREO EN VIVO ===\n")
    print("📱 Envía otro mensaje 'test' desde 946467799 AHORA")
    print("⏰ Monitoreando por 60 segundos...")
    
    engine = SMSEngine()
    await engine.connect()
    
    try:
        # Configurar para recepción
        await engine._send_command("AT+CMGF=1")
        await engine._send_command("AT+CNMI=1,1,0,0,0")
        
        initial_messages = await get_all_messages(engine)
        initial_count = len(initial_messages)
        
        print(f"📊 Mensajes iniciales: {initial_count}")
        
        for i in range(12):  # 60 segundos
            remaining = 60 - (i * 5)
            print(f"⏳ {remaining}s restantes...")
            
            current_messages = await get_all_messages(engine)
            current_count = len(current_messages)
            
            if current_count > initial_count:
                print(f"\n🎉 ¡NUEVO MENSAJE DETECTADO!")
                
                # Mostrar nuevos mensajes
                new_messages = current_messages[initial_count:]
                for msg in new_messages:
                    print(f"📨 De: {msg['sender']}")
                    print(f"💬 Mensaje: {msg['content']}")
                    
                    if '946467799' in msg['sender']:
                        print(f"✅ ¡Es del número de prueba!")
                
                initial_count = current_count
            
            await asyncio.sleep(5)
        
        print(f"\n📊 Monitoreo completado")
        
    finally:
        await engine.disconnect()

async def get_all_messages(engine):
    """Obtiene todos los mensajes del gateway"""
    all_messages = []
    
    try:
        response = await engine._send_command('AT+CMGL="ALL"')
        lines = response.split('\n')
        
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            
            if line.startswith('+CMGL:'):
                if i + 1 < len(lines):
                    content = lines[i + 1].strip()
                    
                    # Extraer sender
                    import re
                    parts = line.split(',')
                    if len(parts) >= 3:
                        sender = parts[2].strip().strip('"')
                        
                        all_messages.append({
                            'sender': sender,
                            'content': content
                        })
                
                i += 1
            
            i += 1
    
    except:
        pass
    
    return all_messages

def menu():
    """Menú de verificación"""
    
    print("🔍 === VERIFICACIÓN DE RECEPCIÓN ===")
    print("1. Verificar mensajes recibidos (buscar tu 'ok')")
    print("2. Test de envío simple")
    print("3. Monitoreo en vivo (60s)")
    print("4. Salir")
    
    while True:
        try:
            choice = input("\n🔢 Selecciona una opción (1-4): ").strip()
            
            if choice == "1":
                asyncio.run(check_received_messages())
            elif choice == "2":
                asyncio.run(send_test_from_gateway())
            elif choice == "3":
                asyncio.run(monitor_live())
            elif choice == "4":
                print("👋 ¡Hasta luego!")
                break
            else:
                print("❌ Opción inválida")
                
        except KeyboardInterrupt:
            print("\n\n⏹️ Interrumpido")
            break

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "check":
            asyncio.run(check_received_messages())
        elif sys.argv[1] == "send":
            asyncio.run(send_test_from_gateway())
        elif sys.argv[1] == "monitor":
            asyncio.run(monitor_live())
    else:
        menu()
