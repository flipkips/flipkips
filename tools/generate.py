"""Build the languages chart for the profile README from local git repositories (no network).

Usage: python tools/generate.py repos.txt
repos.txt lists local repository paths, one per line (kept out of git).
"""
import collections
import json
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASSETS = os.path.join(ROOT, "assets")

LANGS = {
    ".ts": "TypeScript", ".tsx": "TypeScript", ".mts": "TypeScript", ".cts": "TypeScript",
    ".js": "JavaScript", ".jsx": "JavaScript", ".mjs": "JavaScript", ".cjs": "JavaScript",
    ".vue": "Vue", ".svelte": "Svelte", ".py": "Python", ".cs": "C#", ".cshtml": "C#", ".razor": "C#",
    ".cpp": "C++", ".cc": "C++", ".cxx": "C++", ".hpp": "C++", ".h": "C++", ".c": "C",
    ".go": "Go", ".php": "PHP", ".rb": "Ruby", ".java": "Java", ".kt": "Kotlin", ".rs": "Rust",
    ".swift": "Swift", ".dart": "Dart", ".lua": "Lua", ".html": "HTML", ".htm": "HTML",
    ".css": "CSS", ".scss": "SCSS", ".sass": "SCSS", ".less": "Less", ".sql": "SQL",
    ".sh": "Shell", ".bash": "Shell", ".ps1": "PowerShell", ".bat": "Batchfile", ".cmd": "Batchfile",
    ".twig": "Twig",
}
COLORS = {
    "TypeScript": "#3178c6", "JavaScript": "#f1e05a", "Vue": "#41b883", "Svelte": "#ff3e00",
    "Python": "#3572a5", "C#": "#178600", "C++": "#f34b7d", "C": "#555555", "Go": "#00add8",
    "PHP": "#4f5d95", "Ruby": "#701516", "Java": "#b07219", "Kotlin": "#a97bff", "Rust": "#dea584",
    "Swift": "#f05138", "Dart": "#00b4ab", "Lua": "#000080", "HTML": "#e34c26", "CSS": "#663399",
    "SCSS": "#c6538c", "Less": "#1d365d", "SQL": "#e38c00", "Shell": "#89e051", "PowerShell": "#012456",
    "Batchfile": "#c1f12e", "Dockerfile": "#384d54", "Twig": "#c1d026", "Other": "#8b949e",
}
SKIP_DIRS = ("node_modules/", "vendor/", "dist/", "build/", ".next/", ".nuxt/", ".output/", "out/",
             "coverage/", "bin/", "obj/", "third_party/", "wwwroot/lib/", "public/build/", ".venv/", "venv/",
             "__pycache__/", "migrations/")


def git(repo, *args):
    return subprocess.run(["git", "-C", repo, *args], capture_output=True, text=True, encoding="utf-8",
                          errors="replace").stdout


def language_of(path):
    name = os.path.basename(path).lower()
    if name == "dockerfile" or name.startswith("dockerfile."):
        return "Dockerfile"
    if name.endswith((".min.js", ".min.css", ".bundle.js", ".map")):
        return None
    return LANGS.get(os.path.splitext(name)[1])


def scan(repos):
    """Bytes and lines per language across the tracked files of all repositories."""
    lang_bytes, lang_lines = collections.Counter(), collections.Counter()
    for repo in repos:
        for rel in git(repo, "ls-files").splitlines():
            low = "/" + rel.lower()
            if any("/" + d in low for d in SKIP_DIRS):
                continue
            lang = language_of(rel)
            if not lang:
                continue
            full = os.path.join(repo, rel)
            try:
                size = os.path.getsize(full)
                if size > 1_000_000:  # larger files are generated or bundled
                    continue
                with open(full, "rb") as f:
                    data = f.read()
            except OSError:
                continue
            lang_bytes[lang] += size
            lang_lines[lang] += data.count(b"\n") + (0 if data.endswith(b"\n") or not data else 1)
    return lang_bytes, lang_lines


# ---------- SVG ----------

THEMES = {
    "dark": dict(bg="#0d1117", border="#30363d", text="#e6edf3", dim="#8b949e", track="#21262d", add="#3fb950"),
    "light": dict(bg="#ffffff", border="#d0d7de", text="#1f2328", dim="#59636e", track="#eaeef2", add="#1a7f37"),
}
FONT = "font-family:'Segoe UI',Ubuntu,'Helvetica Neue',Arial,sans-serif"


def languages_svg(langs, total_lines, t):
    w, bw = 840, 792
    total = sum(b for _, b, _ in langs)
    x, bar = 24.0, []
    for i, (name, b, _) in enumerate(langs):
        seg = bw * b / total
        bar.append(f'<rect class="g" style="animation-delay:{i * 0.06:.2f}s" x="{x:.1f}" y="58" width="{max(seg, 2):.1f}" '
                   f'height="10" fill="{COLORS.get(name, COLORS["Other"])}"/>')
        x += seg
    legend = []
    cols, row_h = 3, 30
    colw = bw / cols
    for i, (name, b, lines) in enumerate(langs):
        cx = 24 + (i % cols) * colw
        cy = 100 + (i // cols) * row_h
        right = cx + colw - 16
        legend.append(f'<g class="f" style="animation-delay:{0.3 + i * 0.05:.2f}s">'
                      f'<circle cx="{cx + 6}" cy="{cy - 4}" r="6" fill="{COLORS.get(name, COLORS["Other"])}"/>'
                      f'<text x="{cx + 20}" y="{cy}" class="l">{name}</text>'
                      f'<text x="{right - 50:.1f}" y="{cy}" class="a" text-anchor="end">+{lines:,}</text>'
                      f'<text x="{right:.1f}" y="{cy}" class="d" text-anchor="end">{100 * b / total:.1f}%</text></g>')
    h = 100 + ((len(langs) + cols - 1) // cols) * row_h + 4
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}">'
            f'<style>text{{{FONT}}} .t{{font-size:16px;font-weight:600;fill:{t["text"]}}} '
            f'.l{{font-size:13px;fill:{t["text"]}}} .d{{font-size:12px;fill:{t["dim"]}}} '
            f'.a{{font-size:12px;font-weight:600;fill:{t["add"]};font-family:ui-monospace,Consolas,monospace}} '
            f'.g{{animation:grow .9s ease-out both;transform-box:fill-box}} '
            f'@keyframes grow{{from{{transform:scaleX(0)}}to{{transform:scaleX(1)}}}} '
            f'.f{{animation:fade .8s ease-out both}} @keyframes fade{{from{{opacity:0}}to{{opacity:1}}}}</style>'
            f'<rect x="0.5" y="0.5" width="{w - 1}" height="{h - 1}" rx="12" fill="{t["bg"]}" stroke="{t["border"]}"/>'
            f'<text x="24" y="38" class="t">Languages</text>'
            f'<text x="{w - 24}" y="38" text-anchor="end"><tspan class="a" style="font-size:13px">+{total_lines:,}</tspan>'
            f'<tspan class="d"> lines</tspan></text>'
            f'<defs><clipPath id="c"><rect x="24" y="58" width="{bw}" height="10" rx="5"/></clipPath></defs>'
            f'<rect x="24" y="58" width="{bw}" height="10" rx="5" fill="{t["track"]}"/>'
            f'<g clip-path="url(#c)">{"".join(bar)}</g>{"".join(legend)}</svg>')


def main():
    repos = [l.strip() for l in open(sys.argv[1], encoding="utf-8") if l.strip() and not l.startswith("#")]
    lang_bytes, lang_lines = scan(repos)

    ranked = lang_bytes.most_common()
    langs = [(n, b, lang_lines[n]) for n, b in ranked[:8]]
    rest = ranked[8:]
    if rest:
        langs.append(("Other", sum(b for _, b in rest), sum(lang_lines[n] for n, _ in rest)))

    os.makedirs(ASSETS, exist_ok=True)
    for theme, t in THEMES.items():
        with open(os.path.join(ASSETS, f"languages-{theme}.svg"), "w", encoding="utf-8") as f:
            f.write(languages_svg(langs, sum(lang_lines.values()), t))
    total = sum(lang_bytes.values())
    print(json.dumps([(n, f"{100 * b / total:.1f}%", lang_lines[n]) for n, b in ranked], indent=1))


if __name__ == "__main__":
    main()
