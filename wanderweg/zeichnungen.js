/* Illustrationen der Stationen: Strichzeichnungen im Stil der Karte (viewBox 0 0 240 140).
   Klassen: n = nur Linie · d = feine Nebenlinie · a = Akzent (Wegrot) · w = Wasser
            k = dunkle Fläche · p = helle Fläche */
(function () {
  function waves(y, x0, x1) {
    var d = 'M' + x0 + ' ' + y + 'q6-5 12 0';
    for (var x = x0 + 12; x < x1 - 12; x += 12) d += 't12 0';
    return '<path class="w" d="' + d + '"/>';
  }
  function fir(x, y, s) {   // Nadelbaum, Fußpunkt (x, y)
    s = s || 1;
    return '<path d="M' + x + ' ' + (y - 30 * s) + 'l' + (-7 * s) + ' ' + (13 * s) + 'h' + (4 * s) + 'l' + (-6 * s) + ' ' + (11 * s) +
      'h' + (18 * s) + 'l' + (-6 * s) + ' ' + (-11 * s) + 'h' + (4 * s) + 'z"/><path class="n" d="M' + x + ' ' + (y - 6 * s) + 'V' + y + '"/>';
  }
  function gable(x, w, h) { // Giebelhaus auf der Grundlinie y=112
    return '<path d="M' + x + ' 112V' + (112 - h) + 'l' + (w / 2) + ' ' + (-w * 0.4) + 'l' + (w / 2) + ' ' + (w * 0.4) + 'V112z"/>';
  }
  var V = {};

  /* Zeit auf See: Hafen mit Leuchtturm und Minenjagdboot */
  V.see =
    '<path class="d" d="M146 30q4-5 8 0q4-5 8 0M26 40q3-4 6 0q3-4 6 0M60 22q3-4 6 0q3-4 6 0"/>' +
    '<path d="M162 104h74v12h-74z"/><path class="d" d="M170 104v-5h4v5M224 104v-5h4v5"/>' +
    '<path d="M188 104l4-52h14l4 52z"/>' +
    '<path class="a" d="M190.8 68h16.4l.7 10h-17.8zM189.4 87h19.2l.7 9h-20.6z"/>' +
    '<rect x="187" y="42" width="24" height="10"/><path d="M190 42l9-10l9 10z"/><circle class="a" cx="199" cy="47" r="2.6"/>' +
    '<path class="d" d="M183 47h-18M215 47h18M185 40l-12-7M213 40l12-7"/>' +
    '<path d="M46 94h104l-10 17H60z"/><path class="d" d="M56 101h86"/>' +
    '<rect x="80" y="80" width="42" height="14"/><rect x="88" y="68" width="20" height="12"/>' +
    '<path class="n" d="M98 68V38M89 47h18M93 54h10M98 38l-34 56M98 38l50 56"/>' +
    '<path class="a" d="M98 38h9l-3 3l3 3h-9z"/>' +
    '<circle cx="115" cy="75" r="5"/><path class="n" d="M62 94v-7h10"/>' +
    '<path class="d" d="M86 87h5M96 87h5M106 87h5M92 74h4M100 74h4"/>' +
    waves(118, 4, 236) + waves(129, 16, 224);

  /* NATO-Hauptquartier Neapel: Küste, Vesuv, Schirmpinie, großes Hauptquartier */
  V.neapel =
    '<path class="d" d="M96 70L150 26l9 7l8-8l8 6L236 74"/><path class="d" d="M166 20q5-7-1-11q8-3 5-9"/>' +
    '<path class="n" d="M4 100h232"/>' +
    '<rect x="50" y="64" width="140" height="36"/><rect x="98" y="46" width="44" height="54"/>' +
    '<path class="d" stroke-dasharray="4 4" d="M57 72h36M57 80h36M57 88h36M147 72h36M147 80h36M147 88h36M104 76h32"/>' +
    '<rect class="k" x="113" y="84" width="14" height="16"/>' +
    '<path class="w" d="M120 50l2.6 6.4l6.4 2.6l-6.4 2.6l-2.6 6.4l-2.6-6.4l-6.4-2.6l6.4-2.6z"/>' +
    '<path class="n" d="M120 46V34M112 40h16"/><circle class="n" cx="120" cy="32" r="2.5"/>' +
    '<path class="n" d="M58 100V84M72 100V84M86 100V84M154 100V84M168 100V84M182 100V84"/>' +
    '<path class="a" d="M58 84h8v5h-8zM86 84h8v5h-8zM168 84h8v5h-8z"/>' +
    '<path class="p" d="M72 84h8v5h-8zM154 84h8v5h-8zM182 84h8v5h-8z"/>' +
    '<path class="n" d="M26 100V64M26 74l-8-8M26 70l9-8"/><path d="M4 60q22-22 46 0q-23 7-46 0z"/>' +
    '<path class="n" d="M214 100V76M214 82l6-6"/><path d="M200 72q14-14 30 0q-15 5-30 0z"/>' +
    waves(112, 4, 236) + waves(123, 16, 224);

  /* Bachelor: Berlin-Mitte mit Fernsehturm, Dom und Rotem Rathaus */
  V.bachelor =
    '<path class="d" d="M24 28q6-8 14-2q10-6 14 4M176 22q6-8 14-2q10-6 14 4"/>' +
    '<path class="n" d="M6 112h228"/>' +
    '<path d="M117 112l2-60h2l2 60z"/><circle cx="120" cy="45" r="9.5"/><path class="d" d="M110.6 45h18.8M112 41h16"/>' +
    '<path class="n" d="M120 35.5V6"/><path class="a" d="M118.7 12h2.6v6h-2.6zM118.7 24h2.6v6h-2.6z"/>' +
    '<rect x="26" y="86" width="64" height="26"/><path d="M42 86q0-24 16-26q16 2 16 26z"/>' +
    '<path class="n" d="M58 60v-9"/><circle cx="58" cy="49" r="2.2"/>' +
    '<path d="M26 86V74q5-9 10 0v12zM80 86V74q5-9 10 0v12z"/>' +
    '<path class="d" d="M34 94v18M42 94v18M50 94v18M58 94v18M66 94v18M74 94v18M82 94v18M50 72q8-6 16 0"/>' +
    '<rect x="150" y="88" width="66" height="24"/><rect x="175" y="58" width="16" height="30"/><path d="M173 58h20l-4-7h-12z"/>' +
    '<path class="n" d="M183 51V40"/><path class="a" d="M183 40h8v5h-8z"/>' +
    '<path class="d" stroke-dasharray="3 3" d="M155 96h16M155 104h16M195 96h16M195 104h16M179 66h8M179 74h8"/>' +
    '<rect x="98" y="96" width="12" height="16"/><rect x="132" y="90" width="12" height="22"/>' +
    '<path class="d" stroke-dasharray="2 3" d="M101 101h6M101 106h6M135 96h6M135 102h6M135 108h6"/>' +
    waves(124, 30, 210);

  /* Master: Berlin-Tiergarten mit Brandenburger Tor, Siegessäule und Reichstag */
  V.master =
    '<path class="n" d="M6 112h228"/>' +
    '<rect x="16" y="68" width="84" height="10"/><rect x="32" y="56" width="52" height="12"/>' +
    '<path d="M20 78h6v34h-6zM34 78h6v34h-6zM48 78h6v34h-6zM62 78h6v34h-6zM76 78h6v34h-6zM90 78h6v34h-6z"/>' +
    '<path class="n" d="M48 56v-5h5l2-7l3 7h5l2-6l2 6v5"/><path class="a" d="M58 36l2 5h-4z"/>' +
    '<rect x="114" y="102" width="22" height="10"/><rect x="118" y="94" width="14" height="8"/><rect x="122" y="50" width="6" height="44"/>' +
    '<path class="d" d="M122 62h6M122 74h6M122 86h6"/>' +
    '<path class="a" d="M125 32l2 6l7-4l-4 8h-10l-4-8l7 4zM123.5 42h3v8h-3z"/>' +
    '<rect x="148" y="86" width="86" height="26"/><rect x="148" y="76" width="12" height="10"/><rect x="222" y="76" width="12" height="10"/>' +
    '<rect x="174" y="80" width="34" height="6"/><path class="n" d="M176 80q15-27 30 0"/><path class="d" d="M183 80q8-20 16 0M191 56.5V80M178 72h26"/>' +
    '<path class="n" d="M191 56.5V48"/><path class="a" d="M191 48h8v5h-8z"/>' +
    '<path d="M176 94l15-8l15 8z"/><path class="d" d="M180 94v18M186 94v18M192 94v18M198 94v18M204 94v18"/>' +
    '<path class="d" stroke-dasharray="3 3" d="M153 96h18M153 104h18M211 96h18M211 104h18"/>' +
    '<path class="d" d="M104 112q3-14 8 0M138 112q3-12 7 0"/>';

  /* GFZ: Telegrafenberg mit Großem Refraktor und Einsteinturm */
  V.gfz =
    '<path d="M4 122q58-46 116-44q58-2 116 44z"/>' +
    '<rect x="88" y="60" width="60" height="22"/><path d="M95 60a23 23 0 0 1 46 0z"/>' +
    '<path class="n" d="M114 38v22M122 38v22"/><path class="k" d="M114.8 39.5h6.4V60h-6.4z"/>' +
    '<rect class="k" x="113" y="70" width="10" height="12"/><path class="d" stroke-dasharray="3 3" d="M93 68h14M129 68h14"/>' +
    '<path d="M168 96h34v-9h-34z"/><path d="M177 87V60h14v27z"/><path d="M177 60a7 7 0 0 1 14 0z"/>' +
    '<path class="d" d="M184 66v4M184 74v4M172 91.5h6M192 91.5h6"/>' +
    fir(28, 116, 1) + fir(48, 104, 1.1) + fir(68, 96, .9) + fir(160, 100, 1) + fir(214, 112, 1.1) + fir(226, 120, .8) +
    '<path class="d" d="M30 20h2M52 34h2M84 14h2M150 22h2M206 30h2M178 12h2M120 10h2"/>' +
    '<path class="d" d="M118 26L96 6M124 26l26-20"/>';

  /* Promotion: chilenische Küstenkordillere, von der Wüste (Kaktus) zum Regenwald (Araukarie) */
  V.promotion =
    '<circle class="n" cx="40" cy="30" r="10"/><path class="d" d="M40 12v-6M40 54v-6M22 30h-6M64 30h-6M27 17l-4-4M53 17l4-4M27 43l-4 4M53 43l4 4"/>' +
    '<path class="n" d="M168 34q2-12 14-10q8-10 20-2q14-2 14 12z"/><path class="w" d="M176 42l-3 8M188 42l-3 8M200 42l-3 8M212 42l-3 8"/>' +
    '<path class="d" d="M4 86l32-30l20 16l28-36l28 32l26-22l32 28l30-20l36 32"/>' +
    '<path d="M4 122V98l34-26l26 20l30-32l34 34l28-18l40 26l40-14v34z"/>' +
    '<path class="d" d="M94 60l-6 18M94 60l8 22M38 72l-4 12M156 76l4 12"/>' +
    '<g class="n" stroke-width="4"><path d="M28 122V88M28 106h-9V96M28 100h9V88"/></g>' +
    '<path class="n" stroke-width="2.5" d="M206 122V74"/>' +
    '<path class="n" d="M186 88q20-16 40 0M182 78q24-20 48 0M190 68q16-13 32 0"/>' +
    '<path class="d" d="M60 118q4-8 8 0M120 116q4-8 8 0M150 120q4-8 8 0"/>';

  /* GeoMAP: alter Kohlenschacht im Erzgebirge mit Fördergerüst und Halde */
  V.lfulg =
    '<path class="d" d="M118 112l44-46l14 10l12-8l44 44"/><path class="d" d="M150 80l6 10M176 76l-4 12M200 82l6 12"/>' +
    '<path class="n" d="M6 112h228"/>' +
    '<rect x="26" y="78" width="56" height="34"/><path d="M22 78l32-15l32 15z"/>' +
    '<path class="d" d="M34 112V96q5-6 10 0v16M62 112V96q5-6 10 0v16"/><circle class="n" cx="54" cy="72" r="3"/>' +
    '<path class="n" d="M96 112l9-74M130 112l-9-74M102 38h22"/>' +
    '<path class="d" d="M98 98l30-14M128 98L98 84M101 72l23-12M125 72l-23-12M100 84h26M103 60h20"/>' +
    '<circle cx="113" cy="29" r="10"/><path class="d" d="M113 19v20M103 29h20M106 22l14 14M120 22l-14 14"/>' +
    '<path class="n" d="M105 38L60 64"/><path class="d" d="M104.5 24L58 62"/>' +
    '<path d="M148 112l3-56h9l3 56z"/><path class="d" d="M156 48q6-8-1-13q9-4 5-12"/>' +
    '<path d="M178 99h26l-4 9h-18z"/><path class="k" d="M181 99q10-10 20 0z"/><circle cx="185" cy="110" r="2.2"/><circle cx="197" cy="110" r="2.2"/>' +
    '<path class="d" d="M168 112.5h64"/>' +
    fir(222, 100, .8) + fir(14, 112, .7);

  /* G.U.B.: Dresden mit Frauenkirche an der Elbe */
  V.gub =
    '<path class="n" d="M6 112h228"/>' +
    gable(18, 22, 18) + gable(42, 26, 24) + gable(172, 26, 24) + gable(200, 22, 18) +
    '<path class="d" stroke-dasharray="3 3" d="M23 102h12M48 96h14M48 104h14M178 96h14M178 104h14M205 102h12"/>' +
    '<path d="M82 112V78h76v34z"/>' +
    '<path d="M82 78V60q6-10 12 0v18zM146 78V60q6-10 12 0v18z"/><path class="n" d="M88 53v-6M152 53v-6"/>' +
    '<path d="M92 78q-3-24 14-36q7-5 7-12h14q0 7 7 12q17 12 14 36z"/>' +
    '<rect x="114" y="16" width="12" height="14"/><path d="M112.5 16q7.500-12 15 0z"/><path class="n" d="M120 9V2M117 5h6"/>' +
    '<path class="d" d="M120 31v46M106 46q-4 14-4 31M134 46q4 14 4 31M117 20v8M123 20v8"/>' +
    '<path class="d" d="M90 112V94q4-6 8 0v18M105 112V92q4-6 8 0v20M127 112V92q4-6 8 0v20M142 112V94q4-6 8 0v18"/>' +
    '<rect class="k" x="116" y="98" width="8" height="14"/>' +
    waves(123, 4, 236) + waves(133, 16, 224);

  /* LEAG: Braunkohlentagebau mit Schaufelradbagger, Filterbrunnen und abgesenktem Grundwasser */
  V.leag =
    '<path d="M4 122V60h46l8 14h28l8 14h30l8 16h104v18z"/>' +
    '<path class="k" d="M132 110h104v12H132z"/>' +
    '<path class="d" d="M236 62h-14l-6 12h-10M4 70h40M4 96h78"/>' +
    '<path class="w" stroke-dasharray="5 4" d="M4 78q52 2 88 20q16 8 26 10"/><path class="w" d="M10 71l4 6l4-6z"/>' +
    '<path class="w" d="M14 60V46M30 60V46M46 60V46"/><path class="n" d="M11 46h6M27 46h6M43 46h6"/>' +
    '<rect x="152" y="96" width="46" height="8" rx="4"/><path class="d" d="M158 100h34"/>' +
    '<path d="M160 96V78h30v18z"/><rect class="k" x="166" y="82" width="8" height="6"/>' +
    '<path class="n" d="M175 78V40M175 62L112 80M175 48L112 80M175 62l44 8M175 40l44 30"/>' +
    '<path class="d" d="M175 40L112 80M160 66v-8M145 70v-10M130 75v-8"/>' +
    '<rect x="212" y="66" width="16" height="11"/>' +
    '<circle cx="106" cy="82" r="13"/><circle class="n" cx="106" cy="82" r="4"/>' +
    '<path class="a" d="M104 67h4v-4h-4zM104 101h4v-4h-4zM89 80v4h4v-4zM119 80v4h4v-4zM94 70l3 3l-3 3l-3-3zM118 70l3 3l-3 3l-3-3zM94 88l3 3l-3 3l-3-3zM118 88l3 3l-3 3l-3-3z"/>';

  window.WANDERWEG_VIGNETTEN = V;
})();
