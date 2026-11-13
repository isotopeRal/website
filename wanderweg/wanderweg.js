/* Wanderweg – interaktive Karriere-Wanderkarte
   Liest die Inhalte aus window.WANDERWEG (stationen.js) und zeichnet daraus:
   Gelände mit Höhenlinien, den Wanderweg, die Stationen und die Startnummern der Läufe.
   Keine externen Bibliotheken. */
(function () {
  'use strict';

  var D = window.WANDERWEG;
  var VIG = window.WANDERWEG_VIGNETTEN || {};
  var root = document.getElementById('wanderweg');
  var mapEl = document.getElementById('ww-map');
  var dlg = document.getElementById('ww-dlg');
  if (!D || !root || !mapEl) return;

  var SVGNS = 'http://www.w3.org/2000/svg';
  var T0 = 2002.85, T1 = 2027.5;              // Zeitraum der Karte (Jahre)

  // Bildpfade: im Prototyp eingebettet, auf der Website relativ zu aboutMe.html
  function img(name) {
    return (window.WANDERWEG_BILDER && window.WANDERWEG_BILDER[name]) || name;
  }

  /* ------------------------------------------------------------------ */
  /* Hilfsfunktionen                                                    */
  /* ------------------------------------------------------------------ */
  function el(tag, attrs, parent) {
    var n = document.createElementNS(SVGNS, tag);
    for (var k in attrs) n.setAttribute(k, attrs[k]);
    if (parent) parent.appendChild(n);
    return n;
  }
  function html(tag, cls, parent) {
    var n = document.createElement(tag);
    if (cls) n.className = cls;
    if (parent) parent.appendChild(n);
    return n;
  }
  function clamp(v, a, b) { return v < a ? a : v > b ? b : v; }
  function smooth(e0, e1, x) { var t = clamp((x - e0) / (e1 - e0), 0, 1); return t * t * (3 - 2 * t); }
  function band(t, a, b, e) { return smooth(a - e, a, t) * (1 - smooth(b, b + e, t)); }

  // deterministisches Rauschen: die Landschaft sieht bei jedem Besuch gleich aus
  function hash(i, j) {
    var h = Math.imul(i, 374761393) + Math.imul(j, 668265263) | 0;
    h = Math.imul(h ^ (h >>> 13), 1274126177);
    return ((h ^ (h >>> 16)) >>> 0) / 4294967295;
  }
  function vnoise(x, y) {
    var xi = Math.floor(x), yi = Math.floor(y), xf = x - xi, yf = y - yi;
    var u = xf * xf * (3 - 2 * xf), v = yf * yf * (3 - 2 * yf);
    var a = hash(xi, yi), b = hash(xi + 1, yi), c = hash(xi, yi + 1), d = hash(xi + 1, yi + 1);
    return a + (b - a) * u + (c - a) * v + (a - b - c + d) * u * v;
  }
  function fbm(x, y) {
    var s = 0, a = 0.5, f = 1;
    for (var k = 0; k < 4; k++) { s += a * vnoise(x * f, y * f); f *= 2.03; a *= 0.5; }
    return s;
  }

  /* ------------------------------------------------------------------ */
  /* Geometrie: Jahre -> Pixel                                          */
  /* ------------------------------------------------------------------ */
  var G = {};   // aktuelle Abmessungen
  function Y(t) { return G.top + (t - T0) * G.ppy; }
  function T(y) { return T0 + (y - G.top) / G.ppy; }

  // Gaußhügel in Pixeln (rx/ry = Radius in Pixeln bei 1000 px Kartenbreite)
  function bump(x, y, cx, ct, rx, ry) {
    var dx = (x - cx * G.W) / (rx * G.sc), dy = (y - Y(ct)) / (ry * G.sc);
    return Math.exp(-(dx * dx + dy * dy));
  }
  function elbeY(x) { return Y(2022.25) + 22 * G.sc * Math.sin(x / (150 * G.sc)) + 14 * G.sc * Math.sin(x / (61 * G.sc) + 1); }

  /* Höhe in Metern an einem Kartenpunkt – die Landschaft folgt den Lebensstationen */
  function height(x, y) {
    var t = T(y), X = x / G.W;
    // unregelmäßige Grenzen zwischen den Landschaften statt gerader Kanten
    var tw = t + 1.1 * (fbm(x / (230 * G.sc), 7.3) - 0.45);
    var h = 38 + 32 * fbm(x / (170 * G.sc), y / (150 * G.sc));

    // Küste: Nordsee und Golf von Neapel (Marinezeit)
    var coast = 0.30 + 0.07 * Math.sin(t * 1.7) + 0.08 * (fbm(t * 1.3, 3.7) - 0.45);
    var sea = band(t, T0 - 2, 2010.2, 0.7) * smooth(coast + 0.05, coast - 0.13, X);
    h -= sea * 150;
    // Vesuv mit Krater
    h += 1230 * bump(x, y, 0.80, 2008.3, 95, 95);
    h -= 260 * bump(x, y, 0.80, 2008.3, 22, 22);

    // Berliner Seen
    h -= 85 * bump(x, y, 0.15, 2011.75, 75, 34);
    h -= 70 * bump(x, y, 0.85, 2012.75, 38, 60);

    // Hohe Tauern (Masterarbeit im Tauernfenster)
    var alps = band(tw, 2013.6, 2015.8, 0.5);
    h += 3200 * bump(x, y, 0.91, 2014.75, 190, 170) + 2100 * bump(x, y, 0.76, 2015.35, 85, 95);
    h += alps * smooth(0.62, 0.8, X) * 700 * fbm(x / (90 * G.sc), y / (90 * G.sc));

    // Telegrafenberg Potsdam und die chilenische Küstenkordillere
    h += 58 * bump(x, y, 0.82, 2017.45, 55, 48);
    h += 1150 * bump(x, y, 0.05, 2018.0, 85, 230) * (0.7 + 0.6 * fbm(x / 60, y / 60));

    // Erzgebirge
    var erz = band(tw, 2019.9, 2021.9, 1.0);
    h += erz * (260 + 520 * fbm(x / (260 * G.sc) + 9, y / (200 * G.sc)));
    h += 640 * bump(x, y, 0.13, 2021.0, 120, 110);

    // Elbtal bei Dresden
    var dy = (y - elbeY(x)) / (26 * G.sc);
    h -= 90 * Math.exp(-dy * dy);

    // Lausitz: flach, Tagebau mit Böschungsstufen, Bärwalder See
    var lau = smooth(2022.35, 2023.35, tw);
    h = h * (1 - lau) + lau * (108 + 14 * fbm(x / (200 * G.sc), y / (200 * G.sc)));
    var px = (x - 0.82 * G.W) / (125 * G.sc), py = (y - Y(2023.3)) / (88 * G.sc);
    var r = Math.sqrt(px * px + py * py);
    if (r < 1) h -= 96 * Math.ceil((1 - r) * 6) / 6;
    h -= 95 * bump(x, y, 0.15, 2025.75, 95, 62);
    return h;
  }

  /* ------------------------------------------------------------------ */
  /* Gelände: Farbfläche (Canvas) + Höhenlinien (SVG)                   */
  /* ------------------------------------------------------------------ */
  function drawTerrain(svg) {
    var cell = G.W < 640 ? 7 : 9;
    var cols = Math.ceil(G.W / cell) + 1, rows = Math.ceil(G.H / cell) + 1;
    var Hm = new Float32Array(cols * rows);
    for (var j = 0; j < rows; j++)
      for (var i = 0; i < cols; i++) Hm[j * cols + i] = height(i * cell, j * cell);

    // Farbfläche mit Schummerung (Licht von Nordwesten)
    var cv = html('canvas', 'ww-map__tint', null);
    cv.width = cols; cv.height = rows;
    var ctx = cv.getContext('2d'), im = ctx.createImageData(cols, rows), p = im.data;
    for (j = 0; j < rows; j++) for (i = 0; i < cols; i++) {
      var h = Hm[j * cols + i];
      var hx = Hm[j * cols + Math.min(i + 1, cols - 1)] - Hm[j * cols + Math.max(i - 1, 0)];
      var hy = Hm[Math.min(j + 1, rows - 1) * cols + i] - Hm[Math.max(j - 1, 0) * cols + i];
      var shade = clamp(-(hx + hy) / (cell * 12), -0.4, 0.4);
      var c;
      if (h < 0) { var d = clamp(-h / 120, 0, 1); c = [44 - 14 * d, 70 - 18 * d, 86 - 14 * d]; shade = 0; }
      else if (h < 150) c = [44, 46, 42];
      else if (h < 900) { var k = (h - 150) / 750; c = [44 + 9 * k, 46 + 6 * k, 42 + 3 * k]; }
      else if (h < 2600) { k = (h - 900) / 1700; c = [53 + 12 * k, 52 + 10 * k, 45 + 10 * k]; }
      else c = [70, 69, 64];
      // Wald (grünlich) im Hügel- und Bergland
      var forest = fbm(i * cell / 140 + 40, j * cell / 140) > 0.56 && h > 45 && h < 1600;
      if (forest) c = [c[0] - 4, c[1] + 6, c[2] - 2];
      var o = (j * cols + i) * 4;
      p[o] = c[0] * (1 + shade); p[o + 1] = c[1] * (1 + shade); p[o + 2] = c[2] * (1 + shade); p[o + 3] = 255;
    }
    ctx.putImageData(im, 0, 0);
    mapEl.insertBefore(cv, svg);

    // Höhenlinien: 10-m-Abstand im Flachland, 50 m im Hügelland, 100 m im Gebirge
    var levels = [-80, -60, -40, -20, 0];
    for (var L = 50; L <= 200; L += 10) levels.push(L);
    for (L = 250; L <= 500; L += 50) levels.push(L);
    for (L = 600; L <= 3600; L += 100) levels.push(L);

    var dNorm = [], dIndex = [], dShore = [], dDepth = [];
    function interp(a, b, va, vb, Lv) { return a + (b - a) * ((Lv - va) / (vb - va)); }
    levels.forEach(function (Lv) {
      var out = Lv === 0 ? dShore : Lv < 0 ? dDepth : (Lv % 500 === 0 || Lv === 100) ? dIndex : dNorm;
      for (var j = 0; j < rows - 1; j++) for (var i = 0; i < cols - 1; i++) {
        var a = Hm[j * cols + i], b = Hm[j * cols + i + 1], c = Hm[(j + 1) * cols + i + 1], d = Hm[(j + 1) * cols + i];
        var idx = (a >= Lv ? 8 : 0) | (b >= Lv ? 4 : 0) | (c >= Lv ? 2 : 0) | (d >= Lv ? 1 : 0);
        if (idx === 0 || idx === 15) continue;
        var x0 = i * cell, y0 = j * cell, x1 = x0 + cell, y1 = y0 + cell;
        var top = [interp(x0, x1, a, b, Lv), y0], right = [x1, interp(y0, y1, b, c, Lv)],
            bottom = [interp(x0, x1, d, c, Lv), y1], left = [x0, interp(y0, y1, a, d, Lv)];
        var segs;
        switch (idx) {
          case 1: case 14: segs = [left, bottom]; break;
          case 2: case 13: segs = [bottom, right]; break;
          case 3: case 12: segs = [left, right]; break;
          case 4: case 11: segs = [top, right]; break;
          case 5: segs = [left, top, bottom, right]; break;
          case 6: case 9: segs = [top, bottom]; break;
          case 7: case 8: segs = [left, top]; break;
          case 10: segs = [left, bottom, top, right]; break;
        }
        for (var s = 0; s < segs.length; s += 2)
          out.push('M' + segs[s][0].toFixed(1) + ' ' + segs[s][1].toFixed(1) + 'L' + segs[s + 1][0].toFixed(1) + ' ' + segs[s + 1][1].toFixed(1));
      }
    });
    var g = el('g', { fill: 'none', 'stroke-linecap': 'round' }, svg);
    el('path', { d: dDepth.join(''), stroke: 'rgba(127,178,204,.18)', 'stroke-width': 1 }, g);
    el('path', { d: dNorm.join(''), stroke: 'var(--ww-contour)', 'stroke-width': 0.9 }, g);
    el('path', { d: dIndex.join(''), stroke: 'var(--ww-contour-index)', 'stroke-width': 1.4 }, g);
    el('path', { d: dShore.join(''), stroke: 'var(--ww-water)', 'stroke-width': 1.6, opacity: 0.85 }, g);
  }

  /* ------------------------------------------------------------------ */
  /* Kartenbeschriftung                                                 */
  /* ------------------------------------------------------------------ */
  function label(svg, text, X, t, cls, opts) {
    opts = opts || {};
    var n = el('text', { x: (X * G.W).toFixed(1), y: (typeof t === 'number' && t > 1000 ? Y(t) : t).toFixed(1),
      class: 'ww-label ' + (cls || ''), 'text-anchor': opts.anchor || 'middle' }, svg);
    if (opts.rotate) n.setAttribute('transform', 'rotate(' + opts.rotate + ' ' + (X * G.W) + ' ' + Y(t) + ')');
    n.textContent = text;
    fit(n);
    return n;
  }
  // Beschriftung, die über den Kartenrand ragen würde, nach innen schieben
  function fit(n) {
    if (n.getAttribute('transform')) return;
    var b = n.getBBox(), dx = 0;
    if (b.x < 6) dx = 6 - b.x; else if (b.x + b.width > G.W - 6) dx = G.W - 6 - b.x - b.width;
    if (dx) n.setAttribute('x', (+n.getAttribute('x') + dx).toFixed(1));
  }
  function peak(svg, name, X, t) {
    var x = X * G.W, y = Y(t);
    el('path', { d: 'M' + (x - 5) + ' ' + (y + 4) + 'L' + x + ' ' + (y - 5) + 'L' + (x + 5) + ' ' + (y + 4) + 'Z', fill: 'rgba(236,235,229,.8)' }, svg);
    var n = el('text', { x: x, y: y + 20, class: 'ww-label ww-label--peak', 'text-anchor': 'middle' }, svg);
    n.textContent = name;
    fit(n);
  }
  // Bergbauzeichen (Schlägel und Eisen); stillgelegt = auf dem Kopf stehend
  function mine(svg, X, t, name, anchor, stillgelegt) {
    var x = X * G.W, y = Y(t);
    var g = el('g', { transform: stillgelegt ? 'rotate(180 ' + x + ' ' + (y - 1.5) + ')' : '', stroke: 'rgba(236,235,229,.8)', 'stroke-width': 2, 'stroke-linecap': 'round', fill: 'none' }, svg);
    el('path', { d: 'M' + (x - 6) + ' ' + (y + 6) + 'L' + (x + 5) + ' ' + (y - 5) + 'M' + (x + 6) + ' ' + (y + 6) + 'L' + (x - 5) + ' ' + (y - 5) }, g);
    el('path', { d: 'M' + (x + 1) + ' ' + (y - 9) + 'L' + (x + 9) + ' ' + (y - 1) + 'M' + (x - 1) + ' ' + (y - 9) + 'L' + (x - 9) + ' ' + (y - 1), 'stroke-width': 3.2 }, g);
    var n = el('text', { x: anchor === 'end' ? x - 15 : x + 15, y: y + 5, class: 'ww-label', 'text-anchor': anchor || 'start' }, svg);
    n.textContent = name;
    fit(n);
  }

  function drawLabels(svg) {
    // Jahresraster am Kartenrand
    var grid = el('g', {}, svg);
    for (var yr = 2003; yr <= 2026; yr++) {
      el('line', { x1: 0, x2: G.W, y1: Y(yr), y2: Y(yr), stroke: 'rgba(236,235,229,.06)', 'stroke-width': 1 }, grid);
      el('line', { x1: 0, x2: 10, y1: Y(yr), y2: Y(yr), stroke: 'rgba(236,235,229,.5)', 'stroke-width': 1 }, grid);
      var n = el('text', { x: 14, y: Y(yr) + 5, class: 'ww-label ww-label--year' }, grid);
      n.textContent = yr;
    }
    // Elbe
    var d = '';
    for (var x = 0; x <= G.W; x += 6) d += (x ? 'L' : 'M') + x + ' ' + elbeY(x).toFixed(1);
    el('path', { d: d, fill: 'none', stroke: 'var(--ww-water)', 'stroke-width': 4.5 * Math.max(G.sc, 0.7), opacity: 0.7 }, svg);

    var m = G.W < 640;
    label(svg, 'Nordsee', 0.15, 2004.2, 'ww-label--water');
    label(svg, 'Golfo di Napoli', m ? 0.16 : 0.14, 2007.7, 'ww-label--water');
    peak(svg, 'Vesuvio 1281', 0.80, 2008.3);
    label(svg, 'Berlin', 0.72, 2011.55, 'ww-label--region');
    label(svg, 'Müggelsee', 0.15, 2012.2, 'ww-label--water');
    label(svg, 'Wannsee', 0.85, 2013.25, 'ww-label--water');
    label(svg, 'Hohe Tauern', 0.86, 2013.75, 'ww-label--region');
    peak(svg, 'Hochfeiler 3509', 0.91, 2014.75);
    label(svg, 'Potsdam', 0.86, 2017.2, 'ww-label--town');
    peak(svg, 'Telegrafenberg 94', 0.82, 2017.45);
    label(svg, 'Cordillera de la Costa', 0.105, 2018.0, 'ww-label--region', { rotate: -90 });
    label(svg, 'Erzgebirge', 0.80, 2019.85, 'ww-label--region');
    mine(svg, 0.14, 2019.72, 'Lugau/Oelsnitz', 'start', true);
    label(svg, 'Freiberg', 0.80, 2021.8, 'ww-label--town');
    peak(svg, 'Fichtelberg 1215', 0.13, 2021.0);
    label(svg, 'Elbe', 0.9, 2022.05, 'ww-label--water');
    label(svg, 'Dresden', 0.72, 2022.62, 'ww-label--town');
    label(svg, 'Lausitz', 0.24, 2022.95, 'ww-label--region');
    mine(svg, 0.82, 2024.05, 'Tagebau', G.W < 640 ? 'end' : 'start');
    label(svg, 'Bärwalder See', 0.16, 2025.2, 'ww-label--water');
  }

  /* ------------------------------------------------------------------ */
  /* Wanderweg                                                          */
  /* ------------------------------------------------------------------ */
  function waypoints() {
    // Stationen: der Weg läuft durch den Fuß jedes Wegweisers
    var pts = D.stationen.map(function (s) { return { t: s.von, X: s.x || (s.seite === 'links' ? 0.62 : 0.38), s: s }; });
    // Serpentinen zwischen den Stationen
    [[2003.0, .42], [2004.4, .55], [2005.3, .44], [2007.1, .50], [2007.9, .60], [2008.7, .47], [2009.6, .58],
     [2010.2, .46], [2011.6, .53], [2012.4, .42], [2013.1, .55], [2014.15, .48], [2014.45, .63], [2014.75, .49],
     [2015.05, .63], [2015.45, .5], [2017.15, .44], [2017.8, .58], [2018.5, .44], [2019.2, .57], [2019.85, .46],
     [2021.45, .55], [2022.0, .45], [2022.55, .55], [2023.1, .49], [2024.4, .47], [2025.1, .58], [2025.8, .44],
     [2026.4, .55], [D.heute.jahr, .47]].forEach(function (p) { pts.push({ t: p[0], X: p[1] }); });
    pts.sort(function (a, b) { return a.t - b.t; });
    pts.forEach(function (p) { p.x = p.X * G.W; p.y = Y(p.t); });
    return pts;
  }
  function spline(pts) {
    var d = 'M' + pts[0].x.toFixed(1) + ' ' + pts[0].y.toFixed(1);
    for (var i = 0; i < pts.length - 1; i++) {
      var p0 = pts[Math.max(i - 1, 0)], p1 = pts[i], p2 = pts[i + 1], p3 = pts[Math.min(i + 2, pts.length - 1)];
      d += 'C' + (p1.x + (p2.x - p0.x) / 6).toFixed(1) + ' ' + (p1.y + (p2.y - p0.y) / 6).toFixed(1) + ' ' +
        (p2.x - (p3.x - p1.x) / 6).toFixed(1) + ' ' + (p2.y - (p3.y - p1.y) / 6).toFixed(1) + ' ' +
        p2.x.toFixed(1) + ' ' + p2.y.toFixed(1);
    }
    return d;
  }

  var trail = null;   // { path, progress, walker, len, samples }
  function drawTrail(svg, pts) {
    var d = spline(pts);
    el('path', { d: d, fill: 'none', stroke: 'rgba(20,21,19,.75)', 'stroke-width': 8, 'stroke-linecap': 'round' }, svg);
    el('path', { d: d, fill: 'none', stroke: 'var(--ww-trail)', 'stroke-width': 2.6, 'stroke-dasharray': '9 7', opacity: 0.75 }, svg);
    var prog = el('path', { d: d, fill: 'none', stroke: 'var(--ww-trail)', 'stroke-width': 3.6, 'stroke-linecap': 'round' }, svg);
    var len = prog.getTotalLength();
    prog.style.strokeDasharray = len;
    prog.style.strokeDashoffset = len;
    var samples = [];
    for (var l = 0; l <= len; l += 5) { var p = prog.getPointAtLength(l); samples.push([l, p.x, p.y]); }
    var walker = el('g', {}, svg);
    el('circle', { r: 11, fill: 'rgba(226,103,91,.25)' }, walker);
    el('circle', { r: 6, fill: 'var(--ww-trail)', stroke: '#fff', 'stroke-width': 2 }, walker);
    // Start
    el('circle', { cx: pts[0].x, cy: pts[0].y, r: 7, fill: 'none', stroke: 'var(--ww-trail)', 'stroke-width': 3 }, svg);
    var st = el('text', { x: pts[0].x - 14, y: pts[0].y + 5, class: 'ww-label ww-label--town', 'text-anchor': 'end' }, svg);
    st.textContent = G.W < 640 ? 'Start' : 'Start · Bremerhaven';
    trail = { prog: prog, walker: walker, len: len, samples: samples };
    onScroll();
  }
  function onScroll() {
    if (!trail) return;
    var r = mapEl.getBoundingClientRect();
    var target = window.innerHeight * 0.55 - r.top;
    var s = trail.samples, lo = 0, hi = s.length - 1;
    if (target <= s[0][2]) hi = 0;
    else { for (var i = 0; i < s.length; i++) if (s[i][2] >= target) { hi = i; break; } }
    var p = s[hi];
    trail.prog.style.strokeDashoffset = trail.len - p[0];
    trail.walker.setAttribute('transform', 'translate(' + p[1].toFixed(1) + ' ' + p[2].toFixed(1) + ')');
  }

  /* ------------------------------------------------------------------ */
  /* Wegweiser, Startnummern, heute                                     */
  /* ------------------------------------------------------------------ */
  function drawSigns(svg, pts) {
    var gap = G.W < 640 ? 16 : 24;
    D.stationen.forEach(function (s, i) {
      var p = pts.filter(function (q) { return q.s === s; })[0];
      var left = s.seite === 'links';
      // Pfosten und Wegmarke auf dem Weg
      el('line', { x1: p.x, y1: p.y, x2: p.x + (left ? -gap : gap), y2: p.y, stroke: 'rgba(236,235,229,.6)', 'stroke-width': 2 }, svg);
      if (s.typ === 'beruf') el('rect', { x: p.x - 6, y: p.y - 6, width: 12, height: 12, fill: 'var(--ww-trail)', stroke: '#fff', 'stroke-width': 2 }, svg);
      else { el('circle', { cx: p.x, cy: p.y, r: 7.5, fill: 'var(--ww-panel)', stroke: '#fff', 'stroke-width': 1.5 }, svg);
             el('circle', { cx: p.x, cy: p.y, r: 3.5, fill: 'none', stroke: '#fff', 'stroke-width': 1.5 }, svg); }

      var room = left ? p.x - gap - 8 : G.W - p.x - gap - 8;
      var w = Math.min(room, G.W < 640 ? 170 : 270);
      var b = html('button', 'ww-st ww-st--' + s.typ, mapEl);
      b.type = 'button';
      b.style.top = p.y + 'px';
      b.style.width = w + 'px';
      if (left) b.style.right = (G.W - p.x + gap) + 'px'; else b.style.left = (p.x + gap) + 'px';
      b.setAttribute('aria-haspopup', 'dialog');
      b.innerHTML = '<svg class="ww-vig" viewBox="0 0 240 140" aria-hidden="true">' + (VIG[s.id] || '') + '</svg>' +
        '<span class="ww-sign ww-sign--' + s.typ + '"><span class="ww-sign__years"></span><span class="ww-sign__title"></span><span class="ww-sign__place"></span></span>';
      var plate = b.lastChild;
      plate.children[0].textContent = s.label;
      plate.children[1].textContent = s.titel;
      plate.children[2].textContent = s.ort;
      b.addEventListener('click', function () { openStation(i); });
    });
  }
  function pointAtYear(t) {
    var y = Y(t), s = trail.samples;
    for (var i = 0; i < s.length; i++) if (s[i][2] >= y) return { x: s[i][1], y: s[i][2] };
    return { x: s[s.length - 1][1], y: s[s.length - 1][2] };
  }
  function drawBibs() {
    var lastY = -99;
    D.laeufe.forEach(function (l, i) {
      // Läufe, die zeitlich dicht beieinanderliegen, leicht auseinanderrücken
      var p = pointAtYear(Math.max(l.jahr, T(lastY + 27)));
      lastY = p.y;
      var b = html('button', 'ww-bib', mapEl);
      b.type = 'button';
      b.style.left = p.x + 'px';
      b.style.top = p.y + 'px';
      b.textContent = l.strecke ? l.strecke.replace(' km', '').replace(',195', '') : '♥';
      b.title = l.name;
      b.setAttribute('aria-label', 'Lauf: ' + l.name);
      b.addEventListener('click', function () { openLauf(i); });
    });
    var h = pointAtYear(Math.max(D.heute.jahr, T(lastY + 66)));
    var today = html('div', 'ww-today', mapEl);
    today.style.left = h.x + 'px';
    today.style.top = h.y + 'px';
    today.innerHTML = '<img alt="Ralf A. Moskwa"><span>Hier stehe ich heute</span>';
    today.querySelector('img').src = img(D.heute.bild);
  }

  /* ------------------------------------------------------------------ */
  /* Detailfenster                                                      */
  /* ------------------------------------------------------------------ */
  function dialogShell(kicker) {
    dlg.innerHTML = '<div class="ww-dlg__bar"><span></span>' +
      '<button type="button" class="ww-btn" data-act="prev" aria-label="Vorheriger Wegweiser">←</button>' +
      '<button type="button" class="ww-btn" data-act="next" aria-label="Nächster Wegweiser">→</button>' +
      '<button type="button" class="ww-btn" data-act="close" aria-label="Schließen">✕</button></div>' +
      '<div class="ww-dlg__body"></div>';
    dlg.querySelector('.ww-dlg__bar span').textContent = kicker;
    dlg.querySelector('[data-act="close"]').addEventListener('click', function () { dlg.close(); });
    return dlg.querySelector('.ww-dlg__body');
  }
  function show() {
    if (!dlg.open) { if (dlg.showModal) dlg.showModal(); else dlg.setAttribute('open', ''); }
    dlg.scrollTop = 0;
  }
  function nav(prev, next) {
    var bp = dlg.querySelector('[data-act="prev"]'), bn = dlg.querySelector('[data-act="next"]');
    if (prev) bp.addEventListener('click', prev); else { bp.disabled = true; bp.hidden = !next; }
    if (next) bn.addEventListener('click', next); else { bn.disabled = true; bn.hidden = !prev; }
  }
  function gallery(body, list, alt) {
    if (!list || !list.length) return;
    var g = html('div', 'ww-gallery', body);
    list.forEach(function (n) { var im = html('img', '', g); im.loading = 'lazy'; im.alt = alt; im.src = img(n); });
  }
  function openStation(i) {
    var s = D.stationen[i];
    var body = dialogShell((s.typ === 'beruf' ? 'Beruf' : 'Ausbildung') + ' · Wegweiser ' + (i + 1) + ' von ' + D.stationen.length);
    var y = html('p', 'ww-dlg__years', body); y.textContent = s.label;
    var h = html('h3', '', body); h.textContent = s.titel;
    var o = html('p', 'ww-dlg__place', body); o.textContent = s.ort;
    gallery(body, s.bilder, s.titel);
    var c = html('div', '', body); c.innerHTML = s.html;   // Texte stammen aus stationen.js
    nav(i > 0 ? function () { openStation(i - 1); } : null,
        i < D.stationen.length - 1 ? function () { openStation(i + 1); } : null);
    show();
  }
  function openLauf(i) {
    var l = D.laeufe[i];
    var body = dialogShell('Startnummer · Lauf ' + (i + 1) + ' von ' + D.laeufe.length);
    var y = html('p', 'ww-dlg__years', body); y.textContent = [Math.floor(l.jahr), l.strecke, l.zeit].filter(Boolean).join(' · ');
    var h = html('h3', '', body); h.textContent = l.name;
    html('p', 'ww-dlg__place', body);
    var im = html('img', 'ww-photo', body); im.alt = l.name; im.src = img(l.bild);
    nav(i > 0 ? function () { openLauf(i - 1); } : null,
        i < D.laeufe.length - 1 ? function () { openLauf(i + 1); } : null);
    show();
  }
  if (dlg) dlg.addEventListener('click', function (e) { if (e.target === dlg) dlg.close(); });

  /* ------------------------------------------------------------------ */
  /* Aufbau und Neuaufbau bei Größenänderung                            */
  /* ------------------------------------------------------------------ */
  function build() {
    if (G.cleanup) G.cleanup.forEach(function (f) { f(); });
    var W = mapEl.clientWidth;
    G = { W: W, sc: clamp(W / 1000, 0.5, 1.1), ppy: W < 640 ? 175 : 155, top: 30, cleanup: [] };
    G.H = Math.round(Y(T1));
    mapEl.style.height = G.H + 'px';
    mapEl.innerHTML = '';
    var svg = el('svg', { class: 'ww-map__svg', viewBox: '0 0 ' + W + ' ' + G.H, 'aria-hidden': 'true' });
    mapEl.appendChild(svg);
    drawTerrain(svg);
    drawLabels(svg);
    var pts = waypoints();
    drawTrail(svg, pts);
    drawSigns(svg, pts);
    drawBibs();
  }
  var lastW = 0, timer;
  function resize() {
    var w = mapEl.clientWidth;
    if (Math.abs(w - lastW) < 2) return;
    lastW = w;
    build();
  }
  resize();
  window.addEventListener('resize', function () { clearTimeout(timer); timer = setTimeout(resize, 200); });
  window.addEventListener('scroll', onScroll, { passive: true });
})();
