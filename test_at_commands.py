#!/usr/bin/env python3
"""
Script de prueba para comandos AT con el gateway SMS Huawei E8278
"""

import serial
import time
import sys

def send_at_command(ser, command, wait_time=2):
    """Envía un comando AT y espera la respuesta"""
    print(f"Enviando: {command}")
    ser.write(f"{command}\r\n".encode())
    time.sleep(wait_time)
    
    response = ""
    while ser.in_waiting:
        response += ser.read(ser.in_waiting).decode('utf-8', errors='ignore')
        time.sleep(0.1)
    
    print(f"Respuesta: {response.strip()}")
    return response

def test_sms_at(phone_number, message):
    """Prueba de envío de SMS usando comandos AT"""
    try:
        # Abrir conexión serial
        ser = serial.Serial('/dev/ttyUSB0', 9600, timeout=10)
        print("Conexión establecida con /dev/ttyUSB0")
        
        # Esperar un momento para la inicialización
        time.sleep(2)
        
        # Verificar comunicación básica
        send_at_command(ser, "AT")
        
        # Verificar estado de la SIM
        send_at_command(ser, "AT+CPIN?")
        
        # Verificar registro en red
        send_at_command(ser, "AT+CREG?")
        
        # Verificar configuración SMSC
        send_at_command(ser, "AT+CSCA?")
        
        # Configurar modo texto para SMS
        send_at_command(ser, "AT+CMGF=1")
        
        # Enviar SMS
        print(f"\n=== Enviando SMS a {phone_number} ===")
        send_at_command(ser, f'AT+CMGS="{phone_number}"')
        
        # Enviar el texto del mensaje seguido de Ctrl+Z
        print(f"Enviando mensaje: {message}")
        ser.write(f"{message}".encode())
        ser.write(bytes([26]))  # Ctrl+Z
        
        # Esperar respuesta del envío
        time.sleep(5)
        response = ""
        while ser.in_waiting:
            response += ser.read(ser.in_waiting).decode('utf-8', errors='ignore')
            time.sleep(0.1)
        
        print(f"Respuesta del envío: {response.strip()}")
        
        ser.close()
        print("Conexión cerrada")
        
    except Exception as e:
        print(f"Error: {e}")
        return False
    
    return True

if __name__ == "__main__":
    phone = "913044047"
    message = f"Prueba AT Commands - {time.strftime('%H:%M:%S')}"
    
    print("=== Prueba de comandos AT para SMS ===")
    test_sms_at(phone, message)
