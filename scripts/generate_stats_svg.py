import html
import json
import os
import urllib.parse
import urllib.request

USERNAME = os.environ["GITHUB_USERNAME"]
TOKEN = os.environ.get("GITHUB_TOKEN", "")
DISPLAY_NAME = os.environ.get("STATS_TITLE_NAME", "").strip()
OUTPUT_PATH = os.environ.get("OUTPUT_PATH", "assets/stats.svg")

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
    "(": ["00010", "00100", "01000", "01000", "01000", "00100", "00010"],
    ")": ["01000", "00100", "00010", "00010", "00010", "00100", "01000"],
    "'": ["00100", "00100", "01000", "00000", "00000", "00000", "00000"],
    "@": ["01110", "10001", "10111", "10101", "10111", "10000", "01110"],
    " ": ["00000", "00000", "00000", "00000", "00000", "00000", "00000"],
}


def render_pixel_text(
    text: str,
    x: float,
    y: float,
    px: float = 1.8,
    char_gap: float = 1.4,
    fill: str = "#eef6ff",
    align: str = "left",
) -> str:
    upper = text.upper()
    cols_per_char = 5
    step_x = cols_per_char * px + char_gap
    total_w = max(0.0, len(upper) * step_x - char_gap)

    start_x = x
    if align == "right":
        start_x = x - total_w
    elif align == "center":
        start_x = x - total_w / 2.0

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
        "User-Agent": "github-stats-svg-generator",
    }
    if TOKEN:
        headers["Authorization"] = f"Bearer {TOKEN}"
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))


def get_user_profile(username: str):
    return github_get(f"https://api.github.com/users/{urllib.parse.quote(username)}")


def get_all_owned_repos(username: str):
    repos = []
    page = 1
    while True:
        url = (
            f"https://api.github.com/users/{urllib.parse.quote(username)}/repos"
            f"?type=owner&per_page=100&page={page}"
        )
        batch = github_get(url)
        if not batch:
            break
        repos.extend(batch)
        page += 1
    return repos


def search_total_count(query: str) -> int:
    encoded = urllib.parse.quote(query)
    url = f"https://api.github.com/search/issues?q={encoded}&per_page=1"
    data = github_get(url)
    return int(data.get("total_count", 0))


def get_total_commits(username: str) -> int:
    encoded = urllib.parse.quote(f"author:{username}")
    url = f"https://api.github.com/search/commits?q={encoded}&per_page=1"
    headers = {
        "Accept": "application/vnd.github.cloak-preview+json",
        "User-Agent": "github-stats-svg-generator",
    }
    if TOKEN:
        headers["Authorization"] = f"Bearer {TOKEN}"
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=30) as resp:
        data = json.loads(resp.read().decode("utf-8"))
        return int(data.get("total_count", 0))


def compute_rank(stars: int, commits: int, prs: int, issues: int, contributed: int):
    score = (
        commits * 1.0
        + prs * 4.0
        + issues * 2.5
        + stars * 5.0
        + contributed * 3.0
    )
    if score >= 900:
        return "S", 0.90
    if score >= 550:
        return "A+", 0.78
    if score >= 320:
        return "A", 0.65
    if score >= 160:
        return "B+", 0.50
    if score >= 75:
        return "B", 0.36
    return "C+", 0.24


def stat_icon_svg(kind: str) -> str:
    if kind == "star":
        return (
            '<polygon points="10,2.5 12.4,7.4 17.8,8.2 13.9,12 14.8,17.4 '
            '10,14.8 5.2,17.4 6.1,12 2.2,8.2 7.6,7.4" '
            'fill="none" stroke="#00e5ff" stroke-width="1.6" stroke-linejoin="round"/>'
        )
    if kind == "commit":
        return (
            '<path d="M4.2,10 A5.8,5.8 0 1,1 5.8,14.1" fill="none" '
            'stroke="#2979ff" stroke-width="1.6" stroke-linecap="round"/>'
            '<polyline points="2.5,7.2 4.2,10.2 7.2,8.8" fill="none" '
            'stroke="#2979ff" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"/>'
            '<polyline points="10,6.5 10,10.2 12.6,11.8" fill="none" '
            'stroke="#00e5ff" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"/>'
        )
    if kind == "pr":
        return (
            '<circle cx="5.5" cy="4.8" r="2" fill="none" stroke="#00e5ff" stroke-width="1.5"/>'
            '<circle cx="5.5" cy="15.2" r="2" fill="none" stroke="#2979ff" stroke-width="1.5"/>'
            '<circle cx="14.5" cy="13.2" r="2" fill="none" stroke="#00e5ff" stroke-width="1.5"/>'
            '<line x1="5.5" y1="6.8" x2="5.5" y2="13.2" stroke="#38bdf8" stroke-width="1.5"/>'
            '<path d="M14.5,11.2 V8.8 C14.5,6.6 12.7,4.8 10.5,4.8 H7.5" fill="none" '
            'stroke="#38bdf8" stroke-width="1.5"/>'
        )
    if kind == "issue":
        return (
            '<circle cx="10" cy="10" r="7.5" fill="none" stroke="#2979ff" stroke-width="1.6"/>'
            '<line x1="10" y1="6" x2="10" y2="11.2" stroke="#00e5ff" stroke-width="1.8" stroke-linecap="round"/>'
            '<circle cx="10" cy="14.2" r="1" fill="#00e5ff"/>'
        )
    return (
        '<path d="M5,3.5 H15 A1.5,1.5 0 0,1 16.5,5 V17 L10.75,14 L5,17 V5 A1.5,1.5 0 0,1 6.5,3.5 Z" '
        'fill="none" stroke="#00e5ff" stroke-width="1.6" stroke-linejoin="round"/>'
    )


def build_stats_svg(profile, repos, commits, prs, issues, contributed):
    width = 760
    height = 252

    name = DISPLAY_NAME or profile.get("name") or profile.get("login") or USERNAME
    title_px = render_pixel_text(
        f"{name} STATS",
        x=24,
        y=22,
        px=2.1,
        char_gap=1.6,
        fill="#00e5ff",
        align="left",
    )
    user_px = render_pixel_text(
        f"@{USERNAME}",
        x=width - 24,
        y=24,
        px=1.55,
        char_gap=1.2,
        fill="#60a5fa",
        align="right",
    )

    stars = sum(int(r.get("stargazers_count", 0)) for r in repos if not r.get("fork"))
    rank_label, progress = compute_rank(stars, commits, prs, issues, contributed)

    radius = 52
    circumference = 2 * 3.14159265 * radius
    dash_filled = max(6.0, circumference * progress)

    rows = [
        ("star", "TOTAL STARS EARNED:", str(stars)),
        ("commit", "TOTAL COMMITS:", str(commits)),
        ("pr", "TOTAL PRS:", str(prs)),
        ("issue", "TOTAL ISSUES:", str(issues)),
        ("repo", "CONTRIBUTED TO (LAST YEAR):", str(contributed)),
    ]

    row_elements = []
    start_y = 74
    step_y = 32
    for idx, (icon_kind, label, value) in enumerate(rows):
        y = start_y + idx * step_y
        icon_markup = stat_icon_svg(icon_kind)
        label_px = render_pixel_text(
            label,
            x=34,
            y=1,
            px=1.65,
            char_gap=1.3,
            fill="#e6f1ff",
            align="left",
        )
        val_px = render_pixel_text(
            value,
            x=395,
            y=1,
            px=1.75,
            char_gap=1.3,
            fill="#00e5ff",
            align="left",
        )
        row_elements.append(
            f"""  <g transform="translate(24, {y})">
    <rect x="0" y="-11" width="440" height="26" rx="5" fill="#0b1322" stroke="#182b49" stroke-width="1"/>
    <g transform="translate(8, -8)">{icon_markup}</g>
    {label_px}
    {val_px}
  </g>"""
        )

    rank_px = render_pixel_text(
        rank_label,
        x=0,
        y=-9,
        px=3.2,
        char_gap=2.2,
        fill="#eef6ff",
        align="center",
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
  </defs>

  <rect width="{width}" height="{height}" rx="12" fill="url(#bgGrad)" stroke="#1b3358" stroke-width="1.5"/>
  <rect x="0" y="0" width="{width}" height="3" fill="url(#topLine)"/>

  {title_px}
  {user_px}

  <line x1="24" y1="48" x2="{width - 24}" y2="48" stroke="#152642" stroke-width="1"/>

{chr(10).join(row_elements)}

  <g transform="translate(612, 142)">
    <circle cx="0" cy="0" r="{radius + 14}" fill="#0b1322" stroke="#182b49" stroke-width="1"/>
    <circle cx="0" cy="0" r="{radius}" fill="none" stroke="#132238" stroke-width="9"/>
    <circle cx="0" cy="0" r="{radius}" fill="none" stroke="#00e5ff" stroke-width="9"
            stroke-linecap="round" transform="rotate(-90)"
            stroke-dasharray="0 {circumference:.2f}">
      <animate attributeName="stroke-dasharray"
               from="0 {circumference:.2f}"
               to="{dash_filled:.2f} {circumference:.2f}"
               dur="1s" fill="freeze"/>
    </circle>
    {rank_px}
  </g>
</svg>
"""
    return svg


def main():
    os.makedirs(os.path.dirname(OUTPUT_PATH) or ".", exist_ok=True)
    profile = get_user_profile(USERNAME)
    repos = get_all_owned_repos(USERNAME)

    commits = get_total_commits(USERNAME)
    prs = search_total_count(f"author:{USERNAME} type:pr")
    issues = search_total_count(f"author:{USERNAME} type:issue")

    contributed_repos = set()
    for r in repos:
        if r.get("pushed_at", "").startswith("2026"):
            contributed_repos.add(r.get("full_name"))
    contributed = len(contributed_repos)

    svg_content = build_stats_svg(profile, repos, commits, prs, issues, contributed)

    prev_content = ""
    if os.path.exists(OUTPUT_PATH):
        with open(OUTPUT_PATH, "r", encoding="utf-8") as f:
            prev_content = f.read()

    if svg_content != prev_content:
        with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
            f.write(svg_content)
        print(f"Actualizado {OUTPUT_PATH}.")
    else:
        print("Sin cambios en stats.svg.")


if __name__ == "__main__":
    main()
