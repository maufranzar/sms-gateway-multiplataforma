#!/usr/bin/env python3
"""
Instalador Automático SMS Gateway Multiplataforma
Detecta el sistema operativo e instala dependencias automáticamente
"""
import os
import sys
import subprocess
import platform
import shutil
from pathlib import Path

def print_header():
    """Imprime cabecera del instalador"""
    print("🚀 === INSTALADOR SMS GATEWAY MULTIPLATAFORMA ===")
    print("📱 Instalador automático para Windows, Linux y macOS")
    print("🔧 Detectando sistema y configurando entorno...\n")

def detect_system():
    """Detecta el sistema operativo"""
    system = platform.system().lower()
    print(f"💻 Sistema detectado: {system.upper()}")
    return system

def check_python_version():
    """Verifica versión de Python"""
    version = sys.version_info
    print(f"🐍 Python detectado: {version.major}.{version.minor}.{version.micro}")
    
    if version.major < 3 or (version.major == 3 and version.minor < 7):
        print("❌ Error: Se requiere Python 3.7 o superior")
        sys.exit(1)
    
    print("✅ Versión de Python compatible")
    return True

def find_python_executable():
    """Encuentra el ejecutable de Python correcto"""
    candidates = ['python3', 'python', 'py']
    
    for candidate in candidates:
        try:
            result = subprocess.run([candidate, '--version'], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                version_line = result.stdout.strip()
                if '3.' in version_line:
                    print(f"🐍 Usando ejecutable: {candidate}")
                    return candidate
        except FileNotFoundError:
            continue
    
    print("❌ No se encontró un ejecutable Python válido")
    sys.exit(1)

def check_pip():
    """Verifica y obtiene pip"""
    python_exe = find_python_executable()
    
    try:
        result = subprocess.run([python_exe, '-m', 'pip', '--version'], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ pip encontrado")
            return python_exe
    except FileNotFoundError:
        pass
    
    # Intentar instalar pip
    print("📦 Instalando pip...")
    try:
        subprocess.run([python_exe, '-m', 'ensurepip', '--upgrade'], check=True)
        print("✅ pip instalado")
        return python_exe
    except subprocess.CalledProcessError:
        print("❌ Error instalando pip")
        print("💡 Solución: Instala pip manualmente según tu sistema operativo")
        sys.exit(1)

def install_requirements():
    """Instala dependencias"""
    python_exe = check_pip()
    
    requirements = [
        'pyserial>=3.5',
        'asyncio-mqtt',
        'aiofiles'
    ]
    
    print("📦 Instalando dependencias...")
    for req in requirements:
        print(f"   Instalando {req}...")
        try:
            result = subprocess.run([
                python_exe, '-m', 'pip', 'install', req
            ], capture_output=True, text=True)
            
            if result.returncode == 0:
                print(f"   ✅ {req} instalado")
            else:
                print(f"   ⚠️  Error instalando {req}: {result.stderr}")
        except Exception as e:
            print(f"   ❌ Error: {e}")

def setup_permissions_linux():
    """Configura permisos en Linux"""
    print("🔧 Configurando permisos de usuario para puertos serie...")
    
    username = os.getenv('USER')
    if not username:
        print("⚠️  No se pudo detectar el usuario")
        return
    
    # Agregar usuario a grupos necesarios
    groups = ['dialout', 'uucp', 'tty']
    
    for group in groups:
        try:
            # Verificar si el grupo existe
            result = subprocess.run(['getent', 'group', group], 
                                  capture_output=True)
            if result.returncode == 0:
                # Agregar usuario al grupo
                subprocess.run(['sudo', 'usermod', '-a', '-G', group, username])
                print(f"✅ Usuario agregado al grupo {group}")
        except Exception as e:
            print(f"⚠️  Error configurando grupo {group}: {e}")
    
    print("🔄 Nota: Necesitarás cerrar sesión y volver a entrar para que los cambios tengan efecto")

def setup_permissions_macos():
    """Configura permisos en macOS"""
    print("🔧 Configurando permisos en macOS...")
    
    # En macOS, los dispositivos USB suelen estar en /dev/tty.usbserial* o /dev/tty.usbmodem*
    print("✅ En macOS, los permisos suelen funcionar automáticamente")
    print("💡 Si tienes problemas, ejecuta el programa con sudo")

def create_desktop_shortcut_windows():
    """Crea acceso directo en Windows"""
    try:
        import winshell
        from win32com.client import Dispatch
        
        desktop = winshell.desktop()
        path = os.path.join(desktop, "SMS Gateway.lnk")
        target = os.path.join(os.getcwd(), "web_server_multiplatform.py")
        
        shell = Dispatch('WScript.Shell')
        shortcut = shell.CreateShortCut(path)
        shortcut.Targetpath = find_python_executable()
        shortcut.Arguments = target
        shortcut.WorkingDirectory = os.getcwd()
        shortcut.IconLocation = target
        shortcut.save()
        
        print("✅ Acceso directo creado en el escritorio")
    except ImportError:
        print("⚠️  No se pudo crear acceso directo (falta pywin32)")
    except Exception as e:
        print(f"⚠️  Error creando acceso directo: {e}")

def create_desktop_shortcut_linux():
    """Crea acceso directo en Linux"""
    try:
        desktop_path = Path.home() / 'Desktop'
        if not desktop_path.exists():
            desktop_path = Path.home() / 'Escritorio'  # Español
        
        if desktop_path.exists():
            shortcut_path = desktop_path / 'SMS Gateway.desktop'
            
            shortcut_content = f"""[Desktop Entry]
Version=1.0
Type=Application
Name=SMS Gateway
Comment=Gateway SMS Multiplataforma
Exec={find_python_executable()} {os.path.join(os.getcwd(), 'web_server_multiplatform.py')}
Icon=applications-internet
Terminal=true
Categories=Network;
"""
            
            with open(shortcut_path, 'w') as f:
                f.write(shortcut_content)
            
            # Hacer ejecutable
            os.chmod(shortcut_path, 0o755)
            print("✅ Acceso directo creado en el escritorio")
        else:
            print("⚠️  No se encontró carpeta de escritorio")
            
    except Exception as e:
        print(f"⚠️  Error creando acceso directo: {e}")

def create_run_script():
    """Crea script de ejecución"""
    system = platform.system().lower()
    python_exe = find_python_executable()
    
    if system == 'windows':
        script_name = 'run_gateway.bat'
        script_content = f"""@echo off
echo Iniciando SMS Gateway...
{python_exe} web_server_multiplatform.py
pause
"""
    else:
        script_name = 'run_gateway.sh'
        script_content = f"""#!/bin/bash
echo "Iniciando SMS Gateway..."
{python_exe} web_server_multiplatform.py
"""
    
    with open(script_name, 'w') as f:
        f.write(script_content)
    
    if system != 'windows':
        os.chmod(script_name, 0o755)
    
    print(f"✅ Script de ejecución creado: {script_name}")

def check_hardware():
    """Verifica hardware disponible"""
    print("\n🔍 Verificando hardware...")
    
    try:
        from system_config import SystemConfig
        
        config = SystemConfig()
        ports = config.scan_available_ports()
        
        print(f"📱 Puertos serie encontrados: {len(ports)}")
        
        huawei_found = False
        for port in ports:
            if port.get('is_huawei'):
                print(f"   ✅ Huawei encontrado: {port['device']} - {port['description']}")
                huawei_found = True
            elif port.get('is_modem'):
                print(f"   📱 Módem: {port['device']} - {port['description']}")
            else:
                print(f"   🔌 Puerto: {port['device']} - {port['description']}")
        
        if not huawei_found:
            print("⚠️  No se detectó módem Huawei E8278")
            print("💡 Asegúrate de que el dispositivo esté conectado y en modo módem")
        
        return len(ports) > 0
        
    except Exception as e:
        print(f"⚠️  Error verificando hardware: {e}")
        return False

def show_completion_message():
    """Muestra mensaje de finalización"""
    system = platform.system().lower()
    
    print("\n🎉 === INSTALACIÓN COMPLETADA ===")
    print("✅ SMS Gateway está listo para usar")
    print(f"🌐 Para iniciar: python web_server_multiplatform.py")
    
    if system == 'windows':
        print("🖱️  O ejecuta: run_gateway.bat")
    else:
        print("🖱️  O ejecuta: ./run_gateway.sh")
    
    print(f"📱 Interfaz web: http://localhost:8080")
    print("\n🔧 Funciones instaladas:")
    print("   ✅ Detección automática de módem")
    print("   ✅ Interfaz web responsive")
    print("   ✅ Envío y recepción SMS")
    print("   ✅ Compatible con Windows, Linux y macOS")
    
    if system == 'linux':
        print("\n🔄 IMPORTANTE: Cierra sesión y vuelve a entrar para aplicar permisos")
    
    print("\n💡 Consulta README.md para más información")

def main():
    """Función principal del instalador"""
    print_header()
    
    # Verificaciones básicas
    system = detect_system()
    check_python_version()
    
    # Instalación de dependencias
    install_requirements()
    
    # Configuración específica del sistema
    if system == 'linux':
        setup_permissions_linux()
        create_desktop_shortcut_linux()
    elif system == 'darwin':  # macOS
        setup_permissions_macos()
    elif system == 'windows':
        create_desktop_shortcut_windows()
    
    # Crear scripts de ejecución
    create_run_script()
    
    # Verificar hardware
    check_hardware()
    
    # Mensaje final
    show_completion_message()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n❌ Instalación cancelada por el usuario")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error durante la instalación: {e}")
        print("🔧 Intenta ejecutar el instalador con permisos de administrador")
        sys.exit(1)
