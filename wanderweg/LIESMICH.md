# Wanderweg

Interaktive Wanderkarte für die Seite „über mich“ (`aboutMe.html`): Karriere und Ausbildung als Weg durch eine Landschaft.

Beim Veröffentlichen setzt `optimize/build.py` die Karte automatisch in `aboutMe.html` ein. Sie ersetzt dort die beiden Abschnitte mit den Tabs (Karriere, Ausbildung). Am Nicepage-Projekt muss dafür nichts geändert werden.

## Dateien

| Datei | Inhalt |
|---|---|
| `stationen.js` | **Alle Texte und Daten**: Stationen, Läufe, „heute“. Hier wird geändert und ergänzt. |
| `zeichnungen.js` | Die Strichzeichnungen der Stationen (Hafen, Berlin, Frauenkirche …) |
| `wanderweg.js` | Zeichnet Gelände, Höhenlinien, Weg und Schilder |
| `wanderweg.css` | Farben, Schriften, Schilder, Detailfenster |
| `einbau.html` | Der Block, den `build.py` in die Seite einsetzt (Überschrift und Legende der Karte) |
| `bilder/` | Fotos für die Detailfenster (WebP, höchstens ca. 1100 px breit) |

## Häufige Änderungen

**Text einer Station ändern:** in `stationen.js` den Eintrag suchen und den Text hinter `"html":` anpassen. Absätze stehen in `<p>…</p>`, Zwischenüberschriften in `<h4>…</h4>`.

**Neue Station:** einen Eintrag kopieren und anpassen.

- `typ`: `"beruf"` (helles Schild, roter Rand) oder `"ausbildung"` (dunkles Schild, Doppelrand)
- `von`: Beginn als Dezimaljahr, z. B. `2023.7` für September 2023. Das bestimmt die Lage auf der Karte.
- `label`: der Zeitraum, wie er auf dem Schild steht
- `seite`: `"links"` oder `"rechts"` vom Weg
- `id`: Name der Zeichnung in `zeichnungen.js`. Ohne passende Zeichnung erscheint nur das Schild.

**Neuer Lauf:** in `stationen.js` unter `"laeufe"` eine Zeile ergänzen (chronologisch einsortieren) und das Foto nach `bilder/` legen.

**„Hier stehe ich heute“ weiterschieben:** `"heute"` → `"jahr"` erhöhen. Reicht der Weg über 2027 hinaus, zusätzlich in `wanderweg.js` den Wert `T1` anheben.
