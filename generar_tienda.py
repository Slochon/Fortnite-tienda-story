import os
import io
import requests
from PIL import Image, ImageDraw, ImageFont

API_URL = "https://fortnite-api.com/v2/shop"
OUTPUT_DIR = "salida"
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "tienda.png")
BACKGROUND_FILE = "background.png"


def obtener_fuente(tamano, negrita=False):
    if negrita:
        rutas = [
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
            "/usr/share/fonts/truetype/liberation2/LiberationSans-Bold.ttf",
        ]
    else:
        rutas = [
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            "/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf",
        ]

    for ruta in rutas:
        if os.path.exists(ruta):
            return ImageFont.truetype(ruta, tamano)

    return ImageFont.load_default()


def descargar_imagen(url):
    if not url:
        return None

    try:
        r = requests.get(url, timeout=30)
        r.raise_for_status()
        return Image.open(io.BytesIO(r.content)).convert("RGBA")
    except Exception as e:
        print("No se pudo descargar una imagen:", e)
        return None


def obtener_tienda():
    print("Consultando Fortnite-API...")

    r = requests.get(API_URL, timeout=30)
    r.raise_for_status()

    respuesta = r.json()

    data = respuesta.get("data")

    if not isinstance(data, dict):
        raise RuntimeError("La API no devolvió un objeto 'data' válido.")

    entries = data.get("entries")

    if not isinstance(entries, list):
        raise RuntimeError("La API no devolvió una lista 'entries' válida.")

    print("Entradas recibidas:", len(entries))

    return entries
def obtener_objetos(entries):
    objetos = []

    for entry in entries:
        if not isinstance(entry, dict):
            continue

        precio = entry.get("finalPrice")
        items = entry.get("brItems")

        if not isinstance(items, list):
            continue

        imagen_url = None

        asset = entry.get("newDisplayAsset")

        if isinstance(asset, dict):
            renders = asset.get("renderImages")

            if isinstance(renders, list):
                for render in renders:
                    if isinstance(render, dict):
                        imagen_url = render.get("image")
                        if imagen_url:
                            break

        for item in items:
            if not isinstance(item, dict):
                continue

            nombre = (
                item.get("name")
                or item.get("displayName")
                or item.get("id")
                or "Objeto"
            )

            item_imagen = None
            images = item.get("images")

            if isinstance(images, dict):
                item_imagen = (
                    images.get("featured")
                    or images.get("icon")
                    or images.get("background")
                )

            objetos.append({
                "nombre": nombre,
                "precio": precio,
                "imagen": imagen_url or item_imagen,
            })

    print("Objetos encontrados:", len(objetos))

    return objetos


def cargar_fondo():
    if os.path.exists(BACKGROUND_FILE):
        try:
            return Image.open(BACKGROUND_FILE).convert("RGBA")
        except Exception as e:
            print("No se pudo abrir background.png:", e)

    print("No se encontró background.png. Se utilizará un fondo básico.")

    return Image.new(
        "RGBA",
        (1920, 1080),
        (25, 25, 35, 255),
    )


def crear_tienda(objetos):
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    fondo = cargar_fondo()
    ancho, alto = fondo.size

    margen = 50
    columnas = 4
    filas = 2

    separacion_x = 25
    separacion_y = 25

    ancho_tarjeta = (
        ancho
        - margen * 2
        - separacion_x * (columnas - 1)
    ) // columnas

    alto_tarjeta = (
        alto
        - margen * 2
        - separacion_y * (filas - 1)
    ) // filas

    fuente_nombre = obtener_fuente(26, True)
    fuente_precio = obtener_fuente(24, True)

    objetos = objetos[:8]

    for indice, objeto in enumerate(objetos):
        fila = indice // columnas
        columna = indice % columnas

        x = margen + columna * (ancho_tarjeta + separacion_x)
        y = margen + fila * (alto_tarjeta + separacion_y)

        tarjeta = Image.new(
            "RGBA",
            (ancho_tarjeta, alto_tarjeta),
            (15, 15, 25, 235),
        )

        draw = ImageDraw.Draw(tarjeta)

        imagen = descargar_imagen(objeto.get("imagen"))

        if imagen:
            imagen.thumbnail(
                (
                    ancho_tarjeta - 30,
                    alto_tarjeta - 120,
                ),
                Image.Resampling.LANCZOS,
            )

            imagen_x = (ancho_tarjeta - imagen.width) // 2
            imagen_y = 15

            tarjeta.alpha_composite(
                imagen,
                (imagen_x, imagen_y),
            )

        nombre = str(objeto.get("nombre", "Objeto"))

        if len(nombre) > 26:
            nombre = nombre[:23] + "..."

        caja = draw.textbbox(
            (0, 0),
            nombre,
            font=fuente_nombre,
        )

        texto_ancho = caja[2] - caja[0]

        draw.text(
            (
                (ancho_tarjeta - texto_ancho) // 2,
                alto_tarjeta - 80,
            ),
            nombre,
            font=fuente_nombre,
            fill="white",
        )

        precio = objeto.get("precio")

        if precio is not None:
            texto_precio = f"{precio} V-Bucks"

            caja = draw.textbbox(
                (0, 0),
                texto_precio,
                font=fuente_precio,
            )

            precio_ancho = caja[2] - caja[0]

            draw.text(
                (
                    (ancho_tarjeta - precio_ancho) // 2,
                    alto_tarjeta - 45,
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

    print("Tienda creada correctamente.")
    print("Archivo:", OUTPUT_FILE)
def main():
    entries = obtener_tienda()
    objetos = obtener_objetos(entries)

    if not objetos:
        raise RuntimeError(
            "No se encontraron objetos en la respuesta de la tienda."
        )

    crear_tienda(objetos)


if __name__ == "__main__":
    main()