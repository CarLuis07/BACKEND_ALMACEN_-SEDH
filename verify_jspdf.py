#!/usr/bin/env python3
"""
Script para verificar que jsPDF está cargado correctamente
"""
import requests
import re

url = "http://192.168.180.164:8081/requisiciones"

print("🔍 Verificando carga de jsPDF en requisiciones.html...")
print(f"URL: {url}\n")

try:
    response = requests.get(url, timeout=5)
    
    if response.status_code == 200:
        content = response.text
        
        # Buscar referencias a jsPDF
        jspdf_refs = re.findall(r'https://cdnjs\.cloudflare\.com/ajax/libs/jspdf[^\s"\']+', content)
        autotable_refs = re.findall(r'https://cdnjs\.cloudflare\.com/ajax/libs/jspdf-autotable[^\s"\']+', content)
        
        print("✅ HTML cargado exitosamente\n")
        
        if jspdf_refs:
            print("✅ jsPDF encontrado:")
            for ref in jspdf_refs:
                print(f"   {ref}")
        else:
            print("❌ jsPDF NO encontrado")
            
        if autotable_refs:
            print("\n✅ jsPDF-AutoTable encontrado:")
            for ref in autotable_refs:
                print(f"   {ref}")
        else:
            print("\n⚠️  jsPDF-AutoTable NO encontrado (opcional)")
            
        # Buscar la función de generación PDF
        if 'generarPDFRequisicion' in content:
            print("\n✅ Función generarPDFRequisicion encontrada")
        else:
            print("\n❌ Función generarPDFRequisicion NO encontrada")
            
        # Buscar los botones de descarga/impresión
        if 'Descargar PDF' in content:
            print("✅ Botón 'Descargar PDF' encontrado")
        if 'Imprimir' in content:
            print("✅ Botón 'Imprimir' encontrado")
            
    else:
        print(f"❌ Error: Status code {response.status_code}")
        
except requests.exceptions.RequestException as e:
    print(f"❌ Error de conexión: {e}")
except Exception as e:
    print(f"❌ Error: {e}")

print("\n✅ Verificación completada")
