"""
Test Completo del SMS Gateway Avanzado
Prueba todas las funciones: envío, recepción, estados y respuestas
"""
import asyncio
import time
from advanced_sms_engine import advanced_sms_engine, print_status_summary

async def test_complete_workflow():
    """Prueba completa del flujo de trabajo"""
    print("🧪 === TEST COMPLETO SMS GATEWAY AVANZADO ===\n")
    
    try:
        # 1. Conectar al gateway
        print("1️⃣ Conectando al gateway...")
        await advanced_sms_engine.connect()
        
        # Mostrar información del gateway
        network_info = await advanced_sms_engine.get_network_info()
        print(f"📡 Red: {network_info.get('operator', 'N/A')}")
        print(f"📶 Señal: {network_info.get('signal_strength', 'N/A')}")
        print()
        
        # 2. Iniciar monitoreo
        print("2️⃣ Iniciando monitoreo de mensajes...")
        await advanced_sms_engine.start_message_monitoring()
        print("🔔 Monitoreo activo - Los mensajes entrantes se procesarán automáticamente\n")
        
        # 3. Verificar mensajes almacenados
        print("3️⃣ Verificando mensajes almacenados en el gateway...")
        stored_messages = await advanced_sms_engine.check_stored_messages()
        print(f"📋 Mensajes almacenados: {len(stored_messages)}")
        
        for msg in stored_messages:
            print(f"   📨 De {msg['sender']}: {msg['message'][:50]}...")
        print()
        
        # 4. Enviar mensaje de prueba con tracking
        print("4️⃣ Enviando mensaje de prueba con tracking completo...")
        test_message = "🧪 TEST AVANZADO: Responde 'OK' para confirmar recepción"
        
        status = await advanced_sms_engine.send_sms_with_tracking(
            phone_number="913044047",
            message=test_message,
            message_id="test_advanced_001"
        )
        
        print(f"📤 Mensaje enviado:")
        print(f"   🆔 ID: {status.message_id}")
        print(f"   📱 Para: {status.phone_number}")
        print(f"   📋 Estado: {status.status}")
        print(f"   🔢 Referencia: {status.operator_reference}")
        print()
        
        # 5. Enviar segundo mensaje para probar múltiples envíos
        print("5️⃣ Enviando segundo mensaje...")
        status2 = await advanced_sms_engine.send_sms_with_tracking(
            phone_number="913044047",
            message="Mensaje #2 - Estado de conexión",
            message_id="test_advanced_002"
        )
        print(f"📤 Segundo mensaje enviado (ID: {status2.message_id})\n")
        
        # 6. Monitorear por respuestas
        print("6️⃣ Monitoreando respuestas por 45 segundos...")
        print("💡 Envía una respuesta a 913044047 para ver el tracking en acción")
        
        for i in range(9):  # 45 segundos en intervalos de 5
            await asyncio.sleep(5)
            
            # Mostrar progreso
            remaining = 45 - (i + 1) * 5
            print(f"⏳ Tiempo restante: {remaining}s")
            
            # Verificar estados cada 15 segundos
            if (i + 1) % 3 == 0:
                print("\n📊 === ESTADO ACTUAL ===")
                
                # Estados de mensajes enviados
                all_statuses = await advanced_sms_engine.get_all_statuses()
                for msg_status in all_statuses:
                    emoji = "✅" if msg_status.status == "delivered" else "📤" if msg_status.status == "sent" else "⏳"
                    print(f"{emoji} {msg_status.message_id}: {msg_status.status}")
                    if msg_status.response_message:
                        print(f"   💬 Respuesta: {msg_status.response_message}")
                
                # Mensajes recibidos
                received = await advanced_sms_engine.get_received_messages()
                print(f"\n📥 Mensajes recibidos: {len(received)}")
                for msg in received[-3:]:  # Últimos 3
                    indicator = "↩️" if msg.is_response else "📨"
                    print(f"   {indicator} {msg.phone_number}: {msg.message}")
                
                print("=" * 40 + "\n")
        
        # 7. Resumen final
        print("7️⃣ Resumen final del test:")
        print_status_summary()
        
        # 8. Estadísticas detalladas
        print("\n8️⃣ Estadísticas detalladas:")
        
        all_statuses = await advanced_sms_engine.get_all_statuses()
        received_messages = await advanced_sms_engine.get_received_messages()
        
        # Contar por estado
        status_counts = {}
        for status in all_statuses:
            status_counts[status.status] = status_counts.get(status.status, 0) + 1
        
        print(f"📊 Estados de mensajes enviados:")
        for state, count in status_counts.items():
            emoji = {"pending": "⏳", "sent": "📤", "delivered": "✅", "failed": "❌", "response_received": "💬"}
            print(f"   {emoji.get(state, '📋')} {state}: {count}")
        
        print(f"\n📥 Mensajes recibidos:")
        print(f"   📨 Total: {len(received_messages)}")
        print(f"   ↩️ Respuestas: {len([m for m in received_messages if m.is_response])}")
        print(f"   📩 Nuevos: {len([m for m in received_messages if not m.is_response])}")
        
        # 9. Test de consulta específica
        print("\n9️⃣ Test de consulta específica:")
        specific_status = await advanced_sms_engine.get_message_status("test_advanced_001")
        if specific_status:
            print(f"🔍 Estado del mensaje test_advanced_001:")
            print(f"   📋 Estado: {specific_status.status}")
            print(f"   📅 Enviado: {specific_status.sent_time}")
            if specific_status.response_message:
                print(f"   💬 Respuesta: {specific_status.response_message}")
        
        print("\n✅ Test completo finalizado con éxito!")
        
    except Exception as e:
        print(f"❌ Error durante el test: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Limpiar
        print("\n🧹 Limpiando recursos...")
        await advanced_sms_engine.stop_monitoring()
        await advanced_sms_engine.disconnect()
        print("✅ Recursos liberados")

async def test_quick_send():
    """Test rápido de envío"""
    print("⚡ === TEST RÁPIDO DE ENVÍO ===")
    
    try:
        await advanced_sms_engine.connect()
        
        status = await advanced_sms_engine.send_sms_with_tracking(
            "913044047",
            "Test rápido - " + str(int(time.time())),
            f"quick_{int(time.time())}"
        )
        
        print(f"✅ Enviado: {status.message_id} -> {status.status}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
    
    finally:
        await advanced_sms_engine.disconnect()

async def test_reception_only():
    """Test solo de recepción"""
    print("📥 === TEST SOLO RECEPCIÓN ===")
    
    try:
        await advanced_sms_engine.connect()
        await advanced_sms_engine.start_message_monitoring()
        
        print("🔔 Monitoreo activo por 30 segundos...")
        print("📱 Envía un SMS al gateway para probar la recepción")
        
        await asyncio.sleep(30)
        
        received = await advanced_sms_engine.get_received_messages()
        print(f"📥 Mensajes recibidos durante el test: {len(received)}")
        
        for msg in received:
            print(f"   📨 {msg.phone_number}: {msg.message}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
    
    finally:
        await advanced_sms_engine.stop_monitoring()
        await advanced_sms_engine.disconnect()

def menu():
    """Menú interactivo"""
    print("🧪 === MENU DE PRUEBAS SMS GATEWAY AVANZADO ===")
    print("1. Test completo (envío + recepción + estados)")
    print("2. Test rápido de envío")
    print("3. Test solo recepción")
    print("4. Salir")
    
    while True:
        try:
            choice = input("\n🔢 Selecciona una opción (1-4): ").strip()
            
            if choice == "1":
                asyncio.run(test_complete_workflow())
            elif choice == "2":
                asyncio.run(test_quick_send())
            elif choice == "3":
                asyncio.run(test_reception_only())
            elif choice == "4":
                print("👋 ¡Hasta luego!")
                break
            else:
                print("❌ Opción inválida")
                
        except KeyboardInterrupt:
            print("\n\n⏹️ Test interrumpido por el usuario")
            break
        except Exception as e:
            print(f"❌ Error: {e}")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "complete":
            asyncio.run(test_complete_workflow())
        elif sys.argv[1] == "quick":
            asyncio.run(test_quick_send())
        elif sys.argv[1] == "reception":
            asyncio.run(test_reception_only())
        else:
            print("Uso: python test_advanced.py [complete|quick|reception]")
    else:
        menu()
