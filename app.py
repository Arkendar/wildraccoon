"""
app.py — Столярная мастерская «Дикий Енот»

Структура данных (catalog.json):
{
  "gazebos": [
    {
      "id": "abc12345",
      "title": "Беседка 3×4 м",
      "desc": "Описание...",
      "images": ["catalog/gazebos/abc12345/фото1.webp", ...]
    }, ...
  ],
  "houses": [...],
  ...
}

Запуск: python app.py
Сайт:    http://localhost:5000
Админка: http://localhost:5000/admin
"""

import json, uuid, secrets, shutil
from pathlib import Path
from functools import wraps
from flask import (
    Flask, request, redirect, url_for,
    session, render_template, render_template_string,
    jsonify, send_from_directory, abort
)
from PIL import Image

app = Flask(__name__)
app.secret_key = secrets.token_hex(32)

BASE_DIR     = Path(__file__).parent
IMAGES_DIR   = BASE_DIR / "static" / "images" / "catalog"
CATALOG_FILE = BASE_DIR / "catalog.json"

ADMIN_PASSWORD = "dikenot2025"   # ← СМЕНИ НА СВОЙ
WEBP_QUALITY   = 82
MAX_IMG_SIZE   = (1600, 1600)
ALLOWED_EXT    = {".jpg", ".jpeg", ".png", ".webp", ".heic", ".heif"}
app.config["MAX_CONTENT_LENGTH"] = 50 * 1024 * 1024  # 50 МБ

# Фиксированные категории верхнего уровня
TOP_CATEGORIES = [
    {"key": "gazebos",  "title": "Беседки",               "icon": "fas fa-home"},
    {"key": "houses",   "title": "Дома",                  "icon": "fas fa-building"},
    {"key": "baths",    "title": "Бани",                  "icon": "fas fa-fire"},
    {"key": "antique",  "title": "Стиль «Под старину»",   "icon": "fas fa-landmark"},
    {"key": "figures",  "title": "Деревянные фигуры",     "icon": "fas fa-dragon"},
    {"key": "garden",   "title": "Садовая мебель и декор","icon": "fas fa-leaf"},
]


# ══════════════════════════════════════════════════════
#  catalog.json helpers
# ══════════════════════════════════════════════════════

def load_catalog():
    if CATALOG_FILE.exists():
        with open(CATALOG_FILE, encoding="utf-8") as f:
            return json.load(f)
    default = {cat["key"]: [] for cat in TOP_CATEGORIES}
    save_catalog(default)
    return default

def save_catalog(data):
    with open(CATALOG_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def find_sub(catalog, cat_key, sub_id):
    for s in catalog.get(cat_key, []):
        if s["id"] == sub_id:
            return s
    return None


# ══════════════════════════════════════════════════════
#  Image helpers
# ══════════════════════════════════════════════════════

def to_webp(src, dst):
    with Image.open(src) as img:
        if img.mode in ("RGBA", "LA", "P"):
            bg = Image.new("RGB", img.size, (255, 255, 255))
            if img.mode == "P": img = img.convert("RGBA")
            mask = img.split()[-1] if img.mode in ("RGBA","LA") else None
            bg.paste(img, mask=mask); img = bg
        elif img.mode != "RGB":
            img = img.convert("RGB")
        img.thumbnail(MAX_IMG_SIZE, Image.LANCZOS)
        img.save(dst, "WEBP", quality=WEBP_QUALITY, method=6)

def sub_folder(cat_key, sub_id):
    p = IMAGES_DIR / cat_key / sub_id
    p.mkdir(parents=True, exist_ok=True)
    return p


# ══════════════════════════════════════════════════════
#  Auth
# ══════════════════════════════════════════════════════

def login_required(f):
    @wraps(f)
    def dec(*a, **kw):
        if not session.get("admin"):
            return redirect(url_for("login"))
        return f(*a, **kw)
    return dec


# ══════════════════════════════════════════════════════
#  Публичные маршруты
# ══════════════════════════════════════════════════════

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/katalog")
@app.route("/catalog")
def catalog_page():
    catalog = load_catalog()
    return render_template("katalog.html",
        catalog=catalog,
        top_categories=TOP_CATEGORIES)

@app.route("/robots.txt")
def robots():
    return send_from_directory(BASE_DIR, "robots.txt")

@app.route("/sitemap.xml")
def sitemap():
    return send_from_directory(BASE_DIR, "sitemap.xml")


# ══════════════════════════════════════════════════════
#  Auth routes
# ══════════════════════════════════════════════════════

LOGIN_HTML = """<!DOCTYPE html><html lang="ru"><head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Вход — Дикий Енот</title>
<style>*{margin:0;padding:0;box-sizing:border-box}
body{font-family:'Segoe UI',sans-serif;background:#FAF4E8;display:flex;align-items:center;justify-content:center;min-height:100vh}
.c{background:#fff;border-radius:20px;padding:2.5rem 2rem;width:340px;box-shadow:0 8px 32px rgba(42,33,24,.12);text-align:center}
h1{font-size:1.5rem;color:#6B4C33;margin-bottom:.4rem}p{font-size:.85rem;color:#9a8b7d;margin-bottom:1.5rem}
input{width:100%;padding:.75rem 1rem;border:1.5px solid #e0d0bb;border-radius:10px;font-size:1rem;outline:none}
input:focus{border-color:#D4A373}
button{width:100%;margin-top:1rem;padding:.8rem;background:linear-gradient(135deg,#D4A373,#6B4C33);color:#fff;border:none;border-radius:10px;font-size:1rem;font-weight:700;cursor:pointer}
.err{color:#c0392b;font-size:.85rem;margin-top:.75rem}</style></head><body>
<div class="c"><h1>🦝 Дикий Енот</h1><p>Панель управления</p>
<form method="POST"><input type="password" name="password" placeholder="Пароль" autofocus>
<button>Войти</button>{% if error %}<div class="err">{{error}}</div>{% endif %}</form></div></body></html>"""

@app.route("/admin/login", methods=["GET","POST"])
def login():
    error = ""
    if request.method == "POST":
        if request.form.get("password") == ADMIN_PASSWORD:
            session["admin"] = True
            return redirect(url_for("admin"))
        error = "Неверный пароль"
    return render_template_string(LOGIN_HTML, error=error)

@app.route("/admin/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


# ══════════════════════════════════════════════════════
#  Admin panel
# ══════════════════════════════════════════════════════

@app.route("/admin")
@login_required
def admin():
    catalog = load_catalog()
    return render_template_string(ADMIN_HTML,
        catalog=catalog,
        top_categories=TOP_CATEGORIES,
        active_cat=request.args.get("cat", TOP_CATEGORIES[0]["key"]))


# ── API: subcategories ────────────────────────────────

@app.route("/admin/api/sub/add", methods=["POST"])
@login_required
def sub_add():
    d = request.get_json()
    cat_key = d.get("cat_key", "")
    title   = d.get("title", "").strip()
    desc    = d.get("desc", "").strip()
    if not cat_key or not title:
        return jsonify({"ok": False, "error": "Укажи категорию и название"}), 400
    catalog = load_catalog()
    new_id  = str(uuid.uuid4())[:8]
    catalog.setdefault(cat_key, []).append(
        {"id": new_id, "title": title, "desc": desc, "images": []})
    save_catalog(catalog)
    sub_folder(cat_key, new_id)
    return jsonify({"ok": True, "id": new_id, "title": title, "desc": desc, "images": []})

@app.route("/admin/api/sub/edit", methods=["POST"])
@login_required
def sub_edit():
    d = request.get_json()
    catalog = load_catalog()
    sub = find_sub(catalog, d.get("cat_key"), d.get("sub_id"))
    if not sub: return jsonify({"ok": False}), 404
    sub["title"] = d.get("title", sub["title"]).strip()
    sub["desc"]  = d.get("desc",  sub["desc"]).strip()
    save_catalog(catalog)
    return jsonify({"ok": True})

@app.route("/admin/api/sub/delete", methods=["POST"])
@login_required
def sub_delete():
    d = request.get_json()
    cat_key, sub_id = d.get("cat_key"), d.get("sub_id")
    catalog = load_catalog()
    catalog[cat_key] = [s for s in catalog.get(cat_key,[]) if s["id"] != sub_id]
    save_catalog(catalog)
    folder = IMAGES_DIR / cat_key / sub_id
    if folder.exists(): shutil.rmtree(folder)
    return jsonify({"ok": True})

@app.route("/admin/api/sub/reorder", methods=["POST"])
@login_required
def sub_reorder():
    d = request.get_json()
    cat_key, order = d.get("cat_key"), d.get("order", [])
    catalog = load_catalog()
    by_id = {s["id"]: s for s in catalog.get(cat_key, [])}
    catalog[cat_key] = [by_id[i] for i in order if i in by_id]
    save_catalog(catalog)
    return jsonify({"ok": True})


# ── API: photos ───────────────────────────────────────

@app.route("/admin/api/photos/list")
@login_required
def photos_list():
    sub = find_sub(load_catalog(), request.args.get("cat"), request.args.get("sub"))
    if not sub: return jsonify({"ok": False}), 404
    return jsonify({"ok": True, "images": sub["images"]})

@app.route("/admin/api/photos/upload", methods=["POST"])
@login_required
def photos_upload():
    cat_key = request.form.get("cat_key")
    sub_id  = request.form.get("sub_id")
    catalog = load_catalog()
    sub = find_sub(catalog, cat_key, sub_id)
    if not sub: return jsonify({"ok": False, "error": "Подкатегория не найдена"}), 404

    folder = sub_folder(cat_key, sub_id)
    saved, errors = [], []

    for f in request.files.getlist("files"):
        if not f or not f.filename: continue
        if Path(f.filename).suffix.lower() not in ALLOWED_EXT:
            errors.append(f"{f.filename}: неподдерживаемый формат"); continue
        stem = Path(f.filename).stem
        out  = folder / f"{stem}.webp"
        c = 1
        while out.exists(): out = folder / f"{stem}_{c}.webp"; c += 1
        tmp = folder / f"__tmp_{f.filename}"
        try:
            f.save(tmp); to_webp(tmp, out)
            rel = f"catalog/{cat_key}/{sub_id}/{out.name}"
            sub["images"].append(rel)
            saved.append(out.name)
        except Exception as e:
            errors.append(f"{f.filename}: {e}")
        finally:
            if tmp.exists(): tmp.unlink()

    save_catalog(catalog)
    return jsonify({"ok": bool(saved), "saved": saved, "errors": errors, "images": sub["images"]})

@app.route("/admin/api/photos/delete", methods=["POST"])
@login_required
def photos_delete():
    d = request.get_json()
    catalog = load_catalog()
    sub = find_sub(catalog, d.get("cat_key"), d.get("sub_id"))
    if not sub: return jsonify({"ok": False}), 404
    img_path = d.get("img_path")
    sub["images"] = [i for i in sub["images"] if i != img_path]
    save_catalog(catalog)
    full = BASE_DIR / "static" / "images" / img_path
    if full.exists(): full.unlink()
    return jsonify({"ok": True, "images": sub["images"]})

@app.route("/admin/api/photos/reorder", methods=["POST"])
@login_required
def photos_reorder():
    d = request.get_json()
    catalog = load_catalog()
    sub = find_sub(catalog, d.get("cat_key"), d.get("sub_id"))
    if not sub: return jsonify({"ok": False}), 404
    sub["images"] = d.get("order", [])
    save_catalog(catalog)
    return jsonify({"ok": True})


# ══════════════════════════════════════════════════════
#  Admin HTML template
# ══════════════════════════════════════════════════════

ADMIN_HTML = r"""<!DOCTYPE html>
<html lang="ru"><head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Каталог — Дикий Енот</title>
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
<style>
*{margin:0;padding:0;box-sizing:border-box}
:root{--honey:#D4A373;--bark:#6B4C33;--dark:#3d2a18;--cream:#FAF4E8;
      --parch:#F5EDD8;--ash:#9a8b7d;--line:#e8dcc8;
      --red:#c0392b;--green:#27ae60;--sh:0 2px 12px rgba(42,33,24,.1)}
body{font-family:'Segoe UI',sans-serif;background:var(--cream);color:#2A2118;
     min-height:100vh;display:flex;flex-direction:column}

/* Header */
.hdr{background:linear-gradient(135deg,var(--bark),var(--dark));color:#fff;
     padding:.85rem 1.5rem;display:flex;align-items:center;justify-content:space-between;
     position:sticky;top:0;z-index:200;box-shadow:0 2px 16px rgba(0,0,0,.25)}
.hdr-logo{font-size:1.15rem;font-weight:700;display:flex;align-items:center;gap:.5rem}
.hdr-badge{background:var(--honey);font-size:.6rem;font-weight:800;
           padding:2px 7px;border-radius:99px;letter-spacing:.06em;text-transform:uppercase}
.hdr-out{font-size:.82rem;color:rgba(255,255,255,.7);text-decoration:none;
         padding:.35rem .85rem;border:1px solid rgba(255,255,255,.2);
         border-radius:99px;transition:all .2s}
.hdr-out:hover{background:rgba(255,255,255,.12);color:#fff}

/* Layout */
.layout{display:flex;flex:1;min-height:0}

/* Sidebar */
.sidebar{width:210px;flex-shrink:0;background:#fff;border-right:1px solid var(--line);
         overflow-y:auto;padding:.75rem 0}
.sb-label{font-size:.62rem;font-weight:800;letter-spacing:.12em;text-transform:uppercase;
          color:var(--ash);padding:.5rem 1rem .25rem}
.sb-btn{display:flex;align-items:center;gap:.6rem;width:100%;padding:.6rem 1rem;
        font-size:.86rem;font-weight:500;color:#4a3828;background:none;
        border:none;cursor:pointer;text-align:left;transition:background .15s}
.sb-btn i{width:15px;text-align:center;color:var(--honey);font-size:.82rem;flex-shrink:0}
.sb-btn:hover{background:var(--parch)}
.sb-btn.active{background:var(--parch);color:var(--bark);font-weight:700;
               border-right:3px solid var(--honey)}
.sb-count{margin-left:auto;font-size:.7rem;background:var(--line);
          border-radius:99px;padding:1px 7px;color:var(--ash)}

/* Main */
.main{flex:1;overflow-y:auto;padding:1.5rem 1.75rem}

/* Section header */
.sec-hdr{display:flex;align-items:center;justify-content:space-between;margin-bottom:1.25rem;flex-wrap:wrap;gap:.5rem}
.sec-title{font-size:1.25rem;font-weight:700;color:var(--bark)}
.sec-hint{font-size:.76rem;color:var(--ash);margin-bottom:1.25rem;
          display:flex;align-items:center;gap:.35rem}
.sec-hint i{color:var(--honey)}

/* Buttons */
.btn{display:inline-flex;align-items:center;gap:.4rem;padding:.5rem 1rem;
     border-radius:99px;font-size:.82rem;font-weight:700;cursor:pointer;
     border:none;transition:all .18s;font-family:inherit}
.btn-primary{background:linear-gradient(135deg,var(--honey),var(--bark));color:#fff}
.btn-primary:hover{opacity:.88;transform:translateY(-1px)}
.btn-ghost{background:#fff;color:var(--bark);border:1.5px solid var(--honey)}
.btn-ghost:hover{background:var(--parch)}
.btn-danger{background:#fff;color:var(--red);border:1.5px solid #f0c0bb}
.btn-danger:hover{background:var(--red);color:#fff;border-color:var(--red)}
.btn-sm{padding:.32rem .7rem;font-size:.76rem}

/* Subcat cards grid */
.sc-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(270px,1fr));gap:1rem}

/* Subcat card */
.sc-card{background:#fff;border-radius:14px;box-shadow:var(--sh);
         border:2px solid transparent;transition:all .22s;overflow:hidden;
         display:flex;flex-direction:column}
.sc-card:hover{border-color:rgba(212,163,115,.5);box-shadow:0 6px 24px rgba(42,33,24,.13)}
.sc-card.dragging{opacity:.35;cursor:grabbing}
.sc-card.drag-over{border-color:var(--honey);transform:scale(1.02)}

/* Card thumb */
.sc-thumb{height:160px;position:relative;overflow:hidden;cursor:pointer;flex-shrink:0;
          background:var(--parch)}
.sc-thumb img{width:100%;height:100%;object-fit:cover;transition:transform .4s}
.sc-thumb:hover img{transform:scale(1.06)}
.sc-thumb-empty{display:flex;align-items:center;justify-content:center;
                height:100%;flex-direction:column;gap:.4rem;color:#c9b898;font-size:.8rem}
.sc-thumb-empty i{font-size:2.2rem}
.sc-badge{position:absolute;top:.5rem;right:.5rem;
          background:rgba(42,33,24,.65);color:#fff;
          font-size:.68rem;font-weight:700;padding:2px 8px;border-radius:99px;
          backdrop-filter:blur(4px)}
.sc-drag-handle{position:absolute;top:.5rem;left:.5rem;width:26px;height:26px;
                border-radius:6px;background:rgba(42,33,24,.55);color:#fff;
                font-size:.75rem;display:flex;align-items:center;justify-content:center;
                cursor:grab;opacity:0;transition:opacity .2s}
.sc-card:hover .sc-drag-handle{opacity:1}

/* Card body */
.sc-body{padding:.85rem 1rem 1rem;flex:1;display:flex;flex-direction:column;gap:.4rem}
.sc-title{font-size:.98rem;font-weight:700;color:var(--bark);line-height:1.3}
.sc-desc{font-size:.79rem;color:var(--ash);line-height:1.55;flex:1;
         display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden}
.sc-desc-empty{font-style:italic;color:#cbbfa8}
.sc-actions{display:flex;gap:.4rem;flex-wrap:wrap;padding-top:.4rem}

/* Empty state */
.empty-state{text-align:center;padding:4rem 1rem;color:var(--ash)}
.empty-state i{font-size:3.5rem;color:#d4c4a8;margin-bottom:.75rem;display:block}
.empty-state h3{font-size:1.1rem;margin-bottom:.4rem;color:#7a6e65}
.empty-state p{font-size:.85rem;margin-bottom:1.25rem}

/* ── Photo panel (slide-in from right) ── */
.pp-overlay{display:none;position:fixed;inset:0;background:rgba(42,33,24,.45);
            z-index:250;backdrop-filter:blur(3px)}
.pp-overlay.open{display:block}
.pp-panel{position:fixed;top:0;right:-100%;width:min(560px,100%);height:100%;
          background:#fff;z-index:300;box-shadow:-4px 0 40px rgba(42,33,24,.18);
          display:flex;flex-direction:column;transition:right .3s cubic-bezier(.4,0,.2,1)}
.pp-panel.open{right:0}

.pp-hdr{padding:1rem 1.25rem;border-bottom:1px solid var(--line);
        display:flex;align-items:flex-start;justify-content:space-between;flex-shrink:0;
        background:var(--parch)}
.pp-hdr-info h3{font-size:1rem;font-weight:700;color:var(--bark)}
.pp-hdr-info p{font-size:.75rem;color:var(--ash);margin-top:.15rem}
.pp-x{width:30px;height:30px;border-radius:50%;background:var(--line);border:none;
      cursor:pointer;font-size:.95rem;color:var(--ash);
      display:flex;align-items:center;justify-content:center;transition:all .2s;flex-shrink:0}
.pp-x:hover{background:#ddd;color:var(--bark)}

.pp-body{flex:1;overflow-y:auto;padding:1.25rem}

.upload-zone{border:2px dashed #d0bc9e;border-radius:12px;padding:1.75rem;
             text-align:center;background:var(--parch);cursor:pointer;
             transition:all .2s;margin-bottom:1rem}
.upload-zone:hover,.upload-zone.dragover{border-color:var(--honey);background:#fffbf4}
.upload-zone i{font-size:2rem;color:var(--honey);margin-bottom:.5rem;display:block}
.upload-zone p{color:var(--ash);font-size:.85rem;margin-bottom:.2rem}
.upload-zone small{color:#c0b09a;font-size:.74rem}
.upload-zone input{display:none}

.prog-wrap{display:none;margin:.5rem 0}
.prog-bg{background:var(--line);border-radius:3px;overflow:hidden}
.prog-bar{height:4px;background:var(--honey);width:0;transition:width .3s}
.prog-status{font-size:.75rem;color:var(--ash);margin-top:.3rem}

.ph-hint{font-size:.74rem;color:var(--ash);margin-bottom:.7rem;
         display:flex;align-items:center;gap:.3rem}
.ph-hint i{color:var(--honey)}

.ph-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(120px,1fr));gap:.55rem}
.ph-card{border-radius:8px;overflow:hidden;background:var(--parch);position:relative;
         border:2px solid transparent;cursor:grab;transition:all .18s}
.ph-card:active{cursor:grabbing}
.ph-card.dragging{opacity:.35}
.ph-card.drag-over{border-color:var(--honey);transform:scale(1.05)}
.ph-card img{width:100%;height:95px;object-fit:cover;display:block}
.ph-del{position:absolute;top:.3rem;right:.3rem;width:22px;height:22px;border-radius:50%;
        background:rgba(192,57,43,.9);color:#fff;border:none;font-size:.6rem;
        cursor:pointer;display:flex;align-items:center;justify-content:center;
        opacity:0;transition:opacity .18s}
.ph-card:hover .ph-del{opacity:1}
.ph-num{position:absolute;top:.3rem;left:.3rem;width:19px;height:19px;border-radius:50%;
        background:rgba(42,33,24,.6);color:#fff;font-size:.58rem;font-weight:700;
        display:flex;align-items:center;justify-content:center}
.ph-empty{padding:1.5rem;text-align:center;color:var(--ash);
          font-style:italic;font-size:.82rem;grid-column:1/-1}

/* ── Modal ── */
.modal-bg{display:none;position:fixed;inset:0;z-index:400;
          align-items:center;justify-content:center;padding:1rem;
          background:rgba(42,33,24,.55);backdrop-filter:blur(5px)}
.modal-bg.open{display:flex}
.modal{background:#fff;border-radius:18px;padding:1.75rem;width:100%;max-width:420px;
       box-shadow:0 24px 60px rgba(0,0,0,.2);animation:mIn .2s ease}
@keyframes mIn{from{opacity:0;transform:translateY(14px)}to{opacity:1;transform:translateY(0)}}
.modal h3{font-size:1.1rem;color:var(--bark);margin-bottom:1.1rem;
          display:flex;align-items:center;gap:.5rem}
.fg{margin-bottom:.85rem}
.fg label{display:block;font-size:.72rem;font-weight:800;color:var(--ash);
          text-transform:uppercase;letter-spacing:.07em;margin-bottom:.3rem}
.fg input,.fg textarea{width:100%;padding:.6rem .85rem;border:1.5px solid var(--line);
  border-radius:8px;font-size:.9rem;font-family:inherit;outline:none;
  transition:border .2s;resize:vertical;background:#fff}
.fg input:focus,.fg textarea:focus{border-color:var(--honey)}
.fg textarea{min-height:80px}
.m-actions{display:flex;gap:.6rem;justify-content:flex-end;margin-top:1.1rem}

/* Toast */
#toast{position:fixed;bottom:1.5rem;right:1.5rem;padding:.65rem 1.1rem;
       border-radius:10px;font-size:.84rem;font-weight:600;color:#fff;
       z-index:9999;opacity:0;transform:translateY(8px);
       transition:all .25s;pointer-events:none}
#toast.show{opacity:1;transform:translateY(0)}
#toast.ok{background:var(--green)}#toast.err{background:var(--red)}

@media(max-width:640px){
  .sidebar{width:52px}.sb-btn span,.sb-label,.sb-count{display:none}
  .sb-btn{justify-content:center;padding:.7rem}
  .main{padding:1rem}
  .ph-grid{grid-template-columns:repeat(auto-fill,minmax(100px,1fr))}
}
</style></head>
<body>

<div class="hdr">
  <div class="hdr-logo"><i class="fas fa-paw"></i> <span>Дикий Енот</span>
    <span class="hdr-badge">Админ</span></div>
  <a href="/admin/logout" class="hdr-out"><i class="fas fa-sign-out-alt"></i> <span>Выйти</span></a>
</div>

<div class="layout">

<!-- Sidebar -->
<nav class="sidebar">
  <div class="sb-label">Категории</div>
  {% for cat in top_categories %}
  {% set count = catalog.get(cat.key, [])|length %}
  <button class="sb-btn {% if cat.key == active_cat %}active{% endif %}"
          onclick="switchCat('{{ cat.key }}')">
    <i class="{{ cat.icon }}"></i>
    <span>{{ cat.title }}</span>
    {% if count %}<span class="sb-count">{{ count }}</span>{% endif %}
  </button>
  {% endfor %}
</nav>

<!-- Main panels -->
<div class="main">
  {% for cat in top_categories %}
  <div class="cat-panel" id="cp-{{ cat.key }}"
       style="display:{% if cat.key == active_cat %}block{% else %}none{% endif %}">

    <div class="sec-hdr">
      <div class="sec-title">{{ cat.title }}</div>
      <button class="btn btn-primary" onclick="openAddModal('{{ cat.key }}')">
        <i class="fas fa-plus"></i> Новая подкатегория
      </button>
    </div>
    <div class="sec-hint">
      <i class="fas fa-grip-vertical"></i>
      Перетащи карточки чтобы изменить порядок · нажми на фото чтобы управлять изображениями
    </div>

    {% set subs = catalog.get(cat.key, []) %}
    {% if subs %}
    <div class="sc-grid" id="scg-{{ cat.key }}"
         ondragover="scDragOver(event)" ondrop="scDrop(event,'{{ cat.key }}')">
      {% for sub in subs %}
      <div class="sc-card" id="scc-{{ sub.id }}" draggable="true"
           data-id="{{ sub.id }}"
           ondragstart="scDragStart(event)">

        <div class="sc-thumb"
             onclick="openPhotoPanel('{{ cat.key }}','{{ sub.id }}','{{ sub.title|e }}')">
          <div class="sc-drag-handle"><i class="fas fa-grip-vertical"></i></div>
          {% if sub.images %}
            <img src="/static/images/{{ sub.images[0] }}" alt="{{ sub.title }}">
            <span class="sc-badge">{{ sub.images|length }} фото</span>
          {% else %}
            <div class="sc-thumb-empty">
              <i class="fas fa-camera"></i><span>Нажми чтобы добавить фото</span>
            </div>
          {% endif %}
        </div>

        <div class="sc-body">
          <div class="sc-title">{{ sub.title }}</div>
          {% if sub.desc %}
          <div class="sc-desc">{{ sub.desc }}</div>
          {% else %}
          <div class="sc-desc sc-desc-empty">Нет описания</div>
          {% endif %}
          <div class="sc-actions">
            <button class="btn btn-ghost btn-sm"
                    onclick="openPhotoPanel('{{ cat.key }}','{{ sub.id }}','{{ sub.title|e }}')">
              <i class="fas fa-images"></i> Фото
            </button>
            <button class="btn btn-ghost btn-sm"
                    onclick="openEditModal('{{ cat.key }}','{{ sub.id }}','{{ sub.title|e }}','{{ sub.desc|e }}')">
              <i class="fas fa-pen"></i> Изменить
            </button>
            <button class="btn btn-danger btn-sm"
                    onclick="deleteSub('{{ cat.key }}','{{ sub.id }}','{{ sub.title|e }}')">
              <i class="fas fa-trash"></i>
            </button>
          </div>
        </div>
      </div>
      {% endfor %}
    </div>

    {% else %}
    <div class="empty-state">
      <i class="fas fa-folder-open"></i>
      <h3>Подкатегорий пока нет</h3>
      <p>Добавь первую — например «Беседка 3×4 м» — и загрузи фотографии</p>
      <button class="btn btn-primary" onclick="openAddModal('{{ cat.key }}')">
        <i class="fas fa-plus"></i> Добавить первую
      </button>
    </div>
    {% endif %}

  </div>
  {% endfor %}
</div><!-- /main -->
</div><!-- /layout -->

<!-- Photo panel -->
<div class="pp-overlay" id="ppOverlay" onclick="closePP()"></div>
<div class="pp-panel" id="ppPanel">
  <div class="pp-hdr">
    <div class="pp-hdr-info">
      <h3 id="ppTitle">Фотографии</h3>
      <p id="ppSub">Загружай, удаляй, меняй порядок</p>
    </div>
    <button class="pp-x" onclick="closePP()"><i class="fas fa-times"></i></button>
  </div>
  <div class="pp-body">
    <div class="upload-zone" id="ppZone"
         onclick="document.getElementById('ppFile').click()"
         ondragover="uzOver(event)" ondragleave="uzLeave()" ondrop="uzDrop(event)">
      <i class="fas fa-cloud-upload-alt"></i>
      <p>Нажми или перетащи фото сюда</p>
      <small>JPG · PNG · WebP · HEIC (с iPhone) · до 50 МБ · можно несколько сразу</small>
      <input type="file" id="ppFile" multiple accept=".jpg,.jpeg,.png,.webp,.heic,.heif"
             onchange="ppUpload(this.files)">
    </div>
    <div class="prog-wrap" id="ppProg">
      <div class="prog-bg"><div class="prog-bar" id="ppBar"></div></div>
      <div class="prog-status" id="ppStatus"></div>
    </div>
    <div class="ph-hint">
      <i class="fas fa-grip-vertical"></i>
      Перетащи фото чтобы изменить порядок · наведи на фото чтобы удалить
    </div>
    <div class="ph-grid" id="ppGrid"
         ondragover="phDragOver(event)" ondrop="phDrop(event)"></div>
  </div>
</div>

<!-- Add/Edit modal -->
<div class="modal-bg" id="modal">
  <div class="modal">
    <h3><i class="fas fa-layer-group" style="color:var(--honey)"></i>
      <span id="modalTitle">Новая подкатегория</span></h3>
    <div class="fg">
      <label>Название *</label>
      <input id="mName" placeholder="Например: Беседка 3×4 м или Баня 4×6 м">
    </div>
    <div class="fg">
      <label>Описание</label>
      <textarea id="mDesc" placeholder="Характеристики, особенности, материалы..."></textarea>
    </div>
    <div class="m-actions">
      <button class="btn btn-ghost" onclick="closeModal()">Отмена</button>
      <button class="btn btn-primary" id="mSave" onclick="saveModal()">
        <i class="fas fa-check"></i> Сохранить
      </button>
    </div>
  </div>
</div>

<div id="toast"></div>

<script>
let _cat = '{{ active_cat }}';
let _ppCat = null, _ppSub = null;
let _mMode = 'add', _mCat = null, _mSubId = null;
let _scDrag = null, _phDrag = null;

/* ── Sidebar switch ── */
function switchCat(key) {
  document.querySelectorAll('.sb-btn').forEach(b => b.classList.remove('active'));
  document.querySelector(`.sb-btn[onclick="switchCat('${key}')"]`).classList.add('active');
  document.querySelectorAll('.cat-panel').forEach(p => p.style.display = 'none');
  document.getElementById(`cp-${key}`).style.display = 'block';
  _cat = key;
}

/* ── Toast ── */
function toast(msg, ok=true) {
  const t = document.getElementById('toast');
  t.textContent = msg; t.className = 'show ' + (ok?'ok':'err');
  clearTimeout(t._t); t._t = setTimeout(() => t.className = '', 3000);
}

/* ── Modal ── */
function openAddModal(catKey) {
  _mMode='add'; _mCat=catKey; _mSubId=null;
  document.getElementById('modalTitle').textContent = 'Новая подкатегория';
  document.getElementById('mName').value = '';
  document.getElementById('mDesc').value = '';
  document.getElementById('modal').classList.add('open');
  setTimeout(() => document.getElementById('mName').focus(), 80);
}
function openEditModal(catKey, subId, title, desc) {
  _mMode='edit'; _mCat=catKey; _mSubId=subId;
  document.getElementById('modalTitle').textContent = 'Редактировать';
  document.getElementById('mName').value = title;
  document.getElementById('mDesc').value = desc;
  document.getElementById('modal').classList.add('open');
  setTimeout(() => document.getElementById('mName').focus(), 80);
}
function closeModal() { document.getElementById('modal').classList.remove('open'); }

async function saveModal() {
  const title = document.getElementById('mName').value.trim();
  const desc  = document.getElementById('mDesc').value.trim();
  if (!title) { document.getElementById('mName').focus(); return; }
  const btn = document.getElementById('mSave');
  btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i>';
  const url  = _mMode === 'add' ? '/admin/api/sub/add' : '/admin/api/sub/edit';
  const body = _mMode === 'add'
    ? {cat_key:_mCat, title, desc}
    : {cat_key:_mCat, sub_id:_mSubId, title, desc};
  const res  = await fetch(url,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)});
  const data = await res.json();
  btn.innerHTML = '<i class="fas fa-check"></i> Сохранить';
  if (data.ok) { closeModal(); toast(_mMode==='add'?'Подкатегория создана':'Сохранено'); location.reload(); }
  else toast(data.error||'Ошибка',false);
}

/* ── Delete subcat ── */
async function deleteSub(catKey, subId, title) {
  if (!confirm(`Удалить «${title}» и все её фотографии?`)) return;
  const res = await fetch('/admin/api/sub/delete',{method:'POST',
    headers:{'Content-Type':'application/json'},body:JSON.stringify({cat_key:catKey,sub_id:subId})});
  const d = await res.json();
  if (d.ok) { toast('Удалено'); location.reload(); }
  else toast('Ошибка', false);
}

/* ── Subcat drag-reorder ── */
function scDragStart(e) {
  _scDrag = e.currentTarget; _scDrag.classList.add('dragging');
  e.dataTransfer.effectAllowed = 'move';
}
function scDragOver(e) {
  e.preventDefault();
  const over = e.target.closest('.sc-card');
  if (!over || over === _scDrag) return;
  const grid = over.parentElement;
  const cards = [...grid.querySelectorAll('.sc-card')];
  if (cards.indexOf(_scDrag) < cards.indexOf(over)) over.after(_scDrag);
  else over.before(_scDrag);
}
async function scDrop(e, catKey) {
  e.preventDefault();
  if (_scDrag) _scDrag.classList.remove('dragging');
  const order = [...document.getElementById(`scg-${catKey}`).querySelectorAll('.sc-card')]
    .map(c => c.dataset.id);
  await fetch('/admin/api/sub/reorder',{method:'POST',
    headers:{'Content-Type':'application/json'},body:JSON.stringify({cat_key:catKey,order})});
  toast('Порядок сохранён'); _scDrag = null;
}

/* ── Photo panel ── */
function openPP(catKey, subId, title) {
  _ppCat=catKey; _ppSub=subId;
  document.getElementById('ppTitle').textContent = title;
  document.getElementById('ppSub').textContent = 'Загружай, удаляй, меняй порядок';
  document.getElementById('ppPanel').classList.add('open');
  document.getElementById('ppOverlay').classList.add('open');
  loadPh();
}
function closePP() {
  document.getElementById('ppPanel').classList.remove('open');
  document.getElementById('ppOverlay').classList.remove('open');
}
// alias used from HTML onclick
function openPhotoPanel(c,s,t){ openPP(c,s,t); }

async function loadPh() {
  const r = await fetch(`/admin/api/photos/list?cat=${_ppCat}&sub=${_ppSub}`);
  const d = await r.json();
  renderPh(d.images);
}

function renderPh(images) {
  const grid = document.getElementById('ppGrid');
  grid.innerHTML = '';
  if (!images.length) {
    grid.innerHTML = '<div class="ph-empty">Фото пока нет — загрузи выше!</div>'; return;
  }
  images.forEach((src, i) => {
    const c = document.createElement('div');
    c.className='ph-card'; c.draggable=true; c.dataset.src=src;
    c.ondragstart = phDragStart;
    c.innerHTML = `<span class="ph-num">${i+1}</span>
      <img src="/static/images/${src}?t=${Date.now()}" loading="lazy">
      <button class="ph-del" onclick="delPh('${src}')"><i class="fas fa-trash"></i></button>`;
    grid.appendChild(c);
  });
}

/* ── Upload ── */
function uzOver(e){ e.preventDefault(); document.getElementById('ppZone').classList.add('dragover'); }
function uzLeave(){ document.getElementById('ppZone').classList.remove('dragover'); }
function uzDrop(e){ e.preventDefault(); uzLeave(); ppUpload(e.dataTransfer.files); }

async function ppUpload(files) {
  if (!files||!files.length) return;
  const bar=document.getElementById('ppBar'),
        prog=document.getElementById('ppProg'),
        stat=document.getElementById('ppStatus');
  prog.style.display='block'; bar.style.width='15%';
  stat.textContent=`Загружаем ${files.length} файл(ов)...`;
  const fd=new FormData();
  fd.append('cat_key',_ppCat); fd.append('sub_id',_ppSub);
  [...files].forEach(f=>fd.append('files',f));
  try {
    bar.style.width='55%';
    const res=await fetch('/admin/api/photos/upload',{method:'POST',body:fd});
    bar.style.width='100%';
    const d=await res.json();
    if(d.ok){
      stat.textContent=`✅ Загружено: ${d.saved.join(', ')}`+(d.errors.length?` ⚠️ ${d.errors.join(', ')}`:'');
      toast(`Загружено ${d.saved.length} фото`);
      renderPh(d.images);
      updateThumb(_ppCat,_ppSub,d.images);
    } else {
      stat.textContent='❌ '+(d.errors.join('; ')||d.error);
      toast('Ошибка загрузки',false);
    }
  } catch{ stat.textContent='❌ Ошибка сети'; toast('Ошибка сети',false); }
  setTimeout(()=>{prog.style.display='none';bar.style.width='0';},4000);
}

async function delPh(imgPath) {
  if(!confirm('Удалить фото?')) return;
  const res=await fetch('/admin/api/photos/delete',{method:'POST',
    headers:{'Content-Type':'application/json'},
    body:JSON.stringify({cat_key:_ppCat,sub_id:_ppSub,img_path:imgPath})});
  const d=await res.json();
  if(d.ok){ toast('Фото удалено'); renderPh(d.images); updateThumb(_ppCat,_ppSub,d.images); }
  else toast('Ошибка',false);
}

/* ── Photo drag-reorder ── */
function phDragStart(e){ _phDrag=e.currentTarget; _phDrag.classList.add('dragging'); e.dataTransfer.effectAllowed='move'; }
function phDragOver(e){
  e.preventDefault();
  const over=e.target.closest('.ph-card');
  document.querySelectorAll('.ph-card').forEach(c=>c.classList.remove('drag-over'));
  if(over&&over!==_phDrag) over.classList.add('drag-over');
}
async function phDrop(e){
  e.preventDefault();
  const grid=document.getElementById('ppGrid');
  grid.querySelectorAll('.ph-card').forEach(c=>c.classList.remove('drag-over','dragging'));
  const over=e.target.closest('.ph-card');
  if(!over||over===_phDrag||!_phDrag) return;
  const cards=[...grid.querySelectorAll('.ph-card')];
  if(cards.indexOf(_phDrag)<cards.indexOf(over)) over.after(_phDrag);
  else over.before(_phDrag);
  grid.querySelectorAll('.ph-card').forEach((c,i)=>c.querySelector('.ph-num').textContent=i+1);
  const order=[...grid.querySelectorAll('.ph-card')].map(c=>c.dataset.src);
  await fetch('/admin/api/photos/reorder',{method:'POST',
    headers:{'Content-Type':'application/json'},
    body:JSON.stringify({cat_key:_ppCat,sub_id:_ppSub,order})});
  toast('Порядок сохранён'); _phDrag=null;
}

/* ── Update thumb on card after upload/delete ── */
function updateThumb(catKey, subId, images) {
  const card=document.getElementById(`scc-${subId}`);
  if(!card) return;
  const thumb=card.querySelector('.sc-thumb');
  const handle=`<div class="sc-drag-handle"><i class="fas fa-grip-vertical"></i></div>`;
  if(images.length){
    thumb.innerHTML=handle+`<img src="/static/images/${images[0]}?t=${Date.now()}" alt="">
      <span class="sc-badge">${images.length} фото</span>`;
    thumb.onclick=()=>openPP(catKey,subId,card.querySelector('.sc-title').textContent.trim());
  } else {
    thumb.innerHTML=handle+`<div class="sc-thumb-empty">
      <i class="fas fa-camera"></i><span>Нажми чтобы добавить фото</span></div>`;
    thumb.onclick=()=>openPP(catKey,subId,card.querySelector('.sc-title').textContent.trim());
  }
}

/* ── Keyboard ── */
document.addEventListener('keydown', e => {
  if(e.key==='Escape'){ closeModal(); closePP(); }
  if(e.key==='Enter' && document.getElementById('modal').classList.contains('open')
     && e.target.tagName!=='TEXTAREA') saveModal();
});
</script>
</body></html>"""


# ══════════════════════════════════════════════════════
#  Диагностика — зайди на /debug чтобы проверить пути
# ══════════════════════════════════════════════════════

@app.route("/debug")
def debug():
    catalog = load_catalog()
    tmpl_dir   = BASE_DIR / "templates"
    katalog_in_templates = (tmpl_dir / "katalog.html").exists()
    katalog_in_static    = (BASE_DIR / "static" / "templates" / "katalog.html").exists()
    total_items = sum(len(v) for v in catalog.values())

    lines = [
        f"<h2>🦝 Диагностика</h2>",
        f"<p><b>BASE_DIR:</b> {BASE_DIR}</p>",
        f"<p><b>catalog.json существует:</b> {CATALOG_FILE.exists()}</p>",
        f"<p><b>catalog.json путь:</b> {CATALOG_FILE}</p>",
        f"<p><b>Записей в каталоге:</b> {total_items}</p>",
        f"<p><b>katalog.html в templates/:</b> {'✅ ДА' if katalog_in_templates else '❌ НЕТ — нужно переместить!'}</p>",
        f"<p><b>katalog.html в static/templates/:</b> {'⚠️ ДА (старое место)' if katalog_in_static else 'нет'}</p>",
        f"<hr><h3>Содержимое catalog.json:</h3>",
        f"<pre style='background:#f5f5f5;padding:1rem;border-radius:8px'>{json.dumps(catalog, ensure_ascii=False, indent=2)}</pre>",
    ]
    return "<meta charset='UTF-8'>" + "".join(lines)


# ══════════════════════════════════════════════════════
if __name__ == "__main__":
    IMAGES_DIR.mkdir(parents=True, exist_ok=True)
    load_catalog()  # создаст catalog.json если нет
    print("\n🦝 Сервер запущен!")
    print("   Сайт:    http://localhost:5000")
    print("   Админка: http://localhost:5000/admin")
    print(f"   Пароль:  {ADMIN_PASSWORD}\n")
    app.run(debug=True, host="0.0.0.0", port=5000)