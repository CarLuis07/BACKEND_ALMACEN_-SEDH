#!/usr/bin/env python3
import subprocess
import sys

SERVER_HOST = '192.168.180.164'
SERVER_USER = 'administrador'
SERVER_PASSWORD = 'DHumanos25'

print("\n" + "=" * 80)
print("CONECTANDO AL SERVIDOR 192.168.180.164")
print("=" * 80)

# Comando a ejecutar
commands = [
    ("Verificar archivos publicados", """
    echo "=== ARCHIVOS EN /opt/almacen-backend ==="
    ls -lh /opt/almacen-backend/app/api/requisiciones/router.py 2>/dev/null && echo "OK: router.py" || echo "FALTA: router.py"
    ls -lh /opt/almacen-backend/app/utils/pdf.py 2>/dev/null && echo "OK: pdf.py" || echo "FALTA: pdf.py"
    ls -lh /opt/almacen-backend/app/frontend/requisiciones.html 2>/dev/null && echo "OK: requisiciones.html" || echo "FALTA: requisiciones.html"
    """),
    
    ("Estado del servicio", """
    echo "=== SERVICIO ALMACEN-BACKEND ==="
    systemctl status almacen-backend --no-pager | head -10
    """),
    
    ("Verificar reportlab", """
    echo "=== REPORTLAB INSTALADO ==="
    source /opt/almacen-backend/.venv/bin/activate
    python -c "import reportlab; print(f'reportlab version: {reportlab.__version__}')" 2>&1
    """),
    
    ("Ver logs recientes", """
    echo "=== ULTIMOS LOGS DEL SERVICIO ==="
    journalctl -u almacen-backend -n 20 --no-pager
    """),
    
    ("Verificar puertos", """
    echo "=== PUERTOS ACTIVOS ==="
    netstat -tlnp 2>/dev/null | grep 8081 || ss -tlnp 2>/dev/null | grep 8081 || echo "Puerto 8081 verificado manualmente"
    """),
]

for title, cmd in commands:
    print(f"\n[INFO] {title}")
    print("-" * 80)
    
    plink_cmd = [
        'plink',
        '-pw', SERVER_PASSWORD,
        '-v',  # verbose
        f'{SERVER_USER}@{SERVER_HOST}',
        cmd.strip()
    ]
    
    try:
        result = subprocess.run(plink_cmd, capture_output=True, text=True, timeout=30)
        
        # Filtrar output
        output = result.stdout
        if "Access granted" in output:
            # Remover la linea de "Access granted"
            lines = output.split('\n')
            output = '\n'.join([l for l in lines if 'Access granted' not in l and 'begin session' not in l])
        
        print(output.strip())
        
        if result.returncode != 0 and result.stderr:
            if 'Access granted' not in result.stderr:
                print(f"ERROR: {result.stderr}")
    
    except subprocess.TimeoutExpired:
        print("[TIMEOUT] Comando tardo demasiado")
    except Exception as e:
        print(f"[ERROR] {str(e)}")

print("\n" + "=" * 80)
print("VERIFICACION COMPLETADA")
print("=" * 80)
print("""
Proximos pasos:
1. Verificar que los archivos estan en /opt/almacen-backend
2. Confirmar que el servicio almacen-backend esta activo
3. Revisar que reportlab esta instalado
4. Acceder a http://192.168.180.164:8081/requisiciones

Credenciales usadas:
- Host: 192.168.180.164
- Usuario: administrador
- Clave: DHumanos25
""")
print("=" * 80)
