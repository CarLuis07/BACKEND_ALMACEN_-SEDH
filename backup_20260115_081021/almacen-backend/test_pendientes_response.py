import requests
import json

# Configuración
API_BASE_URL = 'http://192.168.180.164:8081/api/v1'

# Token de ejemplo - reemplazar con un token válido
token = input("Ingresa el token: ")

# Hacer la petición
headers = {'Authorization': f'Bearer {token}'}
response = requests.get(f'{API_BASE_URL}/requisiciones/pendientes/jefe', headers=headers)

print(f"Status Code: {response.status_code}")
print(f"\nResponse JSON:")
print(json.dumps(response.json(), indent=2, ensure_ascii=False))
