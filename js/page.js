/* Does rain keep Britain at home? Every UK constituency at every general election 1945 to 2024 on a plain MapLibre base
 * map (OpenFreeMap Positron), coloured by rain in polling hours, with an election slider, search, layers and popups
 * showing turnout and the rain hour by hour. Dr Tristan Hotham, Independent researcher, 2026. MIT licence. */
(function () {
  'use strict';
  const STYLE = 'https://tiles.openfreemap.org/styles/positron';
  const esc = s => String(s ?? '').replace(/[&<>"]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));
  const norm = s => String(s).normalize('NFD').replace(/[̀-ͯ]/g, '').toLowerCase();
  const small = matchMedia('(max-width:600px)').matches;
  const FAMN = { CON: 'Conservative', LAB: 'Labour', LIB: 'Liberal / Lib Dem', SNP: 'SNP', PC: 'Plaid Cymru', ULS: 'Ulster unionist', IRN: 'Irish nationalist / SDLP', SF: 'Sinn Féin', SPK: 'Speaker', OTH: 'Other', GRN: 'Green', REF: 'Reform UK', ALLY: 'National Liberal etc.' };
  const WHY = ['', '1945 poll postponed for wakes week: left out', 'university seat: left out', 'uncontested: no turnout'];
  let map, D, H = null, ei = 20, feats = [], timer = null;
  document.getElementById('theme').addEventListener('click', () => { const r = document.documentElement, d = r.dataset.theme ? r.dataset.theme === 'dark' : matchMedia('(prefers-color-scheme: dark)').matches; r.dataset.theme = d ? 'light' : 'dark'; });
  const T = document.getElementById('title'); const fold = f => T.classList.toggle('folded', f);
  if (small) fold(true);
  document.getElementById('unfold').addEventListener('click', () => fold(false));
  document.getElementById('fold').addEventListener('click', () => fold(true));
  const slider = document.getElementById('el'), yr = document.getElementById('yr');

  function cls(mm) { const b = D.classes.bins; for (let i = b.length - 2; i >= 0; i--) if (mm >= b[i]) return i; return 0; }

  function keyBox() {
    const E = D.elections[ei];
    document.getElementById('nat').innerHTML = `<b>${esc(E.s)}</b> · polls ${esc(E.hrs)}h<br>mean rain <b>${E.rain.toFixed(1)}</b> mm · ${E.wet5.toFixed(0)}% of seats 5 mm or more · turnout ${E.turnout.toFixed(1)}%`;
    document.querySelectorAll('#bars i').forEach((b, i) => b.classList.toggle('on', i === ei));
  }

  function refresh() {
    feats = D.byE[ei].map(i => { const r = D.rows[i]; return { type: 'Feature', properties: { i, c: cls(r[4] / 10), x: r[11] ? 1 : 0, name: r[1] }, geometry: { type: 'Point', coordinates: [r[2], r[3]] } }; });
    map.getSource('s').setData({ type: 'FeatureCollection', features: feats });
    slider.value = ei; yr.textContent = D.elections[ei].s; keyBox(); layerVis();
  }

  function layerVis() {
    const on = id => document.getElementById(id).checked;
    const parts = [];
    if (on('lyW')) parts.push(['all', ['>', ['get', 'c'], 0], ['==', ['get', 'x'], 0]]);
    if (on('lyD')) parts.push(['all', ['==', ['get', 'c'], 0], ['==', ['get', 'x'], 0]]);
    if (on('lyX')) parts.push(['==', ['get', 'x'], 1]);
    const f = parts.length ? ['any', ...parts] : ['==', 1, 0];
    map.setFilter('seats', f); map.setFilter('seats-halo', f); map.setFilter('seat-lbl', f);
    map.setLayoutProperty('seat-lbl', 'visibility', on('lyL') ? 'visible' : 'none');
    for (const l of map.getStyle().layers) if (l.type === 'symbol' && l.id !== 'seat-lbl') map.setLayoutProperty(l.id, 'visibility', on('lyB') ? 'visible' : 'none');
    document.getElementById('key').style.display = on('lyK') ? '' : 'none';
  }

  function spark(h, hrs) {      // 24 hourly bars for polling day, polling hours shaded
    const [a, z] = hrs.split(' to ').map(Number), W = 270, Hh = 54, bw = W / 24, mx = Math.max(20, ...h);
    let s = `<svg class="spark" width="${W}" height="${Hh + 14}" viewBox="0 0 ${W} ${Hh + 14}" role="img" aria-label="Rain hour by hour on polling day">`;
    s += `<rect x="${a * bw}" y="0" width="${(z - a) * bw}" height="${Hh}" fill="#EEF3F8"/>`;
    h.forEach((v, k) => { const hh = Hh * v / mx; if (v > 0) s += `<rect x="${k * bw + 1}" y="${Hh - hh}" width="${bw - 2}" height="${hh}" fill="#2B67A3"/>`; });
    s += `<line x1="0" x2="${W}" y1="${Hh}" y2="${Hh}" stroke="#B7AE9C"/>`;
    for (const t of [0, 6, 12, 18, 24]) s += `<text x="${Math.min(W - 8, t * bw)}" y="${Hh + 12}" font-size="10" fill="#6B655B" font-family="IBM Plex Mono,monospace">${String(t).padStart(2, '0')}</text>`;
    return s + '</svg>';
  }

  function popup(i, ll) {
    const r = D.rows[i], E = D.elections[r[0]];
    const show = () => {
      const h = H ? H[`${r[0]}|${r[8]}`] : null;
      const tr = r[5] == null ? '<span class="nt">no contest</span>' : (r[5] / 10).toFixed(1) + '%';
      const diff = r[5] != null ? ((r[5] / 10) - E.turnout) : null;
      new maplibregl.Popup({ maxWidth: '320px' }).setLngLat(ll).setHTML(`<b class="t">${esc(r[1])}</b><div class="nt">${esc(E.e)} general election · ${esc(E.date)}</div>
        <table><tr><td>Rain while polls were open (${esc(E.hrs)}h)</td><td class="r lc">${(r[4] / 10).toFixed(1)} mm</td></tr>
        <tr><td>Rain over the whole day</td><td class="r">${(r[10] / 10).toFixed(1)} mm</td></tr>
        <tr><td>Temperature in polling hours</td><td class="r">${(r[6] / 10).toFixed(1)} °C</td></tr>
        <tr><td>Turnout</td><td class="r">${tr}</td></tr>
        <tr><td>UK average turnout (contested seats)</td><td class="r">${E.turnout.toFixed(1)}%</td></tr>
        ${r[9] != null ? `<tr><td>Same seat name at the previous election</td><td class="r">${(r[9] / 10).toFixed(1)}%</td></tr>` : ''}
        <tr><td>Won by</td><td class="r">${esc(r[7] >= 0 ? (FAMN[D.fams[r[7]]] || D.fams[r[7]]) : '')}</td></tr></table>
        ${h ? `<div class="nt">Rain hour by hour on polling day (shaded: polls open)</div>${spark(h, E.hrs)}` : ''}
        ${r[11] ? `<div class="nt">${esc(WHY[r[11]])}</div>` : ''}
        ${diff != null ? `<div class="nt">Turnout ${Math.abs(diff).toFixed(1)} points ${diff >= 0 ? 'above' : 'below'} the UK average. One seat cannot show a rain effect: the study compares thousands.</div>` : ''}
        <div class="nt">Rain: ERA5 reanalysis via Open-Meteo (CC BY 4.0), grid cell nearest the seat point (about 30 km resolution). Turnout: Who won here? (UK Parliament, House of Commons Library).</div>`).addTo(map);
    };
    if (H) show(); else fetch('data/site/hours.json').then(x => x.json()).then(h => { H = h; show(); }).catch(() => show());
  }

  function setup() {
    D.byE = D.elections.map(() => []); D.rows.forEach((r, i) => D.byE[r[0]].push(i));
    const sw = document.getElementById('sw'); sw.innerHTML = D.classes.labs.map((l, k) => `<span><i style="background:${D.classes.cols[k]}"></i>${esc(l.replace(' (under 0.1 mm)', ''))}</span>`).join('');
    const mx = Math.max(...D.elections.map(e => e.rain));
    document.getElementById('bars').innerHTML = D.elections.map((e, k) => `<i style="height:${Math.max(3, 100 * e.rain / mx)}%" title="${esc(e.s)}: ${e.rain.toFixed(1)} mm" data-k="${k}"></i>`).join('');
    document.querySelectorAll('#bars i').forEach(b => b.addEventListener('click', () => { stop(); ei = +b.dataset.k; refresh(); }));
    const before = (map.getStyle().layers.find(l => l.type === 'symbol') || {}).id;
    map.addSource('s', { type: 'geojson', data: { type: 'FeatureCollection', features: [] }, attribution: 'Rain: ERA5 via <a href="https://open-meteo.com/">Open-Meteo.com</a> (CC BY 4.0) · Seats: Who won here? (UK Parliament)' });
    const col = ['case', ['==', ['get', 'x'], 1], '#FFFFFF', ['match', ['get', 'c'], ...D.classes.cols.flatMap((c, k) => [k, c]), '#999']];
    const rad = e => ['interpolate', ['linear'], ['zoom'], 4, 3 + e, 7, 5 + e, 10, 8 + e, 13, 11 + e];
    map.addLayer({ id: 'seats-halo', type: 'circle', source: 's', paint: { 'circle-radius': rad(1.4), 'circle-color': '#fff', 'circle-opacity': 0.85 } }, before);
    map.addLayer({ id: 'seats', type: 'circle', source: 's', paint: { 'circle-radius': rad(0), 'circle-color': col, 'circle-stroke-color': ['case', ['==', ['get', 'x'], 1], '#22201C', '#8C8577'], 'circle-stroke-width': ['case', ['==', ['get', 'x'], 1], 1.4, 0.5], 'circle-opacity': 0.95 } }, before);
    map.addLayer({ id: 'seat-lbl', type: 'symbol', source: 's', minzoom: 7.5, layout: { 'text-field': ['get', 'name'], 'text-size': 11, 'text-font': ['Noto Sans Regular'], 'text-offset': [0, 1.1], 'text-anchor': 'top', 'text-optional': true }, paint: { 'text-color': '#4A453D', 'text-halo-color': '#fff', 'text-halo-width': 1.3 } });
    map.on('click', 'seats', e => { const f = e.features[0]; popup(f.properties.i, f.geometry.coordinates); });
    map.on('mouseenter', 'seats', () => map.getCanvas().style.cursor = 'pointer'); map.on('mouseleave', 'seats', () => map.getCanvas().style.cursor = '');
    slider.addEventListener('input', () => { stop(); ei = +slider.value; refresh(); });
    const play = document.getElementById('play');
    play.addEventListener('click', () => { if (timer) { stop(); return; } play.textContent = '❚❚'; play.setAttribute('aria-label', 'Pause');
      if (ei >= D.elections.length - 1) ei = -1; timer = setInterval(() => { ei++; refresh(); if (ei >= D.elections.length - 1) stop(); }, 1100); ei++; refresh(); });
    const lp = document.getElementById('lp'), btn = document.getElementById('lyrBtn');
    btn.addEventListener('click', e => { e.stopPropagation(); const o = lp.classList.toggle('open'); btn.setAttribute('aria-expanded', o); });
    document.addEventListener('click', e => { if (!lp.contains(e.target) && e.target !== btn) { lp.classList.remove('open'); btn.setAttribute('aria-expanded', false); } });
    ['lyW', 'lyD', 'lyX', 'lyL', 'lyB', 'lyK'].forEach(id => document.getElementById(id).addEventListener('change', layerVis));
    refresh();
  }
  function stop() { if (timer) clearInterval(timer); timer = null; const p = document.getElementById('play'); p.textContent = '▶'; p.setAttribute('aria-label', 'Play through the elections'); }

  function setupSearch() {
    const q = document.getElementById('q'), sug = document.getElementById('sug'); let items = [], k = -1;
    const by = {}; D.rows.forEach((r, i) => { (by[r[1]] = by[r[1]] || []).push(i); });
    const idx = Object.keys(by).map(n => ({ n, nn: norm(n), ix: by[n] }));
    const span = it => { const ys = it.ix.map(i => D.elections[D.rows[i][0]].e.slice(-4)); return ys[0] === ys[ys.length - 1] ? ys[0] : `${ys[0]} to ${ys[ys.length - 1]}`; };
    const show = () => { const v = norm(q.value.trim()); sug.innerHTML = ''; k = -1; if (v.length < 2) { sug.style.display = 'none'; return; }
      items = idx.filter(x => x.nn.startsWith(v)).concat(idx.filter(x => !x.nn.startsWith(v) && x.nn.includes(v))).slice(0, 12);
      items.forEach((it, j) => { const li = document.createElement('li'); li.setAttribute('role', 'option'); li.innerHTML = `${esc(it.n)} <span>${span(it)}</span>`; li.addEventListener('mousedown', e => { e.preventDefault(); pick(j); }); sug.appendChild(li); });
      sug.style.display = items.length ? 'block' : 'none'; };
    const pick = j => { const it = items[j]; if (!it) return; q.value = it.n; sug.style.display = 'none'; fold(true); stop();
      let i = it.ix.find(i => D.rows[i][0] === ei); if (i == null) { i = it.ix[it.ix.length - 1]; ei = D.rows[i][0]; refresh(); }
      const r = D.rows[i]; map.flyTo({ center: [r[2], r[3]], zoom: 9, duration: 1200, offset: [0, small ? 170 : 230] }); map.once('moveend', () => popup(i, [r[2], r[3]])); };
    q.addEventListener('input', show);
    q.addEventListener('keydown', e => { const lis = [...sug.children];
      if (e.key === 'ArrowDown' || e.key === 'ArrowUp') { e.preventDefault(); k = Math.max(0, Math.min(lis.length - 1, k + (e.key === 'ArrowDown' ? 1 : -1))); lis.forEach((l, i) => l.setAttribute('aria-selected', i === k)); }
      else if (e.key === 'Enter') { e.preventDefault(); if (!items.length) show(); pick(k < 0 ? 0 : k); } else if (e.key === 'Escape') sug.style.display = 'none'; });
    q.addEventListener('blur', () => setTimeout(() => sug.style.display = 'none', 150));
  }

  fetch('data/site/seats.json').then(r => r.json()).then(d => {
    D = d;
    const m0 = new maplibregl.Map({ container: 'map', style: STYLE, attributionControl: { compact: true }, maxZoom: 14, renderWorldCopies: false,
      center: small ? [-3.4, 54.6] : [-4.6, 54.5], zoom: small ? 4.3 : 5.15 });
    return new Promise((res, rej) => { m0.once('load', () => res(m0)); m0.once('error', e => { if (!m0.loaded()) rej(e.error || e); }); });
  }).then(mm => {
    map = mm; window.__map = mm;
    mm.on('error', e => { const er = e && e.error; if (er && (er.name === 'AbortError' || /abort/i.test(er.message || ''))) return; console.error(er || e); });
    const n = document.getElementById('nojs'); if (n) n.remove();
    mm.addControl(new maplibregl.NavigationControl({ showCompass: false }), 'bottom-right');
    const foldAt = () => document.querySelectorAll('.maplibregl-ctrl-attrib.maplibregl-compact').forEach(at => { at.classList.remove('maplibregl-compact-show'); at.removeAttribute('open'); });
    mm.once('idle', foldAt); setTimeout(foldAt, 1500);
    setup(); setupSearch();
  }).catch(e => { console.error(e); const n = document.getElementById('nojs'); if (n) n.textContent = 'The map could not load: ' + e.message; });
})();
