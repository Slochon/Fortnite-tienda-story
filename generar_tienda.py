import os
import io
import requests
from PIL import Image, ImageDraw, ImageFont

API_URL = "https://fortnite-api.com/v2/shop"

OUTPUT_DIR = "salida"
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "tienda.png")

BACKGROUND_FILE = "background.png"


def descargar_imagen(url):
    try:
        respuesta = requests.get(url, timeout=30)
        respuesta.raise_for_status()
        return Image.open(io.BytesIO(respuesta.content)).convert("RGBA")
    except Exception as e:
        print(f"No se pudo descargar la imagen: {e}")
        return None


def obtener_fuente(tamano, negrita=False):
    posibles = []

    if negrita:
        posibles = [
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
            "/usr/share/fonts/truetype/liberation2/LiberationSans-Bold.ttf",
        ]
    else:
        posibles = [
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            "/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf",
        ]

    for ruta in posibles:
        if os.path.exists(ruta):
            return ImageFont.truetype(ruta, tamano)

    return ImageFont.load_default()


def obtener_tienda():
    print("Consultando la tienda de Fortnite...")

    respuesta = requests.get(API_URL, timeout=30)
    respuesta.raise_for_status()

    datos = respuesta.json()

    if not isinstance(datos, dict):
        raise RuntimeError("La respuesta de la API no es un objeto JSON válido.")

    tienda = datos.get("data")

    if not isinstance(tienda, dict):
        raise RuntimeError("La respuesta no contiene 'data' correctamente.")

    entradas = tienda.get("entries")

    if not isinstance(entradas, list):
        raise RuntimeError("La respuesta no contiene 'entries' correctamente.")

    print(f"Entradas encontradas: {len(entradas)}")

    return entradas


def obtener_objetos(entradas):
    objetos = []

    for entrada in entradas:
        if not isinstance(entrada, dict):
            continue

        precio = entrada.get("finalPrice")

        items = entrada.get("brItems")

        if not isinstance(items, list):
            continue

        for item in items:
            if not isinstance(item, dict):
                continue

            nombre = (
                item.get("name")
                or item.get("displayName")
                or item.get("id")
                or "Objeto"
            )

            imagen_url = None

            asset = entrada.get("newDisplayAsset")

            if isinstance(asset, dict):
                renders = asset.get("renderImages")

                if isinstance(renders, list) and renders:
                    primero = renders[0]

                    if isinstance(primero, dict):
                        imagen_url = primero.get("image")

            if not imagen_url:
                imagen_url = item.get("images", {}).get("icon")

            if not imagen_url:
                imagen_url = item.get("images", {}).get("featured")
def crear_tienda(objetos):
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    if os.path.exists(BACKGROUND_FILE):
        fondo = Image.open(BACKGROUND_FILE).convert("RGBA")
    else:
        fondo = Image.new("RGBA", (1920, 1080), (25, 25, 35, 255))

    ancho, alto = fondo.size

    # Dejamos un margen para que la tienda quede ordenada.
    margen = 50
    columnas = 4
    filas = 2

    espacio_x = 25
    espacio_y = 25

    ancho_tarjeta = (
        ancho - (margen * 2) - (espacio_x * (columnas - 1))
    ) // columnas

    alto_tarjeta = (
        alto - (margen * 2) - (espacio_y * (filas - 1))
    ) // filas

    fuente_nombre = obtener_fuente(28, True)
    fuente_precio = obtener_fuente(26, True)

    # Limitamos a 8 objetos para mantener el diseño limpio.
    objetos = objetos[:8]

    for indice, objeto in enumerate(objetos):
        fila = indice // columnas
        columna = indice % columnas

        x = margen + columna * (ancho_tarjeta + espacio_x)
        y = margen + fila * (alto_tarjeta + espacio_y)

        tarjeta = Image.new(
            "RGBA",
            (ancho_tarjeta, alto_tarjeta),
            (20, 20, 30, 230),
        )

        draw = ImageDraw.Draw(tarjeta)

        # Imagen del cosmético.
        imagen = None

        if objeto.get("imagen"):
            imagen = descargar_imagen(objeto["imagen"])

        if imagen:
            imagen.thumbnail(
                (
                    ancho_tarjeta - 30,
                    alto_tarjeta - 120,
                ),
                Image.Resampling.LANCZOS,
            )

            ix = (ancho_tarjeta - imagen.width) // 2
            iy = 15

            tarjeta.alpha_composite(imagen, (ix, iy))

        # Nombre.
        nombre = str(objeto.get("nombre", "Objeto"))

        # Evitamos nombres demasiado largos.
        if len(nombre) > 28:
            nombre = nombre[:25] + "..."

        bbox = draw.textbbox((0, 0), nombre, font=fuente_nombre)
        texto_ancho = bbox[2] - bbox[0]

        draw.text(
            (
                (ancho_tarjeta - texto_ancho) // 2,
                alto_tarjeta - 85,
            ),
            nombre,
            font=fuente_nombre,
            fill="white",
        )

        # Precio.
        precio = objeto.get("precio")

        if precio is not None:
            texto_precio = f"{precio} V-Bucks"

            bbox = draw.textbbox(
                (0, 0),
                texto_precio,
                font=fuente_precio,
            )

            precio_ancho = bbox[2] - bbox[0]

            draw.text(
                (
                    (ancho_tarjeta - precio_ancho) // 2,
                    alto_tarjeta - 48,
                ),
                texto_precio,
                font=fuente_precio,
                fill="white",
            )

        fondo.alpha_composite(tarjeta, (x, y))

    fondo.convert("RGB").save(
        OUTPUT_FILE,
        "PNG",
        optimize=True,
    )

    print(f"Tienda creada correctamente: {OUTPUT_FILE}")


def main():
    try:
        entradas = obtener_tienda()
        objetos = obtener_objetos(entradas)

        if not objetos:
            raise RuntimeError(
                "No se encontraron objetos en la respuesta de la tienda."
            )

        crear_tienda(objetos)

    except requests.RequestException as e:
        raise RuntimeError(
            f"Error al conectar con Fortnite-API: {e}"
        ) from e


if __name__ == "__main__":
    main()
            objetos.append({
                "nombre": nombre,
                "precio": precio,
                "imagen": imagen_url,
            })

    print(f"Objetos encontrados: {len(objetos)}")

    return objetos


def cargar_fondo():
    if os.path.exists(BACKGROUND_FILE):
        try:
            return Image.open(BACKGROUND_FILE).convert("RGBA")
        except Exception:
            pass

    return Image.new("RGBA", (1920, 1080), (25, 25, 35, 255))