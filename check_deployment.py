#!/usr/bin/env python3
import subprocess
import requests

SERVER_HOST = '192.168.180.164'
SERVER_USER = 'administrador'
SERVER_PASSWORD = 'DHumanos25'

print('=' * 70)
print('VERIFICACION DE DEPLOYMENT EN SERVIDOR')
print('=' * 70)

# Verificar archivos
print('\n[1] VERIFICANDO ARCHIVOS EN SERVIDOR')
print('-' * 70)

files_to_check = [
    '/opt/almacen-backend/app/api/requisiciones/router.py',
    '/opt/almacen-backend/app/utils/pdf.py',
    '/opt/almacen-backend/app/frontend/requisiciones.html'
]

for file_path in files_to_check:
    cmd = [
        'plink',
        '-pw', SERVER_PASSWORD,
        f'{SERVER_USER}@{SERVER_HOST}',
        f'ls -lh {file_path} 2>/dev/null && echo OK || echo FALTA'
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
    status = 'OK' if 'OK' in result.stdout else 'FALTA'
    print(f'{status}: {file_path}')
    if 'rw' in result.stdout:
        size = result.stdout.split()[4]
        print(f'       Tamaño: {size}')

# Verificar servicio
print('\n[2] VERIFICANDO SERVICIO')
print('-' * 70)

cmd = [
    'plink',
    '-pw', SERVER_PASSWORD,
    f'{SERVER_USER}@{SERVER_HOST}',
    'systemctl is-active almacen-backend'
]

try:
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
    status = result.stdout.strip()
    if status == 'active':
        print(f'Status: ACTIVO')
    else:
        print(f'Status: {status}')
except Exception as e:
    print(f'Error: {e}')

# Verificar reportlab
print('\n[3] VERIFICANDO DEPENDENCIAS')
print('-' * 70)

cmd = [
    'plink',
    '-pw', SERVER_PASSWORD,
    f'{SERVER_USER}@{SERVER_HOST}',
    'source /opt/almacen-backend/.venv/bin/activate && pip list | grep reportlab'
]

try:
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=20)
    if 'reportlab' in result.stdout:
        print(f'reportlab: INSTALADO')
        print(f'  {result.stdout.strip()}')
    else:
        print(f'reportlab: NO INSTALADO (intentando instalar...)')
        
        install_cmd = [
            'plink',
            '-pw', SERVER_PASSWORD,
            f'{SERVER_USER}@{SERVER_HOST}',
            'source /opt/almacen-backend/.venv/bin/activate && pip install reportlab -q && echo INSTALADO || echo ERROR'
        ]
        result = subprocess.run(install_cmd, capture_output=True, text=True, timeout=60)
        print(f'  Instalacion: {result.stdout.strip()}')
except Exception as e:
    print(f'Error: {e}')

# Verificar endpoint
print('\n[4] VERIFICANDO ENDPOINT')
print('-' * 70)

try:
    response = requests.get('http://192.168.180.164:8081/requisiciones', timeout=5)
    print(f'HTTP Status: {response.status_code}')
    print(f'Sitio accesible: SI')
except Exception as e:
    print(f'Sitio accesible: NO')
    print(f'Error: {e}')

# Resumen
print('\n' + '=' * 70)
print('RESUMEN')
print('=' * 70)
print('\nPara verificar manualmente en el servidor:')
print('1. SSH: ssh administrador@192.168.180.164')
print('2. Ver archivos:')
print('   ls -la /opt/almacen-backend/app/utils/pdf.py')
print('   ls -la /opt/almacen-backend/app/api/requisiciones/router.py')
print('3. Ver estado servicio: systemctl status almacen-backend')
print('4. Ver logs: journalctl -u almacen-backend -n 50')
print('5. Acceder: http://192.168.180.164:8081/requisiciones')
print()
