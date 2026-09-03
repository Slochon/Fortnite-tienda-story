import os
import io
import math
import requests
from datetime import datetime
from zoneinfo import ZoneInfo
from PIL import Image, ImageDraw, ImageFont

W, H = 1080, 1920
API_URL = "https://fortnite-api.com/v2/shop"
OUT_DIR = "salida"
BG_PATH = "background.png"


def font(size, bold=False):
    candidates = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
        if bold else
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",

        "/usr/share/fonts/truetype/dejavu/DejaVuSansCondensed-Bold.ttf"
        if bold else
        "/usr/share/fonts/truetype/dejavu/DejaVuSansCondensed.ttf",
    ]

    for p in candidates:
        if os.path.exists(p):
            return ImageFont.truetype(p, size)

    return ImageFont.load_default()


def fit_crop(im, size):
    im = im.convert("RGBA")

    ratio = max(
        size[0] / im.width,
        size[1] / im.height
    )

    nw = int(im.width * ratio)
    nh = int(im.height * ratio)

    im = im.resize(
        (nw, nh),
        Image.Resampling.LANCZOS
    )

    left = (nw - size[0]) // 2
    top = (nh - size[1]) // 2

    return im.crop(
        (left, top, left + size[0], top + size[1])
    )


def get_shop():
    headers = {}

    key = os.getenv("FORTNITE_API_KEY")

    if key:
        headers["x-api-key"] = key

    r = requests.get(
        API_URL,
        params={"language": "es-419"},
        headers=headers,
        timeout=30
    )

    r.raise_for_status()

    data = r.json()

    print("RESPUESTA API:")
    print(data)

    return data


def get_items(data):
    shop = data.get("data", data)

    if isinstance(shop, dict):
        entries = (
            shop.get("entries")
            or shop.get("shop")
            or shop.get("items")
            or []
        )
    else:
        entries = shop if isinstance(shop, list) else []

    items = []

    for entry in entries:
        if not isinstance(entry, dict):
            continue

        br = entry.get("br") or entry.get("item") or {}

        if not isinstance(br, dict):
            br = {}

        name = (
            br.get("name")
            or entry.get("name")
            or "Objeto"
        )

        price = (
            entry.get("finalPrice")
            or entry.get("price")
            or br.get("price")
        )

        if price is None:
            price = br.get("finalPrice")

        images = br.get("images", {})

        img = (
            images.get("icon")
            if isinstance(images, dict)
            else None
        )

        img = (
            img
            or entry.get("image")
            or entry.get("icon")
        )

        if img:
            items.append({
                "name": name,
                "price": price,
                "image": img
            })

    if not items and isinstance(shop, dict):
        for key in (
            "featured",
            "daily",
            "specialFeatured",
            "specialDaily"
        ):
            for entry in shop.get(key, []) or []:

                br = (
                    entry.get("br")
                    or entry.get("item")
                    or entry
                )

                images = (
                    br.get("images", {})
                    if isinstance(br, dict)
                    else {}
                )

                img = (
                    images.get("icon")
                    if isinstance(images, dict)
                    else None
                )

                if img:
                    items.append({
                        "name": br.get(
                            "name",
                            "Objeto"
                        ),
                        "price": entry.get(
                            "finalPrice",
                            br.get("price", "?")
                        ),
                        "image": img
                    })

    seen = set()
    result = []

    for item in items:
        k = (
            item["name"],
            str(item["price"]),
            item["image"]
        )

        if k not in seen:
            seen.add(k)
            result.append(item)

    return result 


def make_page(
    bg,
    items,
    page_num,
    total_pages,
    date_text
):
    canvas = fit_crop(
        bg,
        (W, H)
    ).convert("RGBA")

    overlay = Image.new(
        "RGBA",
        (W, H),
        (0, 0, 0, 0)
    )

    d = ImageDraw.Draw(overlay)

    d.rounded_rectangle(
        (38, 145, W - 38, H - 45),
        radius=34,
        fill=(7, 12, 35, 135)
    )

    title_f = font(62, True)
    sub_f = font(28, True)

    d.text(
        (W // 2, 185),
        "TIENDA DE HOY",
        font=title_f,
        anchor="ma",
        fill="white"
    )

    d.text(
        (W // 2, 258),
        f"{date_text}  •  Página {page_num}/{total_pages}",
        font=sub_f,
        anchor="ma",
        fill=(220, 235, 255, 255)
    )

    cols = 3
    rows = 4
    gap = 18

    left = 58
    right = W - 58
    top = 325
    bottom = H - 80

    card_w = (
        right
        - left
        - gap * (cols - 1)
    ) // cols

    card_h = (
        bottom
        - top
        - gap * (rows - 1)
    ) // rows

    for idx, item in enumerate(
        items[:cols * rows]
    ):
        r, c = divmod(idx, cols)

        x = left + c * (card_w + gap)
        y = top + r * (card_h + gap)

        d.rounded_rectangle(
            (
                x,
                y,
                x + card_w,
                y + card_h
            ),
            radius=22,
            fill=(8, 15, 42, 225),
            outline=(125, 185, 255, 150),
            width=2
        )

        try:
            img_data = requests.get(
                item["image"],
                timeout=20
            ).content

            obj = Image.open(
                io.BytesIO(img_data)
            ).convert("RGBA")

            obj.thumbnail(
                (
                    card_w - 24,
                    card_h - 105
                ),
                Image.Resampling.LANCZOS
            )

            ox = (
                x
                + (card_w - obj.width) // 2
            )

            oy = y + 12

            canvas.alpha_composite(
                obj,
                (ox, oy)
            )

        except Exception as e:
            print(
                f"No se pudo cargar imagen: {e}"
            )

        name = str(item["name"])

        if len(name) > 22:
            name = name[:20] + "…"

        nf = font(22, True)
        pf = font(24, True)

        d.text(
            (
                x + card_w // 2,
                y + card_h - 62
            ),
            name,
            font=nf,
            anchor="ma",
            fill="white"
        )

        d.text(
            (
                x + card_w // 2,
                y + card_h - 29
            ),
            f"{item['price']} Pavos",
            font=pf,
            anchor="ma",
            fill=(255, 255, 255, 255)
        )

    canvas.alpha_composite(overlay)

    return canvas.convert("RGB")


def main():
    os.makedirs(
        OUT_DIR,
        exist_ok=True
    )

    data = get_shop()

    items = get_items(data)

    if not items:
        raise RuntimeError(
            "No se encontraron objetos en la respuesta de la tienda."
        )

    bg = Image.open(BG_PATH)

    now = datetime.now(
        ZoneInfo(
            "America/Argentina/Buenos_Aires"
        )
    )

    date_text = now.strftime(
        "%d/%m/%Y"
    )

    per_page = 12

    pages = math.ceil(
        len(items) / per_page
    )

    for p in range(pages):
        page_items = items[
            p * per_page:
            (p + 1) * per_page
        ]

        img = make_page(
            bg,
            page_items,
            p + 1,
            pages,
            date_text
        )

        img.save(
            f"{OUT_DIR}/tienda_{p + 1:02d}.png",
            quality=95
        )

    with open(
        f"{OUT_DIR}/ultima_actualizacion.txt",
        "w",
        encoding="utf-8"
    ) as f:
        f.write(
            f"Actualizada: {now.isoformat()}\n"
        )

        f.write(
            f"Objetos: {len(items)}\n"
        )

        f.write(
            f"Historias generadas: {pages}\n"
        )


if __name__ == "__main__":
    main()