#!/usr/bin/env python3
"""
Optimiert einen Nicepage-Export für GitHub Pages, ohne das Design zu verändern.

Aufruf:  python3 build.py <quellordner> <zielordner>

Schritte:
  1. Kopiert die Website (ohne .git, .github, .DS_Store, Build-Ordner)
  2. Bilder: verkleinert (max. 1920 px) und in WebP umgewandelt, Verweise angepasst
     (in HTML, CSS und den JSON-Dateien des Nicepage-Blogs, z. B. blog/blog.json)
  3. Nicepage-Hinweise: entfernt die Fußzeile „created with …“, das Generator-Tag
     und Links auf nicepage.com (Logo-Links zeigen danach auf die Startseite).
     Nur mit gekaufter Nicepage-Lizenz zulässig.
  4. nicepage.css: entfernt alle Regeln, deren Klassen auf keiner Seite vorkommen
     (Klassen aus HTML, JS und JSON werden berücksichtigt)
  5. Alle CSS-Dateien werden minifiziert
  6. HTML: Lazy Loading für Bilder, Preconnect für Google Fonts,
     nicht blockierendes Laden der Schriften

Benötigt nur Python 3 und Pillow (pip install pillow).
Das Skript ist idempotent: nach jedem neuen Nicepage-Export einfach erneut ausführen.
"""
import os
import re
import shutil
import sys
from pathlib import Path

from PIL import Image, ImageOps

MAX_SIDE = 1920          # längste Bildkante in Pixel
WEBP_QUALITY = 80
RASTER_EXT = {".png", ".jpg", ".jpeg", ".gif"}
SKIP_NAMES = {".git", ".github", ".DS_Store", "_site", "optimize", "node_modules"}
DOWNLOAD_DIR = "files"   # Ordner mit Downloads: Inhalte bleiben unangetastet

# Klassen, die nicepage.js erst zur Laufzeit setzt oder aus Teilstrings zusammenbaut.
# Regeln mit diesen Klassen bleiben immer erhalten.
SAFELIST = re.compile(
    r"^(u-(xs|sm|md|lg|xl|xxl)-mode|u-responsive-.*|u-offcanvas-(un)?shifted-.*|"
    r".*-played|carousel-.*|countdown-.*|timer-.*|waypoint-.*|.*-pagination-.*|"
    r"active|show|open|opened|hover|focus|selected|disabled|collapsed|collapsing|"
    r"in|out|fade|animated|visible|hidden|loaded|loading|expanded|"
    r"u-(active|opened|open|expanded|hidden|visible|animated|dialog-open|"
    r"carousel-item-(next|prev|left|right)))$",
    re.I,
)


# --------------------------------------------------------------------------- #
# Hilfsfunktionen
# --------------------------------------------------------------------------- #
def copy_site(src: Path, dst: Path) -> None:
    if dst.exists():
        shutil.rmtree(dst)

    def ignore(_dir, names):
        return [n for n in names if n in SKIP_NAMES]

    shutil.copytree(src, dst, ignore=ignore)


def text_files(root: Path, *exts):
    for p in root.rglob("*"):
        if p.is_file() and p.suffix.lower() in exts:
            yield p


def in_downloads(site: Path, p: Path) -> bool:
    """True, wenn die Datei im Download-Ordner liegt."""
    return DOWNLOAD_DIR in p.relative_to(site).parts


def site_json_files(site: Path):
    """JSON-Dateien der Website (z. B. blog/blog.json), ohne Downloads."""
    for p in text_files(site, ".json"):
        if not in_downloads(site, p):
            yield p


def fmt(n: int) -> str:
    return f"{n / 1e6:.1f} MB" if n >= 1e6 else f"{n / 1e3:.0f} KB"


# --------------------------------------------------------------------------- #
# 1. Bilder
# --------------------------------------------------------------------------- #
def is_animated(im: Image.Image) -> bool:
    return getattr(im, "is_animated", False) and getattr(im, "n_frames", 1) > 1


def optimize_images(site: Path) -> dict:
    """Wandelt Rasterbilder in WebP um. Gibt {alter_name: neuer_name} zurück.

    Die Verweise werden später nur über den Dateinamen umgeschrieben. Deshalb
    läuft die Umwandlung in zwei Phasen: erst alle Bilder umwandeln, dann pro
    Dateiname prüfen, ob das Ergebnis in allen Ordnern gleich ist. Nur dann
    werden die Originale gelöscht. Bei abweichenden Ergebnissen (gleicher Name
    in mehreren Ordnern, aber nicht überall umgewandelt) bleiben alle Originale
    dieses Namens erhalten, damit kein Verweis ins Leere zeigt.
    """
    # Phase 1: umwandeln, Originale noch nicht löschen
    results = []                                  # (original, webp | None, alt, neu)
    for p in list(site.rglob("*")):
        if not p.is_file() or p.suffix.lower() not in RASTER_EXT:
            continue
        if in_downloads(site, p):                 # Downloads unangetastet lassen
            continue
        size_in = p.stat().st_size
        out = None
        try:
            im = Image.open(p)
            if is_animated(im):
                results.append((p, None, size_in, 0))
                continue
            im = ImageOps.exif_transpose(im)
            im.thumbnail((MAX_SIDE, MAX_SIDE), Image.LANCZOS)
            has_alpha = im.mode in ("RGBA", "LA", "P") and (
                im.mode != "P" or "transparency" in im.info
            )
            im = im.convert("RGBA" if has_alpha else "RGB")
            out = p.with_suffix(".webp")
            if out.exists() and out != p:
                out = p.with_name(p.stem + "-" + p.suffix.lower().lstrip(".") + ".webp")
            im.save(out, "WEBP", quality=WEBP_QUALITY, method=6)
        except Exception as e:  # defekte Datei o. ä.: Original behalten
            print(f"  ! {p.name}: {e}")
            results.append((p, None, size_in, 0))
            continue
        size_out = out.stat().st_size
        if size_out >= size_in:          # WebP bringt nichts -> Original behalten
            out.unlink()
            results.append((p, None, size_in, 0))
            continue
        results.append((p, out, size_in, size_out))

    # Phase 2: pro Dateiname prüfen, ob das Ergebnis überall gleich ist
    outcomes = {}
    for p, out, _, _ in results:
        outcomes.setdefault(p.name, set()).add(out.name if out else None)
    conflicts = {name for name, outs in outcomes.items() if len(outs) > 1}

    renames, before, after = {}, 0, 0
    for p, out, size_in, size_out in results:
        if out is None:
            continue
        if p.name in conflicts:          # Original behalten, WebP verwerfen
            out.unlink()
            continue
        p.unlink()
        renames[p.name] = out.name
        before += size_in
        after += size_out

    print(f"Bilder: {len(renames)} Dateinamen umgewandelt, {fmt(before)} -> {fmt(after)}")
    if conflicts:
        print("  Nicht umgewandelt (gleicher Dateiname in mehreren Ordnern mit "
              "unterschiedlichem Ergebnis): " + ", ".join(sorted(conflicts)))
    return renames


def rewrite_image_refs(site: Path, renames: dict) -> None:
    if not renames:
        return
    names = sorted(renames, key=len, reverse=True)
    pattern = re.compile(r"(?<![\w.-])(" + "|".join(re.escape(n) for n in names) + r")(?![\w.-])")
    # HTML und CSS überall, JSON nur außerhalb des Download-Ordners
    targets = list(text_files(site, ".html", ".css")) + list(site_json_files(site))
    for f in targets:
        s = f.read_text(encoding="utf-8")
        new = pattern.sub(lambda m: renames[m.group(1)], s)
        if new != s:
            f.write_text(new, encoding="utf-8")


# --------------------------------------------------------------------------- #
# 2. CSS: kleiner Parser, Entfernen ungenutzter Regeln, Minifizieren
# --------------------------------------------------------------------------- #
def strip_comments(css: str) -> str:
    out, i, n = [], 0, len(css)
    while i < n:
        c = css[i]
        if c in "\"'":
            j = i + 1
            while j < n and css[j] != c:
                j += 2 if css[j] == "\\" else 1
            out.append(css[i : j + 1])
            i = j + 1
        elif css.startswith("/*", i):
            j = css.find("*/", i + 2)
            i = n if j < 0 else j + 2
        else:
            out.append(c)
            i += 1
    return "".join(out)


def parse_blocks(css: str):
    """Zerlegt CSS in eine Liste aus (prelude, body) bzw. ('@stmt', text).
    body ist bei verschachtelten At-Regeln wieder eine Liste."""
    items, i, n = [], 0, len(css)
    while i < n:
        # Prelude bis '{' oder ';' lesen (Strings/Klammern beachten)
        j, depth = i, 0
        while j < n:
            c = css[j]
            if c in "\"'":
                k = j + 1
                while k < n and css[k] != c:
                    k += 2 if css[k] == "\\" else 1
                j = k + 1
                continue
            if c == "(":
                depth += 1
            elif c == ")":
                depth -= 1
            elif depth == 0 and c in "{;}":
                break
            j += 1
        prelude = css[i:j].strip()
        if j >= n:
            if prelude:
                items.append(("@stmt", prelude))
            break
        if css[j] in ";}":
            if prelude:
                items.append(("@stmt", prelude + ";"))
            i = j + 1
            continue
        # Passende schließende Klammer suchen
        k, depth = j + 1, 1
        while k < n and depth:
            c = css[k]
            if c in "\"'":
                m = k + 1
                while m < n and css[m] != c:
                    m += 2 if css[m] == "\\" else 1
                k = m + 1
                continue
            if c == "{":
                depth += 1
            elif c == "}":
                depth -= 1
            k += 1
        body = css[j + 1 : k - 1]
        low = prelude.lower()
        if low.startswith(("@media", "@supports", "@layer", "@container", "@document")):
            items.append((prelude, parse_blocks(body)))
        else:
            items.append((prelude, body))
        i = k
    return items


CLASS_RE = re.compile(r"\.(-?[_a-zA-Z][\w-]*)")


def selector_used(sel: str, used: set) -> bool:
    # Inhalte von :not(...) etc. ignorieren – sie schränken nur ein
    core = re.sub(r":(not|is|where|has)\([^)]*\)", "", sel)
    core = re.sub(r"\[[^\]]*\]", "", core)  # Attributselektoren nicht auswerten
    for cls in CLASS_RE.findall(core):
        if cls not in used and not SAFELIST.search(cls):
            return False
    return True


def split_selectors(prelude: str):
    parts, depth, cur = [], 0, []
    for c in prelude:
        if c == "(":
            depth += 1
        elif c == ")":
            depth -= 1
        if c == "," and depth == 0:
            parts.append("".join(cur).strip())
            cur = []
        else:
            cur.append(c)
    parts.append("".join(cur).strip())
    return [p for p in parts if p]


def purge(items, used):
    out = []
    for prelude, body in items:
        if prelude == "@stmt":
            out.append((prelude, body))
        elif isinstance(body, list):
            inner = purge(body, used)
            if inner:
                out.append((prelude, inner))
        elif prelude.startswith("@"):
            out.append((prelude, body))          # @font-face, @keyframes, @page …
        else:
            sels = [s for s in split_selectors(prelude) if selector_used(s, used)]
            if sels:
                out.append((",".join(sels), body))
    return out


def minify_decls(body: str) -> str:
    body = re.sub(r"\s+", " ", body).strip()
    body = re.sub(r"\s*([:;,{}>])\s*", r"\1", body)
    # Leerzeichen in calc() wiederherstellen ist nicht nötig: +/- bleiben erhalten
    return body.rstrip(";")


def minify_prelude(p: str) -> str:
    p = re.sub(r"\s+", " ", p).strip()
    p = re.sub(r"\s*([,>~+])\s*(?![^(]*\))", r"\1", p)
    p = re.sub(r"\s*,\s*", ",", p)
    return p


def serialize(items) -> str:
    out = []
    for prelude, body in items:
        if prelude == "@stmt":
            out.append(re.sub(r"\s+", " ", body).strip())
        elif isinstance(body, list):
            out.append(re.sub(r"\s+", " ", prelude).strip() + "{" + serialize(body) + "}")
        elif prelude.lower().startswith("@keyframes") or prelude.lower().startswith("@-webkit-keyframes"):
            inner = parse_blocks(body)
            out.append(re.sub(r"\s+", " ", prelude).strip() + "{" + serialize(inner) + "}")
        else:
            decls = minify_decls(body)
            if decls:
                out.append(minify_prelude(prelude) + "{" + decls + "}")
    return "".join(out)


def collect_used_tokens(site: Path) -> set:
    """Sammelt alle Wörter, die als CSS-Klasse in Frage kommen.

    Neben HTML und JS werden auch die JSON-Dateien der Website gelesen: Das
    Blog-Posts-Element lädt Beiträge aus blog/blog.json nach, und Klassen, die
    nur dort vorkommen, dürfen nicht aus nicepage.css entfernt werden.
    """
    used = set()
    sources = list(text_files(site, ".html", ".js")) + list(site_json_files(site))
    for f in sources:
        s = f.read_text(encoding="utf-8", errors="ignore")
        used.update(re.findall(r"[A-Za-z_][\w-]*", s))
    return used


def optimize_css(site: Path) -> None:
    used = collect_used_tokens(site)
    before = after = 0
    for f in text_files(site, ".css"):
        raw = f.read_text(encoding="utf-8")
        before += len(raw.encode())
        items = parse_blocks(strip_comments(raw))
        if f.name == "nicepage.css":
            items = purge(items, used)
        new = serialize(items)
        f.write_text(new, encoding="utf-8")
        after += len(new.encode())
    print(f"CSS: {fmt(before)} -> {fmt(after)}")


# --------------------------------------------------------------------------- #
# 3. Nicepage-Hinweise entfernen (nur mit gekaufter Nicepage-Lizenz zulässig)
# --------------------------------------------------------------------------- #
BACKLINK_RE = re.compile(
    r'\s*<section\b[^>]*class="[^"]*\bu-backlink\b[^"]*"[^>]*>.*?</section>', re.S | re.I
)
GENERATOR_RE = re.compile(r'\s*<meta\s+name="generator"\s+content="[^"]*nicepage[^"]*"\s*/?>', re.I)
NP_LINK_RE = re.compile(
    r'<a\b([^>]*?)\shref="https?://(?:www\.)?nicepage\.com[^"]*"([^>]*)>(.*?)</a>', re.S | re.I
)


def remove_branding(site: Path) -> None:
    report = []
    for f in sorted(text_files(site, ".html")):
        s = f.read_text(encoding="utf-8")
        found = []

        s, n = BACKLINK_RE.subn("", s)
        if n:
            found.append("Fußzeile „created with“")

        s, n = GENERATOR_RE.subn("", s)
        if n:
            found.append("Generator-Tag")

        home = Path(os.path.relpath(site, f.parent)).as_posix() + "/"

        def fix_link(m):
            if "<img" in m.group(3).lower():          # z. B. Logo: auf Startseite zeigen lassen
                before, after = (re.sub(r'\s*target="_blank"', "", a) for a in m.groups()[:2])
                return f'<a{before} href="{home}"{after}>{m.group(3)}</a>'
            return ""                                  # reiner Textlink: entfernen

        s, n = NP_LINK_RE.subn(fix_link, s)
        if n:
            found.append(f"{n} Link(s) auf nicepage.com")

        if found:
            f.write_text(s, encoding="utf-8")
            report.append(f"  {f.relative_to(site)}: " + ", ".join(found))

    if report:
        print("Nicepage-Hinweise entfernt:")
        print("\n".join(report))
    else:
        print("Nicepage-Hinweise: keine gefunden")


# --------------------------------------------------------------------------- #
# 4. HTML
# --------------------------------------------------------------------------- #
FONT_LINK_RE = re.compile(r'<link id="u-(?:theme|page)-google-font" rel="stylesheet" href="([^"]+)">')
IMG_RE = re.compile(r"<img\b([^>]*)>", re.I)
EMPTY_CSS_RE = re.compile(r'\s*<link rel="stylesheet" href="([^"]+\.css)" media="screen">')


def optimize_html(site: Path) -> None:
    for f in text_files(site, ".html"):
        s = f.read_text(encoding="utf-8")

        # Google Fonts: Verbindung früh aufbauen, Stylesheet nicht blockierend laden
        if "fonts.googleapis.com" in s and "fonts.gstatic.com" not in s:
            s = s.replace(
                "<head>",
                '<head>\n    <link rel="preconnect" href="https://fonts.googleapis.com">'
                '\n    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>',
                1,
            )
        s = FONT_LINK_RE.sub(
            lambda m: (
                f'<link id="u-page-google-font" rel="stylesheet" href="{m.group(1)}" '
                f"media=\"print\" onload=\"this.media='all'\">"
                f'<noscript><link rel="stylesheet" href="{m.group(1)}"></noscript>'
            ),
            s,
        )

        # Leere CSS-Dateien nicht mehr einbinden (spart je eine Anfrage)
        def drop_empty(m):
            target = (f.parent / m.group(1)).resolve()
            if target.exists() and target.stat().st_size == 0:
                return ""
            return m.group(0)

        s = EMPTY_CSS_RE.sub(drop_empty, s)

        # Bilder: die ersten zwei (Logo/Kopfbereich) sofort, alle weiteren "lazy"
        count = [0]

        def lazy(m):
            attrs = m.group(1)
            count[0] += 1
            if count[0] <= 2 or "loading=" in attrs:
                return m.group(0)
            return f'<img loading="lazy" decoding="async"{attrs}>'

        s = IMG_RE.sub(lazy, s)
        f.write_text(s, encoding="utf-8")
    print("HTML: Lazy Loading, Font-Preconnect, leere CSS entfernt")


# --------------------------------------------------------------------------- #
def dir_size(p: Path) -> int:
    return sum(f.stat().st_size for f in p.rglob("*") if f.is_file())


def main():
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    src, dst = Path(sys.argv[1]).resolve(), Path(sys.argv[2]).resolve()
    copy_site(src, dst)
    start = dir_size(dst)
    rewrite_image_refs(dst, optimize_images(dst))
    remove_branding(dst)
    optimize_css(dst)
    optimize_html(dst)
    (dst / ".nojekyll").touch()
    print(f"Gesamt: {fmt(start)} -> {fmt(dir_size(dst))}")


if __name__ == "__main__":
    main()
