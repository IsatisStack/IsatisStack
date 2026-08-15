"""Generate the animated Aqua Launch GitHub profile assets.

The generator uses GitHub's REST API for profile/repository data and GraphQL
for the contribution calendar when GITHUB_TOKEN is available. A public HTML
fallback keeps local generation usable without a token.

    python scripts/generate.py          # live public data
    python scripts/generate.py --demo   # deterministic offline preview
"""

from __future__ import annotations

import argparse
import html
import json
import os
import random
import re
import urllib.error
import urllib.request
from datetime import date, timedelta
from pathlib import Path
from xml.sax.saxutils import escape

from PIL import Image, ImageEnhance, ImageOps

ROOT = Path(__file__).resolve().parent.parent
ASSETS = ROOT / "assets"

OUTER = "#0b1d20"
BG = "#071416"
PANEL = "#0a2928"
PANEL_2 = "#0b2227"
HAIR = "#168f82"
TEAL = "#43ead3"
MINT = "#83ffe8"
BLUE = "#4387ff"
PURPLE = "#9b6cff"
YELLOW = "#f2dc56"
ORANGE = "#ff6b48"
GREEN = "#56f73a"
TEXT = "#dcfff7"
MUTED = "#79aaa4"

GLYPHS = {
    "A": ["01110", "10001", "10001", "11111", "10001", "10001", "10001"],
    "B": ["11110", "10001", "10001", "11110", "10001", "10001", "11110"],
    "C": ["01111", "10000", "10000", "10000", "10000", "10000", "01111"],
    "D": ["11110", "10001", "10001", "10001", "10001", "10001", "11110"],
    "E": ["11111", "10000", "10000", "11110", "10000", "10000", "11111"],
    "F": ["11111", "10000", "10000", "11110", "10000", "10000", "10000"],
    "G": ["01111", "10000", "10000", "10111", "10001", "10001", "01110"],
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
    "2": ["01110", "10001", "00001", "00010", "00100", "01000", "11111"],
    "3": ["11110", "00001", "00001", "01110", "00001", "00001", "11110"],
    "4": ["00010", "00110", "01010", "10010", "11111", "00010", "00010"],
    "5": ["11111", "10000", "10000", "11110", "00001", "00001", "11110"],
    "6": ["01110", "10000", "10000", "11110", "10001", "10001", "01110"],
    "7": ["11111", "00001", "00010", "00100", "01000", "01000", "01000"],
    "8": ["01110", "10001", "10001", "01110", "10001", "10001", "01110"],
    "9": ["01110", "10001", "10001", "01111", "00001", "00001", "01110"],
    " ": ["000", "000", "000", "000", "000", "000", "000"],
}


def load_config() -> dict:
    return json.loads((ROOT / "config.json").read_text(encoding="utf-8"))


def request_json(url: str, *, payload: dict | None = None) -> object:
    headers = {"Accept": "application/vnd.github+json", "User-Agent": "aqua-launch-profile"}
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    data = None
    if payload is not None:
        headers["Content-Type"] = "application/json"
        data = json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(url, headers=headers, data=data)
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.load(response)


def profile_data(username: str) -> dict:
    user = request_json(f"https://api.github.com/users/{username}")
    repos = request_json(f"https://api.github.com/users/{username}/repos?per_page=100&sort=updated")
    if not isinstance(user, dict) or not isinstance(repos, list):
        raise RuntimeError("Unexpected response from GitHub REST API")
    original = [repo for repo in repos if not repo.get("fork")]
    languages: dict[str, int] = {}
    for repo in original:
        language = repo.get("language")
        if language:
            languages[language] = languages.get(language, 0) + 1
    return {
        "public_repos": int(user.get("public_repos", len(repos))),
        "followers": int(user.get("followers", 0)),
        "following": int(user.get("following", 0)),
        "stars": sum(int(repo.get("stargazers_count", 0)) for repo in original),
        "languages": sorted(languages.items(), key=lambda item: item[1], reverse=True)[:5],
    }


def contributions_graphql(username: str) -> dict | None:
    if not os.environ.get("GITHUB_TOKEN"):
        return None
    query = """query($login:String!){user(login:$login){contributionsCollection{contributionCalendar{totalContributions weeks{contributionDays{date contributionCount contributionLevel}}}}}}"""
    result = request_json("https://api.github.com/graphql", payload={"query": query, "variables": {"login": username}})
    if not isinstance(result, dict) or result.get("errors"):
        return None
    try:
        calendar = result["data"]["user"]["contributionsCollection"]["contributionCalendar"]
        days = []
        levels = {"NONE": 0, "FIRST_QUARTILE": 1, "SECOND_QUARTILE": 2, "THIRD_QUARTILE": 3, "FOURTH_QUARTILE": 4}
        for week in calendar["weeks"]:
            for item in week["contributionDays"]:
                days.append({"date": item["date"], "count": int(item["contributionCount"]), "level": levels.get(item["contributionLevel"], 0)})
        return {"total": int(calendar["totalContributions"]), "days": days}
    except (KeyError, TypeError):
        return None


def contributions_html(username: str) -> dict:
    url = f"https://github.com/users/{username}/contributions"
    request = urllib.request.Request(url, headers={"User-Agent": "aqua-launch-profile", "X-Requested-With": "XMLHttpRequest"})
    with urllib.request.urlopen(request, timeout=30) as response:
        source = response.read().decode("utf-8", errors="replace")

    tips: dict[str, int] = {}
    for match in re.finditer(r'<tool-tip[^>]*for="([^"]+)"[^>]*>(.*?)</tool-tip>', source, re.I | re.S):
        label = html.unescape(re.sub(r"<[^>]+>", " ", match.group(2)))
        count = re.search(r"(?:No|([\d,]+))\s+contribution", label)
        if count:
            tips[match.group(1)] = int((count.group(1) or "0").replace(",", ""))

    days = []
    for match in re.finditer(r'<td\b([^>]*ContributionCalendar-day[^>]*)>', source, re.I):
        attrs = dict(re.findall(r'([\w:-]+)="([^"]*)"', match.group(1)))
        iso = attrs.get("data-date")
        if not iso:
            continue
        count = attrs.get("data-count")
        days.append({
            "date": iso,
            "count": int(count) if count is not None else tips.get(attrs.get("id", ""), 0),
            "level": int(attrs.get("data-level", "0")),
        })
    if not days:
        raise RuntimeError("GitHub contribution calendar markup could not be parsed")
    total_match = re.search(r"([\d,]+)\s+contributions?\s+in\s+the\s+last\s+year", html.unescape(source), re.I)
    total = int(total_match.group(1).replace(",", "")) if total_match else sum(day["count"] for day in days)
    return {"total": total, "days": sorted(days, key=lambda item: item["date"])}


def demo_data() -> tuple[dict, dict]:
    rng = random.Random(430)
    end = date.today()
    start = end - timedelta(days=370)
    days = []
    for offset in range(371):
        iso = start + timedelta(days=offset)
        active = rng.random() > (0.69 if offset < 190 else 0.54)
        level = rng.choices([1, 2, 3, 4], weights=[44, 30, 18, 8])[0] if active else 0
        days.append({"date": iso.isoformat(), "count": rng.randint(level, level * 4) if level else 0, "level": level})
    profile = {
        "public_repos": 86,
        "followers": 34,
        "following": 18,
        "stars": 119,
        "languages": [["JavaScript", 35], ["TypeScript", 30], ["CSS", 19], ["C#", 6], ["HTML", 4]],
    }
    return profile, {"total": 430, "days": days}


def trim(value: object, size: int) -> str:
    text = " ".join(str(value or "").split())
    return text if len(text) <= size else text[: size - 1].rstrip() + "…"


def portrait_lines(cfg: dict, cols: int = 66, max_rows: int = 50) -> list[str]:
    path = ROOT / cfg["photo"]
    if not path.exists():
        raise RuntimeError(f"Profile photo not found: {path}")
    with Image.open(path) as source:
        image = ImageOps.autocontrast(ImageEnhance.Contrast(ImageOps.grayscale(source)).enhance(1.25))
        rows = min(max_rows, max(1, round(image.height / image.width * cols * 0.78)))
        small = image.resize((cols, rows), Image.Resampling.LANCZOS)
        pixels = list(small.getdata())
    low, high = min(pixels), max(pixels)
    ramp = " .`:-=+*cs#%@"
    lines = []
    for row in range(rows):
        chars = []
        for value in pixels[row * cols : (row + 1) * cols]:
            normalized = (value - low) / max(1, high - low)
            index = min(len(ramp) - 1, int((1.0 - normalized) * len(ramp)))
            chars.append(ramp[index])
        lines.append("".join(chars))
    return lines


def ascii_lines(word: str, alphabet: str, scale_x: int = 2, scale_y: int = 2) -> list[str]:
    clean = "".join(char for char in word.upper() if char in GLYPHS)[:8] or "HELLO"
    rows = []
    for row in range(7):
        chunks = []
        for char_index, char in enumerate(clean):
            glyph = GLYPHS[char][row]
            chunk = "".join(
                (alphabet[(cell_index + row + char_index) % len(alphabet)] * scale_x) if bit == "1" else (" " * scale_x)
                for cell_index, bit in enumerate(glyph)
            )
            chunks.append(chunk)
        expanded = "   ".join(chunks)
        rows.extend([expanded] * scale_y)
    return rows


def shared_style() -> str:
    return """.display{font:700 28px 'Trebuchet MS',sans-serif;fill:__TEXT__}.title{font:700 24px 'Trebuchet MS',sans-serif;fill:__TEXT__}.label{font:700 9px 'Trebuchet MS',sans-serif;fill:__TEAL__;letter-spacing:1.6px}.body{font:12px 'Trebuchet MS',sans-serif;fill:__MUTED__}.mono{font:10px ui-monospace,Consolas,monospace;fill:__MUTED__}@media(prefers-reduced-motion:reduce){*{animation:none!important}}""".replace("__TEXT__", TEXT).replace("__TEAL__", TEAL).replace("__MUTED__", MUTED)


def identity_svg(cfg: dict) -> str:
    portrait = portrait_lines(cfg)
    portrait_defs, portrait_body = [], []
    char_w, line_h, font_size = 4.0, 5.3, 5.9
    portrait_x, portrait_y = 43.0, 87.0
    for row, raw in enumerate(portrait):
        text = raw.rstrip()
        if not text.strip():
            continue
        left = len(text) - len(text.lstrip())
        segment = text[left:]
        x = portrait_x + left * char_w
        y = portrait_y + row * line_h
        width = len(segment) * char_w
        begin = row * 0.038
        portrait_defs.append(f'<clipPath id="portrait-row-{row}"><rect x="{x:.1f}" y="{y - 4.8:.1f}" width="{width:.1f}" height="{line_h + 1:.1f}"><animate attributeName="width" from="0" to="{width:.1f}" begin="{begin:.3f}s" dur=".32s" fill="freeze"/></rect></clipPath>')
        portrait_body.append(f'<g clip-path="url(#portrait-row-{row})"><text x="{x:.1f}" y="{y:.1f}" textLength="{width:.1f}" lengthAdjust="spacing" xml:space="preserve">{escape(segment)}</text></g>')
        portrait_body.append(f'<rect x="{x:.1f}" y="{y - 4.8:.1f}" width="{char_w:.1f}" height="{line_h:.1f}" fill="{MINT}" opacity="0"><set attributeName="opacity" to=".9" begin="{begin:.3f}s"/><animate attributeName="x" from="{x:.1f}" to="{x + width:.1f}" begin="{begin:.3f}s" dur=".32s" fill="freeze"/><set attributeName="opacity" to="0" begin="{begin + .32:.3f}s"/></rect>')

    first = ascii_lines(cfg.get("wordmark") or cfg["name"].split()[0], "$s+")
    second = ascii_lines(cfg.get("wordmark") or cfg["name"].split()[0], "#*=")
    line_a = "".join(f'<text x="0" y="{20 + row * 14.2:.1f}" textLength="510" lengthAdjust="spacingAndGlyphs" xml:space="preserve">{escape(line)}</text>' for row, line in enumerate(first))
    line_b = "".join(f'<text x="0" y="{20 + row * 14.2:.1f}" textLength="510" lengthAdjust="spacingAndGlyphs" xml:space="preserve">{escape(line)}</text>' for row, line in enumerate(second))
    skills = "".join(f'<g transform="translate({337 + index * 87} 329)"><rect width="78" height="20" rx="10" fill="#0d3636" stroke="#17675f"/><text x="39" y="14" text-anchor="middle" class="chip">{escape(skill)}</text></g>' for index, skill in enumerate(cfg.get("skills", [])[:6]))
    css = shared_style() + f""".portrait-ascii{{font:700 {font_size}px ui-monospace,Consolas,monospace;fill:__MINT__}}.ascii{{font:700 11px ui-monospace,Consolas,monospace;fill:__MINT__;letter-spacing:.4px}}.chip{{font:700 8px 'Trebuchet MS',sans-serif;fill:__TEXT__}}.phase-a{{animation:phaseA 3.4s cubic-bezier(.32,.72,0,1) infinite}}.phase-b{{animation:phaseB 3.4s cubic-bezier(.32,.72,0,1) infinite}}@keyframes phaseA{{0%,42%{{opacity:1}}58%,92%{{opacity:0}}100%{{opacity:1}}}}@keyframes phaseB{{0%,42%{{opacity:0}}58%,92%{{opacity:1}}100%{{opacity:0}}}}""".replace("__MINT__", MINT).replace("__TEXT__", TEXT)
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="900" height="380" viewBox="0 0 900 380" role="img" aria-label="Animated ASCII identity for {escape(cfg['name'])}">
<defs><linearGradient id="shell" x1="0" y1="0" x2="1" y2="1"><stop stop-color="#0b5e58"/><stop offset=".56" stop-color="#0c3438"/><stop offset="1" stop-color="#284e88"/></linearGradient><radialGradient id="aura"><stop stop-color="{TEAL}" stop-opacity=".22"/><stop offset="1" stop-color="{TEAL}" stop-opacity="0"/></radialGradient>{''.join(portrait_defs)}<clipPath id="type"><rect x="0" y="0" width="0" height="225"><animate attributeName="width" from="0" to="520" dur="2.5s" calcMode="spline" keySplines=".32 .72 0 1" fill="freeze"/></rect></clipPath><style>{css}</style></defs>
<rect width="900" height="380" rx="24" fill="{OUTER}"/><rect x="6" y="6" width="888" height="368" rx="20" fill="url(#shell)" stroke="{HAIR}"/><rect x="18" y="18" width="864" height="344" rx="17" fill="{BG}" stroke="#1a7269"/><circle cx="230" cy="185" r="180" fill="url(#aura)"/>
<circle cx="38" cy="37" r="5" fill="#ff665d"/><circle cx="56" cy="37" r="5" fill="#f5c451"/><circle cx="74" cy="37" r="5" fill="#46d468"/><text x="450" y="41" text-anchor="middle" class="mono">{escape(cfg['username'].lower())}@github: ~$ ./wordmark --animate</text>
<rect x="32" y="57" width="286" height="292" rx="22" fill="#081d1f" stroke="#176f68"/><text x="48" y="78" class="label">PORTRAIT.ASCII / @{escape(cfg['username'].upper())}</text><g class="portrait-ascii">{''.join(portrait_body)}</g>
<rect x="329" y="57" width="539" height="222" rx="22" fill="#081d1f" stroke="#176f68"/><g transform="translate(343 67)" clip-path="url(#type)" class="ascii"><g class="phase-a">{line_a}</g><g class="phase-b">{line_b}</g></g>
<text x="337" y="305" class="body">{escape(trim(cfg['role'], 58))} · {escape(cfg['location'])}</text>{skills}
<rect x="342" y="65" width="6" height="15" fill="{MINT}" opacity="0"><set attributeName="opacity" to="1" begin="0s"/><animate attributeName="x" from="342" to="852" dur="2.5s" calcMode="spline" keySplines=".32 .72 0 1" fill="freeze"/><set attributeName="opacity" to="0" begin="2.5s"/></rect>
</svg>'''


def calendar_layout(days: list[dict]) -> tuple[list[tuple[dict, int, int]], int]:
    if not days:
        return [], 53
    parsed = [(date.fromisoformat(item["date"]), item) for item in days]
    parsed.sort(key=lambda item: item[0])
    origin = parsed[0][0] - timedelta(days=(parsed[0][0].weekday() + 1) % 7)
    placed = []
    for current, item in parsed:
        col = (current - origin).days // 7
        row = (current.weekday() + 1) % 7
        placed.append((item, col, row))
    return placed, max(col for _, col, _ in placed) + 1


def contributions_svg(cfg: dict, contribution: dict) -> str:
    placed, weeks = calendar_layout(contribution["days"][-371:])
    cell, gap = 10, 3
    pitch = cell + gap
    grid_width = weeks * pitch - gap
    grid_x = (900 - grid_width) // 2
    colors = ["#102f30", "#15504c", "#167b70", "#1aae9b", TEAL]
    nodes = []
    for index, (item, col, row) in enumerate(placed):
        level = min(4, int(item.get("level", 0)))
        delay = ((col + row) % 18) * 0.025
        nodes.append(f'<rect x="{grid_x + col * pitch}" y="{91 + row * pitch}" width="{cell}" height="{cell}" rx="2" fill="{colors[level]}" class="cell" style="animation-delay:{delay:.3f}s"><title>{escape(item["date"])}: {item.get("count", 0)} contributions</title></rect>')
    css = shared_style() + """.cell{animation:cellIn .55s cubic-bezier(.32,.72,0,1) both}.ship{animation:travel 12s cubic-bezier(.65,0,.35,1) infinite}.shot-a{animation:shoot 1.7s cubic-bezier(.32,.72,0,1) infinite}.shot-b{animation:shoot 1.7s .72s cubic-bezier(.32,.72,0,1) infinite}@keyframes cellIn{from{opacity:0;transform:translateY(5px)}to{opacity:1;transform:translateY(0)}}@keyframes travel{0%,100%{transform:translateX(0)}50%{transform:translateX(715px)}}@keyframes shoot{0%{opacity:0;transform:translateY(0) scaleY(.4)}18%{opacity:1}75%,100%{opacity:0;transform:translateY(-58px) scaleY(1)}}"""
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="900" height="292" viewBox="0 0 900 292" role="img" aria-label="Contribution activity for {escape(cfg['username'])}">
<defs><linearGradient id="shell" x1="0" y1="0" x2="1" y2="1"><stop stop-color="#0b655d"/><stop offset=".58" stop-color="#0c3a3c"/><stop offset="1" stop-color="#2e518c"/></linearGradient><style>{css}</style></defs>
<rect width="900" height="292" rx="24" fill="{OUTER}"/><rect x="6" y="6" width="888" height="280" rx="20" fill="url(#shell)" stroke="{HAIR}"/><rect x="28" y="28" width="844" height="236" rx="18" fill="{PANEL}" stroke="#24a596"/>
<text x="48" y="60" class="title">Contribution Activity</text><text x="49" y="79" class="label">{contribution['total']} CONTRIBUTIONS IN THE LAST YEAR</text><text x="712" y="62" class="mono">LESS</text>{''.join(f'<rect x="{750 + i * 14}" y="52" width="10" height="10" rx="2" fill="{color}"/>' for i, color in enumerate(colors))}<text x="847" y="62" text-anchor="end" class="mono">MORE</text>
{''.join(nodes)}
<path d="M65 235H835" stroke="#174541" stroke-dasharray="2 7"/>
<g class="ship"><g transform="translate(72 240)"><g class="shot-a"><rect x="12" y="-21" width="3" height="14" rx="2" fill="{MINT}"/><circle cx="13.5" cy="-24" r="3" fill="{MINT}"/></g><g class="shot-b"><rect x="12" y="-21" width="3" height="14" rx="2" fill="{BLUE}"/><circle cx="13.5" cy="-24" r="3" fill="{BLUE}"/></g><path d="M13 0L25 27l-12-6-12 6z" fill="{MINT}" stroke="#d9fff8"/><path d="M13 9L18 23H8z" fill="{BLUE}"/><path d="M5 24l-4 9 9-6M21 24l4 9-9-6" fill="none" stroke="{TEAL}" stroke-width="2"/><path d="M9 29l4 10 4-10" fill="{ORANGE}" opacity=".85"/></g></g>
<text x="847" y="252" text-anchor="end" class="label">ORBITAL COMMIT SCAN / LIVE</text>
</svg>'''


def signal_svg(cfg: dict, profile: dict, contribution: dict) -> str:
    metrics = [("STARS", profile["stars"], TEAL), ("CONTRIBUTIONS", contribution["total"], PURPLE), ("REPOSITORIES", profile["public_repos"], BLUE), ("FOLLOWERS", profile["followers"], "#32d8ef")]
    max_metric = max(1, max(value for _, value, _ in metrics))
    cards = []
    for index, (label, value, color) in enumerate(metrics):
        x = 42 + index * 211
        progress = max(18, int(132 * (value / max_metric) ** 0.5))
        cards.append(f'<g transform="translate({x} 83)"><rect width="190" height="112" rx="18" fill="{PANEL_2}" stroke="#1aa595"/><text x="22" y="30" class="label">{label}</text><text x="22" y="70" class="metric" fill="{color}"><tspan fill="{color}">{value}</tspan></text><rect x="22" y="88" width="144" height="7" rx="4" fill="#203b40"/><rect x="22" y="88" width="{progress}" height="7" rx="4" fill="{color}" class="bar" style="animation-delay:{index * .1:.2f}s"/></g>')
    languages = profile.get("languages") or [(skill, 1) for skill in cfg.get("skills", [])[:5]]
    total = max(1, sum(int(count) for _, count in languages))
    language_nodes = []
    palette = [YELLOW, BLUE, PURPLE, GREEN, ORANGE]
    for index, (language, count) in enumerate(languages[:5]):
        y = 362 + index * 29
        percent = round(int(count) / total * 100)
        width = max(16, int(460 * int(count) / total))
        color = palette[index]
        language_nodes.append(f'<circle cx="62" cy="{y - 4}" r="5" fill="{color}"/><text x="82" y="{y}" class="language">{escape(language)}</text><text x="285" y="{y}" text-anchor="end" class="percent" fill="{color}"><tspan fill="{color}">{percent}%</tspan></text><rect x="315" y="{y - 12}" width="510" height="9" rx="5" fill="#224043"/><rect x="315" y="{y - 12}" width="{width}" height="9" rx="5" fill="{color}" class="bar" style="animation-delay:{.15 + index * .08:.2f}s"/>')
    css = shared_style() + """.metric{font:700 34px 'Trebuchet MS',sans-serif}.language{font:700 12px 'Trebuchet MS',sans-serif;fill:__TEXT__}.percent{font:700 11px ui-monospace,Consolas,monospace}.bar{transform-origin:left;animation:grow .85s cubic-bezier(.32,.72,0,1) both}@keyframes grow{from{transform:scaleX(0)}to{transform:scaleX(1)}}""".replace("__TEXT__", TEXT)
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="900" height="520" viewBox="0 0 900 520" role="img" aria-label="Profile signal and language stack for {escape(cfg['username'])}">
<defs><linearGradient id="shell" x1="0" y1="0" x2="1" y2="1"><stop stop-color="#0b625b"/><stop offset=".55" stop-color="#0c3b3d"/><stop offset="1" stop-color="#2d4f88"/></linearGradient><style>{css}</style></defs>
<rect width="900" height="520" rx="24" fill="{OUTER}"/><rect x="6" y="6" width="888" height="238" rx="20" fill="url(#shell)" stroke="{HAIR}"/><rect x="24" y="24" width="852" height="202" rx="18" fill="{PANEL}" stroke="#1ca596"/><text x="42" y="61" class="title">Profile Signal</text><text x="43" y="78" class="label">LIVE GITHUB STATS / @{escape(cfg['username'].upper())}</text>{''.join(cards)}
<rect x="6" y="258" width="888" height="256" rx="20" fill="url(#shell)" stroke="{HAIR}"/><rect x="24" y="276" width="852" height="220" rx="18" fill="{PANEL}" stroke="#1ca596"/><text x="43" y="312" class="title">Language Stack</text><text x="43" y="330" class="label">REPOSITORY-WEIGHTED TECHNOLOGIES</text><text x="849" y="312" text-anchor="end" class="label">&gt; STACK.SCAN</text>{''.join(language_nodes)}
<text x="849" y="509" text-anchor="end" class="mono">{escape(trim(cfg['status'], 62))}</text>
</svg>'''


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--demo", action="store_true", help="use deterministic offline data")
    args = parser.parse_args()
    cfg = load_config()
    username = os.environ.get("GH_USERNAME") or os.environ.get("GITHUB_REPOSITORY_OWNER") or cfg["username"]
    cfg["username"] = username
    if args.demo:
        profile, contribution = demo_data()
    else:
        try:
            profile = profile_data(username)
            contribution = contributions_graphql(username) or contributions_html(username)
        except (urllib.error.URLError, RuntimeError) as exc:
            raise SystemExit(f"GitHub data request failed: {exc}. Use --demo for an offline preview.")
    ASSETS.mkdir(exist_ok=True)
    (ASSETS / "identity.svg").write_text(identity_svg(cfg), encoding="utf-8")
    (ASSETS / "contributions.svg").write_text(contributions_svg(cfg, contribution), encoding="utf-8")
    (ASSETS / "signal.svg").write_text(signal_svg(cfg, profile, contribution), encoding="utf-8")
    print(f"Generated Aqua Launch assets for @{username}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
