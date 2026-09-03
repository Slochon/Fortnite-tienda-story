import html
import os
from datetime import datetime, timezone

import requests


API_URL = "https://fortnite-api.com/v2/shop?language=es-419"
OUTPUT_DIR = "salida"
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "index.html")

HEADERS = {
    "User-Agent": "Mozilla/5.0 Fortnite-Tienda-Story",
    "Accept": "application/json",
}


def descargar_tienda():
    print("Descargando tienda de Fortnite...")

    respuesta = requests.get(
        API_URL,
        headers=HEADERS,
        timeout=30,
    )

    respuesta.raise_for_status()

    data = respuesta.json()

    if not isinstance(data, dict):
        raise RuntimeError("La API no devolvió un objeto JSON válido.")

    if "data" not in data:
        raise RuntimeError("La respuesta de la API no contiene 'data'.")

    return data["data"]


def texto(valor):
    if valor is None:
        return ""

    if isinstance(valor, dict):
        return (
            valor.get("displayValue")
            or valor.get("value")
            or valor.get("name")
            or ""
        )

    return str(valor)


def obtener_secciones(shop):
    """
    Obtiene las distintas secciones de la tienda.

    La API normalmente devuelve:
      featured
      daily
      specialFeatured
      specialDaily
      etc.
    """

    secciones = []

    if not isinstance(shop, dict):
        return secciones

    orden = [
        "featured",
        "daily",
        "specialFeatured",
        "specialDaily",
        "votes",
        "voteWinners",
    ]

    for clave in orden:
        contenido = shop.get(clave)

        if not isinstance(contenido, dict):
            continue

        entries = contenido.get("entries")

        if not isinstance(entries, list):
            continue

        nombre = contenido.get("name")

        if not nombre:
            nombres = {
                "featured": "DESTACADOS",
                "daily": "DIARIOS",
                "specialFeatured": "DESTACADOS ESPECIALES",
                "specialDaily": "DIARIOS ESPECIALES",
                "votes": "VOTACIONES",
                "voteWinners": "GANADORES",
            }

            nombre = nombres.get(clave, clave.upper())

        secciones.append(
            {
                "id": clave,
                "name": nombre,
                "entries": entries,
            }
        )

    return secciones


def obtener_imagen(item):
    """
    Busca una imagen válida del objeto.

    Preferimos featured porque normalmente tiene mejor
    presentación para la tienda.
    """

    images = item.get("images")

    if not isinstance(images, dict):
        return ""

    posibles = [
        images.get("featured"),
        images.get("icon"),
        images.get("smallIcon"),
    ]

    for imagen in posibles:
        if isinstance(imagen, str) and imagen.startswith("http"):
            return imagen

    other = images.get("other")

    if isinstance(other, dict):
        for imagen in other.values():
            if isinstance(imagen, str) and imagen.startswith("http"):
                return imagen

    return ""


def obtener_nombre(item):
    nombre = item.get("name")

    if isinstance(nombre, str) and nombre.strip():
        return nombre.strip()

    return "Objeto de Fortnite"


def obtener_tipo(item):
    tipo = item.get("type")

    if isinstance(tipo, dict):
        return (
            tipo.get("displayValue")
            or tipo.get("value")
            or "Objeto"
        )

    return "Objeto"


def obtener_id(item):
    valor = item.get("id")

    if valor:
        return str(valor)

    return ""


def crear_tarjeta(item, precio, vbuck_icon):
    nombre = html.escape(obtener_nombre(item))
    tipo = html.escape(obtener_tipo(item))
    imagen = html.escape(obtener_imagen(item), quote=True)
    item_id = html.escape(obtener_id(item))

    if not imagen:
        return ""

    precio_html = ""

    if precio is not None:
        try:
            precio_numero = int(precio)
            precio_html = f"""
                <div class="precio">
                    <span>{precio_numero}</span>
                    <img src="{vbuck_icon}" alt="Pavos">
                </div>
            """
        except (ValueError, TypeError):
            pass

    return f"""
        <article class="tarjeta" data-id="{item_id}">
            <div class="imagen-contenedor">
                <img
                    class="imagen"
                    src="{imagen}"
                    alt="{nombre}"
                    loading="lazy"
                >
                <div class="brillo"></div>
            </div>

            <div class="info">
                <div class="tipo">{tipo}</div>
                <div class="nombre">{nombre}</div>
                {precio_html}
            </div>
        </article>
    """


def procesar_entrada(entry, vbuck_icon):
    if not isinstance(entry, dict):
        return []

    try:
        precio = entry.get("finalPrice")

        if precio is None:
            precio = entry.get("regularPrice")
    except Exception:
        precio = None

    items = entry.get("items")

    if not isinstance(items, list):
        items = []

    tarjetas = []

    for item in items:
        if not isinstance(item, dict):
            continue

        imagen = obtener_imagen(item)

        # No mostramos objetos que no tengan imagen.
        if not imagen:
            continue

        tarjeta = crear_tarjeta(
            item,
            precio,
            vbuck_icon,
        )

        if tarjeta:
            tarjetas.append(tarjeta)

    return tarjetas


def generar_html(shop):
    secciones = obtener_secciones(shop)

    fecha_api = shop.get("date") if isinstance(shop, dict) else None

    if fecha_api:
        fecha_mostrada = str(fecha_api)
    else:
        fecha_mostrada = datetime.now(
            timezone.utc
        ).strftime("%Y-%m-%d %H:%M UTC")

    # Icono de Pavos de respaldo.
    vbuck_icon = (
        "https://fortnite-api.com/images/vbuck.png"
    )

    contenido = []
    total_objetos = 0

    for seccion in secciones:
        tarjetas = []

        for entry in seccion["entries"]:
            tarjetas.extend(
                procesar_entrada(
                    entry,
                    vbuck_icon,
                )
            )

        if not tarjetas:
            continue

        total_objetos += len(tarjetas)

        contenido.append(
            f"""
            <section class="seccion">
                <div class="titulo-seccion">
                    <span class="linea"></span>
                    <h2>{html.escape(str(seccion["name"]))}</h2>
                    <span class="contador">{len(tarjetas)}</span>
                </div>

                <div class="grid">
                    {''.join(tarjetas)}
                </div>
            </section>
            """
        )

    if total_objetos == 0:
        raise RuntimeError(
            "No se encontraron objetos con imágenes en la tienda."
        )

    contenido_html = "\n".join(contenido)

    return f"""<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">

    <meta
        name="viewport"
        content="width=device-width, initial-scale=1.0"
    >

    <meta
        name="theme-color"
        content="#090a12"
    >

    <title>Fortnite - Tienda de objetos</title>

    <style>

        * {{
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }}

        html {{
            scroll-behavior: smooth;
        }}

        body {{
            min-height: 100vh;
            background:
                radial-gradient(
                    circle at 50% -10%,
                    rgba(88, 64, 180, 0.45),
                    transparent 35%
                ),
                linear-gradient(
                    180deg,
                    #080912 0%,
                    #101326 45%,
                    #070810 100%
                );

            color: white;
            font-family:
                Arial,
                Helvetica,
                sans-serif;

            overflow-x: hidden;
        }}

        body::before {{
            content: "";
            position: fixed;
            inset: 0;

            pointer-events: none;

            background:
                radial-gradient(
                    circle at 10% 20%,
                    rgba(0, 180, 255, 0.08),
                    transparent 25%
                ),
                radial-gradient(
                    circle at 90% 60%,
                    rgba(255, 0, 190, 0.08),
                    transparent 25%
                );

            z-index: -1;
        }}

        .cabecera {{
            padding: 38px 18px 28px;
            text-align: center;
        }}

        .logo {{
            font-size: clamp(34px, 9vw, 70px);
            font-weight: 1000;
            font-style: italic;
            letter-spacing: -3px;
            text-transform: uppercase;

            text-shadow:
                0 4px 0 rgba(0, 0, 0, 0.45),
                0 0 25px rgba(100, 150, 255, 0.35);
        }}

        .subtitulo {{
            margin-top: 8px;

            font-size: 14px;
            font-weight: 700;
            letter-spacing: 2px;

            color: #aeb5cf;
            text-transform: uppercase;
        }}

        .fecha {{
            margin-top: 14px;

            display: inline-block;

            padding: 8px 15px;

            border: 1px solid rgba(255,255,255,0.13);
            border-radius: 999px;

            background: rgba(255,255,255,0.06);

            color: #dce2f5;

            font-size: 12px;
        }}

        .seccion {{
            width: min(1200px, 100%);
            margin: 0 auto;
            padding: 10px 14px 34px;
        }}

        .titulo-seccion {{
            display: flex;
            align-items: center;
            gap: 12px;

            margin: 10px 0 16px;
        }}

        .titulo-seccion .linea {{
            width: 5px;
            height: 28px;

            border-radius: 5px;

            background:
                linear-gradient(
                    180deg,
                    #8c6cff,
                    #35c7ff
                );

            box-shadow:
                0 0 15px rgba(95, 110, 255, 0.65);
        }}

        .titulo-seccion h2 {{
            font-size: 23px;
            font-weight: 900;
            letter-spacing: 0.5px;
        }}

        .contador {{
            display: flex;
            align-items: center;
            justify-content: center;

            min-width: 28px;
            height: 28px;

            padding: 0 8px;

            border-radius: 8px;

            background: rgba(255,255,255,0.09);

            color: #bfc7df;

            font-size: 12px;
            font-weight: 800;
        }}

        .grid {{
            display: grid;

            grid-template-columns:
                repeat(
                    auto-fill,
                    minmax(160px, 1fr)
                );

            gap: 14px;
        }}

        .tarjeta {{
            position: relative;

            overflow: hidden;

            min-width: 0;

            border-radius: 17px;

            background:
                linear-gradient(
                    145deg,
                    rgba(255,255,255,0.12),
                    rgba(255,255,255,0.035)
                );

            border: 1px solid
                rgba(255,255,255,0.11);

            box-shadow:
                0 12px 30px
                rgba(0,0,0,0.28);

            transition:
                transform 0.2s ease,
                border-color 0.2s ease;
        }}

        .tarjeta:active {{
            transform: scale(0.97);
        }}

        .imagen-contenedor {{
            position: relative;

            width: 100%;
            aspect-ratio: 1 / 1.12;

            overflow: hidden;

            background:
                radial-gradient(
                    circle,
                    rgba(100,130,255,0.20),
                    rgba(5,7,15,0.8)
                );
        }}

        .imagen {{
            width: 100%;
            height: 100%;

            display: block;

            object-fit: cover;

            transition:
                transform 0.35s ease;
        }}

        .tarjeta:hover .imagen {{
            transform: scale(1.035);
        }}

        .brillo {{
            position: absolute;
            inset: 0;

            pointer-events: none;

            background:
                linear-gradient(
                    135deg,
                    rgba(255,255,255,0.13),
                    transparent 30%,
                    transparent 70%,
                    rgba(80,120,255,0.10)
                );
        }}

        .info {{
            padding: 11px 11px 13px;
        }}

        .tipo {{
            margin-bottom: 4px;

            color: #8f98b5;

            font-size: 10px;
            font-weight: 800;

            text-transform: uppercase;
            letter-spacing: 1px;
        }}

        .nombre {{
            min-height: 34px;

            color: white;

            font-size: 15px;
            font-weight: 850;

            line-height: 1.12;
        }}

        .precio {{
            display: flex;
            align-items: center;
            gap: 5px;

            margin-top: 9px;

            font-size: 17px;
            font-weight: 950;
        }}

        .precio img {{
            width: 20px;
            height: 20px;

            object-fit: contain;
        }}

        .pie {{
            padding: 35px 20px 50px;

            text-align: center;

            color: #69718d;

            font-size: 11px;
            line-height: 1.6;
        }}

        @media (max-width: 520px) {{

            .cabecera {{
                padding-top: 30px;
            }}

            .grid {{
                grid-template-columns:
                    repeat(2, minmax(0, 1fr));

                gap: 10px;
            }}

            .seccion {{
                padding-left: 10px;
                padding-right: 10px;
            }}

            .titulo-seccion h2 {{
                font-size: 19px;
            }}

            .nombre {{
                font-size: 14px;
            }}

            .precio {{
                font-size: 16px;
            }}
        }}

        @media (min-width: 900px) {{

            .grid {{
                grid-template-columns:
                    repeat(5, minmax(0, 1fr));
            }}
        }}

    </style>
</head>

<body>

    <header class="cabecera">

        <div class="logo">
            FORTNITE
        </div>

        <div class="subtitulo">
            Tienda de objetos
        </div>

        <div class="fecha">
            Actualizada: {html.escape(fecha_mostrada)}
        </div>

    </header>

    <main>
        {contenido_html}
    </main>

    <footer class="pie">
        Tienda generada automáticamente<br>
        {total_objetos} objetos con imagen
    </footer>

</body>
</html>
"""


def main():
    os.makedirs(
        OUTPUT_DIR,
        exist_ok=True
    )

    shop = descargar_tienda()

    html_final = generar_html(shop)

    with open(
        OUTPUT_FILE,
        "w",
        encoding="utf-8"
    ) as archivo:
        archivo.write(html_final)

    print()
    print("====================================")
    print(" TIENDA GENERADA CORRECTAMENTE")
    print("====================================")
    print(f"Archivo: {OUTPUT_FILE}")
    print("====================================")


if __name__ == "__main__":
    main() 