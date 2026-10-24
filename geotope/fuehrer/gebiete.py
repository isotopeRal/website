# -*- coding: utf-8 -*-
"""
Gebietsumrisse für die Übersichtskarte der geologischen Führer
==============================================================

Was das Skript macht
--------------------
Die Übersichtskarte (geotope/fuehrer/index.html) zeigt für jede Karte
(Sachsen, Kampanien, Pommern …) die Fläche, die ihre Führer abdecken.
Diese Fläche wird nicht von Hand gezeichnet, sondern aus den Lokalitäten
selbst berechnet:

  1. Alle Punkte aller Führer einer Karte werden eingesammelt.
  2. Um jeden Punkt wird ein Kreis gelegt (Standard 6 km Radius).
  3. Die Kreise werden vereinigt und Lücken bis etwa 30 km geschlossen
     („morphologisches Schließen“: erst weit aufblähen, dann wieder
     genauso weit schrumpfen). Weit entfernte Punktgruppen – etwa Danzig
     im Pommern-Führer – bleiben so als eigene Fläche erhalten.
  4. Der Umriss wird vereinfacht, damit die Datei klein bleibt.

Ergebnis ist die Datei fuehrer.js im selben Ordner. Sie enthält die
Angaben aus fuehrer.json, die Umrisse und die Zahl der Lokalitäten.

Einen neuen Führer hinzufügen
-----------------------------
  1. In fuehrer.json einen Eintrag ergänzen (neue Karte oder neuer Führer
     in einer bestehenden Karte) und unter "punkte" angeben, wo dessen
     Koordinaten liegen (siehe PUNKTQUELLEN unten).
  2. Hochladen. Der GitHub-Actions-Workflow (deploy.yml) führt dieses
     Skript bei jedem Push selbst aus. Wer die Seite vorher lokal ansehen
     will, startet es von Hand: python geotope/fuehrer/gebiete.py
  3. Der Ausschnitt der Übersichtskarte passt sich von selbst an.

Benötigt: Python 3.9+ und das Paket shapely (pip install shapely).

PUNKTQUELLEN – so findet das Skript die Koordinaten
---------------------------------------------------
  {"datei": "x.json", "liste": "rows", "lat": "lat", "lon": "lon"}
      JSON-Datei; "liste" ist der Schlüssel, unter dem die Liste der
      Lokalitäten steht (weglassen, wenn die Datei selbst die Liste ist).
  {"datei": "x.html", "skript": "geodata", ...}
      JSON, das in einer HTML-Seite in <script id="geodata"
      type="application/json"> eingebettet ist.
  {"datei": "x.csv", "lat": "lat", "lon": "lon"}
      CSV-Datei mit Spalten für Breite und Länge (Trenner , oder ;).
  {"koordinaten": [[lon, lat], [lon, lat], ...]}
      Punkte direkt im Eintrag, z. B. für einen Führer ohne eigene Datei.
  Zusätzlich möglich: "ohne": {"feld": "wert"} – Zeilen mit diesem Wert
  werden übersprungen (in Sachsen die nur auf TK-Blatt genauen Punkte).

Feinsteuerung je Karte (optional, in fuehrer.json):
  "radius_km"       Kreis um jeden Punkt            (Standard 6)
  "schliessen_km"   Lücken bis zum Doppelten schließen (Standard 15)
  "vereinfachen_km" Toleranz der Vereinfachung      (Standard 0.8)
"""

import csv
import json
import math
import re
import sys
from datetime import date
from pathlib import Path

try:
    from shapely.geometry import MultiPoint, MultiPolygon, Polygon, mapping
    from shapely.geometry.polygon import orient
    from shapely.ops import unary_union
except ImportError:
    sys.exit("Das Paket shapely fehlt. Bitte installieren: pip install shapely")

# Ordner, in dem dieses Skript liegt – alle Pfade in fuehrer.json beziehen sich darauf
ORDNER = Path(__file__).resolve().parent
REGISTER = ORDNER / "fuehrer.json"
AUSGABE = ORDNER / "fuehrer.js"

# Standardwerte für die Umrissberechnung (in Kilometern)
STANDARD = {"radius_km": 6.0, "schliessen_km": 15.0, "vereinfachen_km": 0.8}

# Mittlere Länge eines Breitengrads in km (genau genug für Umrisse)
KM_JE_GRAD = 111.2


# --------------------------------------------------------------------------- #
# Punkte einlesen
# --------------------------------------------------------------------------- #
def zahl(wert):
    """Wandelt eine Koordinate in eine Zahl um (auch mit Komma); None, wenn leer."""
    if wert is None or wert == "":
        return None
    try:
        return float(str(wert).replace(",", "."))
    except ValueError:
        return None


def zeilen_aus_quelle(q: dict):
    """Liefert die Lokalitäten einer Punktquelle als Liste von Wörterbüchern."""
    if "koordinaten" in q:
        return [{"lon": p[0], "lat": p[1]} for p in q["koordinaten"]]

    pfad = (ORDNER / q["datei"]).resolve()
    if not pfad.exists():
        raise FileNotFoundError(f"Datei nicht gefunden: {pfad}")
    text = pfad.read_text(encoding="utf-8")

    if pfad.suffix.lower() == ".csv":
        # Trennzeichen selbst erkennen (Komma oder Semikolon)
        trenner = ";" if text.splitlines()[0].count(";") > text.splitlines()[0].count(",") else ","
        return list(csv.DictReader(text.splitlines(), delimiter=trenner))

    if "skript" in q:
        # JSON aus einem <script id="…" type="application/json">-Block einer HTML-Seite holen
        muster = r'<script id="%s" type="application/json">(.*?)</script>' % re.escape(q["skript"])
        treffer = re.search(muster, text, re.S)
        if not treffer:
            raise ValueError(f'In {pfad.name} gibt es keinen <script id="{q["skript"]}">')
        daten = json.loads(treffer.group(1))
    else:
        daten = json.loads(text)

    # Bei Bedarf die eigentliche Liste aus dem Objekt herausnehmen
    if q.get("liste"):
        daten = daten[q["liste"]]
    return daten


def punkte_lesen(q: dict):
    """Gibt die Koordinaten einer Quelle als Liste von (lon, lat) zurück."""
    feld_lat = q.get("lat", "lat")
    feld_lon = q.get("lon", "lon")
    ohne = q.get("ohne", {})
    punkte = []
    for z in zeilen_aus_quelle(q):
        # Zeilen überspringen, die laut "ohne" nicht in die Fläche sollen
        if any(str(z.get(k)) == str(v) for k, v in ohne.items()):
            continue
        lat, lon = zahl(z.get(feld_lat)), zahl(z.get(feld_lon))
        if lat is None or lon is None:
            continue
        if not (-90 <= lat <= 90 and -180 <= lon <= 180):
            print(f"  ! Koordinate außerhalb des gültigen Bereichs übersprungen: {lat}, {lon}")
            continue
        punkte.append((lon, lat))
    return punkte


# --------------------------------------------------------------------------- #
# Umriss berechnen
# --------------------------------------------------------------------------- #
def umriss(punkte, radius_km, schliessen_km, vereinfachen_km):
    """
    Berechnet aus Punkten (lon, lat) die abgedeckte Fläche.

    Damit Kreise wirklich rund werden und Abstände in km stimmen, wird
    vorübergehend in ein einfaches ebenes Koordinatensystem um die Mitte
    der Punkte umgerechnet (Längengrade mit dem Kosinus der Breite
    gestaucht). Für Gebiete von einigen hundert Kilometern ist das völlig
    ausreichend genau.
    """
    lon0 = sum(p[0] for p in punkte) / len(punkte)
    lat0 = sum(p[1] for p in punkte) / len(punkte)
    kx = KM_JE_GRAD * math.cos(math.radians(lat0))  # km je Längengrad an dieser Breite
    ky = KM_JE_GRAD                                  # km je Breitengrad

    hin = lambda lon, lat: ((lon - lon0) * kx, (lat - lat0) * ky)
    zurueck = lambda x, y: (round(lon0 + x / kx, 3), round(lat0 + y / ky, 3))

    eben = MultiPoint([hin(*p) for p in punkte])

    # Kreise um alle Punkte, vereinigt
    flaeche = eben.buffer(radius_km, quad_segs=8)
    # Lücken schließen: aufblähen und um denselben Betrag wieder schrumpfen
    flaeche = flaeche.buffer(schliessen_km, quad_segs=8).buffer(-schliessen_km, quad_segs=8)
    flaeche = unary_union(flaeche).simplify(vereinfachen_km, preserve_topology=True)

    # Kleine Löcher (z. B. punktfreie Täler) füllen – für eine Übersicht stören sie nur
    polys = list(flaeche.geoms) if isinstance(flaeche, MultiPolygon) else [flaeche]
    gefuellt = []
    for p in polys:
        loecher = [r for r in p.interiors if Polygon(r).area > 400]  # nur Löcher > 400 km² behalten
        gefuellt.append(Polygon(p.exterior, loecher))

    # Zurück in Länge/Breite. Die Kartenbibliothek d3 erwartet den Außenring im
    # Uhrzeigersinn (orient mit sign=-1), sonst würde sie die Fläche als
    # „ganze Erde außer diesem Gebiet“ deuten.
    ergebnis = []
    for p in gefuellt:
        aussen = [zurueck(x, y) for x, y in p.exterior.coords]
        innen = [[zurueck(x, y) for x, y in r.coords] for r in p.interiors]
        ergebnis.append(orient(Polygon(aussen, innen), sign=-1.0))

    geom = MultiPolygon(ergebnis)
    flaeche_km2 = sum(p.area for p in gefuellt)
    return mapping(geom), (round(lon0, 3), round(lat0, 3)), flaeche_km2


# --------------------------------------------------------------------------- #
# Hauptprogramm
# --------------------------------------------------------------------------- #
def main():
    register = json.loads(REGISTER.read_text(encoding="utf-8"))
    karten_aus = []

    for karte in register["karten"]:
        print(f"Karte {karte['name']}:")
        param = {k: karte.get(k, v) for k, v in STANDARD.items()}
        alle_punkte = []
        fuehrer_aus = []

        for f in karte["fuehrer"]:
            pts = punkte_lesen(f["punkte"])
            print(f"  {f.get('kurz', f['id'])}: {len(pts)} Lokalitäten")
            alle_punkte += pts
            # Für die Seite alles außer der Punktquelle übernehmen, dazu die Anzahl
            eintrag = {k: v for k, v in f.items() if k != "punkte"}
            eintrag["n"] = len(pts)
            fuehrer_aus.append(eintrag)

        if not alle_punkte:
            print("  ! keine Koordinaten gefunden – Karte wird übersprungen")
            continue

        gebiet, zentrum, km2 = umriss(alle_punkte, **param)
        km2_text = f"{km2:,.0f}".replace(",", ".")  # deutsche Tausenderpunkte
        print(f"  Umriss: {len(gebiet['coordinates'])} Teilfläche(n), rund {km2_text} km²")

        eintrag = {k: v for k, v in karte.items() if k not in ("fuehrer", *STANDARD)}
        eintrag.update({"fuehrer": fuehrer_aus, "zentrum": zentrum, "gebiet": gebiet})
        karten_aus.append(eintrag)

    daten = {"stand": date.today().isoformat(), "karten": karten_aus}
    # Als Skript (window.FUEHRER = …) statt reinem JSON, damit die Seite auch
    # direkt von der Festplatte (file://) geöffnet funktioniert
    AUSGABE.write_text(
        "// Automatisch erzeugt von gebiete.py aus fuehrer.json – nicht von Hand bearbeiten.\n"
        "window.FUEHRER = " + json.dumps(daten, ensure_ascii=False, separators=(",", ":")) + ";\n",
        encoding="utf-8",
    )
    print(f"Geschrieben: {AUSGABE.name} ({AUSGABE.stat().st_size / 1024:.1f} KB)")


if __name__ == "__main__":
    main()
