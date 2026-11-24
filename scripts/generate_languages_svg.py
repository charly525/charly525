import html
import json
import os
import urllib.request

USERNAME = os.environ["GITHUB_USERNAME"]
TOKEN = os.environ.get("GITHUB_TOKEN", "")
OUTPUT_PATH = os.environ.get("OUTPUT_PATH", "assets/languages.svg")
MIN_PERCENTAGE = float(os.environ.get("MIN_PERCENTAGE", "0.1"))

PALETTE = [
    "#00e5ff",
    "#2979ff",
    "#38bdf8",
    "#2dd4bf",
    "#60a5fa",
    "#22d3ee",
    "#818cf8",
    "#34d399",
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


def build_symbol_svg(lang: str, fallback_color: str) -> str:
    """
    Devuelve un ícono/símbolo vectorial (en un cuadro de 26x26) para el lenguaje.
    Si el lenguaje es nuevo y no está mapeado, usa un emblema genérico de código.
    """
    key = lang.strip().lower()

    # Símbolos personalizados (coordenadas dentro de un grupo de 26x26)
    if key == "python":
        return """
        <rect x="1" y="1" width="24" height="24" rx="6" fill="#10233d" stroke="#3776ab" stroke-width="1.2"/>
        <path d="M13 5.5c-3.2 0-3 1.4-3 1.4v1.7h3.1v.5H8.8c-1.5 0-2.8.9-2.8 2.8s1.1 2.8 2.5 2.8h1.5v-1.3c0-1.4 1.2-2.6 2.6-2.6h2.7c1.2 0 2.2-1 2.2-2.2V7.6c0-1.1-.9-2.1-4.5-2.1zm-1.6 1.2a.7.7 0 1 1 0 1.4.7.7 0 0 1 0-1.4z" fill="#4b8bbe"/>
        <path d="M13 20.5c3.2 0 3-1.4 3-1.4v-1.7h-3.1v-.5h4.3c1.5 0 2.8-.9 2.8-2.8s-1.1-2.8-2.5-2.8H16v1.3c0 1.4-1.2 2.6-2.6 2.6h-2.7c-1.2 0-2.2 1-2.2 2.2v1.9c0 1.1.9 2.1 4.5 2.1zm1.6-1.2a.7.7 0 1 1 0-1.4.7.7 0 0 1 0 1.4z" fill="#ffd43b"/>
        """

    if key == "c":
        return """
        <rect x="1" y="1" width="24" height="24" rx="6" fill="#0d2238" stroke="#659ad2" stroke-width="1.2"/>
        <path d="M17.2 8.7A5.2 5.2 0 1 0 17.2 17.3" fill="none" stroke="#659ad2" stroke-width="2.6" stroke-linecap="round"/>
        """

    if key in ("c++", "cpp"):
        return """
        <rect x="1" y="1" width="24" height="24" rx="6" fill="#0d2238" stroke="#0086d4" stroke-width="1.2"/>
        <path d="M12.5 9.2a4.4 4.4 0 1 0 0 7.6" fill="none" stroke="#4fc3f7" stroke-width="2.2" stroke-linecap="round"/>
        <path d="M15.5 11.5v3m-1.5-1.5h3M20 11.5v3m-1.5-1.5h3" stroke="#00e5ff" stroke-width="1.6" stroke-linecap="round"/>
        """

    if key == "vhdl":
        return """
        <rect x="1" y="1" width="24" height="24" rx="6" fill="#0b2433" stroke="#00e5ff" stroke-width="1.2"/>
        <rect x="8.5" y="8.5" width="9" height="9" rx="1.5" fill="none" stroke="#00e5ff" stroke-width="1.8"/>
        <path d="M5.5 10.5h3m-3 5h3m9-5h3m-3 5h3M10.5 5.5v3m5-3v3m-5 9v3m5-3v3" stroke="#38bdf8" stroke-width="1.5" stroke-linecap="round"/>
        """

    if key in ("shell", "bash", "zsh"):
        return """
        <rect x="1" y="1" width="24" height="24" rx="6" fill="#0b2624" stroke="#2dd4bf" stroke-width="1.2"/>
        <path d="M7.5 9.5l4 3.5-4 3.5M13.5 17h5" fill="none" stroke="#2dd4bf" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
        """

    if key == "html":
        return """
        <rect x="1" y="1" width="24" height="24" rx="6" fill="#291610" stroke="#f97316" stroke-width="1.2"/>
        <path d="M7.5 7h11l-1 10.5-4.5 1.5-4.5-1.5L7.5 7z" fill="none" stroke="#fb923c" stroke-width="1.6" stroke-linejoin="round"/>
        <path d="M10.2 11h5.6l-.3 3.2-2.7.8-2.7-.8" fill="none" stroke="#fdba74" stroke-width="1.4" stroke-linecap="round"/>
        """

    if key == "css":
        return """
        <rect x="1" y="1" width="24" height="24" rx="6" fill="#0d1e36" stroke="#38bdf8" stroke-width="1.2"/>
        <path d="M7.5 7h11l-1 10.5-4.5 1.5-4.5-1.5L7.5 7z" fill="none" stroke="#38bdf8" stroke-width="1.6" stroke-linejoin="round"/>
        <text x="13" y="15.2" text-anchor="middle" fill="#7dd3fc" font-family="Consolas, monospace" font-size="6.8" font-weight="700">#</text>
        """

    if key in ("javascript", "js"):
        return """
        <rect x="1" y="1" width="24" height="24" rx="6" fill="#29230b" stroke="#facc15" stroke-width="1.2"/>
        <text x="13" y="16.5" text-anchor="middle" fill="#facc15" font-family="Consolas, monospace" font-size="10.5" font-weight="700">JS</text>
        """

    if key in ("typescript", "ts"):
        return """
        <rect x="1" y="1" width="24" height="24" rx="6" fill="#0c2038" stroke="#3b82f6" stroke-width="1.2"/>
        <text x="13" y="16.5" text-anchor="middle" fill="#60a5fa" font-family="Consolas, monospace" font-size="10.5" font-weight="700">TS</text>
        """

    if "jupyter" in key:
        return """
        <rect x="1" y="1" width="24" height="24" rx="6" fill="#27170d" stroke="#fb923c" stroke-width="1.2"/>
        <circle cx="13" cy="13" r="4.2" fill="none" stroke="#fb923c" stroke-width="1.8"/>
        <circle cx="7.5" cy="7.5" r="1.4" fill="#fdba74"/>
        <circle cx="18.5" cy="18.5" r="1.4" fill="#fdba74"/>
        """

    if key == "makefile":
        return """
        <rect x="1" y="1" width="24" height="24" rx="6" fill="#0f213a" stroke="#60a5fa" stroke-width="1.2"/>
        <path d="M7.5 16.5l8.5-8.5 2 2-8.5 8.5-2.5.5.5-2.5z" fill="none" stroke="#60a5fa" stroke-width="1.7" stroke-linejoin="round"/>
        """

    if key == "cmake":
        return """
        <rect x="1" y="1" width="24" height="24" rx="6" fill="#0b2333" stroke="#00e5ff" stroke-width="1.2"/>
        <polygon points="13,6.5 19,18.5 7,18.5" fill="none" stroke="#00e5ff" stroke-width="1.8" stroke-linejoin="round"/>
        """

    if key == "powershell":
        return """
        <rect x="1" y="1" width="24" height="24" rx="6" fill="#0c1b36" stroke="#38bdf8" stroke-width="1.2"/>
        <path d="M8 9.5l4.5 3.5L8 16.5M13.5 17h4.5" fill="none" stroke="#7dd3fc" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round"/>
        """

    # Símbolo por defecto para cualquier lenguaje nuevo
    return f"""
    <rect x="1" y="1" width="24" height="24" rx="6" fill="#0d1b2e" stroke="{fallback_color}" stroke-width="1.2"/>
    <path d="M9.5 10L6.5 13l3 3M16.5 10l3 3-3 3M14 8.5l-2 9" fill="none" stroke="{fallback_color}" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"/>
    """


def build_svg(items):
    width = 720
    header_height = 88
    row_height = 48
    padding_x = 24
    bar_x = 270
    bar_max_width = 335
    bottom_padding = 22

    count = max(len(items), 1)
    height = header_height + (count * row_height) + bottom_padding

    # Barra panorámica superior de distribución
    stacked_segments = []
    curr_x = padding_x
    total_bar_w = width - padding_x * 2
    for idx, (lang, _, pct) in enumerate(items):
        seg_w = max(2.0, (pct / 100.0) * total_bar_w)
        color = PALETTE[idx % len(PALETTE)]
        stacked_segments.append(
            f'<rect x="{curr_x:.1f}" y="54" width="0" height="7" rx="3.5" fill="{color}">'
            f'<animate attributeName="width" from="0" to="{seg_w:.1f}" dur="0.85s" fill="freeze"/>'
            f"</rect>"
        )
        curr_x += seg_w

    rows_svg = []
    for idx, (lang, byte_count, pct) in enumerate(items):
        y = header_height + idx * row_height
        color = PALETTE[idx % len(PALETTE)]
        target_w = max(8.0, (pct / 100.0) * bar_max_width)
        delay = round(idx * 0.07, 2)
        safe_lang = html.escape(lang)
        pct_text = f"{pct:.1f}%" if pct >= 1.0 else f"{pct:.2f}%"
        symbol_inner = build_symbol_svg(lang, color)

        row = f"""  <g transform="translate(0, {y})">
    <rect x="{padding_x}" y="3" width="{width - padding_x * 2}" height="40" rx="10"
          fill="#0b1322" stroke="#182b49" stroke-width="1"/>

    <!-- Símbolo del lenguaje -->
    <g transform="translate({padding_x + 10}, 10)">
      {symbol_inner.strip()}
    </g>

    <!-- Nombre del lenguaje -->
    <text x="{padding_x + 44}" y="28" fill="#eef6ff"
          font-family="Segoe UI, Ubuntu, Cantarell, sans-serif" font-size="14" font-weight="600">{safe_lang}</text>

    <!-- Track de la barra -->
    <rect x="{bar_x}" y="17" width="{bar_max_width}" height="12" rx="6" fill="#132238"/>

    <!-- Barra animada -->
    <rect x="{bar_x}" y="17" width="0" height="12" rx="6" fill="url(#barGrad{idx % len(PALETTE)})">
      <animate attributeName="width" from="0" to="{target_w:.1f}" dur="0.9s"
               begin="{delay}s" fill="freeze"/>
    </rect>

    <!-- Porcentaje -->
    <text x="{width - padding_x - 14}" y="28" text-anchor="end" fill="#8be9fd"
          font-family="Consolas, monospace" font-size="13.5" font-weight="700">{pct_text}</text>
  </g>"""
        rows_svg.append(row)

    if not items:
        rows_svg.append(
            f"""  <text x="{padding_x}" y="{header_height + 26}" fill="#8da4c4"
      font-family="Segoe UI, sans-serif" font-size="13">Sin lenguajes detectados aún.</text>"""
        )

    bar_gradients = "\n".join(
        f"""    <linearGradient id="barGrad{i}" x1="0%" y1="0%" x2="100%" y2="0%">
      <stop offset="0%" stop-color="{c}"/>
      <stop offset="100%" stop-color="#38bdf8"/>
    </linearGradient>"""
        for i, c in enumerate(PALETTE)
    )

    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">
  <defs>
    <linearGradient id="bgGrad" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#050811"/>
      <stop offset="100%" stop-color="#091326"/>
    </linearGradient>
    <linearGradient id="topLine" x1="0%" y1="0%" x2="100%" y2="0%">
      <stop offset="0%" stop-color="#00e5ff"/>
      <stop offset="100%" stop-color="#2979ff"/>
    </linearGradient>
{bar_gradients}
  </defs>

  <rect width="{width}" height="{height}" rx="16" fill="url(#bgGrad)" stroke="#1b3358" stroke-width="1.5"/>
  <rect x="0" y="0" width="{width}" height="3" rx="1.5" fill="url(#topLine)"/>

  <text x="{padding_x}" y="35" fill="#f4f9ff"
        font-family="Segoe UI, Ubuntu, Cantarell, sans-serif" font-size="19" font-weight="700">Lenguajes por Uso en Repositorios</text>
  <text x="{width - padding_x}" y="34" text-anchor="end" fill="#60a5fa"
        font-family="Consolas, monospace" font-size="12.5">@{html.escape(USERNAME)}</text>

  <!-- Barra panorámica superior -->
  <rect x="{padding_x}" y="54" width="{total_bar_w}" height="7" rx="3.5" fill="#101d33"/>
  {"".join(stacked_segments)}

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
