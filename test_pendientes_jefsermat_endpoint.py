import requests
import json

# Configuración
BASE_URL = "http://192.168.180.164:8081"
EMAIL = "escarleth.nunez@sedh.gob.hn"
PASSWORD = "Prueba123"  # La contraseña correcta de escarleth

# 1. Login
print("=== 1. LOGIN ===")
login_response = requests.post(
    f"{BASE_URL}/api/v1/accesos/login",
    json={
        "email": EMAIL,
        "password": PASSWORD
    }
)
print(f"Status: {login_response.status_code}")
if login_response.status_code == 200:
    token = login_response.json().get("access_token")
    print(f"Token obtenido: {token[:50]}...")
else:
    print(f"Error: {login_response.text}")
    exit(1)

# 2. Obtener requisiciones pendientes de JefSerMat
print("\n=== 2. REQUISICIONES PENDIENTES JEFSERMAT ===")
headers = {"Authorization": f"Bearer {token}"}
pendientes_response = requests.get(
    f"{BASE_URL}/api/v1/requisiciones/pendientes/jefe-materiales",
    headers=headers
)
print(f"Status: {pendientes_response.status_code}")

if pendientes_response.status_code == 200:
    requisiciones = pendientes_response.json()
    print(f"Total requisiciones: {len(requisiciones)}")
    
    # Verificar si UIT-001-2026 está en la lista
    uit_001 = [r for r in requisiciones if r.get('codRequisicion') == 'UIT-001-2026']
    if uit_001:
        print("⚠️ UIT-001-2026 ESTÁ en la lista (INCORRECTO - ya fue aprobada)")
        print(f"   Detalles: {json.dumps(uit_001[0], indent=2)}")
    else:
        print("✓ UIT-001-2026 NO está en la lista (CORRECTO - ya fue aprobada)")
    
    # Mostrar las primeras 3 requisiciones
    print("\nPrimeras 3 requisiciones:")
    for i, req in enumerate(requisiciones[:3]):
        print(f"  {i+1}. {req.get('codRequisicion')} - {req.get('nombreEmpleado')}")
else:
    print(f"Error: {pendientes_response.text}")
