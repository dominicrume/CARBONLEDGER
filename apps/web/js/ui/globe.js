// Rotatable globe. Countries are coloured by queue status: green cleared, amber in progress, a calm muted tone waiting.
// Drag to turn it, tap a country for details. Needs d3 and topojson-client (loaded in index.html).
import { WORLD } from '../data/geo.js';

// Countries too small for the 1:50m map, drawn as markers instead: [lon, lat]
const POINTS = { TUV: [179.2, -8.5] };

export function createGlobe(canvas, { statusOf, onSelect }) {
  const d3 = window.d3, topo = window.topojson;
  if (!d3 || !topo) return null;
  const features = topo.feature(WORLD, WORLD.objects.countries).features;
  const extra = Object.entries(POINTS).map(([id, c]) => ({ id, point: c }));
  const projection = d3.geoOrthographic().clipAngle(90).precision(0.6);
  const ctx = canvas.getContext('2d');
  const path = d3.geoPath(projection, ctx);
  let size = 0, rotate = [-20, -15], spinning = true, selected = null, raf = 0, last = 0;

  const css = name => getComputedStyle(canvas).getPropertyValue(name).trim();
  function fit() {
    const dpr = window.devicePixelRatio || 1, w = canvas.clientWidth;
    if (!w) return false;
    size = w; canvas.width = w * dpr; canvas.height = w * dpr; ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    projection.translate([w / 2, w / 2]).scale(w / 2 - 2);
    return true;
  }

  function draw() {
    if (!size && !fit()) return;
    projection.rotate(rotate);
    const col = { cleared: css('--ok'), current: css('--warn'), waiting: css('--globe-wait') };   // waiting is not an error: no alarm red
    ctx.clearRect(0, 0, size, size);
    ctx.beginPath(); path({ type: 'Sphere' }); ctx.fillStyle = css('--globe-sea'); ctx.fill();
    ctx.lineWidth = 0.4; ctx.strokeStyle = css('--globe-line');
    for (const f of features) {
      const s = statusOf(f.id);
      ctx.beginPath(); path(f);
      ctx.fillStyle = s ? col[s] : css('--globe-none'); ctx.fill(); ctx.stroke();
    }
    if (selected?.geometry) { ctx.beginPath(); path(selected); ctx.lineWidth = 2; ctx.strokeStyle = css('--globe-select'); ctx.stroke(); }
    // Markers for countries that are tiny on the map but matter in the queue
    const centre = [-rotate[0], -rotate[1]];
    const marks = [...extra.map(e => ({ id: e.id, c: e.point })),
      ...features.filter(f => ['cleared', 'current'].includes(statusOf(f.id)) && path.area(f) < 30).map(f => ({ id: f.id, c: d3.geoCentroid(f) }))];
    for (const m of marks) {
      if (d3.geoDistance(m.c, centre) > Math.PI / 2 - 0.05) continue;
      const [x, y] = projection(m.c), s = statusOf(m.id) || 'waiting';
      ctx.beginPath(); ctx.arc(x, y, 5, 0, 2 * Math.PI); ctx.fillStyle = col[s]; ctx.fill();
      ctx.lineWidth = 1.5; ctx.strokeStyle = css('--globe-select'); ctx.stroke();
    }
    ctx.beginPath(); path({ type: 'Sphere' }); ctx.lineWidth = 1; ctx.strokeStyle = css('--globe-line'); ctx.stroke();
  }

  function tick(t) {
    raf = requestAnimationFrame(tick);
    if (!canvas.offsetParent || document.hidden) return; // not on screen: do nothing
    const auto = spinning && !matchMedia('(prefers-reduced-motion: reduce)').matches;
    canvas.dataset.autorotate = auto ? '1' : '0';     // observable: tests and assistive tools can see whether it moves
    if (auto) { rotate[0] += (t - (last || t)) * 0.006; draw(); }
    last = t;
  }

  // Drag to rotate; a tap without movement selects a country.
  let start = null;
  canvas.addEventListener('pointerdown', e => { start = { x: e.clientX, y: e.clientY, r: [...rotate], moved: false }; canvas.setPointerCapture(e.pointerId); spinning = false; });
  canvas.addEventListener('pointermove', e => {
    if (!start) return;
    const dx = e.clientX - start.x, dy = e.clientY - start.y;
    if (Math.abs(dx) + Math.abs(dy) > 4) start.moved = true;
    const k = 180 / (size || 300);
    rotate = [start.r[0] + dx * k, Math.max(-80, Math.min(80, start.r[1] - dy * k))];
    draw();
  });
  canvas.addEventListener('pointerup', e => {
    if (start && !start.moved) {
      const r = canvas.getBoundingClientRect(), ll = projection.invert([e.clientX - r.left, e.clientY - r.top]);
      const hitPoint = extra.find(p => ll && d3.geoDistance(p.point, ll) < 0.05);
      selected = hitPoint ? { id: hitPoint.id } : (ll && features.find(f => d3.geoContains(f, ll))) || null;
      draw(); onSelect?.(selected?.id || null, selected?.properties?.name);
    }
    start = null;
  });
  addEventListener('resize', () => { fit(); draw(); });

  // Turn smoothly to face a country.
  function focus(id) {
    const f = features.find(x => x.id === id), c = f ? d3.geoCentroid(f) : POINTS[id];
    if (!c) return;
    spinning = false; selected = f || { id };
    const from = [...rotate], to = [-c[0], -c[1]], interp = d3.interpolate(from, to), t0 = performance.now();
    const step = now => { const k = Math.min(1, (now - t0) / 900); rotate = interp(d3.easeCubicInOut(k)); draw(); if (k < 1) requestAnimationFrame(step); };
    requestAnimationFrame(step);
  }

  fit(); draw(); raf = requestAnimationFrame(tick);
  return { redraw: draw, focus, resume() { spinning = true; }, nameOf: id => features.find(f => f.id === id)?.properties?.name };
}
