"""
Modelos de base de datos para el SMS Gateway
"""
from sqlalchemy import Column, Integer, String, DateTime, Text, Enum as SQLEnum, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
from enum import Enum
from datetime import datetime

Base = declarative_base()

class MessageStatus(str, Enum):
    PENDING = "pending"
    SENDING = "sending"
    SENT = "sent"
    DELIVERED = "delivered"
    FAILED = "failed"
    EXPIRED = "expired"

class MessageType(str, Enum):
    COMMAND = "command"
    RESPONSE = "response"
    NOTIFICATION = "notification"

class SMSMessage(Base):
    __tablename__ = "sms_messages"
    
    id = Column(Integer, primary_key=True, index=True)
    phone_number = Column(String(20), nullable=False, index=True)
    message = Column(Text, nullable=False)
    message_type = Column(SQLEnum(MessageType), default=MessageType.COMMAND)
    status = Column(SQLEnum(MessageStatus), default=MessageStatus.PENDING, index=True)
    
    # Información de envío
    reference_id = Column(String(50), nullable=True, index=True)  # AT command reference
    method = Column(String(10), default="AT")  # AT o GAMMU
    retries = Column(Integer, default=0)
    max_retries = Column(Integer, default=3)
    
    # Timestamps
    created_at = Column(DateTime, default=func.now())
    sent_at = Column(DateTime, nullable=True)
    delivered_at = Column(DateTime, nullable=True)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Información adicional
    error_message = Column(Text, nullable=True)
    response_message = Column(Text, nullable=True)
    device_info = Column(Text, nullable=True)
    
    def __repr__(self):
        return f"<SMSMessage(id={self.id}, phone={self.phone_number}, status={self.status})>"

class Device(Base):
    __tablename__ = "devices"
    
    id = Column(Integer, primary_key=True, index=True)
    phone_number = Column(String(20), unique=True, nullable=False, index=True)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True)
    
    # Información del dispositivo
    last_seen = Column(DateTime, nullable=True)
    last_response = Column(Text, nullable=True)
    device_type = Column(String(50), nullable=True)
    firmware_version = Column(String(50), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    def __repr__(self):
        return f"<Device(id={self.id}, name={self.name}, phone={self.phone_number})>"

class SystemLog(Base):
    __tablename__ = "system_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    level = Column(String(20), nullable=False, index=True)  # INFO, WARNING, ERROR
    message = Column(Text, nullable=False)
    component = Column(String(50), nullable=False, index=True)  # SMS_ENGINE, API, DATABASE
    details = Column(Text, nullable=True)
    
    created_at = Column(DateTime, default=func.now())
    
    def __repr__(self):
        return f"<SystemLog(id={self.id}, level={self.level}, component={self.component})>"
