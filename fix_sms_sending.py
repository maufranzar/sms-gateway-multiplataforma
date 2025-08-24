"""
Diagnóstico y Reparación del Envío SMS
Soluciona el problema del prompt (>) que no se recibe
"""
import asyncio
import time
from sms_engine_ultra_simple import SMSEngine

async def diagnose_sms_sending():
    """Diagnóstica paso a paso el envío SMS"""
    
    print("🔧 === DIAGNÓSTICO DE ENVÍO SMS ===\n")
    
    engine = SMSEngine()
    await engine.connect()
    
    try:
        # 1. Verificar configuración básica
        print("1️⃣ Verificando configuración básica...")
        
        # Verificar modo texto
        response = await engine._send_command("AT+CMGF=1")
        print(f"✅ Modo texto: {response.strip()}")
        
        # Verificar codificación
        response = await engine._send_command("AT+CSCS?")
        print(f"📝 Codificación actual: {response.strip()}")
        
        # Configurar codificación GSM si está disponible
        try:
            await engine._send_command('AT+CSCS="GSM"')
            print("✅ Codificación GSM configurada")
        except:
            print("⚠️ Usando codificación por defecto")
        
        print()
        
        # 2. Verificar SMSC
        print("2️⃣ Verificando centro de servicios SMS...")
        try:
            smsc_response = await engine._send_command("AT+CSCA?")
            print(f"📞 SMSC actual: {smsc_response.strip()}")
            
            # Si no hay SMSC, configurar el de Claro Perú
            if "+51" not in smsc_response:
                print("⚙️ Configurando SMSC de Claro Perú...")
                await engine._send_command('AT+CSCA="+51997990000"')
                smsc_check = await engine._send_command("AT+CSCA?")
                print(f"✅ SMSC configurado: {smsc_check.strip()}")
        except Exception as e:
            print(f"❌ Error con SMSC: {e}")
        
        print()
        
        # 3. Test de envío manual paso a paso
        print("3️⃣ Test de envío manual...")
        
        test_number = "946467799"  # Número que puede responder
        test_message = "Test manual"
        
        print(f"📱 Enviando a: {test_number}")
        print(f"💬 Mensaje: {test_message}")
        
        # Paso 1: Iniciar comando de envío
        print("\n🔸 Paso 1: Iniciando comando AT+CMGS...")
        try:
            # Enviar comando sin esperar prompt
            command = f'AT+CMGS="{test_number}"'
            engine.serial_connection.write((command + '\r\n').encode())
            print(f"📤 Comando enviado: {command}")
            
            # Esperar respuesta
            await asyncio.sleep(2)
            
            response = ""
            if engine.serial_connection.in_waiting > 0:
                response = engine.serial_connection.read(engine.serial_connection.in_waiting).decode('utf-8', errors='ignore')
                print(f"📥 Respuesta: {repr(response)}")
            
            # Verificar si hay prompt
            if ">" in response:
                print("✅ Prompt (>) recibido!")
                
                # Paso 2: Enviar mensaje
                print("\n🔸 Paso 2: Enviando mensaje...")
                message_with_ctrl_z = test_message + '\x1A'  # Ctrl+Z
                engine.serial_connection.write(message_with_ctrl_z.encode())
                print(f"📤 Mensaje enviado con Ctrl+Z")
                
                # Esperar confirmación
                await asyncio.sleep(5)
                
                if engine.serial_connection.in_waiting > 0:
                    final_response = engine.serial_connection.read(engine.serial_connection.in_waiting).decode('utf-8', errors='ignore')
                    print(f"📥 Respuesta final: {repr(final_response)}")
                    
                    if "+CMGS:" in final_response:
                        print("✅ ¡Mensaje enviado exitosamente!")
                        # Extraer referencia
                        import re
                        ref_match = re.search(r'\+CMGS:\s*(\d+)', final_response)
                        if ref_match:
                            print(f"🔢 Referencia: {ref_match.group(1)}")
                    else:
                        print("❌ Error en envío")
                
            else:
                print("❌ No se recibió prompt (>)")
                print("🔍 Respuesta completa:", repr(response))
                
                # Intentar método alternativo
                print("\n🔸 Intentando método alternativo...")
                await alternative_send_method(engine, test_number, "Test alternativo")
                
        except Exception as e:
            print(f"❌ Error en envío manual: {e}")
        
        print()
        
        # 4. Test de diferentes configuraciones
        print("4️⃣ Probando diferentes configuraciones...")
        
        configs_to_try = [
            ('AT+CSMP=17,167,0,0', "Configuración SMS PDU"),
            ('AT+CSMP=49,167,0,0', "Configuración SMS texto"),
            ('AT+CNMI=0,0,0,0,0', "Sin notificaciones"),
        ]
        
        for config_cmd, description in configs_to_try:
            try:
                response = await engine._send_command(config_cmd)
                print(f"✅ {description}: {response.strip()}")
            except Exception as e:
                print(f"❌ {description}: {e}")
        
        print()
        
        # 5. Verificar estado del módem
        print("5️⃣ Verificando estado del módem...")
        
        status_commands = [
            ("AT+CREG?", "Registro de red"),
            ("AT+COPS?", "Operador"),
            ("AT+CSQ", "Calidad de señal"),
            ("AT+CPBS?", "Phonebook seleccionado"),
        ]
        
        for cmd, desc in status_commands:
            try:
                response = await engine._send_command(cmd)
                print(f"📊 {desc}: {response.strip()}")
            except Exception as e:
                print(f"❌ {desc}: {e}")
        
    finally:
        await engine.disconnect()

async def alternative_send_method(engine, number, message):
    """Método alternativo de envío"""
    
    print("🔄 Método alternativo de envío...")
    
    try:
        # Limpiar buffer
        if engine.serial_connection.in_waiting > 0:
            engine.serial_connection.read(engine.serial_connection.in_waiting)
        
        # Método con timeout más largo
        engine.serial_connection.write(f'AT+CMGS="{number}"\r'.encode())
        
        # Esperar más tiempo por el prompt
        for i in range(10):  # 10 segundos
            await asyncio.sleep(1)
            if engine.serial_connection.in_waiting > 0:
                response = engine.serial_connection.read(engine.serial_connection.in_waiting).decode('utf-8', errors='ignore')
                print(f"📥 Respuesta {i+1}s: {repr(response)}")
                
                if ">" in response:
                    print("✅ Prompt encontrado con método alternativo!")
                    
                    # Enviar mensaje
                    engine.serial_connection.write((message + '\x1A').encode())
                    
                    # Esperar confirmación
                    await asyncio.sleep(3)
                    if engine.serial_connection.in_waiting > 0:
                        final = engine.serial_connection.read(engine.serial_connection.in_waiting).decode('utf-8', errors='ignore')
                        print(f"📥 Confirmación: {repr(final)}")
                    
                    return True
        
        print("❌ Método alternativo también falló")
        return False
        
    except Exception as e:
        print(f"❌ Error en método alternativo: {e}")
        return False

async def fix_and_test():
    """Arregla la configuración y prueba envío"""
    
    print("🔧 === REPARACIÓN Y PRUEBA ===\n")
    
    engine = SMSEngine()
    await engine.connect()
    
    try:
        # Configuración óptima paso a paso
        print("⚙️ Aplicando configuración óptima...")
        
        configs = [
            ("AT+CMGF=1", "Modo texto"),
            ('AT+CSCS="GSM"', "Codificación GSM"),
            ('AT+CSCA="+51997990000"', "SMSC Claro"),
            ("AT+CSMP=17,167,0,0", "Parámetros SMS"),
            ("AT+CNMI=1,1,0,0,0", "Notificaciones"),
        ]
        
        for cmd, desc in configs:
            try:
                response = await engine._send_command(cmd)
                print(f"✅ {desc}: OK")
            except Exception as e:
                print(f"⚠️ {desc}: {e}")
        
        print()
        
        # Test de envío mejorado
        print("📤 Test de envío con configuración mejorada...")
        
        # Usar el motor original pero con timeout más largo
        result = await engine.send_sms("946467799", "Test reparado " + time.strftime('%H:%M:%S'))
        
        if result.success:
            print(f"✅ ¡Envío exitoso!")
            print(f"🔢 Referencia: {result.reference_id}")
        else:
            print(f"❌ Error: {result.error_message}")
        
    finally:
        await engine.disconnect()

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "fix":
        asyncio.run(fix_and_test())
    else:
        asyncio.run(diagnose_sms_sending())
