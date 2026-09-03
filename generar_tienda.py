import requests
import json

URL = "https://fortnite-api.com/v2/shop"

print("Consultando la tienda de Fortnite...")

respuesta = requests.get(URL, timeout=30)

print("Código HTTP:", respuesta.status_code)

if respuesta.status_code != 200:
    print("Error de la API:")
    print(respuesta.text)
    raise SystemExit(1)

datos = respuesta.json()

print("\nEstructura recibida:")
print(json.dumps(datos, indent=2, ensure_ascii=False)[:5000])

if "data" not in datos:
    print("\n❌ La respuesta no contiene 'data'.")
    raise SystemExit(1)

print("\n✅ La API respondió correctamente.")
print("Tipo de 'data':", type(datos["data"]).__name__)