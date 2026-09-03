import os
import io
from datetime import datetime

import requests
from PIL import Image, ImageDraw, ImageFont, ImageFilter


API_URL = "https://fortnite-api.com/v2/shop?language=es-419"

OUTPUT_DIR = "salida"
BACKGROUND_FILE = "background.png"

ANCHO = 1080
ALTO = 1920

COLUMNAS = 2
FILAS = 4

MARGEN_X = 45
MARGEN_TOP = 245
MARGEN_BOTTOM = 125

ESPACIO_X = 22
ESPACIO_Y = 22


def fuente(tamano, negrita=False):
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


FUENTE_TITULO = fuente(58, True)
FUENTE_FECHA = fuente(30, True)
FUENTE_NOMBRE = fuente(25, True)
FUENTE_TIPO = fuente(18, False)
FUENTE_PRECIO = fuente(28, True)
FUENTE_PIE = fuente(22, True)


def descargar(url):
    if not url:
        return None

    try:
        respuesta = requests.get(url, timeout=30)
        respuesta.raise_for_status()

        return Image.open(
            io.BytesIO(respuesta.content)
        ).convert("RGBA")

    except Exception as error:
        print("No se pudo descargar imagen:", error)
        return None


def obtener_tienda():
    print("Consultando Fortnite-API...")

    respuesta = requests.get(
        API_URL,
        timeout=30,
    )

    respuesta.raise_for_status()

    datos = respuesta.json()

    if not isinstance(datos, dict):
        raise RuntimeError(
            "La respuesta de la API no es válida."
        )

    data = datos.get("data")

    if not isinstance(data, dict):
        raise RuntimeError(
            "La API no contiene 'data'."
        )

    entries = data.get("entries")

    if not isinstance(entries, list):
        raise RuntimeError(
            "La API no contiene 'entries'."
        )

    fecha = data.get("date")

    print("Entradas recibidas:", len(entries))
    print("Fecha de la tienda:", fecha)

    return entries, fecha


def imagen_de_entry(entry):
    asset = entry.get("newDisplayAsset")

    if isinstance(asset, dict):
        renders = asset.get("renderImages")

        if isinstance(renders, list):
            for render in renders:
                if isinstance(render, dict):
                    url = render.get("image")

                    if url:
                        return url

    items = entry.get("brItems")

    if isinstance(items, list):
        for item in items:
            if not isinstance(item, dict):
                continue

            images = item.get("images")

            if isinstance(images, dict):
                for clave in (
                    "featured",
                    "icon",
                    "background",
                ):
                    url = images.get(clave)

                    if url:
                        return url

    return None


def nombre_de_entry(entry):
    items = entry.get("brItems")

    if isinstance(items, list) and items:
        primero = items[0]

        if isinstance(primero, dict):
            nombre = (
                primero.get("name")
                or primero.get("displayName")
                or primero.get("id")
            )

            if nombre:
                return str(nombre)

    dev_name = entry.get("devName")

    if dev_name:
        texto = str(dev_name)

        if " x " in texto:
            texto = texto.split(" x ", 1)[1]

        if " for " in texto:
            texto = texto.split(" for ", 1)[0]

        return texto.strip()

    return "Objeto de Fortnite"


def tipo_de_entry(entry):
    items = entry.get("brItems")

    if not isinstance(items, list) or not items:
        return "OFERTA"

    tipos = []

    for item in items:
        if not isinstance(item, dict):
            continue

        tipo = item.get("type")

        if isinstance(tipo, dict):
            valor = tipo.get("displayValue")
            if valor:
                tipos.append(str(valor))

        elif tipo:
            tipos.append(str(tipo))

    if tipos:
        return tipos[0].upper()

    return "OFERTA"


def preparar_objetos(entries):
    objetos = []

    for entry in entries:
        if not isinstance(entry, dict):
            continue

        precio = entry.get("finalPrice")

        if precio is None:
            continue

        objetos.append({
            "nombre": nombre_de_entry(entry),
            "tipo": tipo_de_entry(entry),
            "precio": precio,
            "imagen": imagen_de_entry(entry),
            "entrada": entry,
        })

    print("Ofertas válidas:", len(objetos))

    return objetos


def preparar_fondo():
    if os.path.exists(BACKGROUND_FILE):
        try:
            original = Image.open(
                BACKGROUND_FILE
            ).convert("RGBA")

            original.thumbnail(
                (ANCHO, ALTO),
                Image.Resampling.LANCZOS,
            )

            fondo = Image.new(
                "RGBA",
                (ANCHO, ALTO),
                (20, 10, 35, 255),
            )

            x = (ANCHO - original.width) // 2
            y = (ALTO - original.height) // 2

            fondo.alpha_composite(
                original,
                (x, y),
            )

            return fondo

        except Exception as error:
            print("Error con background.png:", error)

    return Image.new(
        "RGBA",
        (ANCHO, ALTO),
        (20, 10, 35, 255),
    )
def texto_centrado(draw, texto, y, tipo_fuente, ancho=ANCHO):
    caja = draw.textbbox(
        (0, 0),
        texto,
        font=tipo_fuente,
    )

    ancho_texto = caja[2] - caja[0]

    draw.text(
        (
            (ancho - ancho_texto) // 2,
            y,
        ),
        texto,
        font=tipo_fuente,
        fill="white",
    )


def tarjeta_objeto(objeto, ancho, alto):
    tarjeta = Image.new(
        "RGBA",
        (ancho, alto),
        (20, 15, 35, 245),
    )

    draw = ImageDraw.Draw(tarjeta)

    # Borde luminoso
    draw.rounded_rectangle(
        (2, 2, ancho - 3, alto - 3),
        radius=24,
        outline=(210, 150, 255, 210),
        width=3,
    )

    # Imagen del objeto
    imagen = descargar(objeto.get("imagen"))

    if imagen:
        espacio = (
            ancho - 30,
            alto - 135,
        )

        imagen.thumbnail(
            espacio,
            Image.Resampling.LANCZOS,
        )

        ix = (ancho - imagen.width) // 2
        iy = 15

        tarjeta.alpha_composite(
            imagen,
            (ix, iy),
        )

    # Zona inferior
    zona_y = alto - 115

    draw.rounded_rectangle(
        (
            10,
            zona_y,
            ancho - 10,
            alto - 10,
        ),
        radius=18,
        fill=(10, 8, 20, 220),
    )

    nombre = objeto.get(
        "nombre",
        "Objeto",
    )

    nombre = str(nombre)

    if len(nombre) > 25:
        nombre = nombre[:22] + "..."

    caja = draw.textbbox(
        (0, 0),
        nombre,
        font=FUENTE_NOMBRE,
    )

    nombre_ancho = caja[2] - caja[0]

    draw.text(
        (
            (ancho - nombre_ancho) // 2,
            zona_y + 12,
        ),
        nombre,
        font=FUENTE_NOMBRE,
        fill="white",
    )

    tipo = str(
        objeto.get(
            "tipo",
            "OFERTA",
        )
    )

    caja = draw.textbbox(
        (0, 0),
        tipo,
        font=FUENTE_TIPO,
    )

    tipo_ancho = caja[2] - caja[0]

    draw.text(
        (
            (ancho - tipo_ancho) // 2,
            zona_y + 48,
        ),
        tipo,
        font=FUENTE_TIPO,
        fill=(210, 180, 255),
    )

    precio = objeto.get("precio")

    if precio is not None:
        precio_texto = f"{precio:,} PAVOS".replace(
            ",",
            ".",
        )

        caja = draw.textbbox(
            (0, 0),
            precio_texto,
            font=FUENTE_PRECIO,
        )

        precio_ancho = caja[2] - caja[0]

        draw.text(
            (
                (ancho - precio_ancho) // 2,
                zona_y + 72,
            ),
            precio_texto,
            font=FUENTE_PRECIO,
            fill=(255, 220, 120),
        )

    return tarjeta


def crear_pagina(objetos, numero, total, fecha):
    fondo = preparar_fondo()

    # Capa oscura para que el texto se lea mejor
    oscura = Image.new(
        "RGBA",
        (ANCHO, ALTO),
        (0, 0, 0, 70),
    )

    fondo.alpha_composite(oscura)

    draw = ImageDraw.Draw(fondo)

    # Título
    texto_centrado(
        draw,
        "TIENDA DE FORTNITE",
        42,
        FUENTE_TITULO,
    )

    # Fecha
    fecha_texto = "ACTUALIZACIÓN DIARIA"

    if fecha:
        try:
            fecha_dt = datetime.fromisoformat(
                str(fecha).replace(
                    "Z",
                    "+00:00",
                )
            )

            fecha_texto += (
                "  •  "
                + fecha_dt.strftime("%d/%m/%Y")
            )

        except Exception:
            pass

    texto_centrado(
        draw,
        fecha_texto,
        120,
        FUENTE_FECHA,
    )

    # Indicador de página
    pagina = f"PÁGINA {numero} / {total}"

    texto_centrado(
        draw,
        pagina,
        170,
        FUENTE_FECHA,
    )

    tarjetas = objetos

    area_ancho = ANCHO - (
        MARGEN_X * 2
    )

    tarjeta_ancho = (
        area_ancho
        - ESPACIO_X
    ) // COLUMNAS

    area_alto = (
        ALTO
        - MARGEN_TOP
        - MARGEN_BOTTOM
    )

    tarjeta_alto = (
        area_alto
        - ESPACIO_Y * (FILAS - 1)
    ) // FILAS

    for indice, objeto in enumerate(tarjetas):
        fila = indice // COLUMNAS
        columna = indice % COLUMNAS

        x = (
            MARGEN_X
            + columna
            * (tarjeta_ancho + ESPACIO_X)
        )

        y = (
            MARGEN_TOP
            + fila
            * (tarjeta_alto + ESPACIO_Y)
        )

        tarjeta = tarjeta_objeto(
            objeto,
            tarjeta_ancho,
            tarjeta_alto,
        )

        fondo.alpha_composite(
            tarjeta,
            (x, y),
        )

    # Pie de página
    pie = "SLOCHON  •  TIENDA DIARIA"

    texto_centrado(
        draw,
        pie,
        ALTO - 75,
        FUENTE_PIE,
    )

    return fondo
def guardar_paginas(objetos, fecha):
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # Borrar imágenes anteriores para evitar
    # que queden páginas viejas.
    for archivo in os.listdir(OUTPUT_DIR):
        if archivo.lower().endswith(".png"):
            try:
                os.remove(
                    os.path.join(
                        OUTPUT_DIR,
                        archivo,
                    )
                )
            except OSError:
                pass

    objetos_por_pagina = COLUMNAS * FILAS

    total_paginas = (
        len(objetos) + objetos_por_pagina - 1
    ) // objetos_por_pagina

    if total_paginas == 0:
        raise RuntimeError(
            "No hay objetos para generar."
        )

    print(
        "Se generarán",
        total_paginas,
        "páginas."
    )

    for numero in range(1, total_paginas + 1):
        inicio = (
            numero - 1
        ) * objetos_por_pagina

        fin = (
            inicio + objetos_por_pagina
        )

        objetos_pagina = objetos[
            inicio:fin
        ]

        imagen = crear_pagina(
            objetos_pagina,
            numero,
            total_paginas,
            fecha,
        )

        archivo = os.path.join(
            OUTPUT_DIR,
            f"tienda_{numero:02d}.png",
        )

        imagen.convert("RGB").save(
            archivo,
            "PNG",
            optimize=True,
        )

        print(
            "Creada:",
            archivo,
        )


def main():
    print("=" * 50)
    print("GENERADOR DE TIENDA FORTNITE")
    print("=" * 50)

    try:
        entries, fecha = obtener_tienda()

        objetos = preparar_objetos(
            entries
        )

        if not objetos:
            raise RuntimeError(
                "No se encontraron ofertas "
                "válidas en la tienda."
            )

        guardar_paginas(
            objetos,
            fecha,
        )

        print("=" * 50)
        print("TIENDA GENERADA CORRECTAMENTE")
        print("=" * 50)

    except requests.RequestException as error:
        raise RuntimeError(
            "Error conectando con Fortnite-API: "
            + str(error)
        ) from error


if __name__ == "__main__":
    main()