#!/usr/bin/env python3
"""
Script de inicio para el SMS Gateway
"""
import click
import asyncio
import uvicorn
from rich.console import Console
from rich.table import Table
from rich import print as rprint

from config import settings
from database import create_tables, get_db_sync
from models import SMSMessage, Device, MessageStatus
from sms_engine import sms_engine

console = Console()

@click.group()
def cli():
    """🚀 SMS Gateway - Gestión de mensajes SMS"""
    pass

@cli.command()
def init():
    """Inicializa la base de datos"""
    console.print("🗄️  Inicializando base de datos...", style="yellow")
    try:
        create_tables()
        console.print("✅ Base de datos inicializada correctamente", style="green")
    except Exception as e:
        console.print(f"❌ Error inicializando base de datos: {e}", style="red")

@cli.command()
def start():
    """Inicia el servidor API"""
    console.print("🚀 Iniciando SMS Gateway API...", style="yellow")
    console.print(f"📡 Puerto serie: {settings.SERIAL_PORT}", style="blue")
    console.print(f"🌐 Servidor: http://{settings.HOST}:{settings.PORT}", style="blue")
    
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG
    )

@cli.command()
@click.argument('phone_number')
@click.argument('message')
def send(phone_number: str, message: str):
    """Envía un SMS desde línea de comandos"""
    async def _send():
        console.print(f"📤 Enviando SMS a {phone_number}...", style="yellow")
        
        try:
            if await sms_engine.connect():
                result = await sms_engine.send_sms(phone_number, message)
                
                if result.success:
                    console.print(f"✅ SMS enviado exitosamente", style="green")
                    console.print(f"📋 Referencia: {result.reference_id}", style="blue")
                else:
                    console.print(f"❌ Error enviando SMS: {result.error_message}", style="red")
                
                await sms_engine.disconnect()
            else:
                console.print("❌ No se pudo conectar al gateway", style="red")
                
        except Exception as e:
            console.print(f"❌ Error: {e}", style="red")
    
    asyncio.run(_send())

@cli.command()
def test():
    """Prueba la conexión con el gateway"""
    async def _test():
        console.print("🔧 Probando conexión con gateway...", style="yellow")
        
        try:
            if await sms_engine.connect():
                console.print("✅ Conexión establecida", style="green")
                
                # Obtener información de red
                network_info = await sms_engine.get_network_info()
                
                table = Table(title="📡 Información de Red")
                table.add_column("Parámetro", style="cyan")
                table.add_column("Valor", style="green")
                
                for key, value in network_info.items():
                    table.add_row(key.replace('_', ' ').title(), str(value) if value else "N/A")
                
                console.print(table)
                
                await sms_engine.disconnect()
            else:
                console.print("❌ No se pudo conectar al gateway", style="red")
                
        except Exception as e:
            console.print(f"❌ Error: {e}", style="red")
    
    asyncio.run(_test())

@cli.command()
def status():
    """Muestra el estado de mensajes en la base de datos"""
    console.print("📊 Estado de mensajes SMS", style="yellow")
    
    try:
        db = get_db_sync()
        
        # Contar mensajes por estado
        status_counts = {}
        for status in MessageStatus:
            count = db.query(SMSMessage).filter(SMSMessage.status == status).count()
            status_counts[status.value] = count
        
        table = Table(title="📈 Estadísticas de Mensajes")
        table.add_column("Estado", style="cyan")
        table.add_column("Cantidad", style="green")
        
        for status, count in status_counts.items():
            table.add_row(status.title(), str(count))
        
        console.print(table)
        
        # Mostrar últimos mensajes
        recent_messages = db.query(SMSMessage).order_by(
            SMSMessage.created_at.desc()
        ).limit(5).all()
        
        if recent_messages:
            table = Table(title="📨 Últimos Mensajes")
            table.add_column("ID", style="cyan")
            table.add_column("Teléfono", style="blue")
            table.add_column("Estado", style="green")
            table.add_column("Fecha", style="yellow")
            
            for msg in recent_messages:
                table.add_row(
                    str(msg.id),
                    msg.phone_number,
                    msg.status.value,
                    msg.created_at.strftime("%Y-%m-%d %H:%M:%S")
                )
            
            console.print(table)
        
        db.close()
        
    except Exception as e:
        console.print(f"❌ Error: {e}", style="red")

if __name__ == "__main__":
    cli()
