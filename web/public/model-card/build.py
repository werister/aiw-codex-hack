"""Render MODEL_CARD.md into web/public/model-card/index.html, the public copy for the site.

Run from anywhere: python web/public/model-card/build.py
The repo is private, so links to repo files become plain text; files under web/public become site links.
"""
import datetime
import html
import pathlib
import re
import subprocess

import markdown

here = pathlib.Path(__file__).resolve().parent
repo = here.parents[2]
src = (repo / "MODEL_CARD.md").read_text(encoding="utf-8")
commit = subprocess.run(["git", "log", "-1", "--format=%h", "--", "MODEL_CARD.md"], cwd=repo,
                        capture_output=True, text=True).stdout.strip() or "unknown"

body = markdown.markdown(src, extensions=["tables", "fenced_code", "sane_lists"], output_format="html")


def fix_link(m):
    href, text = html.unescape(m.group(1)), m.group(2)
    if re.match(r"https?://", href):
        return f'<a href="{html.escape(href)}" target="_blank" rel="noopener noreferrer">{text}</a>'
    if href.startswith("web/public/"):
        return f'<a href="../{html.escape(href[len("web/public/"):])}">{text}</a>'
    return f'<span class="repo-ref" title="In the team repository: {html.escape(href)}">{text}</span>'


body = re.sub(r'<a href="([^"]*)">(.*?)</a>', fix_link, body, flags=re.S)
body = re.sub(r"<table>", '<div class="table-wrap"><table>', body).replace("</table>", "</table></div>")
title = re.search(r"<h1>(.*?)</h1>", body, flags=re.S)
title_text = re.sub(r"<[^>]+>", "", title.group(1)) if title else "Model card"
stamp = datetime.datetime.now().strftime("%d %b %Y, %H:%M")

page = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Lift-off · Model card</title>
<script>
  // Served as /model-card (no slash) the relative paths below would resolve against "/". Pin the base to this folder.
  (function () {{
    var p = location.pathname;
    if (location.protocol !== "file:" && !/\\/$|\\.html?$/.test(p)) document.write('<base href="' + p + '/">');
  }})();
</script>
<style>
  @font-face {{ font-family: "Inter Tight"; src: url("../deck/fonts/inter-tight-latin-wght-normal.woff2") format("woff2"); font-weight: 100 900; font-display: swap; }}
  :root {{ --bg: #ffffff; --panel: #f1f1f8; --line: #dcdcea; --ink: #1d1a78; --ink-2: #3b3990; --muted: #5d5b94; --accent: #3c36da; }}
  * {{ box-sizing: border-box; }}
  html {{ -webkit-text-size-adjust: 100%; }}
  body {{ margin: 0; background: var(--bg); color: var(--ink); font: 17px/1.6 "Inter Tight", system-ui, sans-serif; letter-spacing: 0.005em; font-variant-numeric: tabular-nums; -webkit-font-smoothing: antialiased; }}
  header {{ border-bottom: 1px solid var(--line); }}
  header .in, main, footer {{ max-width: 780px; margin: 0 auto; padding: 0 20px; }}
  header .in {{ display: flex; align-items: center; justify-content: space-between; gap: 16px; padding-top: 16px; padding-bottom: 16px; }}
  header img {{ height: 34px; width: auto; display: block; }}
  header span {{ font-size: 15px; color: var(--muted); }}
  main {{ padding-top: 28px; padding-bottom: 40px; }}
  h1 {{ font-size: 34px; line-height: 1.15; font-weight: 300; letter-spacing: -0.01em; margin: 8px 0 20px; }}
  h2 {{ font-size: 24px; line-height: 1.25; font-weight: 400; margin: 40px 0 12px; padding-top: 24px; border-top: 1px solid var(--line); }}
  h3 {{ font-size: 19px; font-weight: 500; margin: 28px 0 8px; }}
  p, li {{ color: var(--ink); }}
  ul, ol {{ padding-left: 22px; }}
  li {{ margin: 6px 0; }}
  a {{ color: var(--accent); text-underline-offset: 3px; }}
  strong {{ font-weight: 600; }}
  code {{ font: 0.92em/1.4 ui-monospace, SFMono-Regular, Menlo, Consolas, monospace; background: var(--panel); border-radius: 6px; padding: 1px 6px; color: var(--ink-2); overflow-wrap: anywhere; }}
  pre {{ background: var(--panel); border-radius: 10px; padding: 14px 16px; overflow-x: auto; }}
  pre code {{ padding: 0; background: none; }}
  .repo-ref {{ border-bottom: 1px dotted var(--muted); }}
  .table-wrap {{ overflow-x: auto; -webkit-overflow-scrolling: touch; margin: 16px 0; border: 1px solid var(--line); border-radius: 10px; }}
  table {{ border-collapse: collapse; width: 100%; font-size: 15px; }}
  th, td {{ padding: 9px 12px; text-align: left; vertical-align: top; border-bottom: 1px solid var(--line); }}
  th {{ font-weight: 500; color: var(--muted); background: var(--panel); white-space: nowrap; }}
  tr:last-child td {{ border-bottom: 0; }}
  footer {{ padding-top: 18px; padding-bottom: 40px; font-size: 14px; color: var(--muted); border-top: 1px solid var(--line); }}
  @media (max-width: 560px) {{ body {{ font-size: 16px; }} h1 {{ font-size: 28px; }} h2 {{ font-size: 21px; }} }}
</style>
</head>
<body>
<header><div class="in"><img src="../brand/lift-off-logo.png" alt="Lift-off"><span>Model card · Frankfurt Airport</span></div></header>
<main>
{body}
</main>
<footer>Generated from <code>MODEL_CARD.md</code> (commit {commit}) on {stamp}. Forecast data: <a href="../data/quality.json">quality.json</a>.</footer>
</body>
</html>
"""
(here / "index.html").write_text(page, encoding="utf-8", newline="\n")
print("model card:", title_text, "| commit", commit, "|", len(page), "bytes")
