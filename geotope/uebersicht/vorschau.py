# -*- coding: utf-8 -*-
"""
Mini-Vorschau der Übersichtskarte als SVG-Bild
==============================================

Was das Skript macht
--------------------
Es zeichnet ein kleines, statisches Bild der Übersichtskarte
(geotope/uebersicht/vorschau.svg): Ausschnitt der Erdkugel, Land, Grenzen,
die farbigen Gebiete der Führer mit Namen und eine Zeile mit den Zahlen.

Das Bild wird auf der Startseite (Nicepage, HTML-Block) als Vorschau
eingebunden und verlinkt auf die interaktive Karte. Weil gebiete.py dieses
Skript am Ende aufruft und der GitHub-Workflow gebiete.py bei jedem Push
ausführt, zeigt die Vorschau neue Führer von selbst – am HTML-Block in
Nicepage muss dafür nichts geändert werden.

Der Ausschnitt wird genauso bestimmt wie auf der Übersichtsseite: Die Kugel
wird so gedreht, dass alle Gebiete möglichst mittig liegen, und so weit
vergrößert, dass sie ins Bild passen. Liegen die Gebiete über die halbe Erde
verteilt, wird die ganze Kugel gezeigt.

Aufruf von Hand (normalerweise nicht nötig):
    python geotope/uebersicht/vorschau.py

Benötigt: Python 3.9+ und shapely.
"""

import json
import math
from pathlib import Path

from shapely.geometry import LineString, MultiLineString, Point, Polygon, box
from shapely.ops import unary_union

ORDNER = Path(__file__).resolve().parent
DATEN = ORDNER / "fuehrer.js"                    # von gebiete.py erzeugt
WELT = ORDNER / "welt" / "laender-50m.js"        # Natural Earth 1:50 Mio.
AUSGABE = ORDNER / "vorschau.svg"

# Bildgröße in Pixeln (Seitenverhältnis 16:9)
BREITE, HOEHE = 640, 360
RAND = 34                 # Abstand der Gebiete zum Bildrand
MIN_SPAN = 7.0            # mindestens so viele Grad Umgebung (Halbmesser), auch bei nur einem Gebiet
GLOBUS_AB = 75.0          # weiter verteilt als 75° von der Mitte → ganze Kugel

# Farben wie auf der Übersichtsseite (helles Farbschema)
FARBE = {
    "hintergrund": "#eef0eb", "meer": "#dbe4e2", "land": "#f6f5ee", "kueste": "#aab2a3",
    "grenze": "#c6ccc0", "netz": "#c3cbc0", "text": "#1c2320", "grau": "#5a645e", "halo": "#ffffff",
}
# Reihenfolge der Gebietsfarben wie in index.html (FARBEN = r1, r3, r2, …)
GEBIETSFARBEN = ["#b0425e", "#c07a12", "#2f6fa8", "#5d8a2e", "#7b4ea0", "#1f8a85", "#a0522d", "#868c85"]
FARBNAMEN = {"r1": "#b0425e", "r2": "#2f6fa8", "r3": "#c07a12", "r4": "#5d8a2e",
             "r5": "#7b4ea0", "r6": "#a0522d", "r7": "#1f8a85", "r8": "#868c85"}
# Ein Bild in einem <img> kann keine Webschriften laden – daher Systemschriften
SCHRIFT = "'Segoe UI',Roboto,'Helvetica Neue',Arial,sans-serif"
RAD = math.pi / 180


def js_laden(pfad: Path):
    """Liest eine Datei der Form 'window.X = {...};' und gibt das Objekt zurück."""
    text = pfad.read_text(encoding="utf-8")
    return json.loads(text[text.index("=") + 1:].strip().rstrip(";"))


# --------------------------------------------------------------------------- #
# Kugelgeometrie
# --------------------------------------------------------------------------- #
def winkelabstand(a, b):
    """Winkel zwischen zwei Punkten (lon, lat) auf der Kugel, in Radiant."""
    l1, p1, l2, p2 = a[0] * RAD, a[1] * RAD, b[0] * RAD, b[1] * RAD
    h = math.sin((p2 - p1) / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin((l2 - l1) / 2) ** 2
    return 2 * math.asin(min(1.0, math.sqrt(h)))


def kappen_mitte(punkte):
    """
    Mitte der kleinsten Kugelkappe, die alle Punkte enthält: grobe Suche im
    5°-Raster, danach schrittweise feiner (wie capCenter() in index.html).
    """
    if len(punkte) == 1:
        return punkte[0]
    best, best_r = punkte[0], float("inf")

    def pruefen(c):
        nonlocal best, best_r
        r = 0.0
        for p in punkte:
            r = max(r, winkelabstand(c, p))
            if r >= best_r:
                return
        best, best_r = c, r

    for la in range(-85, 90, 5):
        for lo in range(-180, 180, 5):
            pruefen((lo, la))
    schritt = 2.5
    while schritt > 0.02:
        lo0, la0 = best
        for i in range(-2, 3):
            for j in range(-2, 3):
                pruefen((lo0 + i * schritt, max(-89.9, min(89.9, la0 + j * schritt))))
        schritt /= 2
    return best


class Ortho:
    """
    Orthografische Projektion: der Blick aus großer Entfernung auf die Kugel.
    mitte = (lon, lat) des Bildmittelpunkts der Kugel, s = Kugelradius in Pixeln,
    tx/ty = Lage des Kugelmittelpunkts im Bild.
    """

    def __init__(self, mitte, s=1.0, tx=0.0, ty=0.0):
        self.l0, self.p0 = mitte[0] * RAD, mitte[1] * RAD
        self.s, self.tx, self.ty = s, tx, ty

    def roh(self, lon, lat):
        """Einheitskoordinaten (x, y) und cos c (> 0: Punkt auf der sichtbaren Seite)."""
        l, p = lon * RAD - self.l0, lat * RAD
        x = math.cos(p) * math.sin(l)
        y = math.cos(self.p0) * math.sin(p) - math.sin(self.p0) * math.cos(p) * math.cos(l)
        cosc = math.sin(self.p0) * math.sin(p) + math.cos(self.p0) * math.cos(p) * math.cos(l)
        return x, y, cosc

    def bild(self, x, y):
        return self.tx + self.s * x, self.ty - self.s * y

    def __call__(self, lon, lat):
        x, y, cosc = self.roh(lon, lat)
        return self.bild(x, y), cosc > 0


def ansicht(punkte, zentren):
    """Bestimmt Drehung und Maßstab so, dass alle Gebiete ins Bild passen."""
    mitte = zentren[0] if len(zentren) == 1 else kappen_mitte(punkte)
    max_winkel = max(winkelabstand(mitte, p) for p in punkte) / RAD
    r_ganz = min(BREITE, HOEHE) / 2 - 10                     # Radius für die ganze Kugel
    if max_winkel > GLOBUS_AB:
        return Ortho(mitte, r_ganz, BREITE / 2, HOEHE / 2)
    # Ausdehnung der Gebiete in Einheitskoordinaten
    p = Ortho(mitte)
    xy = [p.roh(*q)[:2] for q in punkte]
    x0, x1 = min(v[0] for v in xy), max(v[0] for v in xy)
    y0, y1 = min(v[1] for v in xy), max(v[1] for v in xy)
    # oben etwas mehr Platz für die Beschriftung, unten für die Zahlenzeile
    oben, unten = RAND + 16, RAND + 22
    s = min((BREITE - 2 * RAND) / max(x1 - x0, 1e-9), (HOEHE - oben - unten) / max(y1 - y0, 1e-9))
    s_max = (min(BREITE, HOEHE) / 2) / math.sin(MIN_SPAN * RAD)
    s = max(r_ganz, min(s, s_max))
    if s == r_ganz:
        return Ortho(mitte, r_ganz, BREITE / 2, HOEHE / 2)
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    return Ortho(mitte, s, BREITE / 2 - s * cx, oben + (HOEHE - oben - unten) / 2 + s * cy)


# --------------------------------------------------------------------------- #
# Weltkarte (TopoJSON von world-atlas) entschlüsseln
# --------------------------------------------------------------------------- #
def topo_boegen(topo):
    """TopoJSON speichert Linien als ganzzahlige Differenzen – hier zurück in lon/lat."""
    sx, sy = topo["transform"]["scale"]
    tx, ty = topo["transform"]["translate"]
    boegen = []
    for arc in topo["arcs"]:
        x = y = 0
        pts = []
        for dx, dy in arc:
            x += dx
            y += dy
            pts.append((x * sx + tx, y * sy + ty))
        boegen.append(pts)
    return boegen


def ring_aus(boegen, idx):
    """Setzt einen Ring aus Bögen zusammen; ~i (negativ) heißt: Bogen i rückwärts."""
    pts = []
    for i in idx:
        b = boegen[i] if i >= 0 else boegen[~i][::-1]
        pts.extend(b if not pts else b[1:])
    return pts


def landflaechen(topo, boegen):
    """Alle Landpolygone als Listen von Ringen."""
    polys = []
    for g in topo["objects"]["land"]["geometries"]:
        teile = [g["arcs"]] if g["type"] == "Polygon" else g["arcs"]
        for poly in teile:
            polys.append([ring_aus(boegen, r) for r in poly])
    return polys


def grenzlinien(topo, boegen):
    """Bögen, die zu zwei verschiedenen Ländern gehören = Staatsgrenzen (wie topojson.mesh)."""
    nutzer = {}
    for n, g in enumerate(topo["objects"]["countries"]["geometries"]):
        if g.get("type") not in ("Polygon", "MultiPolygon"):
            continue
        teile = [g["arcs"]] if g["type"] == "Polygon" else g["arcs"]
        for poly in teile:
            for ring in poly:
                for i in ring:
                    nutzer.setdefault(i if i >= 0 else ~i, set()).add(n)
    return [boegen[i] for i, s in nutzer.items() if len(s) > 1]


# --------------------------------------------------------------------------- #
# Projizieren und auf Kugel und Bildrand zuschneiden
# --------------------------------------------------------------------------- #
def flaeche_proj(proj, ringe, scheibe):
    """
    Projiziert ein Polygon. Punkte auf der Rückseite werden auf den Kugelrand
    geschoben – für eine kleine Vorschau genau genug. Danach wird auf die
    sichtbare Kugelscheibe zugeschnitten.
    """
    def ring(r):
        out = []
        for lon, lat in r:
            x, y, cosc = proj.roh(lon, lat)
            if cosc < 0:  # Rückseite → auf den Rand der Scheibe
                n = math.hypot(x, y) or 1.0
                x, y = x / n, y / n
            out.append(proj.bild(x, y))
        return out

    aussen = ring(ringe[0])
    if len(aussen) < 4:
        return None
    # Ganz auf der Rückseite liegende Flächen weglassen
    if all(proj.roh(lon, lat)[2] < 0 for lon, lat in ringe[0][::max(1, len(ringe[0]) // 40)]):
        return None
    g = Polygon(aussen, [ring(r) for r in ringe[1:] if len(r) >= 4]).buffer(0)
    return g.intersection(scheibe) if not g.is_empty else None


def linie_proj(proj, pts):
    """Projiziert eine Linie und trennt sie dort auf, wo sie hinter die Kugel läuft."""
    teile, aktuell = [], []
    for lon, lat in pts:
        xy, vorn = proj(lon, lat)
        if vorn:
            aktuell.append(xy)
        elif aktuell:
            teile.append(aktuell)
            aktuell = []
    if aktuell:
        teile.append(aktuell)
    return [t for t in teile if len(t) > 1]


def pfad(geom, nk=1):
    """Wandelt eine shapely-Geometrie in SVG-Pfaddaten um (nk = Nachkommastellen)."""
    f = lambda v: f"{v:.{nk}f}".rstrip("0").rstrip(".")
    teile = []

    def ring(coords, schliessen):
        c = list(coords)
        if len(c) < 2:
            return
        teile.append("M" + "L".join(f"{f(x)} {f(y)}" for x, y in c) + ("Z" if schliessen else ""))

    def geo(g):
        if g.is_empty:
            return
        t = g.geom_type
        if t == "Polygon":
            ring(g.exterior.coords[:-1], True)
            for r in g.interiors:
                ring(r.coords[:-1], True)
        elif t == "LineString":
            ring(g.coords, False)
        elif t.startswith("Multi") or t == "GeometryCollection":
            for x in g.geoms:
                geo(x)

    geo(geom)
    return "".join(teile)


def esc(s):
    return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")


def tausender(n):
    return f"{n:,}".replace(",", ".")


# --------------------------------------------------------------------------- #
# Bild zusammensetzen
# --------------------------------------------------------------------------- #
def zeichnen():
    daten = js_laden(DATEN)
    karten = daten["karten"]
    topo = js_laden(WELT)
    boegen = topo_boegen(topo)

    # Randpunkte aller Gebiete (je Gebiet höchstens 24) bestimmen den Ausschnitt
    punkte, zentren = [], []
    for k in karten:
        ring = [p for poly in k["gebiet"]["coordinates"] for p in poly[0]]
        schritt = max(1, len(ring) // 24)
        punkte += [tuple(p) for p in ring[::schritt]]
        zentren.append(tuple(k["zentrum"]))
    proj = ansicht(punkte, zentren)

    rahmen = box(0, 0, BREITE, HOEHE)
    kreis = Point(proj.tx, proj.ty).buffer(proj.s, quad_segs=64)
    scheibe = kreis.intersection(rahmen)

    # Land (erst vereinigen, dann vereinfachen: 0,4 px Toleranz reichen für die Vorschau)
    land = [flaeche_proj(proj, p, scheibe) for p in landflaechen(topo, boegen)]
    land = unary_union([g for g in land if g is not None and not g.is_empty]).simplify(0.4)

    def linien(liste):
        teile = [LineString(t) for pts in liste for t in linie_proj(proj, pts)]
        return MultiLineString(teile).intersection(rahmen).simplify(0.4) if teile else None

    grenzen = linien(grenzlinien(topo, boegen))

    # Gradnetz: Abstand passend zum Ausschnitt (10°, 5° oder 1°)
    halb = math.degrees(math.asin(min(1.0, min(BREITE, HOEHE) / 2 / proj.s)))
    st = 10 if halb > 25 else 5 if halb > 6 else 1
    netz_pts = [[(lo, la / 2) for la in range(-178, 179)] for lo in range(-180, 180, st)]
    netz_pts += [[(lo / 2, la) for lo in range(-360, 361)] for la in range(-90 + st, 90, st)]
    netz = linien(netz_pts)

    # Gebiete der Führer
    gebiete = []
    for i, k in enumerate(karten):
        farbe = FARBNAMEN.get(k.get("farbe", ""), GEBIETSFARBEN[i % len(GEBIETSFARBEN)])
        teile = [flaeche_proj(proj, poly, scheibe) for poly in k["gebiet"]["coordinates"]]
        g = unary_union([t for t in teile if t is not None and not t.is_empty])
        zx, zy = proj(*k["zentrum"])[0]
        gebiete.append({"k": k, "farbe": farbe, "g": g, "z": (zx, zy)})

    svg = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {BREITE} {HOEHE}" width="{BREITE}" height="{HOEHE}" role="img" aria-label="Karte der Gebiete mit geologischen Führern">',
           f'<rect width="{BREITE}" height="{HOEHE}" fill="{FARBE["hintergrund"]}"/>',
           f'<path d="{pfad(kreis.intersection(rahmen.buffer(2)))}" fill="{FARBE["meer"]}"/>']
    if netz is not None:
        svg.append(f'<path d="{pfad(netz)}" fill="none" stroke="{FARBE["netz"]}" stroke-width=".6"/>')
    svg.append(f'<path d="{pfad(land)}" fill="{FARBE["land"]}" stroke="{FARBE["kueste"]}" stroke-width=".7" stroke-linejoin="round"/>')
    if grenzen is not None:
        svg.append(f'<path d="{pfad(grenzen)}" fill="none" stroke="{FARBE["grenze"]}" stroke-width=".8"/>')
    if proj.s < max(BREITE, HOEHE):  # Kugelrand nur zeigen, wenn er im Bild liegt
        svg.append(f'<path d="{pfad(kreis.exterior)}" fill="none" stroke="#b9c0b4" stroke-width="1"/>')

    # Flächen; sehr kleine Gebiete bekommen zusätzlich einen Punkt
    belegt = []
    beschriftungen = []
    for gb in sorted(gebiete, key=lambda x: -x["g"].area):
        g, farbe = gb["g"], gb["farbe"]
        if not g.is_empty:
            svg.append(f'<path d="{pfad(g)}" fill="{farbe}" fill-opacity=".38" stroke="{farbe}" stroke-width="1.4" stroke-linejoin="round"/>')
        klein = g.is_empty or g.area < 120
        if klein and 0 <= gb["z"][0] <= BREITE and 0 <= gb["z"][1] <= HOEHE:
            svg.append(f'<circle cx="{gb["z"][0]:.1f}" cy="{gb["z"][1]:.1f}" r="6" fill="{farbe}" stroke="#fff" stroke-width="2"/>')
        # Beschriftung über dem Gebiet, sonst darunter; überdeckte Namen entfallen
        if g.is_empty:
            bx0 = bx1 = gb["z"][0]
            by0, by1 = gb["z"][1] - 6, gb["z"][1] + 6
        else:
            bx0, by0, bx1, by1 = g.bounds
        name = gb["k"]["name"]
        w = len(name) * 8.2 + 6
        x = min(max((bx0 + bx1) / 2, w / 2 + 6), BREITE - w / 2 - 6)
        for y in (by0 - 7, by1 + 18):
            y = min(max(y, 18), HOEHE - 30)
            r = (x - w / 2, y - 14, x + w / 2, y + 3)
            if not any(r[0] < q[2] and r[2] > q[0] and r[1] < q[3] and r[3] > q[1] for q in belegt):
                belegt.append(r)
                beschriftungen.append(f'<text x="{x:.1f}" y="{y:.1f}">{esc(name)}</text>')
                break
    svg.append(f'<g font-family="{SCHRIFT}" font-size="14.5" font-weight="700" text-anchor="middle" fill="{FARBE["text"]}" '
               f'stroke="{FARBE["halo"]}" stroke-width="4" stroke-linejoin="round" paint-order="stroke">{"".join(beschriftungen)}</g>')

    # Zahlenzeile unten links
    n_f = sum(len(k["fuehrer"]) for k in karten)
    n_l = sum(f.get("n", 0) for k in karten for f in k["fuehrer"])
    zeile = f'{len(karten)} {"Gebiet" if len(karten) == 1 else "Gebiete"} · {n_f} Führer · {tausender(n_l)} Stellen'
    bw = len(zeile) * 6.6 + 22
    svg.append(f'<g font-family="{SCHRIFT}" font-size="12" font-weight="600"><rect x="10" y="{HOEHE - 34}" width="{bw:.0f}" height="24" rx="12" '
               f'fill="#fafbf8" fill-opacity=".94" stroke="#d6dbd2"/><text x="21" y="{HOEHE - 18}" fill="{FARBE["grau"]}">{esc(zeile)}</text></g>')
    svg.append("</svg>")

    AUSGABE.write_text("\n".join(svg) + "\n", encoding="utf-8")
    print(f"Geschrieben: {AUSGABE.name} ({AUSGABE.stat().st_size / 1024:.1f} KB)")


if __name__ == "__main__":
    zeichnen()
