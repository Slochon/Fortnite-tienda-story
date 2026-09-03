import os #
import html
import requests

API_URL = "https://fortnite-api.com/v2/shop?language=es-419"
SALIDA = "salida"
ARCHIVO = os.path.join(SALIDA, "index.html")


def obtener_tienda():
    r = requests.get(API_URL, timeout=30)
    r.raise_for_status()
    return r.json()


def encontrar_ofertas(data):
    data = data.get("data", data)

    if isinstance(data, dict):
        for clave in ("entries", "shop", "offers"):
            if isinstance(data.get(clave), list):
                return data[clave]

    if isinstance(data, list):
        return data

    return []


def encontrar_item(oferta):
    for clave in ("brItems", "items", "itemGrants", "cosmetics"):
        valor = oferta.get(clave)

        if isinstance(valor, list) and valor:
            return valor[0]

        if isinstance(valor, dict):
            return valor

    return {}


def nombre_item(oferta, item):
    for valor in (
        item.get("name"),
        item.get("displayName"),
        oferta.get("name"),
        oferta.get("displayName"),
        oferta.get("title"),
    ):
        if isinstance(valor, str) and valor.strip():
            return valor.strip()

    return "Objeto"


def imagen_item(oferta, item):
    candidatos = []

    imagenes = item.get("images", {})

    if isinstance(imagenes, dict):
        candidatos += [
            imagenes.get("featured"),
            imagenes.get("icon"),
            imagenes.get("smallIcon"),
        ]

    candidatos += [
        item.get("featuredImage"),
        item.get("icon"),
        item.get("image"),
    ]

    imagenes = oferta.get("images", {})

    if isinstance(imagenes, dict):
        candidatos += [
            imagenes.get("featured"),
            imagenes.get("icon"),
            imagenes.get("smallIcon"),
        ]

    candidatos += [
        oferta.get("featuredImage"),
        oferta.get("image"),
    ]

    for url in candidatos:
        if isinstance(url, str) and url.startswith("http"):
            return url

    return ""


def precio_item(oferta):
    for clave in ("finalPrice", "price", "regularPrice"):
        valor = oferta.get(clave)

        if isinstance(valor, (int, float)):
            return int(valor)

        if isinstance(valor, dict):
            for subclave in (
                "finalPrice",
                "price",
                "regularPrice",
            ):
                numero = valor.get(subclave)

                if isinstance(numero, (int, float)):
                    return int(numero)

    return 0


def generar():
    print("Obteniendo tienda...")

    data = obtener_tienda()
    ofertas = encontrar_ofertas(data)

    print("Ofertas encontradas:", len(ofertas))

    objetos = []
    vistos = set()

    for oferta in ofertas:
        if not isinstance(oferta, dict):
            continue

        item = encontrar_item(oferta)

        nombre = nombre_item(oferta, item)
        imagen = imagen_item(oferta, item)
        precio = precio_item(oferta)

        if not imagen:
            continue

        clave = (nombre, imagen)

        if clave in vistos:
            continue

        vistos.add(clave)

        objetos.append({
            "nombre": nombre,
            "imagen": imagen,
            "precio": precio
        })

    print("Objetos con imagen:", len(objetos))

    if not objetos:
        raise RuntimeError(
            "No se encontraron objetos con imagen."
        )

    os.makedirs(SALIDA, exist_ok=True)

    # Limpiar imágenes antiguas
    for archivo in os.listdir(SALIDA):
        ruta = os.path.join(SALIDA, archivo)

        if os.path.isfile(ruta):
            os.remove(ruta)

    tarjetas = []

    for objeto in objetos:
        nombre = html.escape(objeto["nombre"])
        imagen = html.escape(
            objeto["imagen"],
            quote=True
        )

        precio = objeto["precio"]

        if precio:
            precio_html = f"""
            <div class="precio">
                <span class="v">V</span>
                {precio:,}
            </div>
            """.replace(",", ".")
        else:
            precio_html = """
            <div class="precio">
                GRATIS
            </div>
            """

        tarjetas.append(f"""
        <div class="card">

            <div class="foto">
                <img
                    src="{imagen}"
                    alt="{nombre}"
                    loading="lazy"
                    onerror="this.parentElement.parentElement.remove()"
                >
            </div>

            <div class="datos">

                <div class="nombre">
                    {nombre}
                </div>

                {precio_html}

            </div>

        </div>
        """)

    pagina = f"""<!DOCTYPE html>
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
            #34346b,
            #0b0c19 55%,
            #05060d
        );
}}

header {{
    padding: 30px 15px;

    text-align: center;

    position: sticky;
    top: 0;

    z-index: 10;

    background:
        rgba(8,9,20,.92);

    backdrop-filter:
        blur(12px);

    border-bottom:
        1px solid
        rgba(255,255,255,.12);
}}

h1 {{
    margin: 0;

    font-size: 30px;

    font-weight: 1000;

    font-style: italic;
}}

.sub {{
    margin-top: 7px;

    color: #bfc1dc;

    font-size: 12px;
}}

.contenedor {{
    width: 100%;

    max-width: 1500px;

    margin: auto;

    padding: 15px 10px 40px;
}}

.grid {{
    display: grid;

    grid-template-columns:
        repeat(2, minmax(0, 1fr));

    gap: 9px;
}}

.card {{
    overflow:hidden;border-radius:13px;
background:linear-gradient(145deg,#292c52,#10111f);
border:1px solid rgba(255,255,255,.12);
box-shadow:0 5px 18px rgba(0,0,0,.35)
}
.imagen{aspect-ratio:1/1;overflow:hidden;background:#171827}
.imagen img{display:block;width:100%;height:100%;object-fit:cover}
.info{padding:9px 8px 11px}
.nombre{font-size:13px;font-weight:800;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.precio{margin-top:6px;font-size:15px;font-weight:900}
.pavos{
display:inline-flex;align-items:center;justify-content:center;
width:20px;height:20px;border-radius:50%;
background:#e9edf7;color:#222;font-size:12px
}
@media(min-width:700px){
.grid{grid-template-columns:repeat(3,minmax(0,1fr));gap:12px}
}
@media(min-width:1100px){
.grid{grid-template-columns:repeat(4,minmax(0,1fr));gap:14px}
}
@media(min-width:1500px){
.grid{grid-template-columns:repeat(5,minmax(0,1fr))}
}
</style>
</head>
<body>
<header>
<h1>TIENDA DE FORTNITE</h1>
<div class="sub">Objetos disponibles hoy</div>
</header>
<main class="contenedor">
<section class="grid">
""" + tarjetas + """
</section>
</main>
</body>
</html>
"""


def main():
    print("Obteniendo tienda de Fortnite...")

    datos = obtener_tienda()
    ofertas = encontrar_ofertas(datos)

    print("Ofertas encontradas:", len(ofertas))

    objetos = []
    vistos = set()

    for oferta in ofertas:
        if not isinstance(oferta, dict):
            continue

        item = encontrar_item(oferta)
        nombre = obtener_nombre(oferta, item)
        imagen = obtener_imagen(oferta, item)
        precio = obtener_precio(oferta)

        if not imagen:
            continue

        clave = (nombre, imagen)

        if clave in vistos:
            continue

        vistos.add(clave)
        objetos.append({
            "nombre": nombre,
            "imagen": imagen,
            "precio": precio
        })

    print("Objetos con imagen:", len(objetos))

    if not objetos:
        raise RuntimeError("No se encontraron objetos con imagen.")

    os.makedirs(SALIDA, exist_ok=True)

    for archivo in os.listdir(SALIDA):
        ruta = os.path.join(SALIDA, archivo)
        if os.path.isfile(ruta):
            os.remove(ruta)

    with open(ARCHIVO, "w", encoding="utf-8") as archivo:
        archivo.write(crear_html(objetos))

    print("OK: HTML GENERADO")
    print("Archivo:", ARCHIVO)


if __name__ == "__main__":
    main()
