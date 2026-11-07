#!/usr/bin/env python3
"""Regenerate the profile tiles (assets/*.svg) and README.md from live GitHub data.

Needs the `gh` CLI authenticated (locally, or GH_TOKEN in CI). Python standard library only.
Run from the repo root: python3 scripts/build.py (regenerate by hand; there is no automation).
Fails loudly if any fetch fails, so a broken run never overwrites good tiles.
"""
import datetime
import html
import json
import os
import re
import subprocess

LOGIN = "NVJKKartik"
ORG = "future-agi"
SCHOLAR = "https://scholar.google.com/citations?user=tc23KVoAAAAJ"
ARXIV = "https://arxiv.org/abs/2509.14647"
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASSETS = os.path.join(ROOT, "assets")


def gh(*args):
    out = subprocess.run(["gh", "api", *args], capture_output=True, text=True, check=True).stdout
    return json.loads(out)


def esc(s):
    return html.escape(s, quote=False)


# ---------------------------------------------------------------- live data
def fetch():
    repos = gh("-X", "GET", f"orgs/{ORG}/repos", "-f", "type=public", "-f", "per_page=100")
    stars = sum(r["stargazers_count"] for r in repos if not r["fork"])
    merged = gh("-X", "GET", "search/issues", "-f", f"q=author:{LOGIN} is:pr is:merged org:{ORG} is:public",
                "-f", "per_page=30")
    items = sorted(merged["items"], key=lambda i: i["closed_at"], reverse=True)[:3]
    prs = [{
        "repo": i["repository_url"].rsplit("/", 1)[1],
        "num": i["number"],
        "title": clean_title(i["title"]),
        "url": i["html_url"],
        "date": datetime.datetime.fromisoformat(i["closed_at"].replace("Z", "+00:00")),
    } for i in items]
    cal = gh("graphql", "-f", "query=" + (
        '{user(login:"%s"){contributionsCollection{contributionCalendar{totalContributions '
        'weeks{contributionDays{contributionCount date}}}}}}' % LOGIN)
    )["data"]["user"]["contributionsCollection"]["contributionCalendar"]
    return {"stars": stars, "merged_total": merged["total_count"], "prs": prs, "cal": cal}


def clean_title(t):
    """Drop internal ticket ids like (TH-8895) or 'TH-8993' from a PR title."""
    t = re.sub(r"\s*\((?:TH-\d+(?:,\s*)?)+\)", "", t)
    t = re.sub(r"\bTH-\d+\s*", "", t)
    return re.sub(r"\s{2,}", " ", t).strip()


def short(n):
    return f"{n / 1000:.1f}k".replace(".0k", "k") if n >= 1000 else str(n)


# ---------------------------------------------------------------- brand kit (locked tokens)
KIT = {
    "dark": dict(bg0="#0b0f19", bg1="#131a2b", tile="#0f1523", line="#1f2937", text="#f9fafb", sub="#d1d5db",
                 dim="#9ca3af", acc="#a78bfa", accd="#7c3aed", glow="0.38", dot="#1f2937", bar="#1f2937",
                 chip="#111827", empty="#161d2e"),
    "light": dict(bg0="#ffffff", bg1="#f5f3ff", tile="#ffffff", line="#e5e7eb", text="#111827", sub="#374151",
                  dim="#6b7280", acc="#7c3aed", accd="#7c3aed", glow="0.16", dot="#e5e7eb", bar="#e5e7eb",
                  chip="#ffffff", empty="#eef0f4"),
}
SANS = 'Inter,-apple-system,"Segoe UI",Helvetica,Arial,sans-serif'
MONO = 'ui-monospace,SFMono-Regular,Menlo,Consolas,"Liberation Mono",monospace'


def svg(w, h, title, desc, body, defs=""):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" '
            f'role="img" aria-labelledby="t d"><title id="t">{esc(title)}</title><desc id="d">{esc(desc)}</desc>'
            f'<style>.s{{font-family:{SANS}}}.m{{font-family:{MONO}}}</style><defs>{defs}</defs>{body}</svg>')


def tilebase(w, h, c, r=16):
    return f'<rect x="1" y="1" width="{w-2}" height="{h-2}" rx="{r}" fill="{c["tile"]}" stroke="{c["line"]}" stroke-width="2"/>'


def grow(final, delay, dur=2.4):
    d = delay / dur
    return (f'<animate attributeName="width" values="0;0;{final}" keyTimes="0;{d:.3f};{min(d+0.3,1):.3f}" '
            f'dur="{dur}s" begin="0s" fill="freeze" calcMode="spline" keySplines="0 0 1 1;0.2 0.8 0.2 1"/>')


# ---------------------------------------------------------------- templates
def hero(c, data):
    W, H = 840, 300
    defs = (f'<linearGradient id="bg" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="{c["bg0"]}"/>'
            f'<stop offset="1" stop-color="{c["bg1"]}"/></linearGradient>'
            f'<radialGradient id="gl" cx="0.82" cy="0.18" r="0.7"><stop offset="0" stop-color="{c["accd"]}" '
            f'stop-opacity="{c["glow"]}"/><stop offset="1" stop-color="{c["accd"]}" stop-opacity="0"/></radialGradient>'
            f'<pattern id="dots" width="22" height="22" patternUnits="userSpaceOnUse"><circle cx="2" cy="2" r="1.2" '
            f'fill="{c["dot"]}"/></pattern>'
            '<filter id="blur" x="-50%" y="-200%" width="200%" height="500%"><feGaussianBlur stdDeviation="7"/></filter>')
    b = [f'<rect x="1" y="1" width="{W-2}" height="{H-2}" rx="18" fill="url(#bg)" stroke="{c["line"]}" stroke-width="2"/>',
         f'<rect x="1" y="1" width="{W-2}" height="{H-2}" rx="18" fill="url(#dots)" opacity="0.55"/>',
         f'<rect x="1" y="1" width="{W-2}" height="{H-2}" rx="18" fill="url(#gl)"/>',
         f'<text class="m" x="48" y="66" font-size="13" letter-spacing="2.4" font-weight="600" fill="{c["acc"]}">FOUNDING ENGINEER  ·  FUTURE AGI</text>',
         f'<text class="s" x="46" y="136" font-size="64" font-weight="700" letter-spacing="-2.4" fill="{c["text"]}">Kartik N V J K</text>',
         f'<text class="s" x="48" y="178" font-size="21" fill="{c["sub"]}">Tracing, evals and a gateway that find why AI</text>',
         f'<text class="s" x="48" y="206" font-size="21" fill="{c["sub"]}">agents fail, and the loop that fixes them.</text>']
    x = 48
    for label, w in (("US patent", 108), ("AgentCompass", 144), ("Open source", 132)):
        b.append(f'<rect x="{x}" y="238" width="{w}" height="34" rx="17" fill="{c["chip"]}" stroke="{c["line"]}" stroke-width="1.5"/>')
        b.append(f'<text class="s" x="{x+w/2}" y="260" font-size="14" font-weight="600" text-anchor="middle" fill="{c["sub"]}">{label}</text>')
        x += w + 12
    rows = [(540, 252), (560, 170), (588, 120), (612, 156), (672, 96), (700, 72)]
    for i in range(5):
        b.append(f'<line x1="{540+i*63}" y1="74" x2="{540+i*63}" y2="250" stroke="{c["line"]}" stroke-width="1" opacity="0.8"/>')
    for k, (x0, w) in enumerate(rows):
        y = 82 + k * 29
        acc = k == 3
        if acc:
            b.append(f'<rect x="{x0}" y="{y}" width="{w}" height="16" rx="5" fill="{c["acc"]}" opacity="0.55" filter="url(#blur)">{grow(w, 0.5+0.15*k)}</rect>')
        b.append(f'<rect x="{x0}" y="{y}" width="{w}" height="16" rx="5" fill="{c["acc"] if acc else c["bar"]}">{grow(w, 0.5+0.15*k)}</rect>')
    b.append(f'<text class="m" x="540" y="68" font-size="11" letter-spacing="1.6" fill="{c["dim"]}">AGENT TRACE</text>')
    return svg(W, H, "Kartik N V J K, founding engineer at Future AGI",
               "Tracing, evals and a gateway that find why AI agents fail, and the loop that fixes them. US patent, AgentCompass, open source.",
               "".join(b), defs)


def stat(num, label, sub):
    def f(c, data):
        W, H = 266, 150
        b = [tilebase(W, H, c), f'<rect x="24" y="22" width="28" height="4" rx="2" fill="{c["acc"]}"/>',
             f'<text class="s" x="22" y="84" font-size="56" font-weight="700" letter-spacing="-2" fill="{c["text"]}">{esc(num(data) if callable(num) else num)}</text>',
             f'<text class="s" x="24" y="112" font-size="18" font-weight="600" fill="{c["sub"]}">{esc(label)}</text>',
             f'<text class="m" x="24" y="134" font-size="12" fill="{c["dim"]}">{esc(sub)}</text>']
        shown = num(data) if callable(num) else num
        return svg(W, H, f"{shown} {label}", f"{shown} {label}. {sub}", "".join(b))
    return f


def card(name, tag, l1, l2, flag=False):
    def f(c, data):
        W, H = 410, 124
        b = [tilebase(W, H, c), f'<rect x="1" y="26" width="4" height="72" rx="2" fill="{c["acc"] if flag else c["bar"]}"/>',
             f'<text class="m" x="26" y="32" font-size="11" letter-spacing="1.8" font-weight="600" fill="{c["acc"]}">{esc(tag)}</text>',
             f'<text class="m" x="26" y="62" font-size="23" font-weight="700" fill="{c["text"]}">{esc(name)}</text>',
             f'<text class="s" x="26" y="88" font-size="15" fill="{c["sub"]}">{esc(l1)}</text>',
             f'<text class="s" x="26" y="108" font-size="15" fill="{c["sub"]}">{esc(l2)}</text>',
             f'<text class="s" x="{W-38}" y="40" font-size="22" fill="{c["dim"]}">↗</text>']
        return svg(W, H, name, f"{name}. {l1} {l2}", "".join(b))
    return f


def paper(kind, lines, venue):
    def f(c, data):
        W, H = 410, 196
        b = [tilebase(W, H, c), f'<rect x="1" y="28" width="4" height="140" rx="2" fill="{c["acc"]}"/>',
             f'<text class="m" x="26" y="38" font-size="12" letter-spacing="1.8" font-weight="600" fill="{c["acc"]}">{esc(kind)}</text>']
        for i, l in enumerate(lines):
            b.append(f'<text class="s" x="26" y="{76+i*29}" font-size="22" font-weight="700" letter-spacing="-0.3" fill="{c["text"]}">{esc(l)}</text>')
        b.append(f'<text class="m" x="26" y="{H-26}" font-size="13" fill="{c["dim"]}">{esc(venue)}</text>')
        return svg(W, H, " ".join(lines), f'{kind}. {" ".join(lines)} {venue}', "".join(b))
    return f


def ship(i):
    """One merged-PR row; i = 0..2 into data['prs']."""
    def f(c, data):
        W, H = 840, 76
        p = data["prs"][i]
        title = p["title"] if len(p["title"]) <= 74 else p["title"][:73].rstrip() + "…"
        day = f'{p["date"].day} {p["date"].strftime("%b")}'
        b = [tilebase(W, H, c, 14), f'<rect x="1" y="16" width="4" height="44" rx="2" fill="{c["acc"]}"/>',
             f'<text class="m" x="26" y="30" font-size="12" letter-spacing="0.4" fill="{c["acc"]}">{esc(p["repo"])} #{p["num"]}</text>',
             f'<text class="s" x="26" y="56" font-size="19" font-weight="600" fill="{c["text"]}">{esc(title)}</text>',
             f'<text class="m" x="{W-28}" y="30" font-size="12" text-anchor="end" fill="{c["dim"]}">MERGED {day.upper()}</text>',
             f'<text class="s" x="{W-28}" y="56" font-size="20" text-anchor="end" fill="{c["dim"]}">↗</text>']
        return svg(W, H, f'{p["repo"]} #{p["num"]}: {p["title"]}', f'Merged {day}. {p["title"]}', "".join(b))
    return f


def heatmap(c, data):
    cal = data["cal"]
    weeks = cal["weeks"]
    W, H = 840, 196
    cell, gap, x0, y0 = 11, 3, 28, 62
    counts = sorted(d["contributionCount"] for w in weeks for d in w["contributionDays"] if d["contributionCount"])
    q = [counts[int(len(counts) * p)] for p in (0.25, 0.5, 0.75)] if counts else [1, 2, 3]

    def level(n):
        return 0 if n == 0 else 1 if n <= q[0] else 2 if n <= q[1] else 3 if n <= q[2] else 4
    op = [None, 0.28, 0.5, 0.75, 1.0]
    b = [tilebase(W, H, c),
         f'<text class="s" x="28" y="36" font-size="18" font-weight="700" fill="{c["text"]}">{cal["totalContributions"]:,} contributions</text>',
         f'<text class="m" x="{W-28}" y="36" font-size="12" text-anchor="end" fill="{c["dim"]}">LAST 12 MONTHS</text>']
    last_month = None
    for wi, w in enumerate(weeks):
        x = x0 + wi * (cell + gap)
        month = w["contributionDays"][0]["date"][5:7]
        if month != last_month and wi < len(weeks) - 3:
            b.append(f'<text class="m" x="{x}" y="54" font-size="10" fill="{c["dim"]}">{datetime.date(2000, int(month), 1).strftime("%b").upper()}</text>')
        last_month = month
        for di, d in enumerate(w["contributionDays"]):
            lv = level(d["contributionCount"])
            y = y0 + di * (cell + gap)
            if lv == 0:
                b.append(f'<rect x="{x}" y="{y}" width="{cell}" height="{cell}" rx="2.5" fill="{c["empty"]}"/>')
            else:
                b.append(f'<rect x="{x}" y="{y}" width="{cell}" height="{cell}" rx="2.5" fill="{c["acc"]}" opacity="{op[lv]}"/>')
    lx = W - 28 - 5 * (cell + gap) - 70
    b.append(f'<text class="m" x="{lx}" y="{H-14}" font-size="10" text-anchor="end" fill="{c["dim"]}">LESS</text>')
    for k in range(5):
        fill = c["empty"] if k == 0 else c["acc"]
        o = "" if k == 0 else f' opacity="{op[k]}"'
        b.append(f'<rect x="{lx+8+k*(cell+gap)}" y="{H-23}" width="{cell}" height="{cell}" rx="2.5" fill="{fill}"{o}/>')
    b.append(f'<text class="m" x="{lx+8+5*(cell+gap)+6}" y="{H-14}" font-size="10" fill="{c["dim"]}">MORE</text>')
    return svg(W, H, f'{cal["totalContributions"]:,} contributions in the last 12 months',
               f'Contribution heatmap for {LOGIN}: {cal["totalContributions"]:,} contributions over the last 12 months.',
               "".join(b))


TILES = {
    "hero": hero,
    "stat-stars": stat(lambda d: short(d["stars"]), "stars", f"across {ORG} public repos"),
    "stat-prs": stat(lambda d: str(d["merged_total"]), "merged PRs", f"to {ORG} public repos"),
    "stat-papers": stat("6", "papers & patents", "Google Scholar"),
    "ship-0": ship(0), "ship-1": ship(1), "ship-2": ship(2),
    "heatmap": heatmap,
    "p-future-agi": card("future-agi", "PLATFORM", "Tracing, evals, simulations, gateway", "and guardrails. Self-hostable.", True),
    "p-traceai": card("traceAI", "TRACING", "OpenTelemetry tracing for AI apps", "and frameworks.", True),
    "p-alk": card("agent-learning-kit", "EVALS · SIMULATION", "Evaluation and simulation environment", "for AI workflows."),
    "p-opt": card("agent-opt", "OPTIMIZATION", "Automated optimization of AI agent", "workflows."),
    "p-sim": card("simulate-sdk", "VOICE · TESTING", "Voice AI simulation SDK for testing", "agents."),
    "p-sdk": card("futureagi-sdk", "SDK", "Evals, prompts and observability for", "Python and TypeScript."),
    "paper-patent": paper("2026 · US PATENT", ["Synthetic data generation", "system and method"], "US Patent 12,608,610"),
    "paper-compass": paper("2025 · ARXIV", ["AgentCompass: Towards Reliable", "Evaluation of Agentic Workflows", "in Production"], "arXiv:2509.14647"),
}


# ---------------------------------------------------------------- README
def pic(name, alt, w, href=None):
    p = (f'<picture><source media="(prefers-color-scheme: dark)" srcset="assets/{name}-dark.svg">'
         f'<img src="assets/{name}-light.svg" alt="{esc(alt)}" width="{w}"></picture>')
    return f'<a href="{href}">{p}</a>' if href else p


def readme(d):
    L = f"https://github.com/{ORG}/"
    o = [f'<p align="center">{pic("hero", "Kartik N V J K, founding engineer at Future AGI. Tracing, evals and a gateway that find why AI agents fail, and the loop that fixes them.", "100%")}</p>',
         '<p align="center">\n'
         '  <a href="https://www.linkedin.com/in/n-v-j-k-kartik-95283823b/">LinkedIn</a> &nbsp;·&nbsp;\n'
         f'  <a href="{SCHOLAR}">Google Scholar</a> &nbsp;·&nbsp;\n'
         '  <a href="https://dev.to/kartik-nvjk">DEV</a> &nbsp;·&nbsp;\n'
         f'  <a href="{ARXIV}">arXiv</a> &nbsp;·&nbsp;\n'
         '  <a href="https://futureagi.com">Future AGI</a>\n</p>',
         '<p align="center">' + " ".join([
             pic("stat-stars", f'{short(d["stars"])} stars across {ORG} public repos', "32%", L.rstrip("/")),
             pic("stat-prs", f'{d["merged_total"]} merged pull requests to {ORG} public repos', "32%",
                 f'https://github.com/pulls?q=is%3Apr+is%3Amerged+author%3A{LOGIN}+org%3A{ORG}+is%3Apublic'),
             pic("stat-papers", "6 papers and patents on Google Scholar", "32%", SCHOLAR)]) + "</p>",
         "## Recently merged"]
    for i, p in enumerate(d["prs"]):
        o.append(f'<p align="center">{pic(f"ship-{i}", f"{p["repo"]} #{p["num"]}: {p["title"]}", "100%", p["url"])}</p>')
    o.append("## Activity")
    o.append(f'<p align="center">{pic("heatmap", f"{d["cal"]["totalContributions"]:,} contributions in the last 12 months", "100%")}</p>')
    o.append("## Open source")
    cards = [("p-future-agi", "future-agi"), ("p-traceai", "traceAI"), ("p-alk", "agent-learning-kit"),
             ("p-opt", "agent-opt"), ("p-sim", "simulate-sdk"), ("p-sdk", "futureagi-sdk")]
    for i in range(0, 6, 2):
        o.append('<p align="center">' + " ".join(pic(n, f"{r} on GitHub", "49%", L + r) for n, r in cards[i:i+2]) + "</p>")
    o.append("## Papers and patents")
    o.append('<p align="center">' + " ".join([
        pic("paper-patent", "2026 US Patent 12,608,610: Synthetic data generation system and method", "49%"),
        pic("paper-compass", "2025 arXiv 2509.14647: AgentCompass: Towards Reliable Evaluation of Agentic Workflows in Production", "49%", ARXIV)]) + "</p>")
    o.append(f'''<details>
<summary>4 earlier papers (education and applied ML)</summary>

| Year | Title | Venue |
| --- | --- | --- |
| 2025 | Exploring Emotional Trajectories through Valence and Arousal in Open-Ended Math Learning Environments | APSCE |
| 2025 | Energy-Efficient Depthwise Separable CNNs for Classification and Segmentation of Lung Cancer Nodules | IEEE INDISCON |
| 2024 | Advancing Speaker Diarization With Whisper Speech Recognition for Different Learning Environments | IEEE T4E / TALE |
| 2024 | Unlocking the Triggers: Automating the Identification of Triggers of Socially Shared Metacognitive Regulation in Collaborative Problem-Solving | T4E |

</details>

<sub>[All papers on Google Scholar]({SCHOLAR}) · IIIT Dharwad</sub>''')
    o.append("## Writing")
    o.append("[My agent had great traces and still never got better. Here is the loop I built.]"
             "(https://dev.to/kartik-nvjk/my-agent-had-great-traces-and-still-never-got-better-here-is-the-loop-i-built-15o9)")
    o.append("`Python` `Go` `TypeScript` `Java` `C#` `Django` `React` `PostgreSQL` `ClickHouse` `Redis` `Temporal` `OpenTelemetry` `Docker` `Kubernetes` `GCP`")
    return "\n\n".join(o) + "\n"


def main():
    data = fetch()
    os.makedirs(ASSETS, exist_ok=True)
    for f in os.listdir(ASSETS):
        os.remove(os.path.join(ASSETS, f))
    for name, fn in TILES.items():
        for theme, c in KIT.items():
            with open(os.path.join(ASSETS, f"{name}-{theme}.svg"), "w") as fh:
                fh.write(fn(c, data))
    with open(os.path.join(ROOT, "README.md"), "w") as fh:
        fh.write(readme(data))
    print(f'stars={data["stars"]} merged={data["merged_total"]} contributions={data["cal"]["totalContributions"]}')
    for p in data["prs"]:
        print(f'  {p["repo"]} #{p["num"]}: {p["title"]}')


if __name__ == "__main__":
    main()
