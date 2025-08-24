"""
API REST simplificada para el SMS Gateway
"""
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from typing import List, Optional
from datetime import datetime
import logging
import asyncio

from config import settings
from database import create_tables, get_db_sync
from models import SMSMessage, Device, MessageStatus, MessageType
from sms_engine import sms_engine
from pydantic import BaseModel

# Configurar logging
logging.basicConfig(level=getattr(logging, settings.LOG_LEVEL))
logger = logging.getLogger(__name__)

# Modelos Pydantic para la API
class SMSRequest(BaseModel):
    phone_number: str
    message: str
    message_type: str = "command"

class SMSResponse(BaseModel):
    id: int
    phone_number: str
    message: str
    status: str
    reference_id: Optional[str] = None
    created_at: datetime
    sent_at: Optional[datetime] = None

class DeviceCreate(BaseModel):
    phone_number: str
    name: str
    description: Optional[str] = None
    device_type: Optional[str] = None

class DeviceResponse(BaseModel):
    id: int
    phone_number: str
    name: str
    description: Optional[str] = None
    is_active: bool
    last_seen: Optional[datetime] = None
    created_at: datetime

class NetworkInfo(BaseModel):
    network_status: Optional[str] = None
    operator: Optional[str] = None
    signal_strength: Optional[int] = None
    lac: Optional[str] = None
    cell_id: Optional[str] = None
    smsc: Optional[str] = None

# Crear aplicación FastAPI
app = FastAPI(
    title="SMS Gateway API",
    description="API para gestión de SMS a través de gateway Huawei E8278",
    version="1.0.0"
)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup_event():
    """Inicialización al arrancar la aplicación"""
    logger.info("🚀 Iniciando SMS Gateway API")
    
    # Crear tablas de base de datos
    try:
        create_tables()
        logger.info("✅ Base de datos inicializada")
    except Exception as e:
        logger.error(f"❌ Error en base de datos: {e}")
    
    # Conectar al gateway SMS
    try:
        if await sms_engine.connect():
            logger.info("✅ Gateway SMS conectado")
        else:
            logger.warning("⚠️ No se pudo conectar al gateway SMS")
    except Exception as e:
        logger.error(f"❌ Error conectando gateway: {e}")

@app.on_event("shutdown")
async def shutdown_event():
    """Limpieza al cerrar la aplicación"""
    logger.info("🔌 Cerrando SMS Gateway API")
    try:
        await sms_engine.disconnect()
    except Exception as e:
        logger.error(f"Error cerrando gateway: {e}")

@app.get("/", response_class=HTMLResponse)
async def root():
    """Página principal con información del gateway"""
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>SMS Gateway</title>
        <meta charset="UTF-8">
        <style>
            body { font-family: Arial, sans-serif; margin: 40px; background: #f5f5f5; }
            .container { max-width: 800px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
            .status { padding: 15px; border-radius: 8px; margin: 15px 0; }
            .connected { background-color: #d4edda; color: #155724; border: 1px solid #c3e6cb; }
            .disconnected { background-color: #f8d7da; color: #721c24; border: 1px solid #f5c6cb; }
            .info { background-color: #d1ecf1; color: #0c5460; border: 1px solid #bee5eb; padding: 15px; border-radius: 8px; margin: 15px 0; }
            h1 { color: #333; text-align: center; }
            h3 { color: #0c5460; }
            ul { list-style-type: none; padding: 0; }
            li { margin: 8px 0; }
            a { color: #007bff; text-decoration: none; }
            a:hover { text-decoration: underline; }
            .endpoint { background: #f8f9fa; padding: 10px; border-left: 4px solid #007bff; margin: 5px 0; }
            .badge { display: inline-block; padding: 4px 8px; background: #007bff; color: white; border-radius: 12px; font-size: 12px; margin-left: 10px; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🚀 SMS Gateway API</h1>
            <div class="status connected">
                ✅ Sistema Operativo
            </div>
            <div class="info">
                <h3>📡 Información del Sistema</h3>
                <p><strong>Dispositivo:</strong> Huawei E8278 HiLink</p>
                <p><strong>Puerto:</strong> /dev/ttyUSB0 @ 9600 bps</p>
                <p><strong>Operador:</strong> Claro Perú</p>
                <p><strong>SMSC:</strong> +51997990000</p>
                <p><strong>Servidor:</strong> http://localhost:8000</p>
            </div>
            <div class="info">
                <h3>🔗 Endpoints Disponibles</h3>
                <div class="endpoint">
                    <a href="/docs">📚 Documentación Swagger</a>
                    <span class="badge">Interactive</span>
                </div>
                <div class="endpoint">
                    <a href="/status">📊 Estado del Gateway</a>
                    <span class="badge">JSON</span>
                </div>
                <div class="endpoint">
                    <a href="/messages">📨 Lista de Mensajes</a>
                    <span class="badge">JSON</span>
                </div>
                <div class="endpoint">
                    <a href="/devices">📱 Dispositivos Registrados</a>
                    <span class="badge">JSON</span>
                </div>
                <div class="endpoint">
                    <a href="/network-info">🌐 Información de Red</a>
                    <span class="badge">JSON</span>
                </div>
            </div>
            <div class="info">
                <h3>📋 Ejemplo de Uso</h3>
                <p><strong>Enviar SMS via POST:</strong></p>
                <pre style="background: #f8f9fa; padding: 10px; border-radius: 4px; overflow-x: auto;">
curl -X POST "http://localhost:8000/send-sms" \\
     -H "Content-Type: application/json" \\
     -d '{
       "phone_number": "913044047",
       "message": "Comando de prueba",
       "message_type": "command"
     }'</pre>
            </div>
        </div>
    </body>
    </html>
    """
    return html_content

@app.get("/status")
async def gateway_status():
    """Estado del gateway SMS"""
    try:
        network_info = {}
        if sms_engine.is_connected:
            network_info = await sms_engine.get_network_info()
        
        return {
            "connected": sms_engine.is_connected,
            "timestamp": datetime.now(),
            "network": network_info,
            "port": settings.SERIAL_PORT,
            "baudrate": settings.SERIAL_BAUDRATE
        }
    except Exception as e:
        logger.error(f"Error obteniendo status: {e}")
        return {
            "connected": False,
            "error": str(e),
            "timestamp": datetime.now()
        }

@app.post("/send-sms")
async def send_sms(sms_request: SMSRequest, background_tasks: BackgroundTasks):
    """Envía un SMS"""
    try:
        # Crear registro en base de datos
        db = get_db_sync()
        db_message = SMSMessage(
            phone_number=sms_request.phone_number,
            message=sms_request.message,
            message_type=MessageType.COMMAND if sms_request.message_type == "command" else MessageType.NOTIFICATION,
            status=MessageStatus.PENDING
        )
        db.add(db_message)
        db.commit()
        db.refresh(db_message)
        db.close()
        
        # Programar envío en background
        background_tasks.add_task(
            process_sms_sending,
            db_message.id,
            sms_request.phone_number,
            sms_request.message
        )
        
        return {
            "id": db_message.id,
            "phone_number": db_message.phone_number,
            "message": db_message.message,
            "status": db_message.status.value,
            "created_at": db_message.created_at
        }
        
    except Exception as e:
        logger.error(f"Error en send_sms: {e}")
        raise HTTPException(status_code=500, detail=str(e))

async def process_sms_sending(message_id: int, phone_number: str, message: str):
    """Procesa el envío de SMS en background"""
    db = get_db_sync()
    try:
        # Obtener mensaje de la base de datos
        db_message = db.query(SMSMessage).filter(SMSMessage.id == message_id).first()
        if not db_message:
            return
        
        # Actualizar estado a SENDING
        db_message.status = MessageStatus.SENDING
        db.commit()
        
        # Conectar si no está conectado
        if not sms_engine.is_connected:
            await sms_engine.connect()
        
        # Enviar SMS
        result = await sms_engine.send_sms(phone_number, message)
        
        if result.success:
            db_message.status = MessageStatus.SENT
            db_message.reference_id = result.reference_id
            db_message.sent_at = datetime.now()
            logger.info(f"✅ SMS {message_id} enviado exitosamente")
        else:
            db_message.status = MessageStatus.FAILED
            db_message.error_message = result.error_message
            db_message.retries += 1
            logger.error(f"❌ SMS {message_id} falló: {result.error_message}")
        
        db.commit()
        
    except Exception as e:
        logger.error(f"Error procesando envío de SMS {message_id}: {e}")
        if db_message:
            db_message.status = MessageStatus.FAILED
            db_message.error_message = str(e)
            db.commit()
    finally:
        db.close()

@app.get("/messages")
async def get_messages(
    status: Optional[str] = None,
    phone_number: Optional[str] = None,
    limit: int = 50
):
    """Obtiene lista de mensajes"""
    try:
        db = get_db_sync()
        query = db.query(SMSMessage)
        
        if status:
            # Convertir string a enum
            try:
                status_enum = MessageStatus(status)
                query = query.filter(SMSMessage.status == status_enum)
            except ValueError:
                db.close()
                raise HTTPException(status_code=400, detail=f"Estado inválido: {status}")
        
        if phone_number:
            query = query.filter(SMSMessage.phone_number == phone_number)
        
        messages = query.order_by(SMSMessage.created_at.desc()).limit(limit).all()
        
        result = []
        for msg in messages:
            result.append({
                "id": msg.id,
                "phone_number": msg.phone_number,
                "message": msg.message,
                "status": msg.status.value,
                "reference_id": msg.reference_id,
                "created_at": msg.created_at,
                "sent_at": msg.sent_at,
                "error_message": msg.error_message
            })
        
        db.close()
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error obteniendo mensajes: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/messages/{message_id}")
async def get_message(message_id: int):
    """Obtiene un mensaje específico"""
    try:
        db = get_db_sync()
        message = db.query(SMSMessage).filter(SMSMessage.id == message_id).first()
        
        if not message:
            db.close()
            raise HTTPException(status_code=404, detail="Mensaje no encontrado")
        
        result = {
            "id": message.id,
            "phone_number": message.phone_number,
            "message": message.message,
            "status": message.status.value,
            "reference_id": message.reference_id,
            "created_at": message.created_at,
            "sent_at": message.sent_at,
            "error_message": message.error_message
        }
        
        db.close()
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error obteniendo mensaje {message_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/network-info")
async def get_network_info():
    """Obtiene información de la red móvil"""
    try:
        if not sms_engine.is_connected:
            # Intentar conectar
            if not await sms_engine.connect():
                raise HTTPException(status_code=503, detail="Gateway no conectado")
        
        info = await sms_engine.get_network_info()
        return info
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error obteniendo info de red: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/devices")
async def create_device(device: DeviceCreate):
    """Registra un nuevo dispositivo"""
    try:
        db = get_db_sync()
        
        # Verificar si ya existe
        existing = db.query(Device).filter(Device.phone_number == device.phone_number).first()
        if existing:
            db.close()
            raise HTTPException(status_code=400, detail="Dispositivo ya registrado")
        
        db_device = Device(
            phone_number=device.phone_number,
            name=device.name,
            description=device.description,
            device_type=device.device_type
        )
        db.add(db_device)
        db.commit()
        db.refresh(db_device)
        
        result = {
            "id": db_device.id,
            "phone_number": db_device.phone_number,
            "name": db_device.name,
            "description": db_device.description,
            "is_active": db_device.is_active,
            "last_seen": db_device.last_seen,
            "created_at": db_device.created_at
        }
        
        db.close()
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creando dispositivo: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/devices")
async def get_devices(active_only: bool = True):
    """Obtiene lista de dispositivos"""
    try:
        db = get_db_sync()
        query = db.query(Device)
        
        if active_only:
            query = query.filter(Device.is_active == True)
        
        devices = query.order_by(Device.name).all()
        
        result = []
        for device in devices:
            result.append({
                "id": device.id,
                "phone_number": device.phone_number,
                "name": device.name,
                "description": device.description,
                "is_active": device.is_active,
                "last_seen": device.last_seen,
                "created_at": device.created_at
            })
        
        db.close()
        return result
        
    except Exception as e:
        logger.error(f"Error obteniendo dispositivos: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main_simple:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG
    )
