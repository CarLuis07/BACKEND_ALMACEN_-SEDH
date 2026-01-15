#!/usr/bin/env python3
"""Script para desplegar y diagnosticar usando paramiko"""

import paramiko
import sys
import time

SERVER = "192.168.180.164"
USER = "administrador"
PASSWORD = "DHumanos25"

def ssh_connect():
    """Crea conexión SSH"""
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        print(f"Conectando a {SERVER} como {USER}...")
        client.connect(SERVER, username=USER, password=PASSWORD, allow_agent=False, look_for_keys=False)
        print("✓ Conectado")
        return client
    except Exception as e:
        print(f"✗ Error de conexión: {e}")
        return None

def run_command(client, cmd, description=""):
    """Ejecuta un comando remoto"""
    if description:
        print(f"\n{description}")
    
    try:
        stdin, stdout, stderr = client.exec_command(cmd)
        exit_code = stdout.channel.recv_exit_status()
        
        output = stdout.read().decode('utf-8', errors='ignore')
        error = stderr.read().decode('utf-8', errors='ignore')
        
        if exit_code == 0:
            print(f"✓ Éxito")
            if output:
                for line in output.strip().split('\n')[:20]:  # Mostrar primeras 20 líneas
                    print(f"  {line}")
                if output.count('\n') > 20:
                    print(f"  ... ({output.count(chr(10))} líneas totales)")
        else:
            print(f"✗ Error (código {exit_code})")
            if error:
                print(f"  {error[:200]}")
        
        return exit_code == 0, output, error
    except Exception as e:
        print(f"✗ Error ejecutando comando: {e}")
        return False, "", str(e)

def diagnose():
    """Diagnostica el deployment"""
    client = ssh_connect()
    if not client:
        return False
    
    try:
        print("\n" + "=" * 70)
        print("DIAGNÓSTICO POST-DEPLOYMENT")
        print("=" * 70)
        
        # 1. Verificar archivo router.py
        run_command(client, 
            "ls -lh /opt/almacen-backend/app/api/requisiciones/router.py && wc -l /opt/almacen-backend/app/api/requisiciones/router.py",
            "\n1. Verificando archivo router.py")
        
        # 2. Buscar el endpoint
        run_command(client,
            "grep -n 'def api_listar_notificaciones' /opt/almacen-backend/app/api/requisiciones/router.py",
            "\n2. Buscando endpoint api_listar_notificaciones")
        
        # 3. Estado del servicio
        run_command(client,
            "systemctl is-active almacen-backend",
            "\n3. Estado del servicio")
        
        # 4. Probar endpoint
        success, output, error = run_command(client,
            'curl -s -w "\\n%{http_code}" http://127.0.0.1:8081/api/v1/requisiciones/notificaciones -H "Authorization: Bearer test"',
            "\n4. Probando endpoint HTTP")
        
        # Analizar respuesta
        if output:
            lines = output.strip().split('\n')
            if lines:
                http_code = lines[-1] if len(lines) > 0 else "???"
                body = '\n'.join(lines[:-1]) if len(lines) > 1 else ""
                print(f"\n   HTTP Code: {http_code}")
                if body:
                    print(f"   Body: {body[:100]}")
        
        # 5. Logs recientes
        run_command(client,
            "journalctl -u almacen-backend -n 15 --no-pager 2>&1 | grep -E 'ERROR|Failed|error'",
            "\n5. Errores recientes en logs")
        
        # 6. Verificar sintaxis Python del router
        run_command(client,
            "python3 -m py_compile /opt/almacen-backend/app/api/requisiciones/router.py",
            "\n6. Verificando sintaxis Python del router")
        
        # 7. Listar rutas registradas
        run_command(client,
            "python3 << 'EOFPYTHON'\nimport sys\nsys.path.insert(0, '/opt/almacen-backend')\ntry:\n    from app.main import app\n    print('Rutas con notificaciones:')\n    for route in app.routes:\n        if 'notificaciones' in str(route.path).lower():\n            print(f'  {route.path} {route.methods}')\nexcept Exception as e:\n    print(f'Error: {e}')\nEOFPYTHON",
            "\n7. Rutas registradas en la app")
        
        print("\n" + "=" * 70)
        print("FIN DEL DIAGNÓSTICO")
        print("=" * 70)
        
        return True
        
    finally:
        client.close()

if __name__ == "__main__":
    try:
        success = diagnose()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n✗ Interrumpido por el usuario")
        sys.exit(1)
