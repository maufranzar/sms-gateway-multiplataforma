"""
Configuración del SMS Gateway
"""
import os
from pydantic import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # Configuración del puerto serie
    SERIAL_PORT: str = "/dev/ttyUSB0"
    SERIAL_BAUDRATE: int = 9600
    SERIAL_TIMEOUT: int = 10
    
    # Configuración de la base de datos
    DATABASE_URL: str = "sqlite:///./sms_gateway.db"
    
    # Configuración del servidor
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    DEBUG: bool = True
    
    # Configuración SMS
    SMS_MODE: str = "AT"  # AT o GAMMU
    DEFAULT_SMSC: str = "+51997990000"
    MAX_RETRIES: int = 3
    RETRY_DELAY: int = 30  # segundos
    
    # Configuración de logs
    LOG_LEVEL: str = "INFO"
    LOG_FILE: str = "sms_gateway.log"
    
    class Config:
        env_file = ".env"

# Instancia global de configuración
settings = Settings()
