#!/usr/bin/env python3
"""
optimize_images.py — Оптимизация изображений для сайта "Дикий Енот"
Конвертирует JPG/PNG → WebP, сжимает, ресайзит если нужно.
Оригиналы НЕ удаляются — сохраняются рядом с .webp файлом.
"""

import os
import sys
from pathlib import Path

try:
    from PIL import Image
except ImportError:
    print("❌ Pillow не установлен. Запусти:\n   pip install Pillow --break-system-packages")
    sys.exit(1)

# ══════════════════════════════════════════════════════
#  НАСТРОЙКИ — измени если нужно
# ══════════════════════════════════════════════════════

# Папка с изображениями (относительно скрипта или абсолютный путь)
IMAGES_DIR = "./static/images"

# Максимальная ширина/высота — если фото больше, уменьшится пропорционально
# Для каталога 1600px более чем достаточно
MAX_SIZE = (1600, 1600)

# Качество WebP: 82 — хороший баланс качество/размер (0–100)
QUALITY = 82

# Расширения для обработки
EXTENSIONS = {".jpg", ".jpeg", ".png", ".JPG", ".JPEG", ".PNG"}

# Пропустить если WebP уже существует (True = не перезаписывать)
SKIP_EXISTING = False

# ══════════════════════════════════════════════════════


def format_size(bytes_count):
    if bytes_count < 1024:
        return f"{bytes_count} Б"
    elif bytes_count < 1024 * 1024:
        return f"{bytes_count/1024:.1f} КБ"
    else:
        return f"{bytes_count/1024/1024:.1f} МБ"


def optimize(input_path: Path) -> tuple[int, int] | None:
    """Возвращает (исходный_размер, новый_размер) или None если пропущено."""
    output_path = input_path.with_suffix(".webp")

    if SKIP_EXISTING and output_path.exists():
        return None

    original_size = input_path.stat().st_size

    try:
        with Image.open(input_path) as img:
            # Конвертируем RGBA → RGB если PNG с прозрачностью
            if img.mode in ("RGBA", "LA", "P"):
                background = Image.new("RGB", img.size, (255, 255, 255))
                if img.mode == "P":
                    img = img.convert("RGBA")
                background.paste(img, mask=img.split()[-1] if img.mode == "RGBA" else None)
                img = background
            elif img.mode != "RGB":
                img = img.convert("RGB")

            # Уменьшаем если больше MAX_SIZE
            img.thumbnail(MAX_SIZE, Image.LANCZOS)

            # Сохраняем в WebP
            img.save(output_path, "WEBP", quality=QUALITY, method=6)

    except Exception as e:
        print(f"   ⚠️  Ошибка: {input_path.name} — {e}")
        return None

    new_size = output_path.stat().st_size
    return original_size, new_size


def main():
    images_dir = Path(IMAGES_DIR)

    if not images_dir.exists():
        print(f"❌ Папка не найдена: {images_dir.resolve()}")
        print("   Запусти скрипт из корня проекта или укажи правильный путь в IMAGES_DIR")
        sys.exit(1)

    # Собираем все подходящие файлы рекурсивно
    files = [
        f for f in images_dir.rglob("*")
        if f.suffix in EXTENSIONS and f.is_file()
        and ".webp" not in f.name  # на всякий случай
    ]

    if not files:
        print(f"⚠️  Не найдено JPG/PNG файлов в {images_dir.resolve()}")
        sys.exit(0)

    print(f"\n🖼️  Найдено файлов: {len(files)}")
    print(f"📁 Папка: {images_dir.resolve()}")
    print(f"⚙️  Качество WebP: {QUALITY}, макс. размер: {MAX_SIZE[0]}px\n")
    print("─" * 60)

    total_original = 0
    total_new = 0
    converted = 0
    skipped = 0
    errors = 0

    for i, f in enumerate(sorted(files), 1):
        rel = f.relative_to(images_dir)
        print(f"[{i:>3}/{len(files)}] {rel}", end="  ")

        result = optimize(f)
        if result is None:
            print("⏭  пропущено")
            skipped += 1
            continue

        orig, new = result
        saved = orig - new
        pct = (saved / orig * 100) if orig > 0 else 0
        total_original += orig
        total_new += new
        converted += 1

        arrow = "✅" if pct > 5 else "➡️"
        print(f"{arrow}  {format_size(orig)} → {format_size(new)}  (−{pct:.0f}%)")

    print("─" * 60)
    total_saved = total_original - total_new
    total_pct = (total_saved / total_original * 100) if total_original > 0 else 0

    print(f"\n✅ Готово!")
    print(f"   Конвертировано : {converted} файлов")
    if skipped:
        print(f"   Пропущено      : {skipped} файлов")
    print(f"   Было           : {format_size(total_original)}")
    print(f"   Стало          : {format_size(total_new)}")
    print(f"   Сэкономлено    : {format_size(total_saved)} (−{total_pct:.0f}%)")
    print()
    print("💡 Оригиналы (JPG/PNG) остались нетронутыми.")
    print("   После проверки что всё выглядит нормально —")
    print("   можешь удалить их командой:")
    print(f"   find {IMAGES_DIR} -name '*.jpg' -o -name '*.jpeg' -o -name '*.png' | xargs rm")
    print()
    print("⚠️  Не забудь обновить пути в HTML/JS с .jpg/.png → .webp")


if __name__ == "__main__":
    main()