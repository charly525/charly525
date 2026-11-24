import html
import json
import os
import urllib.request

USERNAME = os.environ["GITHUB_USERNAME"]
TOKEN = os.environ.get("GITHUB_TOKEN", "")
OUTPUT_PATH = os.environ.get("OUTPUT_PATH", "assets/languages.svg")
MIN_PERCENTAGE = float(os.environ.get("MIN_PERCENTAGE", "0.1"))

PALETTE = [
    "#00e5ff",  # Cian brillante
    "#2979ff",  # Azul real
    "#00b0ff",  # Azul eléctrico
    "#64ffda",  # Turquesa neón
    "#448aff",  # Azul acento
    "#18ffff",  # Cian intenso
    "#82b1ff",  # Azul claro
    "#1de9b6",  # Verde azulado
]


def github_get(url: str):
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "github-languages-svg-generator",
    }
    if TOKEN:
        headers["Authorization"] = f"Bearer {TOKEN}"
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))


def get_all_repos(username: str):
    repos = []
    page = 1
    while True:
        url = (
            f"https://api.github.com/users/{username}/repos"
            f"?type=owner&per_page=100&page={page}"
        )
        batch = github_get(url)
        if not batch:
            break
        for repo in batch:
            if not repo.get("fork"):
                repos.append(repo)
        page += 1
    return repos


def aggregate_languages(repos):
    totals = {}
    for repo in repos:
        langs_url = repo.get("languages_url")
        if not langs_url:
            continue
        langs = github_get(langs_url)
        for lang, byte_count in langs.items():
            totals[lang] = totals.get(lang, 0) + byte_count

    total_bytes = sum(totals.values())
    if total_bytes == 0:
        return []

    items = []
    for lang, byte_count in sorted(totals.items(), key=lambda kv: kv[1], reverse=True):
        pct = (byte_count / total_bytes) * 100.0
        if pct >= MIN_PERCENTAGE:
            items.append((lang, byte_count, pct))
    return items


def build_svg(items):
    width = 680
    header_height = 68
    row_height = 44
    padding_x = 24
    bar_max_width = 340
    bottom_padding = 20

    count = max(len(items), 1)
    height = header_height + (count * row_height) + bottom_padding

    rows_svg = []
    for idx, (lang, byte_count, pct) in enumerate(items):
        y = header_height + idx * row_height
        color = PALETTE[idx % len(PALETTE)]
        target_w = max(6.0, (pct / 100.0) * bar_max_width)
        delay = round(idx * 0.08, 2)
        safe_lang = html.escape(lang)
        pct_text = f"{pct:.1f}%" if pct >= 1.0 else f"{pct:.2f}%"

        row = f"""  <g transform="translate(0, {y})">
    <rect x="{padding_x}" y="4" width="{width - padding_x * 2}" height="36" rx="8"
          fill="#0c1322" stroke="#182b49" stroke-width="1"/>
    <circle cx="{padding_x + 18}" cy="22" r="5" fill="{color}"/>
    <text x="{padding_x + 32}" y="27" fill="#e6f1ff" font-family="Segoe UI, Ubuntu, Cantarell, sans-serif"
          font-size="13.5" font-weight="600">{safe_lang}</text>

    <!-- Barra de fondo -->
    <rect x="255" y="15" width="{bar_max_width}" height="14" rx="7" fill="#132238"/>

    <!-- Barra animada -->
    <rect x="255" y="15" width="0" height="14" rx="7" fill="{color}">
      <animate attributeName="width" from="0" to="{target_w:.1f}" dur="0.9s"
               begin="{delay}s" fill="freeze"/>
    </rect>

    <!-- Porcentaje -->
    <text x="{width - padding_x - 12}" y="27" text-anchor="end" fill="#7fdbff"
          font-family="Consolas, monospace" font-size="13" font-weight="700">{pct_text}</text>
  </g>"""
        rows_svg.append(row)

    if not rows_svg:
        rows_svg.append(
            f"""  <text x="{padding_x}" y="{header_height + 24}" fill="#8da4c4"
      font-family="Segoe UI, sans-serif" font-size="13">Sin lenguajes detectados aún.</text>"""
        )

    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">
  <defs>
    <linearGradient id="bgGrad" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#050811"/>
      <stop offset="100%" stop-color="#091224"/>
    </linearGradient>
    <linearGradient id="accentLine" x1="0%" y1="0%" x2="100%" y2="0%">
      <stop offset="0%" stop-color="#00e5ff"/>
      <stop offset="100%" stop-color="#2979ff"/>
    </linearGradient>
  </defs>

  <rect width="{width}" height="{height}" rx="14" fill="url(#bgGrad)" stroke="#1a3154" stroke-width="1.5"/>
  <rect x="0" y="0" width="{width}" height="3" rx="1.5" fill="url(#accentLine)"/>

  <text x="{padding_x}" y="34" fill="#f0f7ff" font-family="Segoe UI, Ubuntu, Cantarell, sans-serif"
        font-size="18" font-weight="700">Lenguajes por Uso en Repositorios</text>
  <text x="{width - padding_x}" y="33" text-anchor="end" fill="#64b5f6"
        font-family="Consolas, monospace" font-size="12">@{html.escape(USERNAME)}</text>
  <line x1="{padding_x}" y1="48" x2="{width - padding_x}" y2="48" stroke="#152642" stroke-width="1"/>

{chr(10).join(rows_svg)}
</svg>
"""
    return svg


def main():
    os.makedirs(os.path.dirname(OUTPUT_PATH) or ".", exist_ok=True)
    repos = get_all_repos(USERNAME)
    items = aggregate_languages(repos)
    svg_content = build_svg(items)

    prev_content = ""
    if os.path.exists(OUTPUT_PATH):
        with open(OUTPUT_PATH, "r", encoding="utf-8") as f:
            prev_content = f.read()

    if svg_content != prev_content:
        with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
            f.write(svg_content)
        print(f"Actualizado {OUTPUT_PATH} con {len(items)} lenguajes.")
    else:
        print("Sin cambios en los porcentajes de lenguajes.")


if __name__ == "__main__":
    main()
