#!/usr/bin/env python3
"""
Conexion SSH interactiva al servidor 192.168.180.164
Usuario: administrador
Clave: DHumanos25
"""

import subprocess
import sys

SERVER_HOST = '192.168.180.164'
SERVER_USER = 'administrador'
SERVER_PASSWORD = 'DHumanos25'

print("\n" + "=" * 80)
print("CONEXION SSH AL SERVIDOR")
print("=" * 80)
print(f"""
Host: {SERVER_HOST}
Usuario: {SERVER_USER}
Clave: {SERVER_PASSWORD}

Opciones de comandos:
1. Ver estado del servicio almacen-backend
2. Ver ultimos logs del servicio
3. Ver archivos publicados
4. Verificar espacio en disco
5. Ver procesos de Python
6. Ver puertos activos
7. Reiniciar servicio
8. Ver informacion del sistema
9. Ejecutar comando personalizado
0. Salir
""")
print("=" * 80)

def ejecutar_comando(comando):
    """Ejecuta un comando en el servidor SSH"""
    print(f"\n[EJECUTANDO] {comando}\n")
    cmd = [
        'plink',
        '-pw', SERVER_PASSWORD,
        f'{SERVER_USER}@{SERVER_HOST}',
        comando
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        
        # Limpiar output de plink
        output = result.stdout
        if 'Access granted' in output:
            lines = output.split('\n')
            output = '\n'.join([l for l in lines if 'Access granted' not in l and 'begin session' not in l])
        
        print(output)
        
        if result.returncode != 0 and result.stderr:
            print(f"\n[ERROR] {result.stderr}")
    except subprocess.TimeoutExpired:
        print("[TIMEOUT] El comando tardó demasiado")
    except Exception as e:
        print(f"[ERROR] {e}")

def menu():
    """Muestra el menu interactivo"""
    while True:
        try:
            opcion = input("\n¿Que deseas hacer? (0-9): ").strip()
            
            if opcion == '0':
                print("\n[INFO] Desconectando...")
                break
            elif opcion == '1':
                ejecutar_comando('systemctl status almacen-backend --no-pager')
            elif opcion == '2':
                ejecutar_comando('journalctl -u almacen-backend -n 50 --no-pager')
            elif opcion == '3':
                ejecutar_comando('ls -lh /opt/almacen-backend/app/api/requisiciones/router.py /opt/almacen-backend/app/utils/pdf.py /opt/almacen-backend/app/frontend/requisiciones.html 2>/dev/null')
            elif opcion == '4':
                ejecutar_comando('df -h /opt')
            elif opcion == '5':
                ejecutar_comando('ps aux | grep python | grep -v grep')
            elif opcion == '6':
                ejecutar_comando('netstat -tlnp 2>/dev/null | grep 8081 || ss -tlnp 2>/dev/null | grep 8081')
            elif opcion == '7':
                print("\n[ADVERTENCIA] Esto reiniciara el servicio almacen-backend")
                confirmar = input("¿Continuar? (s/n): ").strip().lower()
                if confirmar == 's':
                    ejecutar_comando('sudo systemctl restart almacen-backend && sleep 2 && systemctl status almacen-backend --no-pager | head -10')
            elif opcion == '8':
                ejecutar_comando('uname -a && echo "---" && lsb_release -a 2>/dev/null || cat /etc/os-release | head -5')
            elif opcion == '9':
                comando = input("\nIngresa el comando a ejecutar: ").strip()
                if comando:
                    ejecutar_comando(comando)
            else:
                print("\n[ERROR] Opcion no valida. Ingresa un numero del 0 al 9")
        except KeyboardInterrupt:
            print("\n\n[INFO] Conexion interrumpida por el usuario")
            break
        except Exception as e:
            print(f"\n[ERROR] {e}")

# Menu principal
menu()

print("\n" + "=" * 80)
print("DESCONEXION COMPLETADA")
print("=" * 80)
