import html
import os
import requests


API_URL = "https://fortnite-api.com/v2/shop?language=es-419"
OUTPUT_DIR = "salida"
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "index.html")


def obtener_tienda():
    print("Consultando Fortnite-API...")

    response = requests.get(
        API_URL,
        timeout=30,
        headers={
            "User-Agent": "Fortnite-Tienda-Story/1.0",
            "Accept": "application/json",
        },
    )

    print("HTTP:", response.status_code)

    response.raise_for_status()

    return response.json()


def buscar_objetos(data):
    """
    Busca objetos de forma flexible dentro de la respuesta.
    No asumimos una única estructura de la API.
    """

    if not isinstance(data, dict):
        return []

    data = data.get("data", data)

    if isinstance(data, list):
        return data

    if not isinstance(data, dict):
        return []

    # Estructuras habituales
    for key in ("entries", "items", "shop"):
        value = data.get(key)

        if isinstance(value, list):
            return value

        if isinstance(value, dict):
            entries = value.get("entries")

            if isinstance(entries, list):
                return entries

    # Buscar recursivamente listas de diccionarios
    def recorrer(obj):
        if isinstance(obj, list):
            if obj and all(isinstance(x, dict) for x in obj):
                return obj

            for elemento in obj:
                resultado = recorrer(elemento)

                if resultado:
                    return resultado

        elif isinstance(obj, dict):
            for value in obj.values():
                resultado = recorrer(value)

                if resultado:
                    return resultado

        return []

    return recorrer(data)


def obtener_item(entry):
    for key in ("brItems", "items", "grants"):
        value = entry.get(key)

        if isinstance(value, list) and value:
            if isinstance(value[0], dict):
                return value[0]

        if isinstance(value, dict):
            return value

    return entry


def obtener_nombre(entry):
    item = obtener_item(entry)

    for key in ("name", "displayName", "title"):
        value = item.get(key)

        if value:
            return str(value)

    for key in ("displayName", "name", "title"):
        value = entry.get(key)

        if value:
            return str(value)

    return "Objeto Fortnite"


def obtener_imagen(entry):
    item = obtener_item(entry)

    objetos = [item, entry]

    for obj in objetos:
        if not isinstance(obj, dict):
            continue

        images = obj.get("images")

        if isinstance(images, dict):
            for key in (
                "featured",
                "icon",
                "large",
                "smallIcon",
            ):
                url = images.get(key)

                if isinstance(url, str) and url.startswith("http"):
                    return url

        for key in (
            "icon",
            "image",
            "featuredImage",
        ):
            url = obj.get(key)

            if isinstance(url, str) and url.startswith("http"):
                return url

    return None


def obtener_precio(entry):
    for key in (
        "finalPrice",
        "regularPrice",
        "price",
    ):
        value = entry.get(key)

        if value is not None:
            try:
                return int(value)
            except (TypeError, ValueError):
                pass

    return 0


def escapar(value):
    return html.escape(str(value))


def crear_html(objetos):
    tarjetas = []

    for numero, entry in enumerate(objetos, start=1):

        if not isinstance(entry, dict):
            continue

        imagen = obtener_imagen(entry)

        if not imagen:
            continue

        nombre = obtener_nombre(entry)
        precio = obtener_precio(entry)

        tarjetas.append(
            f"""
            <article class="card">

                <div class="numero">
                    #{numero}
                </div>

                <img
                    src="{escapar(imagen)}"
                    alt="{escapar(nombre)}"
                    loading="lazy"
                >

                <div class="info">

                    <div class="nombre">
                        {escapar(nombre)}
                    </div>

                    <div class="precio">
                        <span class="vbucks">V</span>
                        {precio:,}
                    </div>

                </div>

            </article>
            """
        )

    if not tarjetas:
        raise RuntimeError(
            "La API respondió, pero no encontramos objetos "
            "con imágenes válidas."
        )

    contenido = "\n".join(tarjetas)

    return f"""
<!DOCTYPE html>
<html lang="es">

<head>

<meta charset="UTF-8">

<meta
    name="viewport"
    content="width=device-width, initial-scale=1.0"
>

<title>Tienda Fortnite</title>

<style>

* {{
    box-sizing: border-box;
}}

body {{
    margin: 0;

    font-family:
        Arial,
        Helvetica,
        sans-serif;

    color: white;

    background:
        radial-gradient(
            circle at top,
            #315b9e,
            #17284f 35%,
            #080c1a 80%
        );
}}

header {{
    padding: 30px 15px;

    text-align: center;

    background:
        linear-gradient(
            180deg,
            rgba(44,72,137,.95),
            rgba(8,12,27,.2)
        );

    box-shadow:
        0 8px 30px
        rgba(0,0,0,.45);
}}

.titulo {{
    font-size: clamp(32px, 9vw, 58px);

    font-weight: 1000;

    letter-spacing: 2px;

    text-transform: uppercase;

    text-shadow:
        0 4px 0 #111,
        0 8px 25px rgba(0,0,0,.7);
}}

.subtitulo {{
    margin-top: 8px;

    font-size: 13px;

    opacity: .75;
}}

.contenedor {{
    max-width: 1200px;

    margin: auto;

    padding: 15px 10px 40px;
}}

.tienda {{
    display: grid;

    grid-template-columns:
        repeat(
            auto-fit,
            minmax(160px, 1fr)
        );

    gap: 13px;
}}

.card {{
    position: relative;

    overflow: hidden;

    border-radius: 16px;

    background:
        linear-gradient(
            145deg,
            #3b5791,
            #11182f
        );

    border:
        1px solid
        rgba(255,255,255,.18);

    box-shadow:
        0 10px 25px
        rgba(0,0,0,.4);
}}

.card img {{
    display: block;

    width: 100%;

    aspect-ratio: 1 / 1;

    object-fit: cover;

    background: #182342;
}}

.numero {{
    position: absolute;

    top: 8px;
    left: 8px;

    z-index: 2;

    padding: 4px 7px;

    border-radius: 6px;

    background:
        rgba(0,0,0,.6);

    font-size: 10px;

    font-weight: bold;
}}

.info {{
    padding: 10px 11px 13px;
}}

.nombre {{
    min-height: 38px;

    display: flex;

    align-items: center;

    font-size: 14px;

    line-height: 1.15;

    font-weight: 900;

    text-shadow:
        0 2px 5px
        rgba(0,0,0,.8);
}}

.precio {{
    display: flex;

    align-items: center;

    gap: 7px;

    margin-top: 7px;

    font-size: 18px;

    font-weight: 1000;
}}

.vbucks {{
    display: flex;

    align-items: center;

    justify-content: center;

    width: 23px;
    height: 23px;

    border-radius: 50%;

    background:
        linear-gradient(
            135deg,
            #62dcff,
            #1675e4
        );

    border:
        2px solid white;

    font-size: 12px;
}}

footer {{
    padding: 10px 20px 35px;

    text-align: center;

    font-size: 11px;

    opacity: .5;
}}

@media (max-width: 420px) {{

    .tienda {{
        grid-template-columns:
            repeat(2, 1fr);

        gap: 9px;
    }}

    .nombre {{
        font-size: 13px;
    }}

    .precio {{
        font-size: 16px;
    }}

}}

</style>

</head>

<body>

<header>

    <div class="titulo">
        TIENDA FORTNITE
    </div>

    <div class="subtitulo">
        Tienda actualizada automáticamente
    </div>

</header>

<main class="contenedor">

    <section class="tienda">

        {contenido}

    </section>

</main>

<footer>
    Fortnite Tienda Story
</footer>

</body>

</html>
"""


def main():

    os.makedirs(
        OUTPUT_DIR,
        exist_ok=True
    )

    data = obtener_tienda()

    objetos = buscar_objetos(data)

    print(
        "Objetos encontrados:",
        len(objetos)
    )

    if not objetos:
        raise RuntimeError(
            "No se encontraron objetos en la respuesta de la API."
        )

    html_final = crear_html(objetos)

    with open(
        OUTPUT_FILE,
        "w",
        encoding="utf-8"
    ) as archivo:

        archivo.write(html_final)

    cantidad = html_final.count(
        '<article class="card">'
    )

    print(
        "Tarjetas generadas:",
        cantidad
    )

    print(
        "Página creada:",
        OUTPUT_FILE
    )


if __name__ == "__main__":
    main()