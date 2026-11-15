// VOREM Studio: ingest, direct (server: /v1/studio/direct), edit, preview, budget, export. Powered by VOREM.
'use strict';
const GROUPS = { hero: 'Presenter', three: 'Three cards', steps: 'Gold timeline', stat: 'Number + source', quiz: 'Quick question' };
const STOP = 0.6, BEAT = 0.85, FIXED = 0.6 + 5 + 8;          // the kit's pause, lead and tail, opening, end card and references

// A loaded example so the studio opens working. It is marked as an example and is never saved as one of your films.
const EXAMPLE = {
  id: null, example: true, title: 'Example · Smart bins pitch', cap: 3, wpm: 140,
  source: 'Example brief: a two-minute pitch for AI sorting bins on a university campus. Problem: contamination, fixed collection rounds, habits reset every year. Solution: bins that see the item and point to the right slot, plus fill sensors. Ask: a 90-day pilot in two buildings.',
  sources: 'Sensoneo (n.d.) University pilot case study results. Bins were on average 62% full when collected.',
  rubric: '', pname: 'Presenter Name', prole: 'Strategy consultant', audience: 'Estates directors',
  chapters: ['', 'The problem', 'The solution', 'The ask'],
  beats: [
    { group: 'hero', step: 0, chapter: 0, head: ['SMART BINS.', 'CLEANER CAMPUS.'], accent: 1, text: 'Good day. In two minutes I will show you how a campus can stop contaminating its own recycling.' },
    { group: 'three', step: 0, chapter: 1, head: ['THREE', 'ROOT CAUSES.'], accent: 1, items: [{ w: 'confusing', label: 'CONFUSING SIGNS' }, { w: 'fixed', label: 'FIXED ROUNDS' }, { w: 'reset', label: 'HABITS RESET' }],
      text: 'Recycling fails for three reasons. Confusing signs at the bin. Fixed collection rounds, not real demand. And habits that reset every September.' },
    { group: 'stat', step: 0, chapter: 1, head: ['62% FULL', 'AT COLLECTION.'], accent: 0, label: 'Average fill at collection', value: 62, w: '62', source_w: 'sensoneo', source: 'Sensoneo · one US university pilot',
      text: 'In one US university pilot, reported by Sensoneo, bins were only 62 per cent full when they were collected.' },
    { group: 'quiz', step: 0, chapter: 2, head: ['QUICK QUESTION:', 'WHICH BIN?'], accent: 1, w: 'which', question: 'A half-full coffee cup. Which bin?', options: ['Paper?', 'Plastic?', 'General?'], answer_w: 'hesitated', answer: 'You hesitated? So does everyone.',
      text: 'Quick question. You are holding a half-full coffee cup. Which bin? If you hesitated, so does everyone else. Our bin sees the cup and lights the right slot.' },
    { group: 'steps', step: 0, chapter: 3, head: ['NINETY DAYS.', 'TWO BUILDINGS.'], accent: 1, title: 'The pilot', items: [{ w: 'install', label: 'Install' }, { w: 'measure', label: 'Measure' }, { w: 'decide', label: 'Decide' }],
      text: 'We install in two buildings, measure for ninety days against a baseline, and then you decide on the evidence.' },
    { group: 'hero', step: 1, chapter: 3, head: ['START THE', 'PILOT.'], accent: 1, text: 'Approve the pilot, and we start next term. Thank you.' },
  ],
};

let P = clone(EXAMPLE), sel = 0, saveTimer = null, library = [], directing = false;
const LS = 'vorem-studio-films', LSCODE = 'vorem-studio-code';
const store = { get(k, d) { try { return JSON.parse(localStorage.getItem(k)) ?? d; } catch { return d; } }, set(k, v) { try { localStorage.setItem(k, JSON.stringify(v)); return true; } catch { return false; } } };
const $ = id => document.getElementById(id);
function clone(o) { return JSON.parse(JSON.stringify(o)); }
function esc(s) { return String(s ?? '').replace(/[&<>"]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c])); }
function toast(msg) { const t = $('toast'); t.textContent = msg; t.hidden = false; clearTimeout(toast.t); toast.t = setTimeout(() => t.hidden = true, 2600); }
const words = s => (s || '').trim().split(/\s+/).filter(Boolean);
const sentences = s => (s || '').trim().split(/(?<=[.?!])\s+/).filter(Boolean);
const mmss = s => `${Math.floor(s / 60)}:${String(Math.round(s % 60)).padStart(2, '0')}`;

// ---------- ingest ----------
const FIELDS = ['source', 'sources', 'rubric', 'pname', 'prole', 'audience', 'cap'];
function fillIngest() {
  $('title').value = P.title || ''; FIELDS.forEach(f => $(f).value = P[f] ?? ''); $('wpm').value = P.wpm || 140;
}
FIELDS.forEach(f => $(f).addEventListener('input', () => { P[f] = f === 'cap' ? +$(f).value : $(f).value; changed(f === 'cap'); }));
$('title').addEventListener('input', () => { P.title = $('title').value; changed(false); });
$('wpm').addEventListener('input', () => { P.wpm = +$('wpm').value || 140; changed(true); });

const drop = $('drop');
drop.onclick = () => $('file').click();
drop.onkeydown = e => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); $('file').click(); } };
['dragenter', 'dragover'].forEach(ev => drop.addEventListener(ev, e => { e.preventDefault(); drop.classList.add('on'); }));
['dragleave', 'drop'].forEach(ev => drop.addEventListener(ev, e => { e.preventDefault(); drop.classList.remove('on'); }));
drop.addEventListener('drop', e => readFile(e.dataTransfer.files[0]));
$('file').onchange = e => readFile(e.target.files[0]);
function readFile(f) {
  if (!f) return;
  if (f.size > 400000) { toast('That file is over 400 KB. Paste the part the film needs.'); return; }
  const r = new FileReader();
  r.onload = () => { $('source').value = String(r.result); P.source = $('source').value; changed(false); toast(`Read ${f.name}`); };
  r.onerror = () => toast('Could not read that file. Paste the text instead.');
  r.readAsText(f);
}

// ---------- the director ----------
const DIRECTOR = `You are the director of VOREM Studio. Turn the material below into a narrated film in the VOREM style, as JSON.

The VOREM style: calm, measured narration, one breath per sentence. Each beat is 1 to 4 short sentences with a two-line
UPPERCASE headline (each line at most 22 characters), one of the two lines is the "accent" (amber). No hard cuts; visuals
appear on the words that name them. Structure: a hook, the question or problem, the problem as three causes, the
solution(s), the plan, the impact (measured), a conclusion and a clear ask. Include exactly one "quiz" beat (a quick question
to the viewer) and at least two headlines that are questions. If a rubric is given, give it one chapter per section, in order.
Keep the presenter's own wording and signposting where the material is their script or transcript.

Accuracy rules: use a number ONLY if it appears in the material or the sources; never invent figures, names or studies.
If the material has no number for a "stat" beat, do not use a stat beat.

Length: the narration must fit the limit at {WPM} words a minute plus about 1 second per beat. Aim for about {WORDS} words in total.

Visual groups (use only these):
- "hero": the presenter. Use for the first beat (step 0) and the last beat (step 1, ending with "Thank you.").
- "three": three cards. Add "items": [{"w": a word spoken in the beat that reveals the card, "label": "CARD LABEL"} x3].
- "steps": a gold numbered timeline. Add "title" and "items": [{"w": spoken word, "label": "Step label"} x2 to x4].
- "stat": a percentage counting up. Add "label", "value" (0-100, from the sources), "w" (the number as spoken, e.g. "62"),
  "source" (short source name) and "source_w" (a spoken word naming the source).
- "quiz": add "w" (a spoken word that opens the question, e.g. "which"), "question", "options" (2-4 short strings),
  "answer_w" (a spoken word near the reveal) and "answer" (a short line).
Every "w" must be a single word that appears in that beat's text.

Reply with only a JSON object:
{"title": string, "chapters": ["", "Chapter 1 name", ...], "beats": [{"group", "step", "chapter" (index into chapters, 0 = intro), "head": [line1, line2], "accent": 0 or 1, "text", ...group fields}]}`;

$('code').value = store.get(LSCODE, '');
$('code').addEventListener('input', () => store.set(LSCODE, $('code').value));
$('directBtn').onclick = async () => {
  if (!directing) { $('directNote').innerHTML = '<span class="err">Directing is not switched on yet. Write and edit beats by hand, then export.</span>'; return; }
  if (words(P.source).length < 5) { $('directNote').innerHTML = '<span class="err">Add a brief, script or notes first.</span>'; return; }
  if (!$('code').value) { $('directNote').innerHTML = '<span class="err">Enter the studio access code.</span>'; $('code').focus(); return; }
  const btn = $('directBtn'); btn.disabled = true; btn.innerHTML = '<span class="spin"></span>Directing…';
  $('directNote').textContent = 'Claude is writing the beats. This usually takes under a minute.';
  try {
    const r = await fetch('/v1/studio/direct', { method: 'POST', headers: { 'Content-Type': 'application/json', 'X-Studio-Code': $('code').value },
      body: JSON.stringify({ material: P.source, sources: P.sources || '', rubric: P.rubric || '', presenter: P.pname || '', role: P.prole || '',
        audience: P.audience || '', cap_min: +P.cap || 7, wpm: +P.wpm || 140 }) });
    const out = await r.json().catch(() => ({}));
    if (!r.ok) throw new Error(typeof out.detail === 'string' ? out.detail : 'Directing failed. Try again in a moment.');
    P = { ...P, example: false, id: P.example ? null : P.id, title: out.title || P.title, chapters: out.chapters && out.chapters.length ? out.chapters : ['', 'Part one'],
      beats: out.beats.map(normalise) };
    sel = 0; renderAll(); changed(true);
    $('directNote').textContent = `Directed ${P.beats.length} beats. Edit anything, then export.`;
  } catch (e) {
    $('directNote').innerHTML = `<span class="err">${esc(e.message || 'Directing failed. Try again in a moment.')}</span>`;
  } finally { btn.disabled = false; btn.textContent = 'Direct the film'; }
};

function normalise(b) {
  const g = GROUPS[b.group] ? b.group : 'three';
  const out = { ...b, group: g, step: +b.step || 0, chapter: +b.chapter || 0, accent: b.accent ? 1 : 0, text: String(b.text || ''),
    head: Array.isArray(b.head) ? [String(b.head[0] || ''), String(b.head[1] || '')] : ['', ''] };
  if (g === 'three' && !Array.isArray(out.items)) out.items = [{ w: '', label: 'CARD ONE' }, { w: '', label: 'CARD TWO' }, { w: '', label: 'CARD THREE' }];
  if (g === 'steps' && !Array.isArray(out.items)) out.items = [{ w: '', label: 'Step one' }, { w: '', label: 'Step two' }, { w: '', label: 'Step three' }];
  return out;
}

// ---------- beat sheet ----------
function renderBeats() {
  const list = $('beats');
  $('chapters').innerHTML = (P.chapters || []).map((c, i) => `<span class="chap">${i ? '0' + i + ' · ' : ''}${esc(c || 'Intro')}</span>`).join('');
  if (!P.beats.length) { list.innerHTML = '<div class="empty"><b>No beats yet</b>Add your material on the left and choose Direct the film, or add a beat by hand.</div>'; return; }
  list.innerHTML = P.beats.map((b, i) => {
    const flags = numberFlags(b);
    return `<article class="beat${i === sel ? ' sel' : ''}" data-i="${i}">
      <div class="bhead"><span class="num">${String(i + 1).padStart(2, '0')}</span><span class="pill">${esc(GROUPS[b.group] || b.group)}</span>
        <span class="pill">${esc(P.chapters[b.chapter] || 'Intro')}</span>${flags.length ? `<span class="pill flag" title="Not found in your sources">Check ${esc(flags.join(', '))}</span>` : ''}
        <span class="spacer"></span><span class="mono">${words(b.text).length} w · ${mmss(beatSeconds(b))}</span>
        <button class="iconbtn" data-act="up" aria-label="Move beat up">↑</button><button class="iconbtn" data-act="down" aria-label="Move beat down">↓</button><button class="iconbtn" data-act="del" aria-label="Delete beat">✕</button></div>
      ${[0, 1].map(k => `<div class="hl"><input id="h${i}_${k}" class="${b.accent === k ? 'acc' : ''}" value="${esc(b.head[k])}" maxlength="28" aria-label="Headline line ${k + 1}"><button class="acc-t${b.accent === k ? ' on' : ''}" data-act="acc" data-k="${k}">amber</button></div>`).join('')}
      <textarea id="t${i}" aria-label="Narration for beat ${i + 1}">${esc(b.text)}</textarea>
      <div class="bfoot"><span class="mono">Visual</span><select id="g${i}" aria-label="Visual for beat ${i + 1}">${Object.entries(GROUPS).map(([k, v]) => `<option value="${k}"${k === b.group ? ' selected' : ''}>${v}</option>`).join('')}</select>
        <span class="mono">Chapter</span><select id="c${i}" aria-label="Chapter for beat ${i + 1}">${(P.chapters || []).map((c, ci) => `<option value="${ci}"${ci === b.chapter ? ' selected' : ''}>${esc(c || 'Intro')}</option>`).join('')}</select></div>
    </article>`;
  }).join('');
}
$('beats').addEventListener('click', e => {
  const art = e.target.closest('.beat'); if (!art) return;
  const i = +art.dataset.i, act = e.target.dataset.act;
  if (act === 'del') { P.beats.splice(i, 1); sel = Math.min(sel, P.beats.length - 1); renderAll(); changed(true); return; }
  if (act === 'up' && i > 0) { [P.beats[i - 1], P.beats[i]] = [P.beats[i], P.beats[i - 1]]; sel = i - 1; renderAll(); changed(true); return; }
  if (act === 'down' && i < P.beats.length - 1) { [P.beats[i + 1], P.beats[i]] = [P.beats[i], P.beats[i + 1]]; sel = i + 1; renderAll(); changed(true); return; }
  if (act === 'acc') { P.beats[i].accent = +e.target.dataset.k; sel = i; renderAll(); changed(false); return; }
  if (sel !== i) { sel = i; document.querySelectorAll('.beat').forEach(a => a.classList.toggle('sel', +a.dataset.i === i)); renderPreview(); }
});
$('beats').addEventListener('input', e => {
  const m = e.target.id.match(/^([htgc])(\d+)(?:_(\d))?$/); if (!m) return;
  const b = P.beats[+m[2]];
  if (m[1] === 'h') { b.head[+m[3]] = e.target.value.toUpperCase(); }
  if (m[1] === 't') b.text = e.target.value;
  sel = +m[2]; renderPreview(); renderBudget(); changed(false);
});
$('beats').addEventListener('change', e => {
  const m = e.target.id.match(/^([gc])(\d+)$/); if (!m) return;
  const b = P.beats[+m[2]];
  if (m[1] === 'g') Object.assign(b, normalise({ ...b, group: e.target.value }));
  if (m[1] === 'c') b.chapter = +e.target.value;
  sel = +m[2]; renderAll(); changed(true);
});
$('addBtn').onclick = () => { P.beats.splice(sel + 1, 0, normalise({ group: 'three', chapter: P.beats[sel]?.chapter || 0, head: ['NEW', 'HEADLINE.'], accent: 1, text: '' })); sel = Math.min(sel + 1, P.beats.length - 1); renderAll(); changed(true); };

// numbers in the narration that do not appear in the sources or the material
function numberFlags(b) {
  const pool = `${P.sources || ''} ${P.source || ''}`;
  return [...new Set((b.text.match(/\d[\d,.]*/g) || []).map(n => n.replace(/[.,]$/, '')))].filter(n => !pool.includes(n));
}

// ---------- preview ----------
function renderPreview() {
  const b = P.beats[sel], f = $('frame');
  $('pvLabel').textContent = b ? `beat ${sel + 1} of ${P.beats.length}` : '';
  if (!b) { f.innerHTML = '<div class="cap">Your film appears here</div>'; return; }
  const ch = b.chapter, top = 36;
  const firstWords = words(b.text).slice(0, 3), key = firstWords.reduce((a, w, k) => w.length > (firstWords[a] || '').length ? k : a, 0);
  f.innerHTML = `<div class="eb">${esc(P.title || 'VOREM Studio')}</div><div class="ct">${ch ? '0' + ch + ' / 0' + (P.chapters.length - 1) : ''}</div>
    <div class="kick" style="top:${top - 7}%">${ch ? '0' + ch + ' · ' + esc(P.chapters[ch]) : 'Introduction'}</div>
    <div class="lines" style="top:${top}%">${b.head.map((l, k) => `<div class="ln${k === b.accent ? ' acc' : ''}"><b>${esc(l)}</b></div>`).join('')}</div>
    <div class="rule" style="top:${top + 23}%"></div>
    <div class="viz"><div>${viz(b)}</div></div>
    <div class="cap">${firstWords.map((w, k) => k === key ? `<u>${esc(w)}</u>` : esc(w)).join(' ')}</div>`;
}
function viz(b) {
  if (b.group === 'hero') return `<div class="vcard presenter" style="bottom:10%"><small>PRESENTER</small>${esc(P.pname || 'Presenter')}<div style="font:500 1.2cqw var(--body);color:var(--mute);margin-top:.4cqw">${esc(P.prole || '')}</div></div>`;
  if (b.group === 'three') return (b.items || []).slice(0, 3).map((it, k) => `<div class="vcard" style="left:${k * 9}%;top:${4 + k * 30}%;width:72%;animation-delay:${k * .15}s"><small>0${k + 1}</small>${esc(it.label)}</div>`).join('');
  if (b.group === 'steps') return `<div class="mono" style="position:absolute;left:6cqw;top:-1%;font-size:1.1cqw">${esc(b.title || '')}</div>` + (b.items || []).map((it, k) => `<div class="vnode" style="top:${8 + k * 22}%">0${k + 1}</div><div class="vrow${k === 0 ? ' on' : ''}" style="top:${8 + k * 22}%;animation-delay:${k * .12}s">${esc(it.label)}</div>`).join('');
  if (b.group === 'stat') return `<div class="ring" style="--p:${+b.value || 0}"><span>${+b.value || 0}%</span></div><div class="vchip" style="left:62%;top:20%">${esc(b.source || 'Source')}</div>`;
  if (b.group === 'quiz') return `<div class="vcard" style="left:4%;top:8%;width:90%"><small>QUICK QUESTION</small>${esc(b.question || '')}<div style="display:flex;gap:.6cqw;margin-top:1cqw;flex-wrap:wrap">${(b.options || []).map(o => `<span class="vchip" style="position:static;color:var(--ink);border-color:var(--line2);background:rgba(255,255,255,.04)">${esc(o)}</span>`).join('')}</div></div><div class="vchip" style="left:4%;top:66%">${esc(b.answer || '')}</div>`;
  return '';
}
$('prevBtn').onclick = () => { if (sel > 0) { sel--; renderAll(); scrollSel(); } };
$('nextBtn').onclick = () => { if (sel < P.beats.length - 1) { sel++; renderAll(); scrollSel(); } };
function scrollSel() { document.querySelector('.beat.sel')?.scrollIntoView({ block: 'nearest', behavior: 'smooth' }); }
$('readBtn').onclick = () => {
  const b = P.beats[sel]; if (!b) return;
  if (!('speechSynthesis' in window)) { toast('This browser cannot read aloud.'); return; }
  speechSynthesis.cancel();
  const u = new SpeechSynthesisUtterance(b.text.replace(/(?<=[.?!])\s+/g, ' ... ')); u.rate = (+P.wpm || 140) / 165; u.lang = 'en-GB';
  speechSynthesis.speak(u);
};

// ---------- budget ----------
function beatSeconds(b) { const w = words(b.text).length; return w / ((+P.wpm || 140) / 60) + sentences(b.text).length * STOP + BEAT; }
function renderBudget() {
  const total = P.beats.reduce((s, b) => s + beatSeconds(b), FIXED), cap = (+P.cap || 7) * 60, over = total > cap;
  const nw = P.beats.reduce((s, b) => s + words(b.text).length, 0);
  $('estT').textContent = mmss(total); $('estT').classList.toggle('over', over);
  $('estOf').textContent = `estimated length · limit ${mmss(cap)}${over ? ` · ${Math.ceil((total - cap) / 60 * (+P.wpm || 140))} words over` : ''}`;
  $('meter').style.width = Math.min(100, total / cap * 100) + '%'; $('meter').classList.toggle('over', over);
  $('sWords').textContent = nw; $('sBeats').textContent = P.beats.length; $('beatCount').textContent = `${P.beats.length} beats`;
  $('maxS').textContent = Math.floor(cap);
  const quiz = P.beats.filter(b => b.group === 'quiz').length, qs = P.beats.filter(b => b.head.join(' ').includes('?')).length;
  const flagged = P.beats.map((b, i) => numberFlags(b).length ? i + 1 : 0).filter(Boolean);
  const badW = P.beats.map((b, i) => { const t = words(b.text).map(w => w.toLowerCase().replace(/[^a-z0-9-]/g, ''));
    const ws = [b.w, b.answer_w, b.source_w, ...(b.items || []).map(x => x.w)].filter(Boolean);
    return ws.some(w => !t.some(x => x.startsWith(String(w).toLowerCase()))) ? i + 1 : 0; }).filter(Boolean);
  const long = P.beats.map((b, i) => b.head.some(l => l.length > 22) ? i + 1 : 0).filter(Boolean);
  const C = [
    [!over, over ? `Over the limit: cut about ${Math.ceil((total - cap) / 60 * (+P.wpm || 140))} words, keep the pace` : 'Fits the length limit'],
    [!flagged.length, flagged.length ? `Numbers not in your sources: beat ${flagged.join(', ')}` : 'Every number appears in your material or sources'],
    [quiz === 1, quiz === 1 ? 'One quick-question beat' : `Use exactly one quick-question beat (now ${quiz})`],
    [qs >= 2, qs >= 2 ? `${qs} question headlines` : 'Add a second question headline'],
    [!badW.length, badW.length ? `Reveal words missing from the narration: beat ${badW.join(', ')}` : 'Every visual has a word to appear on'],
    [!long.length, long.length ? `Headline lines over 22 characters: beat ${long.join(', ')}` : 'Headlines fit the frame'],
    [P.beats[0]?.group === 'hero' && P.beats[P.beats.length - 1]?.group === 'hero', 'Opens and closes on the presenter'],
  ];
  $('checks').innerHTML = C.map(([ok, t]) => `<li class="${ok ? '' : 'bad'}">${esc(t)}</li>`).join('');
}
function renderAll() { renderBeats(); renderPreview(); renderBudget(); }

// ---------- export ----------
function filmJson() {
  const pron = [];
  return JSON.stringify({
    meta: { eyebrow: P.title || 'VOREM', name: P.pname || '', role: P.prole || '', short_role: P.prole || '',
      ai_label: 'Narration · AI voice', end_title: (P.title || 'VOREM').split(/[·:-]/)[0].trim(), end_accent: P.chapters[P.chapters.length - 1] || '',
      end_sub: P.audience ? `For ${P.audience}` : '', end_line: [P.pname, P.prole].filter(Boolean).join(' · '), pronounce: pron,
      refs: (P.sources || '').split('\n').map(s => s.trim()).filter(Boolean).map(esc) },
    chapters: P.chapters,
    beats: P.beats.map((b, i) => ({ id: `b${String(i + 1).padStart(2, '0')}`, ...b })),
  }, null, 1);
}
$('exportBtn').onclick = () => {
  const name = (P.title || 'film').replace(/[^\w-]+/g, '-').replace(/^-|-$/g, '').toLowerCase() || 'film';
  const a = document.createElement('a'); a.href = URL.createObjectURL(new Blob([filmJson()], { type: 'application/json' }));
  a.download = `${name}.film.json`; document.body.append(a); a.click(); a.remove(); setTimeout(() => URL.revokeObjectURL(a.href), 2000);
  toast('Exported');
};
$('copyBtn').onclick = copyJson;
function copyJson() {
  navigator.clipboard.writeText(filmJson()).then(() => toast('film.json copied'), () => toast('Copy was blocked. Use Export instead.'));
}

// ---------- your films (saved privately per viewer) ----------
function changed(structural) {
  if (P.example) { $('saved').textContent = 'example · not saved'; return; }
  $('saved').textContent = 'saving…'; clearTimeout(saveTimer); saveTimer = setTimeout(save, 900);
  if (structural) renderBudget();
}
function save() {
  if (!P.id) P.id = 'f' + Date.now().toString(36);
  const { example, ...body } = P, all = store.get(LS, []).filter(f => f.id !== P.id);
  all.unshift({ ...body, updated: Date.now() });
  $('saved').textContent = store.set(LS, all.slice(0, 40)) ? 'saved in this browser' : 'not saved (storage is blocked)';
  refreshLib();
}
function refreshLib() {
  library = store.get(LS, []);
  $('libState').textContent = `${library.length} in this browser`;
  $('lib').innerHTML = library.length ? library.map(f => `<button data-id="${esc(f.id)}"><span>${esc(f.title || 'Untitled film')}</span><span>${(f.beats || []).length} beats</span></button>`).join('')
    : '<p class="note">No saved films yet. Your first direct or edit saves one here, in this browser.</p>';
}
$('lib').addEventListener('click', e => {
  const b = e.target.closest('button[data-id]'); if (!b) return;
  const f = library.find(x => x.id === b.dataset.id); if (!f) return;
  P = { ...clone(f), example: false }; sel = 0; fillIngest(); renderAll(); $('saved').textContent = 'saved';
});
$('newBtn').onclick = () => {
  P = { id: null, example: false, title: 'Untitled film', cap: 7, wpm: 140, source: '', sources: '', rubric: '', pname: '', prole: '', audience: '', chapters: [''], beats: [] };
  sel = 0; fillIngest(); renderAll(); $('saved').textContent = ''; $('source').focus();
};

// ---------- boot ----------
fillIngest(); renderAll(); $('saved').textContent = 'example · not saved';
refreshLib();
fetch('/v1/studio/status').then(r => r.json()).then(s => { directing = !!s.directing;
  if (!directing) $('directNote').textContent = 'Directing switches on once the studio is connected to Claude. Until then, write beats by hand and export.'; })
  .catch(() => { $('directNote').textContent = 'The studio server is not reachable. You can still edit and export.'; });
