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
    px: float = 2.4,
    gap: float = 0.6,
    fill: str = "#e6f1ff",
    align: str = "left",
) -> str:
    upper = text.upper()
    cols_per_char = 5
    rows_per_char = 7
    step_x = (cols_per_char + 1) * (px + gap)
    total_w = max(0.0, len(upper) * step_x - (px + gap))

    start_x = x
    if align == "right":
        start_x = x - total_w
    elif align == "center":
        start_x = x - total_w / 2.0

    rects = []
    for char_idx, ch in enumerate(upper):
        glyph = PIXEL_FONT.get(ch, PIXEL_FONT[" "])
        gx = start_x + char_idx * step_x
        for r_idx, row_bits in enumerate(glyph):
            for c_idx, bit in enumerate(row_bits):
                if bit == "1":
                    rx = gx + c_idx * (px + gap)
                    ry = y + r_idx * (px + gap)
                    rects.append(
                        f'<rect x="{rx:.1f}" y="{ry:.1f}" width="{px:.1f}" height="{px:.1f}" fill="{fill}"/>'
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
        <rect x="1" y="1" width="24" height="24" rx="5" fill="#10233d" stroke="#3776ab" stroke-width="1.2"/>
        <path d="M13 5.5c-3.2 0-3 1.4-3 1.4v1.7h3.1v.5H8.8c-1.5 0-2.8.9-2.8 2.8s1.1 2.8 2.5 2.8h1.5v-1.3c0-1.4 1.2-2.6 2.6-2.6h2.7c1.2 0 2.2-1 2.2-2.2V7.6c0-1.1-.9-2.1-4.5-2.1zm-1.6 1.2a.7.7 0 1 1 0 1.4.7.7 0 0 1 0-1.4z" fill="#4b8bbe"/>
        <path d="M13 20.5c3.2 0 3-1.4 3-1.4v-1.7h-3.1v-.5h4.3c1.5 0 2.8-.9 2.8-2.8s-1.1-2.8-2.5-2.8H16v1.3c0 1.4-1.2 2.6-2.6 2.6h-2.7c-1.2 0-2.2 1-2.2 2.2v1.9c0 1.1.9 2.1 4.5 2.1zm1.6-1.2a.7.7 0 1 1 0-1.4.7.7 0 0 1 0 1.4z" fill="#ffd43b"/>
        """

    if key == "c":
        return """
        <rect x="1" y="1" width="24" height="24" rx="5" fill="#0d2238" stroke="#659ad2" stroke-width="1.2"/>
        <path d="M17.2 8.7A5.2 5.2 0 1 0 17.2 17.3" fill="none" stroke="#659ad2" stroke-width="2.6" stroke-linecap="round"/>
        """

    if key in ("c++", "cpp"):
        return """
        <rect x="1" y="1" width="24" height="24" rx="5" fill="#0d2238" stroke="#0086d4" stroke-width="1.2"/>
        <path d="M12.5 9.2a4.4 4.4 0 1 0 0 7.6" fill="none" stroke="#4fc3f7" stroke-width="2.2" stroke-linecap="round"/>
        <path d="M15.5 11.5v3m-1.5-1.5h3M20 11.5v3m-1.5-1.5h3" stroke="#00e5ff" stroke-width="1.6" stroke-linecap="round"/>
        """

    if key == "vhdl":
        return """
        <rect x="1" y="1" width="24" height="24" rx="5" fill="#0b2433" stroke="#00e5ff" stroke-width="1.2"/>
        <rect x="8.5" y="8.5" width="9" height="9" rx="1.5" fill="none" stroke="#00e5ff" stroke-width="1.8"/>
        <path d="M5.5 10.5h3m-3 5h3m9-5h3m-3 5h3M10.5 5.5v3m5-3v3m-5 9v3m5-3v3" stroke="#38bdf8" stroke-width="1.5" stroke-linecap="round"/>
        """

    if key in ("shell", "bash", "zsh"):
        return """
        <rect x="1" y="1" width="24" height="24" rx="5" fill="#0b2624" stroke="#2dd4bf" stroke-width="1.2"/>
        <path d="M7.5 9.5l4 3.5-4 3.5M13.5 17h5" fill="none" stroke="#2dd4bf" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
        """

    if key == "html":
        return """
        <rect x="1" y="1" width="24" height="24" rx="5" fill="#291610" stroke="#f97316" stroke-width="1.2"/>
        <path d="M7.5 7h11l-1 10.5-4.5 1.5-4.5-1.5L7.5 7z" fill="none" stroke="#fb923c" stroke-width="1.6" stroke-linejoin="round"/>
        <path d="M10.2 11h5.6l-.3 3.2-2.7.8-2.7-.8" fill="none" stroke="#fdba74" stroke-width="1.4" stroke-linecap="round"/>
        """

    if "jupyter" in key:
        return """
        <rect x="1" y="1" width="24" height="24" rx="5" fill="#27170d" stroke="#fb923c" stroke-width="1.2"/>
        <circle cx="13" cy="13" r="4.2" fill="none" stroke="#fb923c" stroke-width="1.8"/>
        <circle cx="7.5" cy="7.5" r="1.4" fill="#fdba74"/>
        <circle cx="18.5" cy="18.5" r="1.4" fill="#fdba74"/>
        """

    if key == "makefile":
        return """
        <rect x="1" y="1" width="24" height="24" rx="5" fill="#0f213a" stroke="#60a5fa" stroke-width="1.2"/>
        <path d="M7.5 16.5l8.5-8.5 2 2-8.5 8.5-2.5.5.5-2.5z" fill="none" stroke="#60a5fa" stroke-width="1.7" stroke-linejoin="round"/>
        """

    if key == "cmake":
        return """
        <rect x="1" y="1" width="24" height="24" rx="5" fill="#0b2333" stroke="#00e5ff" stroke-width="1.2"/>
        <polygon points="13,6.5 19,18.5 7,18.5" fill="none" stroke="#00e5ff" stroke-width="1.8" stroke-linejoin="round"/>
        """

    if key == "powershell":
        return """
        <rect x="1" y="1" width="24" height="24" rx="5" fill="#0c1b36" stroke="#38bdf8" stroke-width="1.2"/>
        <path d="M8 9.5l4.5 3.5L8 16.5M13.5 17h4.5" fill="none" stroke="#7dd3fc" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round"/>
        """

    return f"""
    <rect x="1" y="1" width="24" height="24" rx="5" fill="#0d1b2e" stroke="{fallback_color}" stroke-width="1.2"/>
    <path d="M9.5 10L6.5 13l3 3M16.5 10l3 3-3 3M14 8.5l-2 9" fill="none" stroke="{fallback_color}" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"/>
    """


def build_svg(items):
    width = 760
    header_height = 94
    row_height = 50
    padding_x = 24
    bar_x = 310
    bar_max_width = 325
    bottom_padding = 24

    count = max(len(items), 1)
    height = header_height + (count * row_height) + bottom_padding

    total_bar_w = width - padding_x * 2
    stacked_segments = []
    curr_x = padding_x
    for idx, (_, _, pct) in enumerate(items):
        seg_w = max(2.0, (pct / 100.0) * total_bar_w)
        color = PALETTE[idx % len(PALETTE)]
        stacked_segments.append(
            f'<rect x="{curr_x:.1f}" y="58" width="0" height="8" rx="2" fill="{color}">'
            f'<animate attributeName="width" from="0" to="{seg_w:.1f}" dur="0.85s" fill="freeze"/>'
            f"</rect>"
        )
        curr_x += seg_w

    title_pixels = render_pixel_text(
        "LENGUAJES POR USO",
        x=padding_x,
        y=20,
        px=2.8,
        gap=0.7,
        fill="#00e5ff",
        align="left",
    )
    user_pixels = render_pixel_text(
        f"@{USERNAME}",
        x=width - padding_x,
        y=22,
        px=2.2,
        gap=0.6,
        fill="#60a5fa",
        align="right",
    )

    rows_svg = []
    for idx, (lang, _, pct) in enumerate(items):
        y = header_height + idx * row_height
        color = PALETTE[idx % len(PALETTE)]
        target_w = max(8.0, (pct / 100.0) * bar_max_width)
        delay = round(idx * 0.07, 2)
        pct_text = f"{pct:.1f}%" if pct >= 1.0 else f"{pct:.2f}%"
        symbol_inner = build_symbol_svg(lang, color)

        lang_pixels = render_pixel_text(
            lang,
            x=padding_x + 44,
            y=14,
            px=2.1,
            gap=0.5,
            fill="#eef6ff",
            align="left",
        )
        pct_pixels = render_pixel_text(
            pct_text,
            x=width - padding_x - 14,
            y=14,
            px=2.1,
            gap=0.5,
            fill="#00e5ff",
            align="right",
        )

        row = f"""  <g transform="translate(0, {y})">
    <rect x="{padding_x}" y="3" width="{width - padding_x * 2}" height="42" rx="6"
          fill="#0b1322" stroke="#182b49" stroke-width="1"/>

    <g transform="translate({padding_x + 10}, 11)">
      {symbol_inner.strip()}
    </g>

    {lang_pixels}

    <rect x="{bar_x}" y="18" width="{bar_max_width}" height="12" rx="3" fill="#132238"/>
    <rect x="{bar_x}" y="18" width="0" height="12" rx="3" fill="{color}">
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
            y=header_height + 16,
            px=2.2,
            gap=0.6,
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

  <rect x="{padding_x}" y="58" width="{total_bar_w}" height="8" rx="2" fill="#101d33"/>
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
