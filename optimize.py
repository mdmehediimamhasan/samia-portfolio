"""Speed up the portfolio: small WebP thumbnails for galleries, lighter effects.
Usage: python optimize.py <site-folder>   (safe to run more than once)"""
import os, re, sys
from PIL import Image

site = sys.argv[1] if len(sys.argv) > 1 else "."
img_dir = os.path.join(site, "images")
thumb_dir = os.path.join(img_dir, "thumbs")
os.makedirs(thumb_dir, exist_ok=True)

# 1. thumbnails (dashboards wider, everything else 800px)
for name in os.listdir(img_dir):
    if not name.lower().endswith(".jpg"):
        continue
    width = 1100 if name.startswith("dash-") else 800
    im = Image.open(os.path.join(img_dir, name)).convert("RGB")
    if im.width > width:
        im = im.resize((width, round(im.height * width / im.width)), Image.LANCZOS)
    im.save(os.path.join(thumb_dir, name[:-4] + ".webp"), "WEBP", quality=78, method=6)

# 2. patch index.html
path = os.path.join(site, "index.html")
html = open(path, encoding="utf-8").read()
if "images/thumbs/" not in html:
    # remove the full-screen animated grain layer (expensive to repaint on scroll)
    html = re.sub(r'body::before\{content:"";position:fixed;inset:0;pointer-events:none;z-index:200;opacity:\.035;\s*'
                  r'background-image:url\("data:image/svg\+xml,[^"]*"\)\}', "", html)
    # lighter nav blur
    html = html.replace("backdrop-filter:blur(14px);-webkit-backdrop-filter:blur(14px)",
                        "backdrop-filter:blur(8px);-webkit-backdrop-filter:blur(8px)")
    # helper that maps a full image path to its thumbnail
    html = html.replace("const $ = s => document.querySelector(s);",
                        "const $ = s => document.querySelector(s);\n"
                        "const thumb = s => s.replace('images/','images/thumbs/').replace(/\\.jpg$/,'.webp');", 1)
    # galleries and dashboards use thumbnails; the lightbox still opens the full image
    html = html.replace('<img src="${item.img}"', '<img src="${thumb(item.img)}" decoding="async"')
    html = html.replace('<img src="${p.img}" alt="${esc(p.title)} dashboard screenshot"',
                        '<img src="${thumb(p.img)}" decoding="async" alt="${esc(p.title)} dashboard screenshot"')
    for f in ("sketch-teacup", "photo-archway"):
        html = html.replace(f'src="images/{f}.jpg"', f'src="images/thumbs/{f}.webp" decoding="async"')
    open(path, "w", encoding="utf-8").write(html)
print("optimized", site)
