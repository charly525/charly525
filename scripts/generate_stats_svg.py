import html
import json
import os
import urllib.parse
import urllib.request

USERNAME = os.environ["GITHUB_USERNAME"]
TOKEN = os.environ.get("GITHUB_TOKEN", "")
DISPLAY_NAME = os.environ.get("STATS_TITLE_NAME", "").strip()
OUTPUT_PATH = os.environ.get("OUTPUT_PATH", "assets/stats.svg")


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
    # Puntaje ponderado sencillo para el anillo y rango visual
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
            'fill="none" stroke="#4f6ef7" stroke-width="1.6" stroke-linejoin="round"/>'
        )
    if kind == "commit":
        return (
            '<path d="M4.2,10 A5.8,5.8 0 1,1 5.8,14.1" fill="none" '
            'stroke="#4f6ef7" stroke-width="1.6" stroke-linecap="round"/>'
            '<polyline points="2.5,7.2 4.2,10.2 7.2,8.8" fill="none" '
            'stroke="#4f6ef7" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"/>'
            '<polyline points="10,6.5 10,10.2 12.6,11.8" fill="none" '
            'stroke="#4f6ef7" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"/>'
        )
    if kind == "pr":
        return (
            '<circle cx="5.5" cy="4.8" r="2" fill="none" stroke="#4f6ef7" stroke-width="1.5"/>'
            '<circle cx="5.5" cy="15.2" r="2" fill="none" stroke="#4f6ef7" stroke-width="1.5"/>'
            '<circle cx="14.5" cy="13.2" r="2" fill="none" stroke="#4f6ef7" stroke-width="1.5"/>'
            '<line x1="5.5" y1="6.8" x2="5.5" y2="13.2" stroke="#4f6ef7" stroke-width="1.5"/>'
            '<path d="M14.5,11.2 V8.8 C14.5,6.6 12.7,4.8 10.5,4.8 H7.5" fill="none" '
            'stroke="#4f6ef7" stroke-width="1.5"/>'
        )
    if kind == "issue":
        return (
            '<circle cx="10" cy="10" r="7.5" fill="none" stroke="#4f6ef7" stroke-width="1.6"/>'
            '<line x1="10" y1="6" x2="10" y2="11.2" stroke="#4f6ef7" stroke-width="1.8" stroke-linecap="round"/>'
            '<circle cx="10" cy="14.2" r="1" fill="#4f6ef7"/>'
        )
    # contributed / repo
    return (
        '<path d="M5,3.5 H15 A1.5,1.5 0 0,1 16.5,5 V17 L10.75,14 L5,17 V5 A1.5,1.5 0 0,1 6.5,3.5 Z" '
        'fill="none" stroke="#4f6ef7" stroke-width="1.6" stroke-linejoin="round"/>'
    )


def build_stats_svg(profile, repos, commits, prs, issues, contributed):
    width = 620
    height = 248

    name = DISPLAY_NAME or profile.get("name") or profile.get("login") or USERNAME
    title_text = html.escape(f"{name}'s GitHub Stats")

    stars = sum(int(r.get("stargazers_count", 0)) for r in repos if not r.get("fork"))
    rank_label, progress = compute_rank(stars, commits, prs, issues, contributed)

    # Círculo de progreso a la derecha
    radius = 52
    circumference = 2 * 3.14159265 * radius
    dash_filled = max(6.0, circumference * progress)

    rows = [
        ("star", "Total Stars Earned:", str(stars)),
        ("commit", "Total Commits:", str(commits)),
        ("pr", "Total PRs:", str(prs)),
        ("issue", "Total Issues:", str(issues)),
        ("repo", "Contributed to (last year):", str(contributed)),
    ]

    row_elements = []
    start_y = 78
    step_y = 30
    for idx, (icon_kind, label, value) in enumerate(rows):
        y = start_y + idx * step_y
        icon_markup = stat_icon_svg(icon_kind)
        row_elements.append(
            f"""  <g transform="translate(26, {y})">
    <g transform="translate(0, -14)">{icon_markup}</g>
    <text x="32" y="0" fill="#e6edf7" font-family="Segoe UI, Ubuntu, Cantarell, sans-serif"
          font-size="14.5" font-weight="700">{html.escape(label)}</text>
    <text x="275" y="0" fill="#eef4ff" font-family="Consolas, monospace"
          font-size="15" font-weight="700">{html.escape(value)}</text>
  </g>"""
        )

    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">
  <defs>
    <linearGradient id="statsBg" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#050714"/>
      <stop offset="55%" stop-color="#0a0924"/>
      <stop offset="100%" stop-color="#120b2e"/>
    </linearGradient>
  </defs>

  <rect x="1" y="1" width="{width - 2}" height="{height - 2}" rx="12"
        fill="url(#statsBg)" stroke="#7c8599" stroke-width="1.2"/>

  <text x="26" y="42" fill="#7c8cf8" font-family="Segoe UI, Ubuntu, Cantarell, sans-serif"
        font-size="21" font-weight="600">{title_text}</text>

{chr(10).join(row_elements)}

  <!-- Anillo de rango a la derecha -->
  <g transform="translate(495, 136)">
    <circle cx="0" cy="0" r="{radius}" fill="none" stroke="#252852" stroke-width="9.5"/>
    <circle cx="0" cy="0" r="{radius}" fill="none" stroke="#7c8cf8" stroke-width="9.5"
            stroke-linecap="round" transform="rotate(-90)"
            stroke-dasharray="0 {circumference:.2f}">
      <animate attributeName="stroke-dasharray"
               from="0 {circumference:.2f}"
               to="{dash_filled:.2f} {circumference:.2f}"
               dur="1s" fill="freeze"/>
    </circle>
    <text x="0" y="9" text-anchor="middle" fill="#e8edff"
          font-family="Segoe UI, Ubuntu, Cantarell, sans-serif"
          font-size="28" font-weight="700">{html.escape(rank_label)}</text>
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

    # Repositorios propios actualizados en el último año como aproximación rápida sin GraphQL
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
