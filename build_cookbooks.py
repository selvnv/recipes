#!/usr/bin/env python3
"""Собирает сборники рецептов cookbook-modern.html и cookbook-chef.html"""

import re
import os
from pathlib import Path

ROOT = Path(__file__).parent
EXCLUDE_DIRS = {"old", ".git", "__pycache__"}

MODERN_STYLE_FILE = ROOT / "recipe-modern.html"
CHEF_STYLE_FILE = ROOT / "recipe-chef.html"

OUTPUT_MODERN = ROOT / "cookbook-modern.html"
OUTPUT_CHEF = ROOT / "cookbook-chef.html"

# Каталоги рецептов (все папки с .html, кроме old)
def get_recipe_dirs():
    dirs = []
    for item in sorted(ROOT.iterdir()):
        if item.is_dir() and item.name not in EXCLUDE_DIRS:
            # Проверим, есть ли внутри modern.html и chef.html
            if (item / "modern.html").exists() or (item / "chef.html").exists():
                dirs.append(item)
    return dirs


def extract_css(html_text):
    """Извлекает содержимое тега <style>...</style>"""
    m = re.search(r"<style>(.*?)</style>", html_text, re.DOTALL)
    if m:
        return m.group(1).strip()
    return ""


def extract_body_content(html_text):
    """Извлекает всё внутри <body>...</body> БЕЗ самих тегов body"""
    m = re.search(r"<body>(.*?)</body>", html_text, re.DOTALL)
    if m:
        return m.group(1).strip()
    return ""


def get_base_css(template_path):
    """Получает базовый CSS из шаблона"""
    text = template_path.read_text(encoding="utf-8")
    return extract_css(text)


def parse_recipe_html(filepath):
    """Извлекает содержимое контейнера и title из файла рецепта"""
    text = filepath.read_text(encoding="utf-8")
    title_match = re.search(r"<title>(.*?)</title>", text, re.DOTALL)
    title = title_match.group(1).strip() if title_match else filepath.parent.name

    content = extract_body_content(text)
    return title, content


def fix_image_paths(html_text, dirname):
    """Заменяет относительные пути к картинкам на пути с префиксом каталога рецепта."""
    # Замена src="filename.ext" → src="dirname/filename.ext"
    # Не трогаем http/https/data: ссылки
    def replace_src(match):
        attr_name = match.group(1)  # src или srcset
        quote = match.group(2)      # кавычка " или '
        path = match.group(3)
        # Пропускаем абсолютные URL, data: URI и уже содержащие /
        if path.startswith(("http://", "https://", "data:", "/")) or "/" in path:
            return match.group(0)
        return f'{attr_name}={quote}{dirname}/{path}{quote}'

    html_text = re.sub(
        r'(src|srcset)=(["\'])(.*?)\2',
        replace_src,
        html_text
    )
    return html_text


def build_cookbook(style, output_path, recipe_dirs):
    """Создаёт сборник"""
    if style == "modern":
        template_path = MODERN_STYLE_FILE
        file_suffix = "modern.html"
        title = "Сборник рецептов"
        body_class = ""
    else:
        template_path = CHEF_STYLE_FILE
        file_suffix = "chef.html"
        title = "Сборник рецептов"
        body_class = ""

    if not template_path.exists():
        print(f"Шаблон {template_path} не найден, пропускаю стиль {style}")
        return

    base_css = get_base_css(template_path)

    # Собираем все рецепты
    recipes = []
    for d in recipe_dirs:
        recipe_file = d / file_suffix
        if recipe_file.exists():
            recipe_title, recipe_body = parse_recipe_html(recipe_file)
            recipes.append((d.name, recipe_title, recipe_body))
            print(f"  + {d.name}")

    if not recipes:
        print(f"Нет рецептов для стиля {style}")
        return

    # Формируем оглавление
    toc_items = []
    for idx, (dirname, rtitle, _) in enumerate(recipes):
        # Извлекаем чистое название рецепта (без " — Рецепт")
        clean_title = rtitle.replace(" — Рецепт", "").strip()
        toc_items.append(f'<li><a href="#recipe-{idx}">{clean_title}</a></li>')

    toc_html = '<ol class="toc-list">\n' + "\n".join(toc_items) + "\n</ol>"

    # Формируем все рецепты
    recipe_sections = []
    for idx, (dirname, rtitle, rbody) in enumerate(recipes):
        clean_title = rtitle.replace(" — Рецепт", "").strip()
        # Исправляем пути к картинкам
        fixed_body = fix_image_paths(rbody, dirname)
        # Оборачиваем каждый рецепт в секцию с якорем
        recipe_sections.append(f"""
        <!-- ====== {clean_title} ====== -->
        <section id="recipe-{idx}" class="recipe-section">
            {fixed_body}
        </section>
        <div class="section-divider"></div>
        """)

    recipes_html = "\n".join(recipe_sections)

    # Дополнительные стили для сборника
    if style == "chef":
        extra_css = """
        /* ===== СТИЛИ СБОРНИКА (Chef) ===== */
        .cookbook-header {
            text-align: center;
            padding: 60px 48px 40px;
            background: linear-gradient(135deg, #1a1a1a 0%, #252525 100%);
            border-bottom: 1px solid var(--accent);
        }
        .cookbook-header h1 {
            font-family: var(--font-heading);
            font-size: 42px;
            font-weight: normal;
            color: var(--accent-light);
            margin-bottom: 8px;
            letter-spacing: 1px;
            position: relative;
        }
        .cookbook-header h1::after {
            content: '';
            display: block;
            width: 80px;
            height: 1px;
            background: var(--accent);
            margin: 16px auto 0;
        }
        .cookbook-header p {
            color: var(--text-light);
            font-size: 15px;
            font-style: italic;
            margin-top: 4px;
        }

        /* Оглавление */
        .toc {
            padding: 32px 48px;
            border-bottom: 1px solid var(--border);
        }
        .toc h2 {
            font-family: var(--font-heading);
            font-size: 18px;
            font-weight: normal;
            color: var(--accent);
            margin-bottom: 20px;
            text-transform: uppercase;
            letter-spacing: 2px;
        }
        .toc-list {
            list-style: none;
            padding: 0;
            columns: 2;
            column-gap: 24px;
        }
        @media (max-width: 600px) {
            .toc-list {
                columns: 1;
            }
        }
        .toc-list li {
            margin-bottom: 8px;
            break-inside: avoid;
        }
        .toc-list li a {
            color: var(--accent-light);
            text-decoration: none;
            font-size: 15px;
            padding: 4px 0;
            display: inline-block;
            transition: color 0.2s;
        }
        .toc-list li a:hover {
            color: var(--accent);
        }

        /* Разделитель между рецептами */
        .section-divider {
            height: 40px;
        }
        @media print {
            .section-divider {
                height: 0;
                page-break-before: always;
            }
            .cookbook-header {
                background: #fff;
                border-bottom-color: #ccc;
            }
            .cookbook-header h1 {
                color: #000;
            }
            .cookbook-header h1::after {
                background: #000;
            }
            .toc h2 {
                color: #555;
            }
            .toc-list li a {
                color: #555;
            }
        }
    """
    else:
        extra_css = """
        /* ===== СТИЛИ СБОРНИКА (Modern) ===== */
        .cookbook-header {
            text-align: center;
            padding: 60px 48px 40px;
            background: linear-gradient(135deg, #fafdfa 0%, #f0f9f0 100%);
            border-bottom: 1px solid var(--border);
        }
        .cookbook-header h1 {
            font-family: var(--font-heading);
            font-size: 42px;
            font-weight: 700;
            color: var(--text);
            margin-bottom: 8px;
        }
        .cookbook-header p {
            color: var(--text-light);
            font-size: 17px;
        }

        /* Оглавление */
        .toc {
            padding: 32px 48px;
            border-bottom: 1px solid var(--border);
        }
        .toc h2 {
            font-family: var(--font-heading);
            font-size: 20px;
            font-weight: 600;
            color: var(--text);
            margin-bottom: 16px;
        }
        .toc-list {
            list-style: none;
            padding: 0;
            columns: 2;
            column-gap: 24px;
        }
        @media (max-width: 600px) {
            .toc-list {
                columns: 1;
            }
        }
        .toc-list li {
            margin-bottom: 8px;
            break-inside: avoid;
        }
        .toc-list li a {
            color: var(--accent-dark);
            text-decoration: none;
            font-size: 15px;
            padding: 4px 0;
            display: inline-block;
            transition: color 0.2s;
        }
        .toc-list li a:hover {
            color: var(--accent);
        }

        /* Разделитель между рецептами */
        .section-divider {
            height: 40px;
        }
        @media print {
            .section-divider {
                height: 0;
                page-break-before: always;
            }
        }
    """

    # Собираем итоговый HTML
    html = f"""<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <link rel="icon" type="image/png" href="favicon.png">
    <title>{title}</title>
    <style>
{base_css}
{extra_css}
    </style>
</head>
<body>

    <div class="container">

        <!-- ШАПКА СБОРНИКА -->
        <div class="cookbook-header">
            <h1>{title}</h1>
            <p>{len(recipes)} рецептов</p>
        </div>

        <!-- ОГЛАВЛЕНИЕ -->
        <div class="toc">
            <h2>Содержание</h2>
            {toc_html}
        </div>

        {recipes_html}

    </div>

</body>
</html>"""

    output_path.write_text(html, encoding="utf-8")
    print(f"Сборник сохранён: {output_path} ({len(recipes)} рецептов)")


def main():
    recipe_dirs = get_recipe_dirs()
    print(f"Найдено каталогов с рецептами: {len(recipe_dirs)}")
    print()

    print("=== Сборник Modern ===")
    build_cookbook("modern", OUTPUT_MODERN, recipe_dirs)

    print()
    print("=== Сборник Chef ===")
    build_cookbook("chef", OUTPUT_CHEF, recipe_dirs)

    print()
    print("Готово!")


if __name__ == "__main__":
    main()