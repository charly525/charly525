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

# Mapa de caracteres pixelados (5 columnas x 7 filas)
PIXEL_FONT = {
    "A": ["01110", "10001", "10001", "11111", "10001", "10001", "10001"],
    "B": ["11110", "10001", "10001", "11110", "10001", "10001", "11110"],
    "C": ["01111", "10000", "10000", "10000", "10000", "10000", "01111"],
    "D": ["11110", "10001", "10001", "10001", "10001", "10001", "11110"],
    "E": ["11111", "10000", "10000", "11110", "10000", "10000", "11111"],
    "F": ["11111", "10000", "10000", "11110", "10000", "10000", "10000"],
    "G": ["01111", "10000", "10000", "10111", "10001", "10001", "01111"],
    "H": ["10001", "10001", "10001", "11111", "10001", "10001", "10001"],
    "I": ["11111", "00100", "00100", "00100", "00100", "00100", "11111"],
    "J": ["00111", "00010", "00010", "00010", "10010", "10010", "01100"],
    "K": ["10001", "10010", "10100", "11000", "10100", "10010", "10001"],
    "L": ["10000", "10000", "10000", "10000", "10000", "10000", "11111"],
    "M": ["10001", "11011", "10101", "10101", "10001", "10001", "10001"],
    "N": ["10001", "11001", "10101", "10011", "10001", "10001", "10001"],
    "O": ["01110", "10001", "10001", "10001", "10001", "10001", "01110"],
    "P": ["11110", "10001", "10001", "11110", "10000", "10000", "10000"],
    "Q": ["01110", "10001", "10001", "10001", "10101", "10010", "01101"],
    "R": ["11110", "10001", "10001", "11110", "10100", "10010", "10001"],
    "S": ["01111", "10000", "10000", "01110", "00001", "00001", "11110"],
    "T": ["11111", "00100", "00100", "00100", "00100", "00100", "00100"],
    "U": ["10001", "10001", "10001", "10001", "10001", "10001", "01110"],
    "V": ["10001", "10001", "10001", "10001", "10001", "01010", "00100"],
    "W": ["10001", "10001", "10001", "10101", "10101", "11011", "10001"],
    "X": ["10001", "10001", "01010", "00100", "01010", "10001", "10001"],
    "Y": ["10001", "10001", "01010", "00100", "00100", "00100", "00100"],
    "Z": ["11111", "00001", "00010", "00100", "01000", "10000", "11111"],
    "0": ["01110", "10011", "10101", "10101", "11001", "10001", "01110"],
    "1": ["00100", "01100", "00100", "00100", "00100", "00100", "01110"],
    "2": ["01110", "10001", "00001", "00110", "01000", "10000", "11111"],
    "3": ["11110", "00001", "00001", "01110", "00001", "00001", "11110"],
    "4": ["00010", "00110", "01010", "10010", "11111", "00010", "00010"],
    "5": ["11111", "10000", "11110", "00001", "00001", "10001", "01110"],
    "6": ["01110", "10000", "11110", "10001", "10001", "10001", "01110"],
    "7": ["11111", "00001", "00010", "00100", "01000", "01000", "01000"],
    "8": ["01110", "10001", "10001", "01110", "10001", "10001", "01110"],
    "9": ["01110", "10001", "10001", "01111", "00001", "00001", "01110"],
    ".": ["00000", "00000", "00000", "00000", "00000", "01100", "01100"],
    ":": ["00000", "01100", "01100", "00000", "01100", "01100", "00000"],
    "-": ["00000", "00000", "00000", "11111", "00000", "00000", "00000"],
    "+": ["00000", "00100", "00100", "11111", "00100", "00100", "00000"],
    "#": ["01010", "01010", "11111", "01010", "11111", "01010", "01010"],
    "@": ["01110", "10001", "10111", "10101", "10111", "10000", "01110"],
    "%": ["11001", "11010", "00100", "01000", "10110", "10011", "00000"],
    "/": ["00001", "00010", "00010", "00100", "01000", "01000", "10000"],
    "_": ["00000", "00000", "00000", "00000", "00000", "00000", "11111"],
    " ": ["00000", "00000", "00000", "00000", "00000", "00000", "00000"],
}


def render_pixel_text(
    text: str,
    x: float,
    y: float,
    px: float = 2.0,
    char_gap: float = 1.6,
    fill: str = "#e6f1ff",
    align: str = "left",
) -> str:
    """
    Dibuja texto en bloques sólidos de píxeles (sin huecos internos entre píxeles
    adyacentes) con tamaño configurable.
    """
    upper = text.upper()
    cols_per_char = 5
    char_w = cols_per_char * px
    step_x = char_w + char_gap
    total_w = max(0.0, len(upper) * step_x - char_gap)

    start_x = x
    if align == "right":
        start_x = x - total_w
    elif align == "center":
        start_x = x - total_w / 2.0

    # Pequeño solape de 0.15px evita líneas finas de antialiasing entre píxeles contiguos
    overlap = 0.15
    rects = []
    for char_idx, ch in enumerate(upper):
        glyph = PIXEL_FONT.get(ch, PIXEL_FONT[" "])
        gx = start_x + char_idx * step_x
        for r_idx, row_bits in enumerate(glyph):
            for c_idx, bit in enumerate(row_bits):
                if bit == "1":
                    rx = gx + c_idx * px
                    ry = y + r_idx * px
                    rects.append(
                        f'<rect x="{rx:.2f}" y="{ry:.2f}" '
                        f'width="{px + overlap:.2f}" height="{px + overlap:.2f}" fill="{fill}"/>'
                    )
    return "\n    ".join(rects)


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
    key = lang.strip().lower()

    if key == "python":
        return """
        <rect x="1" y="1" width="22" height="22" rx="5" fill="#10233d" stroke="#3776ab" stroke-width="1.2"/>
        <path d="M12 4.8c-2.9 0-2.7 1.3-2.7 1.3v1.5h2.8v.5H8.1c-1.4 0-2.5.8-2.5 2.5s1 2.5 2.3 2.5h1.3v-1.2c0-1.3 1.1-2.3 2.4-2.3h2.4c1.1 0 2-.9 2-2V6.7c0-1-.8-1.9-4.1-1.9zm-1.4 1.1a.6.6 0 1 1 0 1.2.6.6 0 0 1 0-1.2z" fill="#4b8bbe"/>
        <path d="M12 19.2c2.9 0 2.7-1.3 2.7-1.3v-1.5h-2.8v-.5h4c1.4 0 2.5-.8 2.5-2.5s-1-2.5-2.3-2.5h-1.3v1.2c0 1.3-1.1 2.3-2.4 2.3H9.9c-1.1 0-2 .9-2 2v1.7c0 1 .8 1.9 4.1 1.9zm1.4-1.1a.6.6 0 1 1 0-1.2.6.6 0 0 1 0 1.2z" fill="#ffd43b"/>
        """

    if key == "c":
        return """
        <rect x="1" y="1" width="22" height="22" rx="5" fill="#0d2238" stroke="#659ad2" stroke-width="1.2"/>
        <path d="M15.8 8.2A4.8 4.8 0 1 0 15.8 15.8" fill="none" stroke="#659ad2" stroke-width="2.4" stroke-linecap="round"/>
        """

    if key in ("c++", "cpp"):
        return """
        <rect x="1" y="1" width="22" height="22" rx="5" fill="#0d2238" stroke="#0086d4" stroke-width="1.2"/>
        <path d="M11.5 8.6a4 4 0 1 0 0 6.8" fill="none" stroke="#4fc3f7" stroke-width="2" stroke-linecap="round"/>
        <path d="M14.2 10.6v2.8m-1.4-1.4h2.8M18.3 10.6v2.8m-1.4-1.4h2.8" stroke="#00e5ff" stroke-width="1.5" stroke-linecap="round"/>
        """

    if key == "vhdl":
        return """
        <rect x="1" y="1" width="22" height="22" rx="5" fill="#0b2433" stroke="#00e5ff" stroke-width="1.2"/>
        <rect x="7.8" y="7.8" width="8.4" height="8.4" rx="1.4" fill="none" stroke="#00e5ff" stroke-width="1.7"/>
        <path d="M5 9.8h2.8m-2.8 4.4h2.8m8.4-4.4h2.8m-2.8 4.4h2.8M9.8 5v2.8m4.4-2.8v2.8m-4.4 8.4v2.8m4.4-2.8v2.8" stroke="#38bdf8" stroke-width="1.4" stroke-linecap="round"/>
        """

    if key in ("shell", "bash", "zsh"):
        return """
        <rect x="1" y="1" width="22" height="22" rx="5" fill="#0b2624" stroke="#2dd4bf" stroke-width="1.2"/>
        <path d="M6.8 8.8l3.6 3.2-3.6 3.2M12.4 15.5h4.6" fill="none" stroke="#2dd4bf" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round"/>
        """

    if key == "html":
        return """
        <rect x="1" y="1" width="22" height="22" rx="5" fill="#291610" stroke="#f97316" stroke-width="1.2"/>
        <path d="M6.8 6.5h10.4l-.9 9.6-4.3 1.4-4.3-1.4-.9-9.6z" fill="none" stroke="#fb923c" stroke-width="1.5" stroke-linejoin="round"/>
        <path d="M9.3 10.2h5.4l-.2 2.9-2.5.7-2.5-.7" fill="none" stroke="#fdba74" stroke-width="1.3" stroke-linecap="round"/>
        """

    if "jupyter" in key:
        return """
        <rect x="1" y="1" width="22" height="22" rx="5" fill="#27170d" stroke="#fb923c" stroke-width="1.2"/>
        <circle cx="12" cy="12" r="3.8" fill="none" stroke="#fb923c" stroke-width="1.7"/>
        <circle cx="6.9" cy="6.9" r="1.3" fill="#fdba74"/>
        <circle cx="17.1" cy="17.1" r="1.3" fill="#fdba74"/>
        """

    if key == "makefile":
        return """
        <rect x="1" y="1" width="22" height="22" rx="5" fill="#0f213a" stroke="#60a5fa" stroke-width="1.2"/>
        <path d="M6.8 15.2l7.8-7.8 1.9 1.9-7.8 7.8-2.3.4.4-2.2z" fill="none" stroke="#60a5fa" stroke-width="1.6" stroke-linejoin="round"/>
        """

    if key == "cmake":
        return """
        <rect x="1" y="1" width="22" height="22" rx="5" fill="#0b2333" stroke="#00e5ff" stroke-width="1.2"/>
        <polygon points="12,6 17.5,17 6.5,17" fill="none" stroke="#00e5ff" stroke-width="1.7" stroke-linejoin="round"/>
        """

    if key == "powershell":
        return """
        <rect x="1" y="1" width="22" height="22" rx="5" fill="#0c1b36" stroke="#38bdf8" stroke-width="1.2"/>
        <path d="M7.2 8.8l4.1 3.2-4.1 3.2M12.5 15.5h4.2" fill="none" stroke="#7dd3fc" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/>
        """

    return f"""
    <rect x="1" y="1" width="22" height="22" rx="5" fill="#0d1b2e" stroke="{fallback_color}" stroke-width="1.2"/>
    <path d="M8.8 9.2L6 12l2.8 2.8M15.2 9.2L18 12l-2.8 2.8M13 7.8l-1.8 8.4" fill="none" stroke="{fallback_color}" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"/>
    """


def build_svg(items):
    width = 760
    header_height = 80
    row_height = 44
    padding_x = 22
    bar_x = 278
    bar_max_width = 368
    bottom_padding = 20

    count = max(len(items), 1)
    height = header_height + (count * row_height) + bottom_padding

    total_bar_w = width - padding_x * 2
    stacked_segments = []
    curr_x = padding_x
    for idx, (_, _, pct) in enumerate(items):
        seg_w = max(2.0, (pct / 100.0) * total_bar_w)
        color = PALETTE[idx % len(PALETTE)]
        stacked_segments.append(
            f'<rect x="{curr_x:.1f}" y="48" width="0" height="7" rx="2" fill="{color}">'
            f'<animate attributeName="width" from="0" to="{seg_w:.1f}" dur="0.85s" fill="freeze"/>'
            f"</rect>"
        )
        curr_x += seg_w

    title_pixels = render_pixel_text(
        "LENGUAJES",
        x=padding_x,
        y=20,
        px=2.3,
        char_gap=1.8,
        fill="#00e5ff",
        align="left",
    )
    user_pixels = render_pixel_text(
        f"@{USERNAME}",
        x=width - padding_x,
        y=22,
        px=1.55,
        char_gap=1.2,
        fill="#60a5fa",
        align="right",
    )

    rows_svg = []
    for idx, (lang, _, pct) in enumerate(items):
        y = header_height + idx * row_height
        color = PALETTE[idx % len(PALETTE)]
        target_w = max(8.0, (pct / 100.0) * bar_max_width)
        delay = round(idx * 0.06, 2)
        pct_text = f"{pct:.1f}%" if pct >= 1.0 else f"{pct:.2f}%"
        symbol_inner = build_symbol_svg(lang, color)

        lang_pixels = render_pixel_text(
            lang,
            x=padding_x + 38,
            y=14,
            px=1.65,
            char_gap=1.3,
            fill="#eef6ff",
            align="left",
        )
        pct_pixels = render_pixel_text(
            pct_text,
            x=width - padding_x - 12,
            y=14,
            px=1.65,
            char_gap=1.3,
            fill="#00e5ff",
            align="right",
        )

        row = f"""  <g transform="translate(0, {y})">
    <rect x="{padding_x}" y="2" width="{width - padding_x * 2}" height="38" rx="6"
          fill="#0b1322" stroke="#182b49" stroke-width="1"/>

    <g transform="translate({padding_x + 9}, 9)">
      {symbol_inner.strip()}
    </g>

    {lang_pixels}

    <rect x="{bar_x}" y="16" width="{bar_max_width}" height="10" rx="2.5" fill="#132238"/>
    <rect x="{bar_x}" y="16" width="0" height="10" rx="2.5" fill="{color}">
      <animate attributeName="width" from="0" to="{target_w:.1f}" dur="0.9s"
               begin="{delay}s" fill="freeze"/>
    </rect>

    {pct_pixels}
  </g>"""
        rows_svg.append(row)

    if not items:
        empty_px = render_pixel_text(
            "SIN LENGUAJES",
            x=padding_x,
            y=header_height + 14,
            px=1.7,
            char_gap=1.3,
            fill="#8da4c4",
        )
        rows_svg.append(f"  <g>{empty_px}</g>")

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
  </defs>

  <rect width="{width}" height="{height}" rx="12" fill="url(#bgGrad)" stroke="#1b3358" stroke-width="1.5"/>
  <rect x="0" y="0" width="{width}" height="3" fill="url(#topLine)"/>

  {title_pixels}
  {user_pixels}

  <rect x="{padding_x}" y="48" width="{total_bar_w}" height="7" rx="2" fill="#101d33"/>
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
