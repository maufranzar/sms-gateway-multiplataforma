"""
API REST para el SMS Gateway
"""
from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
import logging

from config import settings
from database import get_db, create_tables
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
    message_type: MessageType = MessageType.COMMAND

class SMSResponse(BaseModel):
    id: int
    phone_number: str
    message: str
    status: MessageStatus
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
    logger.info("Iniciando SMS Gateway API")
    
    # Crear tablas de base de datos
    create_tables()
    
    # Conectar al gateway SMS
    if not await sms_engine.connect():
        logger.error("No se pudo conectar al gateway SMS")
    else:
        logger.info("Gateway SMS conectado exitosamente")

@app.on_event("shutdown")
async def shutdown_event():
    """Limpieza al cerrar la aplicación"""
    logger.info("Cerrando SMS Gateway API")
    await sms_engine.disconnect()

@app.get("/", response_class=HTMLResponse)
async def root():
    """Página principal con información del gateway"""
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>SMS Gateway</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 40px; }
            .status { padding: 10px; border-radius: 5px; margin: 10px 0; }
            .connected { background-color: #d4edda; color: #155724; }
            .disconnected { background-color: #f8d7da; color: #721c24; }
            .info { background-color: #d1ecf1; color: #0c5460; }
        </style>
    </head>
    <body>
        <h1>🚀 SMS Gateway API</h1>
        <div class="status connected" id="status">
            ✅ Gateway Conectado
        </div>
        <div class="info">
            <h3>📡 Información del Sistema</h3>
            <p><strong>Dispositivo:</strong> Huawei E8278</p>
            <p><strong>Puerto:</strong> /dev/ttyUSB0</p>
            <p><strong>Operador:</strong> Claro Perú</p>
        </div>
        <div class="info">
            <h3>🔗 Endpoints Disponibles</h3>
            <ul>
                <li><a href="/docs">📚 Documentación Swagger</a></li>
                <li><a href="/status">📊 Estado del Gateway</a></li>
                <li><a href="/messages">📨 Lista de Mensajes</a></li>
                <li><a href="/devices">📱 Dispositivos Registrados</a></li>
            </ul>
        </div>
    </body>
    </html>
    """
    return html_content

@app.get("/status")
async def gateway_status():
    """Estado del gateway SMS"""
    network_info = await sms_engine.get_network_info()
    
    return {
        "connected": sms_engine.is_connected,
        "timestamp": datetime.now(),
        "network": network_info
    }

@app.post("/send-sms", response_model=SMSResponse)
async def send_sms(
    sms_request: SMSRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Envía un SMS"""
    
    # Crear registro en base de datos
    db_message = SMSMessage(
        phone_number=sms_request.phone_number,
        message=sms_request.message,
        message_type=sms_request.message_type,
        status=MessageStatus.PENDING
    )
    db.add(db_message)
    db.commit()
    db.refresh(db_message)
    
    # Programar envío en background
    background_tasks.add_task(
        process_sms_sending,
        db_message.id,
        sms_request.phone_number,
        sms_request.message
    )
    
    return SMSResponse(
        id=db_message.id,
        phone_number=db_message.phone_number,
        message=db_message.message,
        status=db_message.status,
        created_at=db_message.created_at
    )

async def process_sms_sending(message_id: int, phone_number: str, message: str):
    """Procesa el envío de SMS en background"""
    db = SessionLocal()
    try:
        # Obtener mensaje de la base de datos
        db_message = db.query(SMSMessage).filter(SMSMessage.id == message_id).first()
        if not db_message:
            return
        
        # Actualizar estado a SENDING
        db_message.status = MessageStatus.SENDING
        db.commit()
        
        # Enviar SMS
        result = await sms_engine.send_sms(phone_number, message)
        
        if result.success:
            db_message.status = MessageStatus.SENT
            db_message.reference_id = result.reference_id
            db_message.sent_at = datetime.now()
        else:
            db_message.status = MessageStatus.FAILED
            db_message.error_message = result.error_message
            db_message.retries += 1
        
        db.commit()
        
    except Exception as e:
        logger.error(f"Error procesando envío de SMS {message_id}: {e}")
        if db_message:
            db_message.status = MessageStatus.FAILED
            db_message.error_message = str(e)
            db.commit()
    finally:
        db.close()

@app.get("/messages", response_model=List[SMSResponse])
async def get_messages(
    status: Optional[MessageStatus] = None,
    phone_number: Optional[str] = None,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """Obtiene lista de mensajes"""
    
    query = db.query(SMSMessage)
    
    if status:
        query = query.filter(SMSMessage.status == status)
    
    if phone_number:
        query = query.filter(SMSMessage.phone_number == phone_number)
    
    messages = query.order_by(SMSMessage.created_at.desc()).limit(limit).all()
    
    return [
        SMSResponse(
            id=msg.id,
            phone_number=msg.phone_number,
            message=msg.message,
            status=msg.status,
            reference_id=msg.reference_id,
            created_at=msg.created_at,
            sent_at=msg.sent_at
        )
        for msg in messages
    ]

@app.get("/messages/{message_id}", response_model=SMSResponse)
async def get_message(message_id: int, db: Session = Depends(get_db)):
    """Obtiene un mensaje específico"""
    
    message = db.query(SMSMessage).filter(SMSMessage.id == message_id).first()
    if not message:
        raise HTTPException(status_code=404, detail="Mensaje no encontrado")
    
    return SMSResponse(
        id=message.id,
        phone_number=message.phone_number,
        message=message.message,
        status=message.status,
        reference_id=message.reference_id,
        created_at=message.created_at,
        sent_at=message.sent_at
    )

@app.post("/devices", response_model=DeviceResponse)
async def create_device(device: DeviceCreate, db: Session = Depends(get_db)):
    """Registra un nuevo dispositivo"""
    
    # Verificar si ya existe
    existing = db.query(Device).filter(Device.phone_number == device.phone_number).first()
    if existing:
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
    
    return DeviceResponse(
        id=db_device.id,
        phone_number=db_device.phone_number,
        name=db_device.name,
        description=db_device.description,
        is_active=db_device.is_active,
        last_seen=db_device.last_seen,
        created_at=db_device.created_at
    )

@app.get("/devices", response_model=List[DeviceResponse])
async def get_devices(active_only: bool = True, db: Session = Depends(get_db)):
    """Obtiene lista de dispositivos"""
    
    query = db.query(Device)
    if active_only:
        query = query.filter(Device.is_active == True)
    
    devices = query.order_by(Device.name).all()
    
    return [
        DeviceResponse(
            id=device.id,
            phone_number=device.phone_number,
            name=device.name,
            description=device.description,
            is_active=device.is_active,
            last_seen=device.last_seen,
            created_at=device.created_at
        )
        for device in devices
    ]

@app.get("/network-info", response_model=NetworkInfo)
async def get_network_info():
    """Obtiene información de la red móvil"""
    
    if not sms_engine.is_connected:
        raise HTTPException(status_code=503, detail="Gateway no conectado")
    
    info = await sms_engine.get_network_info()
    return NetworkInfo(**info)

# Importar SessionLocal aquí para evitar circular imports
from database import SessionLocal

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG
    )
