"""
Solucionador de Recepción SMS - Diferentes Configuraciones
Prueba varias configuraciones para encontrar la que funciona
"""
import asyncio
from sms_engine_ultra_simple import SMSEngine

class ReceptionTester:
    def __init__(self):
        self.engine = SMSEngine()
    
    async def test_cnmi_configurations(self):
        """Prueba diferentes configuraciones CNMI"""
        
        configurations = [
            ("2,2,0,0,0", "Notificación directa completa"),
            ("1,1,0,0,0", "Notificación básica"),
            ("2,1,0,0,0", "Almacenar y notificar"),
            ("1,2,0,0,0", "Mostrar directamente"),
            ("0,0,0,0,0", "Sin notificaciones automáticas"),
            ("2,0,0,0,0", "Solo almacenar"),
        ]
        
        print("🧪 === PROBANDO CONFIGURACIONES DE RECEPCIÓN ===\n")
        
        await self.engine.connect()
        
        for config, description in configurations:
            print(f"🔧 Probando: AT+CNMI={config}")
            print(f"📝 Descripción: {description}")
            
            try:
                response = await self.engine._send_command(f"AT+CNMI={config}")
                print(f"✅ Éxito: {response.strip()}")
                
                # Verificar configuración actual
                current = await self.engine._send_command("AT+CNMI?")
                print(f"📋 Configuración actual: {current.strip()}")
                
            except Exception as e:
                print(f"❌ Error: {e}")
            
            print("-" * 50)
        
        await self.engine.disconnect()
    
    async def test_manual_check(self):
        """Método manual para verificar mensajes"""
        print("📥 === VERIFICACIÓN MANUAL DE MENSAJES ===\n")
        
        await self.engine.connect()
        
        try:
            # Verificar mensajes en diferentes ubicaciones
            locations = ["SM", "ME", "MT"]
            
            for location in locations:
                print(f"🔍 Verificando ubicación: {location}")
                
                try:
                    # Seleccionar ubicación
                    await self.engine._send_command(f'AT+CPMS="{location}"')
                    
                    # Listar mensajes
                    response = await self.engine._send_command('AT+CMGL="ALL"')
                    print(f"📋 Respuesta: {response}")
                    
                    # Contar mensajes
                    lines = response.split('\n')
                    message_count = len([line for line in lines if line.startswith('+CMGL:')])
                    print(f"📊 Mensajes encontrados: {message_count}")
                    
                except Exception as e:
                    print(f"❌ Error en {location}: {e}")
                
                print("-" * 30)
        
        finally:
            await self.engine.disconnect()
    
    async def setup_polling_mode(self):
        """Configura modo de polling manual"""
        print("⚙️ === CONFIGURANDO MODO POLLING ===\n")
        
        await self.engine.connect()
        
        try:
            # Desactivar notificaciones automáticas
            print("🔇 Desactivando notificaciones automáticas...")
            await self.engine._send_command("AT+CNMI=0,0,0,0,0")
            
            # Configurar almacenamiento en memoria
            print("💾 Configurando almacenamiento...")
            await self.engine._send_command('AT+CPMS="ME","ME","ME"')
            
            # Verificar configuración
            config = await self.engine._send_command("AT+CNMI?")
            storage = await self.engine._send_command("AT+CPMS?")
            
            print(f"✅ Configuración CNMI: {config.strip()}")
            print(f"✅ Configuración almacenamiento: {storage.strip()}")
            
            print("\n🔄 Modo polling configurado correctamente")
            print("💡 Ahora el sistema verificará mensajes cada pocos segundos")
            
        except Exception as e:
            print(f"❌ Error configurando polling: {e}")
        
        finally:
            await self.engine.disconnect()

async def main():
    tester = ReceptionTester()
    
    print("🔧 === DIAGNÓSTICO DE RECEPCIÓN SMS ===")
    print("Vamos a encontrar la configuración correcta para tu gateway\n")
    
    # 1. Probar configuraciones CNMI
    await tester.test_cnmi_configurations()
    
    input("\n⏸️ Presiona Enter para continuar con verificación manual...")
    
    # 2. Verificación manual
    await tester.test_manual_check()
    
    input("\n⏸️ Presiona Enter para configurar modo polling...")
    
    # 3. Configurar polling
    await tester.setup_polling_mode()
    
    print("\n✅ Diagnóstico completado!")

if __name__ == "__main__":
    asyncio.run(main())
