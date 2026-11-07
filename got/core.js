// Dar v2 — core runtime: config, storage, i18n helpers, formatting, catalog merge, pricing & tax,
// and the data gateway. In "demo" (model) mode every operation runs in a local backend that mirrors the
// future server contract exactly; in "live" mode the same operations go to ONE automation endpoint:
//   POST {apiBase}/{endpoint}  body {op, payload, token, app, lang, country, v}  ->  {ok, data, error}
import { legalPlain, LEGAL_DOC as LEGAL_DOC_KIND } from './legal.js?v=3.34.0-d66b90ae'; // (v3.33.5: a legal row is a whole document)
import * as R from './registry.js?v=3.34.0-d66b90ae';
import { extOps } from './ops2.js?v=3.34.0-d66b90ae';
import { referOps } from './refer.js?v=3.34.0-d66b90ae'; // v3.30: a sold copy's own client referral programme and rewards wallet
import { extOps3 } from './ops3.js?v=3.34.0-d66b90ae';
import { learnOps } from './learn.js?v=3.34.0-d66b90ae';
import { geoOps } from './geo-ops.js?v=3.34.0-d66b90ae';
import { setPlacesRoot, shownPlace, placesFile, cityIndex } from './places.js?v=3.34.0-d66b90ae';
import { leadViolations } from './lead-lock.js?v=3.34.0-d66b90ae'; // v3.33.29: an office taken from the map keeps the map's data
import { setScriptOf, fold as foldName } from './geo-osm.js?v=3.34.0-d66b90ae';
import { behaviorOps } from './behavior.js?v=3.34.0-d66b90ae';
import { onboardingFor, computeMenu, DEFAULT_STYLE, cleanStyle } from './onboarding.js?v=3.34.0-d66b90ae';
import { LANGS, UI, FIELDS, OPTS, ROLES } from './i18n.js?v=3.34.0-d66b90ae';
import { S as ST } from './state.js?v=3.34.0-d66b90ae'; // (v3.20: who reads an error — the developer is told where its reason is, everyone else plainly)
import { isBaseLang, langInfo, isRtlLang, textKey, icu, asciiDigits, langEnglish, setTranslator } from './langs.js?v=3.34.0-d66b90ae';
import { webTemplate } from './webtpl.js?v=3.34.0-d66b90ae'; // v3.28: «موقعي» — the starting website
import { svcFeatState, featWhy, featOk, featState, featMsg, featOwn, FEATURE_DEFS } from './features.js?v=3.34.0-d66b90ae'; // v3.32: the central control of features
setScriptOf(l => langInfo(l)?.script || 'Latn'); // v3.16: a place's own name when it is in the reader's script
import { teamBrief } from './staff.js?v=3.34.0-d66b90ae';
import { valueHasKeys, hasKeys, sweepLocal } from './keys.js?v=3.34.0-d66b90ae';
import { compute, estimateFrom, todayInsight, intelInsight, twinInsight, partnerInsight, builderInsight, providerInsight, pulseInsight } from './compute.js?v=3.34.0-d66b90ae';
const INSIGHTS = { today: todayInsight, intel: intelInsight, twin: twinInsight, partner: partnerInsight, builder: builderInsight, provider: providerInsight, pulse: pulseInsight };
import { norm as normText } from './commands.js?v=3.34.0-d66b90ae';
import { brain, brainHandles, isExternal, extendBrain, autoCapable } from './brain.js?v=3.34.0-d66b90ae';
import { ACTS32, accountingExport } from './acts32.js?v=3.34.0-d66b90ae';
import { ops32 } from './ops32.js?v=3.34.0-d66b90ae';
import { billingOps, billingCfg, partnerCfg, SUB_SCREEN, BILLING_DEFAULTS, termsNow, termsOk, leaving } from './billing.js?v=3.34.0-d66b90ae';
import { SOLO, SHOW, SHOW_KIND, PV, SOLD_OUT, SHOW_TEXTS } from './edition.js?v=3.34.0-d66b90ae';
import { sampleData, tplLibrary } from './seed.js?v=3.34.0-d66b90ae';
import { DEMO_CITIES } from './world.js?v=3.34.0-d66b90ae';
const DEMO_CC = new Set(DEMO_CITIES.split('\n').map(l => l.split('|')[0]));
import * as UV from './units-view.js?v=3.34.0-d66b90ae';
import { BUILD32_ASYNC } from './build32.js?v=3.34.0-d66b90ae';
import { integrityIssues, queueIssues } from './health32.js?v=3.34.0-d66b90ae';
import { devPrompt, DEV_HELP, relevantRecords, compactRow, ASSIST_COLLS, wordsOf, scoreText, fold, cut as clip, fieldDoc, compactResult, draftsOf, enhancePrompt, applyEnhance } from './assist.js?v=3.34.0-d66b90ae';
import { imagesOf as attachImages, evidenceOf as attachEvidence, namesOf as attachNames } from './attach.js?v=3.34.0-d66b90ae';
import { setSoloName, quickPrompt, think, framePrompt, frameSplit, tenantDomain, nowContext, normField, runQuery, runStats, receptionPrompt, parseReception, AI_WAIT, apiReference, evidencePool, groundCheck, trimUngrounded } from './mind.js?v=3.34.0-d66b90ae';
import { guardClaims, truthOf } from './truth.js?v=3.34.0-d66b90ae';
import { WHERE_HINTS } from './platmap.js?v=3.34.0-d66b90ae'; // v3.33 (note 5): where the things he names live

export const VERSION = '3.34.0-model';
// v3.33.28 (the owner, 2026-10-28: thousands of people at once): how long since a person last touched this page — a tab nobody touches for five
// minutes asks the server a third as often (sync.js, ui.js); the moment he touches it or the tab shows again, it asks at once
let TOUCH = Date.now(); export const idleMs = () => Date.now() - TOUCH;
export const IDLE_AFTER = 5 * 60e3;
if (typeof window !== 'undefined' && typeof window.addEventListener === 'function') for (const ev of ['pointerdown', 'keydown', 'touchstart', 'wheel']) window.addEventListener(ev, () => { TOUCH = Date.now(); }, { passive: true, capture: true });
sweepLocal(VERSION); // v3.11.1: a key this browser kept a copy of (the settings, the log, a conversation) is masked here once
export const CFG = { mode: 'demo', apiBase: '', endpoint: 'dar/v2', root: './', pretty: false, timeout: 20000 };
// v3.10: a file kept on the server is named in the record by its address (dar-sync.php?f=<48 hex>), relative to the site's root;
// fileHref() makes it a full address for the page (or a feed, or a message) that shows it. Anything else passes through.
export const FILE_REF = /^dar-sync\.php\?f=[0-9a-f]{48}$/;
export const isFileRef = u => typeof u === 'string' && FILE_REF.test(u);
export const fileHref = u => { if (!isFileRef(u)) return u; try { return new URL((CFG.root || './') + u, typeof location !== 'undefined' ? location.href : 'http://localhost/').href; } catch { return u; } };
// what a picture field may hold: a data URL, an https address, or a stored file
export const IMG_OK = /^(https:\/\/|data:image\/|dar-sync\.php\?f=[0-9a-f]{48}$|dar-sync\.php\?art=[0-9a-f]{32}$)/; // (v3.33.70: ?art= — a picture drawn as code by the site's AI)

// ---------------------------------------------------------------- storage (never throws)
const MEM = new Map();
// v3.30: the buyers' preview lives on the platform's own address (…/v/<token>/…), so the browser gives its pages the same storage
// as the platform's. Its example keeps a drawer of its own: nothing the example writes reaches the platform's pages in this browser
// (an owner who opens his preview where he works, a subscriber who is also a buyer), and nothing the platform's pages keep here
// (its settings, its questions, an account's records) reaches the example
const NS = PV ? 'dar2pv:' : 'dar2:';
export const STORE_NS = NS;
let storageOk = true;
// v3.3 hosted mode (assets/sync.js): `call` runs every operation (the engine here, accounts on Dar Sync) and `onWrite`
// learns which keys an operation changed, with their value before the change, so only those rows travel to the server
export const HOSTED = { call: null, onWrite: null, auto: null }; // v3.3 hosted mode (assets/sync.js); v3.4 adds pub/pubGet (public pages on the server); v3.6 auto: {on} — the automation bridge sends messages automatically
function rawGet(k) { try { const v = globalThis.localStorage?.getItem(NS + k); if (v != null) return v; } catch { storageOk = false; } return MEM.has(k) ? MEM.get(k) : null; }
// v3.33.3 (live, 2026-10-23 — «ضع الموقع في وضع الصيانة» answered «امتلأت مساحة التخزين في هذا المتصفح»: the change log the server
// sends the owner's panel had grown to 2.5 MB): what this browser keeps is a copy. When its storage is full, the copies of logs leave it
// (kept in memory for this page; the next start brings them again, smaller) and the write is tried once more; on the hosted site a
// change still reaches the server when the browser cannot keep a copy of it
const SHED = ['audit', 'errors', 'jobs'];
function shed(k) {
  let freed = false;
  for (const s of SHED) { if (s === k) continue; try { const v = globalThis.localStorage?.getItem(NS + s); if (v != null) { if (!MEM.has(s)) MEM.set(s, v); globalThis.localStorage.removeItem(NS + s); freed = true; } } catch { /* nothing to free */ } }
  if (freed) try { globalThis.localStorage?.setItem(NS + 'sync:refetch', '1'); } catch { /* the next pull is a full one anyway when it can be */ }
  return freed;
}
function rawSet(k, v) {
  const w = HOSTED.onWrite, old = w ? rawGet(k) : null; MEM.set(k, v); let ok = true;
  try { globalThis.localStorage?.setItem(NS + k, v); } catch { ok = false; if (shed(k)) { try { globalThis.localStorage?.setItem(NS + k, v); ok = true; } catch { /* still full */ } } if (!ok) { storageOk = false; try { globalThis.localStorage?.removeItem(NS + k); globalThis.localStorage?.setItem(NS + 'sync:refetch', '1'); } catch { /* an older copy would come back wrong */ } } }
  if (w) w(k, old); return ok || !!w; // (hosted: the server keeps it — this page keeps it in memory)
}
function rawDel(k) { const w = HOSTED.onWrite, old = w ? rawGet(k) : null; MEM.delete(k); try { globalThis.localStorage?.removeItem(NS + k); } catch { /* ignore */ } if (w && old != null) w(k, old); }
export const store = {
  get(k, d = null) { const v = rawGet(k); if (v == null) return d; try { return JSON.parse(v); } catch { return d; } },
  set(k, v) { return rawSet(k, JSON.stringify(v)); },
  del(k) { rawDel(k); },
  keys(prefix = '') {
    const out = new Set();
    try { const ls = globalThis.localStorage; if (ls) for (let i = 0; i < ls.length; i++) { const k = ls.key(i); if (k && k.startsWith(NS + prefix)) out.add(k.slice(NS.length)); } } catch { /* ignore */ }
    for (const k of MEM.keys()) if (k.startsWith(prefix)) out.add(k);
    return [...out];
  },
  get persistent() { return storageOk; },
};

// ---------------------------------------------------------------- small utils
export const uid = (p = '') => p + Date.now().toString(36) + Math.random().toString(36).slice(2, 8);
// v3.13.2: a partner's referral code as the visitor met it, with when he first opened that partner's link (the programme's
// ownership days count from it; another partner's link starts again)
export function keepRef(code) { const c = String(code || '').trim().slice(0, 24); if (!c) return; if (store.get('pref:ref') !== c || !store.get('pref:ref_at')) store.set('pref:ref_at', new Date().toISOString()); store.set('pref:ref', c); }
export const nowIso = () => new Date().toISOString();
export const DAY = 864e5;
export const latinDigits = s => asciiDigits(s); // v3.16: the digits of every script (Arabic, Persian, Devanagari, Bengali, Thai…)
export const humanize = k => String(k || '').replace(/^x_/, '').replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase());
export const clone = o => JSON.parse(JSON.stringify(o));
// v3.17.2: a listing's shown place is moved by an offset that only the office knows: a random secret kept in its own settings
// (never in a page, a link or the public code). An offset worked out from the public address alone (the office and listing ids
// are in the link, and the offset's code is public) could be taken back, and the exact place with it. A new secret makes the
// office's pages publish again (sync.js follows its settings), so the old offsets leave the server with the next publish.
export function mapSeed(tid, rid) {
  const k = `set:${tid}:maps_salt`; let v = store.get(k, ''); if (typeof v !== 'string' || v.length < 16) { v = randomHex(16); store.set(k, v); }
  return v + ':' + tid + ':' + rid;
}
export function randomHex(n = 24) { const a = new Uint8Array(n); crypto.getRandomValues(a); return [...a].map(x => x.toString(16).padStart(2, '0')).join(''); }
export async function sha256(text) {
  if (globalThis.crypto?.subtle) { const b = await crypto.subtle.digest('SHA-256', new TextEncoder().encode(text)); return [...new Uint8Array(b)].map(x => x.toString(16).padStart(2, '0')).join(''); }
  let h = 0x811c9dc5; for (const ch of String(text)) { h ^= ch.charCodeAt(0); h = Math.imul(h, 0x01000193) >>> 0; } return 'weak' + h.toString(16);
}
async function hashPassword(password, salt) {
  if (globalThis.crypto?.subtle) {
    const key = await crypto.subtle.importKey('raw', new TextEncoder().encode(password), 'PBKDF2', false, ['deriveBits']);
    const bits = await crypto.subtle.deriveBits({ name: 'PBKDF2', salt: new TextEncoder().encode(salt), iterations: 100000, hash: 'SHA-256' }, key, 256);
    return [...new Uint8Array(bits)].map(x => x.toString(16).padStart(2, '0')).join('');
  }
  return sha256(salt + ':' + password);
}

// ---------------------------------------------------------------- errors
export class DarError extends Error { constructor(code, extra) { super(code); this.code = code; this.extra = extra || null; } }
const fail = (code, extra) => { throw new DarError(code, extra); };

// ---------------------------------------------------------------- language & texts
export const LANG = { cur: 'ar', cal: 'gregory', auto: false, cc: '' };
let TEXTS = {};
export function setTexts(x) { TEXTS = x || {}; }
export const li = () => LANGS[LANG.cur]?.i ?? 1; // v3.16: a language other than the three reads English where it has no translation
// v3.16 — every other language reads its PACK (assets/langs.js): the key of the English text → its translation. What it does
// not have yet shows in English and is noted (the translation engine is told which texts people actually see)
export const PACK = { lang: '', map: new Map(), v: '', n: 0, total: 0, miss: new Map(), seen: 0 };
export function setPack(lang, data) { PACK.lang = lang || ''; PACK.map = new Map(Object.entries((data && data.map) || {})); PACK.v = String(data?.v || ''); PACK.n = PACK.map.size; PACK.total = +data?.total || 0; PACK.miss = new Map(); }
export function addToPack(lang, map) { if (lang !== PACK.lang || !map) return 0; let n = 0; for (const [k, v] of Object.entries(map)) if (typeof v === 'string' && v) { PACK.map.set(k, v); PACK.miss.delete(k); n++; } PACK.n = PACK.map.size; return n; }
// a text in the reader's language: the pack's translation of its source (English, else the language it was written in)
export function tr(src) {
  const s = String(src ?? ''); if (!s || isBaseLang(LANG.cur) || !/\p{L}/u.test(s)) return s;
  const k = textKey(s); const v = PACK.map.get(k); if (v) return v;
  if (PACK.lang === LANG.cur && PACK.miss.size < 4000 && !PACK.miss.has(k)) PACK.miss.set(k, s.slice(0, 2000));
  return s;
}
setTranslator((src, lang) => (!lang || lang === LANG.cur) && !isBaseLang(LANG.cur) ? tr(src) : src);
let AREA = 'm2'; export const setAreaUnit = u => { AREA = u === 'ft2' ? 'ft2' : 'm2'; };
// v3.32: the unit of an area in the reader's language (م² in Arabic, m² in English and French; the country's ft² where it uses feet) — never «m²» in an Arabic screen
export const areaUnit = () => unitVar('au');
const unitVar = k => k === 'au' ? (UI['u_' + AREA]?.[li()] || (AREA === 'ft2' ? 'ft²' : 'm²')) : k === 'per' ? (UI['u_per_' + AREA]?.[li()] || '') : undefined;
export const areaSym = u => UI['u_' + (u === 'ft2' ? 'ft2' : 'm2')]?.[li()] || (u === 'ft2' ? 'ft²' : 'm²');
// v3.26: an interface text the owner (or his assistant) rewrote — one string instead of three, or the Arabic copied into the English
// and French places — never shows Arabic on an English or French screen when Dar has that text in the reader's language
const AR_SCRIPT = /[؀-ۿ]/;
// v3.26: a copy sold to one business speaks of that business, never of «دار»: the word, alone or with a joined preposition
// (لـ بـ وـ فـ كـ), becomes the business's name in every text the interface writes (the texts' own keys and the business's own
// records are untouched)
let BRAND_SUB = null;
export function setBrandSub(name) { const n = String(name || '').trim(); BRAND_SUB = (SOLO || SHOW) && n && !/^(دار|dar)$/i.test(n) ? n : null; if (SOLO || SHOW) setSoloName(n); } // (v3.26: the showcase speaks of its product's name)
const AR_DAR = /(^|[^\p{Script=Arabic}])((?:[وف][لبك]|[لبوفك])?)دار(?!\p{Script=Arabic})/gu, LAT_DAR = /(?<![\w-])Dar(?![\w-])/g; // (a header's name, X-Dar-Key, is not a word; v3.30: the word's edge is any sign outside the Arabic script — «دار،» and «دار؟» end there too, as the server's \p{Arabic} reads them)
// v3.29: before its business is named (the installation page, a banner on it), a sold copy says «the real-estate system» in the
// reader's language — never «دار» (the owner, 2026-10-15: «لا تضع اسم Dar»); «لـ» before «ال» reads «للـ»
// v3.31 (the owner, 2026-10-16: «لا يوجد شيء اسمه مطور بعد الشراء»): in a sold copy the developer's panel is its administration and the
// platform's owner is the system's owner — the same rule as the server's solo_roles (mail and alerts), here for every text the interface writes
const SOLO_ROLES_HIT = /المطو|المنصة|platform|developer|plateforme|développeur/i;
const soloRoles = s => (typeof s !== 'string' || !SOLO_ROLES_HIT.test(s)) ? s : s
  .replace(/لوحة المطوّ?ر/g, 'لوحة الإدارة').replace(/مساعد المطوّ?ر/g, 'مساعد الإدارة').replace(/(?:مالك|صاحب) المنصة/g, 'مالك النظام')
  .replace(/\b(D)eveloper panel\b/gi, (m, d) => d === 'D' ? 'Administration' : 'administration').replace(/\bplatform(’s|'s)? owner\b/gi, (m, ap) => 'system' + (ap || '') + ' owner')
  .replace(/\bdu panneau développeur/gi, 'de l’administration').replace(/\bau panneau développeur/gi, 'à l’administration').replace(/\b(?:le )?panneau développeur/gi, m => /^[LP]/.test(m) ? 'L’administration' : 'l’administration').replace(/propriétaire de la plateforme/gi, 'propriétaire du système');
export function brandSub(s) {
  const n = BRAND_SUB || ((SOLO || SHOW) ? String(UI.solo_system?.[li()] || UI.solo_system?.[1] || '') : '');
  if (!n || typeof s !== 'string' || (s.indexOf('دار') < 0 && s.indexOf('Dar') < 0)) return s;
  const arN = AR_SCRIPT.test(n), al = arN && n.startsWith('ال'); // (its own name may hold the word — «دار الأمان», «Dar Al Arkan» — and stays as it is)
  return s.split(n).join('\uE000').replace(AR_DAR, (m, pre, px) => pre + (px ? (al && px.endsWith('ل') ? px + '\uE001' : px + (arN ? '' : 'ـ') + '\uE000') : '\uE000')).replace(LAT_DAR, '\uE000').split('\uE001').join(n.slice(1)).split('\uE000').join(n);
}
function ownText(key, i) {
  const o0 = TEXTS[key]; if (o0 == null) return '';
  const o = typeof o0 === 'string' ? (AR_SCRIPT.test(o0) ? [o0, '', ''] : ['', o0, o0]) : o0;
  const v = o[i]; if (!v) return '';
  if (i > 0 && key !== 'brand' && v === o[0] && AR_SCRIPT.test(v) && UI[key]?.[i]) return '';
  return v;
}
export function t(key, vars) {
  const i = li(); const o = TEXTS[key]; const base = isBaseLang(LANG.cur);
  let s = base ? (ownText(key, i) || (UI[key] && (UI[key][i] || UI[key][1] || UI[key][0])) || key) // v3.7: a text written in one language shows in it until it is translated
    : (src => src ? tr(src) : key)((typeof o === 'string' ? o : o && (ownText(key, 1) || o[0] || o[2])) || (UI[key] && (UI[key][1] || UI[key][0] || UI[key][2])) || ''); // v3.16: any other language (v3.26: a one-string text too)
  if (SHOW && SHOW_TEXTS[key] && UI[SHOW_TEXTS[key]]) return t(SHOW_TEXTS[key], vars); // v3.30: the buyers' preview says what its example really does (it keeps no key)
  if ((SOLO || SHOW) && key !== 'brand') { if (SOLD_OUT.texts[key] && UI[SOLD_OUT.texts[key]]) return t(SOLD_OUT.texts[key], vars); s = soloRoles(brandSub(s)); } // v3.26: a sold copy's own words (the showcase: its product's name)
  if (vars) { if (!base) s = icu(s, vars, locale()); s = s.replace(/\{(\w+)\}/g, (_, k) => (vars[k] ?? unitVar(k) ?? '')); if (base && /[\d\u0660-\u0669]/.test(s)) s = countFix(s, LANG.cur); }
  else if (s.includes('{au}') || s.includes('{per}')) s = s.replace(/\{(au|per)\}/g, (_, k) => unitVar(k));
  return s;
}
// v3.13: an error's words — its own text when Dar has one, else «error (code)» (never the raw key); a validation reason's words
// likewise: its text, else the reason itself (a developer can still read what it was)
// v3.13: a list reads with the language's own separator («، » in Arabic, «, » elsewhere)
export const LSEP = () => LANG.cur === 'ar' || LANG.cur === 'fa' || LANG.cur === 'ur' || LANG.cur === 'ckb' || LANG.cur === 'ps' ? '، ' : ['zh-Hans', 'zh-Hant', 'ja', 'yue'].includes(LANG.cur) ? '、' : ', ';
// v3.20: a fault inside the server is said plainly to an office, a client or a visitor — what happened and what to do, never
// the panel's «Monitoring» they do not have nor a file to reinstall; the developer keeps the full words
const SERVER_FAULT = ['server_error', 'server_encode', 'server_time', 'server_memory', 'server_fault', 'server_broken'];
export const errText = (e, dflt = 'error') => { const c = e?.code; if (!c) return t(dflt); if (c === 'rate_limited' && +e?.extra?.wait > 0) return t('e_rate_limited_wait', { n: Math.round(+e.extra.wait) }); // (v3.26.1: the minutes left, from the server)
  if (c === 'ai_budget_reached' && e?.extra?.unit && (e.extra.unit !== 'ops' || e.extra.period === 'day')) return t('e_ai_quota', { unit: t('qu_unit_' + e.extra.unit), per: t('qu_per_' + (e.extra.period || 'month')) }); // (v3.32: which allowance ran out — dar-quota.php)
  if (c === 'limit_reached' && e?.extra?.key && +e?.extra?.limit > 0) return t('e_limit_reached_k', { what: t('limk_' + e.extra.key), n: String(+e.extra.limit) }); // (v3.33.21: which limit, and its number)
  if (SERVER_FAULT.includes(c) || ['network', 'timeout', 'bad_response', 'busy'].includes(c)) return t('e_server_quiet'); const k = 'e_' + c; const m = t(k); return m !== k ? m : t('error'); }; // (v3.33.24: never a technical code on the screen — not even the developer's; the watcher keeps it)
export function vText(v) {
  if (Array.isArray(v)) return v.map(vText).join(', ');
  if (v && typeof v === 'object') return Object.entries(v).map(([a, b]) => a + ': ' + vText(b)).join(', ');
  const s = String(v ?? ''); const k = 'v_' + s; const m = t(k); if (m !== k) return m;
  return /^[a-z][a-z0-9_]{0,40}$/.test(s) && !/^\d+$/.test(s) ? t('v_invalid') + ' (' + s + ')' : s;
}
// Counted nouns read correctly in every language: "3 يوم" → "3 أيام", "11 يوم" → "11 يومًا", "1 يوم" → "يوم واحد",
// "2 خدمة" → "خدمتان"; "1 days" → "1 day"; "1 fichier(s) envoyé(s)" → "1 fichier envoyé". Developer texts benefit too.
const AR_NOUNS = { // singular: [dual (oblique, reads right after بعد/منذ/متأخر), plural (3–10), accusative (11–99), feminine]
  'يوم': ['يومين', 'أيام', 'يومًا', 0], 'ساعة': ['ساعتين', 'ساعات', 'ساعة', 1], 'دقيقة': ['دقيقتين', 'دقائق', 'دقيقة', 1], 'شهر': ['شهرين', 'أشهر', 'شهرًا', 0],
  'خدمة': ['خدمتين', 'خدمات', 'خدمة', 1], 'سجل': ['سجلين', 'سجلات', 'سجلًا', 0], 'اشتراك': ['اشتراكين', 'اشتراكات', 'اشتراكًا', 0], 'عملية': ['عمليتين', 'عمليات', 'عملية', 1],
  'رسالة': ['رسالتين', 'رسائل', 'رسالة', 1], 'عقار': ['عقارين', 'عقارات', 'عقارًا', 0], 'طلب': ['طلبين', 'طلبات', 'طلبًا', 0], 'ملف': ['ملفين', 'ملفات', 'ملفًا', 0],
  'صورة': ['صورتين', 'صور', 'صورة', 1], 'ترجمة': ['ترجمتين', 'ترجمات', 'ترجمة', 1], 'عميل': ['عميلين', 'عملاء', 'عميلًا', 0], 'موظف': ['موظفين', 'موظفين', 'موظفًا', 0],
  'وحدة': ['وحدتين', 'وحدات', 'وحدة', 1], 'مهمة': ['مهمتين', 'مهام', 'مهمة', 1], 'فاتورة': ['فاتورتين', 'فواتير', 'فاتورة', 1], 'عقد': ['عقدين', 'عقود', 'عقدًا', 0],
  'مكتب': ['مكتبين', 'مكاتب', 'مكتبًا', 0], 'تغيير': ['تغييرين', 'تغييرات', 'تغييرًا', 0], 'مستخدم': ['مستخدمين', 'مستخدمين', 'مستخدمًا', 0], 'بند': ['بندين', 'بنود', 'بندًا', 0],
  'مستند': ['مستندين', 'مستندات', 'مستندًا', 0], 'موعد': ['موعدين', 'مواعيد', 'موعدًا', 0], 'شريك': ['شريكين', 'شركاء', 'شريكًا', 0], 'دولة': ['دولتين', 'دول', 'دولة', 1],
  'حرف': ['حرفين', 'أحرف', 'حرفًا', 0], 'إعلان': ['إعلانين', 'إعلانات', 'إعلانًا', 0], 'منافس': ['منافسين', 'منافسين', 'منافسًا', 0], 'صف': ['صفين', 'صفوف', 'صفًا', 0], 'عمود': ['عمودين', 'أعمدة', 'عمودًا', 0],
  'مصدر': ['مصدرين', 'مصادر', 'مصدرًا', 0], 'مشاهدة': ['مشاهدتين', 'مشاهدات', 'مشاهدة', 1], 'مرة': ['مرتين', 'مرات', 'مرة', 1],
  'سطر': ['سطرين', 'أسطر', 'سطرًا', 0], 'نص': ['نصين', 'نصوص', 'نصًا', 0], 'عنصر': ['عنصرين', 'عناصر', 'عنصرًا', 0],
  'لغة': ['لغتين', 'لغات', 'لغة', 1], 'منطقة': ['منطقتين', 'مناطق', 'منطقة', 1],
  'جزء': ['جزأين', 'أجزاء', 'جزءًا', 0], 'سرّ': ['سرّين', 'أسرار', 'سرًّا', 0], 'مفتاح': ['مفتاحين', 'مفاتيح', 'مفتاحًا', 0], // (v3.20: the library's parts and the secrets it hid)
  'تشغيل': ['تشغيلين', 'تشغيلات', 'تشغيلًا', 0], 'أتمتة': ['أتمتتين', 'أتمتات', 'أتمتة', 1], 'حساب': ['حسابين', 'حسابات', 'حسابًا', 0], // (v3.20: the rest of what the screens count)
  'سنة': ['سنتين', 'سنوات', 'سنة', 1], 'أسبوع': ['أسبوعين', 'أسابيع', 'أسبوعًا', 0], 'خطوة': ['خطوتين', 'خطوات', 'خطوة', 1], 'صفحة': ['صفحتين', 'صفحات', 'صفحة', 1],
  'ثانية': ['ثانيتين', 'ثوانٍ', 'ثانية', 1], 'نموذج': ['نموذجين', 'نماذج', 'نموذجًا', 0], 'اقتراح': ['اقتراحين', 'اقتراحات', 'اقتراحًا', 0], 'نطاق': ['نطاقين', 'نطاقات', 'نطاقًا', 0],
  'نقرة': ['نقرتين', 'نقرات', 'نقرة', 1], 'ملاحظة': ['ملاحظتين', 'ملاحظات', 'ملاحظة', 1], 'عقدة': ['عقدتين', 'عُقد', 'عقدة', 1], 'حقل': ['حقلين', 'حقول', 'حقلًا', 0],
  'إجراء': ['إجراءين', 'إجراءات', 'إجراءً', 0], 'نتيجة': ['نتيجتين', 'نتائج', 'نتيجة', 1], 'زيارة': ['زيارتين', 'زيارات', 'زيارة', 1], 'مدينة': ['مدينتين', 'مدن', 'مدينة', 1],
  'متطلب': ['متطلبين', 'متطلبات', 'متطلبًا', 0], 'جلسة': ['جلستين', 'جلسات', 'جلسة', 1], 'درس': ['درسين', 'دروس', 'درسًا', 0], 'ذكرى': ['ذكريين', 'ذكريات', 'ذكرى', 1],
  'استدعاء': ['استدعاءين', 'استدعاءات', 'استدعاءً', 0], 'ادعاء': ['ادعاءين', 'ادعاءات', 'ادعاءً', 0], 'رد': ['ردين', 'ردود', 'ردًا', 0], 'إعداد': ['إعدادين', 'إعدادات', 'إعدادًا', 0],
  'تذكير': ['تذكيرين', 'تذكيرات', 'تذكيرًا', 0], 'حي': ['حيين', 'أحياء', 'حيًا', 0], 'شخص': ['شخصين', 'أشخاص', 'شخصًا', 0],
  'صفقة': ['صفقتين', 'صفقات', 'صفقة', 1], 'حجز': ['حجزين', 'حجوزات', 'حجزًا', 0], 'دفعة': ['دفعتين', 'دفعات', 'دفعة', 1], 'مشروع': ['مشروعين', 'مشاريع', 'مشروعًا', 0], 'مسوق': ['مسوقين', 'مسوقين', 'مسوقًا', 0], 'معاينة': ['معاينتين', 'معاينات', 'معاينة', 1], // (v3.30: the business's pulse)
};
// v3.20: two of a thing is «…ان» where it is the subject — at the start, after «:» «(» «—» «·» «،», or after a passive or
// intransitive verb («حُفظ مفتاحان», «تم: ملفان») — and «…ين» after a preposition, a noun it belongs to or a verb it is the
// object of («خلال يومين», «من أتمتتين», «وجدنا صفين»); «مرتين» is always so (how often, not who)
const AR_NOM_AFTER = new Set(['أُرسلت', 'أُرسل', 'تُرجم', 'تُرجمت', 'جُهّز', 'جُهزت', 'استُخدمت', 'استُخدم', 'وُضعت', 'وُضع', 'أُلغيت', 'أُلغي', 'فُحصت', 'فُحص', 'نُفّذ', 'نُفّذت', 'حُفظ', 'حُفظت', 'حُذف', 'حُذفت', 'رُصد', 'سُجلت', 'سُجل', 'أُضيف', 'أُضيفت', 'أُخفي', 'أُخفيت', 'ستفشل', 'تفشل', 'يفشل', 'فشل', 'فشلت', 'نجح', 'نجحت', 'يعمل', 'تعمل', 'وصل', 'وصلت', 'عاد', 'بقي', 'بقيت', 'تبقى', 'يتبقى', 'لديك', 'لديه', 'لدينا', 'عندك', 'عنده', 'هناك', 'يوجد', 'توجد', 'تستخدمها', 'يستخدمها', 'تستخدمه', 'يستخدمه', 'ينتظر', 'تنتظر', 'ينتظرك', 'تنتظرك']);
const AR_TIME = new Set(['يوم', 'ساعة', 'دقيقة', 'شهر', 'أسبوع', 'سنة', 'ثانية']); // (after a verb, a span of time is how long — «ينتظر ساعتين»)
const arDual = (sg, du, before) => { if (sg === 'مرة' || !du.endsWith('ين')) return du; const w = (/(\S+)\s*$/.exec(before) || ['', ''])[1]; return w === '' || /[(:—–·،«\n-]$/.test(w) || (!AR_TIME.has(sg) && AR_NOM_AFTER.has(w)) ? du.slice(0, -2) + 'ان' : du; };
const AR_FORM = {}; for (const [sg, [du, pl, acc]] of Object.entries(AR_NOUNS)) for (const f of [sg, du, du.replace(/ين$/, 'ان'), pl, acc, acc.replace('ً', '')]) AR_FORM[f] = sg;
// (v3.20: a number glued to a Latin name or to another number is not a count — «🔑K1 مفتاح Groq», «1/2 ساعة», «1-2 يوم» stay as written)
const AR_RE = new RegExp('(^|[^A-Za-z\\d\u0660-\u0669,٬._#/\\-\u2013])([\\d\u0660-\u0669][\\d\u0660-\u0669,٬]*)\\s+(' + Object.keys(AR_FORM).sort((a, b) => b.length - a.length).join('|') + ')(?=$|[\\s،.؛:)!؟,»])', 'g');
const EN_ONE = { days: 'day', hours: 'hour', minutes: 'minute', months: 'month', services: 'service', files: 'file', records: 'record', leads: 'lead', clients: 'client', properties: 'property', requests: 'request', photos: 'photo', translations: 'translation', invoices: 'invoice', tasks: 'task', users: 'user', units: 'unit', contracts: 'contract', offices: 'office', changes: 'change', subscriptions: 'subscription', operations: 'operation', messages: 'message', items: 'item', employees: 'employee', documents: 'document', signatures: 'signature', partners: 'partner', countries: 'country', listings: 'listing', rows: 'row', columns: 'column', times: 'time', sources: 'source', competitors: 'competitor', views: 'view', parts: 'part', characters: 'character', secrets: 'secret', keys: 'key' };
const FR_ONE = { jours: 'jour', heures: 'heure', minutes: 'minute', services: 'service', fichiers: 'fichier', enregistrements: 'enregistrement', prospects: 'prospect', clients: 'client', biens: 'bien', demandes: 'demande', photos: 'photo', traductions: 'traduction', factures: 'facture', tâches: 'tâche', utilisateurs: 'utilisateur', lots: 'lot', contrats: 'contrat', agences: 'agence', changements: 'changement', abonnements: 'abonnement', opérations: 'opération', messages: 'message', éléments: 'élément', employés: 'employé', documents: 'document', signatures: 'signature', partenaires: 'partenaire', pays: 'pays', annonces: 'annonce', lignes: 'ligne', colonnes: 'colonne', fois: 'fois', sources: 'source', concurrents: 'concurrent', vues: 'vue', parties: 'partie', caractères: 'caractère' };
const toNum = d => +String(d).replace(/[\u0660-\u0669]/g, x => '٠١٢٣٤٥٦٧٨٩'.indexOf(x)).replace(/[,٬]/g, '');
export function countFix(s, lang) {
  if (lang === 'ar') {
    let pr; try { pr = new Intl.PluralRules('ar'); } catch { return s; }
    return s.replace(AR_RE, (all, pre, num, word, at, whole) => {
      const sg = AR_FORM[word]; const [du, pl, acc, fem] = AR_NOUNS[sg]; const cat = pr.select(toNum(num));
      if (cat === 'one') return pre + sg + (fem ? ' واحدة' : ' واحد');
      if (cat === 'two') return pre + arDual(sg, du, whole.slice(0, at) + pre);
      return pre + num + ' ' + (cat === 'few' || cat === 'zero' ? pl : cat === 'many' ? acc : sg);
    });
  }
  const first = s.match(/[\d][\d,.\u202f\u00a0 ]*/); const n = first ? toNum(first[0].replace(/[\s\u202f\u00a0]/g, '')) : null;
  if (n != null && s.includes('(s)')) s = s.replace(/\(s\)/g, (lang === 'fr' ? n < 2 : n === 1) ? '' : 's');
  const ONE = lang === 'fr' ? FR_ONE : lang === 'en' ? EN_ONE : null; if (!ONE) return s;
  return s.replace(new RegExp('(^|[^\\d.,])(' + (lang === 'fr' ? '[01]' : '1') + ')\\s+(' + Object.keys(ONE).join('|') + ')(?![\\wÀ-ÿ])', 'g'), (all, pre, num, w) => pre + num + ' ' + ONE[w]);
}
// v3.16: in any other language a text given in three ([ar, en, fr] or {ar, en, fr}) reads its own language when it has it
// ({…, es: '…'}), else the pack's translation of its English (or of the language it was written in)
const srcOf = v => Array.isArray(v) ? (v[1] || v[0] || v[2] || '') : (v.en || v.ar || v.fr || '');
export const L = v => (v != null && typeof v === 'object' && (SOLO || SHOW) ? brandSub(L0(v)) : L0(v)); // (v3.26: a sold copy's names — v3.29: before it is named too)
const L0 = v => { if (v == null) return ''; if (typeof v === 'string') return v; if (!isBaseLang(LANG.cur)) { if (!Array.isArray(v) && typeof v === 'object' && typeof v[LANG.cur] === 'string' && v[LANG.cur]) return v[LANG.cur]; return tr(String(srcOf(v) || '')); } const i = li(); if (!Array.isArray(v) && typeof v === 'object') { const k = ['ar', 'en', 'fr']; return String(v[k[i]] || v.en || v.ar || v.fr || ''); } return v[i] || v[1] || v[0] || ''; }; // (v3.11.1: {ar, en, fr} reads too)
// Per-language resolution: a developer edit in one language never leaks into another language that has its own text.
export const Lx = (...vs) => { if (!isBaseLang(LANG.cur)) { for (const v of vs) if (v && typeof v === 'object' && !Array.isArray(v) && typeof v[LANG.cur] === 'string' && v[LANG.cur]) return v[LANG.cur]; for (const v of vs) { if (!v) continue; const s = typeof v === 'string' ? v : srcOf(v); if (s) return tr(s); } return ''; } const i = li(); for (const v of vs) if (v && typeof v !== 'string' && v[i]) return v[i]; for (const v of vs) { const x = L(v); if (x) return x; } return ''; };
export const merge3 = (o, d) => (o || d) ? [0, 1, 2].map(i => (o && o[i]) || (d && d[i]) || '') : o;
export const missing3 = v => !v ? [0, 1, 2] : [0, 1, 2].filter(i => !String(v[i] || '').trim());
// a collection may rename a shared field (hr_attendance.method is "recorded via", not "payment method"): 'coll.key' wins
// v3.33 (the owner, 2026-10-22: «يجب أن يُصرف للمسوق من خلال الآيبان الذي يدخله في الموقع»): an IBAN, checked as banks check it —
// its country's length (ISO 13616) and its two check digits (mod 97); the spaces people type are taken away
const IBAN_LEN = { AD: 24, AE: 23, AL: 28, AT: 20, AZ: 28, BA: 20, BE: 16, BG: 22, BH: 22, BR: 29, BY: 28, CH: 21, CR: 22, CY: 28, CZ: 24, DE: 22, DK: 18, DO: 28, DZ: 26, EE: 20, EG: 29, ES: 24, FI: 18, FO: 18, FR: 27, GB: 22, GE: 22, GI: 23, GL: 18, GR: 27, GT: 28, HR: 21, HU: 28, IE: 22, IL: 23, IQ: 23, IS: 26, IT: 27, JO: 30, KW: 30, KZ: 20, LB: 28, LC: 32, LI: 21, LT: 20, LU: 20, LV: 21, LY: 25, MA: 28, MC: 27, MD: 24, ME: 22, MK: 19, MR: 27, MT: 31, MU: 30, NL: 18, NO: 15, OM: 23, PK: 24, PL: 28, PS: 29, PT: 25, QA: 29, RO: 24, RS: 22, SA: 24, SC: 31, SD: 18, SE: 24, SI: 19, SK: 24, SM: 27, ST: 25, SV: 28, TL: 23, TN: 24, TR: 26, UA: 29, VA: 22, VG: 24, XK: 20, YE: 30 };
export function ibanCheck(v) {
  const s = String(v || '').toUpperCase().replace(/[\s\-.]/g, ''); if (!s) return { ok: false, why: 'required' };
  if (!/^[A-Z]{2}\d{2}[A-Z0-9]{11,30}$/.test(s)) return { ok: false, why: 'format', iban: s };
  const want = IBAN_LEN[s.slice(0, 2)]; if (want && s.length !== want) return { ok: false, why: 'length', iban: s, want };
  const r = (s.slice(4) + s.slice(0, 4)).replace(/[A-Z]/g, ch => String(ch.charCodeAt(0) - 55)); let m = 0; for (const d of r) m = (m * 10 + +d) % 97;
  return m === 1 ? { ok: true, iban: s } : { ok: false, why: 'check', iban: s };
}
export const ibanShow = s => (String(s || '').length > 8 ? String(s).slice(0, 4) + '…' + String(s).slice(-4) : String(s || ''));
// v3.33: the name on screen of a setting or a field an assistant's reply named by its key (assets/plain.js) — '' when Dar has none
const PLAIN_ALIAS = { 'maintenance.on': 'plain_k_maintenance', maintenance: 'plain_k_maintenance', master_key: 'plain_k_master_key', wa_gateway: 'plain_k_wa_gateway', 'wa.gateway': 'plain_k_wa_gateway' };
export function plainLabelOf(key) {
  const k = String(key || '').trim(); if (!k) return '';
  if (PLAIN_ALIAS[k]) return t(PLAIN_ALIAS[k]);
  const flat = k.replace(/^P\./, '').replace(/\./g, '_'); if (UI['keys_f_' + flat]) return t('keys_f_' + flat);
  const last = k.split('.').pop(); if (FIELDS[flat]) return fieldLabel(flat); if (FIELDS[last] && last.length > 2) return fieldLabel(last);
  return '';
}
export const fieldLabel = (k, coll) => { const ck = coll ? coll + '.' + k : null; const s = (ck && (TEXTS['f:' + ck] || FIELDS[ck]) ? Lx(TEXTS['f:' + ck], FIELDS[ck]) : '') || Lx(TEXTS['f:' + k], FIELDS[k]) || humanize(k); return s.includes('{au}') ? s.replace('{au}', unitVar('au')) : s; };
export const optLabel = v => { const s = Lx(TEXTS['o:' + v], (SOLO || SHOW) && SOLD_OUT.opts?.[v] && !TEXTS['o:' + v] ? SOLD_OUT.opts[v] : OPTS[v]) || humanize(v); return SOLO || SHOW ? brandSub(s) : s; }; // (v3.26: a sold copy's words)
export const collLabel = c => Lx(TEXTS['c:' + c], R.COLL[c], CCOLL[c]) || humanize(c);
export const actLabel = a => Lx(TEXTS['a:' + a], R.ACTS[a]) || humanize(a);
export const catLabel = (c, P) => Lx(P?.cats?.[c], TEXTS['cat:' + c], R.CATS[c]) || humanize(c);
export const roleLabel = (k, P) => Lx(P?.ai?.roles?.[k]?.n, TEXTS['r:' + k], ROLES[k]) || humanize(k);
// v3.16: any language, written the way the visitor's country writes it (es + MX → es-MX) when the browser knows that locale
const LOCS = new Map();
export function locale() {
  let base = LANGS[LANG.cur]?.locale;
  if (!base) { const key = LANG.cur + '|' + (LANG.cc || ''); base = LOCS.get(key); if (!base) { base = 'en-GB'; for (const cand of [LANG.cc && !LANG.cur.includes('-') ? LANG.cur + '-' + LANG.cc : '', LANG.cur]) { if (!cand) continue; try { const c = Intl.getCanonicalLocales(cand)[0]; if (Intl.NumberFormat.supportedLocalesOf([c]).length) { base = c; break; } } catch { /* not a tag the browser knows */ } } LOCS.set(key, base); } }
  if (LANG.cal === 'islamic') return base.includes('-u-') ? base.replace(/ca-[a-z]+/, 'ca-islamic-umalqura') : base + '-u-ca-islamic-umalqura';
  return base;
}
export const isRtl = () => LANGS[LANG.cur] ? LANGS[LANG.cur].dir === 'rtl' : isRtlLang(LANG.cur);
export const langName = code => langInfo(code)?.name || LANGS[code]?.name || code;
export const langEn = code => langEnglish(code);
export const knownLang = x => typeof x === 'string' && (isBaseLang(x) || !!langInfo(x)); // v3.16: any language of the catalogue

// ---------------------------------------------------------------- formatting
const THREE_DEC = ['KWD', 'BHD', 'OMR', 'JOD', 'TND', 'LYD'];
export function fmtNum(v, max = 0) { if (v == null || v === '' || !isFinite(+v)) return '—'; try { return new Intl.NumberFormat(locale(), { maximumFractionDigits: max }).format(+v); } catch { return String(v); } }
export function fmtMoney(v, cur = 'SAR') {
  if (v == null || v === '' || !isFinite(+v)) return t('on_request');
  const n = +v; const dec = Number.isInteger(n) ? 0 : (THREE_DEC.includes(cur) ? 3 : 2);
  try { return new Intl.NumberFormat(locale(), { style: 'currency', currency: cur, minimumFractionDigits: dec, maximumFractionDigits: dec }).format(n); } catch { return fmtNum(n, dec) + ' ' + cur; }
}
export function fmtPct(v, max = 1) { return v == null || !isFinite(+v) ? '—' : fmtNum(v, max) + '%'; }
export function fmtDate(v, time = false) {
  if (!v) return '—'; const d = new Date(v); if (isNaN(d)) return String(v);
  try { return new Intl.DateTimeFormat(locale(), time ? { dateStyle: 'medium', timeStyle: 'short' } : { dateStyle: 'medium' }).format(d); } catch { return d.toISOString().slice(0, time ? 16 : 10); }
}
export function fmtAgo(v) {
  if (!v) return '—'; const d = new Date(v); if (isNaN(d)) return String(v);
  const diff = (d - Date.now()) / 1000; const abs = Math.abs(diff);
  const [n, u] = abs < 60 ? [diff, 'second'] : abs < 3600 ? [diff / 60, 'minute'] : abs < 86400 ? [diff / 3600, 'hour'] : abs < 2592000 ? [diff / 86400, 'day'] : abs < 31536000 ? [diff / 2592000, 'month'] : [diff / 31536000, 'year'];
  try { return new Intl.RelativeTimeFormat(locale(), { numeric: 'auto' }).format(Math.round(n), u); } catch { return fmtDate(v); }
}

// ---------------------------------------------------------------- schema helpers
// Schemas the developer controls from his panel: fields of his own services (custom_ent), extra fields added to any
// built-in collection (ent_extra), extra choices for built-in lists (ent_opts) and optional fields he hides (ent_hide).
// The interface sets them from bootstrap; a server (no interface) reads them from the stored platform document, so a
// service the developer adds works the same in the browser model and on a live server.
let SCHEMA = null, _schemaRaw = null, _schemaStored = null;
const schemaOf = p => ({ custom_ent: p?.custom_ent || {}, ent_extra: p?.ent_extra || {}, ent_opts: p?.ent_opts || {}, ent_hide: p?.ent_hide || {}, chan_policy: p?.channel_policy && typeof p.channel_policy === 'object' ? p.channel_policy : {} });
export function setSchema(P) { SCHEMA = schemaOf(P); CCOLL = Object.fromEntries((Array.isArray(P?.custom) ? P.custom : []).filter(x => x && typeof x === 'object').flatMap(x => (Array.isArray(x.e) ? x.e : []).map(c => [c, x.n]))); }
let CCOLL = {}; // v3.5: a service the developer added names its own list (its counter read «Qa Valuation 0»)
export function setCustomEnt(x) { SCHEMA = { ...(SCHEMA || schemaOf({})), custom_ent: x || {} }; }
function schema() {
  if (SCHEMA) return SCHEMA;
  const raw = rawGet('platform'); if (raw !== _schemaRaw) { _schemaRaw = raw; let p = {}; try { p = JSON.parse(raw || 'null') || {}; } catch { p = {}; } _schemaStored = schemaOf(p); }
  return _schemaStored || (_schemaStored = schemaOf({}));
}
export const entSpec = coll => { const sc = schema(); const base = R.ENT[coll] || sc.custom_ent[coll] || ''; const extra = sc.ent_extra[coll]; return extra ? (base ? base + '|' + extra : extra) : base; };
export const fieldsOf = coll => {
  const sc = schema(); const seen = new Set(); const opts = sc.ent_opts[coll] || {}; const hide = sc.ent_hide[coll] || [];
  const cp = Array.isArray(sc.chan_policy[coll]) && sc.chan_policy[coll].length ? sc.chan_policy[coll].map(String) : null; // (v3.33, note 56: the channels the developer allows here)
  return R.parseFields(entSpec(coll)).filter(f => !seen.has(f.key) && seen.add(f.key)).map(f => ({ ...f, ...(f.type === 'sel' && opts[f.key] ? { options: [...new Set([...f.options, ...opts[f.key]])] } : {}), ...(cp && f.type === 'sel' && f.key === 'channel' ? { options: f.options.filter(o => cp.includes(o) || (o === 'app' && cp.includes('app'))) } : {}), ...(cp && f.type === 'channels' ? { allow: cp } : {}), ...(hide.includes(f.key) && !f.req ? { hidden: true } : {}) }));
};
export function cleanRow(fields, input, partial = false) {
  const row = {}, errors = {};
  for (const f of fields) {
    if (!(f.key in input)) { if (!partial && f.req) errors[f.key] = 'required'; continue; }
    let v = input[f.key];
    const empty = v === '' || v == null || (Array.isArray(v) && !v.length);
    if (empty) { if (f.req) errors[f.key] = 'required'; row[f.key] = f.type === 'bool' ? false : (['tags', 'images'].includes(f.type) ? [] : (f.type === 'json' ? {} : '')); continue; }
    switch (f.type) {
      case 'num': case 'money': case 'percent': case 'rating': {
        const n = Number(latinDigits(v).replace(/[,\s٬]/g, '').replace('٫', '.'));
        if (!isFinite(n)) { errors[f.key] = 'number'; break; }
        if (f.type === 'percent' && (n < 0 || n > 100)) { errors[f.key] = 'range'; break; }
        if (f.type === 'rating' && (n < 1 || n > 5)) { errors[f.key] = 'range'; break; }
        if ((f.type === 'money') && n < 0) { errors[f.key] = 'range'; break; }
        row[f.key] = n; break;
      }
      case 'bool': row[f.key] = v === true || v === 'true' || v === 'on' || v === 1 || v === '1'; break;
      case 'email': { const s = String(v).trim().toLowerCase(); if (!/^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/.test(s)) errors[f.key] = 'email'; else row[f.key] = s; break; }
      case 'phone': { const s = latinDigits(v).replace(/[^\d+]/g, ''); if (s.replace('+', '').length < 7 || s.length > 16) errors[f.key] = 'phone'; else row[f.key] = s; break; }
      case 'url': { const s = String(v).trim(); if (!/^https?:\/\/[^\s<>"']+$/i.test(s)) errors[f.key] = 'url'; else row[f.key] = s; break; }
      case 'sel': if (!f.options.includes(v)) errors[f.key] = 'option'; else row[f.key] = v; break;
      case 'tags': row[f.key] = (Array.isArray(v) ? v : String(v).split(/[,،]/)).map(s => String(s).trim()).filter(Boolean).filter(x => f.ui !== 'multi' || !f.options?.length || f.options.includes(x)).slice(0, 50); break;
      case 'json': if (typeof v === 'object') row[f.key] = v; else { try { row[f.key] = JSON.parse(v); } catch { errors[f.key] = 'json'; } } break;
      case 'images': row[f.key] = (Array.isArray(v) ? v : [v]).filter(x => typeof x === 'string' && IMG_OK.test(x)).slice(0, 12); break;
      case 'image': case 'file': { const s = String(v); if (!/^(data:|https:\/\/|dar-sync\.php\?f=[0-9a-f]{48}$)/.test(s)) errors[f.key] = 'url'; else row[f.key] = s; break; }
      case 'color': if (!/^#[0-9a-f]{6}$/i.test(v)) errors[f.key] = 'color'; else row[f.key] = v; break;
      case 'date': case 'datetime': { const d = new Date(v); if (isNaN(d)) errors[f.key] = 'date'; else row[f.key] = String(v); break; }
      case 'ref': row[f.key] = String(v).slice(0, 80); break;
      case 'time': { const m = /^([01]?\d|2[0-3]):([0-5]\d)/.exec(latinDigits(v).trim()); if (!m) errors[f.key] = 'time'; else row[f.key] = m[1].padStart(2, '0') + ':' + m[2]; break; }
      case 'secret': row[f.key] = /^…\S{1,8}$/.test(String(v)) ? String(v) : ''; break; // v3.5: a record keeps only the last characters of a key (the key is in the server's vault)
      default: row[f.key] = String(v).slice(0, f.type === 'area' ? 20000 : 500);
    }
  }
  return { row, errors };
}

// ---------------------------------------------------------------- catalog (registry + developer overrides)
export function catalog(P) {
  P = P || {};
  const over = P.services || {};
  const custom = Array.isArray(P.custom) ? P.custom.filter(c => c && typeof c === 'object' && !Array.isArray(c) && c.id) : []; // v3.11.1: a wrong value never stops the pages
  const list = [...R.SERVICES, ...custom.map(c => ({ e: [], a: [], c: [], t: [], k: [], s: '', screen: 'generic', plans: [], status: 'active', ...c, custom: true }))];
  const orderOf = s => (over[s.id]?.order ?? list.indexOf(s));
  return list.map(s => {
    const o = over[s.id] || {};
    const m = { ...s, ...o, n: s.custom ? (o.n || s.n) : merge3(o.n, s.n), d: s.custom ? (o.d || s.d) : merge3(o.d, s.d), t: o.t || s.t, plans: o.plans || s.plans, cat: o.cat || s.cat, order: orderOf(s) };
    if (o.extra_acts) m.xa = o.extra_acts;
    if (s.custom && s.acts) m.xa = [...(s.acts || []), ...(o.extra_acts || [])];
    // v3.33.12 (the owner, 2026-10-24: «أبقيت خدمات متعلقة بمتطلبات غير مفعلة»): a copy of an office's service in another interface (a
    // developer company's «b_…») that he never set on its own follows the office's when he marked it «soon» or under maintenance
    if (s.share && !o.status && m.status === 'active' && ['soon', 'maintenance'].includes(over[s.share]?.status)) m.status = over[s.share].status;
    // v3.32: a service that cannot work without a feature the developer stopped follows it (off: hidden; maintenance or soon: marked)
    const fs = svcFeatState(P, m);
    if (fs === 'off' && m.status !== 'hidden') { m.status = 'hidden'; m.feat = 'off'; }
    else if (fs === 'maintenance' && ['active', 'soon'].includes(m.status)) { m.status = 'maintenance'; m.feat = 'maintenance'; }
    else if (fs === 'soon' && m.status === 'active') { m.status = 'soon'; m.feat = 'soon'; }
    return m;
  }).sort((a, b) => a.order - b.order);
}
// v3.33 (the owner, 2026-10-22 — notes 40 and 44: «الدول المجهزة عددها 16 وهذا غير صحيح», «الخدمات في المنظومة يجب أن تعكس العدد الفعلي»): the figures
// the overview, the home page and the examples print. A service is counted once however many apps carry it (a developer's «b_…» copy of an
// office service shares its id), the panel's own screens are not services of the platform's subscribers, and a service that is «soon»,
// stopped or hidden is counted apart — the number a visitor reads is what he can use today.
export const SUB_APPS = ['app', 'partner', 'builders', 'providers', 'console'];
export function svcCounts(services) {
  const rank = { active: 0, maintenance: 1, soon: 2, suspended: 3, hidden: 4 }; const best = new Map(); const byApp = {};
  for (const s of services || []) {
    if (!SUB_APPS.includes(s.app)) continue; const k = s.share || s.id; const st = rank[s.status] === undefined ? 'active' : s.status;
    if (!best.has(k) || rank[st] < rank[best.get(k)]) best.set(k, st);
    if (st === 'active') byApp[s.app] = (byApp[s.app] || 0) + 1;
  }
  const out = { total: best.size, active: 0, maintenance: 0, soon: 0, suspended: 0, hidden: 0, byApp };
  for (const st of best.values()) out[st]++; return out;
}
// the countries a person can really choose: his own rows that are on, plus every other country of the world while the platform is open to all
export function countryCounts(rows, P) {
  const W = worldOf(P); const own = (rows || []).filter(c => c.enabled !== false); const extra = W.mode === 'all' ? Object.keys(R.WORLD).filter(k => !W.blocked.includes(k) && !(rows || []).some(c => c.code === k)).length : 0;
  return { open: own.length + extra, configured: own.length, rows: (rows || []).length, off: (rows || []).length - own.length, blocked: W.blocked.length, world: Object.keys(R.WORLD).length, mode: W.mode };
}
export function catsFor(app, P, services) {
  const inApp = [...new Set(services.filter(s => s.app === app).map(s => s.cat))];
  const ord = P?.catOrder?.[app] || R.CAT_ORDER?.[app];
  if (ord) return [...ord.filter(c => inApp.includes(c)), ...inApp.filter(c => !ord.includes(c))];
  return inApp;
}
// Subscriber team roles: which menu categories / services a role may open (developer can override per app).
export function roleAllows(app, role, svc, P) {
  if (!svc || !role || role === 'owner') return true;
  const map = P?.tenant_roles?.[app] || R.TENANT_ROLES?.[app]; if (!map) return true;
  const allowed = map[role]; if (!allowed) return false;
  return allowed.includes('*') || allowed.includes(svc.cat) || allowed.includes(svc.id) || (svc.share && allowed.includes(svc.share)) || (R.ROLE_ALWAYS || []).includes(svc.id);
}
export function audienceOf(app) { return ({ app: 'office', builders: 'builder', providers: 'provider', console: 'console', partner: 'partner', developer: 'dev' })[app] || 'public'; }
// Access decision for one service in one context: ok | hidden | suspended | soon | country | plan
export function access(svc, ctx) {
  if (!svc) return 'hidden';
  if (ctx.dev) return svc.status === 'hidden' ? 'hidden_dev' : 'ok';
  if (svc.status === 'hidden') return 'hidden';
  if (svc.status === 'suspended') return 'suspended';
  if (svc.status === 'maintenance') return 'maintenance'; // v3.32: «تحت الصيانة» (the developer's status, or a feature it needs)
  if (svc.countries && ctx.country && (svc.countries[ctx.country] === false || (ctx.intl && svc.countries['*'] === false))) return 'country'; // '*' = every country outside his rows
  if (svc.status === 'soon') return 'soon';
  if (ctx.trial) return 'ok'; // v3.5.1: the free trial opens every service of the account's interface (the owner can turn this off)
  if (Array.isArray(ctx.tsvc)) return planHas({ services: ctx.tsvc }, svc) ? 'ok' : 'plan'; // v3.32: a trial of chosen services (dar-trials.php)
  const audPlans = (ctx.plans || []).filter(p => p.audience === ctx.audience).map(p => p.code);
  const gated = (svc.plans || []).filter(c => audPlans.includes(c));
  const unlocked = (ctx.unlocked || []).includes(svc.id) || !!(svc.share && (ctx.unlocked || []).includes(svc.share));
  if (gated.length && ctx.plan && !gated.includes(ctx.plan) && !unlocked) return 'plan';
  // v3.5: a plan that lists its services explicitly (the plan's «services» field) includes exactly those — the account,
  // subscription and help screens always stay open so a subscriber can still upgrade
  const mine = ctx.plan && (ctx.plans || []).find(p => p.code === ctx.plan && p.audience === ctx.audience);
  if (mine && Array.isArray(mine.services) && mine.services.length && !planHas(mine, svc) && !unlocked) return 'plan';
  return 'ok';
}
// v3.5.1: an account in its free trial (not yet over) tries everything, unless the owner set «trial_all» off
// v3.32: a trial with its own terms (dar-trials.php: the account's «trial») — everything, its plan's services, or services chosen
export const trialRunning = T => !!T && T.status === 'trial' && (!T.trial_end || Date.parse(T.trial_end) > Date.now());
export const trialOpen = (T, P) => { if (!trialRunning(T)) return false; const sc = T.trial?.scope; return sc === 'all' ? true : sc === 'plan' || sc === 'custom' ? false : P?.trial_all !== false; };
export const trialSvcs = T => trialRunning(T) && T.trial?.scope === 'custom' && Array.isArray(T.trial.services) ? T.trial.services : null;
// a trial link (?trial=CODE) is kept until the visitor signs up, as a partner's link is
export function keepTrial(code) { const c = String(code || '').trim(); if (/^[A-Za-z0-9][A-Za-z0-9_-]{1,39}$/.test(c)) store.set('pref:trial', c); }
export const planHas = (plan, svc) => ['account', 'b_account', 'pr_account'].includes(svc.cat) || ALWAYS_OPEN.includes(svc.id) || (plan.services || []).includes(svc.id) || !!(svc.share && (plan.services || []).includes(svc.share));
export const ALWAYS_OPEN = ['help', 'settings', 'subscription', 'b_settings', 'b_subscription', 'b_help', 'pr_settings', 'pr_subscription', 'pr_help', 'p_help', 'c_plans', 'c_overview', 'today', 'command', 'b_dashboard', 'b_command', 'pr_dashboard', 'p_dashboard'];

// ---------------------------------------------------------------- countries, prices and tax
// Every country (v2.4): the developer's rows are overrides; any other ISO country works with an international profile unless he
// blocks it or limits the platform to his rows (P.world). Local-currency rates come from P.fx (an FX worker or the developer),
// else from one of his rows using the same currency, else prices show in US dollars. Never another country's tax or currency.
let WORLD_P = null; export const setWorldP = P => { WORLD_P = P || null; };
const WORLD_DEF = { mode: 'all', blocked: [], currency: 'local', tax_rate: 0, tax_label: '', price_display: 'excl', gateways: ['stripe', 'paypal'] };
export function worldOf(P) {
  const w = (P && P.world) || {}; const codes = v => [...new Set((Array.isArray(v) ? v : []).map(x => String(x).trim().toUpperCase()).filter(x => R.WORLD[x]))];
  const rate = +w.tax_rate; const gw = (Array.isArray(w.gateways) ? w.gateways : []).map(x => String(x).trim().toLowerCase()).filter(x => /^[a-z0-9_-]{2,30}$/.test(x)).slice(0, 12);
  return { mode: w.mode === 'listed' ? 'listed' : 'all', blocked: codes(w.blocked), currency: w.currency === 'usd' ? 'usd' : 'local', tax_rate: rate >= 0 && rate <= 100 ? rate : 0, tax_label: String(w.tax_label || '').slice(0, 20), price_display: w.price_display === 'incl' ? 'incl' : 'excl', gateways: gw.length ? gw : [...WORLD_DEF.gateways] };
}
export function fxOf(P) { const out = {}; for (const [k, v] of Object.entries((P && P.fx) || {})) if (/^[A-Z]{3}$/.test(k) && +v > 0 && +v < 1e7) out[k] = +v; return out; }
// may this country be chosen / sign up? his rows decide for his countries (enabled), the world list for every other one
export function countryOpen(code, countries, P) {
  const c = String(code || '').trim().toUpperCase(); const row = (countries || []).find(x => x.code === c);
  if (row) return row.enabled !== false;
  const w = worldOf(P || WORLD_P || getP()); return w.mode === 'all' && !!R.WORLD[c] && !w.blocked.includes(c);
}
function intlCountry(code, P, list) {
  // the office always works in its own currency (currency); Dar bills it in that currency when the rate is known, else in US dollars (bill_currency)
  const w = worldOf(P); const W = R.WORLD[code]; let bill_currency = 'USD', usd_rate = 1;
  if (w.currency === 'local' && W.cur !== 'USD') { const r = fxOf(P)[W.cur] || +((list || []).find(c => c.currency === W.cur && +c.usd_rate > 0)?.usd_rate || 0); if (r > 0) { bill_currency = W.cur; usd_rate = r; } }
  return { code, name_ar: '', name_en: '', name_fr: '', currency: W.cur, bill_currency, usd_rate, tax_label: w.tax_label, tax_rate: +w.tax_rate > 0 ? w.tax_rate : (R.STD_TAX[code] || 0), price_display: w.price_display, default_lang: W.lang, calendar: 'gregory', tz: W.tz, area_unit: W.unit, dial: W.dial, ad_permit_label: '', ad_permit_required: false, gateways: w.gateways, enabled: true, intl: true };
}
const rowDefaults = c => (c.area_unit && c.dial ? c : { ...c, area_unit: c.area_unit || R.WORLD[c.code]?.unit || 'm2', dial: c.dial || R.WORLD[c.code]?.dial || '' });
export const billCur = c => c?.bill_currency || c?.currency || 'SAR';
// a phone number as WhatsApp and tel: links need it (country code, no trunk prefix) — numbers are stored as people type them
export function intlPhone(phone, code) {
  let d = latinDigits(String(phone || '')).trim(); if (!d) return '';
  if (d.startsWith('+')) return d.replace(/\D/g, '');
  d = d.replace(/\D/g, ''); if (d.startsWith('00')) return d.slice(2);
  const W = R.WORLD[String(code || '').toUpperCase()]; if (!W || !d) return d;
  if (W.np && d.startsWith(W.np) && d.length - W.np.length >= 6) return W.dial + d.slice(W.np.length);
  if (d.startsWith(W.dial) && d.length >= W.dial.length + 8) return d;
  return W.dial + d;
}
export function countryBy(code, countries, P) {
  const list = countries || []; const hit = list.find(c => c.code === code); if (hit) return rowDefaults(hit);
  const PP = P || WORLD_P || getP();
  if (code && countryOpen(code, list, PP)) return intlCountry(String(code).trim().toUpperCase(), PP, list);
  return rowDefaults(list.find(c => c.code === PP?.default_country) || list[0] || { code: 'SA', currency: 'SAR', usd_rate: 3.75, tax_rate: 15, tax_label: 'VAT', price_display: 'inherit' });
}
export function taxMode(country, P) { const m = country?.price_display; return m && m !== 'inherit' ? m : (P?.price_display || 'incl'); }
function roundPrice(v, cur) { if (v <= 0) return 0; return THREE_DEC.includes(cur) ? Math.ceil(v * 2) / 2 : Math.ceil(v); }
// Price the customer sees before tax logic (the developer decides whether it includes tax).
export function listPrice(item, country, P) {
  if (!item) return null;
  const own = item.prices && item.prices[country.code];
  if (own !== undefined && own !== null && own !== '') return +own;
  if (item.base_price == null || item.base_price === '') return null;
  if (+item.base_price === 0) return 0;
  const baseRate = +(P?.base_usd_rate || ((P?.base_currency || 'USD') === 'USD' ? 1 : 3.75)); const rate = +(country.usd_rate || 1); const cur = billCur(country);
  if ((P?.base_currency || 'USD') === cur) return +item.base_price;
  return roundPrice(+item.base_price / baseRate * rate, cur);
}
// Breakdown of a price for checkout and display. mode incl: price already contains tax; excl: tax added on top.
export function taxBreakdown(price, country, P) {
  if (price == null) return null;
  const rate = +(country.tax_rate || 0); const mode = taxMode(country, P); const r2 = x => Math.round(x * 100) / 100;
  if (mode === 'incl') { const net = r2(price / (1 + rate / 100)); return { mode, rate, net, tax: r2(price - net), total: r2(price) }; }
  return { mode, rate, net: r2(price), tax: r2(price * rate / 100), total: r2(price * (1 + rate / 100)) };
}
export function taxNote(country, P) {
  const rate = +(country.tax_rate || 0); if (!rate) return country?.intl ? t('tax_local') : t('tax_none');
  const l = ({ ar: { VAT: 'ضريبة القيمة المضافة', GST: 'ضريبة السلع والخدمات', TVA: 'ضريبة القيمة المضافة' }, fr: { VAT: 'TVA' } }[LANG.cur] || {})[String(country.tax_label || '').toUpperCase()] || country.tax_label || ''; // v2.9: the tax named in the reader's language
  return taxMode(country, P) === 'incl' ? t('tax_incl_rate', { r: fmtNum(rate, 2), l }) : t('tax_excl_rate', { r: fmtNum(rate, 2), l });
}
// v3.33 (the owner, 2026-10-22 — note 6: «وضع خانة لتحديد النسبة المئوية للخصم وينعكس عند وضع الخصم على مظاهر عرض الباقات ويكتب مثلاً بجانب السعر "الخصم 26%"»;
// note 50: «الخصم الذي يضعه المسوق يجب أن يكون بناءً على السعر الحالي بعد الخصم»): a plan carries its own discount (discount_pct, until discount_until when set).
// What a person pays for the plan is its price AFTER that discount; a partner's offer and a coupon are taken from that price, never from the list price.
// money as both twins round it (PHP round(x, 2): a half goes up — 1.005 → 1.01)
export const r2c = x => Math.round((+x + (+x >= 0 ? 1e-9 : -1e-9)) * 100) / 100;
export function planDiscPct(plan, at = Date.now()) {
  const d = +plan?.discount_pct; if (!(d > 0 && d < 100)) return 0;
  const u = String(plan?.discount_until || ''); if (u) { const e = Date.parse(/^\d{4}-\d{2}-\d{2}$/.test(u) ? u + 'T23:59:59Z' : u); if (e && e < at) return 0; }
  return Math.round(d * 100) / 100;
}
// v3.33 (the owner, 2026-10-22 — notes 8 and 26: «إمكانية تخصيص مدة التجربة المجانية حسب الباقة (شهري أو سنوي)»): a plan's free days for the cycle chosen —
// its own number for that cycle when set, else the plan's general trial_days
export const yearlyOn = P => P?.billing?.yearly === true; // v3.33.23 (the owner, 2026-10-24): a yearly subscription only when the developer offers it — dar-billing.php bill_yearly_on
export const trialDaysFor = (p, cycle) => { const v = cycle === 'year' ? p?.trial_days_year : p?.trial_days_month; return Math.max(0, Math.floor(+(v !== undefined && v !== null && v !== '' ? v : p?.trial_days) || 0)); };
export function planCost(plan, country, P, cycle, own = null) {
  const monthly = own ?? listPrice(plan, country, P); if (monthly == null) return null;
  const months = cycle === 'year' ? 12 - (own != null ? 0 : Math.max(0, Math.min(11, +plan?.months_free || 0))) : 1; const list = r2c(monthly * months);
  const pct = own != null ? 0 : planDiscPct(plan); const now = pct ? r2c(list * (1 - pct / 100)) : list;
  return { monthly, months, list, now, pct, off: r2c(list - now) };
}
export function guessCountry(countries, P, geo) {
  const ok = c => !!c && countryOpen(c, countries, P || WORLD_P || undefined);
  const g = String(geo || '').toUpperCase(); if (ok(g)) return g; // the server's view of the visitor (e.g. CF-IPCountry), when it sends one
  let tz = ''; try { tz = Intl.DateTimeFormat().resolvedOptions().timeZone || ''; } catch { /* ignore */ }
  const map = { Riyadh: 'SA', Dubai: 'AE', Kuwait: 'KW', Qatar: 'QA', Bahrain: 'BH', Muscat: 'OM', Cairo: 'EG', Amman: 'JO', Baghdad: 'IQ', Beirut: 'LB', Casablanca: 'MA', Algiers: 'DZ', Tunis: 'TN', Paris: 'FR', Brussels: 'BE', Toronto: 'CA', Montreal: 'CA', Vancouver: 'CA' };
  const hit = Object.keys(map).find(k => tz.includes(k));
  if (hit && ok(map[hit])) return map[hit];
  const byTz = tz ? Object.values(R.WORLD).find(w => w.tz === tz)?.code : null; if (ok(byTz)) return byTz;
  let langs = []; try { langs = [...(navigator.languages || []), navigator.language]; } catch { /* no navigator (server) */ }
  for (const l of langs) { const m = /[-_]([A-Za-z]{2})$/.exec(l || ''); if (m && ok(m[1].toUpperCase())) return m[1].toUpperCase(); }
  return null;
}

// ---------------------------------------------------------------- platform settings (developer-owned document)
export function platformDefaults() {
  return {
    services: {}, custom: [], custom_ent: {}, cats: {}, catOrder: {}, texts: {},
    theme: { ...R.DEFAULT_THEME }, landing: clone(R.DEFAULT_LANDING), partner: { ...R.DEFAULT_PARTNER }, billing: clone(BILLING_DEFAULTS),
    ai: { roles: {} }, links: {}, domain: '', landings: {}, tenant_roles: {}, onboarding: {}, price_display: 'incl', base_currency: 'USD', base_usd_rate: 1, default_country: 'SA', world: { ...WORLD_DEF }, fx: {},
    dev_roles: clone(R.DEV_ROLES), wa: { numbers: [], confirm: true }, master_key_hash: '', master_key_preview: '', seeded: 0,
    // everything below is edited from the developer panel (no automation-side configuration)
    ent_extra: {}, ent_opts: {}, ent_hide: {}, recipes: { off: [], custom: [] }, hr_policy: {}, hr_policy_cc: {},
    security: { ...R.SECURITY_DEFAULTS }, schedules: { ...R.SCHEDULE_DEFAULTS }, migration: { ...R.MIGRATION_DEFAULTS }, radar: { ...R.RADAR_DEFAULTS },
    // live-operation switches: example accounts read-only on a real server, maintenance notice, bot protection on public forms
    demo_mode: 'readonly', maintenance: { on: false, message: [] }, captcha: { provider: '', site_key: '', on: [] }, maps: { on: true, tiles: 'osm', tile_url: '', attribution: '', geocoder: '', nearby: true, precision: 'approximate' },
    // growth: measurement tags (public pages only, after consent), rich-preview share links, own hosts and the target subscribers point their domains to
    tracking: { gtm: '', ga4: '', meta: '', consent: 'ask' }, share_base: '', hosts: [], cname_target: '', legal_edits: [],
    max_photos: 12, upload_max_mb: 1, // photos per record and size per file on a live server (raise it with the server's request size); the in-browser model stays at ~1 MB
  };
}
// only well-formed tag ids ever reach a page (nothing else can be injected through them)
// v3.18.3: the measurement tags a public page may load (each id in its own form, or left out): Clarity, Cloudflare Web Analytics, the
// TikTok, Snap, LinkedIn and X tags join Google's and Meta's (set on «الربط والمفاتيح»)
const TRACK_RE = { gtm: /^GTM-[A-Z0-9]{4,12}$/, ga4: /^G-[A-Z0-9]{4,14}$/, meta: /^\d{6,20}$/, clarity: /^[a-z0-9]{6,16}$/, cfa: /^[a-f0-9]{32}$/, tiktok: /^[A-Z0-9]{10,30}$/, snap: /^[a-f0-9-]{36}$/, linkedin: /^\d{4,12}$/, x: /^[a-z0-9]{4,12}$/ };
const trackingOf = P => { const x = P.tracking || {}; const o = {}; for (const [k, re] of Object.entries(TRACK_RE)) o[k] = typeof x[k] === 'string' && re.test(x[k]) ? x[k] : ''; return Object.values(o).some(Boolean) ? { ...o, consent: x.consent === 'none' ? 'none' : 'ask' } : null; };
// ---- white label: the office's name, colour, logo and own domain (plan or purchased add-on)
// a feature add-on (unit 1) opens its service; a quantity pack (unit > 1) only raises a limit through tenant.extra
export const isFeatureAddon = a => !!a && (+a.unit_label || 1) === 1;
export const unlockedOf = (T, addons) => (T?.addons || []).map(code => (addons || []).find(a => a.code === code && a.active !== false && isFeatureAddon(a))?.service).filter(Boolean);
export const cleanHost = h => { const x = String(h || '').trim().toLowerCase().replace(/^https?:\/\//, '').replace(/[/?#].*$/, '').replace(/\.$/, ''); return /^(?=.{4,253}$)([a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z]{2,24}$/.test(x) ? x : ''; };
function brandOf(T) {
  if (!T || !PUB_APPS.includes(T.app)) return null; const svc = catalog(getP()).find(s => s.app === T.app && (s.id === 'white_label' || s.share === 'white_label'));
  if (!svc || access(svc, { country: T.country, intl: !listedCountry(T.country), plan: T.plan, audience: audienceOf(T.app), plans: rowsOf('platform', 'plans'), unlocked: unlockedOf(T, rowsOf('platform', 'addons')) }) !== 'ok') return null;
  const w = store.get(`set:${T.id}:white_label`, {}); const prof = store.get(`set:${T.id}:profile`, {}); if (!w.brand_name && !w.brand_color && !T.domain) return null;
  return { name: String(w.brand_name || T.name || '').slice(0, 60), color: /^#[0-9a-f]{6}$/i.test(w.brand_color || '') ? w.brand_color : '', logo: IMG_OK.test(prof.logo || '') ? prof.logo : '', domain: T.domain || '', domain_status: T.domain ? (T.domain_status || 'pending') : '' };
}
const officeCard = T => { const prof = store.get(`set:${T.id}:profile`, {}); const b = brandOf(T); return { name: b?.name || T.name, city: T.city, country: T.country, phone: prof.public_phone || store.get(`set:${T.id}:connections`, {})?.whatsapp?.account || '', license: prof.license_no || '', cr: prof.cr || '', logo: IMG_OK.test(prof.logo || '') ? prof.logo : '', bio: String(prof.bio || '').slice(0, 600), color: b?.color || '', white: !!b }; };
const withBrand = T => { if (!T) return T; const b = brandOf(T); return b ? { ...T, brand: b } : T; };
const pwMin = () => Math.max(6, +getP().security?.password_min || 8);
// v3.2 — where a developer text lives, by its translation path (the paths i18n.translate and the developer screens use)
function i18nSlot(P, path) {
  const m = /^(texts|cats|custom|landings|onboarding|recipes):(.+)$/.exec(String(path || '')); if (!m) return null; const [, kind, rest] = m; const parts = rest.split('.');
  if (kind === 'texts' || kind === 'cats') { P[kind] ||= {}; return { obj: P[kind], key: rest }; }
  if (kind === 'custom') { const svc = (Array.isArray(P.custom) ? P.custom : []).find(x => x && x.id === parts[0]); const f = parts[1] || 'n'; return svc && (f === 'n' || f === 'd') ? { obj: svc, key: f } : null; }
  if (kind === 'recipes') { const r = (P.recipes?.custom || []).find(x => x.k === parts[0]); return r && ['n', 'd', 'v'].includes(parts[1]) ? { obj: r, key: parts[1] } : null; }
  if (kind === 'onboarding') { const cfg = P.onboarding?.[parts[0]]; if (!cfg) return null; if (parts[1] === 'title') return { obj: cfg, key: 'title' }; const q = (cfg.questions || []).find(x => x.id === parts[1]); if (!q) return null; if (parts[2] === 'q' || parts[2] === 'hint') return { obj: q, key: parts[2] }; const o = (q.options || []).find(x => x.id === parts[2]); return o ? { obj: o, key: 'n' } : null; }
  let o = P.landings?.[parts[0]]; const ks = parts.slice(1).map(k => /^\d+$/.test(k) ? +k : k); if (!o || !ks.length) return null; // landings
  for (const k of ks.slice(0, -1)) { o = o[k]; if (!o || typeof o !== 'object') return null; }
  return { obj: o, key: ks[ks.length - 1] };
}
// the empty languages of one text take the given ones ([ar,en,fr] or {ar,en,fr}); a written language is never replaced
function fillI18n(P, path, value) {
  if (/^custom:[^.]+$/.test(path) && value && typeof value === 'object' && !Array.isArray(value) && (value.n || value.d)) { let n = 0; for (const f of ['n', 'd']) if (value[f]) n += fillI18n(P, path + '.' + f, value[f]); return n; }
  const slot = i18nSlot(P, path); if (!slot) return 0; const cur = slot.obj[slot.key]; const LNS = ['ar', 'en', 'fr'];
  const a = Array.isArray(cur) ? [...cur] : LNS.map(l => cur?.[l] || ''); const b = Array.isArray(value) ? value : LNS.map(l => value?.[l] || '');
  let n = 0; for (let i = 0; i < 3; i++) if (!String(a[i] ?? '').trim() && String(b[i] ?? '').trim()) { a[i] = String(b[i]).trim().slice(0, 4000); n++; }
  if (n) slot.obj[slot.key] = cur && !Array.isArray(cur) && typeof cur === 'object' ? { ...cur, ar: a[0], en: a[1], fr: a[2] } : a;
  return n;
}
const PATH_PERM = { legal_edits: 'texts', features: 'services', channel_policy: 'services', sales: 'subscriptions', quotas: 'pricing', trials: 'pricing', treasury: 'payments', analytics: 'monitoring', learning: 'ai', sites: 'services', maps: 'appearance', doctor: 'monitoring', grow: 'texts', i18n: 'texts', trial_all: 'pricing', geo: 'countries', max_photos: 'services', upload_max_mb: 'services', tracking: 'appearance', share_base: 'appearance', hosts: 'services', cname_target: 'services', demo_mode: 'services', maintenance: 'services', captcha: 'accounts', ent_extra: 'services', ent_opts: 'services', ent_hide: 'services', recipes: 'services', migration: 'services', radar: 'services', security: 'accounts', schedules: 'automation', hr_policy: 'countries', hr_policy_cc: 'countries', onboarding: 'services', landings: 'appearance', tenant_roles: 'accounts', services: 'services', custom: 'services', custom_ent: 'services', cats: 'services', catOrder: 'services', texts: 'texts', theme: 'appearance', landing: 'appearance', links: 'appearance', domain: 'appearance', partner: 'pricing', billing: 'payments', ai: 'ai', price_display: 'countries', tax_note: 'countries', base_currency: 'countries', base_usd_rate: 'countries', default_country: 'countries', world: 'countries', fx: 'countries', autonomy: 'automation', dev_roles: 'accounts', dev_roles_view: 'accounts', wa: 'automation', master_key_hash: 'automation', master_key_preview: 'automation' };
const COLL_PERM = { promos: 'texts', mig_sources: 'services', radar_sources: 'services', tpl_library: 'texts', countries: 'countries', plans: 'pricing', addons: 'pricing', coupons: 'pricing', trial_plans: 'pricing', offers: 'pricing', cashback_rules: 'pricing', gateways: 'payments', legal: 'texts', faq: 'texts', books: 'texts', notif_templates: 'texts', assets: 'texts', ref_ads: 'appearance', platform_tools: 'automation', oauth_apps: 'automation', platform_webhooks: 'automation', incidents: 'monitoring', psuggestions: 'tenants', dev_campaigns: 'tenants', market_requests: 'tenants' };

// ================================================================= LOCAL BACKEND (model mode)
const users = () => store.get('users', []) || [];
const tenants = () => store.get('tenants', []) || [];
const saveUsers = x => store.set('users', x);
const saveTenants = x => store.set('tenants', x);
// v3.11.1: a field that must be a list or a group but holds something else is read as its default — no page ever stops on a
// wrong value (the server puts the last good value back, dar-keys.php)
const shapeOf = v => Array.isArray(v) ? (v.length ? 'list' : 'empty') : v && typeof v === 'object' ? (Object.keys(v).length ? 'map' : 'empty') : v == null ? 'null' : 'scalar';
const wantOf = d => Array.isArray(d) ? 'list' : d && typeof d === 'object' ? 'map' : 'scalar';
export const shapeFits = (v, d) => { const s = shapeOf(v), w = wantOf(d); return s === 'null' || s === w || (s === 'empty' && w !== 'scalar'); };
// the groups inside the record whose shape the pages rely on (the server's P_SHAPES, dar-keys.php)
const NESTED_SHAPES = [['ai.roles', {}], ['wa.numbers', []], ['recipes.off', []], ['recipes.custom', []], ['captcha.on', []], ['billing.bank', {}], ['billing.remind_days', []]];
const SHAPE_SAID = new Set();
const getP = () => {
  const d = platformDefaults(); const p = store.get('platform'); if (!p || typeof p !== 'object' || Array.isArray(p)) return d;
  const out = { ...d };
  for (const [k, v] of Object.entries(p)) {
    if (k in d && !shapeFits(v, d[k])) { if (!SHAPE_SAID.has(k)) { SHAPE_SAID.add(k); try { import('./watch.js?v=3.34.0-d66b90ae').then(w => w.capture('warn', 'platform setting «' + k + '» has a wrong shape: read as its default', 'platform:' + k)).catch(() => {}); } catch { /* no window */ } } continue; }
    out[k] = v;
  }
  return out;
};
const saveP = p => { if (!store.set('platform', p)) fail('storage_full'); };
const ckey = (tenant, coll) => `db:${tenant}:${coll}`;
// v3.2: a developer's "properties" are its units (assets/units-view.js) — every office engine works for developers
const PUB_APPS = ['app', 'builders']; // accounts whose listings have public pages (office page, listing, booking, QR)
let BT = { raw: undefined, ids: new Set() };
function builderTenant(tid) {
  if (!tid || tid === 'platform') return false; const raw = rawGet('tenants');
  if (raw !== BT.raw) { let list = []; try { list = JSON.parse(raw || '[]') || []; } catch { list = []; } BT = { raw, ids: new Set(list.filter(x => x && x.app === 'builders').map(x => x.id)) }; }
  return BT.ids.has(tid);
}
const unitView = tid => UV.unitListings(store.get(ckey(tid, 'units'), []), store.get(ckey(tid, 'projects'), []), store.get(ckey(tid, 'b_leases'), []), store.get(ckey(tid, 'b_permits'), []));
const rowsOf = (tenant, coll) => coll === 'properties' && builderTenant(tenant) ? unitView(tenant) : store.get(ckey(tenant, coll), []);
function saveRows(tenant, coll, list) {
  if (coll === 'properties' && builderTenant(tenant)) { const r = UV.writeBack(store.get(ckey(tenant, 'units'), []), unitView(tenant), list); if (r.changed && !store.set(ckey(tenant, 'units'), r.units)) fail('storage_full'); return; }
  if (!store.set(ckey(tenant, coll), list)) fail('storage_full');
}
// v3.29 — the starter examples of a sold copy (the ops 'starter.*'): which lists, how many, and how an example is told from his own
// row — «_ex» holds the row's own «updated» time when it was put there, so a row he has changed since is no longer an example
const STARTER = { app: { owners: 2, properties: 5, leads: 6, deals: 3, appointments: 3, tasks: 3 }, builders: { projects: 1, units: 8, reservations: 2, stages: 5, leads: 4 } };
const starterKey = tid => `set:${tid}:starter`;
const isStarterRow = r => !!r && typeof r === 'object' && !!r._ex && String(r._ex) === String(r.updated);
function starterState(c) {
  const T = c.tenant, cfg = SOLO && T ? STARTER[c.app] : null; if (!cfg) return { can: false, count: 0, done: false, empty: false };
  const st = store.get(starterKey(T.id), null); let count = 0, any = 0;
  for (const coll of Object.keys(cfg)) { const l = rowsOf(T.id, coll); any += l.length; count += l.filter(isStarterRow).length; }
  return { can: ['owner', 'admin', 'manager'].includes(c.user?.role), count, done: !!st, state: st?.state || '', empty: any === 0 };
}
function starterRows(app, data, me, mark, uidOf) {
  const take = (coll, n) => (Array.isArray(data[coll]) ? data[coll] : []).slice(0, n).map(r => ({ ...r }));
  const put = (r, f) => { if (f && typeof r[f] === 'string' && r[f].trim()) r[f] = r[f].trim() + ' · ' + mark; return r; };
  const out = {};
  const fin = (coll, list) => { out[coll] = list.map(r => ({ ...r, by: uidOf || null, _ex: r.updated })); };
  const cfg = STARTER[app];
  if (app === 'app') {
    const owners = take('owners', cfg.owners).map(r => { delete r.portal_token; return put(r, 'name'); });
    const props = take('properties', cfg.properties).map(r => { r.ad_license = ''; r.ad_license_expiry = ''; r.images = []; return put(r, 'title'); });
    const leads = take('leads', cfg.leads).map(r => { r.assigned_to = me; return put(r, 'name'); });
    const deals = take('deals', cfg.deals).map((r, i) => { const pr = props[i % props.length], ld = leads[i % leads.length]; return put({ ...r, lead: ld.id, property: pr.id, owner: me, value: pr.price, commission: Math.round((+pr.price || 0) * 0.025), title: String(r.title || '').replace(/:.*$/, '') + ': ' + String(pr.title).replace(/ · .*$/, '') }, 'title'); });
    const appts = take('appointments', cfg.appointments).map((r, i) => { const pr = props[i % props.length], ld = leads[i % leads.length]; return put({ ...r, lead: ld.id, property: pr.id, reminder: '', title: String(r.title || '').replace(/:.*$/, '') + ': ' + String(pr.title).replace(/ · .*$/, '') }, 'title'); });
    const tasks = take('tasks', cfg.tasks).map(r => { r.assigned_to = me; return put(r, 'title'); });
    fin('owners', owners); fin('properties', props); fin('leads', leads); fin('deals', deals); fin('appointments', appts); fin('tasks', tasks);
  } else {
    const pr = take('projects', cfg.projects).map(r => { r.license_no = ''; return put(r, 'name'); }); const pid = pr[0]?.id;
    const units = (data.units || []).filter(u => u.project === pid).slice(0, cfg.units).map(r => ({ ...r }));
    const uids = new Set(units.map(u => u.id));
    const res = (data.reservations || []).filter(x => uids.has(x.unit)).slice(0, cfg.reservations).map(r => { const x = { ...r }; delete x.portal_token; return x; });
    const st = (data.stages || []).filter(x => x.project === pid).slice(0, cfg.stages).map(r => ({ ...r }));
    const leads = take('leads', cfg.leads).map(r => { r.assigned_to = me; return put(r, 'name'); });
    fin('projects', pr); fin('units', units); fin('reservations', res); fin('stages', st); fin('leads', leads);
  }
  return out;
}
// a service of the office catalog as the developer app names it (b_leads for leads…), for links and notices
const svcIn = (app, base) => { if (!base || app === 'app') return base; const s = catalog(getP()).find(x => x.app === app && (x.id === base || x.share === base)); return s ? s.id : base; };
const isPlatformColl = c => R.PLATFORM.includes(c);
// v3.33.3: a line of the log stays small — a value of more than 16 KB is not kept in it (its undo is said to be unavailable), and the
// log keeps its 600 latest lines (the server does the same: dar-sync.php audit_slim)
const AUDIT_BIG = 16000;
export function auditSlim(e) {
  if (!e || typeof e !== 'object') return e; let cut = false;
  const keep = arr => Array.isArray(arr) ? arr.filter(x => { const big = JSON.stringify(x?.value ?? null).length > AUDIT_BIG; if (big) cut = true; return !big; }) : arr;
  const out = { ...e }; if (Array.isArray(e.undo)) out.undo = keep(e.undo); if (Array.isArray(e.redo)) out.redo = keep(e.redo);
  if (cut) { out.undo_trimmed = true; if (Array.isArray(out.undo) && !out.undo.length) delete out.undo; }
  return out;
}
function audit(c, entry) {
  const list = store.get('audit', []); const id = uid('a');
  list.unshift(auditSlim({ id, at: nowIso(), app: c.app, uid: c.user?.id || null, who: c.user?.name || '', tenant: c.tenant?.id || null, imp: c.imp || null, ...entry }));
  if (list.length > 600) list.length = 600;
  store.set('audit', list); return id;
}

function seedPlatform() {
  const P = getP();
  if (P.seeded >= 6) return;
  if (P.seeded >= 3) { upgradeSeed(P); return; }
  const put = (coll, rows) => { if (!rowsOf('platform', coll).length) saveRows('platform', coll, rows.map(r => ({ id: uid('r'), created: nowIso(), ...r }))); };
  put('countries', R.COUNTRIES); put('plans', R.PLANS); put('addons', R.ADDONS); if (!SOLO && !SHOW) put('gateways', R.GATEWAYS); // (v3.26.1: a sold copy and the showcase charge nothing — no payment gateway listed)
  const faq = [
    [['هل بياناتي ملكي؟', 'Is my data mine?', 'Mes données m’appartiennent-elles ?'], ['نعم. تستطيع تصدير كل بياناتك في أي وقت من صفحة الخصوصية، ولا تُباع لأي جهة.', 'Yes. You can export all your data at any time from the privacy page; it is never sold.', 'Oui. Vous pouvez tout exporter à tout moment ; elles ne sont jamais vendues.']],
    [['هل أحتاج خبرة تقنية؟', 'Do I need technical skills?', 'Faut-il des compétences techniques ?'], ['لا. تكتب ما تريد في رسالة واحدة ويتولى الفريق الذكي التنفيذ.', 'No. Write what you need in one message and the AI team handles it.', 'Non. Écrivez votre besoin en un message, l’équipe IA s’en charge.']],
    [['هل أستطيع الإلغاء؟', 'Can I cancel?', 'Puis-je résilier ?'], ['نعم، من صفحة الاشتراك وبدون تجديد مخفي.', 'Yes, from the subscription page, with no hidden renewals.', 'Oui, depuis la page abonnement, sans renouvellement caché.']],
    [['في أي الدول تعمل دار؟', 'Which countries does Dar serve?', 'Dans quels pays Dar est-il disponible ?'], ['تظهر الخدمات والأسعار حسب الدولة التي تختارها أعلى الصفحة.', 'Services and prices follow the country you choose at the top of the page.', 'Services et prix suivent le pays choisi en haut de page.']],
  ];
  put('faq', (SOLO || SHOW ? soldFaq() : faq).flatMap(([q, a], i) => ['ar', 'en', 'fr'].map((lang, j) => ({ question: q[j], answer: a[j], lang, sort: i + 1 }))));
  put('books', [
    { title: 'The Millionaire Real Estate Agent', author_book: 'Gary Keller', topic: 'Real estate', lang: 'en' },
    { title: 'Ninja Selling', author_book: 'Larry Kendall', topic: 'Sales', lang: 'en' },
    { title: 'Influence', author_book: 'Robert B. Cialdini', topic: 'Persuasion', lang: 'en' },
    { title: 'Never Split the Difference', author_book: 'Chris Voss', topic: 'Negotiation', lang: 'en' },
    { title: 'Building a StoryBrand', author_book: 'Donald Miller', topic: 'Marketing', lang: 'en' },
  ]);
  put('mig_sources', SOLO || SHOW ? R.MIG_SOURCES.map(soldRow) : R.MIG_SOURCES); put('radar_sources', SOLO || SHOW ? R.RADAR_SOURCES.filter(x => x.kind !== 'network') : R.RADAR_SOURCES); put('tpl_library', tplLibrary());
  P.seeded = 6; saveP(P);
}
// v3.26: a copy sold to one business starts with questions its own visitors ask (an office's or a developer company's), and its
// import guides speak of «the system» — never of «دار»; it has no network of offices to pool anonymous prices with
function soldFaq() {
  const privacy = [['هل بياناتي محفوظة؟', 'Is my information safe?', 'Mes informations sont-elles protégées ?'], ['نستخدم بياناتك للتواصل معك بشأن طلبك فقط، ولا نبيعها لأي جهة. التفاصيل في سياسة الخصوصية.', 'We use your details only to answer your request, and never sell them. The privacy policy has the details.', 'Nous utilisons vos coordonnées uniquement pour répondre à votre demande et ne les vendons jamais. La politique de confidentialité donne les détails.']];
  if (SOLO === 'builder') return [
    [['كيف أحجز وحدة؟', 'How do I reserve a unit?', 'Comment réserver un logement ?'], ['اختر الوحدة وأرسل طلبك من صفحتها، وسيتواصل معك فريق المبيعات لإتمام الحجز.', 'Choose the unit and send your request from its page; our sales team will contact you to complete the reservation.', 'Choisissez le logement et envoyez votre demande depuis sa page ; notre équipe commerciale vous contactera pour finaliser la réservation.']],
    [['هل أستطيع زيارة المشروع؟', 'Can I visit the project?', 'Puis-je visiter le projet ?'], ['نعم. أرسل طلبك من صفحة الوحدة أو من صفحة التواصل، وسنتفق معك على موعد الزيارة.', 'Yes. Send your request from the unit’s page or the contact page, and we will agree on a time with you.', 'Oui. Envoyez votre demande depuis la page du logement ou la page contact, et nous conviendrons d’un rendez-vous.']],
    privacy,
  ];
  return [
    [['كيف أطلب معاينة عقار؟', 'How do I arrange a viewing?', 'Comment organiser une visite ?'], ['أرسل طلبك من صفحة العقار أو من صفحة التواصل، وسيتصل بك فريقنا لتحديد الموعد.', 'Send your request from the property’s page or the contact page; our team will call you to set a time.', 'Envoyez votre demande depuis la page du bien ou la page contact ; notre équipe vous appellera pour fixer un rendez-vous.']],
    [['هل أستطيع عرض عقاري لديكم؟', 'Can I list my property with you?', 'Puis-je vous confier mon bien ?'], ['نعم. أرسل لنا تفاصيل عقارك من صفحة التواصل، وسيتواصل معك فريقنا لمعاينته والاتفاق على عرضه.', 'Yes. Send us your property’s details from the contact page; our team will contact you to see it and agree on listing it.', 'Oui. Envoyez-nous les détails de votre bien depuis la page contact ; notre équipe vous contactera pour le visiter et convenir de sa mise en vente.']],
    privacy,
  ];
}
const SOLD_SEED = [['لا تقابل حقلًا في دار', 'لا تقابل حقلًا في النظام'], ['Columns with no matching Dar field', 'Columns with no matching field'], ['فيسحبها خادم دار', 'فيسحبها الخادم'], ['Dar’s server pulls it', 'the server pulls it'],
  ['le serveur de Dar la récupère', 'le serveur la récupère'], ['يُفعّله مطور دار لكل بوابة', 'تفعّله الإدارة لكل بوابة'], ['Dar’s developer turns it on', 'The administration turns it on'], ['par le développeur de Dar', 'par l’administration']];
export function soldText(s) {
  if (typeof s !== 'string' || (s.indexOf('دار') < 0 && s.indexOf('Dar') < 0)) return s;
  for (const [a, b] of SOLD_SEED) s = s.split(a).join(b);
  return s.replace(/(^|[^\p{Script=Arabic}])([وف]?[لبك]?)دار(?!\p{Script=Arabic})/gu, (m, pre, px) => pre + (px.endsWith('ل') ? px.slice(0, -1) + 'للنظام' : px + 'النظام'))
    .replace(/(?<![\w-])Dar’s(?![\w-])/g, 'the system’s').replace(/\bde Dar(?![\w-])/g, 'du système').replace(/(?<![\w-])Dar(?![\w-])/g, 'the system');
}
const soldRow = row => Object.fromEntries(Object.entries(row).map(([k, v]) => [k, soldText(v)]));
// v3.2: the official market sources go live on a platform seeded before them (a row the developer edited stays as he set it)
function upgradeSeed(P) {
  const rs = rowsOf('platform', 'radar_sources'); let changed = false;
  for (const def of R.RADAR_SOURCES.filter(x => x.kind === 'official')) {
    const row = rs.find(x => x.key === def.key);
    if (!row) { rs.push({ id: uid('r'), created: nowIso(), ...def }); changed = true; } else if (row.status === 'soon' && !row.updated) { Object.assign(row, def); changed = true; }
  }
  if (changed) saveRows('platform', 'radar_sources', rs);
  // v3.2: the documents method reads text PDFs on the device now — its guide says so (unless the developer rewrote it)
  const ms = rowsOf('platform', 'mig_sources'); const doc = ms.find(x => x.key === 'documents'); const def = R.MIG_SOURCES.find(x => x.key === 'documents');
  if (doc && def && !doc.updated && doc.guide_ar !== def.guide_ar) { Object.assign(doc, { guide_ar: def.guide_ar, guide_en: def.guide_en, guide_fr: def.guide_fr }); saveRows('platform', 'mig_sources', ms); }
  // v3.5: the systems connected by an API key say how it works now (the server pulls the list) — unless the developer rewrote them
  let apiNew = false; for (const row of ms) { const d = R.MIG_SOURCES.find(x => x.key === row.key); if (d && (d.methods || []).includes('api') && !row.updated && row.guide_ar !== d.guide_ar) { Object.assign(row, { guide_ar: d.guide_ar, guide_en: d.guide_en, guide_fr: d.guide_fr }); apiNew = true; } }
  if (apiNew) saveRows('platform', 'mig_sources', ms);
  P.seeded = 6; saveP(P);
}

function ctxOf(app, token) {
  const c = { app, user: null, tenant: null, imp: null };
  if (token) {
    const tk = store.get('tokens', {})[token];
    if (tk && tk.exp > Date.now() && tk.app === app) {
      c.user = users().find(u => u.id === tk.uid) || null;
      if (c.user && R.staffExpired(c.user)) c.user = null; // v3.31: his access ended — signed out
      if (c.user) c.tenant = tenants().find(x => x.id === c.user.tenant) || null;
      c.imp = tk.imp || null;
    }
  }
  return c;
}
const needUser = c => { if (!c.user) fail('auth_required'); if (c.user.status === 'inactive') fail('forbidden'); };
const needDev = c => { needUser(c); if (c.user.app !== 'developer') fail('forbidden'); };
// v3.31: a member's access — what he changes (devPerms) and what he sees (devView): his own choice (user.access) or his role's rows,
// the owner's matrix over the defaults (registry devAccessOf, the server's dev_access). Before, the panel read the owner's saved
// matrix alone: a member whose role's row the owner never saved — an «admin» on a new platform — got nothing at all
function devPerms(c) { return R.devAccessOf(c.user, getP()).edit; }
function devView(c) { return R.devAccessOf(c.user, getP()).view; }
const needPerm = (c, perm) => { needDev(c); if (!devPerms(c).includes(perm)) fail('forbidden', { perm }); };
const needView = (c, perm) => { needDev(c); if (!devView(c).includes(perm)) fail('forbidden', { perm }); };
// v3.31: what a member is given — the parts he changes and sees (none given: his role's rows) and the end of his access — checked as
// the server checks it: someone who is not the owner gives no more than he holds himself, and «accounts» (managing the staff) only
// the owner gives. An invitation's end must still be ahead.
function staffGrant(c, role, p, forInvite) {
  const P = getP(); let access = null;
  if (p.access && typeof p.access === 'object') {
    const e = Array.isArray(p.access.edit) ? p.access.edit.filter(x => R.DEV_PERMS.includes(x)) : null, v = Array.isArray(p.access.view) ? p.access.view.filter(x => R.DEV_PERMS.includes(x)) : null;
    if (!e || !v) fail('validation', { access: 'format' }); access = { edit: [...new Set(e)], view: [...new Set([...e, ...v])] };
  }
  const want = access || R.devRoleAccess(role, P);
  if (c.user.role !== 'owner' && role !== 'owner') { const mine = R.devAccessOf(c.user, P); if (want.edit.some(x => !mine.edit.includes(x)) || want.view.some(x => !mine.view.includes(x)) || want.edit.includes('accounts')) fail('forbidden', { access: 'beyond' }); }
  let until = 0; const u = p.until;
  if (u !== undefined && u !== null && u !== '' && u !== 0) { until = typeof u === 'number' ? u : Date.parse(u); if (!(until > 0)) fail('validation', { until: 'format' }); if (forInvite && until <= Date.now()) fail('validation', { until: 'past' }); }
  return { ...(access ? { access } : {}), ...(until ? { until } : {}) };
}
function needWritable(c) { if (c.tenant?.status === 'suspended') fail('tenant_suspended'); if (demoLocked(c.tenant)) fail('demo_readonly'); }
const demoLocked = T => !!(T?.demo && RUNTIME.server && (getP().demo_mode || 'readonly') !== 'sandbox');
export const tzOf = code => countryBy(code, rowsOf('platform', 'countries'), getP()).tz || R.COUNTRY_TZ[code] || R.WORLD[code]?.tz || 'Asia/Riyadh';
const listedCountry = code => rowsOf('platform', 'countries').some(x => x.code === code);
// a country a new account (or a profile change) may use: his enabled rows, or any open world country — never a silent fallback
const ptxt = (v, n) => Array.isArray(v) ? v.slice(0, 3).map(x => String(x ?? '').slice(0, n)) : v && typeof v === 'object' ? ['ar', 'en', 'fr'].map(l => String(v[l] ?? '').slice(0, n)) : String(v ?? '').slice(0, n);
function cleanProposal(p) { // v2.5.1: plus the machine plan the worker executes after approval (≤ 20 KB of JSON, never shown as text)
  const r = cleanProposal0(p); if (r && p.plan && typeof p.plan === 'object') { try { const s = JSON.stringify(p.plan); if (s.length <= 20000) r.plan = JSON.parse(s); } catch { /* not JSON: dropped */ } } return r;
}
function cleanProposal0(p) {
  if (!p || typeof p !== 'object') return null; const summary = ptxt(p.summary, 600); if (Array.isArray(summary) ? !summary.some(Boolean) : !summary) return null;
  const exp = p.expires_at && !isNaN(new Date(p.expires_at)) ? new Date(p.expires_at).toISOString() : null;
  return { summary, steps: (Array.isArray(p.steps) ? p.steps : []).slice(0, 20).map(x => ptxt(x, 300)), evidence: (Array.isArray(p.evidence) ? p.evidence : []).slice(0, 20).map(e => ({ label: ptxt(e && typeof e === 'object' && !Array.isArray(e) ? e.label : e, 200), value: String(e?.value ?? '').slice(0, 200), source: String(e?.source ?? '').slice(0, 200) })), impact: ptxt(p.impact, 300), risk: ['low', 'medium', 'high'].includes(p.risk) ? p.risk : 'medium', expires_at: exp };
}
const ARANK = { auto: 0, ask: 1, block: 2 };
export function autonomyOf(P) {
  const d = R.AUTONOMY_DEFAULTS; const a = (P && P.autonomy) || {}; const policy = {};
  for (const k of R.AUTONOMY_CATS) policy[k] = a.policy && a.policy[k] in ARANK ? a.policy[k] : d.policy[k];
  const num = (v, lo, hi, def) => { v = +v; return v !== '' && Number.isFinite(v) && v >= lo && v <= hi ? Math.round(v) : def; };
  return { policy, approval_hours: num(a.approval_hours, 1, 720, d.approval_hours), quiet_start: num(a.quiet_start, 0, 23, d.quiet_start), quiet_end: num(a.quiet_end, 0, 23, d.quiet_end), max_msgs_client_day: num(a.max_msgs_client_day, 0, 50, d.max_msgs_client_day), shadow_days: num(a.shadow_days, 0, 90, d.shadow_days), agent_daily_ops: num(a.agent_daily_ops, 0, 100000, d.agent_daily_ops), escalation: String(a.escalation || '').slice(0, 200) };
}
// an account may only make the developer's policy stricter (and set its own quiet hours)
export function mergeAutonomy(d, m) {
  const policy = {}; for (const k of R.AUTONOMY_CATS) { const a = d.policy[k], b = m?.policy?.[k]; policy[k] = b in ARANK && ARANK[b] > ARANK[a] ? b : a; }
  const q = v => Number.isInteger(v) && v >= 0 && v <= 23; return { ...d, policy, quiet_start: q(m?.quiet_start) ? m.quiet_start : d.quiet_start, quiet_end: q(m?.quiet_end) ? m.quiet_end : d.quiet_end };
}
function tenantAutonomy(v) {
  const policy = {}; for (const k of R.AUTONOMY_CATS) if (v?.policy?.[k] in ARANK) policy[k] = v.policy[k];
  const q = x => (x === '' || x == null ? undefined : Number.isInteger(+x) && +x >= 0 && +x <= 23 ? +x : fail('validation', { quiet: 'range' }));
  const out = { policy }; const s = q(v?.quiet_start), e = q(v?.quiet_end); if (s !== undefined) out.quiet_start = s; if (e !== undefined) out.quiet_end = e; return out;
}
// v3.13.1 — the account owner's own limits for his account's assistant («تعليماتي للمساعد»): when it must ask before acting
// (all | risky | none) and his standing orders in his words. Only the account's owner or admin writes them (settings.set, and
// the server checks the same); the assistant has no step that reaches them, so it can never loosen its own limits.
export const ASSIST_CONFIRM = ['all', 'risky', 'none'];
export function cleanAssist(v) { const o = v && typeof v === 'object' && !Array.isArray(v) ? v : {}; return { confirm: ASSIST_CONFIRM.includes(o.confirm) ? o.confirm : 'risky', rules: String(o.rules ?? '').replace(/\r/g, '').trim().slice(0, 4000) }; }
export const acctAssist = tid => cleanAssist(tid && tid !== 'platform' ? store.get(`set:${tid}:assist`, null) : null);
// v3.13.1 — the account's own limits for its AI team («استقلالية الفريق الذكي», never looser than the developer's) bind its
// assistant too: what one of them blocks the assistant never does; what one of them asks about waits for a tick, whatever the policy
export const acctAutonomy = tid => mergeAutonomy(autonomyOf(getP()), tid && tid !== 'platform' ? store.get(`set:${tid}:autonomy`, null) : null).policy;
const FIN_COLLS = ['invoices', 'expenses', 'payments', 'receipts', 'wallet_tx', 'obligations', 'b_payments', 'installments'];
const PRICE_COLLS = ['properties', 'units', 'leases', 'pr_services', 'projects'];
export function stepAutonomy(a) {
  if (!a || typeof a !== 'object') return '';
  if (a.do === 'delete') return 'delete_data';
  if (a.do === 'message' || a.do === 'send') return 'client_messages';
  if (a.do === 'create' || a.do === 'update') {
    if (FIN_COLLS.includes(a.coll)) return 'finance_entries'; if (a.coll === 'contracts') return 'contracts';
    if (a.do === 'update' && PRICE_COLLS.includes(a.coll) && a.row && ['price', 'rent', 'amount', 'price_from', 'price_to'].some(k => k in a.row)) return 'prices';
    return 'records';
  }
  return '';
}
// v3.13.1 — the account's settings its assistant may change: the same fields and checks as their screens (never its limits —
// «autonomy» and «assist» — nor its keys, connections or white label: those stay with the person, in their screens)
const TIME_RX = /^([01]\d|2[0-3]):[0-5]\d$/;
const dayList = v => (Array.isArray(v) ? [...new Set(v.map(x => +x).filter(d => Number.isInteger(d) && d >= 0 && d <= 6))].sort((a, b) => a - b) : null);
const intIn = (v, lo, hi) => { const n = Math.round(+latinDigits(String(v ?? '')).replace(/[^\d.-]/g, '')); return v === '' || v == null || !Number.isFinite(n) || n < lo || n > hi ? null : n; };
export const ACCT_SET_KEYS = ['profile', 'booking', 'pond', 'hr_policy', 'office_page', 'website']; // (v3.28: «موقعي»)
const ACCT_SETTINGS = {
  profile: {
    fields: c => R.parseFields(R.PROFILE_FIELDS[audienceOf(c.app)] || R.PROFILE_FIELDS.office).filter(f => !['image', 'images', 'file'].includes(f.type)),
    get: c => { const T = c.tenant || {}; return { name: T.name || '', city: T.city || '', country: T.country || '', timezone: T.tz || '', ...store.get(`set:${T.id}:profile`, {}) }; },
    clean(v, c, cur) { const fields = this.fields(c); const { row, errors } = cleanRow(fields, Object.fromEntries(Object.entries(v).filter(([k]) => fields.some(f => f.key === k)))); if (Object.keys(errors).length) fail('validation', errors); return { ...cur, ...row }; },
    put: (v, c) => OPS['settings.set']({ key: 'profile', value: v }, c),
  },
  booking: {
    get: c => OPS['booking.settings']({}, c),
    clean(v) {
      const days = dayList(v.days); if (!days?.length) fail('validation', { days: 'invalid' });
      for (const k of ['from', 'to']) if (!TIME_RX.test(String(v[k] ?? ''))) fail('validation', { [k]: 'time' });
      if (String(v.from) >= String(v.to)) fail('validation', { to: 'range' });
      const slot = intIn(v.slot_minutes, 10, 480); if (slot == null) fail('validation', { slot_minutes: 'range' }); const hz = intIn(v.horizon_days, 1, 180); if (hz == null) fail('validation', { horizon_days: 'range' });
      return { days, from: String(v.from), to: String(v.to), slot_minutes: slot, horizon_days: hz, note: String(v.note ?? '').slice(0, 300) };
    },
    put: (v, c) => OPS['booking.settings']({ value: v }, c),
  },
  pond: { get: c => OPS['pond.settings']({}, c), clean(v) { const h = intIn(v.hours, 1, 2160); if (h == null) fail('validation', { hours: 'range' }); return { hours: h }; }, put: (v, c) => OPS['pond.settings']({ value: v }, c) },
  hr_policy: {
    get: c => { const r = OPS['hr.policy']({}, c) || {}; const keys = [...R.parseFields(R.HR_POLICY_FIELDS).map(f => f.key), 'workdays']; return Object.fromEntries(keys.map(k => [k, r[k] ?? R.HR_POLICY[k]])); },
    clean(v, c, cur) {
      const fields = R.parseFields(R.HR_POLICY_FIELDS); const { row, errors } = cleanRow(fields, Object.fromEntries(Object.entries(v).filter(([k]) => fields.some(f => f.key === k)))); if (Object.keys(errors).length) fail('validation', errors);
      for (const k of ['workday_start', 'workday_end']) if (!TIME_RX.test(String(row[k] ?? ''))) fail('validation', { [k]: 'time' });
      const days = 'workdays' in v ? dayList(v.workdays) : cur.workdays; if (!days?.length) fail('validation', { workdays: 'invalid' });
      return { ...cur, ...row, workdays: days };
    },
    put: (v, c) => OPS['hr.policy']({ value: v }, c),
  },
  office_page: { get: c => store.get(`set:${c.tenant.id}:office_page`, {}), clean: v => ({ show: v.show === true || v.show === 'true', headline: String(v.headline ?? '').trim().slice(0, 140), about: String(v.about ?? '').trim().slice(0, 1200) }), put: (v, c) => OPS['settings.set']({ key: 'office_page', value: v }, c) },
  website: { get: c => webGet(c), clean: v => cleanWebsite(v), put: (v, c) => OPS['settings.set']({ key: 'website', value: v }, c) }, // v3.28: «موقعي»
};
// v3.28 — «موقعي» (the owner, 2026-10-15: «انشئ لكل مشتري خدمة إنشاء موقع لعرض خدماته ومنتجاته وغيرها للعملاء متكامل من داخل
// واجهته ونشره برابط خاص … تحكم كامل لا محدود من خلال مساعد الذكاء الاصطناعي»): the website's own settings — its link, its look,
// its languages, how to reach the business, whether search engines may list it and whether it is the site's home page
export const WEB_FONTS = ['modern', 'classic', 'rounded', 'tajawal', 'cairo', 'almarai', 'readex', 'plex', 'messiri', 'amiri', 'kufi'], WEB_MODES = ['light', 'dark'];
// v3.28 (the owner: «ليكون بتصميم 3d ومليان حياة وابداع … على ان يستطيع التحكم به تحكم كامل وتصميمه هو وتعديله»): its living 3D
// scene and its hour, its motion, depth, ground, shape and buttons — the same lists as the site's server (dar-web3d.php)
export const WEB_SCENES = ['auto', 'city', 'tower', 'photo', 'emblem', 'aurora', 'lines', 'none'], WEB_TIMES = ['auto', 'day', 'dusk', 'night'], WEB_MOTIONS = ['alive', 'calm', 'still'];
export const WEB_DEPTHS = ['tilt', 'float', 'flat'], WEB_BGS = ['aurora', 'blueprint', 'plain'], WEB_SHAPES = ['soft', 'round', 'sharp'], WEB_BUTTONS = ['3d', 'glass', 'flat'];
export const WEB_EFFECTS = ['auto', 'rise', 'tilt', 'zoom', 'flip', 'none'];
// each block's own shapes (the section's «layout»)
export const WEB_LAYOUTS = { cards: ['auto', 'tilt', 'flip', 'plain'], how_steps: ['auto', 'stairs', 'plain'], photo_gallery: ['auto', 'ring', 'grid'], client_reviews: ['auto', 'flow', 'grid'], key_numbers: ['auto', 'count', 'plain'], hero: ['auto', 'search', 'split', 'center', 'cover'], lead_form: ['request', 'valuation', 'alert', 'interest'], custom_html: ['auto', 'bare'] }; // (v3.31: the hero's layout, the kind of form)
// v3.31 (the owner: «خدمات متطورة وتفاعلية … بيانات موقعه غير مربوطة بواجهته»): what its visitors may do there, the business's
// advertising pixels, and the fields the website takes from the business's own records while its own settings leave them empty
// (the same lists as the site's server, dar-web2.php)
export const WEB_FEATURES = ['favs', 'share', 'calc', 'book', 'alerts', 'bar', 'suggest', 'print'];
export const WEB_PX = { ga4: /^G-[A-Z0-9]{4,14}$/, gads: /^AW-\d{6,14}$/, meta: /^\d{8,20}$/, tiktok: /^[A-Z0-9]{10,32}$/, snap: /^[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}$/ };
export const WEB_LINKED = ['name', 'logo', 'phone', 'whatsapp', 'email', 'address', 'about', 'license', 'cr', 'instagram', 'x', 'tiktok', 'snapchat', 'youtube', 'linkedin', 'facebook', 'review_url'];
export const WEB_THEMES = { prestige: { color: '#1b2433', accent: '#c9a45c', font: 'messiri', mode: 'dark', scene: 'emblem', time: 'night', bg: 'plain', shape: 'sharp', buttons: 'glass', depth: 'float' },
  coastal: { color: '#0e5a7a', accent: '#f08a5d', font: 'readex', mode: 'light', scene: 'city', time: 'day', bg: 'aurora', shape: 'round', buttons: 'flat', depth: 'tilt' },
  urban: { color: '#23272f', accent: '#e2683c', font: 'plex', mode: 'light', scene: 'city', time: 'dusk', bg: 'blueprint', shape: 'sharp', buttons: '3d', depth: 'tilt' },
  desert: { color: '#6b4226', accent: '#d9a25f', font: 'kufi', mode: 'light', scene: 'lines', time: 'dusk', bg: 'plain', shape: 'soft', buttons: '3d', depth: 'float' },
  oasis: { color: '#1f4d3a', accent: '#d8c27a', font: 'almarai', mode: 'light', scene: 'aurora', time: 'day', bg: 'aurora', shape: 'round', buttons: 'glass', depth: 'float' },
  midnight: { color: '#2a2f6b', accent: '#7fd1c7', font: 'tajawal', mode: 'dark', scene: 'city', time: 'night', bg: 'aurora', shape: 'soft', buttons: '3d', depth: 'tilt' },
  editorial: { color: '#3b2a4a', accent: '#d4a33f', font: 'amiri', mode: 'light', scene: 'none', time: 'day', bg: 'plain', shape: 'sharp', buttons: 'flat', depth: 'flat' },
  skyline: { color: '#1e3a5f', accent: '#c8a24a', font: 'cairo', mode: 'light', scene: 'auto', time: 'auto', bg: 'aurora', shape: 'soft', buttons: '3d', depth: 'tilt' } };
export function webProfileOf(prof = {}, conns = {}, wl = {}, T = {}) {
  const s = (x, n = 200) => String(x ?? '').trim().slice(0, n); const ph = x => String(x ?? '').replace(/[^\d+]/g, '');
  const acc = k => { const x = conns?.[k]; return x && typeof x === 'object' && !['pending', 'off', 'failed', 'removed', 'error'].includes(String(x.status || '')) ? String(x.account || '').trim() : ''; };
  const wa = ph(acc('whatsapp')), pub = ph(prof?.public_phone);
  const parts = [...new Set([s(prof?.address, 160), s(prof?.district, 60), s(prof?.city || T?.city, 60)].filter(Boolean))];
  const em = s(prof?.email, 120);
  const out = { name: s(wl?.brand_name, 80) || s(prof?.name, 80) || s(T?.name, 80), logo: IMG_OK.test(String(prof?.logo || '')) ? String(prof.logo) : '', phone: pub || wa, whatsapp: wa || pub, email: /^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/.test(em) ? em : '',
    address: parts.join(/\p{Script=Arabic}/u.test(parts.join('')) ? '، ' : ', '), about: s(prof?.bio, 1200), license: s(prof?.license_no, 60), cr: s(prof?.cr, 60), review_url: '' };
  for (const k of WEB_SOCIAL) { const u = acc(k); out[k] = /^https:\/\/[^\s<>"'`]{4,300}$/i.test(u) ? u : ''; }
  const g = conns?.google_business; if (g && /^https:\/\/[^\s<>"'`]{4,400}$/.test(String(g.review_url || ''))) out.review_url = String(g.review_url);
  return out;
}
export const WEB_SOCIAL = ['instagram', 'x', 'tiktok', 'snapchat', 'youtube', 'linkedin', 'facebook'];
export const WEB_RESERVED = ['admin', 'api', 'app', 'assets', 'builders', 'console', 'dar', 'developer', 'lib', 'login', 'partner', 'providers', 'site', 'static', 'www', 'mail', 'help', 'support', 'status', 'legal', 'v', 's'];
export const webSlugOk = s => /^[a-z0-9](?:[a-z0-9-]{1,38}[a-z0-9])$/.test(String(s || '')) && !String(s).includes('--') && !WEB_RESERVED.includes(String(s));
const knownLangCode = l => !!l && (isBaseLang(l) || !!langInfo(l));
const webHex = (x, d = '') => /^#[0-9a-f]{6}$/i.test(String(x || '')) ? String(x).toLowerCase() : d;
const webUrl = x => { const v = String(x ?? '').trim().slice(0, 300); return /^https:\/\/[^\s<>"'`]+$/i.test(v) ? v : ''; };
export function cleanWebsite(v = {}) {
  const str = (x, n) => String(x ?? '').trim().slice(0, n); const out = {};
  const slug = str(v.slug, 40).toLowerCase(); if (slug && !webSlugOk(slug)) fail('validation', { slug: WEB_RESERVED.includes(slug) ? 'reserved' : 'slug' }); out.slug = slug;
  out.name = str(v.name, 80); out.tagline = str(v.tagline, 160);
  out.color = webHex(v.color, '#1e3a5f'); out.accent = webHex(v.accent, '#c8a24a');
  out.font = WEB_FONTS.includes(v.font) ? v.font : 'modern'; out.mode = WEB_MODES.includes(v.mode) ? v.mode : 'light';
  const lang = str(v.lang, 12); out.lang = knownLangCode(lang) ? lang : 'ar';
  out.langs = [...new Set((Array.isArray(v.langs) ? v.langs : String(v.langs || '').split(/[\s,،]+/)).map(x => String(x || '').trim()).filter(x => knownLangCode(x) && x !== out.lang))].slice(0, 80);
  const ph = x => String(x ?? '').replace(/[^\d+]/g, '').slice(0, 20); out.phone = ph(v.phone); out.whatsapp = ph(v.whatsapp);
  const em = str(v.email, 120); if (em && !/^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/.test(em)) fail('validation', { email: 'email' }); out.email = em;
  out.address = str(v.address, 200); out.hours = str(v.hours, 120);
  for (const k of WEB_SOCIAL) out[k] = webUrl(v[k]);
  out.logo = IMG_OK.test(String(v.logo || '')) && String(v.logo).length < 400000 ? String(v.logo) : '';
  out.index = v.index === true || v.index === 'true' || v.index === 'on'; out.home = v.home === true || v.home === 'true' || v.home === 'on';
  // v3.28: its 3D scene, motion, depth, ground, shape, buttons — and his own CSS (the site's server cleans it when it draws the page)
  for (const [k, list, d] of [['scene', WEB_SCENES, 'auto'], ['time', WEB_TIMES, 'auto'], ['motion', WEB_MOTIONS, 'alive'], ['depth', WEB_DEPTHS, 'tilt'], ['bg', WEB_BGS, 'aurora'], ['shape', WEB_SHAPES, 'soft'], ['buttons', WEB_BUTTONS, '3d']]) out[k] = list.includes(v[k]) ? v[k] : d;
  out.css = String(v.css ?? '').slice(0, 60000); out.design = v.design === 'free' ? 'free' : ''; // (v3.33.61: a design the AI made whole)
  // v3.31: its own words where it wants other ones than its profile's, what its visitors may do, its pixels, its share picture, its
  // payment estimate's starting figures, the ready look it started from
  out.about = str(v.about, 1200); out.license = str(v.license, 60); out.cr = str(v.cr, 60); out.review_url = webUrl(v.review_url);
  const f = v.features && typeof v.features === 'object' ? v.features : {}; out.features = Object.fromEntries(WEB_FEATURES.map(k => [k, !(k in f) || (f[k] !== false && f[k] !== 'false' && f[k] !== 0)]));
  const px = v.px && typeof v.px === 'object' ? v.px : {}; out.px = {};
  for (const [k, re] of Object.entries(WEB_PX)) { const x = String(px[k] ?? '').trim(); if (!x) continue; if (!re.test(x)) fail('validation', { ['px_' + k]: 'format' }); out.px[k] = x; }
  out.og_image = IMG_OK.test(String(v.og_image || '')) && String(v.og_image).length < 400000 ? String(v.og_image) : '';
  const cc = v.calc && typeof v.calc === 'object' ? v.calc : {}; const num = (x, a, b, d) => (x === '' || x == null || isNaN(+x)) ? d : Math.max(a, Math.min(b, +x));
  out.calc = { rate: num(cc.rate, 0, 30, 5.5), years: Math.round(num(cc.years, 1, 35, 25)), down: Math.round(num(cc.down, 0, 90, 20)) };
  out.theme = /^[a-z]{2,20}$/.test(String(v.theme || '')) ? String(v.theme) : '';
  out.redirects = cleanRedirects(v.redirects); out.banner = cleanBanner(v.banner); // v3.33.31
  return out;
}
// v3.33.31 (the owner: «طور الخدمة لتنافس المواقع العالمية»): the old addresses he sends to a new place (a permanent redirect — only for an address
// that would otherwise find nothing: a page that exists always wins), and the announcement bar over his header (a text, a link, a tone, a last day).
// The site's server (dar-web.php web_redirects_clean / web_banner_clean) cleans them by the same rules.
export const WEB_NO_REDIRECT = ['sitemap.xml', 'robots.txt', 'contact', 'languages', 'favorites'];
const WEB_PATH_RE = /^[a-z0-9][a-z0-9/_.-]{0,79}$/;
export function cleanRedirects(list) {
  const out = []; const seen = new Set();
  const norm = x => String(x ?? '').trim().toLowerCase().replace(/^https?:\/\/[^/]+/i, '').replace(/[?#].*$/, '').replace(/^\/+|\/+$/g, '');
  for (const r of Array.isArray(list) ? list : []) {
    if (!r || typeof r !== 'object' || out.length >= 100) continue;
    const from = norm(r.from); if (!WEB_PATH_RE.test(from) || WEB_NO_REDIRECT.includes(from) || seen.has(from)) continue;
    let to = String(r.to ?? '').trim();
    if (/^https:\/\/[^\s<>"'`]{4,300}$/i.test(to)) { /* another site */ }
    else { if (/^[a-z][a-z0-9+.-]*:/i.test(to)) continue; to = norm(to); if (to === 'home') to = ''; if (to !== '' && !WEB_PATH_RE.test(to)) continue; if (to === from) continue; }
    seen.add(from); out.push({ from, to });
  }
  return out;
}
export const WEB_BANNER_TONES = ['brand', 'accent', 'dark'];
export function cleanBanner(b) {
  b = b && typeof b === 'object' ? b : {}; const s = (x, n) => String(x ?? '').trim().slice(0, n);
  let link = s(b.link, 300); if (link && !/^(https:\/\/[^\s<>"'`]+|tel:[+\d]{4,20}|mailto:[^\s<>"'`]+|[a-z0-9][a-z0-9-]{0,40}|#[a-z0-9_-]{1,40})$/i.test(link)) link = '';
  let until = s(b.until, 10); if (!/^\d{4}-\d{2}-\d{2}$/.test(until)) until = '';
  return { on: b.on === true || b.on === 'true' || b.on === 'on', text: s(b.text, 160), label: s(b.label, 30), link, until, tone: WEB_BANNER_TONES.includes(b.tone) ? b.tone : 'brand' };
}
// what he has set, over the starting values (its owner's language) — v3.31: a field he leaves empty is the business's own, read from
// its records (its profile, its linked accounts, its brand) at every visit; webGet adds those values and names them (_linked)
function webRaw(c) {
  const T = c.tenant || {}; const owner = users().find(u => u.tenant === T.id && u.role === 'owner');
  const lang = knownLangCode(owner?.lang) ? owner.lang : knownLangCode(R.WORLD?.[T.country]?.lang) ? R.WORLD[T.country].lang : 'ar';
  const base = { slug: '', name: '', tagline: '', color: '#1e3a5f', accent: '#c8a24a', font: 'modern', mode: 'light', lang, langs: [], phone: '', whatsapp: '', email: '', address: '', hours: '', index: false, home: false, scene: 'auto', time: 'auto', motion: 'alive', depth: 'tilt', bg: 'aurora', shape: 'soft', buttons: '3d', css: '' };
  return { ...base, ...store.get(`set:${T.id}:website`, {}) };
}
const webProfile = T => webProfileOf(store.get(`set:${T.id}:profile`, {}), store.get(`set:${T.id}:connections`, {}), store.get(`set:${T.id}:white_label`, {}), T);
function webGet(c) {
  const raw = webRaw(c); const pf = webProfile(c.tenant || {}); const out = { ...raw }; const linked = [];
  for (const k of WEB_LINKED) if (!String(raw[k] ?? '') && pf[k]) { out[k] = pf[k]; linked.push(k); }
  return { ...out, _linked: linked, _profile: pf };
}
const webPubInfo = tid => { const p = store.get(`set:${tid}:website_pub`, null); return p && p.v ? { v: p.v, at: p.at, by: p.by || '', off: p.off === true, slug: p.settings?.slug || '' } : null; };

// what a person may read of them (the assistant's look-up): only the keys his role reaches
function acctSettings(c) {
  const out = {};
  for (const k of ACCT_SET_KEYS) { try { out[k] = ACCT_SETTINGS[k].get(c); } catch { /* not his to read */ } }
  return out;
}
function acceptCountry(v) { const P = getP(); const cc = String(v || P.default_country || 'SA').trim().toUpperCase(); if (!countryOpen(cc, rowsOf('platform', 'countries'), P)) fail('validation', { country: 'country_na' }); return cc; }
// in-app notices: what happened outside the screen (public pages, workers, the AI team) — shown under the bell
function notify(tid, n) {
  if (!tid || tid === 'platform') return; const list = rowsOf(tid, 'notices');
  if (builderTenant(tid)) { const head = String(n.link || '').split(/[/?#]/)[0]; if (head) n = { ...n, link: svcIn('builders', head) + String(n.link).slice(head.length) }; if (n.svc) n = { ...n, svc: svcIn('builders', n.svc) }; }
  list.unshift({ id: uid('n'), created: nowIso(), code: String(n.code || '').slice(0, 40), vars: n.vars && typeof n.vars === 'object' ? n.vars : {}, title: String(n.title || '').slice(0, 200), body: String(n.body || '').slice(0, 1000), level: ['info', 'good', 'warn', 'bad'].includes(n.level) ? n.level : 'info', link: String(n.link || '').slice(0, 160), svc: String(n.svc || '').slice(0, 60), act: String(n.act || '').slice(0, 60), to: n.to || 'managers', read_by: [] });
  saveRows(tid, 'notices', list.slice(0, 300));
}

function issueToken(user, app, imp = null, days = 0) {
  const token = 'tk_' + randomHex(20); const tokens = store.get('tokens', {});
  for (const [k, v] of Object.entries(tokens)) if (v.exp < Date.now()) delete tokens[k];
  tokens[token] = { uid: user.id, app, exp: Date.now() + (days || +getP().security?.session_days || 30) * DAY, imp }; store.set('tokens', tokens);
  return token;
}
function publicUser(u) { if (!u) return null; const { hash, salt, ...rest } = u; return rest; }
// v3.17: what the pages need of the map settings
function mapsOf(P) {
  const m = P.maps || {}; const tiles = ['osm', 'carto', 'custom'].includes(m.tiles) ? m.tiles : 'osm'; const url = String(m.tile_url || ''); const keyed = /\{key\}/.test(url);
  return { on: m.on !== false, tiles: tiles === 'custom' && !/^https:\/\//.test(url) ? 'osm' : tiles, tile_url: tiles === 'custom' && !keyed ? url : '', proxied: tiles === 'custom' && keyed, attribution: String(m.attribution || '').slice(0, 200), nearby: m.nearby !== false, precision: ['exact', 'approximate', 'hidden'].includes(m.precision) ? m.precision : 'approximate' };
}
// v3.26: a sold copy's business as this browser knows it (on a host the server says it with every first pull: RUNTIME.solo)
function soloLocal() { const T = tenants().find(x => x.solo); return T ? { edition: SOLO, app: T.app, t: T.id, name: T.name || '', color: '', country: T.country || '' } : { edition: SOLO, app: SOLO === 'builder' ? 'builders' : 'app', t: '', name: '', color: '', country: '' }; }
function bootData(c) {
  const P = getP(); const dev = c.user?.app === 'developer';
  const base = {
    services: P.services, custom: P.custom, custom_ent: P.custom_ent, cats: P.cats, catOrder: P.catOrder, texts: P.texts, theme: P.theme, landing: P.landing,
    partner: P.partner, ai: P.ai, links: P.links, domain: P.domain, landings: P.landings, tenant_roles: P.tenant_roles, onboarding: P.onboarding, price_display: P.price_display, tax_note: P.tax_note, base_currency: P.base_currency, base_usd_rate: P.base_usd_rate, default_country: P.default_country, world: worldOf(P), fx: fxOf(P), autonomy: dev ? autonomyOf(P) : { ...autonomyOf(P), escalation: '' }, geo: R.WORLD[RUNTIME.geo] ? RUNTIME.geo : null, langs: RUNTIME.langs || null,
    ent_extra: P.ent_extra, ent_opts: P.ent_opts, ent_hide: P.ent_hide, channel_policy: P.channel_policy && typeof P.channel_policy === 'object' ? P.channel_policy : {}, // (v3.33, note 56) recipes: P.recipes, password_min: Math.max(6, +P.security?.password_min || 8),
    maintenance: P.maintenance?.on ? P.maintenance : null, demo_mode: SHOW ? 'sandbox' : (P.demo_mode || 'readonly'), // (v3.26: the preview's examples are each visitor's own)
    captcha: P.captcha?.provider && P.captcha?.site_key ? { provider: P.captcha.provider, site_key: P.captcha.site_key, on: P.captcha.on || [] } : null,
    maps: mapsOf(P), // v3.17: the maps every page draws (never a key: a provider that needs one is read through the server)
    // v3.33 (the owner, 2026-10-22 — notes 23, 27, 39: «تعطيل بعض الخدمات لا ينعكس على باقي المنصة»): the state of every feature he set (on · off ·
    // maintenance · soon, its message, the plans it is limited to) reaches every page — the home page, the sign-up pages, each account's screens
    features: P.features && typeof P.features === 'object' ? Object.fromEntries(FEATURE_DEFS.features.map(f => [f.id, featOwn(P, f.id)]).filter(([, v]) => Object.keys(v).length).map(([k, v]) => [k, { state: String(v.state || 'on'), ...(v.msg ? { msg: v.msg } : {}), ...(Array.isArray(v.plans) && v.plans.length ? { plans: v.plans.map(String).slice(0, 20) } : {}) }])) : {}, // (v3.33.12: each feature under its own name, whichever way it was saved)
    legal_edits: legalEditsOf(P), tracking: trackingOf(P), share_base: /^https:\/\//.test(P.share_base || '') ? P.share_base : '', hosts: P.hosts || [], cname_target: P.cname_target || '', login_code: P.security?.login_code || 'off', upload_max_mb: Math.min(25, Math.max(1, +P.upload_max_mb || 1)), max_photos: Math.min(40, Math.max(12, +P.max_photos || 12)),
    billing: c.user ? billingCfg(P) : undefined, // v3.13.2: how subscribers pay (bank details, the lifecycle's days) — for signed-in people
    // v3.33.31 (the owner, 2026-10-28: «الزر الظاهر في الصورة لا يمكن إطفاءه»): the contact details a visitor is sent to when paying online is not open (the
    // developer's «sales» record) reach the pages — they were saved but never delivered, so the screens showed nothing
    sales: P.sales && typeof P.sales === 'object' ? { whatsapp: String(P.sales.whatsapp || '').slice(0, 30), phone: String(P.sales.phone || '').slice(0, 30), email: String(P.sales.email || '').slice(0, 120), ...(Array.isArray(P.sales.note) ? { note: P.sales.note.slice(0, 3).map(x => String(x || '').slice(0, 400)) } : {}) } : null,
    login_providers: rowsOf('platform', 'oauth_apps').filter(a => a.active !== false && a.login === true && a.client_id && a.ready !== false).map(a => a.platform),
    langs_incomplete: P.i18n?.incomplete !== false, // v3.26: the owner allowed languages that are not fully translated yet (v3.28, the owner: «كل لغات العالم» — allowed unless he limits them)
    solo: SOLO ? (RUNTIME.solo && RUNTIME.solo.t ? RUNTIME.solo : soloLocal()) : null, show: SHOW, // v3.26: a sold copy's business (its interface, its account, its name) · the showcase
  };
  const pub = coll => rowsOf('platform', coll);
  const data = {
    P: dev ? { ...base, trial_all: P.trial_all !== false, dev_roles: P.dev_roles, dev_roles_view: P.dev_roles_view, wa: P.wa, master_key_preview: P.master_key_preview, assist: P.assist } : base, // v3.13: the owner's assistant policy/rules reach his panel (never a visitor) · v3.31: the roles' rows to see too
    countries: pub('countries'), plans: pub('plans').filter(p => dev || p.active !== false), addons: pub('addons').filter(a => dev || (a.active !== false && a.customer !== false)), // (v3.33, notes 47 and 66: customers see only what they may buy)
    offers: pub('offers').filter(o => o.active !== false && (!o.valid_until || new Date(o.valid_until) >= new Date(new Date().toDateString()))),
    gateways: SOLO || SHOW ? [] : pub('gateways').map(g => ({ code: g.code, name: g.name, countries: g.countries, active: g.active, env: g.env })), // (v3.26.1: none in a sold copy)
    // v3.5: the developer's wording for a system notice (per language; the bell uses it instead of the built-in words)
    ntpl: pub('notif_templates').filter(x => x && x.code && x.body && (x.channel || 'app') === 'app').map(x => ({ code: x.code, lang: x.lang || '', body: String(x.body).slice(0, 600) })),
    mode: CFG.mode, version: VERSION,
  };
  if (c.user) {
    const ob = c.tenant && !dev ? store.get(`set:${c.tenant.id}:onboarding`, null) : null;
    // (v3.32.1: every service is in the menu — the answers to the first questions only order and suggest; what he took out himself stays
    // out; a list kept from before the update limits nothing any more)
    const obMenu = null; const obHide = Array.isArray(ob?.hidden) ? ob.hidden.map(String) : [];
    data.me = { user: publicUser(c.user), tenant: withBrand(c.tenant), imp: c.imp, perms: dev ? devPerms(c) : [], view: dev ? devView(c) : [], menu: obMenu, hide: obHide, rec: (ob?.rec || []).filter(id => obHide.includes(id)), style: { ...DEFAULT_STYLE, ...(ob?.style || {}) }, onboarded: dev || !!ob?.done || !!c.tenant?.demo || !onboardingFor(c.app, P), answers: ob?.answers || {}, ...(c.tenant && !dev ? { assist: acctAssist(c.tenant.id), autonomy: acctAutonomy(c.tenant.id) } : {}) }; // v3.13.1: the account's assistant policy and its AI-team limits (its plan cards follow them)
  }
  return data;
}

// Which services own a collection in an app (used to enforce plan/country/suspension on data calls).
// v2.9: data only the platform writes (commissions, payouts, offers, ledgers, wallets). Subscribers and their AI team
// read it; every write comes from inside the platform, wrapped in asSystem() (synchronous, so the flag cannot leak).
let SYS_WRITE = 0;
// v3.30: what a form, an import of one record or the assistant may write in an account's list — never a field the system keeps (a
// client's referral code, a portal's token, a counter: shown, never typed); the system's own steps write those themselves
const typedFields = coll => { const fs = fieldsOf(coll); return SYS_WRITE || isPlatformColl(coll) ? fs : fs.filter(f => !f.ro); };
const asSystem = f => { SYS_WRITE++; try { return f(); } finally { SYS_WRITE--; } };
const sumAmt = list => Math.round(list.reduce((s, r) => s + (+r.amount || 0), 0) * 100) / 100;
// a commission becomes payable once its hold period has passed (it only ever moves forward). v3.13.2: on a host the server
// alone writes commissions (its duty ripens them); a page shows the same status without writing
const isHostedNow = () => CFG.mode === 'hosted' && !!HOSTED.call;
// v3.22: the numbers of the partner programme that partners see (a change of one of them is told to every partner)
const PP_SHOWN = ['commission_rate', 'commission_months', 'hold_days', 'min_payout', 'min_count', 'max_discount', 'max_trial_hours', 'ownership_days', 'bonus_meeting', 'bonus_trial', 'bonus_subscription', 'bonus_renewal', 'bonus_recruit', 'recruit_rate', 'recruit_subs', 'recruit_months', 'pass_first', 'pass_weekly', 'pass_hours'];
const ppShown = P => { const pp = partnerCfg(P, R); return PP_SHOWN.map(k => +pp[k] || 0); };
function ripenCommissions(tid) {
  const list = rowsOf(tid, 'p_commissions'); const today = new Date().toISOString().slice(0, 10); let ch = false;
  for (const r of list) if (r.status === 'pending' && r.due_date && String(r.due_date).slice(0, 10) <= today) { r.status = 'eligible'; r.updated = nowIso(); ch = true; }
  if (ch && !isHostedNow()) saveRows(tid, 'p_commissions', list); return list;
}
// a developer adds and removes units (its listings follow); a loose "property" has no unit behind it
function noLooseListing(c, coll) { if (coll === 'properties' && (c.app === 'builders' || builderTenant(c.tenant?.id))) fail('use_units'); }
function guardCollection(c, coll, write) {
  if (coll === 'market_requests' && !write) { needUser(c); if (c.app === 'providers' || c.user.app === 'developer') return; fail('forbidden'); }
  if (isPlatformColl(coll)) {
    if (!write && R.PUBLIC_READ.includes(coll)) return;
    (write ? needPerm : needView)(c, COLL_PERM[coll] || 'services'); return; // (v3.31: reading needs the permission to see it)
  }
  needUser(c);
  if (c.user.app === 'developer') fail('forbidden');
  if (write && R.SYSTEM_OWNED.includes(coll) && !SYS_WRITE) fail('forbidden', { reason: 'system_owned' });
  if (write && (coll === 'site_pages' || coll === 'site_sections') && !MANAGER_ROLE.includes(roleOf(c))) fail('forbidden', { role: c.user.role }); // (v3.28: the website is its managers' to write)
  const P = getP(); const svcs = catalog(P).filter(s => s.app === c.app && ((s.e || []).includes(coll) || (coll === 'properties' && c.app === 'builders' && (s.e || []).includes('units'))));
  const customColl = coll.startsWith('x_') && (Array.isArray(P.custom) ? P.custom : []).some(s => s && s.app === c.app && (s.e || []).includes(coll));
  if (!svcs.length && !customColl) fail('forbidden');
  const mine = svcs.filter(s => roleAllows(c.app, c.user.role, s, P));
  if (svcs.length && !mine.length) fail('forbidden', { role: c.user.role });
  const ctx = accessCtx(c);
  const states = mine.map(s => access(s, ctx));
  if (mine.length && !states.includes('ok')) fail(states.includes('plan') ? 'not_in_plan' : states.includes('country') ? 'not_in_country' : 'service_suspended');
  if (write) needWritable(c);
}
function accessCtx(c) { return { dev: c.user?.app === 'developer', country: c.tenant?.country, intl: !listedCountry(c.tenant?.country), plan: c.tenant?.plan, audience: audienceOf(c.app), plans: rowsOf('platform', 'plans'), unlocked: unlockedOf(c.tenant, rowsOf('platform', 'addons')), trial: trialOpen(c.tenant, getP()), tsvc: trialSvcs(c.tenant) }; }
// the plan sells AI operations — whichever engine runs them (cloud team or the local engine)
function aiAllowance(c) { const lim = +planLimits(c).ai_ops; if (lim) { const m0 = new Date(); m0.setDate(1); m0.setHours(0, 0, 0, 0); const used = store.get('jobs', []).filter(j => j.tenant === c.tenant?.id && new Date(j.at) >= m0 && isAiJob(j)).length; if (used >= lim + (+c.tenant?.extra?.ai_ops || 0)) fail('quota_exceeded', { limit: lim, key: 'ai_ops' }); } }
function planLimits(c) {
  const p = rowsOf('platform', 'plans').find(x => x.code === c.tenant?.plan && x.audience === audienceOf(c.app)); const L = { ...(p?.limits || {}) };
  // v3.33 (the owner, 2026-10-22 — note 66): the add-ons the account holds add to a plan's limit (+5 users, +10,000 properties); an unlimited plan stays unlimited; the twin of dar-acct.php acct_addon_extra
  const held = c.tenant?.addons || []; const rows = held.length ? rowsOf('platform', 'addons') : [];
  for (const code of held) { const a = rows.find(x => x.code === code); if (a?.extra_key && +a.extra_n > 0 && +L[a.extra_key] > 0) L[a.extra_key] = +L[a.extra_key] + +a.extra_n; }
  for (const k of Object.keys(L)) if (+L[k] > 0 && +c.tenant?.extra?.[k] > 0 && !/^ai_/.test(k)) L[k] = +L[k] + +c.tenant.extra[k]; // (v3.33.21: every limit, as dar-sync.php plan_limit)
  return L;
}
const LIMIT_COLL = { team: 'users', properties: 'properties', projects: 'projects', units: 'units' }; // (v3.33.21: the server refuses the same — dar-sync.php PLAN_COLLS)
const realCount = list => list.filter(r => !isStarterRow(r)).length; // (the starter examples are not his: they never count — as the server's plan_rows_guard)
// Employees see only their own attendance, leave and payslips; HR/managers see everyone.
const SELF_COLLS = ['hr_attendance', 'hr_leaves', 'hr_payroll'];
const HR_ROLES = ['owner', 'admin', 'manager', 'hr'];
function selfOnly(c, coll) { return SELF_COLLS.includes(coll) && c.user && c.user.app !== 'developer' && !HR_ROLES.includes(c.user.role) && !(c.user.role === 'accountant' && coll === 'hr_payroll'); }
function selfName(c) { if (!c.tenant) return c.user?.name || ''; const em = String(c.user?.email || '').toLowerCase(); const e = em && rowsOf(c.tenant.id, 'hr_employees').find(x => String(x.email || '').toLowerCase() === em); return e ? e.name : (c.user?.name || ''); }

function listRows(list, p) {
  let out = list;
  if (p.where) for (const [k, v] of Object.entries(p.where)) if (v !== '' && v != null) out = out.filter(r => Array.isArray(r[k]) ? r[k].includes(v) : String(r[k] ?? '') === String(v));
  if (p.q) { const q = latinDigits(p.q).toLowerCase().trim(); if (q) out = out.filter(r => Object.values(r).some(v => typeof v === 'string' && !v.startsWith('data:') && latinDigits(v).toLowerCase().includes(q))); }
  if (p.sort) { const desc = p.sort.startsWith('-'); const k = p.sort.replace(/^-/, ''); out = [...out].sort((a, b) => { const x = a[k] ?? '', y = b[k] ?? ''; const r = (typeof x === 'number' && typeof y === 'number') ? x - y : String(x).localeCompare(String(y)); return desc ? -r : r; }); }
  const total = out.length; const off = +p.offset || 0; const lim = Math.min(+p.limit || 500, 2000);
  return { rows: out.slice(off, off + lim), total };
}
const tenantKey = (c, coll) => isPlatformColl(coll) ? 'platform' : c.tenant.id;

function emitEvent(c, event, row) {
  // v3.2: webhooks go straight out — from the server when live, from the office's browser on the static site — and never
  // through the automation (each call there would be a paid execution). Fire-and-forget: the write never waits for it.
  if (CFG.mode === 'hosted') return; // v3.5: on the site's own server the server notices the change and sends it (signed, retried, logged)
  const hooks = c.tenant ? rowsOf(c.tenant.id, 'webhooks').filter(h => h.active !== false && h.event === event) : [];
  if (hooks.length && O32) { const p = O32.deliverHooks(c, event, row); HOOKS_INFLIGHT.add(p); p.catch(() => {}).finally(() => HOOKS_INFLIGHT.delete(p)); }
}
const HOOKS_INFLIGHT = new Set();
let O32 = null; // v3.2 operations (assigned once the module has loaded, see below)
const EVENT_OF = { leads: 'lead_created', properties: 'property_created', appointments: 'appointment_created' };

// v2.5.3: the job list stays bounded, but only finished jobs are dropped (oldest first) — queued, running and awaiting-approval work is never lost
const JOB_CAP = 2000, JOB_FINAL = ['done', 'failed', 'rejected'];
function trimJobs(jobs) { for (let i = jobs.length - 1; i >= 0 && jobs.length > JOB_CAP; i--) if (JOB_FINAL.includes(jobs[i].status)) jobs.splice(i, 1); }
function queueJob(c, j) {
  const jobs = store.get('jobs', []);
  // the subscriber's chosen style (tone/detail/channel) travels with every AI job so the AI team answers the way they asked
  const style = c.tenant && c.user?.app !== 'developer' ? store.get(`set:${c.tenant.id}:onboarding`, {})?.style : undefined;
  const job = { id: uid('j'), at: nowIso(), app: c.app, tenant: c.tenant?.id || (c.user?.app === 'developer' ? 'platform' : null), uid: c.user?.id || null, lang: LANG.cur, country: c.tenant?.country || null, tz: c.tenant ? (c.tenant.tz || tzOf(c.tenant.country)) : null, status: RUNTIME.server ? 'queued' : 'waiting_link', ...(style ? { style } : {}), ...j };
  if (c.tenant && c.user?.app !== 'developer' && !job.prefs && isAiJob(job)) { const pf = BEHAVIOR.compact(c); if (pf) job.prefs = pf; } // v3.1: what this person usually works on, when and how (AI work only)
  jobs.unshift(job); trimJobs(jobs); store.set('jobs', jobs);
  return job;
}

function createTenantAndUser(p, app, extra = {}) {
  const email = String(p.email || '').trim().toLowerCase(); const phone = latinDigits(p.phone || '').replace(/[^\d+]/g, '');
  if (!/^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/.test(email)) fail('validation', { email: 'email' });
  if (users().some(u => u.app === app && u.email === email)) fail('exists', { email: 'exists' });
  const T = { id: uid('t'), app, audience: audienceOf(app), name: String(p.company || p.office_name || p.name || '').slice(0, 120), plan: p.plan || '', country: acceptCountry(p.country), city: p.city || '', status: 'trial', created: nowIso(), account_type: p.account_type || '', attribution: p.ref || '', category: p.category || '', partner_kind: p.partner_type || '', demo: !!extra.demo, ...extra.tenant };
  const plan = rowsOf('platform', 'plans').find(x => x.code === T.plan && x.audience === T.audience);
  T.trial_end = new Date(Date.now() + (plan?.trial_days ?? 14) * DAY).toISOString();
  if (app === 'partner') { T.status = 'active'; delete T.trial_end; } // v3.33: a partner has no plan, so no trial
  if (app === 'partner') { const pre = String(p.name || 'P').replace(/[^A-Za-z]/g, '').slice(0, 3).toUpperCase() || 'DAR'; const taken = new Set([...tenants().filter(x => x.app === 'partner').map(x => String(x.code || '').toUpperCase()), ...rowsOf('platform', 'coupons').map(x => String(x.partner_code || '').toUpperCase())]); let code = ''; do { code = pre + Math.floor(100000 + Math.random() * 900000); } while (taken.has(code)); T.code = code; T.tier = 'partner'; } // (v3.22: a code is one partner's alone — it was 3 letters and 4 digits, and two partners could share one; the server checks it again)
  return { T, email, phone };
}

// ================================================================= v3.5–3.8: the assistant that understands (assets/assist.js, assets/mind.js)
// On a host with the platform's own AI (dar-ai.php; assets/sync.js sets LLM.ask), every assistant asks it with the
// account's own records (the developer: the platform's settings), its memory and the conversation so far (dar-mind.php,
// LLM.mind), looks things up, checks and corrects its own operations, and gets words and a plan back. Each step runs as
// the same operation a click would (permissions, plan limits, validation, audit and undo unchanged); small safe changes for
// the person himself may run at once with Undo; the rest waits for him. v3.8: no rule-made answers and no ready requests —
// when no AI provider answers, the request is kept and asked again by itself. Example accounts ask through the public door
// (LLM.demo: the free providers only).
export const LLM = { ask: null, n8n: null, code: null, bridge: null, flow: null, node: null, mind: null, demo: null, status: null, outcome: null, media: null }; // (v3.19: media — a picture, a voice, a song made on the server)
const lblOf = x => { if (x == null) return ''; if (Array.isArray(x)) return L(x); const s = String(x); return s.startsWith('u:') ? t(s.slice(2)) : s.startsWith('o:') ? optLabel(s.slice(2)) : s.startsWith('c:') ? collLabel(s.slice(2)) : s.startsWith('f:') ? fieldLabel(s.slice(2)) : s; };
const svcText = s => [...(s.n || []), ...(s.d || [])].join(' ') + ' ' + s.id.replace(/_/g, ' ');
const svcActs = s => [...(s.a || []), ...(s.c || []), ...(s.xa || []).map(x => x.id)].slice(0, 8);
// v3.8: an account's assistant (Dar Mind): who it works for, what the person may read and change, today at a glance, the
// records the message is about, the collections with their fields (so it can look up and count exactly), the screens
const MIND_ROUNDS = { tenant: 4, dev: 8, open: 3 };
const rowName = r => clip(r?.name || r?.title || r?.name_ar || r?.office_name || r?.unit_no || r?.number || r?.employee || r?.id || '', 60);
// v3.16: the everyday words that point to a collection whose name does not contain them («موعد» → appointments: «المواعيد» is a
// broken plural) — so the fields of what the request is about are in the prompt; any other collection is one look-up away
const COLL_HINTS = {
  appointments: 'موعد مواعيد معاينه معاينات زياره اجتماع appointment meeting viewing visit rendez-vous rdv visite réunion',
  tasks: 'مهمه مهام ذكرني تذكير متابعه task todo reminder follow-up tâche rappel', deals: 'صفقه صفقات بيع deal sale affaire vente',
  invoices: 'فاتوره فواتير invoice bill facture', contracts: 'عقد عقود contract contrat', expenses: 'مصروف مصاريف expense cost dépense',
  leads: 'عميل عملاء زبون مشتري client lead buyer prospect acheteur', properties: 'عقار عقارات فيلا شقه ارض عماره محل property villa apartment flat land building bien appartement terrain',
  maintenance: 'صيانه عطل اصلاح maintenance repair réparation panne', documents: 'مستند مستندات وثيقه ملف document file', owners: 'مالك ملاك owner landlord propriétaire',
  leases: 'ايجار تاجير lease rent bail loyer', tenants: 'مستاجر مستاجرين tenant locataire'
};
function tenantBrief(c, text, lang, mem, tier, { demo = false, voice = false, aware = '', know = '' } = {}) {
  const P = getP(); const ax = accessCtx(c); const words = wordsOf(text); const T = c.tenant || {};
  const now = nowContext(T.tz || tzOf(T.country)); const today = now.date; const deep = tier === 'deep';
  const mine = catalog(P).filter(s => s.app === c.app && access(s, ax) === 'ok' && roleAllows(c.app, c.user.role, s, P));
  const colls = [...new Set(mine.flatMap(s => s.e || []))].filter(x => entSpec(x) && !isPlatformColl(x));
  const byColl = {}; const counts = {};
  for (const coll of colls) { try { const r = OPS['data.list']({ coll, limit: 2000 }, c); counts[coll] = r.total; if (ASSIST_COLLS.includes(coll) || coll.startsWith('x_')) byColl[coll] = r.rows; } catch { /* this person may not read it */ } }
  const readable = Object.keys(counts); const at = {};
  if (byColl.appointments) { const list = byColl.appointments.filter(a => String(a.start || '').slice(0, 10) === today && a.status !== 'cancelled').sort((a, b) => String(a.start).localeCompare(String(b.start))); at.appointments_today = list.slice(0, 8).map(a => ({ id: a.id, time: String(a.start).slice(11, 16), title: clip(a.title, 60), status: a.status || 'scheduled' })); if (list.length > 8) at.appointments_today_more = list.length - 8; }
  if (byColl.tasks) { const open = byColl.tasks.filter(x => x.status !== 'done'); at.tasks_overdue = open.filter(x => x.due && String(x.due).slice(0, 10) < today).length; const due = open.filter(x => String(x.due || '').slice(0, 10) === today); if (due.length) at.tasks_due_today = due.slice(0, 6).map(x => ({ id: x.id, title: clip(x.title, 60), time: String(x.due).slice(11, 16) })); }
  if (byColl.leads) { at.new_clients_last_7_days = byColl.leads.filter(l => Date.now() - Date.parse(l.created || 0) < 7 * DAY).length; at.clients_not_contacted_yet = byColl.leads.filter(l => (l.status || 'new') === 'new').length; }
  if (byColl.deals) at.deals_open = byColl.deals.filter(d => !['closed', 'after_sale'].includes(d.stage)).length;
  if (byColl.properties) at.properties_available = byColl.properties.filter(x => (x.status || 'available') === 'available').length;
  const prio = [...ASSIST_COLLS.filter(x => readable.includes(x)), ...readable.filter(x => x.startsWith('x_')), ...readable.filter(x => !ASSIST_COLLS.includes(x) && !x.startsWith('x_'))];
  const shown = prio.slice(0, deep ? 22 : 16);
  const writable = shown.filter(coll => { if (R.SYSTEM_OWNED.includes(coll)) return false; try { guardCollection(c, coll, true); return true; } catch { return false; } });
  const scored = mine.map(s => [s, scoreText(svcText(s), words)]).sort((a, b) => b[1] - a[1]);
  const services = [...scored.filter(x => x[1] > 0).slice(0, deep ? 12 : 8), ...scored.filter(x => x[1] === 0).slice(0, deep ? 6 : 4)].map(([s, n]) => ({ id: s.id, name: L(s.n), ...(n > 0 ? { acts: svcActs(s) } : {}) }));
  // v3.16 — a lighter prompt (it reaches more models, faster, and they read it better): the records the request is about, the
  // fields of the collections it is about (any other collection's fields are one look-up away), the counts that are not zero
  const records = relevantRecords(byColl, text, deep ? 16 : 8); const inRecs = new Set(records.map(r => r.coll));
  const collScore = coll => scoreText(coll.replace(/_/g, ' ') + ' ' + collLabel(coll) + ' ' + (R.COLL?.[coll] || []).join(' ') + ' ' + (COLL_HINTS[coll] || ''), words);
  const focus = [...shown.filter(x => inRecs.has(x) || collScore(x) > 0), ...shown.filter(x => ['leads', 'properties', 'projects', 'units', 'p_leads', 'pr_jobs'].includes(x) && (counts[x] || 0) > 0), ...shown.filter(x => (counts[x] || 0) > 0)].filter((x, i, a) => a.indexOf(x) === i).slice(0, deep ? 10 : 6);
  const nonzero = Object.fromEntries(Object.entries(counts).filter(([, n]) => n > 0));
  const country = countryBy(T.country, rowsOf('platform', 'countries'), P); const kind = demo ? 'open' : 'tenant';
  const acct = demo ? cleanAssist(null) : acctAssist(T.id); // v3.13.1: the account owner's limits and standing orders
  // v3.13.1: what its screens do that this person may do — its settings, its team, messages to clients, links, approvals
  const role = c.user.role || ''; const mgr = MANAGER_ROLE.includes(role);
  const contactColls = readable.filter(coll => (fieldsOf(coll) || []).some(f => f.type === 'phone' || f.type === 'email'));
  const can = { website: !demo && mgr && readable.includes('site_pages'), setDocs: /إعداد|اعداد|ملف|بيانات المكتب|حجز|الحجز|مواعيد|ساعات|دوام|إجاز|اجاز|حوض|سياسة|سياسه|صفحة المكتب|صفحه المكتب|موقع|الموقع|\b(?:setting|settings|profile|booking|hours|leave|pond|policy|page|website|site)\b/i.test(text), create: writable, delete: writable.length > 0, clock: readable.includes('hr_attendance'), settings: demo ? [] : ACCT_SET_KEYS.filter(k => (k === 'hr_policy' ? [...MANAGER_ROLE, 'hr'] : MANAGER_ROLE).includes(role)), profileFields: ACCT_SETTINGS.profile.fields(c).map(f => f.key), team: !demo && mgr ? teamRoles(c.app) : [], message: !demo && CFG.mode === 'hosted' ? contactColls : [], conversations: readable.includes('conversations') && !demo && CFG.mode === 'hosted', link: demo ? [] : Object.keys(LINK_WHAT).filter(w => w === 'portal' ? readable.includes('owners') || readable.includes('tenants') : readable.includes(LINK_WHAT[w])), approve: !demo };
  const domain = tenantDomain({ app: c.app, office: { name: T.name || '', city: T.city || '', country: T.country || '', currency: country.currency || 'SAR' }, counts: nonzero, today: at, records, schema: focus.map(coll => fieldDoc(coll, fieldsOf(coll), 16)).join('; '), others: [...shown.filter(x => !focus.includes(x)), ...prio.slice(shown.length, shown.length + 30)], services, can, assist: acct, owner: role === 'owner', limits: demo ? null : acctAutonomy(T.id), confirm: acct.confirm, aware, know });
  const frame = framePrompt({ kind: 'tenant', lang, now, voice, person: { name: c.user.name || '', role: c.user.role || '' }, mem, summary: mem?.context?.summary || '', rounds: MIND_ROUNDS[kind], autorun: !demo && !c.imp && mem?.prefs?.autorun !== false && acct.confirm !== 'all', confirm: acct.confirm, remember: !demo && !!LLM.mind, tools: ['- {"do":"fields","coll":"<collection>"} — the fields of a collection whose fields are not detailed above (before creating or filtering by them).', '- {"do":"howto","q":"<what he wants to do>"} — the screens of Dar that do it, what each one does and its tools (to explain how, or to open or run the right one; a screen his plan lacks says so).', '- {"do":"now","section":"<collection>|today|moves|messages|pages|team|plan|channels"} — one part of THE ACCOUNT NOW in full (its records, its movements, who did what).', '- To point to a record created by an earlier step of the same answer, write "$<step number>" (e.g. "lead":"$1" for the client created by step 1).'].join('\n') });
  // v3.8: the console's assistant knows Dar's API exactly (the developer building on Dar asks how to call it)
  const api = c.app === 'console' ? apiReference(CFG.mode === 'hosted' && typeof location !== 'undefined' ? new URL((CFG.root || './') + ((SOLO || SHOW) ? 'api/v1' : 'dar-sync.php?api=v1'), location.href).href : '') : '';
  return { sys: domain + (api ? '\n' + api : '') + '\n' + frame, opts: { dev: false, colls: readable, services: mine.map(s => s.id) }, rounds: MIND_ROUNDS[kind] };
}
// the settings a developer's message is about (their current value goes into the request)
const DEV_TOPIC = { theme: /لون|الوان|ألوان|ثيم|هويه|هوية|شعار|colou?r|theme|brand|logo|couleur/i, landing: /الصفحه الرئيسيه|الصفحة الرئيسية|الموقع الرئيسي|واجهه الموقع|واجهة الموقع|hero|landing|headline|accueil/i, maintenance: /صيانه|صيانة|maintenance/i, partner: /شريك|شركاء|عموله|عمولة|partner|commission/i, world: /دول العالم|كل الدول|باقي الدول|world|international/i, price_display: /ضريب|شامل|tax|vat|tva|ttc/i, base_currency: /عمله|عملة|عملات|currenc|devise/i, fx: /صرف|exchange rate|taux de change/i, security: /امان|أمان|كلمه المرور|كلمة المرور|جلس|password|session|security|sécurité/i, captcha: /captcha|كابتشا|روبوت/i, wa: /واتس|whatsapp/i, schedules: /جدوله|جدولة|schedule|planif/i, autonomy: /استقلال|موافقه|موافقة|autonomy|approval/i, links: /روابط|رابط|نطاق فرعي|subdomain|lien/i, domain: /نطاق|دومين|domain|domaine/i, demo_mode: /تجريبي|المثال|demo|exemple|example/i, max_photos: /عدد الصور|photos/i, upload_max_mb: /حجم الملف|حجم الرفع|upload/i, onboarding: /اسئله البدايه|أسئلة البداية|onboarding/i, default_country: /الدوله الافتراضيه|الدولة الافتراضية|default country|pays par défaut/i, ai: /الموظفين الاذكياء|الموظفين الأذكياء|ai roles/i };
function devTexts(text) {
  const quoted = [...String(text).matchAll(/[«"“]([^»"”]{2,80})[»"”]/g)].map(m => fold(m[1].trim()));
  if (!quoted.length && !/(?:^|[\s،,.؟?!«(])(?:و?(?:ال)?(?:نص|نصوص|كلمه|كلمة|كلمات|عباره|عبارة|عبارات|عنوان|عناوين|زر|أزرار|ازرار|تسميه|تسمية|مكتوب|صياغه|صياغة))(?=$|[\s،,.؟?!»)])|\b(?:text|texts|label|labels|button|buttons|wording|libell\w*|bouton\w*|texte\w*)\b/i.test(text)) return []; // (v3.12: whole words — «المنصة» holds «نص» and is not about texts)
  const words = wordsOf(text); const hits = [];
  for (const [k, v] of Object.entries(UI)) {
    if (!Array.isArray(v)) continue; const o = TEXTS[k]; const cur = [0, 1, 2].map(i => (o && o[i]) || v[i] || '');
    const hay = fold(cur.join(' | ')); const s = quoted.length ? quoted.reduce((n, q) => n + (hay.includes(q) ? 10 : 0), 0) : scoreText(hay, words);
    if (s >= (quoted.length ? 10 : 4)) hits.push([s, k, cur]);
  }
  return hits.sort((a, b) => b[0] - a[0]).slice(0, 8).map(([, k, cur]) => ({ key: k, text: cur.map(x => clip(x, 110)) }));
}
// v3.33 (the owner, 2026-10-22 — note 5: «يقوم بالطلب مني أسماء ملفات وروابط ولا يعرف أين وكيف ينفذ»): where a thing he names or
// sees lives — the settings he means (platmap.js), the screens of his panel, the services, the interface texts showing those words
// (his own wording first) — so the assistant changes it the plain way instead of asking him for a file. An account's assistant is
// given its own screens only.
// (words that say what to DO or name the site in general — they find nothing by themselves)
const WHERE_STOP = new Set(['موقع', 'الموقع', 'صفحه', 'الصفحه', 'منصه', 'المنصه', 'دار', 'قسم', 'القسم', 'خانه', 'الخانه', 'خدمه', 'الخدمه', 'خدمات', 'الخدمات', 'غير', 'غيّر', 'عدل', 'تعديل', 'اجعل', 'ضع', 'اضف', 'احذف', 'اظهر', 'اخف', 'اخفي', 'ابي', 'ابغى', 'اريد', 'نريد', 'لو', 'سمحت', 'الان', 'change', 'edit', 'page', 'site', 'website', 'section', 'make', 'set', 'show', 'hide', 'please', 'want', 'service', 'services', 'changer', 'modifier', 'site', 'service']);
// v3.33.5 (live, 2026-10-23: asked to change one sentence, the owner's assistant saved a «legal» row holding only that clause — which
// would have replaced the whole terms for Saudi readers): a row of the legal texts is a WHOLE document, so one far shorter than the
// text it replaces is refused, with the way to change some words (P.legal_edits)
function legalWhole(row) {
  if (!row || typeof row !== 'object') return; const doc = String(row.doc || ''); if (!doc.trim()) return;
  const kind = Object.entries(LEGAL_DOC_KIND).find(([, v]) => v === row.doc_type)?.[0]; if (!kind) return;
  const full = legalPlain(kind, { ar: 0, en: 1, fr: 2 }[row.lang || 'ar'] ?? 0); if (full && doc.length < full.length * 0.4) fail('legal_excerpt', { have: doc.length, whole: full.length });
}
// v3.33.5: one sentence of a legal text changed (P.legal_edits) — its document, its language, the exact words shown and the new ones
const LEGAL_EDIT_DOCS = ['terms', 'usage', 'privacy', 'refund', 'partners'];
// (the names the legal texts' rows use — refund_policy, partner_terms — and the plain words, for the same pages)
export const LEGAL_DOC_ALIAS = { refund_policy: 'refund', refunds: 'refund', partner_terms: 'partners', partner: 'partners', policy: 'usage', acceptable_use: 'usage', terms_and_conditions: 'terms' };
export function legalEditOf(v) {
  if (!v || typeof v !== 'object') return null; const doc = LEGAL_DOC_ALIAS[String(v.doc || '')] || String(v.doc || ''), lang = String(v.lang || 'ar'), old = String(v.old ?? ''), nw = String(v.new ?? '');
  if (!LEGAL_EDIT_DOCS.includes(doc) || !['ar', 'en', 'fr'].includes(lang) || old.trim().length < 3 || old.length > 1500 || nw.length > 3000) return null; // (new = old: the change of those words taken back)
  return { doc, lang, old, new: nw, ...(typeof v.at === 'string' && v.at ? { at: v.at.slice(0, 30) } : {}) };
}
export const legalEditsOf = P => (Array.isArray(P?.legal_edits) ? P.legal_edits : []).map(legalEditOf).filter(Boolean).slice(-200);
export function whereIs(q, c) {
  const P = getP(); const words = new Set([...wordsOf(q)].filter(w => !WHERE_STOP.has(w))); const dev = c?.user?.app === 'developer'; const fq = fold(String(q || '').trim()); const found = [];
  // (v3.33.15: a setting whose words cover everything he asked — «صفحة الصيانة» is the maintenance setting — comes before a text that merely
  // quotes those words, such as the notice shown to the platform's team while the site is closed)
  if (dev) for (const h of WHERE_HINTS) { const hay = fold(h.w + ' ' + h.what); const s = scoreText(hay, words); const all = words.size > 0 && [...words].every(w => hay.includes(w)); if (s > 0) found.push([s + 3 + (all ? 10 : 0), { kind: 'setting', what: h.what, how: h.how, ...(h.screen ? { screen: h.screen } : {}) }]); }
  for (const s of catalog(P)) {
    if (!dev && (s.app !== c?.app || s.status === 'hidden' || !roleAllows(c.app, c.user?.role, s, P))) continue;
    const sc = scoreText(svcText(s), words) + (String(q).includes(s.id) ? 10 : 0); if (sc <= 0) continue;
    found.push([sc, s.app === 'developer' ? { kind: 'screen', id: s.id, name: L(s.n), holds: clip(L(s.d), 120), how: '{"do":"open","service":"' + s.id + '"}' }
      : { kind: 'service', id: s.id, app: s.app, name: L(s.n), status: s.status || 'active', how: dev ? 'services.' + s.id + '.status | .plans | .countries' : '{"do":"open","service":"' + s.id + '"}' }]);
  }
  if (dev) for (const [k, v] of Object.entries(UI)) {
    if (!Array.isArray(v)) continue; const o = TEXTS[k]; const cur = [0, 1, 2].map(i => (o && o[i]) || v[i] || ''); const hay = fold(cur.join(' | '));
    const s = fq.length >= 3 && hay.includes(fq) ? 12 : scoreText(hay, words); if (s >= 4) found.push([s, { kind: 'text', key: k, text: cur.map(x => clip(x, 110)), how: '{"do":"set","path":"texts.' + k + '","value":["<Arabic>","<English>","<French>"]}' }]);
  }
  return found.sort((a, b) => b[0] - a[0]).slice(0, 12).map(x => x[1]);
}
// v3.12: what a developer's message is about — the manuals and the data his prompt carries (any other manual is one look-up away)
const DEV_TOPICS = {
  code: /كود|برمج|برنامج|ملف|ملفات|صفح|شاش|واجه|زر|ازرار|أزرار|حقل|حقول|تصميم|ستايل|عطل|خلل|إصلاح|اصلاح|أصلح|اصلح|ميزة|ميزه|خاصية|خاصيه|لا يعمل|ما يعمل|ما يشتغل|مايشتغل|ما تشتغل|يظهر|تظهر|ما يظهر|خطأ|اخطاء|أخطاء|\b(?:code|file|files|page|screen|button|field|style|css|html|js|javascript|php|bug|fix|feature|broken|error|errors|crash|ui|ux|layout)\b/i,
  flow: /اتمته|أتمتة|اتمتة|اتمتات|أتمتات|تلقائي|آلي|آليا|كل ما|كلما|عندما|سير العمل|سير عمل|ورك ?فلو|تريجر|مشغل|جدوله|جدولة|\b(?:automati\w*|workflow\w*|trigger\w*|schedule\w*|whenever|webhook\w*)\b/i,
  node: /عقده|عقدة|عقد|تكامل|تكاملات|ربط خدمة|خدمة خارجية|منصة خارجية|\b(?:node|nodes|integration\w*|api|connector\w*)\b/i,
  channel: /واتس|وتساب|انستجرام|إنستجرام|انستقرام|إنستقرام|انستا|رسال|ارسل|أرسل|إرسال|ارسال|بريد|ايميل|إيميل|قناة|قنوات|تواصل|اتحدث معك|أتحدث معك|أكلمك|اكلمك|اراسلك|أراسلك|\b(?:whatsapp|instagram|insta|sms|e-?mail|mail|channel\w*|send|message\w*|talk to you)\b/i,
  ai: /ذكاء|نموذج|نماذج|مزود|مزوّد|مزودين|بطيء|بطء|بطيئ|سرعه|سرعة|يتأخر|تأخر|متأخر|يرد|الرد|تجاوب|\b(?:ai|model\w*|provider\w*|groq|gemini|openrouter|cerebras|mistral|llm|slow|speed|latency)\b/i,
  service: /خدمه جديده|خدمة جديدة|خدمات جديدة|وحده جديده|وحدة جديدة|قسم جديد|\b(?:new service|module)\b/i,
  n8n: /\bn8n\b/i, bridge: /جسر|\bbridge\b/i,
  plans: /باق|باقات|خطة|خطط|اشتراك|اشتراكات|سعر|أسعار|اسعار|تسعير|\b(?:plan|plans|price\w*|subscription\w*|pricing|tier\w*)\b/i,
  countries: /دول|دولة|دوله|بلد|بلاد|\b(?:country|countries|pays|region\w*)\b/i,
  gateways: /دفع|بوابة|بوابات|مدفوعات|\b(?:gateway\w*|payment\w*|moyasar|tap|stripe|paypal|hyperpay|paytabs)\b/i,
  // v3.18.4: the requirements and keys («الربط والمفاتيح»)
  req: /مفتاح|مفاتيح|المفاتيح|ربط|الربط|اربط|متطلب|متطلبات|ناقص|النواقص|تفعيل|فعّ?ل|تفعل|تتفعل|مفعل|احمر|أحمر|الحمراء|توكن|سر |كلمة المرور|كابتشا|تنبيه|تنبيهات|نسخ احتياطي|النسخة الخارجية|\b(?:keys?|tokens?|secrets?|link\w*|requirements?|missing|activat\w*|turnstile|captcha|uptime\w*|r2|backup\w*|healthchecks|ntfy|discord|slack|browserless|pagespeed|clarity|smtp|infobip|telegram|oauth|webhook\w*)\b/i,
};
export function devTopics(text, ctx = '') {
  const s = String(text || ''); const out = Object.keys(DEV_TOPICS).filter(k => DEV_TOPICS[k].test(s));
  if (ctx === 'automation' && !out.includes('flow')) out.push('flow');
  if (out.includes('flow') && !out.includes('node')) out.push('node'); // (a workflow may need an integration)
  return out;
}
const tenantRow = T => { const o = ownerOf(T); return { id: T.id, app: T.app, name: T.name || '', plan: T.plan || '', status: T.status || '', country: T.country || '', ...(o ? { owner: o } : {}) }; };
// v3.33.24 (the owner, 2026-10-24: «أعطني رقم العميل swetkw5@gmail.com» — nothing found: the e-mail and phone are its owner's): an account
// is found by its owner's e-mail, name or phone too, and its row carries them
const ownerOf = T => { const u = users().find(x => x.tenant === T.id && x.role === 'owner') || users().find(x => x.tenant === T.id); return u ? { name: u.name || '', email: u.email || '', phone: u.phone || '' } : null; };
const digitsOf = s => latinDigits(String(s || '')).replace(/\D/g, '');
function findTenants(q) {
  const w = wordsOf(q); const ql = String(q || '').trim().toLowerCase(); const qd = digitsOf(q);
  // (anyone of the account — its owner or one of its people — by e-mail or phone)
  const person = T => users().find(u => u.tenant === T.id && ((ql && String(u.email || '').toLowerCase() === ql) || (qd.length >= 7 && digitsOf(u.phone).endsWith(qd.slice(-9)))));
  return tenants().filter(T => T.status !== 'deleted').map(T => { const o = ownerOf(T); const p = person(T); return [T, scoreText([T.name, T.city, T.code, T.id, T.country, T.plan, o?.name, o?.email, o?.phone].join(' '), w) + (String(q).includes(T.id) ? 10 : 0) + (p ? 20 : 0), p]; })
    .filter(x => x[1] > 0).sort((a, b) => b[1] - a[1]).slice(0, 10).map(([T, , p]) => ({ ...tenantRow(T), ...(p ? { person_found: { name: p.name || '', email: p.email || '', phone: p.phone || '', role: p.role || '' } } : {}) }));
}
// v3.6: what the AI needs of the bridge's state (never its secret or its address's path parts beyond the host)
function bridgeBrief(st) {
  if (!st || typeof st !== 'object') return null; const last = st.last || {}; const use = st.use || {};
  let host = ''; try { host = st.url ? new URL(st.url).host : ''; } catch { host = ''; }
  return { linked: !!(st.has_key && st.url), n8n_host: host, on: !!st.on, paused: !!st.paused, test_mode: !!st.test, ai_fallback: !!st.ai, ready: !!st.ready, n8n_mode: last.mode || '',
    last_call: last.at ? { at: last.at, ok: !!last.ok, why: last.why || '', http: last.http ?? null } : null, counts_24h: st.counts || {}, oldest_waiting_min: st.oldest_waiting_min || 0,
    month: { allowed: use.allowed ?? st.budget ?? null, used: use.calls ?? null, ai: use.ai ?? null, left_today: use.day_left ?? null }, monthly_budget: st.budget ?? null, can_link_itself: !!st.n8n_api };
}
// v3.7: the automation engine as the AI sees it (never a webhook key, never a secret)
let FLOWN = {}; // workflow id → name, for the steps' labels
const flowTrig = tr => { if (!tr || typeof tr !== 'object') return null; const o = { type: tr.type, scope: tr.scope || 'all' }; for (const k of ['event', 'coll', 'kind', 'every', 'at', 'field', 'value', 'verify', 'node', 'op']) if (tr[k] != null && tr[k] !== '') o[k] = tr[k]; return o; };
const NODEN = {}; const DEVK = {}; // v3.7: names of library nodes and the kind of each proposal, for the steps shown to the person
const flowBrief = f => { FLOWN[f.id] = f.name; return { id: f.id, name: clip(f.name, 60), active: !!f.active, trigger: flowTrig(f.trigger), runs_24h: f.runs_24h || 0, fails_24h: f.fails_24h || 0, last: f.last_status || '' }; };
// v3.18.4: the requirements' short summary (req.brief) — read for each message, kept 30 seconds; a step that changed one reads it again
const RQB = { at: 0, v: null, p: null };
// (v3.33 — notes 15/35, «الرد لا يتجاوز ثانيتين»: one request in flight is shared — the turn warms it while it reads its memory,
// and the brief that needs it a moment later waits for the same answer instead of asking again)
async function reqBrief() { if (RQB.v && Date.now() - RQB.at < 30000) return RQB.v; if (RQB.p) return RQB.p; RQB.p = api.call('req.brief', {}).then(r => { RQB.v = r; RQB.at = Date.now(); return r; }).finally(() => { RQB.p = null; }); return RQB.p; }
export const reqBriefReset = () => { RQB.at = 0; };
// v3.18.4: every section of his panel as it is now (dar-now.php) — read for each message of the owner, kept 30 seconds; after a
// step changed something, read again fresh («يجب ان يطلع على كل شيء بلا استثناء»)
const NOWB = { at: 0, v: null, fresh: false, p: null };
// v3.20 — «مكتبة المعرفة» (dar-know.php): the library's parts that match a message — the owner's (his Drive and documents) for his
// assistant, an account's own for its assistants. Only on the server (an example account has none); a library that cannot be read
// for this message simply does not ride with it (the assistant can still look it up)
const KNB = new Map(); // (v3.33: the same question's library parts, asked once — warmed while the memory is read)
async function knowBrief(c, text, compact = false) {
  if (CFG.mode !== 'hosted' || c?.tenant?.demo || c?.user?.demo) return '';
  if (c?.user?.app === 'developer' && c.user.role !== 'owner') return '';
  const key = (c?.tenant?.id || 'dev') + '|' + (compact ? 1 : 0) + '|' + String(text || '').slice(0, 2000); const hit = KNB.get(key);
  if (hit && Date.now() - hit.at < 20000) return hit.p;
  const pr = api.call('know.brief', { q: String(text || '').slice(0, 2000), ...(compact ? { max: 1300 } : {}) }).then(r => r?.text || '', () => '');
  KNB.set(key, { at: Date.now(), p: pr }); if (KNB.size > 20) KNB.delete(KNB.keys().next().value); return pr;
}
async function nowBrief(fresh = false) { if (!fresh && !NOWB.fresh && NOWB.v && Date.now() - NOWB.at < 30000) return NOWB.v; const fr = fresh || NOWB.fresh; if (!fr && NOWB.p) return NOWB.p; const pr = api.call('now', fr ? { fresh: true } : {}).then(r => { NOWB.v = r; NOWB.at = Date.now(); NOWB.fresh = false; return r; }).finally(() => { if (NOWB.p === pr) NOWB.p = null; }); if (!fr) NOWB.p = pr; return pr; }
export const nowReset = () => { NOWB.fresh = true; RQB.at = 0; AWB.clear(); };
// v3.20 — «الحساب الآن»: an account's whole state and every movement in it, for its AI (dar-aware.php on the host: its needs, its
// day, who did what, what arrived by itself, its messages, pages, channels, team and plan); read here from this browser's own
// records where there is no host (the static site, an example account). Kept 30 seconds; a step that changed something reads it
// again. («المشترك كمكتب عقاري منظومة الذكاء الاصطناعي التي في واجهته تكون مطلعه على كل شيء وكل حركة وتحرك»)
const AWB = new Map();
const NEED_EN = { unfollowed: 'clients not contacted yet, waiting over a day', upcoming_appts: 'appointments in the next 2 days', stalled_deals: 'open deals with no movement for 14+ days', overdue_inv: 'invoices past due', expiring_leases: 'leases ending within 30 days', stale_props: 'listings available for 45+ days', missing_license: 'available listings without an advertising licence', leaves_pending: 'leave requests waiting', obligations_soon: 'obligations due within 14 days', staff_expiring: 'staff IDs or contracts expiring within 30 days', sign_waiting: 'documents waiting for a signature', late_installments: 'buyers\' instalments late', due_installments: 'instalments due soon', pending_reservations: 'reservations waiting for confirmation', handovers_soon: 'handovers soon', delayed_stages: 'construction stages behind plan', permits_expiring: 'permits expiring', warranty_late: 'warranty requests late', eoi_waiting: 'expressions of interest waiting' };
const agoEn = v => { const d = (Date.now() - Date.parse(v || 0)) / 1000; if (!isFinite(d)) return ''; return d < 90 ? 'just now' : d < 5400 ? Math.round(d / 60) + ' min ago' : d < 129600 ? Math.round(d / 3600) + ' h ago' : Math.round(d / 86400) + ' days ago'; };
function awareLocal(c, lite = false) {
  const P = getP(); const ax = accessCtx(c); const T = c.tenant || {}; const ctx = computeCtx(c, {});
  const mine = catalog(P).filter(s => s.app === c.app && access(s, ax) === 'ok' && roleAllows(c.app, c.user.role, s, P));
  const colls = [...new Set(mine.flatMap(s => s.e || []))].filter(x => entSpec(x) && !isPlatformColl(x)); const sec = []; const empty = [];
  for (const coll of colls) {
    let rows; try { rows = OPS['data.list']({ coll, limit: 5000 }, c).rows; } catch { continue; }
    if (!rows.length) { empty.push(coll); continue; }
    const sf = (fieldsOf(coll) || []).find(f => ['status', 'stage', 'outcome'].includes(f.key) && f.type === 'sel')?.key; const by = {};
    if (sf) for (const r of rows) { const k = r[sf] || '—'; by[k] = (by[k] || 0) + 1; }
    const new7 = rows.filter(r => Date.now() - Date.parse(r.created || 0) < 7 * DAY).length;
    sec.push(`${coll} ${rows.length}${sf ? ' [' + Object.entries(by).sort((a, b) => b[1] - a[1]).slice(0, lite ? 3 : 6).map(([k, n]) => k + ' ' + n).join(', ') + ']' : ''}${new7 ? ', +' + new7 + ' this week' : ''}`);
  }
  let needs = []; try { needs = (todayInsight(ctx).sections || []).map(s => `- [${s.coll}] ${s.total} ${NEED_EN[s.key] || s.key.replace(/_/g, ' ')}${s.rows?.length ? ' (' + s.rows.slice(0, lite ? 2 : 4).map(r => '«' + clip(String(r.title ?? ''), 40) + '»').join(', ') + ')' : ''}`); } catch { needs = []; }
  const log = ctx.audit().filter(a => !a.coll || colls.includes(a.coll)).slice(0, lite ? 4 : 10).map(a => `- ${agoEn(a.at)} — ${a.who || 'someone'}: ${a.op}${a.coll ? ' ' + a.coll : ''}${a.after && typeof a.after === 'object' && (a.after.name || a.after.title) ? ' «' + clip(String(a.after.name || a.after.title), 40) + '»' : ''}`);
  return [`THE ACCOUNT NOW — «${clip(T.name || '', 60)}»${T.city ? ' in ' + T.city : ''}; read from its records just now. Every figure below is real; for any part in full: {"do":"now","section":"<collection>|today|moves"}.`,
    needs.length ? 'NEEDS ATTENTION FIRST:\n' + needs.slice(0, lite ? 6 : 14).join('\n') : 'NEEDS ATTENTION FIRST: nothing found — the account is up to date.',
    log.length ? 'LATEST MOVES:\n' + log.join('\n') : 'LATEST MOVES: none yet.', 'SECTIONS (records it holds): ' + (sec.length ? sec.join(' · ') : 'nothing entered yet') + '.', !lite && empty.length ? 'NOT USED YET: ' + empty.slice(0, 30).join(', ') + '.' : ''].filter(Boolean).join('\n');
}
// the same parts in full where there is no host (an example account, the static site)
function awareLocalDetail(c, section) {
  const ctx = computeCtx(c, {}); const P = getP(); const ax = accessCtx(c);
  const colls = [...new Set(catalog(P).filter(s => s.app === c.app && access(s, ax) === 'ok' && roleAllows(c.app, c.user.role, s, P)).flatMap(s => s.e || []))].filter(x => entSpec(x) && !isPlatformColl(x));
  if (section === 'today') { const ti = todayInsight(ctx); return { section, needs: (ti.sections || []).map(s => ({ coll: s.coll, what: NEED_EN[s.key] || s.key, total: s.total, items: (s.rows || []).map(r => r.title) })), setup: ti.steps }; }
  if (section === 'moves') return { section, log: ctx.audit().filter(a => !a.coll || colls.includes(a.coll)).slice(0, 80).map(a => ({ at: a.at, who: a.who, op: a.op, coll: a.coll || '', path: a.path || '', after: a.after || null })) };
  if (colls.includes(section)) { const rows = OPS['data.list']({ coll: section, limit: 5000 }, c).rows; return { section, total: rows.length, latest: rows.slice(0, 25).map(r => compactRow(section, r)), moves: ctx.audit().filter(a => a.coll === section).slice(0, 40) }; }
  fail('not_found', { section, known: ['today', 'moves', ...colls] });
}
async function awareBrief(c, { lite = false } = {}) {
  if (!c?.tenant || !c.user) return '';
  const key = c.tenant.id + ':' + c.user.id + ':' + (lite ? 1 : 0); const hit = AWB.get(key);
  if (hit && Date.now() - hit.at < 30000) return hit.p; // (v3.33: an answer still on its way is shared too)
  const pr = (async () => {
    let text = '';
    if (CFG.mode === 'hosted' && !c.tenant.demo && !c.user.demo) { try { text = String((await api.call('aware.now', lite ? { lite: true } : {}))?.text || ''); } catch { text = ''; } }
    if (!text) { try { text = awareLocal(c, lite); } catch { text = ''; } }
    return text;
  })();
  AWB.set(key, { at: Date.now(), p: pr }); return pr;
}
export { awareBrief };
export { findTenants }; // (v3.33.24: tests/plain3324.mjs — an account found by its owner's e-mail or phone)
const reqEmpty = it => (it.fields || []).filter(f => f.m).filter(f => { const v = it.values?.[f.k] || {}; return 'set' in v ? !v.set : v.v == null || v.v === '' || (Array.isArray(v.v) && !v.v.length) || v.v === false; }).map(f => f.k);
const reqVal = v => (!v ? null : 'set' in v ? (v.set ? 'set ' + (v.hint || '') : 'empty') : v.v);
async function llmDev(c, text, lang, p = {}, frame = '', fs = null) {
  const knowP = knowBrief(c, text, !!p.compact); // v3.20: his library (Drive and documents) — the parts that match this message, asked at once
  const P = getP(); const perms = devPerms(c); const words = wordsOf(text); const today = new Date().toISOString().slice(0, 10);
  // (v3.33 — notes 15/35, «الرد لا يتجاوز ثانيتين»: the requirements and the whole platform are asked at once, while the rest is gathered)
  const reqP = perms.includes('automation') && CFG.mode === 'hosted' ? reqBrief().catch(() => null) : null; const nowP = c.user.role === 'owner' && CFG.mode === 'hosted' ? nowBrief() : null; nowP?.catch(() => {});
  const topics = p.compact ? devTopics(text, p.ctx || '').slice(0, 2) : devTopics(text, p.ctx || ''); // v3.12: what the message is about — the manuals and data its prompt carries (v3.19: two at most when it is asked again lighter)
  const roots = Object.keys(PATH_PERM).filter(k => perms.includes(PATH_PERM[k]) && !/^master_key/.test(k));
  const colls = Object.keys(COLL_PERM).filter(k => perms.includes(COLL_PERM[k]));
  const services = catalog(P).map(s => [s, scoreText(svcText(s), words) + (text.includes(s.id) ? 10 : 0)]).filter(x => x[1] > 0).sort((a, b) => b[1] - a[1]).slice(0, 12)
    .map(([s]) => ({ id: s.id, app: s.app, name: L(s.n), status: s.status || 'active', plans: s.plans || [], ...(s.countries ? { off_in: Object.keys(s.countries).filter(k => s.countries[k] === false) } : {}) }));
  // v3.26.1: a sold copy and the showcase have no plan and no payment gateway — their assistant is not told of any
  const sold = SOLO || SHOW;
  const plans = sold ? null : rowsOf('platform', 'plans').map(p => ({ id: p.id, code: p.code, audience: p.audience, name: Lx([p.name_ar, p.name_en, p.name_fr]) || p.name_ar, base_price: p.base_price ?? null, prices: p.prices || {}, active: p.active !== false }));
  const countries = rowsOf('platform', 'countries').map(x => ({ id: x.id, code: x.code, name: Lx([x.name_ar, x.name_en, x.name_fr]) || x.code, currency: x.currency, enabled: x.enabled !== false, ...(sold ? {} : { gateways: x.gateways || [] }) }));
  const gateways = sold ? null : rowsOf('platform', 'gateways').map(g => ({ id: g.id, code: g.code, name: g.name, countries: g.countries || [], env: g.env || 'test', active: g.active !== false }));
  // v3.12: a country he names («أضف قطر») brings the countries in full; an account switched on or off, its plans; a gateway he names, the gateways
  const named = (list, keys) => list.some(x => keys.some(k => { const v = String(x[k] || '').trim(); return v.length >= 3 && text.toLowerCase().includes(v.toLowerCase()); }));
  if (!topics.includes('countries') && named(rowsOf('platform', 'countries'), ['name_ar', 'name_en', 'name_fr'])) topics.push('countries');
  if (!topics.includes('plans') && /حساب|حسابات|مكتب|مكاتب|شرك|\b(?:account\w*|tenant\w*|office\w*)\b/i.test(text) && /فعّ?ل|تفعيل|أوقف|اوقف|إيقاف|ايقاف|علّ?ق|جمّ?د|رقّ?|ترقي|\b(?:activat\w*|suspend\w*|upgrad\w*|downgrad\w*)\b/i.test(text)) topics.push('plans');
  if (gateways && !topics.includes('gateways') && named(gateways, ['code', 'name'])) topics.push('gateways');
  const tl = tenants().filter(T => T.status !== 'deleted'); const counts = {};
  for (const T of tl) { const a = counts[T.app] || (counts[T.app] = {}); a[T.status || 'trial'] = (a[T.status || 'trial'] || 0) + 1; }
  const current = {}; for (const [k, re] of Object.entries(DEV_TOPIC)) if (roots.includes(k) && re.test(text)) current[k] = clip(JSON.stringify(P[k] ?? null), 900);
  const collHit = coll => scoreText([...(R.COLL[coll] || []), coll.replace(/_/g, ' ')].join(' '), words) > 0;
  const create = [...new Set([...colls.filter(collHit), ...['countries', 'plans', 'gateways'].filter(x => colls.includes(x) && topics.includes(x))])].slice(0, 5).map(coll => ({ coll, fields: fieldsOf(coll) }));
  const canCode = c.user.role === 'owner' && CFG.mode === 'hosted' && !!LLM.code; const canN8n = perms.includes('automation') && !!LLM.n8n && !(SOLO || SHOW); // (v3.28: a sold copy links no outside automation site)
  let n8n = null;
  if (canN8n && /n8n|workflow|سير العمل|سير عمل|اتمته|أتمتة|اتمتة|automati|ورك ?فلو/i.test(text)) { try { const r = await LLM.n8n({ action: 'list' }); n8n = (r.workflows || []).slice(0, 80).map(w => ({ id: w.id, name: clip(w.name, 60), active: !!w.active })); } catch (e) { n8n = { error: e?.code || 'error', note: 'n8n is not linked yet: its address and API key are added in the Automation link screen (d_automation)' }; } }
  // v3.6: the automation bridge (the server sends the offices' messages and asks AI through his n8n) — its state when he talks about it
  const canBridge = perms.includes('automation') && !!LLM.bridge && !(SOLO || SHOW); let bridge = null;
  if (canBridge && /n8n|bridge|جسر|اتمته|أتمتة|اتمتة|automati|إرسال|ارسال|يرسل|تُرسل|ترسل|رسائل|الرسائل|واتساب|whatsapp|gmail|sms|بريد|send|message|envoi/i.test(text)) { try { bridge = bridgeBrief(await LLM.bridge('status')); } catch (e) { bridge = { error: e?.code || 'error' }; } }
  // v3.7: the automation engine — its workflows and state when he talks about automation (or writes from its screen)
  const canFlow = perms.includes('automation') && !!LLM.flow; let flows = null; let flowCtx = null;
  if (canFlow && (p.ctx === 'automation' || /اتمته|أتمتة|اتمتة|اتمتات|أتمتات|automati|workflow|سير العمل|سير عمل|ورك ?فلو|trigger|تريجر|مشغل|node|عقده|عقدة|webhook|ويب ?هوك|n8n|make\b|تكامل|integration|connect|اقتراح|اقترح|proposal|suggest/i.test(text))) {
    try { const r = await LLM.flow('list', {}); flows = (r.flows || []).slice(0, 60).map(flowBrief); flowCtx = { paused_accounts: (r.paused || []).map(x => ({ id: x.id, name: x.name })), channels: { whatsapp: !!r.channels?.whatsapp?.ready, email: !!r.channels?.email?.ready, sms: !!r.channels?.sms?.ready, ai: !!(r.channels?.ai?.ready || r.channels?.ai?.bridge), sending: r.channels?.active || 'none' }, ...(p.flow && FLOWN[p.flow] ? { open_in_editor: { id: p.flow, name: FLOWN[p.flow] } } : {}), ...(p.tenant ? { chosen_account: p.tenant } : {}) }; }
    catch (e) { flows = null; flowCtx = { error: e?.code || 'error' }; }
  }
  // v3.8: a new service (or a change to one of his own) designed by the AI — on a hosted site, with the «services» permission
  const canSvc = perms.includes('services') && CFG.mode === 'hosted';
  // v3.12: the channels (WhatsApp, SMS, e-mail, Instagram) and the AI providers, from the assistant too
  const canChan = perms.includes('automation') && CFG.mode === 'hosted'; const canAI = perms.includes('ai') && CFG.mode === 'hosted';
  // v3.18.4: every requirement's real state goes with every message (short), and what Dar did with the keys of this one
  const canReq = perms.includes('automation') && CFG.mode === 'hosted'; let reqNow = null;
  const isOwner = c.user.role === 'owner' && CFG.mode === 'hosted'; let nowTxt = '';
  if (canReq) reqNow = await reqP; // (asked at the start of this brief)
  if (isOwner) { try { nowTxt = (await nowP).text || ''; } catch (e) { nowTxt = 'THE WHOLE PLATFORM NOW: Dar could not read it for this message (' + (e?.code || 'error') + ') — look a section up before saying anything about it: {"do":"now","section":"<id>"}'; } }
  if (p.compact && nowTxt.length > 3500) nowTxt = nowTxt.slice(0, 3500).replace(/\n[^\n]*$/, '') + '\n… (shortened for this attempt — look any section up in full: {"do":"now","section":"<id>"})'; // v3.19
  const know = await knowP;
  const keys = Array.isArray(p.keys) ? p.keys.filter(k => k && typeof k === 'object' && /^K\d{1,3}$/.test(String(k.h || ''))).slice(0, 20) : null;
  if (canReq && keys?.length && !topics.includes('req')) topics.push('req');
  const platform = { mode: CFG.mode, version: VERSION, base_currency: P.base_currency, price_display: P.price_display, default_country: P.default_country, maintenance: !!P.maintenance?.on, theme: { brand: P.theme?.brand || null, accent: P.theme?.accent || null }, domain: P.domain || '' };
  const sys = devPrompt({ lang, today, platform, counts: { accounts: counts, developer_users: users().filter(u => u.app === 'developer').length }, current, services, plans, countries, gateways, tenants: findTenants(text).slice(0, 8), texts: devTexts(text), roots, create, colls, canCode, canN8n, n8n, canBridge, bridge, canFlow, flows, flowCtx, canSvc, ownServices: canSvc ? (P.custom || []).slice(0, 60).map(x => ({ id: x.id, app: x.app, name: L(x.n), status: x.status || 'active' })) : [], ctx: p.ctx || '', frame: fs ? '' : frame, head: fs?.head || '', tail: fs?.tail || '', topics, canChan, canAI, assist: c.user.role === 'owner' ? (P.assist || null) : null, canReq, reqNow, now: nowTxt, canOp: isOwner, keys, know });
  return { sys, opts: { dev: true, colls, services: catalog(P).map(s => s.id), roots, canCode, canN8n, canBridge, canFlow, canSvc, canChan, canAI, canReq, canOp: isOwner }, rounds: MIND_ROUNDS.dev, long: canCode && topics.includes('code'), topics };
}
// v3.8: the rows a look-up reads — every record this person may read (data.list keeps his role, plan and «only his own»
// rules), or, for the developer, the subscribers' accounts
function mindRows(coll, c) {
  if (coll === 'tenants') { needPerm(c, 'tenants'); const us = users(); return tenants().filter(T => T.status !== 'deleted').map(T => ({ id: T.id, name: T.name || '', app: T.app, plan: T.plan || '', status: T.status || 'trial', country: T.country || '', city: T.city || '', created: T.created || '', trial_end: T.trial_end || '', users: us.filter(u => u.tenant === T.id).length, demo: !!T.demo, owner_name: ownerOf(T)?.name || '', owner_email: ownerOf(T)?.email || '', owner_phone: ownerOf(T)?.phone || '' })); }
  const first = OPS['data.list']({ coll, limit: 2000 }, c); let rows = first.rows;
  for (let off = 2000; off < first.total && off < 40000; off += 2000) rows = rows.concat(OPS['data.list']({ coll, limit: 2000, offset: off }, c).rows);
  return rows.map(r => { if (!SKIP_FULL.some(k => k in r)) return r; const o = { ...r }; for (const k of SKIP_FULL) delete o[k]; return o; }); // no key hash, token or file ever reaches the AI
}
const SKIP_ALL = ['images', 'image', 'file', 'photos', 'docs', 'logo', 'signature', 'hash', 'salt', 'secret', 'token', 'portal_token', 'password'];
const SKIP_BIN = ['images', 'image', 'file', 'photos', 'docs', 'logo', 'signature', 'hash', 'salt'];
let SKIP_FULL = SKIP_ALL; // v3.18.4: the owner's own AI tools read secrets and tokens too (no barrier between him and them); pictures, files and password hashes stay out (noise)
function fullRow(coll, r) {
  const o = {}; for (const [k, v] of Object.entries(r || {})) { if (SKIP_FULL.includes(k) || v === '' || v == null || (typeof v === 'string' && v.startsWith('data:'))) continue; o[k] = typeof v === 'string' ? clip(v, 500) : typeof v === 'object' ? clip(JSON.stringify(v), 300) : v; }
  return o;
}
const pickRow = (coll, r, fields) => fields?.length ? Object.fromEntries([['id', r.id], ...fields.filter(f => !SKIP_FULL.includes(f) && r[f] !== undefined && r[f] !== '' && !(typeof r[f] === 'string' && r[f].startsWith('data:'))).map(f => [f, typeof r[f] === 'string' ? clip(r[f], 120) : r[f]])]) : compactRow(coll, r);
// v3.19 — what the assistant makes by itself (assets/media.js): a picture (a connected generator, else drawn from code), a voice, a
// song (ElevenLabs, else composed and played by Dar), the spoken conversation. The owner's own voice service and music stay his and
// his AI team's; an office's assistant makes pictures (one AI operation of its plan each) and speaks with the device's voice.
async function mediaLookup(l, c, x = {}) {
  const M = await import('./media.js?v=3.34.0-d66b90ae'); const K = await import('./kit.js?v=3.34.0-d66b90ae');
  const team = c?.user?.app === 'developer'; const media = CFG.mode === 'hosted' && LLM.media && !x.demo ? LLM.media : null;
  const store = CFG.mode === 'demo' ? null : async (data, name) => { try { return await K.storeFile(data, name); } catch { return String(data).length < 900000 ? data : ''; } };
  const raster = typeof document !== 'undefined' ? M.svgToPng : null;
  if (l.do === 'image') { const r = await M.makeImage(l, { media, ask: x.ask || null, turn: x.turn || '', store, raster }); return { ...r, _label: { do: 'image', label: clip(l.prompt, 60), n: r.image?.made ? 1 : 0, ...(r.image?.made ? {} : { error: true }) } }; }
  if (l.do === 'speak') { const r = await M.speakText(l.text, { media: team ? media : null }); return { speak: { said: !!r.spoken, via: r.via || '', ...(r.why ? { why: r.why } : {}), ...(r.url ? { url: r.url } : {}) }, media: r.media || [], _label: { do: 'speak', label: clip(l.text, 60), ...(r.spoken ? {} : { error: true }) } }; }
  if (l.do === 'song') { const r = await M.makeSong(l, { media: team ? media : null, ask: x.ask || null, turn: x.turn || '', store }); return { ...r, _label: { do: 'song', label: clip(l.brief, 60), n: r.song?.made ? 1 : 0, ...(r.song?.made ? {} : { error: true }) } }; }
  M.setVoice(!!l.on); return { voice: l.on ? 'on — his answers are read aloud, and the microphone listens after each one' : 'off', _label: { do: 'voice' } };
}
async function runLookups(list, c, x = {}) {
  const out = []; SKIP_FULL = c?.user?.app === 'developer' && c.user.role === 'owner' ? SKIP_BIN : SKIP_ALL;
  for (const l of list) {
    try {
      if (['image', 'speak', 'song', 'voice'].includes(l.do)) { out.push(await mediaLookup(l, c, x)); continue; } // v3.19
      // v3.13.1 — an account's own settings (and the limits that bind its assistant), its team, the approvals waiting
      if (l.do === 'settings' && c.tenant) { out.push({ settings: acctSettings(c), limits: { assistant_confirm: acctAssist(c.tenant.id).confirm, ai_team: acctAutonomy(c.tenant.id) }, _label: { do: 'settings' } }); continue; }
      if (l.do === 'team' && c.tenant) { if (!MANAGER_ROLE.includes(roleOf(c))) fail('forbidden'); const us = users().filter(u => u.tenant === c.tenant.id).map(u => ({ id: u.id, name: u.name, role: u.role, status: u.status || 'active', email: u.email })); const inv = store.get('tinvites', []).filter(x => x.tenant === c.tenant.id && (x.exp || 0) > Date.now()).map(x => ({ email: x.email, role: x.role, name: x.name || '' })); out.push({ team: us, invitations_waiting: inv, roles: teamRoles(c.app), _label: { do: 'team', n: us.length } }); continue; }
      if (l.do === 'approvals' && c.tenant) { const js = store.get('jobs', []).filter(j => j.tenant === c.tenant.id && j.status === 'needs_approval' && (MANAGER_ROLE.includes(roleOf(c)) || j.uid === c.user.id)).slice(0, 30).map(j => ({ id: j.id, what: L(j.proposal?.summary) || actLabel(j.action), service: j.service, created: j.created, expires: j.proposal?.expires_at || '', risk: j.proposal?.risk || '', impact: L(j.proposal?.impact) || '' })); out.push({ approvals: js, _label: { do: 'approvals', n: js.length } }); continue; }
      // v3.16 — a collection's fields on demand; and «how do I…»: the screens of his catalogue that do it (with what his plan allows)
      if (l.do === 'fields') { guardCollection(c, l.coll, false); const fl = fieldsOf(l.coll); if (!fl) fail('not_found'); out.push({ fields: l.coll, doc: fieldDoc(l.coll, fl, 40), _label: { do: 'fields', coll: l.coll } }); continue; }
      if (l.do === 'howto' && c.tenant) {
        const P = getP(); const ax = accessCtx(c); const w = wordsOf(l.q);
        const hits = catalog(P).filter(s => s.app === c.app && !['hidden'].includes(s.status) && roleAllows(c.app, c.user.role, s, P)).map(s => [s, scoreText(svcText(s), w)]).filter(x => x[1] > 0).sort((a, b) => b[1] - a[1]).slice(0, 6)
          .map(([s]) => { const ac = access(s, ax); return { service: s.id, name: L(s.n), does: L(s.d), tools: svcActs(s).map(a => ({ id: a, name: actLabel(a) })), ...(ac === 'ok' ? {} : { available: false, why: ac }) }; });
        out.push({ howto: l.q, screens: hits, ...(hits.length ? {} : { note: 'no screen matches these words: ask him what he wants to do, in other words' }), _label: { do: 'howto', n: hits.length } }); continue;
      }
      if (l.do === 'query') { const r = runQuery(mindRows(l.coll, c), l); out.push({ query: l.coll, ...(l.where ? { where: l.where } : {}), ...(l.since || l.until ? { range: [l.since || '', l.until || ''], date: l.date || 'created' } : {}), total: r.total, shown: r.rows.length, rows: r.rows.map(x => pickRow(l.coll, x, l.fields)), _label: { do: 'query', coll: l.coll, n: r.total } }); continue; }
      if (l.do === 'stats') { const r = runStats(mindRows(l.coll, c), l); out.push({ stats: l.coll, ...(l.where ? { where: l.where } : {}), ...(l.since || l.until ? { range: [l.since || '', l.until || ''], date: l.date || 'created' } : {}), ...r, _label: { do: 'stats', coll: l.coll, op: r.op, n: r.n } }); continue; }
      if (l.do === 'get') { const r = l.coll === 'tenants' ? mindRows('tenants', c).find(x => x.id === l.id) : OPS['data.get']({ coll: l.coll, id: l.id }, c); if (!r) fail('not_found'); out.push({ get: l.coll, id: l.id, record: fullRow(l.coll, r), _label: { do: 'get', coll: l.coll, label: rowName(r) } }); continue; }
      if (l.do === 'recall') { const r = LLM.mind && !c.tenant?.demo ? await LLM.mind.recall({ text: l.q, limit: 20, budget: 3500 }) : { memories: [] }; out.push({ recall: l.q, memories: (r?.memories || []).map(m => ({ id: m.id, kind: m.kind, scope: m.scope, text: m.text })), _label: { do: 'recall', n: (r?.memories || []).length } }); continue; }
      // v3.33 (note 5): where a thing he names or sees lives — a look-up, never «which file?» to him
      if (l.do === 'where') { const found = whereIs(l.q, c); out.push({ where: l.q, found, ...(found.length ? {} : { note: 'nothing matches these words — try the exact words he sees on the screen, or other words for the same thing' }), _label: { do: 'where', label: l.q, n: found.length } }); continue; }
      if (l.do === 'find' && l.coll === 'tenants') { needPerm(c, 'tenants'); const rows = findTenants(l.q); out.push({ find: 'tenants', q: l.q, rows, _label: { do: 'find', coll: 'tenants', n: rows.length } }); continue; }
      if (l.do === 'find') {
        let rows = OPS['data.list']({ coll: l.coll, q: l.q, limit: 12 }, c).rows;
        if (!rows.length) { const w = wordsOf(l.q); rows = OPS['data.list']({ coll: l.coll, limit: 3000 }, c).rows.map(x => [x, scoreText(Object.values(x).filter(v => typeof v === 'string' && !v.startsWith('data:')).join(' '), w)]).filter(x => x[1] > 0).sort((a, b) => b[1] - a[1]).slice(0, 12).map(x => x[0]); }
        out.push({ find: l.coll, q: l.q, rows: rows.map(x => compactRow(l.coll, x)), _label: { do: 'find', coll: l.coll, n: rows.length } }); continue;
      }
      if (l.do === 'search') { const r = await LLM.code('code.search', { q: l.q, ...(l.terms ? { terms: l.terms } : {}), ...(l.path ? { path: l.path } : {}), ...(l.ctx ? { ctx: l.ctx } : {}), ...(l.regex ? { regex: true } : {}), limit: 24 }); out.push({ search: l.q, ...(l.path ? { in: l.path } : {}), files_searched: r.files, hits: (r.hits || []).map(h => ({ path: h.path, line: h.line, text: h.text })), ...(r.more ? { more: 'only the first hits are shown — narrow it with path or a more exact text' } : {}) }); continue; }
      if (l.do === 'files') { const r = await LLM.code('code.list', {}); const q = String(l.q || '').toLowerCase(); const fl = (r.files || []).filter(f => f.text && (!l.path || f.path.startsWith(l.path)) && (!q || f.path.toLowerCase().includes(q))); out.push({ files: l.path || '/', ...(l.q ? { q: l.q } : {}), total: fl.length, list: fl.slice(0, 200).map(f => `${f.path} (${f.size})`), ...(fl.length > 200 ? { more: 'only the first 200 are shown — give a longer path or q' } : {}) }); continue; }
      if (l.do === 'read') {
        const r = await LLM.code('code.read', { path: l.path, ...(l.from ? { from: l.from } : {}), ...(l.to ? { to: l.to } : {}) });
        if (r.range) { out.push({ read: r.path, range: r.range, of_lines: r.lines, content: r.content }); continue; }
        const lines = r.content.split('\n').length; const big = r.content.length > 30000;
        out.push({ read: r.path, of_lines: lines, content: big ? r.content.slice(0, 30000) : r.content, ...(big ? { cut: `the file is longer (${lines} lines): read the rest with from/to` } : {}) }); continue;
      }
      if (l.do === 'setting') { let v = getP(); for (const k of l.path.split('.')) { v = v?.[k]; if (v === undefined) break; } const sv = JSON.stringify(v ?? null); out.push({ setting: l.path, value: sv.length > 8000 ? { cut_json: sv.slice(0, 8000) } : (v ?? null) }); continue; }
      if (l.do === 'diag') {
        if (l.what === 'guard') { const r = await LLM.code('server.health', {}); out.push({ diag: 'guard', guard: r.guard || { unavailable: 'dar-guard.php is not installed' } }); continue; } // v3.13
        if (l.what === 'doctor') { // v3.14: the self-check (dar-doctor.php) — what it found, what it repaired and proved, what waits for him
          if (l.run) await api.call('doctor.run', { full: true });
          const r = await api.call('doctor.status', {}); const open = (r.incidents || []).filter(x => !['fixed', 'gone'].includes(x.status));
          out.push({ diag: 'doctor', checked_at: r.last?.at || null, state: r.counts, layers: r.layers, incidents: open.slice(0, 25).map(x => ({ id: x.id, what: x.code, subject: x.subject, level: x.level, status: x.status, info: x.info, repair: x.remedy || null, runs_by_itself: !!x.auto, his_step: x.person || null, ai: x.ai?.summary || null })),
            repaired: (r.fixes || []).slice(0, 12).map(f => ({ what: f.code, repair: f.remedy, at: f.at, verified: f.verified, by: f.by })), test_journey: (r.canary?.steps || []).map(s => ({ step: s.step, ok: s.ok, why: s.why })), policy: r.policy }); continue;
        }
        if (l.what === 'growth') { // v3.15: the growth engine (dar-grow.php) — its numbers, the best chance now and the cheapest route, what it decided
          const r = await api.call('grow.status', {}); let log = []; try { log = ((await api.call('grow.log', {})).log || []).slice(0, 12).map(x => ({ at: x.at, kind: x.kind, what: x.text, why: x.data?.why || null })); } catch { /* the rest stands */ }
          out.push({ diag: 'growth', on: r.cfg?.on, mode: r.cfg?.mode, ai_ready: r.ai, pages: r.pages, last_30_days: r.totals30, funnel: r.funnel, best_chance_now: (r.best || []).slice(0, 3), cheapest_routes: (r.routes || []).slice(0, 3), learned: r.clusters, channels: (r.channels || []).map(c => ({ id: c.id, mode: c.mode, state: c.state })), last_decisions: log, last_run: r.state?.last || null, note: 'route expectations are estimates from this site\'s own numbers' }); continue;
        }
        if (l.what === 'health') { const r = await LLM.code('server.health', {}); const hs = JSON.stringify(r); out.push({ diag: 'health', health: hs.length > 6000 ? { cut_json: hs.slice(0, 6000) } : r }); continue; }
        const r = await LLM.code('code.history', l.path ? { path: l.path } : {}); out.push({ diag: 'history', changes: (r.changes || []).slice(0, 25).map(x => ({ id: x.id, path: x.path, action: x.action, at: x.at, note: x.note })) }); continue;
      }
      if (l.do === 'bridge' && LLM.bridge) { needPerm(c, 'automation'); if (l.action === 'list') { const r = await LLM.bridge('list', l.status ? { status: l.status } : {}); out.push({ bridge: 'list', ...(l.status ? { status: l.status } : {}), rows: (r.rows || []).slice(0, 30).map(x => ({ tenant: x.tenant, channel: x.channel, to: x.to, status: x.status, tries: x.tries, created: x.created, err: x.err || '' })) }); } else out.push({ bridge: 'status', state: bridgeBrief(await LLM.bridge('status')) }); continue; }
      if (l.do === 'flow' && LLM.flow) {
        needPerm(c, 'automation');
        if (l.action === 'list') { const r = await LLM.flow('list', {}); out.push({ flow: 'list', workflows: (r.flows || []).slice(0, 80).map(flowBrief), paused_accounts: (r.paused || []).map(x => ({ id: x.id, name: x.name })) }); continue; }
        if (l.action === 'get') { const r = await LLM.flow('get', { id: l.id }); FLOWN[r.id] = r.name; out.push({ flow: 'get', workflow: { id: r.id, name: r.name, active: r.active, trigger: flowTrig(r.trigger), nodes: (r.def?.nodes || []).map(n => ({ id: n.id, type: n.type, name: n.name, cfg: n.cfg, on_error: n.on_error })), edges: r.def?.edges || [], settings: { runs_day: r.def?.settings?.runs_day, retry_runs: r.def?.settings?.retry_runs } }, problems: (r.lint || []).filter(x => x.level !== 'info'), needs: r.needs || [], recent: (r.recent || []).slice(0, 10).map(x => ({ id: x.id, status: x.status, tenant: x.tenant, at: x.started, err: x.err || '' })) }); continue; }
        if (l.action === 'runs') { const r = await LLM.flow('runs', { limit: 30, ...(l.id ? { flow: l.id } : {}), ...(l.status ? { status: l.status } : {}) }); out.push({ flow: 'runs', runs: (r.runs || []).map(x => ({ id: x.id, workflow: x.flow_name || x.flow, account: x.tenant_name || x.tenant, status: x.status, at: x.started, steps: x.steps_n, err: x.err || '' })) }); continue; }
        if (l.action === 'diagnose') { out.push({ flow: 'diagnose', diagnosis: await LLM.flow('diagnose', { ...(l.id ? { id: l.id } : {}), ...(l.run ? { run: l.run } : {}) }) }); continue; }
        if (l.action === 'check') { out.push({ flow: 'check', ...(await LLM.flow('check', {})) }); continue; }
        if (l.action === 'stats') { const r = await LLM.flow('stats', { days: 7 }); out.push({ flow: 'stats', days: r.days, heaviest: (r.rows || []).slice(0, 15).map(x => ({ id: x.flow, name: x.name, runs: x.runs, failed: x.failed, seconds: Math.round((x.ms || 0) / 1000), steps: x.steps, ai: x.ai, http: x.http, messages: x.sends })) }); continue; }
        if (l.action === 'usage') { const r = await LLM.flow('usage', {}); out.push({ flow: 'usage', month: r.ym, accounts: (r.rows || []).slice(0, 25).map(x => ({ id: x.tenant, name: x.name, plan: x.plan, runs: x.flow_runs, limit: x.limit_runs, whatsapp: x.wa_msgs, emails: x.emails, sms: x.sms, ai: x.ai_calls, api_calls: x.http_calls, webhooks: x.webhooks_in })), total: r.total }); continue; }
      }
      if ((l.do === 'node' || l.do === 'dev') && LLM.node) {
        needPerm(c, 'automation');
        if (l.do === 'node') { const r = await LLM.node('node.list', {}); out.push({ node: 'list', nodes: (r.nodes || []).slice(0, 60).map(x => { NODEN[x.id] = x.name; return { id: x.id, key: x.key, name: x.name, status: x.status, risk: x.risk, version: x.ver, live_version: x.live_ver, tests_ok: x.tests_ok, origin: x.origin }; }), ai_ready: !!r.ai, policy: r.policy }); continue; }
        const r = await LLM.node('dev.proposals', {}); out.push({ dev: 'proposals', scanned: r.scan_at, proposals: (r.proposals || []).slice(0, 20).map(x => { DEVK[x.id] = { kind: x.kind, title: x.title }; return { id: x.id, kind: x.kind, title: x.title, score: x.score, evidence: x.detail }; }) }); continue;
      }
      // v3.18.4: every requirement and key — what stops the platform, each one's state and why, one in full, the secrets kept by handle
      if (l.do === 'req') {
        needPerm(c, 'automation'); const chk = x => (x ? { ok: x.ok, code: x.code || '', said: clip(x.msg || '', 160), at: x.at || '' } : null);
        if (l.action === 'missing') { const r = await api.call('req.brief', {}); RQB.v = r; RQB.at = Date.now(); const rd = r.readiness || {}; out.push({ req: 'missing', platform_ready: !!rd.ready, stops_the_platform: rd.blocking || [], recommended_not_working: rd.recommended || [], his_steps_outside_dar: (rd.external || []).map(x => x.id), ai_providers_answering: rd.ai_working || [], changed_lately: (r.changes || []).slice(0, 10), _label: { do: 'req', label: 'missing', n: (rd.blocking || []).length } }); continue; }
        if (l.action === 'board') { const r = await api.call('req.board', {}); out.push({ req: 'board', counts: r.counts, items: (r.items || []).map(it => ({ id: it.id, group: it.g, need: it.need, status: it.status, ...(it.name ? { name: it.name } : {}), ...(it.last ? { check: chk(it.last) } : {}), ...(reqEmpty(it).length ? { empty: reqEmpty(it) } : {}) })), _label: { do: 'req', label: 'board', n: (r.items || []).length } }); continue; }
        if (l.action === 'item') { const it = await api.call('req.item', { id: l.id }); out.push({ req: 'item', item: { id: it.id, status: it.status, need: it.need, cost: it.cost, console: it.link || '', about: it.about || '', fields: (it.fields || []).map(f => ({ field: f.k, type: f.t, needed: !!f.m, ...(f.o ? { options: f.o } : {}), ...(f.re ? { form: f.re } : {}), value: reqVal(it.values?.[f.k]) })), last_check: chk(it.last), ...(it.nodes ? { connectors: it.nodes.map(n => ({ id: n.id, key: n.key, name: n.name, status: n.status, key_set: n.set })) } : {}), ...(it.extras ? { other_keys: it.extras } : {}) }, _label: { do: 'req', label: it.id } }); continue; }
        if (l.action === 'secret') { const r = await api.call('req.secret', { id: l.id, ...(l.field ? { field: l.field } : {}) }); out.push({ req: 'secret', id: r.id, values: r.values, _label: { do: 'req', label: l.id } }); continue; } // (v3.18.4: the owner's own tools read his keys — no barrier)
        if (l.action === 'held') { const r = await api.call('keys', { action: 'held' }); out.push({ req: 'held', kept_by_handle: r.held || [], _label: { do: 'req', label: 'held', n: (r.held || []).length } }); continue; }
        if (l.action === 'watch') { const r = await api.call('req.watch', {}); const js = JSON.stringify(r); out.push({ req: 'watch', site: js.length > 12000 ? { cut_json: js.slice(0, 12000) } : r, _label: { do: 'req', label: 'watch' } }); continue; }
      }
      // v3.18.4: any read of his panel (the operation a screen performs), its result as the screen would get it
      if (l.do === 'op') { if (!(c.user.role === 'owner' && CFG.mode === 'hosted')) fail('forbidden'); const r = await api.call(l.op, l.payload || {}); const js = JSON.stringify(r ?? null); out.push({ op: l.op, result: js.length > 30000 ? { cut_json: js.slice(0, 30000) } : r, _label: { do: 'op', label: l.op } }); continue; }
      // v3.18.4: one section of his panel in full (its records, settings and state, read now) — or every section in a few lines
      // v3.20: the library — search it, read a document from a part, list every document (dar-know.php)
      if (l.do === 'know') {
        if (CFG.mode !== 'hosted' || c?.tenant?.demo || c?.user?.demo) { out.push({ know: 'unavailable', note: 'this example account has no library (it lives on the server)', _label: { do: 'know' } }); continue; }
        const r = await api.call('know.lookup', l.list ? { list: true } : l.doc ? { doc: l.doc, part: l.part || 0 } : { q: l.q }); const js = JSON.stringify(r);
        out.push({ ...(js.length > 40000 ? { know: r.know, cut_json: js.slice(0, 40000) } : r), _label: { do: 'know', label: l.q || r.title || '', n: (r.found || r.documents || []).length } }); continue;
      }
      if (l.do === 'now' && c.tenant && c.user?.app !== 'developer') { const sec = String(l.section || ''); let r; if (CFG.mode === 'hosted' && !c.tenant.demo && !c.user.demo) { try { r = sec ? await api.call('aware.now', { section: sec }) : { text: await awareBrief(c) }; } catch (e) { if (e?.code === 'not_found') throw e; r = null; } } if (!r) r = sec ? awareLocalDetail(c, sec) : { text: awareLocal(c) }; const js = JSON.stringify(r); out.push({ now: sec || 'all', detail: js.length > 40000 ? { cut_json: js.slice(0, 40000) } : r, _label: { do: 'now', label: sec || t('now_all') } }); continue; } // v3.20: the account's own state
      if (l.do === 'now') { if (!(c.user.role === 'owner' && CFG.mode === 'hosted')) fail('forbidden'); if (l.section) { const r = await api.call('now', { section: l.section }); const js = JSON.stringify(r); out.push({ now: l.section, detail: js.length > 40000 ? { cut_json: js.slice(0, 40000) } : r, _label: { do: 'now', label: r.name || l.section } }); } else { const r = await nowBrief(true); out.push({ now: 'all', text: r.text, _label: { do: 'now', label: t('now_all') } }); } continue; }
      // v3.12: the manual of a group of tools; the channels' state and what they received; the AI providers, and why one does not answer
      if (l.do === 'help') { const doc = DEV_HELP[l.topic]; out.push({ help: l.topic, manual: doc || 'no such group', _label: { do: 'help', label: l.topic } }); continue; }
      if (l.do === 'channel') {
        needPerm(c, 'automation');
        if (l.action === 'inbox') { const r = await api.call('chan.wa_inbox', {}); out.push({ channel: 'inbox', messages: (r.rows || []).slice(0, 20).map(x => ({ from: x.from, text: clip(x.text, 200), status: x.status, reply: clip(x.reply, 200), at: x.at })), _label: { do: 'channel', label: 'inbox', n: (r.rows || []).length } }); continue; }
        const r = await api.call('chan.status', {}); out.push({ channel: 'status', state: r, _label: { do: 'channel', label: 'status' } }); continue;
      }
      if (l.do === 'ai') {
        needPerm(c, 'ai'); const r = await api.call('ai.settings', {});
        const prov = (r.providers || []).map(x => ({ id: x.id, name: x.name, enabled: x.enabled, answers_now: (r.ready || []).includes(x.id), keys: (x.keys || []).map(k => ({ resting: k.resting, ...(k.resting ? { until: k.until, why: k.err || '', said: clip(k.note, 160) } : {}), ...(k.ok_at ? { last_ok: k.ok_at } : {}) })), models: { economy: x.economy, standard: x.standard, deep: x.deep } })).filter(x => x.enabled || x.keys.length);
        out.push({ ai: 'status', providers: prov, today: r.day || [], assist: r.assist, council: r.council, cache_hours: r.cache_hours, last_calls: (r.log || []).slice(0, 12).map(x => ({ at: x.at, provider: x.provider, model: x.model, ok: x.ok, ms: x.ms, code: x.code })), _label: { do: 'ai', label: 'status', n: prov.length } }); continue;
      }
      // v3.32: the engineer (dar-eng.php) — a task handed over (the server runs it; this page may close) and what the tasks did
      if (l.do === 'task' || l.do === 'tasks') {
        if (CFG.mode !== 'hosted') { out.push({ ...l, error: 'not_available', note: 'the engineer works on a hosted server only', _label: { do: l.do, error: true } }); continue; }
        const engSum = v => ({ id: v.id, title: v.title, state: v.status, phase: v.phase, requirements: (v.reqs || []).map(r => r.status + ': ' + r.text), files_changed: [...new Set((v.files || []).filter(f => f.area !== 'sandbox').map(f => f.path))], checks: (v.tests || []).map(r => (r.ok ? 'passed ' : 'FAILED ') + r.suite + (r.path ? ' ' + r.path : '') + (r.ok ? '' : ': ' + clip(r.summary || '', 120))), report: clip(v.report || '', 900), waiting: v.status === 'needs_approval' ? 'his approval: ' + (v.pending?.what || []).join(' · ') : v.status === 'needs_input' ? 'his answer: ' + (v.question || '') : '' });
        if (l.do === 'task') { let hh = 0; for (const ch of l.ask) hh = (hh * 31 + ch.codePointAt(0)) >>> 0; const r = await api.call('eng.create', { ask: l.ask, title: l.title || '', via: 'chat', lang: LANG.cur === 'en' ? 'en' : 'ar', ...(l.kind ? { kind: l.kind } : {}), idem: (x.turn || 'tk') + '-' + hh.toString(36) }); out.push({ task: r.id, state: r.status, title: r.title, note: 'handed to the engineer: it runs on the server now and does not depend on this page; its state shows in «مهام المهندس» (#/d_engineer). Say it STARTED — never that it is done.', _label: { do: 'task', label: clip(r.title || l.ask, 60) } }); continue; }
        if (l.id) { const v = await api.call('eng.get', { id: l.id }); out.push({ tasks: [engSum(v)], _label: { do: 'tasks', n: 1 } }); continue; }
        const r = await api.call('eng.list', { limit: 10 }); out.push({ tasks: (r.tasks || []).map(engSum), _label: { do: 'tasks', n: (r.tasks || []).length } }); continue;
      }
      if (l.do === 'radar') { // v3.13: the AI radar — the latest models the world reached and what is new (activate with an "ai" step)
        needPerm(c, 'ai'); const r = await api.call('ai.radar', { action: 'get', limit: 50 });
        out.push({ radar: 'models', scanned_at: r.scanned_at, total: r.total, new: r.new, brief: r.brief, sources: (r.sources || []).map(x => ({ name: x.name, ok: x.ok, ...(x.count ? { count: x.count } : {}) })), running: r.active?.tiers || {}, council: r.active?.council, models: (r.models || []).slice(0, 50).map(m => ({ provider: m.provider, id: m.id, ctx: m.ctx, in: m.in, out: m.out, free: m.free, new: m.new })), _label: { do: 'radar', n: r.total || 0 } }); continue;
      }
      if (l.do === 'n8n' && LLM.n8n) { needPerm(c, 'automation'); const r = await LLM.n8n({ action: l.action, ...(l.id ? { id: l.id } : {}) }); out.push({ n8n: l.action, ...(l.id ? { id: l.id } : {}), ...(r.workflows ? { workflows: r.workflows.slice(0, 80) } : {}), ...(r.workflow ? { workflow: r.workflow } : {}), ...(r.executions ? { executions: r.executions.slice(0, 30) } : {}) }); continue; }
    } catch (e) { out.push({ ...l, error: e?.code || 'error', _label: { do: l.do, coll: l.coll || '', error: true } }); }
  }
  return out;
}
// names for the interface: which record, account or service each step touches (a step on something that is not there is dropped)
function labelPlan(actions, c) {
  const cat = catalog(getP()); const out = [];
  for (const a of actions) {
    const x = { ...a };
    if ((a.do === 'update' || a.do === 'delete') && a.id) { const row = rowsOf(isPlatformColl(a.coll) ? 'platform' : c.tenant?.id, a.coll).find(r => r.id === a.id); if (!row) continue; x.label = clip(row.name || row.title || row.name_ar || row.office_name || row.code || row.number || row.unit_no || row.id, 60); }
    if (a.do === 'tenant') { const T = tenants().find(z => z.id === a.id); if (!T) continue; x.label = T.name || T.id; }
    // v3.13.1: an account's own steps, named (the member, the client, the record, the request)
    if (a.do === 'team' && a.id) { const u = users().find(z => z.id === a.id && z.tenant === c.tenant?.id); if (!u) continue; x.label = u.name || u.email; }
    if (a.do === 'message') { if (a.conversation) { const cv = rowsOf(c.tenant?.id, 'conversations').find(z => z.id === a.conversation); if (!cv) continue; x.label = clip(cv.contact || '', 60); } else { const r = rowsOf(tenantKey(c, a.coll), a.coll).find(z => String(z.id) === String(a.id)); if (!r) continue; const ct = contactOf(a.coll, r); const to = a.channel === 'email' ? ct.email : ct.phone; x.label = rowName(r) + (to ? ` (${to})` : ''); } } // (v3.13.1: where it goes, shown before he says yes)
    if (a.do === 'link') { const coll = a.what === 'portal' ? a.coll : LINK_WHAT[a.what]; const r = coll ? rowsOf(c.tenant?.id, coll).find(z => String(z.id) === String(a.id)) : null; if (!r) continue; x.label = clip(r.title || r.client || r.name || r.signer_name || r.id, 60); }
    if (a.do === 'approve') { const j = store.get('jobs', []).find(z => z.id === a.id && z.tenant === c.tenant?.id); if (!j) continue; x.label = clip(L(j.proposal?.summary) || actLabel(j.action), 120); }
    if (a.do === 'set') { const m = /^services\.([^.]+)(?:\.|$)/.exec(a.path); if (m) { const s = cat.find(z => z.id === m[1]); if (!s) continue; x.label = L(s.n); } }
    if (a.do === 'node' && a.id && NODEN[a.id]) x.label = NODEN[a.id];
    if (a.do === 'req' && a.id) { const k = 'rq_t_' + a.id; const n = t(k); x.label = n && n !== k ? n : a.id; } // v3.18.4
    if (a.do === 'dev' && a.id) { if (!DEVK[a.id]) continue; x.label = DEVK[a.id].title; x.kind = DEVK[a.id].kind; }
    if (a.do === 'flow') { if (a.id && FLOWN[a.id]) x.label = FLOWN[a.id]; if (a.tenant) { const T = tenants().find(z => z.id === a.tenant); if (!T) continue; x.label = T.name || T.id; } }
    if (a.do === 'open' || a.do === 'run') { const s = cat.find(z => z.id === a.service); if (!s) continue; x.label = L(s.n); if (a.do === 'run') { const xa = (s.xa || []).find(z => z.id === a.action); x.act_label = xa?.n ? L(xa.n) : actLabel(a.action); } }
    // the records a new row points to (a viewing's property, a deal's client) are named, not shown as ids
    if (a.row && (a.do === 'create' || a.do === 'update')) for (const f of fieldsOf(a.coll)) if (f.type === 'ref' && a.row[f.key]) {
      const v = String(a.row[f.key]);
      if (/^\$\d{1,2}$/.test(v)) { const n = +v.slice(1); const src = actions.find(y => y._n === n) || actions[n - 1]; const nm = src?.row ? clip(src.row.name || src.row.title || src.row.unit_no || src.row.number || '', 60) : ''; if (nm) (x.refs ||= {})[f.key] = '«' + nm + '» ' + t('pl_new_record'); continue; }
      const ref = rowsOf(isPlatformColl(f.ref) ? 'platform' : c.tenant?.id, f.ref).find(r => r.id === a.row[f.key]); if (ref) (x.refs ||= {})[f.key] = clip(ref.name || ref.title || ref.office_name || ref.unit_no || ref.number || ref.id, 60);
    }
    out.push(x);
  }
  return out;
}
// v3.8: one turn of Dar Mind (assets/mind.js) for any assistant: the person's memory and conversation from the server, the
// strongest tier the owner allows, look-ups, its own operations checked against the schema and corrected, small safe changes
// for the person himself run at once with Undo, the rest proposed; when no AI provider answers, the request is kept
// v3.9: … and the council: how many different models answer now (members) and how many sit in a hard request's council
export const AIPOL = { at: 0, assist: 'auto', members: 1, size: 3 }; // (v3.12: «auto» by default — fast for the simple, the council for the hard)
async function aiPolicy() {
  if (Date.now() - AIPOL.at < 300000 || !LLM.status) return AIPOL.assist;
  AIPOL.at = Date.now();
  try { const r = await LLM.status(); if (['auto', 'deep', 'standard'].includes(r?.assist)) AIPOL.assist = r.assist; if (r?.council) { AIPOL.members = Math.max(1, Math.min(6, Math.round(+r.council.members) || 1)); AIPOL.size = Math.max(2, Math.min(6, Math.round(+r.council.size) || 3)); } } catch { /* the defaults stay */ } // (v3.13.1: up to 6, as the server allows)
  return AIPOL.assist;
}
const MIND_SURF = ['chat', 'command', 'dev', 'flow', 'console', 'whatsapp', 'service'];
async function mindTurn(p, c, surface) {
  needUser(c); const dev = c.user.app === 'developer'; if (!dev && !c.tenant) fail('forbidden');
  // v3.10: what the person attached (assets/attach.js): its text is the data of this request, its pictures go to the models
  const atts = (Array.isArray(p.attachments) ? p.attachments : []).filter(a => a && typeof a === 'object').slice(0, 4);
  const words = String(p.text || '').slice(0, 3800); if (!words.trim() && !atts.length) fail('validation', { text: 'required' });
  const text = ((words.trim() || '(he attached files without writing a message)') + (atts.length ? '\n📎 ' + attachNames(atts) : '')).slice(0, 4000);
  const pics = attachImages(atts);
  // v3.12: the pictures he sent stay with the conversation (their addresses in his files), so every device shows them
  const keptPics = atts.filter(a => a.kind === 'image' && typeof a.url === 'string' && /^(?:\.{0,2}\/|https?:\/\/)?[\w./?=&%:-]{1,300}$/.test(a.url) && !a.url.startsWith('data:')).map(a => a.url).slice(0, 4);
  const lang = knownLang(p.lang) ? p.lang : LANG.cur;
  const demo = (!dev || SHOW) && !!(c.tenant?.demo || c.user?.demo); // (v3.26: the showcase's example administration asks through the public door too)
  const ask0 = demo ? (LLM.demo ? r => LLM.demo({ ...r, purpose: 'example' }) : null) : LLM.ask;
  const ask = ask0 && pics.length ? r => ask0({ ...r, images: pics }) : ask0;
  if (!ask) return { understood: false, pending: true, ai_off: CFG.mode === 'hosted' ? 'ai_not_configured' : 'no_server' };
  const mind = !demo && LLM.mind ? LLM.mind : null; const app = c.app; const sf = MIND_SURF.includes(surface) ? surface : 'chat';
  // v3.12: the conversation and the memory are fetched while the policy is read (one wait, not two)
  const recallP = mind ? mind.recall({ text: text.slice(0, 4000), app, surface: sf, ...(p.thread ? { thread: p.thread } : {}) }).catch(e => { throw e; }) : null; recallP?.catch(() => {});
  // v3.33 (the owner, 2026-10-22 — notes 15/35: «ردود المساعدات لا تتجاوز ثانيتين»): what the brief will need from the server is
  // asked now, while the memory and the policy are read — the waits overlap instead of following each other
  if (!demo && CFG.mode === 'hosted' && !p.heal) { try { if (dev) { if (devPerms(c).includes('automation')) reqBrief().catch(() => {}); if (c.user.role === 'owner') nowBrief().catch(() => {}); } else awareBrief(c).catch(() => {}); knowBrief(c, text, false).catch(() => {}); } catch { /* only a head start */ } }
  const policy = demo ? 'standard' : await aiPolicy();
  const env = {
    ask,
    // v3.9: the council — how many different models can answer (an example account: a second one checks a doubtful answer)
    members: demo ? 2 : AIPOL.members, councilSize: AIPOL.size,
    outcome: !demo && LLM.outcome ? LLM.outcome : null,
    learn: mind && mind.learn && !c.imp ? x => mind.learn({ ...x, app, surface: sf }) : null,
    recall: mind ? t0 => (t0 === text.slice(0, 4000) && recallP ? recallP : mind.recall({ text: t0, app, surface: sf, ...(p.thread ? { thread: p.thread } : {}) })) : null,
    remember: mind ? (items, forget) => mind.remember({ items, forget }) : null,
    threadAdd: mind && !p.no_thread ? (items, turn) => mind.thread({ action: 'add', app, surface: sf, items, turn, ...(p.thread ? { thread: p.thread } : {}) }) : null,
    // v3.12: what the turn is doing, for the waiting bubble of the screen that asked (by its turn id)
    progress: ev => { try { globalThis.document?.dispatchEvent?.(new CustomEvent('dar:mind', { detail: ev })); } catch { /* no screen */ } },
    brief: async ({ text: tx, mem, tier, compact = false, voice = false }) => {
      if (!dev) { const [aware, know] = await Promise.all([awareBrief(c, { lite: compact }), knowBrief(c, tx, compact)]); return tenantBrief(c, tx, lang, mem, tier, { demo, voice, aware, know }); } // (v3.20: the whole account and its movements; its library)
      const P = getP(); const now = nowContext(tzOf(P.default_country || 'SA'));
      // v3.12: the rules that never change first, what belongs to this moment last (a provider that keeps a prompt's opening answers faster)
      const fs = frameSplit({ kind: 'dev', lang, now, voice, person: { name: c.user.name || '', role: c.user.role || '' }, mem, summary: mem?.context?.summary || '', rounds: MIND_ROUNDS.dev, autorun: false, confirm: c.user.role === 'owner' ? cleanAssist(P.assist).confirm : 'risky', remember: !!mind, tools: '- "tenants" (the subscribers\' accounts: id, name, app app|builders|providers|partner|console, plan, status trial|active|suspended, country, city, created, trial_end, users) can be queried and counted too, like the platform collections.' });
      return llmDev(c, tx, lang, compact ? { ...p, compact: true } : p, '', fs);
    },
    lookup: (list, x = {}) => runLookups(list, c, { ...x, ask, demo }),
    verify: async actions => { const r = mindVerify(actions, c); if (dev && LLM.code && r.actions.some(a => a.do === 'apply')) await verifyCode(r, c); return r; },
    label: actions => labelPlan(actions, c),
    plainLabel: k => plainLabelOf(k), // v3.33
    quick: ({ mem }) => quickPrompt({ lang, dev, name: c.user.name || '', place: c.tenant?.name || '', summary: mem?.context?.summary || '', rules: dev ? cleanAssist(getP().assist).rules || '' : c.tenant ? acctAssist(c.tenant.id).rules || '' : '', owner: dev || c.user.role === 'owner' }), // v3.33 (notes 15/35): a greeting answered at once
    mayAuto: (acts = []) => { if (dev || c.imp || p.autorun === false) return false; const cf = acctAssist(c.tenant?.id).confirm; if (cf === 'none') return true; if (cf !== 'risky') return false; const lim = acctAutonomy(c.tenant?.id); return (acts.length ? acts : [{ do: 'create', coll: 'leads' }]).every(a => lim[stepAutonomy(a) || 'records'] === 'auto'); }, // (v3.13.1: «before everything», or records his AI team must ask about by default — nothing runs by itself)
    run: plan => autoRun(plan, c, p),
    // v3.18.4: what the developer's assistant claims, held against what is true now (the requirements' states, the keys of this
    // message, the steps not run yet): a sentence claiming what is not so is taken out, and he is told
    guard: dev ? (reply, { plan: pl = [] } = {}) => { const keys = Array.isArray(p.keys) ? p.keys : []; const keysBad = keys.some(k => ['held', 'refused', 'error', 'failing', 'saved'].includes(k?.status)); return guardClaims(reply, { truth: truthOf(RQB.v), keysBad, anyBad: keysBad, pending: (pl || []).some(a => a.do === 'req' && a.action === 'activate') ? Object.keys(truthOf(RQB.v)) : (pl || []).filter(a => a.do === 'req' && a.id && a.action !== 'check').map(a => a.id), placed: keys.filter(k => ['working', 'failing', 'saved', 'exists'].includes(k?.status) && k.req).map(k => k.req) }); } : null,
  };
  const heal = p.heal && typeof p.heal === 'object' ? { n: Math.max(0, Math.min(99, Math.round(+p.heal.n) || 0)), last: String(p.heal.last || '').replace(/[^a-z_]/g, '').slice(0, 40) } : null; // v3.19: asked again after a fault — lighter
  return think({ text, attach: attachEvidence(atts), lang, kind: dev ? 'dev' : demo ? 'open' : 'tenant', surface: sf, history: p.history, policy, ...(heal ? { heal } : {}), ...(p.voice ? { voice: true } : {}), turn: typeof p.turn === 'string' && /^[A-Za-z0-9_-]{6,64}$/.test(p.turn) ? p.turn : undefined, images: keptPics }, env);
}
// v3.8: the AI's own operations checked against the real schema and records before anyone runs them: what it wrote in words
// becomes what the record keeps (choices → their codes, «900 ألف» → 900000, dates, phones), a record it points to must exist
// (or be made by an earlier step: "$1"), required fields must be there, a duplicate is pointed out. What it gets wrong goes
// back to it to correct (assets/mind.js); what still cannot be prepared is never run.
// v3.13.1 — the steps an account's assistant takes like its screens' buttons, checked before he is asked (what is wrong goes back
// to the model with the reason, so it corrects itself)
const MANAGER_ROLE = ['owner', 'admin', 'manager'];
const roleOf = c => c.user?.role || '';
export const LINK_WHAT = { esign: 'signatures', docreq: 'doc_requests', shortlist: 'shortlists', portal: '' };
// a record's phone and e-mail, by its fields' types (a client, an owner, a tenant, a signer…)
export function contactOf(coll, row) {
  const fs = fieldsOf(coll) || []; const pick = type => { for (const f of fs) if (f.type === type && row?.[f.key]) return String(row[f.key]); return ''; };
  return { phone: pick('phone'), email: pick('email'), name: rowName(row) };
}
const teamRoles = app => Object.keys(R.TENANT_ROLES[app] || {}).filter(r => r !== 'owner');
function verifyAcctStep(a, c) {
  if (!c.tenant || c.user?.app === 'developer') return 'this step belongs to an account\'s assistant';
  const T = c.tenant; const role = roleOf(c);
  if (a.do === 'setting') {
    if (!ACCT_SET_KEYS.includes(a.key)) return `«${a.key}» is not a setting you change — you change: ${ACCT_SET_KEYS.join(', ')} (its limits and keys stay with the person, in their screens)`;
    if (!(a.key === 'hr_policy' ? [...MANAGER_ROLE, 'hr'] : MANAGER_ROLE).includes(role)) return `this person (${role}) cannot change the ${a.key} setting`;
    try { const spec = ACCT_SETTINGS[a.key]; const before = spec.get(c); spec.clean({ ...before, ...(a.set || {}) }, c, before); } catch (e) { return `setting ${a.key}: ${e?.code === 'validation' ? Object.entries(e.extra || {}).map(([k, v]) => `${k} ${v}`).join(', ') : e?.code || 'refused'} — look the settings up and correct the values`; }
    return '';
  }
  if (a.do === 'team') {
    if (!MANAGER_ROLE.includes(role)) return `this person (${role}) cannot manage the team`;
    const roles = teamRoles(c.app); if (!roles.length) return 'this kind of account has no team roles';
    if (a.action === 'invite' && a.role === 'admin' && !['owner', 'admin'].includes(role)) return `only the account's owner or an admin gives the admin role — not a ${role}`;
    if (a.action === 'invite') { if (!/^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/.test(a.email || '')) return 'invite: a valid e-mail is required — ask him for it'; if (!roles.includes(a.role)) return `invite: the role must be one of ${roles.join(', ')}`; if (users().some(u => u.app === c.app && u.email === String(a.email).toLowerCase())) return 'invite: this e-mail already has an account here'; return ''; }
    const u = users().find(x => x.id === a.id && x.tenant === T.id); if (!u) return `there is no member «${a.id}» in this account — look the team up ({"do":"team"})`;
    if (u.role === 'owner') return 'the account owner\'s access is not changed from here'; if (u.id === c.user.id) return 'he does not change his own access from here';
    if ((u.role === 'admin' || a.role === 'admin') && !['owner', 'admin'].includes(role)) return `only the account's owner or an admin gives, changes or takes the admin role — not a ${role}`;
    if (a.action === 'role' && !roles.includes(a.role)) return `role: one of ${roles.join(', ')}`;
    return '';
  }
  if (a.do === 'message') {
    if (CFG.mode !== 'hosted') return 'messages to clients leave through the hosted site\'s channels — not available on this copy';
    if (a.conversation) { try { guardCollection(c, 'conversations', true); } catch (e) { return `this person cannot answer conversations (${e.code})`; } const cv = rowsOf(T.id, 'conversations').find(x => x.id === a.conversation); return cv ? '' : `there is no conversation «${a.conversation}» — look it up`; }
    try { guardCollection(c, a.coll, false); } catch (e) { return `this person cannot read ${a.coll} (${e.code})`; }
    const r = rowsOf(tenantKey(c, a.coll), a.coll).find(x => String(x.id) === String(a.id)); if (!r) return `there is no ${a.coll} record «${a.id}» — look it up`;
    const ct = contactOf(a.coll, r); if (a.channel === 'email' ? !ct.email : !ct.phone) return `«${ct.name}» has no ${a.channel === 'email' ? 'e-mail' : 'phone number'} on record — ask him for it, or use another channel`;
    return '';
  }
  if (a.do === 'link') {
    const coll = a.what === 'portal' ? a.coll : LINK_WHAT[a.what]; if (!coll || (a.what === 'portal' && !['owners', 'tenants'].includes(coll))) return 'link: what = esign|docreq|shortlist, or portal with coll owners|tenants';
    try { guardCollection(c, coll, true); } catch (e) { return `this person cannot work on ${coll} (${e.code})`; }
    const r = rowsOf(T.id, coll).find(x => String(x.id) === String(a.id)); if (!r) return `there is no ${coll} record «${a.id}» — look it up`;
    if (a.send) { if (CFG.mode !== 'hosted') return 'sending the link leaves through the hosted site\'s channels — not available on this copy'; const ct = contactOf(coll, r); if (a.send.channel === 'email' ? !ct.email : !ct.phone) return `«${ct.name}» has no ${a.send.channel === 'email' ? 'e-mail' : 'phone number'} on record — make the link without sending it, or ask him for the number`; }
    return '';
  }
  if (a.do === 'website') { // v3.28: «موقعي»
    if (!MANAGER_ROLE.includes(role)) return `this person (${role}) cannot publish or translate the website`;
    if (!['publish', 'unpublish', 'translate'].includes(a.action)) return 'website: action = publish | unpublish | translate';
    if (a.action === 'translate' && !knownLangCode(a.lang)) return 'website translate: "lang" must be a language code (any language of the world)';
    if (a.action !== 'publish' && !store.get(`set:${T.id}:website_pub`, null)?.v) return 'the website is not published yet — publish it first ({"do":"website","action":"publish"})';
    return '';
  }
  if (a.do === 'approve') {
    const j = store.get('jobs', []).find(x => x.id === a.id && x.tenant === T.id); if (!j) return `there is no approval «${a.id}» in this account — look them up ({"do":"approvals"})`;
    if (j.status !== 'needs_approval') return 'this request is no longer waiting for approval'; if (!MANAGER_ROLE.includes(role) && j.uid !== c.user.id) return 'this person cannot decide it';
    return '';
  }
  return '';
}
// v3.28: the assistant's checks on its steps, for the tests (the session's own context)
export const mindVerifyTest = actions => { const s = api.session(api.app); return mindVerify(actions, ctxOf(api.app, s?.token)); };
function mindVerify(actions, c) {
  const out = [], issues = [], notes = []; const labelsOf = code => OPTS[code] || [];
  actions.forEach((a0, i) => {
    const a = { ...a0, _n: i + 1, ...(a0.row ? { row: { ...a0.row } } : {}) }; const what = [a.do, a.coll || a.action || a.path || ''].filter(Boolean).join(' ');
    const issue = (msg, level = 'error') => issues.push({ i, what, msg, level });
    // v3.13.1: what the account's own AI-team limits block, its assistant never does (the person still can, from its screen)
    if (c.tenant && c.user?.app !== 'developer') { const cat = stepAutonomy(a); if (cat && acctAutonomy(c.tenant.id)[cat] === 'block') { issue(`the account's limits for its AI team block this (${cat} = blocked, set by the account owner or the platform) — do not propose it; tell him he can do it himself from its screen`); out.push(a); return; } }
    if (['setting', 'team', 'message', 'link', 'approve', 'website'].includes(a.do)) { const m = verifyAcctStep(a, c); if (m) issue(m); out.push(a); return; }
    if (['create', 'update', 'delete'].includes(a.do)) {
      try { guardCollection(c, a.coll, true); if (a.do === 'delete') noLooseListing(c, a.coll); } catch (e) { issue(`this person cannot ${a.do} in ${a.coll} (${e.code})`); out.push(a); return; }
      if (a.do !== 'create') { const cur = rowsOf(tenantKey(c, a.coll), a.coll).find(r => String(r.id) === String(a.id)); if (!cur) { issue(`there is no ${a.coll} record with id «${a.id}» — look it up (find, query) and use its real id`); out.push(a); return; } }
      if (a.do === 'delete') { out.push(a); return; }
      const fields = fieldsOf(a.coll); const by = Object.fromEntries(fields.map(f => [f.key, f])); const row = {}; const bad = [];
      for (const [k, v] of Object.entries(a.row || {})) {
        const f = by[k]; if (!f) { notes.push(`${a.coll}.${k}`); continue; } if (f.ro) continue;
        if (f.type === 'ref' && /^\$\d{1,2}$/.test(String(v))) { const n = +String(v).slice(1); const src = actions[n - 1]; if (n >= a._n || !src || src.do !== 'create' || src.coll !== f.ref) bad.push(`${k}: «${v}» must name an earlier step that creates a ${f.ref} record`); else row[k] = String(v); continue; }
        const r = normField(f, v, labelsOf); if (r.err) { bad.push(`${k}: ${r.err}`); continue; }
        if (r.noTime && a.coll === 'appointments' && k === 'start') issue(`start «${clip(v, 30)}» has no time — use the time he said, or ask him`, 'warn');
        row[k] = r.v;
      }
      for (const f of fields) if (f.type === 'ref' && row[f.key] && !/^\$\d/.test(String(row[f.key]))) {
        const list = rowsOf(isPlatformColl(f.ref) ? 'platform' : c.tenant?.id, f.ref); const v = String(row[f.key]);
        if (list.some(r => String(r.id) === v)) continue;
        const hits = list.filter(r => [r.name, r.title, r.unit_no, r.number, r.office_name].some(x => x && fold(x) === fold(v)));
        if (hits.length === 1) { row[f.key] = hits[0].id; continue; }
        bad.push(hits.length > 1 ? `${f.key}: «${clip(v, 40)}» matches ${hits.length} ${f.ref} records (${hits.slice(0, 4).map(r => r.id + ' ' + rowName(r)).join(', ')}) — choose one id` : `${f.key}: there is no ${f.ref} record «${clip(v, 40)}» — look it up, or create it in an earlier step and write "$<step>"`);
      }
      const { errors } = cleanRow(fields, row, a.do === 'update');
      for (const [k, e] of Object.entries(errors)) if (!bad.some(b => b.startsWith(k + ':'))) bad.push(`${k}: ${e === 'required' ? 'required — missing' : e}`);
      if (a.do === 'create' && !bad.length) for (const ks of R.DEDUPE_KEYS[a.coll] || []) {
        if (!ks.every(k => row[k] != null && row[k] !== '')) continue;
        const nk = (k, v) => k === 'phone' || k.endsWith('_phone') ? latinDigits(v).replace(/\D/g, '').slice(-9) : fold(v);
        const dup = rowsOf(tenantKey(c, a.coll), a.coll).find(r => ks.every(k => r[k] != null && r[k] !== '' && nk(k, r[k]) === nk(k, row[k])));
        if (dup) issue(`a ${a.coll} record with the same ${ks.join(' + ')} already exists: id ${dup.id} «${rowName(dup)}» — update it instead, unless he clearly wants a second one`, 'warn');
        break;
      }
      if (bad.length) issue(bad.join('; '));
      out.push({ ...a, row, _types: Object.fromEntries(Object.keys(row).map(k => [k, by[k]?.type || ''])) }); return; // (v3.9: the council compares values by their field's type)
    }
    out.push(a);
  });
  // a step that depends on a step that cannot run cannot run either
  for (const x of [...issues]) if (x.level !== 'warn') out.forEach((a, j) => { if (j !== x.i && a.row && Object.values(a.row).includes('$' + (x.i + 1)) && !issues.some(y => y.i === j && y.level !== 'warn')) issues.push({ i: j, what: a.do + ' ' + (a.coll || ''), msg: `it depends on step ${x.i + 1}, which has a problem`, level: 'error' }); });
  return { actions: out, issues, notes: notes.length ? [`unknown fields left out: ${[...new Set(notes)].slice(0, 8).join(', ')}`] : [] };
}
// v3.10: a change set to the site's code is tried before anyone is asked to confirm it: the server checks it without writing (every
// find present once, every file's syntax, the shape of the engine), the browser parses the scripts, and what is wrong goes back to
// the model with the nearest text so it corrects itself; what passes carries the lines it would change (shown in the plan's card)
const CODE_TRIED = new Map();
function codeProblem(e) {
  const x = e?.extra || {}; const where = x.change ? `change ${x.change}${x.edit ? ', edit ' + x.edit : ''} (${x.path || ''})` : (x.path ? x.path : 'the change set');
  switch (e?.code) {
    case 'find_none': return `${where}: the "find" text is not in the file${x.near ? ` — the nearest text is at line ${x.near.line}: «${clip(x.near.text, 200)}»` : ''}. Read the file's lines again and copy the text exactly (spaces and line breaks included).`;
    case 'find_many': return `${where}: the "find" text is in the file ${x.count} times — add surrounding text so that it is unique, or set "all":true if you mean every one.`;
    case 'not_found': return `${where}: this file does not exist — look up the real path (files, search), or create it with "write".`;
    case 'exists': return `${where}: ${x.to || 'the target'} already exists — a rename never overwrites.`;
    case 'forbidden': return `${where}: this file cannot be changed (${x.why || x.path || 'protected'}) — the emergency door dar-rescue.php and the engine's own essential files are protected; choose another way.`;
    case 'validation': return `${where}: ${Object.entries(x).filter(([k]) => !['change', 'edit', 'op', 'path'].includes(k)).map(([k, v]) => k + ': ' + (typeof v === 'object' ? JSON.stringify(v) : v)).join('; ') || 'not accepted'}.`;
    case 'file_too_big': return `${where}: the file would be too large.`;
    default: return `${where}: refused (${e?.code || 'error'}).`;
  }
}
async function verifyCode(r, c) {
  const { localCheck } = await import('./devcode.js?v=3.34.0-d66b90ae');
  for (let i = 0; i < r.actions.length; i++) {
    const a = r.actions[i]; if (a.do !== 'apply') continue;
    const key = JSON.stringify(a.changes); let rep = CODE_TRIED.get(key);
    if (!rep) {
      try { const res = await LLM.code('code.apply', { changes: a.changes, check: true, content: true }); rep = { ok: true, changes: res.changes || [], unchanged: !!res.unchanged }; }
      catch (e) { rep = { ok: false, msg: codeProblem(e) }; }
      if (rep.ok) for (const ch of rep.changes) if (ch.content != null) { const bad = await localCheck(ch.path, ch.content); if (bad) { rep = { ok: false, msg: `${ch.path}: the file would not parse — ${bad}` }; break; } }
      if (CODE_TRIED.size > 40) CODE_TRIED.clear(); CODE_TRIED.set(key, rep);
    }
    if (!rep.ok) { r.issues.push({ i, what: 'apply', msg: rep.msg, level: 'error' }); continue; }
    if (rep.unchanged) { r.issues.push({ i, what: 'apply', msg: 'this change set changes nothing (every file is already as it would be) — is it already done?', level: 'warn' }); continue; }
    a.preview = rep.changes.map(({ content, ...x }) => x);
  }
}
// v3.8: an office's receptionist (its WhatsApp agent, its voice receptionist, its page) is the platform's AI: it answers from
// the office's available listings, rules and hours, and hands over a call-back or a viewing once the client gives his number.
// No AI answering now: said plainly (the page offers its contact form) — never a rule-made reply.
async function agentAI({ Tn, c, text, history = [], channel = 'web', office, listings, rules, settings, tz, cur, bookUrl, pageUrl }) {
  const demo = !!Tn.demo || !c; const ask = demo ? (LLM.demo ? r => LLM.demo({ ...r, purpose: c ? 'example' : 'site' }) : null) : LLM.ask;
  const off = code => ({ reply: t('agent_ai_wait'), intent: 'offline', items: [], form: true, ai_off: code, lang: LANG.cur });
  if (!ask) return off(CFG.mode === 'hosted' ? 'ai_not_configured' : 'no_server');
  const sys = receptionPrompt({ office, listings, rules, settings, now: nowContext(tz || 'Asia/Riyadh'), cur, bookUrl, pageUrl, channel });
  const msgs = [{ role: 'system', content: sys }]; for (const h of history.slice(-12)) if (h.text) msgs.push({ role: h.from === 'agent' ? 'assistant' : 'user', content: String(h.text).slice(0, 600) });
  if (msgs.at(-1).role !== 'user' || msgs.at(-1).content !== text) msgs.push({ role: 'user', content: text });
  try {
    let r = await ask({ fn: 'ui.reception', messages: msgs, json: true, soft_json: true, tier: 'standard', temperature: 0.3, max_tokens: 700, member: 0, said: String(text || '').slice(0, 600) }); let out = parseReception(r.data || r.text, listings);
    // v3.9: a price, an area or any figure the office's facts do not give never reaches the client: it goes back once, then to a
    // second model; a sentence that still carries one is left out of the reply
    // (the facts are the office's own — never the client's words or the history: a client cannot make a price true by asking it)
    const pool = evidencePool([sys]); let g = groundCheck(out.reply, pool); let calls = 1;
    if (!g.ok) {
      const again = [...msgs, { role: 'assistant', content: JSON.stringify({ reply: out.reply }) }, { role: 'user', content: `Your reply states figures that are not in the office's facts above: ${g.bad.join(', ')}. Never give a price, an area, a size, a distance or any number that is not written in those facts — say the team will confirm it. Answer again with the complete JSON.` }];
      for (const member of [0, 1]) {
        try { calls++; const r2 = await ask({ fn: 'ui.reception', messages: again, json: true, soft_json: true, tier: 'standard', temperature: 0.3, max_tokens: 700, member, said: String(text || '').slice(0, 600) }); const o2 = parseReception(r2.data || r2.text, listings); const g2 = groundCheck(o2.reply, pool); if (o2.reply && g2.bad.length < g.bad.length) { r = r2; out = o2; g = g2; } }
        catch { break; }
        if (g.ok) break;
      }
      if (!g.ok) {
        const left = trimUngrounded(out.reply, g.bad);
        // (a viewing or a call-back the client asked for is never dropped: it reaches the office, confirmed in the page's words)
        if (left.length < 12 && !out.booking && !out.lead) return { ...off('ai_unverified'), ai: { provider: r.provider || '', model: r.model || '', calls } };
        out = { ...out, reply: left.length >= 12 ? left : t(out.booking ? 'viewing_requested' : 'agent_lead_sent'), trimmed: g.bad };
      }
    }
    return { ...out, ai: { provider: r.provider || '', model: r.model || '', calls } };
  }
  catch (e) { if (AI_WAIT.includes(e?.code) || e?.code === 'ai_budget_reached') return off(e.code); throw e; }
}
// "$n" in a row: the id of the record step n created
const withRefs = (row, made) => row ? Object.fromEntries(Object.entries(row).map(([k, v]) => [k, typeof v === 'string' && /^\$\d{1,2}$/.test(v) && made[+v.slice(1)] ? made[+v.slice(1)] : v])) : row;
// v3.8: small safe changes for the person himself, run at once (create, update, his attendance), each with what undoes it
async function autoRun(plan, c, p) {
  const out = []; const made = {}; AWB.clear(); // (v3.20: the next message reads the account as these steps left it)
  for (const [i, a] of plan.entries()) {
    try {
      const row = withRefs(a.row, made);
      if (a.do === 'create') { const r = await OPS['data.create']({ coll: a.coll, row }, c); made[a._n || i + 1] = r.id; out.push({ i, a, ok: true, id: r.id, label: rowName(r), undo: { created: { coll: a.coll, id: r.id } }, open: `${a.coll}:${r.id}` }); continue; }
      if (a.do === 'update') { const cur = OPS['data.get']({ coll: a.coll, id: a.id }, c); const before = Object.fromEntries(Object.keys(row).map(k => [k, cur[k] ?? ''])); const r = await OPS['data.update']({ coll: a.coll, id: a.id, row }, c); out.push({ i, a, ok: true, id: a.id, label: a.label || rowName(r), undo: r?._audit ? { audit: r._audit } : { restore: { coll: a.coll, id: a.id, row: before } }, open: `${a.coll}:${a.id}` }); continue; }
      if (a.do === 'clock') { const r = await OPS['hr.clock']({ action: a.action, method: p.channel === 'whatsapp' ? 'whatsapp' : 'app' }, c); out.push({ i, a, ok: true, id: r?.id || '', label: '' }); continue; }
      out.push({ i, a, ok: false, code: 'not_auto' }); break;
    } catch (e) { out.push({ i, a, ok: false, code: e?.code || 'error', extra: e?.extra || null }); break; }
  }
  for (const a of plan) if (a.row && !out.some(d => d.ok && d.a === a)) a.row = withRefs(a.row, made); // what waits points to what was made
  return out;
}
// v3.8: an AI action that carries its own instruction (a developer's own service, one the AI designed included, or an action
// he added to a built-in one) runs that instruction with the platform's AI on the service's records — the same messages as
// the designer's «try it» (dar-devai.php svc_act_messages); the changes it proposes stay within the service's own fields and
// records, and are made only when the person applies them
async function customAct(svc, xa, c, p) {
  const coll = (svc.e || [])[0]; if (!LLM.ask || !xa?.prompt || !coll || !c.tenant) return null;
  const fields = R.parseFields(entSpec(coll)); if (!fields.length) return null;
  const all = rowsOf(c.tenant.id, coll); const want = [...(Array.isArray(p.ids) ? p.ids : []), p.input?.id].filter(Boolean).map(String);
  const recs = (want.length ? all.filter(r => want.includes(String(r.id))) : all.slice(0, 20)).map(r => Object.fromEntries(Object.entries(r).filter(([k, v]) => k === 'id' || (fields.some(f => f.key === k) && v !== '' && v != null)).map(([k, v]) => [k, typeof v === 'string' ? v.slice(0, 600) : v])));
  if (!recs.length) return { kind: 'text', title: xa.n, text: t('xa_no_records') };
  const lang = knownLang(p.lang) ? p.lang : LANG.cur; const name = L(xa.n) || xa.id;
  const fd = fields.map(f => `${f.key} (${f.type}${f.options ? ': ' + f.options.join('|') : ''}, «${fieldLabel(f.key, coll)}»)`).join('; ');
  const sys = `You are the AI action «${name}» of the service «${L(svc.n)}» on Dar, working for the account «${c.tenant.name || ''}». Follow this instruction: ${xa.prompt}\nThe records' fields: ${fd}.\nWrite in ${langEnglish(lang)}. Use only the facts given; never invent figures. Return ONLY JSON: {"text": "your answer for the person (plain text, short lines allowed)", "updates": [{"id": "<a record id>", "fields": {"<field key>": <new value>}}]} — "updates" only when the instruction asks you to fill or change fields of these records, otherwise [].`;
  const team = teamBrief(svc.t, getP(), r => ROLES[r]?.[1] || r); // v3.11: the service's team and the reviewer's bar
  const account = await awareBrief(c, { lite: true }).catch(() => ''); // v3.20: the account as it is now
  const r = await LLM.ask({ fn: 'ui.service.action', ...(p.lref ? { ref: p.lref } : {}), messages: [{ role: 'system', content: (team ? sys + '\n' + team : sys) + (account ? '\nTHE ACCOUNT AS IT IS NOW (context, never contradict it):\n' + clip(account, 1800) : '') }, { role: 'user', content: 'The records: ' + JSON.stringify(recs).slice(0, 9000) }], json: true, soft_json: true, tier: 'standard', temperature: 0.3, max_tokens: 1200 });
  let d = r.data; if (!d || typeof d !== 'object') { try { d = JSON.parse(String(r.text || '').replace(/^```(?:json)?\s*/i, '').replace(/```\s*$/, '')); } catch { d = { text: String(r.text || '') }; } }
  const ids = new Set(recs.map(x => String(x.id))); const keys = new Set(fields.filter(f => !f.ro).map(f => f.key));
  const apply = (Array.isArray(d.updates) ? d.updates : []).slice(0, 20).filter(u => u && ids.has(String(u.id)) && u.fields && typeof u.fields === 'object')
    .map(u => ({ coll, id: String(u.id), patch: Object.fromEntries(Object.entries(u.fields).filter(([k, v]) => keys.has(k) && (typeof v !== 'object' || Array.isArray(v)))) })).filter(a => Object.keys(a.patch).length);
  const text = String(d.text || '').trim().slice(0, 4000) || t('xa_nothing');
  return { kind: 'multi', title: xa.n, parts: [{ kind: 'text', text, ai: true }], ...(apply.length ? { apply } : {}), ai: { provider: r.provider || '', model: r.model || '' } };
}
// a tool's result read by the AI: its conclusion first, and better-written drafts (the local result stays when it cannot)
async function llmEnhance(svc, action, res, c, input = null, lref = '') {
  if (!LLM.ask || !res || typeof res !== 'object' || ['empty', 'download', 'media', 'link'].includes(res.kind)) return res;
  const compact = compactResult(res, lblOf); if (!compact) return res;
  const drafts = draftsOf(res).length;
  try {
    const account = c.tenant ? await awareBrief(c, { lite: true }).catch(() => '') : ''; // v3.20: the account as it is now
    const r = await LLM.ask({ fn: 'ui.service.enhance', ...(lref ? { ref: lref } : {}), messages: [{ role: 'user', content: enhancePrompt({ lang: LANG.cur, service: L(svc.n), action: actLabel(action), office: { name: c.tenant?.name || '' }, result: compact, drafts, input, key: (svc.share || svc.id) + '.' + action, team: teamBrief(svc.t, getP(), r => ROLES[r]?.[1] || r), account }) }], json: true, tier: 'standard', temperature: 0.3, max_tokens: drafts ? 3000 : 700 });
    let o = r.data; if (!o) { try { o = JSON.parse(String(r.text || '').replace(/^```(?:json)?\s*/i, '').replace(/```\s*$/, '')); } catch { o = null; } }
    return applyEnhance(res, o, ['خلاصة الفريق الذكي', 'AI team summary', 'Synthèse de l’équipe IA']);
  } catch { return res; }
}

// v3.16: a country's regions in the reader's language (lib/geo/<code>.json) — the example of a country without a ready list
// of cities names its cities after them; nothing waits more than a few seconds for it
const GEO_FILES = new Map();
export async function geoFile(cc) {
  const c = String(cc || '').toUpperCase(); if (!/^[A-Z]{2}$/.test(c)) return null; if (GEO_FILES.has(c)) return GEO_FILES.get(c);
  let out = null;
  try { if (typeof fetch === 'function' && typeof location !== 'undefined') { const ctl = typeof AbortController === 'function' ? new AbortController() : null; const tm = ctl ? setTimeout(() => ctl.abort(), 4000) : null; try { const r = await fetch((CFG.root || './') + 'lib/geo/' + c + '.json', ctl ? { signal: ctl.signal } : {}); if (r.ok) out = await r.json(); } finally { if (tm) clearTimeout(tm); } } } catch { out = null; }
  if (out && Array.isArray(out.r)) GEO_FILES.set(c, out); return out && Array.isArray(out.r) ? out : null;
}
// v3.33.29 (the owner, 2026-10-28: «المعاينة (مثال) حسب الدولة» — an example prospect in Dubai had no emirate): the region (emirate, governorate, state…) a city
// belongs to, from the lists shipped with the site — «Dubai» in the UAE → «دبي». A place that is itself one of the country's regions (an example made from them) is its own.
export async function regionNameOf(cc, city) {
  const c = String(cc || '').toUpperCase(), name = String(city || '').trim(); if (!/^[A-Z]{2}$/.test(c) || !name) return '';
  const g = await geoFile(c).catch(() => null); if (!g) return '';
  const f = await placesFile(c).catch(() => null); const i = f ? cityIndex(f, name) : -1; const code = i >= 0 ? f.c[i][4] : '';
  const row = (code && g.r.find(x => x[0] === code)) || g.r.find(x => !x[3] && [x[1], x[4], x[5], x[6], regionLabel(x)].some(v => v && foldName(v) === foldName(name)));
  return row ? regionLabel(row) : '';
}
// an example partner kept from an older version: its prospects were made before they were «from the map» (locked) and before they carried their emirate
async function upgradeExample(T) {
  const rows = rowsOf(T.id, 'p_leads').map(r => ({ ...r })); if (!rows.length) return; const before = JSON.stringify(rows);
  for (const r of rows) if (!r.src) r.src = 'map';
  await fillRegions({ p_leads: rows }, T.demo_cc || T.country);
  if (JSON.stringify(rows) !== before) saveRows(T.id, 'p_leads', rows);
}
// the example rows that carry a city and have a region to fill get it, whatever the country
async function fillRegions(data, cc) {
  for (const [coll, list] of Object.entries(data || {})) {
    if (coll.startsWith('_') || !Array.isArray(list) || !fieldsOf(coll).some(f => f.key === 'region')) continue;
    const memo = new Map();
    for (const r of list) { if (!r || typeof r !== 'object' || r.region || !r.city) continue; if (!memo.has(r.city)) memo.set(r.city, await regionNameOf(cc, r.city).catch(() => '')); const n = memo.get(r.city); if (n) r.region = n; }
  }
}
// one region's name for the reader: its name in Arabic, English or French when given, else (any other language) the
// translation of its English or official name, else the official name
// the time zone of a region (lib/geo, from the tz database) when the country has several — from the regions already loaded
export function regionZone(cc, name) { const g = GEO_FILES.get(String(cc || '').toUpperCase()); if (!g) return ''; const x = String(name || '').trim().toLowerCase(); const row = g.r.find(r => [r[1], r[4], r[5], r[6], regionLabel(r)].some(v => v && String(v).toLowerCase() === x)); return row ? (row[7] || '') : ''; }
export const regionLabel = row => { if (!Array.isArray(row)) return ''; const [, local, , , ar, en, fr] = row; const i = li(); if (isBaseLang(LANG.cur)) return (i === 0 ? ar : i === 2 ? (fr || en) : en) || (i === 0 ? tr0(en || local, 'ar') : '') || en || local; return tr(en || local); };
const tr0 = s => s; // (Arabic names of the regions not written in the source come from the translation engine's Arabic pack, v3.16 server side)
async function regionNames(cc) { const g = await geoFile(cc); if (!g) return []; return g.r.filter(x => !x[3]).slice(0, 8).map(regionLabel).filter(Boolean); }
const DEMO_HAS = cc => DEMO_CC.has(cc);
const OPS = {
  // ---- system
  'system.ping': () => ({ pong: true, mode: 'demo', version: VERSION, at: nowIso() }),
  'platform.bootstrap': (p, c) => bootData(c),

  // ---- auth
  'auth.status': () => ({ has_owner: users().some(u => u.app === 'developer' && u.role === 'owner') }),
  'auth.setup': async (p, c) => {
    if (c.app !== 'developer') fail('forbidden');
    if (users().some(u => u.app === 'developer' && u.role === 'owner')) fail('owner_exists');
    if (String(p.password || '').length < pwMin()) fail('validation', { password: 'short' });
    const email = String(p.email || '').trim().toLowerCase(); if (!/^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/.test(email)) fail('validation', { email: 'email' });
    const salt = randomHex(12); const u = { id: uid('u'), app: 'developer', tenant: 'platform', role: 'owner', name: String(p.name || '').slice(0, 80), email, phone: '', salt, hash: await hashPassword(p.password, salt), status: 'active', created: nowIso() };
    saveUsers([...users(), u]); const token = issueToken(u, 'developer');
    audit({ ...c, user: u }, { op: 'auth.setup' });
    return { token, user: publicUser(u) };
  },
  'auth.register': async (p, c) => {
    if (['developer', 'site', 'demo', 'status'].includes(c.app)) fail('forbidden');
    if (String(p.password || '').length < pwMin()) fail('validation', { password: 'short' });
    if (!String(p.name || '').trim()) fail('validation', { name: 'required' });
    const { T, email, phone } = createTenantAndUser(p, c.app);
    if (c.app !== 'partner' && T.audience !== 'partner') {
      const plans = rowsOf('platform', 'plans').filter(x => x.audience === T.audience && x.active !== false);
      if (plans.length && !plans.some(x => x.code === T.plan)) T.plan = plans.sort((a, b) => (a.sort || 0) - (b.sort || 0))[0].code;
    }
    // v3.13.2: a partner's referral link counts within the programme's ownership days from the visitor's first click
    { const own = +partnerCfg(getP(), R).ownership_days || 0; const refAt = Date.parse(String(p.ref_at || '')); if (T.attribution && own > 0 && Number.isFinite(refAt) && Date.now() - refAt > own * DAY) T.attribution = ''; }
    let viaCoupon = false; // (the owner set that coupon's partner himself: it stands even before that partner's account exists)
    if (p.coupon) { const cp = rowsOf('platform', 'coupons').find(x => x.code?.toLowerCase() === String(p.coupon).toLowerCase() && x.active !== false); if (cp) { T.coupon = cp.code; if (cp.partner_code) T.attribution = cp.partner_code; viaCoupon = !!cp.partner_code; } } // (v3.22: a partner's coupon credits him over any link — the partner terms say so)
    if (RUNTIME.server && !(p.agree === true || p.agree === 'on')) fail('validation', { agree: 'required' });
    const at = p.attribution && typeof p.attribution === 'object' ? p.attribution : {}; const utm = Object.fromEntries(['source', 'medium', 'campaign', 'content', 'term', 'landing', 'referrer', 'first_at', 'gclid', 'fbclid', 'ttclid', 'sccid', 'msclkid', 'wbraid', 'gbraid', 'click_at'].filter(k => at[k]).map(k => [k, String(at[k]).slice(0, 200)])); if (Object.keys(utm).length) T.utm = utm;
    if (p.offer) { const f = findOffer(String(p.offer)); if (f && !f.expired && (!T.attribution || T.attribution === f.partner.code)) { T.offer = f.offer.id; T.attribution ||= f.partner.code; const h = Math.max(0, Math.min(+f.offer.trial_hours || 0, +partnerCfg(getP(), R).max_trial_hours || 0)); if (h > 0 && !(Date.parse(T.trial_end) >= Date.now() + h * 3600e3)) T.trial_end = new Date(Date.now() + h * 3600e3).toISOString(); } else if (!f && isHostedNow()) T.offer = String(p.offer).slice(0, 40); } // (on a host the server checks the offer: this browser does not hold the partners; v3.22: the offer's trial hours are kept — the trial lasts at least that long, as the offer page tells the office)
    // v3.13.2: only a partner that exists and is active is credited (on a host the server checks it); v3.22: never one who asked
    // to leave, by his coupon either
    if (T.attribution && !isHostedNow()) { const pt = tenants().find(x => x.app === 'partner' && x.code === T.attribution); if (pt ? leaving(pt) || (!viaCoupon && ['suspended', 'deleted'].includes(pt.status)) : !viaCoupon) T.attribution = ''; }
    // v3.22: the rate and months this account will earn its partner, as the programme has them today — kept with it
    delete T.partner_terms; if (T.attribution) T.partner_terms = termsNow(partnerCfg(getP(), R));
    const salt = randomHex(12);
    const u = { id: uid('u'), app: c.app, tenant: T.id, role: 'owner', name: String(p.name).slice(0, 80), email, phone, salt, hash: await hashPassword(p.password, salt), status: 'active', created: nowIso(), lang: LANG.cur, ...(p.agree === true || p.agree === 'on' ? { terms_at: nowIso(), terms_v: String(p.terms_v || '').slice(0, 40) } : {}) };
    saveTenants([...tenants(), T]); saveUsers([...users(), u]);
    // v3.5: a builder company and a provider list their owner in their team too (their «team» screen used to start empty)
    if (['app', 'builders', 'providers'].includes(c.app)) saveRows(T.id, 'team', [{ id: uid('r'), created: nowIso(), name: u.name, role: 'owner', phone, email, status: 'active' }]);
    if (!isHostedNow()) BILL.accrueOnRegister(T); // v3.13.2: the partner's trial bonus, when the developer set one (the server's on a host)
    const token = issueToken(u, c.app); audit({ ...c, user: u, tenant: T }, { op: 'auth.register' });
    return { token, user: publicUser(u), tenant: T };
  },
  'auth.login': async (p, c) => {
    const email = String(p.email || '').trim().toLowerCase();
    const fails = store.get('loginfail', {}); const f = fails[c.app + ':' + email];
    if (f && f.n >= 5 && Date.now() - f.at < 10 * 60e3) fail('rate_limited');
    const u = users().find(x => x.app === c.app && (x.email === email || (x.phone && x.phone === latinDigits(p.email).replace(/[^\d+]/g, ''))));
    const ok = u && u.hash === await hashPassword(String(p.password || ''), u.salt);
    if (!ok) { fails[c.app + ':' + email] = { n: (f && Date.now() - f.at < 10 * 60e3 ? f.n : 0) + 1, at: Date.now() }; store.set('loginfail', fails); fail('wrong_login'); }
    if (u.status === 'inactive') fail('forbidden');
    if (R.staffExpired(u)) fail('access_expired', { until: new Date(+u.until).toISOString() }); // v3.31
    delete fails[c.app + ':' + email]; store.set('loginfail', fails);
    if (RUNTIME.server && needsLoginCode(u, c.app)) return startLoginCode(u, c); // v2.5.2: P.security.login_code is enforced on a server
    const token = issueToken(u, c.app); audit({ ...c, user: u }, { op: 'auth.login' });
    return { token, user: publicUser(u), tenant: tenants().find(x => x.id === u.tenant) || null };
  },
  'auth.logout': (p, c, token) => { const tokens = store.get('tokens', {}); delete tokens[token]; store.set('tokens', tokens); return { ok: true }; },
  'auth.me': (p, c) => { needUser(c); return { user: publicUser(c.user), tenant: withBrand(c.tenant), imp: c.imp }; },
  'auth.demo': async (p, c) => {
    // v3.26: the showcase — an example of the administration itself, in this visitor's browser only (what he changes stays here)
    if (SHOW && c.app === 'developer') {
      const lang0 = knownLang(p.lang) ? p.lang : 'ar'; let u0 = users().find(x => x.app === 'developer' && x.demo && x.status !== 'inactive');
      if (!u0) { u0 = { id: uid('u'), app: 'developer', tenant: 'platform', role: 'owner', name: ({ ar: 'مالك النظام', en: 'System owner', fr: 'Propriétaire du système' })[lang0] || 'System owner', email: `demo-admin-${randomHex(5)}@example.com`, phone: '', salt: '', hash: '!', status: 'active', created: nowIso(), demo: true }; saveUsers([...users(), u0]); }
      return { token: issueToken(u0, 'developer', null, 1), user: publicUser(u0), tenant: null };
    }
    if (!['app', 'partner', 'builders', 'providers', 'console'].includes(c.app)) fail('forbidden');
    const lang = knownLang(p.lang) ? p.lang : 'ar';
    // v3.16: the example of the visitor's country (its people, cities, money and phone numbers) in his language
    const HOMES = { ar: 'SA', en: 'AE', fr: 'FR' }; const P0 = getP();
    const cc0 = String(p.country || '').trim().toUpperCase(); const cc = R.WORLD[cc0] && countryOpen(cc0, rowsOf('platform', 'countries'), P0) ? cc0 : (HOMES[lang] || (R.WORLD[P0.default_country] ? P0.default_country : 'SA'));
    const sandbox = RUNTIME.server && getP().demo_mode === 'sandbox';
    // v3.33.31 (the owner, 2026-10-28: «معاينة واجهات المشتركين حسب كل باقة»): an example of ONE plan — the marketer opens the subscriber's interface as that plan shows it (?example=1&plan=CODE)
    const planWanted = (() => { const w = String(p.plan || '').trim().slice(0, 40); return w && ['app', 'builders', 'providers'].includes(c.app) && rowsOf('platform', 'plans').some(x => x.code === w && x.audience === audienceOf(c.app) && x.active !== false) ? w : ''; })();
    const mkEx = SHOW && c.app === 'partner'; // v3.30: the buyers' preview of the marketers' interface — one example marketer for each edition (office / developer)
    const pPrice = code => { const pl = rowsOf('platform', 'plans').find(x => x.audience === 'office' && x.code === code); const b = +pl?.base_price || 0; return b > 0 ? Math.round(b * (1 - Math.max(0, Math.min(90, +pl?.discount_pct || +pl?.discount || 0)) / 100) * 100) / 100 : 0; }; // (v3.33.42: the example marketer's commissions are made of the platform's own rate and plan prices)
    let T = sandbox ? null : tenants().find(x => x.demo && x.app === c.app && x.demo_lang === lang && (x.demo_cc || x.country) === cc && (!mkEx || (x.demo_kind || 'office') === SHOW_KIND) && (x.demo_plan || '') === planWanted), u;
    // v3.16.2: one example per type, language AND country, each under its own address — the same browser opening the example
    // of a second country (or keeping one from an older version) no longer collides with the first («موجود مسبقًا»); an
    // example left half-made (its account without its office) is taken up or made again, never refused
    const email0 = sandbox ? `demo-${c.app}-${lang}-${randomHex(5)}@example.com` : `demo-${c.app}${mkEx ? '-' + SHOW_KIND : ''}${planWanted ? '-p' + planWanted.replace(/[^a-z0-9]/gi, '').toLowerCase() : ''}-${lang}-${cc.toLowerCase()}@example.com`;
    if (!sandbox && !T) { const left = users().find(x => x.app === c.app && x.email === email0); const lt = left && tenants().find(x => x.id === left.tenant); if (lt?.demo) T = lt; else if (left?.demo) saveUsers(users().filter(x => x.id !== left.id)); }
    // v3.33.43 (the owner, 2026-10-30: the offices of the marketer's preview were still family names): an example kept in this browser from an older version is made again once —
    // its offices, visits, offers and commissions — so what was kept earlier never stays on the screen
    if (T && c.app === 'partner' && !sandbox && (T.demo_gen || 0) < 3) {
      try {
        const regions0 = (HOMES[lang] === cc || DEMO_HAS(cc)) ? [] : await regionNames(cc); const nat0 = (() => { try { return new Intl.DisplayNames([locale()], { type: 'region' }).of(cc) || ''; } catch { return ''; } })();
        const d0 = sampleData('partner', lang, T, { cc, tr, regions: regions0, fx: fxOf(P0), nat: nat0, own: mkEx ? SHOW_KIND : '', rate: +P0.partner?.commission_rate || 0, prices: { basic: pPrice('basic'), advanced: pPrice('advanced'), enterprise: pPrice('enterprise') } });
        await fillRegions(d0, cc); for (const k of ['p_leads', 'p_visits', 'p_offers', 'p_commissions']) if (Array.isArray(d0[k])) saveRows(T.id, k, d0[k]);
        T.demo_gen = 3; saveTenants(tenants().map(x => x.id === T.id ? T : x));
      } catch { /* the example stays as it was */ }
    }
    if (T && c.app === 'partner') { try { await upgradeExample(T); } catch { /* the example stays as it was */ } } // v3.33.29: an example kept from an older version takes the map's lock and its emirate
    if (T) { u = users().find(x => x.tenant === T.id && x.status !== 'inactive'); if (!u) { u = { id: uid('u'), app: c.app, tenant: T.id, role: 'owner', name: 'Demo', email: users().some(x => x.app === c.app && x.email === email0) ? `demo-${c.app}-${lang}-${randomHex(5)}@example.com` : email0, phone: '', salt: '', hash: '!', status: 'active', created: nowIso(), demo: true }; saveUsers([...users(), u]); } if (!T.demo_cc) { T.demo_cc = cc; saveTenants(tenants().map(x => x.id === T.id ? T : x)); } }
    if (!T) {
      const country = cc;
      const plans = rowsOf('platform', 'plans').filter(x => x.audience === audienceOf(c.app));
      const plan = planWanted || (plans.find(x => x.code === 'advanced') || plans.sort((a, b) => (b.sort || 0) - (a.sort || 0))[0] || {}).code || '';
      const made = createTenantAndUser({ name: 'Demo', email: email0, company: t('sample_data'), plan, country }, c.app, { demo: true, tenant: { demo_lang: lang, status: 'active', ...(sandbox ? { demo_sandbox: true, demo_expires: new Date(Date.now() + DAY).toISOString() } : {}) } });
      T = made.T; T.demo_cc = cc; T.demo_gen = 3; if (planWanted) T.demo_plan = planWanted; T.name = ({ app: { ar: 'مكتب الريم العقاري', en: 'Al Reem Realty', fr: 'Agence Lumière' }, builders: { ar: 'شركة الأفق للتطوير', en: 'Horizon Developments', fr: 'Horizon Promotion' }, providers: { ar: 'نخبة الصيانة', en: 'Elite Maintenance', fr: 'Élite Maintenance' }, partner: { ar: 'فيصل الشمري', en: 'Faisal Al Shammari', fr: 'Julien Martin' }, console: { ar: 'استوديو المطورين', en: 'Dev Studio', fr: 'Studio Dev' } }[c.app] || {})[lang] || T.name; // an example account reads like a real one (the banner says it is an example)
      if (!['ar', 'en', 'fr'].includes(lang)) T.name = tr(({ app: 'Al Reem Realty', builders: 'Horizon Developments', providers: 'Elite Maintenance', partner: 'Faisal Al Shammari', console: 'Dev Studio' })[c.app] || T.name);
      const regions = (HOMES[lang] === cc || DEMO_HAS(cc)) ? [] : await regionNames(cc);
      const nat = (() => { try { return new Intl.DisplayNames([locale()], { type: 'region' }).of(cc) || ''; } catch { return ''; } })();
            const data = sampleData(c.app, lang, T, { cc, tr, regions, fx: fxOf(P0), nat, own: mkEx ? SHOW_KIND : '', rate: +P0.partner?.commission_rate || 0, prices: { basic: pPrice('basic'), advanced: pPrice('advanced'), enterprise: pPrice('enterprise') } });
      await fillRegions(data, cc); // v3.33.29: the example's places carry their emirate / region too
      for (const e of data.hr_employees || []) if (String(e.email || '').toLowerCase() === `demo-${c.app}-${lang}@example.com`.toLowerCase()) e.email = made.email; // (the owner is still his own employee record: «my attendance», «my leave»)
      const owner0 = HOMES[lang] === cc ? ({ ar: 'فيصل الشمري', en: 'Faisal Al Shammari', fr: 'Julien Martin' })[lang] : (data.team?.[0]?.name || data.hr_employees?.[0]?.name || 'Demo');
      if (c.app === 'partner' && HOMES[lang] !== cc) T.name = owner0;
      u = { id: uid('u'), app: c.app, tenant: T.id, role: 'owner', name: owner0, email: made.email, phone: '', salt: '', hash: '!', status: 'active', created: nowIso(), demo: true };
      saveTenants([...tenants(), T]); saveUsers([...users(), u]);
      for (const [coll, list] of Object.entries(data)) {
        if (coll === '_platform') { const flag = `demo_platform:${c.app}:${lang}`; if (sandbox && store.get(flag)) continue; store.set(flag, true); for (const [pc, pl] of Object.entries(list)) saveRows('platform', pc, [...rowsOf('platform', pc), ...pl]); continue; }
        if (coll === '_store') { for (const [k, v] of Object.entries(list)) store.set(k.replace('{t}', T.id), v); continue; }
        // private examples get their own client-link tokens (sample links never open another visitor's copy)
        if (sandbox && Array.isArray(list)) for (const r of list) for (const f of ['token', 'portal_token']) if (typeof r[f] === 'string' && r[f].startsWith('demo')) r[f] += randomHex(4);
        saveRows(T.id, coll, list);
      }
      if (SHOW && ['app', 'builders'].includes(c.app)) REF.seedProgramme(T, lang); // v3.30: the example business already takes marketers — the programme, two ads, two marketers
      if (mkEx) { // the example marketer works for the visitor's example business of his edition (his own, if he opened it; else made now)
        const bizApp = SHOW_KIND === 'builder' ? 'builders' : 'app'; const alive = x => !(x.demo_expires && Date.parse(x.demo_expires) < Date.now());
        const B = tenants().filter(x => x.demo && x.app === bizApp && x.demo_lang === lang && (x.demo_cc || x.country) === cc && alive(x)).sort((a1, a2) => String(a2.created || '').localeCompare(String(a1.created || '')))[0] || (await OPS['auth.demo'](p, { ...c, app: bizApp })).tenant;
        T.demo_biz = B.id; T.demo_kind = SHOW_KIND; saveTenants(tenants().map(x => x.id === T.id ? T : x));
        REF.exampleMarketer(B, T, u, lang);
      }
    }
    const token = issueToken(u, c.app, null, 1); // example sessions last a day
    return { token, user: publicUser(u), tenant: T };
  },
  'auth.reset': async (p, c) => {
    const email = String(p.email || '').trim().toLowerCase().slice(0, 120);
    // v3.2 (no server): the account lives in this browser, so the reset link opens here at once — nothing waits for an e-mail
    if (!RUNTIME.server) { const u0 = users().find(x => x.app === c.app && x.email === email && x.status !== 'inactive'); if (!u0) return { queued: true }; const tok0 = randomHex(24); const rs = store.get('resets', {}); const now0 = Date.now(); for (const [k, v] of Object.entries(rs)) if (v.exp < now0 || v.uid === u0.id) delete rs[k]; rs[await sha256(tok0)] = { uid: u0.id, app: c.app, exp: now0 + 3600e3 }; store.set('resets', rs); return { local: true, path: '#/reset/' + tok0 }; }
    // v2.5.2: a one-hour link; the answer is the same whether or not the address exists (no account probing).
    // The job belongs to the platform (never shown to the account), and only the automation sends it.
    const u = users().find(x => x.app === c.app && x.email === email && x.status !== 'inactive');
    if (u) {
      const tok = randomHex(24); const resets = store.get('resets', {}); const now = Date.now();
      for (const [k, v] of Object.entries(resets)) if (v.exp < now || v.uid === u.id) delete resets[k];
      resets[await sha256(tok)] = { uid: u.id, app: c.app, exp: now + 3600e3 }; store.set('resets', resets);
      queueJob({ ...c, user: null, tenant: null }, { service: 'auth', action: 'password_reset', input: { email, path: '#/reset/' + tok, lang: knownLang(u.lang) ? u.lang : LANG.cur } });
    }
    return { queued: true };
  },
  'auth.password': async (p, c) => {
    needUser(c); if (String(p.password || '').length < pwMin()) fail('validation', { password: 'short' });
    const list = users(); const u = list.find(x => x.id === c.user.id);
    if (!u.demo && u.hash !== await hashPassword(String(p.current || ''), u.salt)) fail('wrong_login');
    u.salt = randomHex(12); u.hash = await hashPassword(p.password, u.salt); saveUsers(list); audit(c, { op: 'auth.password' }); return { ok: true };
  },
  'auth.invite': async (p, c) => {
    needPerm(c, 'accounts'); const P = getP(); const role = p.role !== 'owner' && (p.role in R.DEV_ROLES || p.role in (P.dev_roles || {})) ? p.role : p.role === 'owner' && c.user.role === 'owner' ? 'owner' : 'viewer';
    const g = staffGrant(c, role, p, true);
    const code = 'inv_' + randomHex(12); const inv = store.get('invites', []);
    inv.unshift({ code, role, name: String(p.name || '').slice(0, 80), email: String(p.email || '').toLowerCase().trim(), exp: Date.now() + 3 * DAY, by: c.user.id, ...g });
    store.set('invites', inv); audit(c, { op: 'auth.invite', path: 'role:' + role }); return { code };
  },
  'auth.accept': async (p, c) => {
    const inv = store.get('invites', []); const i = inv.findIndex(x => x.code === p.code && x.exp > Date.now());
    if (i < 0) fail('not_found'); if (String(p.password || '').length < pwMin()) fail('validation', { password: 'short' });
    const x = inv[i]; if (users().some(u => u.app === 'developer' && u.email === x.email)) fail('exists');
    if (+x.until > 0 && +x.until <= Date.now()) fail('access_expired', { until: new Date(+x.until).toISOString() });
    const salt = randomHex(12); const u = { id: uid('u'), app: 'developer', tenant: 'platform', role: x.role, name: p.name || x.name, email: x.email, phone: '', salt, hash: await hashPassword(p.password, salt), status: 'active', created: nowIso(), ...(x.access ? { access: x.access } : {}), ...(+x.until > 0 ? { until: +x.until } : {}) };
    saveUsers([...users(), u]); inv.splice(i, 1); store.set('invites', inv); const token = issueToken(u, 'developer');
    audit({ ...c, user: u }, { op: 'auth.accept' }); return { token, user: publicUser(u) };
  },

  // ---- data
  'data.list': (p, c) => {
    const coll = String(p.coll || ''); if (!entSpec(coll)) fail('not_found');
    guardCollection(c, coll, false);
    const t0 = isPlatformColl(coll) ? 'platform' : c.tenant.id;
    let list = coll === 'p_commissions' && c.tenant ? ripenCommissions(c.tenant.id) : rowsOf(t0, coll);
    if (coll === 'market_requests' && c.user?.app !== 'developer') {
      list = list.filter(r => (r.status === 'open' || r.tenant === c.tenant?.id) && (!!r.demo === !!c.tenant?.demo) && (!r.demo || !r.demo_lang || r.demo_lang === c.tenant?.demo_lang)).map(({ tenant, ...r }) => ({ ...r, mine: tenant === c.tenant?.id }));
      const cats = c.tenant?.categories || (c.tenant?.category ? [c.tenant.category] : []); // chosen in the first-run questions
      if (cats.length && !p.sort) list = [...list.filter(r => cats.includes(r.category)), ...list.filter(r => !cats.includes(r.category))];
    }
    if (coll === 'legal' || coll === 'faq' || coll === 'books' || coll === 'assets') list = list.filter(r => !p.lang || !r.lang || r.lang === p.lang);
    if (selfOnly(c, coll)) { const me = selfName(c); list = list.filter(r => r.employee === me); }
    // v3.5: an owner's number of properties is counted from the properties (by phone or name), never typed
    if (coll === 'owners' && c.tenant) { const props = rowsOf(c.tenant.id, 'properties'); const ph = x => latinDigits(x || '').replace(/\D/g, '').slice(-9); list = list.map(o => ({ ...o, properties_count: props.filter(pp => (o.phone && ph(pp.owner_phone) && ph(pp.owner_phone) === ph(o.phone)) || (o.name && String(pp.owner_name || '').trim() === String(o.name).trim())).length })); }
    return listRows(list, p);
  },
  'data.get': (p, c) => { guardCollection(c, p.coll, false); const r = rowsOf(tenantKey(c, p.coll), p.coll).find(x => x.id === p.id); if (!r || (selfOnly(c, p.coll) && r.employee !== selfName(c))) fail('not_found'); return r; },
  'data.create': (p, c) => {
    const coll = String(p.coll || ''); if (!entSpec(coll)) fail('not_found'); guardCollection(c, coll, true); noLooseListing(c, coll); if (coll === 'legal') legalWhole(p.row);
    if (selfOnly(c, coll)) { if (coll !== 'hr_leaves') fail('forbidden'); p = { ...p, row: { ...(p.row || {}), employee: selfName(c), status: 'pending', approver: '' } }; }
    // v3.5: an invoice or a contract made without a number gets the next one (INV-2026-008); an invoice without its tax gets
    // the country's rate on its amount — from a form, the assistant or an import alike
    const NUM_PRE = { invoices: 'INV', contracts: 'CT' }[coll];
    if (NUM_PRE && c.tenant && !String(p.row?.number ?? '').trim()) { const y = new Date().getFullYear(); const re = new RegExp(`^${NUM_PRE}-${y}-(\\d+)$`); const n = Math.max(0, ...rowsOf(c.tenant.id, coll).map(r => +((re.exec(String(r.number || '')) || [])[1] || 0))); p = { ...p, row: { ...(p.row || {}), number: `${NUM_PRE}-${y}-${String(n + 1).padStart(3, '0')}` } }; }
    if (coll === 'invoices' && c.tenant && (p.row?.tax === '' || p.row?.tax == null) && +latinDigits(String(p.row?.amount ?? '')).replace(/[^\d.]/g, '') > 0) { const rate = +(countryBy(c.tenant.country, rowsOf('platform', 'countries'), getP())?.tax_rate || 0); if (rate > 0) p = { ...p, row: { ...p.row, tax: Math.round(+latinDigits(String(p.row.amount)).replace(/[^\d.]/g, '') * rate) / 100 } }; }
    const { row, errors } = cleanRow(typedFields(coll), p.row || {}); if (Object.keys(errors).length) fail('validation', errors);
    // v3.5: what a person did not choose starts at the record's first step (a property «available», a lead «new»), switched on
    for (const f of fieldsOf(coll)) { if (f.type === 'sel' && ['status', 'stage'].includes(f.key) && (row[f.key] == null || row[f.key] === '') && f.options?.length) row[f.key] = f.options[0]; if (f.type === 'bool' && ['active', 'enabled'].includes(f.key) && !(f.key in (p.row || {}))) row[f.key] = true; }
    const tk = tenantKey(c, coll); const list = rowsOf(tk, coll);
    const lim = LIMIT_COLL[coll] && planLimits(c)[LIMIT_COLL[coll]]; if (lim && realCount(list) >= lim) fail('limit_reached', { limit: lim, key: LIMIT_COLL[coll] });
    const rec = { id: uid('r'), created: nowIso(), updated: nowIso(), by: c.user?.id || null, ...row };
    list.unshift(rec); saveRows(tk, coll, list); audit(c, { op: 'create', coll, rid: rec.id, after: summarize(rec) });
    if (EVENT_OF[coll]) emitEvent(c, EVENT_OF[coll], rec);
    if (coll === 'p_visits' && !isHostedNow()) BILL.visitBonus(c, rec); // v3.13.2: the meeting bonus waits for the developer's review (the server's on a host)
    if (!isPlatformColl(coll)) { EXT.afterWrite(c, coll, rec, null); return rowsOf(tk, coll).find(x => x.id === rec.id) || rec; }
    return rec;
  },
  'data.update': (p, c) => {
    const coll = String(p.coll || ''); guardCollection(c, coll, true); if (coll === 'legal' && p.row && 'doc' in p.row) legalWhole(p.row);
    const tk = tenantKey(c, coll); const list = rowsOf(tk, coll); const i = list.findIndex(x => x.id === p.id); if (i < 0) fail('not_found');
    const { row, errors } = cleanRow(typedFields(coll), p.row || {}, true); if (Object.keys(errors).length) fail('validation', errors);
    if (coll === 'p_leads') { const bad = leadViolations(list[i], row); if (bad.length) fail('validation', Object.fromEntries(bad.map(k => [k, 'locked']))); } // v3.33.29: an office taken from the map keeps the map's data (assets/lead-lock.js)
    if (selfOnly(c, coll)) { const own = list[i].employee === selfName(c); if (coll !== 'hr_leaves' || !own || list[i].status !== 'pending' || (row.status && !['pending', 'cancelled'].includes(row.status)) || 'employee' in row || 'approver' in row) fail('forbidden'); }
    if (coll === 'hr_leaves' && row.status && row.status !== list[i].status && ['approved', 'rejected'].includes(row.status)) row.approver = c.user?.name || '';
    const before = list[i]; list[i] = { ...before, ...row, updated: nowIso() }; saveRows(tk, coll, list);
    const undoRow = isPlatformColl(coll) ? { coll, id: p.id, row: Object.fromEntries(Object.keys(row).map(k => [k, before[k] ?? ''])) } : null;
    const aid = audit(c, { op: 'update', coll, rid: p.id, before: summarize(before, row), after: summarize(list[i], row), undo_row: undoRow });
    if (undoRow) return { ...list[i], _audit: aid };
    if (coll === 'deals' && row.stage === 'closed' && before.stage !== 'closed') emitEvent(c, 'deal_won', list[i]);
    if (coll === 'invoices' && row.status === 'paid' && before.status !== 'paid') emitEvent(c, 'invoice_paid', list[i]);
    EXT.afterWrite(c, coll, list[i], before);
    return rowsOf(tk, coll).find(x => x.id === p.id) || list[i];
  },
  'data.delete': (p, c) => {
    const coll = String(p.coll || ''); guardCollection(c, coll, true); noLooseListing(c, coll); if (selfOnly(c, coll)) fail('forbidden');
    const ids = Array.isArray(p.ids) ? p.ids : [p.id]; const tk = tenantKey(c, coll); const list = rowsOf(tk, coll);
    const keep = list.filter(x => !ids.includes(x.id)); if (keep.length === list.length) fail('not_found');
    saveRows(tk, coll, keep); if (tk !== 'platform') LEARN.forgetEntities(tk, ids); // v2.6: a deleted record is forgotten by the AI team too
    audit(c, { op: 'delete', coll, rid: ids.join(','), before: { count: list.length - keep.length } }); return { deleted: list.length - keep.length };
  },
  // v3.29 (the owner, 2026-10-15: «واجهات المشترين جامدة وليس فيها حياة» → «فارغة عند أول دخول»): a sold copy opens with a few
  // examples of its own business — an office: owners, listings, clients, deals, visits and tasks; a developer: a project, its
  // units, reservations, stages and clients — each named «… · مثال», left out of the website, the automations and the API by the
  // server, and all removed by one press (only those he has not changed since). Added once per business, never again.
  'starter.status': (p, c) => { needUser(c); return starterState(c); },
  // v3.30 — «نظرة عامة» of the administration: the business's pulse (assets/compute.js pulseInsight). On a host the server answers
  // (dar-solo.php: its business's rows there); here — the buyers' preview, whose example administration lives in the visitor's browser —
  // from the example business of the edition being previewed
  'solo.overview': async (p, c) => {
    needUser(c); if (c.app !== 'developer') fail('forbidden');
    const want = SOLO === 'builder' || PV?.page === 'developers' ? 'builders' : 'app';
    const alive = x => x.status !== 'deleted' && !(x.demo_expires && Date.parse(x.demo_expires) < Date.now());
    let T = tenants().find(x => x.app === want && alive(x)) || tenants().find(x => ['app', 'builders'].includes(x.app) && alive(x));
    // (v3.30: the buyers' preview opened on its administration first — the example business it looks at is made now, once: the same one
    // the business's own page shows later, never a second one on the next visit)
    if (!T && SHOW) T = (await OPS['auth.demo']({ lang: LANG.cur }, { ...c, app: want }))?.tenant || null;
    if (!T) fail('not_found');
    const ctx = computeCtx({ app: T.app, tenant: T, user: { role: 'owner', app: T.app } }, {}); const cc = countryBy(T.country, rowsOf('platform', 'countries'), getP());
    return { ...pulseInsight(ctx), name: T.name || '', currency: cc?.currency || R.WORLD?.[T.country]?.cur || 'SAR', app: T.app, at: nowIso() };
  },
  'starter.add': async (p, c) => {
    needUser(c); if (!SOLO || !c.tenant || !STARTER[c.app] || !['owner', 'admin', 'manager'].includes(c.user.role)) fail('forbidden');
    const T = c.tenant, cfg = STARTER[c.app]; if (store.get(starterKey(T.id), null)) return { added: 0, again: true };
    if (!Object.keys(cfg).every(k => rowsOf(T.id, k).length === 0)) { store.set(starterKey(T.id), { state: 'skipped', at: nowIso() }); return { added: 0, skipped: true }; } // (he already has his own work)
    const lang = knownLang(LANG.cur) ? LANG.cur : 'ar'; const HOMES = { ar: 'SA', en: 'AE', fr: 'FR' };
    const cc = R.WORLD[String(T.country || '').toUpperCase()] ? String(T.country).toUpperCase() : (HOMES[lang] || 'SA');
    const regions = (HOMES[lang] === cc || DEMO_HAS(cc)) ? [] : await regionNames(cc);
    const nat = (() => { try { return new Intl.DisplayNames([locale()], { type: 'region' }).of(cc) || ''; } catch { return ''; } })();
    const data = sampleData(c.app, lang, T, { cc, tr, regions, fx: fxOf(getP()), nat });
    await fillRegions(data, cc);
    const rows = starterRows(c.app, data, c.user.name || '', t('life_example'), c.user.id);
    for (const [coll, list] of Object.entries(rows)) saveRows(T.id, coll, list);
    const n = Object.values(rows).reduce((a, l) => a + l.length, 0); store.set(starterKey(T.id), { state: 'added', at: nowIso(), n });
    audit(c, { op: 'starter.add', path: 'rows:' + n }); return { added: n };
  },
  'starter.remove': (p, c) => {
    needUser(c); if (!SOLO || !c.tenant || !STARTER[c.app] || !['owner', 'admin', 'manager'].includes(c.user.role)) fail('forbidden');
    const T = c.tenant; let n = 0;
    for (const coll of Object.keys(STARTER[c.app])) { const list = rowsOf(T.id, coll); const keep = list.filter(r => !isStarterRow(r)); if (keep.length === list.length) continue; n += list.length - keep.length; saveRows(T.id, coll, keep); LEARN.forgetEntities(T.id, list.filter(isStarterRow).map(r => r.id)); }
    store.set(starterKey(T.id), { state: 'removed', at: nowIso(), n }); audit(c, { op: 'starter.remove', path: 'rows:' + n }); return { removed: n };
  },
  // v3.13.1 — the Undo of a deletion: the record put back as it was (same id, its own fields, each checked again), by someone who
  // may write in that collection — never over a record that exists
  'data.restore': (p, c) => {
    const coll = String(p.coll || ''); if (!entSpec(coll)) fail('not_found'); guardCollection(c, coll, true); noLooseListing(c, coll); if (selfOnly(c, coll)) fail('forbidden');
    const src = p.row && typeof p.row === 'object' && !Array.isArray(p.row) ? p.row : null; const id = String(src?.id ?? '');
    if (!/^[A-Za-z0-9_-]{2,64}$/.test(id)) fail('validation', { id: 'invalid' });
    const tk = tenantKey(c, coll); const list = rowsOf(tk, coll); if (list.some(x => String(x.id) === id)) fail('exists', { id: 'exists' });
    const lim = LIMIT_COLL[coll] && planLimits(c)[LIMIT_COLL[coll]]; if (lim && realCount(list) >= lim) fail('limit_reached', { limit: lim, key: LIMIT_COLL[coll] });
    const { row, errors } = cleanRow(fieldsOf(coll), src, true); if (Object.keys(errors).length) fail('validation', errors);
    const when = v => (typeof v === 'string' && !isNaN(Date.parse(v)) ? v.slice(0, 40) : nowIso());
    const rec = { id, created: when(src.created), updated: nowIso(), by: typeof src.by === 'string' ? src.by.slice(0, 40) : c.user?.id || null, ...row };
    list.unshift(rec); saveRows(tk, coll, list); audit(c, { op: 'restore', coll, rid: id, after: summarize(rec) });
    if (!isPlatformColl(coll)) EXT.afterWrite(c, coll, rec, null);
    return rec;
  },
  'data.bulk': (p, c) => {
    const coll = String(p.coll || ''); if (!entSpec(coll)) fail('not_found'); guardCollection(c, coll, true); noLooseListing(c, coll); if (selfOnly(c, coll)) fail('forbidden');
    const fields = fieldsOf(coll); const tk = tenantKey(c, coll); const list = rowsOf(tk, coll); const bad = [];
    const lim = LIMIT_COLL[coll] && planLimits(c)[LIMIT_COLL[coll]];
    let added = 0;
    for (const [n, input] of (p.rows || []).slice(0, 5000).entries()) {
      if (lim && realCount(list) >= lim) { bad.push({ n, errors: { _: 'limit' } }); continue; }
      const { row, errors } = cleanRow(fields, input); if (Object.keys(errors).length) { bad.push({ n, errors }); continue; }
      list.unshift({ id: uid('r'), created: nowIso(), updated: nowIso(), by: c.user?.id || null, ...row }); added++;
    }
    saveRows(tk, coll, list); audit(c, { op: 'import', coll, after: { added, rejected: bad.length } }); return { added, rejected: bad };
  },
  'settings.get': (p, c) => { needUser(c); return store.get(`set:${c.tenant?.id || 'platform'}:${p.key}`, {}); },
  // v3.13.1 — one account setting changed in part (the assistant's «setting» step, and its Undo with replace:true): merged into what
  // is there, checked like its screen, written through the same operation as its screen (and its permissions)
  'settings.patch': (p, c) => {
    needUser(c); needWritable(c); if (c.user.app === 'developer' || !c.tenant) fail('forbidden');
    const key = String(p.key || ''); const spec = ACCT_SETTINGS[key]; if (!spec) fail('forbidden', { key: 'not_allowed' });
    const v = p.value && typeof p.value === 'object' && !Array.isArray(p.value) ? p.value : null; if (!v) fail('validation', { value: 'required' });
    const before = spec.get(c); const next = spec.clean(p.replace ? { ...v } : { ...before, ...v }, c, before);
    spec.put(next, c); return { key, before, after: spec.get(c) };
  },
  'settings.set': (p, c) => {
    needUser(c); needWritable(c); const key = String(p.key || '');
    if (key === 'autonomy') { if (c.user.app === 'developer' || !['owner', 'admin'].includes(c.user.role)) fail('forbidden'); p = { ...p, value: tenantAutonomy(p.value) }; }
    if (key === 'assist') { if (c.user.app === 'developer' || !c.tenant || !['owner', 'admin'].includes(c.user.role)) fail('forbidden'); p = { ...p, value: cleanAssist(p.value) }; } // v3.13.1
    if (['profile', 'booking', 'hr_policy', 'pond', 'office_page', 'website', 'website_pub'].includes(key) && c.user.app !== 'developer' && !['owner', 'admin', 'manager'].includes(c.user.role) && !(key === 'hr_policy' && c.user.role === 'hr')) fail('forbidden');
    if (key === 'website') { // v3.28 — v3.31: a value sent back as it came from the business's own records stays linked to them
      const v0 = { ...(p.value || {}) }; if (Array.isArray(v0._linked) && c?.tenant) { const pf = webProfile(c.tenant); for (const k of v0._linked) if (WEB_LINKED.includes(k) && String(v0[k] ?? '') === String(pf[k] ?? '')) v0[k] = ''; }
      p = { ...p, value: cleanWebsite(v0) };
    }
    if (key === 'website_pub') fail('forbidden', { key: 'publish_with_website.publish' });
    if (key === 'profile') { // tenant profile -> also updates tenant name/city/country
      const list = tenants(); const T = list.find(x => x.id === c.tenant.id);
      if (p.value?.country && String(p.value.country).toUpperCase() !== T.country) T.country = acceptCountry(p.value.country);
      if (p.value && 'timezone' in p.value) { const z = String(p.value.timezone || '').slice(0, 60); if (z) { try { new Intl.DateTimeFormat('en', { timeZone: z }); } catch { fail('validation', { timezone: 'option' }); } } T.tz = z; } // a city in another zone of a multi-zone country
      for (const k of ['name', 'city', 'region']) if (p.value?.[k]) T[k] = String(p.value[k]).slice(0, 120);
      // v3.33.21: his bank account added at Whop's secure page (the Platform pays through Whop) — nothing more to type here; an IBAN typed is still checked
      if (p.value?.payout_method === 'iban' && !String(p.value.payout_iban || '').trim()) p = { ...p, value: { ...p.value, payout_details: 'bank:whop' } };
      else if (p.value?.payout_method === 'iban') { const ib = ibanCheck(p.value.payout_iban); if (!ib.ok) fail('validation', { payout_iban: 'iban_' + ib.why }); if (!/\S+\s+\S+/u.test(String(p.value.payout_name || '').trim())) fail('validation', { payout_name: 'full_name' }); p = { ...p, value: { ...p.value, payout_iban: ib.iban, payout_details: ibanShow(ib.iban) + ' · ' + String(p.value.payout_name).trim().slice(0, 80) + (p.value.payout_bank ? ' · ' + String(p.value.payout_bank).trim().slice(0, 60) : '') } }; } // v3.33
      // v3.16: a region of a country with several time zones sets the account's zone (when he did not choose one himself)
      if (p.value?.region && !(p.value && 'timezone' in p.value && p.value.timezone)) { const z = regionZone(T.country, p.value.region); if (z) T.tz = z; }
      saveTenants(list);
    }
    if (key === 'white_label' && c.tenant) {
      if (!['owner', 'admin'].includes(c.user.role) && c.user.app !== 'developer') fail('forbidden');
      const v = { ...(p.value || {}) }; const raw = String(v.custom_domain || '').trim(); const host = cleanHost(raw); if (raw && !host) fail('validation', { custom_domain: 'invalid' });
      if (host && tenants().some(x => x.id !== c.tenant.id && x.domain === host)) fail('validation', { custom_domain: 'duplicate' });
      if (host && (getP().hosts || []).concat(getP().domain ? [getP().domain] : []).some(h => host === h || host.endsWith('.' + h))) fail('validation', { custom_domain: 'invalid' });
      v.custom_domain = host; const list = tenants(); const T = list.find(x => x.id === c.tenant.id);
      if ((T.domain || '') !== host) { T.domain = host; T.domain_status = host ? 'pending' : ''; saveTenants(list); if (host) queueJob(c, { service: 'white_label', action: 'domain', input: { host, target: getP().cname_target || '' } }); }
      p = { ...p, value: v };
    }
    store.set(`set:${c.tenant?.id || 'platform'}:${key}`, p.value || {}); audit(c, { op: 'settings', path: key }); return { ok: true };
  },

  // ---- services, jobs, audit, monitoring
  'service.run': (p, c) => {
    needUser(c);
    const P = getP(); const svc = catalog(P).find(s => s.id === p.service && s.app === c.app); if (!svc) fail('not_found');
    const st = access(svc, accessCtx(c)); if (st !== 'ok') fail(st === 'plan' ? 'not_in_plan' : st === 'country' ? 'not_in_country' : 'service_suspended');
    if (!roleAllows(c.app, c.user.role, svc, P)) fail('forbidden', { role: c.user.role });
    const computedAct = (svc.c || []).includes(p.action);
    const local = LOCAL_ACTS[svc.id + '.' + p.action] || (svc.share && LOCAL_ACTS[svc.share + '.' + p.action]);
    if (local) { if (p.preview) return { computed: true, result: null }; const lr = local(p.input || {}, c); return lr && typeof lr.then === 'function' ? lr.then(result => ({ computed: true, result })) : { computed: true, result: lr }; }
    if (computedAct) {
      const ctx = computeCtx(c, p.input || {});
      const res = compute(svc.id, p.action, ctx);
      if (res && res.write && p.preview) return { computed: true, result: null }; // v3.5: a screen's first look never writes
      if (res && res.write) { needWritable(c); for (const w of res.write) OPS['data.create']({ coll: w.coll, row: w.row }, c); delete res.write; }
      return { computed: true, result: res };
    }
    const isAi = (svc.a || []).includes(p.action) || (svc.xa || []).some(x => x.id === p.action);
    if (!isAi) fail('not_found');
    needWritable(c);
    aiAllowance(c);
    const job = queueJob(c, { service: svc.id, action: p.action, input: p.input || {}, ids: p.ids || [], roles: svc.t || [] });
    audit(c, { op: 'job', path: svc.id + '.' + p.action, rid: job.id });
    return { queued: true, job };
  },
  // v2.7: the local AI engine — the action is answered NOW from the account's own records, no provider needed.
  // service.run is unchanged (it queues the job for the linked cloud team); this op never queues and never fails.
  'service.ai': async (p, c) => {
    needUser(c);
    const P = getP(); const svc = catalog(P).find(s => s.id === p.service && s.app === c.app); if (!svc) fail('not_found');
    const st = access(svc, accessCtx(c)); if (st !== 'ok') fail(st === 'plan' ? 'not_in_plan' : st === 'country' ? 'not_in_country' : 'service_suspended');
    if (!roleAllows(c.app, c.user.role, svc, P)) fail('forbidden', { role: c.user.role });
    const isAi = (svc.a || []).includes(p.action) || (svc.xa || []).some(x => x.id === p.action); if (!isAi) fail('not_found');
    if (isExternal(svc.id, p.action)) fail('needs_link'); // only an action with no local executor at all (none left in v3.2)
    // an instant draft shown beside a job the cloud team is already doing: no second AI operation, nothing recorded
    const companion = p.draft_for ? store.get('jobs', []).find(j => j.id === p.draft_for && j.tenant === c.tenant?.id && j.uid === c.user.id && j.service === svc.id && j.action === p.action && ['queued', 'waiting_link', 'running'].includes(j.status) && Date.now() - new Date(j.at) < 10 * 60e3) : null;
    if (p.draft_for && !companion) fail('not_found');
    if (!companion) { needWritable(c); aiAllowance(c); }
    // v3.8: an action with its own instruction follows it (the platform's AI); without an answer the local engine's brief stays
    const xa = !companion && (svc.xa || []).find(x => x.id === p.action && x.prompt);
    // v3.32: the AI calls of this job carry its reference, so its review (👍/👎) reaches the learning (dar-learn.php) — never counted as a turn
    const lref = companion ? '' : 'jb' + Date.now().toString(36) + Math.random().toString(36).slice(2, 10);
    if (xa && LLM.ask) {
      const own = await customAct(svc, xa, c, { ...p, lref }).catch(() => null);
      if (own) { const job = queueJob(c, { service: svc.id, action: p.action, input: p.input || {}, ids: p.ids || [], roles: svc.t || [], engine: 'ai', status: 'done', finished_at: nowIso(), result: liteResult(own), lrn: lref }); audit(c, { op: 'job', path: 'ai:' + svc.id + '.' + p.action, rid: job.id }); return { computed: true, local: false, result: own, job: { id: job.id, status: job.status } }; }
    }
    const ctx = actCtx(c, p.input || {});
    let result = await brain(svc.id, p.action, ctx, svc); if (!result) fail('needs_link');
    if (companion) return { computed: true, local: true, draft: true, result };
    if (p.enhance !== false) result = await llmEnhance(svc, p.action, result, c, p.input || null, lref); // v3.5: the platform's own AI reads the result and writes the drafts
    const job = queueJob(c, { service: svc.id, action: p.action, input: p.input || {}, ids: p.ids || [], roles: svc.t || [], engine: 'local', status: 'done', finished_at: nowIso(), result: liteResult(result), ...(lref && p.enhance !== false && LLM.ask ? { lrn: lref } : {}) });
    audit(c, { op: 'job', path: 'local:' + svc.id + '.' + p.action, rid: job.id });
    return { computed: true, local: true, result, job: { id: job.id, status: job.status } };
  },
  // v2.7: last resort for the worker — when every cloud provider failed, the local engine completes the job (never "failed" for lack of a provider)
  'ai.fallback': async (p, c) => {
    needPerm(c, 'automation'); const j = store.get('jobs', []).find(x => x.id === p.id); if (!j) fail('not_found');
    if (['done', 'failed', 'rejected', 'needs_approval'].includes(j.status)) return j;
    if (!brainHandles(j.service, j.action) || autoCapable(j.service, j.action)) { // only what the local engine genuinely performs (v3.2: a job queued for AUTOMATIC sending stays for the real channel)
      if (!p.error) fail('not_supported');
      // the worker passes the original error: the job closes as failed with it, honestly, in this same call
      return OPS['jobs.complete']({ id: j.id, status: 'failed', error: String(p.error).slice(0, 500), meta: { provider: 'none', engine: 'none', reason: String(p.reason || '').slice(0, 80) } }, c);
    }
    const T = tenants().find(x => x.id === j.tenant); if (!T) fail('not_found');
    const cx = { app: T.app, tenant: T, imp: null, user: { id: 'ai:' + j.id, app: T.app, tenant: T.id, role: 'owner', name: 'AI · local', status: 'active' } };
    const svc = catalog(getP()).find(s => s.id === j.service && s.app === T.app);
    const ctx = computeCtx(cx, j.input || {}); ctx.lang = j.lang || ctx.lang; ctx.listingUrl = id => listingUrl(T, id);
    const result = await brain(j.service, j.action, ctx, svc);
    return OPS['jobs.complete']({ id: j.id, status: 'done', result: liteResult(result), meta: { provider: 'local', engine: 'local', reason: String(p.reason || 'providers_exhausted').slice(0, 80) } }, c);
  },
  'jobs.list': (p, c) => { needUser(c); const all = store.get('jobs', []); return c.user.app === 'developer' ? all : all.filter(j => j.tenant === c.tenant?.id); },
  // workers (n8n): take jobs to perform and report the result — a developer account with the "automation" permission
  'jobs.claim': (p, c) => {
    needPerm(c, 'automation'); const all = store.get('jobs', []); const lim = Math.min(Math.max(+p.limit || 10, 1), 100); const out = [];
    // v2.5.3: oldest first (no starvation); services[]/except[] filters; a job left "running" past its lease (worker crashed) is handed out again, and after 3 tries it fails with a notice
    const only = Array.isArray(p.services) ? p.services.map(String).slice(0, 100) : null; const except = Array.isArray(p.except) ? p.except.map(String).slice(0, 100) : [];
    const lease = Math.min(Math.max(+p.lease_min || 20, 5), 240) * 60e3; const now = Date.now(); const timedOut = [];
    for (let i = all.length - 1; i >= 0; i--) {
      const j = all[i];
      if (j.status === 'running' && j.claimed_at && now - new Date(j.claimed_at) > lease) { if ((+j.attempts || 1) >= 3) { Object.assign(j, { status: 'failed', error: 'worker_timeout', finished_at: nowIso() }); timedOut.push(j); continue; } j.status = 'queued'; }
      if (out.length >= lim || !['waiting_link', 'queued'].includes(j.status)) continue;
      if (p.service && j.service !== p.service) continue; if (p.action && j.action !== p.action) continue; if (only && !only.includes(j.service)) continue; if (except.includes(j.service)) continue;
      j.status = 'running'; j.claimed_at = nowIso(); j.worker = c.user.id; j.attempts = (+j.attempts || 0) + 1; out.push(j);
    }
    store.set('jobs', all);
    for (const j of timedOut) { const T = j.tenant && tenants().find(t => t.id === j.tenant); if (T && j.uid) notify(T.id, { code: 'job_failed', svc: j.service, act: j.action, link: j.service, level: 'bad', to: j.uid, vars: { job: j.id } }); }
    return out;
  },
  'jobs.complete': async (p, c) => {
    needPerm(c, 'automation'); const all = store.get('jobs', []); const j = all.find(x => x.id === p.id); if (!j) fail('not_found');
    if (!['done', 'failed', 'needs_approval'].includes(p.status)) fail('validation', { status: 'invalid' });
    if (['done', 'failed', 'rejected'].includes(j.status)) return j; // v2.5.1: a repeated completion (worker retry) never applies writes or sends notices twice
    if (j.status === 'needs_approval' && p.status !== 'failed') fail('validation', { status: 'awaiting_decision' }); // only the account's decision reopens it
    if (p.status === 'needs_approval') {
      const pr = cleanProposal(p.proposal); if (!pr) fail('validation', { proposal: 'required' });
      Object.assign(j, { status: 'needs_approval', proposal: pr, proposed_at: nowIso() }); store.set('jobs', all); LEARN.onComplete(j, p.meta);
      const T0 = j.tenant && j.tenant !== 'platform' ? tenants().find(x => x.id === j.tenant) : null;
      if (T0) notify(T0.id, { code: 'approval_needed', svc: j.service, act: j.action, link: 'jobs', level: 'warn', ...(j.uid ? { to: j.uid } : {}) });
      audit(c, { op: 'job', path: 'propose:' + j.action, rid: j.id }); return j;
    }
    if (!['done', 'failed'].includes(p.status)) fail('validation', { status: 'invalid' });
    Object.assign(j, { status: p.status, result: p.result ?? null, error: p.error ? String(p.error).slice(0, 500) : null, finished_at: nowIso() });
    store.set('jobs', all); LEARN.onComplete(j, p.meta); // v2.6: a private learning signal in the job's own account (quality, provider, outcome)
    const T = j.tenant && j.tenant !== 'platform' ? tenants().find(x => x.id === j.tenant) : null;
    if (T && p.status === 'done' && Array.isArray(p.writes) && p.writes.length) { // records the AI team produced (validated like any user write)
      const cx = { app: T.app, tenant: T, imp: null, user: { id: 'ai:' + j.id, app: T.app, tenant: T.id, role: 'owner', name: 'AI · ' + (j.action || ''), status: 'active' } }; const applied = [];
      for (const w of p.writes.slice(0, 50)) { try { if (!w || typeof w !== 'object' || R.PLATFORM.includes(w.coll)) fail('forbidden'); const r = w.op === 'update' ? OPS['data.update']({ coll: w.coll, id: w.id, row: w.row || {} }, cx) : OPS['data.create']({ coll: w.coll, row: w.row || {} }, cx); applied.push({ ok: true, coll: w.coll, id: r?.id || w.id }); } catch (e) { applied.push({ ok: false, coll: w?.coll, code: e.code || 'error', extra: e.extra || null }); } }
      const again = store.get('jobs', []); const jj = again.find(x => x.id === j.id); if (jj) { jj.applied = applied; store.set('jobs', again); } j.applied = applied;
    }
    if (T && j.uid && !String(j.action || '').startsWith('webhook:')) notify(T.id, p.notify && typeof p.notify === 'object' ? { level: 'info', ...p.notify, to: p.notify.to || j.uid } : { code: p.status === 'done' ? 'job_done' : 'job_failed', svc: j.service, act: j.action, link: j.service, level: p.status === 'done' ? 'good' : 'bad', to: j.uid, vars: { job: j.id } });
    audit(c, { op: 'job', path: 'complete:' + j.action, rid: j.id }); return j;
  },
  'jobs.decide': (p, c) => {
    needUser(c); const all = store.get('jobs', []); const j = all.find(x => x.id === p.id); if (!j) fail('not_found');
    const dev = c.user.app === 'developer'; const worker = dev && devPerms(c).includes('automation'); const platformJob = !j.tenant || j.tenant === 'platform';
    if (!dev) { if (j.tenant !== c.tenant?.id) fail('not_found'); needWritable(c); if (!['owner', 'admin', 'manager'].includes(c.user.role) && j.uid !== c.user.id) fail('forbidden'); }
    else if (!platformJob && !worker) fail('forbidden'); // a developer decides platform jobs; a subscriber's job only through the worker relaying that subscriber's own reply
    let by = c.user.id, channel = 'app';
    if (dev && !platformJob) { const u = users().find(x => x.id === p.by_user && x.tenant === j.tenant); if (!u) fail('validation', { by_user: 'required' }); by = u.id; channel = String(p.channel || 'whatsapp').slice(0, 20); }
    if (j.status !== 'needs_approval') fail('validation', { status: 'invalid' });
    if (j.proposal?.expires_at && new Date(j.proposal.expires_at) < new Date()) { j.status = 'rejected'; j.decision = { decision: 'expired', by: null, channel: 'system', note: '', at: nowIso() }; store.set('jobs', all); LEARN.onDecide(j, {}); fail('validation', { status: 'expired' }); }
    if (!['approve', 'reject'].includes(p.decision)) fail('validation', { decision: 'option' });
    j.decision = { decision: p.decision, by, channel, note: String(p.note || '').slice(0, 300), at: nowIso() }; j.status = p.decision === 'approve' ? 'queued' : 'rejected';
    store.set('jobs', all); LEARN.onDecide(j, p); audit(c, { op: 'job', path: 'decide:' + p.decision + ':' + j.action, rid: j.id }); return j;
  },
  // data portability and erasure for every interface (owner/admin export, owner deletes after a 30-day grace the worker honours)
  'account.export': (p, c) => {
    needUser(c); const T = c.tenant; if (!T) fail('forbidden'); if (!['owner', 'admin'].includes(c.user.role)) fail('forbidden');
    const data = {}; for (const k of new Set([...Object.keys(R.ENT), ...Object.keys(getP().custom_ent || {})])) { const rows = rowsOf(T.id, k); if (rows.length) data[k] = rows; }
    audit(c, { op: 'account.export' });
    return { file: 'dar-' + String(T.name || 'account').replace(/[^\p{L}\p{N}]+/gu, '-').slice(0, 40) + '-' + nowIso().slice(0, 10) + '.json', data: { exported_at: nowIso(), account: { id: T.id, name: T.name, app: T.app, country: T.country, plan: T.plan, created: T.created }, users: users().filter(u => u.tenant === T.id).map(publicUser), collections: data, ai: { ...LEARN.exportOf(T.id), behavior: BEHAVIOR.exportOf(T.id) } } };
  },
  'account.delete_request': (p, c) => {
    needUser(c); if (!c.tenant) fail('forbidden'); if (c.user.role !== 'owner') fail('forbidden'); if (c.tenant.demo) fail('demo_readonly');
    if (String(p.confirm || '').trim().toLowerCase() !== String(c.tenant.name || '').trim().toLowerCase()) fail('validation', { confirm: 'mismatch' });
    const list = tenants(); const T = list.find(x => x.id === c.tenant.id); const after = new Date(Date.now() + 30 * DAY).toISOString();
    T.deletion = { requested_at: nowIso(), by: c.user.id, after }; saveTenants(list);
    queueJob(c, { service: 'account', action: 'delete', input: { after } }); audit(c, { op: 'account.delete_request' }); return withBrand(T);
  },
  'account.delete_cancel': (p, c) => {
    needUser(c); if (!c.tenant) fail('forbidden'); if (c.user.role !== 'owner') fail('forbidden');
    const list = tenants(); const T = list.find(x => x.id === c.tenant.id); if (!T.deletion) return withBrand(T);
    delete T.deletion; saveTenants(list); queueJob(c, { service: 'account', action: 'delete_cancel', input: {} }); audit(c, { op: 'account.delete_cancel' }); return withBrand(T);
  },
  // the policy a worker must apply for one account (users read their own; the automation reads any account)
  'autonomy.get': (p, c) => {
    needUser(c); const dev = autonomyOf(getP()); let tid = c.tenant?.id;
    if (c.user.app === 'developer') { if (!p.tenant) return { platform: dev, account: null, effective: dev }; if (!devPerms(c).includes('automation')) fail('forbidden'); tid = String(p.tenant); if (!tenants().some(x => x.id === tid)) fail('not_found'); }
    const mine = store.get(`set:${tid}:autonomy`, null); return { platform: c.user.app === 'developer' ? dev : { ...dev, escalation: '' }, account: mine, effective: mergeAutonomy(dev, mine) };
  },
  'jobs.clear': (p, c) => { needPerm(c, 'automation'); const all = store.get('jobs', []); const keep = p.status ? all.filter(j => j.status !== p.status) : []; store.set('jobs', keep); audit(c, { op: 'jobs.clear' }); return { removed: all.length - keep.length }; },
  'audit.list': (p, c) => { needUser(c); const all = store.get('audit', []); return (c.user.app === 'developer' ? all : all.filter(a => a.tenant === c.tenant?.id)).slice(0, +p.limit || 500); },
  // v3.0: the 24/7 watcher's sink. Accepts one event or a batch; folds repeats into a count so one broken screen
  // can't flood the log; keeps the newest 500. Open (no auth) so the beacon works before sign-in; strictly sanitised.
  'monitor.log': (p, c) => {
    const list = store.get('errors', []); const now = nowIso();
    const raw = Array.isArray(p.batch) ? p.batch.slice(0, 20) : [p];
    for (const e of raw) {
      const sev = ['error', 'warn', 'info'].includes(e.sev) ? e.sev : 'error';
      const msg = String(e.msg || '').slice(0, 500), where = String(e.where || '').slice(0, 200);
      if (!msg) continue;
      const fp = sev + '|' + msg.slice(0, 120) + '|' + where.slice(0, 60);
      const hit = list.find(x => x.fp === fp && Date.parse(now) - Date.parse(x.last || x.at) < 36e5);
      if (hit) { hit.count = (hit.count || 1) + (+e.count || 1); hit.last = now; continue; } // fold repeats within the hour
      list.unshift({ at: now, last: now, fp, sev, app: String(e.app || c.app || '').slice(0, 20), msg, where, route: String(e.route || '').slice(0, 60), tenant: e.tenant ? String(e.tenant).slice(0, 40) : null, count: Math.max(1, +e.count || 1), crumbs: Array.isArray(e.crumbs) ? e.crumbs.slice(-6) : undefined });
    }
    if (list.length > 500) list.length = 500; store.set('errors', list);
    const since = Date.now() - 36e5, recent = list.filter(x => Date.parse(x.last || x.at) >= since);
    return { ok: true, open_errors: recent.filter(x => x.sev === 'error').length };
  },
  // v3.2: the records checked against themselves (assets/health32.js) — every account for the developer, one's own for a manager
  'monitor.integrity': (p, c) => integrityScan(p, c),
  'monitor.list': (p, c) => {
    needPerm(c, 'monitoring'); const errors = store.get('errors', []); const since = Date.now() - 24 * 36e5;
    const win = errors.filter(x => Date.parse(x.last || x.at) >= since);
    const by = {}; for (const e of win) by[e.where || 'other'] = (by[e.where || 'other'] || 0) + (e.count || 1);
    return { errors: errors.slice(0, +p.limit || 200), jobs: store.get('jobs', []).slice(0, 200), summary: { day_errors: win.filter(x => x.sev === 'error').length, day_warns: win.filter(x => x.sev === 'warn').length, top: Object.entries(by).sort((a, b) => b[1] - a[1]).slice(0, 8).map(([k, n]) => ({ where: k, n })) } };
  },

  // ---- platform (developer)
  'platform.get': (p, c) => { needDev(c); return getP(); },
  'platform.set': (p, c) => {
    needDev(c);
    const changes = p.changes || [{ path: p.path, value: p.value }];
    const P = getP(); const undo = []; const roots = new Set(); const pp0 = JSON.stringify(ppShown(P)); const P0 = {}; // (v3.22) (v3.33.4: P0 — a root as it was before this change, for its undo)
    for (let ch of changes) {
      // v3.2: a translation path (texts:…, custom:…, landings:…) fills only the empty languages of that one text — the AI
      // translator's platform_changes and the developer's own translations; what the developer wrote is never replaced
      const tm = /^(texts|cats|custom|landings|onboarding|recipes):/.exec(String(ch.path || ''));
      // v3.11.1: a key, a token or a password is never a setting (it goes to the vault: paste it in the assistant, or the
      // channels / AI connections screens) — the settings reach every visitor
      if (valueHasKeys(ch.value) || hasKeys(String(ch.path || ''))) fail('secret_in_settings', { path: '' }); // (the path is not echoed: it could hold the key)
      if (tm) { const root = tm[1]; if (!devPerms(c).includes(PATH_PERM[root])) fail('forbidden', { perm: PATH_PERM[root] }); const sub = String(ch.path).slice(root.length + 1); if (!(root in P0)) P0[root] = P[root] === undefined ? null : clone(P[root]); if (root === 'texts' && /^[^.\s]{1,80}$/.test(sub)) { if (!roots.has(root) && !undo.some(u => u.path === 'texts.' + sub)) { const was = P0.texts?.[sub]; undo.push({ path: 'texts.' + sub, value: was === undefined ? null : clone(was) }); } } else if (!roots.has(root)) { roots.add(root); undo.push({ path: root, value: P0[root] }); } fillI18n(P, ch.path, ch.value); continue; } // (v3.33.3: one text's undo is that text — the whole list of texts in every line had filled the owner's browser)
      // v3.33.5 (the owner, 2026-10-23: the legal texts corrected through the assistant): one sentence of a legal text changed — added to
      // P.legal_edits ({doc, lang, old, new}); the pages keep their sections and their other languages (site.js, dar-site.php)
      if (ch.path === 'legal_edits' && ch.value && typeof ch.value === 'object' && !Array.isArray(ch.value)) {
        const e = legalEditOf(ch.value); if (!e) fail('validation', { legal_edits: 'doc, lang, old, new' });
        const list = (Array.isArray(P.legal_edits) ? P.legal_edits : []).filter(x => !(x && x.doc === e.doc && x.lang === e.lang && x.old === e.old)); if (e.new !== e.old) list.push({ ...e, at: nowIso() });
        ch = { path: 'legal_edits', value: list.slice(-200) };
      }
      let parts = String(ch.path || '').split('.').filter(Boolean); if (!parts.length || !(parts[0] in PATH_PERM)) fail('bad_request');
      if (parts[0] === 'features' && parts.length > 2) parts = ['features', parts.slice(1).join('.')]; // (v3.33.12: a feature's setting under its own name — «ig.link» — as every page reads it)
      if (!devPerms(c).includes(PATH_PERM[parts[0]])) fail('forbidden', { perm: PATH_PERM[parts[0]] });
      if (parts[0] === 'doctor' && c.user?.role !== 'owner') fail('forbidden', { perm: 'owner' }); // (v3.14: what the self-check repairs by itself is the owner's own choice)
      checkSetting(parts, ch.value);
      // v3.11.1: a value keeps the shape of the one it replaces (a list stays a list, a group a group): one wrong value
      // read by every page could stop them all
      { let cur = P, dflt = platformDefaults(); for (const k of parts) { cur = cur != null && typeof cur === 'object' ? cur[k] : undefined; dflt = dflt != null && typeof dflt === 'object' ? dflt[k] : undefined; }
        const was = cur !== undefined && cur !== null ? cur : dflt; if (was !== undefined && was !== null && ch.value !== null && ch.value !== undefined && !shapeFits(ch.value, was)) fail('validation', { [ch.path]: 'shape' }); }
      let o = P; for (const k of parts.slice(0, -1)) { if (o[k] == null || typeof o[k] !== 'object') o[k] = {}; o = o[k]; }
      const last = parts[parts.length - 1]; undo.push({ path: ch.path, value: o[last] === undefined ? null : clone(o[last]) });
      if (ch.value === null || ch.value === undefined) delete o[last]; else o[last] = ch.value;
    }
    // v3.11.1: the groups inside keep their shape too (a list stays a list) — the server keeps its own value otherwise, so the
    // refusal is said here, before anything is saved
    for (const [path, want] of NESTED_SHAPES) { const v = path.split('.').reduce((o, k) => (o != null && typeof o === 'object' ? o[k] : undefined), P); if (v != null && !shapeFits(v, want)) fail('validation', { [path]: 'shape' }); }
    saveP(P); const id = audit(c, { op: 'platform.set', label: p.label || '', path: changes.map(x => x.path).join(', '), undo, redo: changes });
    // v3.22: the partner terms — «ونبلغك داخل المنصة حين نغيّرها» (on a host the server tells them, dar-billing.php)
    if (!isHostedNow() && JSON.stringify(ppShown(P)) !== pp0) for (const T of tenants().filter(x => x.app === 'partner' && !x.demo && x.status !== 'deleted')) notify(T.id, { code: 'partner_program', level: 'info', vars: {}, link: 'p_payouts' });
    return { ok: true, id };
  },
  'platform.undo': (p, c) => {
    needDev(c); const all = store.get('audit', []); const a = all.find(x => x.id === p.id && (Array.isArray(x.undo) || x.undo_row)); if (!a || a.undone) fail('not_found');
    if (a.undo_row) OPS['data.update']({ coll: a.undo_row.coll, id: a.undo_row.id, row: a.undo_row.row }, c);
    else OPS['platform.set']({ changes: a.undo, label: 'undo ' + (a.label || a.path) }, c);
    const again = store.get('audit', []); const x = again.find(y => y.id === p.id); if (x) x.undone = true; store.set('audit', again); return { ok: true };
  },
  // (never a session: a backup file must not let its holder act as the person who made it)
  'platform.export': (p, c) => { needPerm(c, 'services'); const out = {}; for (const k of store.keys('')) { if (/^(sess|sync|keyidx|pref|cfg_override):?/.test(k)) continue; out[k] = store.get(k); } delete out.tokens; delete out.loginfail; delete out.vault; return { at: nowIso(), version: VERSION, data: out }; },
  'platform.import': (p, c) => {
    needDev(c); if (c.user.role !== 'owner') fail('forbidden'); const data = p.backup?.data; if (!data || typeof data !== 'object') fail('bad_request');
    const keepTokens = store.get('tokens', {}); const keepVault = store.get('vault', null); for (const k of store.keys('')) store.del(k);
    for (const [k, v] of Object.entries(data)) if (k !== 'vault') store.set(k, v); store.set('tokens', keepTokens); if (keepVault) store.set('vault', keepVault); return { ok: true, keys: Object.keys(data).length };
  },
  'catalog.create': (p, c) => {
    needPerm(c, 'services'); const P = getP();
    const id = 'x_' + (String(p.slug || '').toLowerCase().replace(/[^a-z0-9_]/g, '').slice(0, 24) || randomHex(3));
    if (catalog(P).some(s => s.id === id)) fail('exists');
    const svc = { id, app: p.app || 'app', cat: p.cat || 'core', icon: p.icon || 'sparkle', n: p.n || [id, id, id], d: p.d || ['', '', ''], e: [], a: [], c: [], t: p.t || [], k: [], s: '', screen: 'generic', plans: p.plans || [], status: p.status || 'active', acts: (p.acts || []).map(a => ({ id: a.id || 'act_' + randomHex(2), n: a.n, prompt: a.prompt || '' })), custom: true };
    if (p.fields) { const coll = id; P.custom_ent[coll] = p.fields; svc.e = [coll]; svc.k = ['count:' + coll]; }
    P.custom = [...(P.custom || []), svc]; saveP(P); audit(c, { op: 'catalog.create', path: id, undo: [{ path: 'custom', value: (P.custom || []).filter(s => s.id !== id) }], redo: [{ path: 'custom', value: P.custom }] }); // (v3.11.1: the list after it too — a repair puts back the newest)
    // a service written in one language is queued for translation into the others (the AI translator fills the missing slots after linking)
    // (v3.2: the developer panel translates on the device first and queues only what is left — it passes translate:false)
    if (p.translate !== false && (missing3(svc.n).length || (svc.d.some(Boolean) && missing3(svc.d).length))) queueJob(c, { service: 'd_services', action: 'translate', input: { items: [{ path: `custom:${id}`, n: svc.n, d: svc.d }] } });
    return svc;
  },
  'catalog.remove': (p, c) => {
    needPerm(c, 'services'); const P = getP(); const before = clone(P.custom || []);
    P.custom = (P.custom || []).filter(s => s.id !== p.id); if (P.custom.length === before.length) fail('not_found');
    saveP(P); audit(c, { op: 'platform.set', label: 'remove ' + p.id, path: 'custom', undo: [{ path: 'custom', value: before }], redo: [{ path: 'custom', value: P.custom }] }); return { ok: true };
  },
  'tenants.list': (p, c) => {
    needPerm(c, 'tenants'); const us = users();
    return tenants().filter(T => !p.app || T.app === p.app).map(T => ({ ...T, tz: T.tz || tzOf(T.country), owner: publicUser(us.find(u => u.tenant === T.id && u.role === 'owner')), records: store.keys(`db:${T.id}:`).reduce((n, k) => n + (store.get(k, []).length || 0), 0) })); // v2.5.3: tz always present (the automation schedules digests by local time)
  },
  // v2.5.2: erasure the account asked for (account.delete_request) once its grace period has passed — the automation calls it hourly.
  // Business data, people, sessions, keys, jobs and the account's audit lines go; a tombstone keeps id/app/country/plan/dates for platform totals.
  'tenants.purge': (p, c) => { needPerm(c, 'automation'); return purgeTenant(String(p.id || ''), c); },
  // v2.5.4: the contract's scheduled duties for every account (or one) — overdue flips, expiry alerts, renewal tasks, link expiry,
  // lead pond. The server runs it every hour by itself; the automation may call it on demand. {kinds?: [...], tenant?}
  'system.sweep': (p, c) => { needPerm(c, 'automation'); const r = withMemorySweep(EXT.sweep(p || {}, OPS)); if (!isHostedNow() && !p?.tenant) r.billing = BILL.tick(); return r; }, // (v3.13.2: the subscriptions' lifecycle; on a host the server's duty)
  // v3.5: on the site's own server the account's scheduled duties (invoices overdue, obligations, leases ending, HR,
  // expiring links, renewal tasks, occupancy) run from its manager's browser — at most every 30 minutes, once each
  'account.sweep': (p, c) => {
    needUser(c); if (!c.tenant || c.user.app === 'developer') fail('forbidden'); if (!['owner', 'admin', 'manager'].includes(c.user.role) || c.tenant.demo || c.imp) return { skipped: 'role' };
    if (c.tenant.status === 'suspended') return { skipped: 'suspended' }; // (v3.13.2: a suspended account is read-only — nothing to write)
    const k = `set:${c.tenant.id}:sweep_at`; if (Date.now() - (+store.get(k, 0) || 0) < 30 * 60e3 && !p.force) return { skipped: 'recent' };
    store.set(k, Date.now()); return EXT.sweep({ tenant: c.tenant.id }, OPS);
  },
  'tenants.update': (p, c) => {
    needPerm(c, 'tenants'); const list = tenants(); const T = list.find(x => x.id === p.id); if (!T) fail('not_found');
    const before = { status: T.status, plan: T.plan, tier: T.tier }; const ds0 = T.domain_status;
    for (const k of ['status', 'plan', 'tier']) if (p[k] != null) T[k] = String(p[k]);
    if (p.status != null && !['trial', 'active', 'past_due', 'suspended'].includes(T.status)) fail('validation', { status: 'option' });
    // v3.13.2: a suspension by the developer says so (the lifecycle never lifts it by itself); his activation clears what was due
    if (p.status === 'suspended' && before.status !== 'suspended') T.suspend_reason = 'manual';
    if (p.status === 'active' || p.status === 'trial') { delete T.suspend_reason; delete T.due_reason; delete T.grace_until; delete T.readonly_since; delete T.purge_at; } // (v3.21: and the read-only clock)
    if (p.cycle != null) { if (!['month', 'year'].includes(p.cycle)) fail('validation', { cycle: 'option' }); T.cycle = p.cycle; }
    // the price agreed with this account (a plan «on request», or a special price): what its subscription page asks for
    if ('price' in p) { if (p.price == null || p.price === '') delete T.price; else { const v = +String(p.price).replace(/[^\d.]/g, ''); if (!(v > 0) || v > 10000000) fail('validation', { price: 'number' }); T.price = Math.round(v * 100) / 100; } }
    if (p.country != null) { const cc = String(p.country).trim().toUpperCase(); if (!R.WORLD[cc] && !listedCountry(cc)) fail('validation', { country: 'country_na' }); T.country = cc; } // the developer may place an account in any real country
    if (Array.isArray(p.addons)) { const known = rowsOf('platform', 'addons').map(a => a.code); T.addons = [...new Set(p.addons.map(String).filter(x => known.includes(x)))]; }
    for (const k of ['renews_at', 'trial_end', 'grace_until', 'cancel_at']) if (k in p) { if (p[k] == null || p[k] === '') delete T[k]; else if (!isNaN(Date.parse(p[k]))) T[k] = new Date(p[k]).toISOString(); else fail('validation', { [k]: 'invalid' }); }
    if (p.extra && typeof p.extra === 'object') T.extra = Object.fromEntries(Object.entries(p.extra).filter(([, v]) => Number.isFinite(+v) && +v >= 0).map(([k, v]) => [k, +v]));
    if (p.domain_status != null) { if (!['pending', 'active', 'error'].includes(p.domain_status) || !T.domain) fail('validation', { domain_status: 'invalid' }); T.domain_status = p.domain_status; }
    saveTenants(list); audit(c, { op: 'tenants.update', rid: T.id, before, after: { status: T.status, plan: T.plan, tier: T.tier, addons: T.addons, domain_status: T.domain_status } });
    if (T.domain_status !== ds0 && ['active', 'error'].includes(T.domain_status)) notify(T.id, { code: T.domain_status === 'active' ? 'domain_ready' : 'domain_error', vars: { host: T.domain }, level: T.domain_status === 'active' ? 'good' : 'bad', svc: 'white_label', to: 'managers' });
    // v3.13.2: a partner's commission comes from money received (billing.confirm), never from a status switched by hand
    return T;
  },
  'tenants.impersonate': (p, c) => {
    needPerm(c, 'tenants'); const T = tenants().find(x => x.id === p.id); if (!T) fail('not_found');
    const u = users().find(x => x.tenant === T.id && x.role === 'owner'); if (!u) fail('not_found');
    const token = issueToken(u, T.app, c.user.id); audit(c, { op: 'impersonate', rid: T.id }); return { token, app: T.app, user: publicUser(u), tenant: T };
  },
  'devusers.list': (p, c) => { needView(c, 'accounts'); // (v3.31: whoever may see the accounts sees the list)
    return { users: users().filter(u => u.app === 'developer').map(publicUser), invites: store.get('invites', []).map(({ code, ...x }) => ({ ...x, code: code.slice(0, 8) + '…' })) }; },
  'devusers.save': (p, c) => {
    needPerm(c, 'accounts'); const list = users(); const u = list.find(x => x.id === p.id && x.app === 'developer'); if (!u) fail('not_found');
    if (u.id === c.user.id) fail('forbidden', { self: 'own_access' }); if (u.role === 'owner' && c.user.role !== 'owner') fail('forbidden', { role: 'owner' });
    const owners = list.filter(x => x.app === 'developer' && x.role === 'owner' && x.status !== 'inactive');
    if (u.role === 'owner') { if (owners.length === 1 && ((p.role && p.role !== 'owner') || p.status === 'inactive')) fail('last_owner'); if (p.role && p.role !== 'owner') u.role = p.role; if (p.status) u.status = p.status === 'inactive' ? 'inactive' : 'active'; }
    else {
      if (p.role !== undefined && p.role !== u.role) { if (p.role === 'owner' || !/^[a-z_]{2,30}$/.test(String(p.role))) fail('forbidden', { role: p.role }); staffGrant(c, p.role, {}, false); u.role = p.role; }
      if (p.status !== undefined) u.status = p.status === 'inactive' ? 'inactive' : 'active';
      if (p.access !== undefined || p.until !== undefined) { const g = staffGrant(c, u.role, p, false); if (p.access !== undefined) { if (g.access) u.access = g.access; else delete u.access; } if (p.until !== undefined) { if (g.until) u.until = g.until; else delete u.until; } }
    }
    saveUsers(list); audit(c, { op: 'devusers.save', rid: u.id, after: { role: u.role, status: u.status, access: u.access || null, until: u.until || null } }); return { user: publicUser(u) };
  },
  'devusers.update': (p, c) => {
    needPerm(c, 'accounts'); const list = users(); const u = list.find(x => x.id === p.id && x.app === 'developer'); if (!u) fail('not_found');
    if (u.role === 'owner' && list.filter(x => x.app === 'developer' && x.role === 'owner' && x.status !== 'inactive').length === 1 && (p.role && p.role !== 'owner' || p.status === 'inactive')) fail('last_owner');
    if (u.id === c.user.id) fail('forbidden', { self: 'own_access' }); // (v3.31: no one changes his own role — and no one is made owner here)
    if (p.role && u.role !== 'owner') { if (p.role === 'owner' || !/^[a-z_]{2,30}$/.test(String(p.role))) fail('forbidden', { role: p.role }); staffGrant(c, p.role, {}, false); }
    if (p.role) u.role = p.role; if (p.status) u.status = p.status === 'inactive' ? 'inactive' : 'active'; saveUsers(list); audit(c, { op: 'devusers.update', rid: u.id, after: { role: u.role, status: u.status } }); return publicUser(u);
  },
  'keys.master': async (p, c) => {
    needDev(c); if (c.user.role !== 'owner') fail('forbidden'); const key = ((SOLO || SHOW) ? 'key_mk_' : 'dar_mk_') + randomHex(24); // (v3.30: a sold copy's master key carries no name of the platform)
    OPS['platform.set']({ changes: [{ path: 'master_key_hash', value: await sha256(key) }, { path: 'master_key_preview', value: key.slice(0, 10) + '…' + key.slice(-4) }], label: 'master key rotated' }, c);
    return { key };
  },
  'keys.create': async (p, c) => {
    needUser(c); needWritable(c);
    const coll = c.app === 'console' ? 'c_keys' : 'api_keys';
    // v3.5: a builder company has its own API key too («مفتاح API لشركتك»), like an office
    if (c.app === 'app' || c.app === 'builders') { const svc = catalog(getP()).find(s => s.app === c.app && (s.id === 'api_access' || s.share === 'api_access')); if (access(svc, accessCtx(c)) !== 'ok') fail('not_in_plan'); }
    if (!['app', 'builders', 'console'].includes(c.app)) fail('forbidden');
    const key = ((SOLO || SHOW) ? 'key_' : 'dar_') + (c.app === 'console' ? 'c_' : 'o_') + randomHex(20); const list = store.get(ckey(c.tenant.id, coll), []);
    { const lim = +planLimits(c).keys; if (lim && list.filter(k => k.status === 'active').length >= lim) fail('limit_reached', { limit: lim, key: 'keys' }); } // (v3.33.21: the plan's «API keys») // (v3.30: a sold copy's keys carry no name of the platform; the server knows both)
    const rec = { id: uid('r'), created: nowIso(), name: String(p.name || 'key').slice(0, 60), scope: ['read', 'write', 'full'].includes(p.scope) ? p.scope : 'read', key_preview: key.slice(0, 8) + '…' + key.slice(-4), hash: await sha256(key), status: 'active' };
    list.unshift(rec); store.set(ckey(c.tenant.id, coll), list); store.set('keyidx:' + rec.hash, { tenant: c.tenant.id, coll, id: rec.id }); audit(c, { op: 'keys.create', rid: rec.id }); return { key, record: { ...rec, hash: undefined } };
  },
  'keys.list': (p, c) => { needUser(c); const coll = c.app === 'console' ? 'c_keys' : 'api_keys'; return store.get(ckey(c.tenant.id, coll), []).map(({ hash, ...r }) => r); },
  'keys.revoke': (p, c) => { needUser(c); const coll = c.app === 'console' ? 'c_keys' : 'api_keys'; const list = store.get(ckey(c.tenant.id, coll), []); const r = list.find(x => x.id === p.id); if (!r) fail('not_found'); r.status = 'revoked'; store.set(ckey(c.tenant.id, coll), list); if (r.hash) store.del('keyidx:' + r.hash); audit(c, { op: 'keys.revoke', rid: r.id }); return { ok: true }; },

  // ---- public pages (no login; only public fields leave the "server")
  'public.card': (p) => {
    const T = tenants().find(x => x.app === 'partner' && x.code && x.code.toLowerCase() === String(p.code || '').toLowerCase() && x.status !== 'suspended'); if (!T) fail('not_found');
    const u = users().find(x => x.tenant === T.id && x.role === 'owner'); const prof = store.get(`set:${T.id}:profile`, {});
    return { name: u?.name || T.name, code: T.code, city: T.city, country: T.country, tier: T.tier, phone: prof.public_phone || '', bio: prof.bio || '', photo: prof.photo || '' };
  },
  'public.listing': (p) => {
    const T = tenants().find(x => x.id === p.t && PUB_APPS.includes(x.app) && x.status !== 'suspended'); if (!T) fail('not_found');
    const r = rowsOf(T.id, 'properties').find(x => x.id === p.id && x.status !== 'off'); if (!r) fail('not_found');
    const prof = store.get(`set:${T.id}:profile`, {});
    const { owner_name, owner_phone, by, _mig, ...safe } = r;
    // v3.17: the place a visitor sees — exactly, only its area (the default: a point a few hundred metres off, drawn as a circle), or none
    { const how = ['exact', 'approximate', 'hidden'].includes(safe.map_show) ? safe.map_show : (getP().maps?.precision || 'approximate'); const sp = getP().maps?.on === false ? null : shownPlace(safe.lat, safe.lng, mapSeed(T.id, r.id), how); delete safe.lat; delete safe.lng; delete safe.map_show; if (sp && (sp.lat || sp.lon)) { safe.lat = sp.lat; safe.lng = sp.lon; safe.map_exact = sp.exact; } }
    if (!p.preview) { const sk = `pstat:${T.id}`; const st = store.get(sk, {}); st._since ||= nowIso().slice(0, 10); const x = (st[r.id] ||= { views: 0, leads: 0 }); x.views++; x.last_view = nowIso(); store.set(sk, st); }
    return { property: safe, office: officeCard(T) };
  },
  // a subscriber's own domain → which office it belongs to (the server answers only after the DNS check marked it active)
  'public.host': (p) => {
    const host = cleanHost(p.host); if (!host) fail('not_found'); const alt = host.startsWith('www.') ? host.slice(4) : 'www.' + host;
    const T = tenants().find(x => PUB_APPS.includes(x.app) && x.status !== 'suspended' && x.domain && (x.domain === host || x.domain === alt) && (!RUNTIME.server || x.domain_status === 'active'));
    const b = T && brandOf(T); if (!b) fail('not_found'); return { t: T.id, brand: b };
  },
  // the office page: available properties with filters (the office turns it on; always on for its own domain)
  'public.catalog': (p) => {
    const T = tenants().find(x => x.id === p.t && PUB_APPS.includes(x.app) && x.status !== 'suspended'); if (!T) fail('not_found');
    const cfg = store.get(`set:${T.id}:office_page`, {}); const own = !!(T.domain && T.domain_status === 'active') || (SOLO && !!T.solo); // (v3.26: a sold copy's business — its page is the site itself)
    if (!cfg.show && !own && !T.demo) fail('not_found');
    const avail = rowsOf(T.id, 'properties').filter(r => !r.status || r.status === 'available'); let rows = avail;
    for (const k of ['purpose', 'type', 'city']) if (p[k]) rows = rows.filter(r => r[k] === p[k]);
    const q = String(p.q || '').trim().toLowerCase().slice(0, 60); if (q) rows = rows.filter(r => [r.title, r.city, r.district, r.description].some(x => String(x || '').toLowerCase().includes(q)));
    rows = [...rows].sort((a, b) => String(b.listed_at || b.created || '').localeCompare(String(a.listed_at || a.created || '')));
    const size = 24, page = Math.max(0, Math.floor(+p.page || 0)); const uniq = k => [...new Set(avail.map(r => r[k]).filter(Boolean))].sort();
    const items = rows.slice(page * size, page * size + size).map(r => ({ id: r.id, title: r.title, type: r.type, purpose: r.purpose, city: r.city, district: r.district, price: r.price, area: r.area, bedrooms: r.bedrooms, bathrooms: r.bathrooms, image: (r.images || []).find(u => IMG_OK.test(u || '')) || '', ...((sp => (sp ? { lat: sp.lat, lng: sp.lon, map_exact: sp.exact } : {}))(getP().maps?.on === false ? null : shownPlace(r.lat, r.lng, mapSeed(T.id, r.id), ['exact', 'approximate', 'hidden'].includes(r.map_show) ? r.map_show : (getP().maps?.precision || 'approximate')))) })); // v3.17: on the office page's map, as the listing allows
    const rc = store.get(`set:${T.id}:ai_receptionist`, {}); const rsv = catalog(getP()).find(s => s.app === T.app && (s.id === 'ai_receptionist' || s.share === 'ai_receptionist')); const agent = !!rc.web_receptionist && !!rsv && access(rsv, { country: T.country, intl: !listedCountry(T.country), plan: T.plan, audience: audienceOf(T.app), plans: rowsOf('platform', 'plans'), unlocked: unlockedOf(T, rowsOf('platform', 'addons')) }) === 'ok'; // v3.2: the office's voice receptionist on its page
    return { office: officeCard(T), page: { headline: String(cfg.headline || '').slice(0, 140), about: String(cfg.about || '').slice(0, 1200) }, items, total: rows.length, more: rows.length > (page + 1) * size, facets: { purpose: uniq('purpose'), type: uniq('type'), city: uniq('city') }, ...(agent ? { agent: { hours: String(rc.working_hours || ''), lang: rc.voice_lang || '' } } : {}) };
  },
  'public.partner_offer': (p) => OPS['public.offer'](p), // (v3.33.27: the server answers it on a live host — assets/sync.js)
  'public.offer': (p) => {
    for (const T of tenants().filter(x => x.app === 'partner')) {
      const o = rowsOf(T.id, 'p_offers').find(x => x.id === p.id);
      if (o) { const u = users().find(x => x.tenant === T.id && x.role === 'owner'); return { offer: o, partner: { name: u?.name || '', code: T.code }, country: T.country }; }
    }
    fail('not_found');
  },
  'public.status': () => ({ mode: CFG.mode, version: VERSION, incidents: rowsOf('platform', 'incidents').filter(i => i.status !== 'resolved').map(i => ({ title: i.title, severity: i.severity, opened_at: i.opened_at || i.created })) }),
  'public.suggest': (p, c) => {
    const text = String(p.body || '').trim(); if (text.length < 3) fail('validation', { body: 'required' });
    const list = rowsOf('platform', 'psuggestions'); list.unshift({ id: uid('r'), created: nowIso(), title: String(p.title || text.slice(0, 60)), body: text.slice(0, 4000), app: c.app, status: 'new' });
    saveRows('platform', 'psuggestions', list.slice(0, 2000)); return { ok: true };
  },

  // ---- marketplace loop: office request -> provider quote -> office accepts -> provider job
  'market.request': (p, c) => {
    needUser(c); needWritable(c); if (!PUB_APPS.includes(c.app)) fail('forbidden');
    const rec = OPS['data.create']({ coll: 'service_requests', row: { ...p.row, status: 'open' } }, c);
    const list = rowsOf('platform', 'market_requests');
    list.unshift({ id: rec.id, created: nowIso(), tenant: c.tenant.id, title: rec.title, category: rec.category, city: rec.city || c.tenant.city || '', details: rec.details || '', status: 'open' });
    saveRows('platform', 'market_requests', list); return rec;
  },
  'market.quote': (p, c) => {
    needUser(c); needWritable(c); if (c.app !== 'providers') fail('forbidden');
    const req = rowsOf('platform', 'market_requests').find(x => x.id === p.request && x.status === 'open'); if (!req) fail('not_found');
    const amount = Number(latinDigits(p.amount)); if (!isFinite(amount) || amount <= 0) fail('validation', { amount: 'number' });
    const PL = planLimits(c); const m0 = new Date(); m0.setDate(1); m0.setHours(0, 0, 0, 0);
    if (+PL.quotes && rowsOf(c.tenant.id, 'pr_quotes').filter(x => new Date(x.created) >= m0).length >= +PL.quotes) fail('limit_reached', { limit: +PL.quotes, key: 'quotes' }); // (v3.33.21: the plan's quotes a month)
    const q = { id: uid('q'), created: nowIso(), request: req.id, office: req.tenant, provider: c.tenant.id, provider_name: c.tenant.name, amount, message: String(p.message || '').slice(0, 1000), status: 'sent', featured: +PL.featured > 0 };
    saveRows('platform', 'market_quotes', [q, ...rowsOf('platform', 'market_quotes')]);
    saveRows(c.tenant.id, 'pr_quotes', [{ id: q.id, created: q.created, request: req.title, amount, message: q.message, status: 'sent' }, ...rowsOf(c.tenant.id, 'pr_quotes')]);
    audit(c, { op: 'market.quote', rid: q.id }); return q;
  },
  'market.quotes': (p, c) => { needUser(c); const l = rowsOf('platform', 'market_quotes').filter(q => q.office === c.tenant?.id && (!p.request || q.request === p.request)); return [...l.filter(q => q.featured), ...l.filter(q => !q.featured)]; }, // (v3.33.21: a featured provider's quote first)
  'market.accept': (p, c) => {
    needUser(c); needWritable(c); const all = rowsOf('platform', 'market_quotes'); const q = all.find(x => x.id === p.id && x.office === c.tenant.id); if (!q) fail('not_found');
    q.status = 'accepted'; for (const o of all) if (o.request === q.request && o.id !== q.id && o.status === 'sent') o.status = 'rejected'; saveRows('platform', 'market_quotes', all);
    const reqs = rowsOf('platform', 'market_requests'); const r = reqs.find(x => x.id === q.request); if (r) { r.status = 'assigned'; saveRows('platform', 'market_requests', reqs); }
    const mine = rowsOf(c.tenant.id, 'service_requests'); const m = mine.find(x => x.id === q.request); if (m) { m.status = 'assigned'; saveRows(c.tenant.id, 'service_requests', mine); }
    const pq = rowsOf(q.provider, 'pr_quotes'); for (const x of pq) if (x.id === q.id) x.status = 'accepted'; saveRows(q.provider, 'pr_quotes', pq);
    saveRows(q.provider, 'pr_jobs', [{ id: uid('r'), created: nowIso(), title: r?.title || '', client: c.tenant.name, date: '', status: 'scheduled', amount: q.amount }, ...rowsOf(q.provider, 'pr_jobs')]);
    audit(c, { op: 'market.accept', rid: q.id }); return q;
  },

  // ---- partner offers and commissions
  'offers.create': (p, c) => {
    needUser(c); needWritable(c); if (c.app !== 'partner') fail('forbidden');
    const P = getP(); const pp = P.partner || R.DEFAULT_PARTNER; const disc = Math.max(0, Math.min(+p.discount || 0, +pp.max_discount || 0)); const hours = Math.max(0, Math.min(+p.trial_hours || 0, +pp.max_trial_hours || 0));
    // v3.33.27 (the owner, 2026-10-28, note 5: «المسوق ينشئ كوبونًا خاصًا به بنسبة الخصم التي يحددها … من سعر الباقة الفعلي مثل رابط الخصم الموجود حاليًا، وينشره للجميع؛ رابط الخصم لا يرتبط
    // بمكتب محدد، وعند الضغط عليه ينتقل العميل للواجهة الرئيسية وينسب الاشتراك للمسوق»): an offer for everyone (no office — a coupon code of his and a link to the main site,
    // 30 days) or for one office (48 hours, as before); a plan of any audience, or every plan; the discount still taken from the plan's CURRENT price
    const office = String(p.office || '').trim().slice(0, 120); const pub = p.scope === 'public' || (p.scope !== 'office' && !office);
    const plans = rowsOf('platform', 'plans').filter(x => x.active !== false && ['office', 'builder', 'provider'].includes(x.audience));
    const plan = p.plan ? plans.find(x => x.code === p.plan) : null; if (p.plan && !plan) fail('validation', { plan: 'option' }); if (!pub && !office) fail('validation', { office: 'required' });
    let code = String(p.code || '').trim().toUpperCase().replace(/\s+/g, ''); if (code && !/^[A-Z0-9_-]{3,24}$/.test(code)) fail('validation', { code: 'format' });
    const mine = rowsOf(c.tenant.id, 'p_offers'); const taken = x => mine.some(o => String(o.code || '').toUpperCase() === x) || rowsOf('platform', 'coupons').some(cp => String(cp.code || '').toUpperCase() === x);
    if (pub) { if (code && taken(code)) fail('validation', { code: 'taken' }); if (!code) { const base = (String(c.tenant.code || 'DAR').toUpperCase().replace(/[^A-Z0-9]/g, '').slice(0, 14) || 'DAR') + (disc ? String(Math.round(disc)) : ''); code = base.length >= 3 ? base : base + 'OFF'; for (let i = 2; taken(code); i++) code = base + '-' + i; } } else code = '';
    const country = countryBy(c.tenant.country, rowsOf('platform', 'countries'), getP()); const price = plan ? planCost(plan, country, P, 'month')?.now ?? null : null; // (v3.33, note 50: the marketer's discount is taken from the plan's CURRENT price)
    const total = price == null ? null : Math.round(price * (1 - disc / 100) * 100) / 100;
    const rec = asSystem(() => OPS['data.create']({ coll: 'p_offers', row: { office: pub ? '' : office, plan: plan ? plan.code : '', discount: disc, trial_hours: hours, total: total ?? '', status: 'sent', ...(pub ? { code } : {}) } }, c)); // (no office: an offer for everyone)
    const list = rowsOf(c.tenant.id, 'p_offers'); const r = list.find(x => x.id === rec.id); r.expires = new Date(Date.now() + (pub ? 30 * 24 : 48) * 3600e3).toISOString(); saveRows(c.tenant.id, 'p_offers', list);
    return r;
  },

  // ---- v2.9 partner: the offices that really subscribed (view only), the statement, and payouts the Dar team settles
  // v3.33.31 (the owner, 2026-10-28): the marketer's real trial is an account on the server (dar-trials.php op_partner_pass); an example or a local copy has none — it says so, and the preview stays open
  'partner.pass': (p, c) => {
    needUser(c); if (c.app !== 'partner') fail('forbidden');
    if (p?.action === 'open') fail('not_available', { pass: 'server' });
    return { example: true, state: { allowed: false, left: 0, first_week: false, first_week_ends: '', next_at: null, hours: 24, per_first_week: 2, per_week: 1, used: 0 }, live: {}, plans: [] };
  },
  'partner.code_check': (p, c) => {
    needUser(c); if (c.app !== 'partner') fail('forbidden');
    const x = String(p?.code || '').trim().toUpperCase(); if (!/^[A-Z0-9_-]{3,24}$/.test(x)) return { free: false, code: x, why: 'format' };
    const taken = rowsOf(c.tenant.id, 'p_offers').some(o => String(o.code || '').toUpperCase() === x) || rowsOf('platform', 'coupons').some(cp => String(cp.code || '').toUpperCase() === x);
    return { free: !taken, code: x };
  },
  'partner.clients': (p, c) => {
    needUser(c); if (c.app !== 'partner') fail('forbidden');
    const T = c.tenant; const com = rowsOf(T.id, 'p_commissions').filter(x => x.status !== 'cancelled'); const of = n => com.filter(x => x.office === n);
    const ofT = x => com.filter(r => r.account ? r.account === x.id : r.office === x.name); // (v3.13.2: by the account itself; older rows by its name)
    const pp0 = partnerCfg(getP(), R); const tm = x => termsOk(x.partner_terms) ? x.partner_terms : termsNow(pp0); // (v3.22: the rate and months each account earns him)
    const rows = tenants().filter(x => x.attribution && x.attribution === T.code && x.app !== 'partner' && x.status !== 'deleted').map(x => ({ name: x.name, app: x.app, plan: x.plan, status: x.status, since: x.created, trial_end: x.trial_end || '', renews_at: x.renews_at || '', rate: +tm(x).rate, months: +tm(x).months, commission: sumAmt(ofT(x)), paid: sumAmt(ofT(x).filter(r => r.status === 'paid')) }));
    if (!rows.length && T.demo) { // the example partner: the offices behind its sample commissions (the whole account is an example)
      const names = [...new Set(com.map(x => x.office).filter(Boolean))];
      return { example: true, rows: names.map((n, i) => { const e = of(n); return { name: n, app: 'app', plan: e[0]?.plan || '', status: i % 4 === 3 ? 'trial' : 'active', since: e.reduce((a, r) => !a || r.created < a ? r.created : a, ''), trial_end: '', commission: sumAmt(e), paid: sumAmt(e.filter(r => r.status === 'paid')) }; }) };
    }
    return { example: false, rows };
  },
  'partner.statement': (p, c) => {
    needUser(c); if (c.app !== 'partner') fail('forbidden');
    const pp = { ...R.DEFAULT_PARTNER, ...(getP().partner || {}) }; const com = ripenCommissions(c.tenant.id); const prof = store.get(`set:${c.tenant.id}:profile`, {});
    const amt = st => sumAmt(com.filter(x => st.includes(x.status)));
    return { hold: amt(['pending', 'waiting']), review: amt(['review']), available: amt(['eligible', 'approved']), requested: amt(['queued']), paid: amt(['paid']), min_payout: +pp.min_payout || 0, min_count: +pp.min_count || 0, count: com.filter(x => ['eligible', 'approved'].includes(x.status) && +x.amount > 0 && x.kind !== 'fee_share').length, hold_days: +pp.hold_days || 0, method: prof.payout_method || '', has_details: prof.payout_method === 'payoneer' || !!String(prof.payout_details || '').trim(), auto_payout: pp.auto_payout !== false, payouts: rowsOf(c.tenant.id, 'p_payouts') }; // (v3.24: Payoneer needs no details here — the partner registers at Payoneer)
  },
  'partner.payout_request': (p, c) => {
    needUser(c); needWritable(c); if (c.app !== 'partner' || !['owner', 'admin'].includes(c.user.role)) fail('forbidden');
    const pp = { ...R.DEFAULT_PARTNER, ...(getP().partner || {}) }; const tid = c.tenant.id; const com = ripenCommissions(tid);
    const ready = com.filter(x => ['eligible', 'approved'].includes(x.status)); const amount = sumAmt(ready);
    if (!ready.length || amount <= 0) fail('validation', { amount: 'nothing_due' });
    if (amount < (+pp.min_payout || 0)) fail('validation', { amount: 'below_min' });
    if (ready.filter(x => +x.amount > 0 && x.kind !== 'fee_share').length < (+pp.min_count || 0)) fail('validation', { amount: 'below_count' }); // (v3.32: «whop بعد تحقيق عدد معين من العمولات»)
    const prof = store.get(`set:${tid}:profile`, {}); if (!prof.payout_method || !String(prof.payout_details || '').trim()) fail('validation', { payout_details: 'required' }); // (here nothing is sent by a service: the request waits for the team)
    if (prof.payout_method === 'iban' && !ibanCheck(prof.payout_iban).ok) fail('validation', { payout_iban: 'iban_check' }); // (v3.33: an IBAN that does not check is never paid)
    const rec = asSystem(() => OPS['data.create']({ coll: 'p_payouts', row: { amount, method: prof.payout_method, details: String(prof.payout_details).slice(0, 200), ...(prof.payout_method === 'iban' ? { iban: ibanCheck(prof.payout_iban).iban, iban_name: String(prof.payout_name || '').slice(0, 120), iban_bank: String(prof.payout_bank || '').slice(0, 80) } : {}), status: 'requested', requested_at: nowIso() } }, c));
    for (const x of ready) { x.status = 'queued'; x.payout = rec.id; x.updated = nowIso(); } saveRows(tid, 'p_commissions', com);
    audit(c, { op: 'payout.request', rid: rec.id, after: { amount } }); return rec;
  },
  // v3.33: the IBAN payouts waiting for the team, as one file its bank takes (a bulk transfer)
  'partner.payouts_export': (p, c) => {
    const rows = OPS['partner.payouts']({}, c).filter(x => x.method === 'iban' && ['requested', 'approved'].includes(x.status) && x.iban); const cur = getP().base_currency || 'USD';
    const q = v => '"' + String(v ?? '').replace(/"/g, '""') + '"';
    const csv = [['partner', 'code', 'holder', 'iban', 'bank', 'amount', 'currency', 'requested_at', 'payout_id'], ...rows.map(x => [x.partner, x.code, x.iban_name, x.iban, x.iban_bank, (+x.amount || 0).toFixed(2), cur, x.requested_at || x.created, x.id])].map(r => r.map(q).join(',')).join('\r\n') + '\r\n';
    return { csv: '\uFEFF' + csv, count: rows.length, name: `dar-payouts-iban-${new Date().toISOString().slice(0, 10)}.csv` };
  },
  'partner.payouts': (p, c) => {
    needPerm(c, 'payments'); const out = [];
    for (const T of tenants().filter(x => x.app === 'partner')) for (const r of rowsOf(T.id, 'p_payouts')) out.push({ ...r, tenant: T.id, partner: T.name, code: T.code });
    return out.sort((a, b) => String(b.requested_at || b.created).localeCompare(String(a.requested_at || a.created)));
  },
  'partner.payout_decide': (p, c) => {
    needPerm(c, 'payments'); const T = tenants().find(x => x.id === p.tenant && x.app === 'partner'); if (!T) fail('not_found');
    const list = rowsOf(T.id, 'p_payouts'); const r = list.find(x => x.id === p.id); if (!r) fail('not_found');
    const next = { approve: 'approved', paid: 'paid', reject: 'rejected' }[p.decision]; if (!next) fail('validation', { decision: 'option' });
    if (!({ requested: ['approved', 'paid', 'rejected'], approved: ['paid', 'rejected'] }[r.status] || []).includes(next)) fail('validation', { decision: 'state' });
    const note = String(p.note || '').trim().slice(0, 300); if (next === 'rejected' && !note) fail('validation', { note: 'required' }); // (v3.22: the partner is told why)
    if (next === 'paid') { const fee = p.fee == null || p.fee === '' ? 0 : Math.round(+latinDigits(String(p.fee)).replace(/[^\d.]/g, '') * 100) / 100; if (!(fee >= 0) || fee > +r.amount) fail('validation', { fee: 'range' }); r.fee = fee; r.fee_share = Math.round(fee / 2 * 100) / 100; r.net = Math.round((+r.amount - r.fee_share) * 100) / 100; r.paid_at = nowIso(); } // (v3.22: the transfer fee, half of it the partner's)
    if (next === 'paid') { const ref = String(p.ref || '').trim().slice(0, 80); if (ref) r.ref = ref; } // (v3.33: the bank's reference of the transfer, shown to him)
    r.status = next; if (note) r.note = note; r.updated = nowIso(); saveRows(T.id, 'p_payouts', list);
    const com = rowsOf(T.id, 'p_commissions'); for (const x of com) if (x.payout === r.id) { if (next === 'paid') { x.status = 'paid'; x.paid_at = r.paid_at; } else if (next === 'rejected') { x.status = 'eligible'; delete x.payout; } x.updated = nowIso(); }
    saveRows(T.id, 'p_commissions', com);
    if (T.status !== 'deleted') notify(T.id, { code: next === 'paid' && r.fee_share > 0 ? 'payout_paid_fee' : 'payout_' + next, level: next === 'rejected' ? 'warn' : 'good', vars: { amount: r.amount, net: r.net ?? r.amount, fee: r.fee_share || 0, note, ref: r.ref || '' }, link: 'p_payouts' }); // (an account already deleted keeps its payouts, nothing else)
    audit(c, { op: 'payout.' + next, rid: r.id, after: { tenant: T.id, amount: r.amount } }); return r;
  },

  // ---- billing (quotes are real math; charging needs a gateway on the server)
  'billing.quote': (p, c) => {
    const P = getP(); const country = countryBy(p.country, rowsOf('platform', 'countries'), P);
    // v3.13.2: the developer prices an account from his panel (its own record); a subscriber prices his own
    const Tq = c?.user?.app === 'developer' && p.tenant ? tenants().find(x => x.id === p.tenant) || null : c?.tenant || null;
    const plan = rowsOf('platform', 'plans').find(x => x.code === p.plan && (!p.audience || x.audience === p.audience));
    // v3.13.2: the price agreed with this account (a plan «on request», or a special price) is its own plan's price
    const own = Tq && +Tq.price > 0 && (!p.plan || p.plan === Tq.plan) ? +Tq.price : null;
    // v3.24: an add-on bought on its own is priced alone (the plan's price is not added to it)
    const addonOnly = !!p.addon_only && (p.addons || []).length > 0;
    const monthly = addonOnly ? 0 : own ?? listPrice(plan, country, P); if (monthly == null) return { on_request: true };
    const pc = addonOnly ? null : planCost(plan, country, P, p.cycle === 'year' ? 'year' : 'month', own); let price = addonOnly ? 0 : pc.now; const planOff = addonOnly ? 0 : pc.off; // (v3.33: the plan's own discount first — the offer and the coupon are taken from what is left)
    let discount = 0; const cp = p.coupon && rowsOf('platform', 'coupons').find(x => x.code?.toLowerCase() === String(p.coupon).toLowerCase() && x.active !== false && (!x.valid_until || new Date(x.valid_until) >= new Date()) && (!x.countries?.length || x.countries.includes(country.code)));
    if (cp) discount = Math.round(price * (+cp.percent || 0)) / 100;
    // a partner's offer: open within its hours, and kept by the account that signed up with it (on a host its terms travel
    // in the account's record, set by the server — this browser does not hold the partners)
    const oid = String(p.offer || Tq?.offer || ''); let of = findOffer(oid); let offer = null;
    if (!of && oid && Tq?.offer === oid && Tq.offer_info && typeof Tq.offer_info === 'object') of = { offer: { id: oid, discount: +Tq.offer_info.discount || 0, plan: Tq.offer_info.plan || '' }, partner: { code: Tq.offer_info.partner || '' }, expired: false };
    if (of && (!of.expired || Tq?.offer === of.offer.id) && (!of.offer.plan || of.offer.plan === p.plan)) { const pct = Math.min(+of.offer.discount || 0, +(P.partner || R.DEFAULT_PARTNER).max_discount || 10); const od = Math.round(price * pct) / 100; if (od > discount) { discount = od; offer = { id: of.offer.id, discount: pct, partner: of.partner.code }; } }
    for (const code of p.addons || []) { const a = rowsOf('platform', 'addons').find(x => x.code === code && x.active !== false); const ap = listPrice(a, country, P); if (ap != null) price += ap * (p.cycle === 'year' ? 12 : 1); }
    const b = taxBreakdown(price - discount, country, P);
    return { currency: billCur(country), subtotal: price, discount, plan_off: planOff, plan_pct: addonOnly ? 0 : pc.pct, list_price: addonOnly ? 0 : pc.list, coupon: cp && !offer ? cp.code : null, offer, ...b };
  },
  // v3.13.2: no card gateway yet — the subscriber is shown the amount, the platform's bank details and his own reference, and
  // tells the platform «I transferred» (billing.claim); nothing pretends to charge
  'billing.checkout': (p, c) => {
    needUser(c); if (!c.tenant || c.user.app === 'developer') fail('forbidden');
    const plan = p.plan || c.tenant.plan; const cycle = p.cycle === 'year' ? 'year' : 'month'; const sold = rowsOf('platform', 'addons').filter(x => x.active !== false && x.customer !== false).map(x => x.code); // (v3.33, note 66: only what customers may buy — the twin of dar-pay.php pay_addon_row)
    const addons = Array.isArray(p.addons) ? p.addons.map(String).filter(x => sold.includes(x)).slice(0, 10) : [];
    if (p.service && !addons.length) { const a = rowsOf('platform', 'addons').find(x => x.service === p.service && sold.includes(x.code)); if (a) addons.push(a.code); else fail('not_for_sale', { service: p.service }); } // a service bought on its own (the store); with no add-on to sell it is refused — it used to fall through to a plan checkout of the plan he already has
    const q = OPS['billing.quote']({ plan, audience: c.tenant.audience, country: c.tenant.country, cycle, coupon: p.coupon || '', addons, addon_only: !!p.addon_only }, c);
    return { needs: 'transfer', plan, cycle, addons, addon_only: !!p.addon_only && addons.length > 0, quote: q, amount: q.on_request ? null : q.total, currency: q.currency || billCur(countryBy(c.tenant.country, rowsOf('platform', 'countries'), getP())), ...OPS['billing.pay_info']({}, c) };
  },
  // subscription self-service (live: the server talks to the gateway; the model records the request honestly)
  'billing.usage': (p, c) => {
    needUser(c); if (!c.tenant) fail('forbidden'); const T = c.tenant; const d = coll => rowsOf(T.id, coll);
    const m0 = new Date(); m0.setDate(1); m0.setHours(0, 0, 0, 0); const since = m0.getTime(); const day0 = new Date(); day0.setHours(0, 0, 0, 0);
    const mine = store.get('jobs', []).filter(j => j.tenant === T.id && new Date(j.at).getTime() >= since);
    return { period_start: m0.toISOString().slice(0, 10), users: users().filter(u => u.tenant === T.id && u.status !== 'inactive').length, properties: d('properties').length, projects: d('projects').length, units: d('units').length,
      ai_ops: mine.filter(isAiJob).length, messages: d('messages').filter(m => m.direction === 'out' && new Date(m.created || m.at).getTime() >= since).length,
      keys: store.get(ckey(T.id, 'api_keys'), []).filter(k => k.status === 'active').length, quotes: d('pr_quotes').filter(q => new Date(q.created).getTime() >= since).length,
      requests_day: d('service_requests').filter(r => new Date(r.created) >= day0).length, categories: (T.categories || (T.category ? [T.category] : [])).length, extra: T.extra || {} };
  },
  'billing.cancel': (p, c) => {
    needUser(c); if (!['owner', 'admin'].includes(c.user.role)) fail('forbidden'); const list = tenants(); const T = list.find(x => x.id === c.tenant?.id); if (!T) fail('not_found');
    const end = T.renews_at || T.trial_end || new Date(Date.now() + 30 * DAY).toISOString(); T.cancel_at = end; T.cancel_reason = String(p.reason || '').slice(0, 300); saveTenants(list);
    queueJob(c, { service: 'subscription', action: 'cancel', input: { at: end, reason: T.cancel_reason } }); audit(c, { op: 'billing.cancel' }); return { cancel_at: end };
  },
  'billing.resume': (p, c) => {
    needUser(c); if (!['owner', 'admin'].includes(c.user.role)) fail('forbidden'); const list = tenants(); const T = list.find(x => x.id === c.tenant?.id); if (!T || !T.cancel_at) fail('not_found');
    delete T.cancel_at; delete T.cancel_reason; saveTenants(list); queueJob(c, { service: 'subscription', action: 'resume', input: {} }); audit(c, { op: 'billing.resume' }); return { ok: true };
  },
  'billing.invoices': (p, c) => { needUser(c); if (!c.tenant) fail('forbidden'); return store.get(`binv:${c.tenant.id}`, []); },
  'billing.portal': () => fail(RUNTIME.server ? 'not_configured' : 'live_only'),
  'public.payment.status': () => fail(RUNTIME.server ? 'not_configured' : 'live_only'),
  // sign-in with Google/Apple/Microsoft (server: redirect flow; the model states it honestly)
  'auth.oauth_start': () => fail(RUNTIME.server ? 'not_configured' : 'live_only'),
  'auth.oauth_finish': () => fail(RUNTIME.server ? 'not_configured' : 'live_only'),
  'auth.oauth_test': () => fail(RUNTIME.server ? 'not_configured' : 'live_only'), // v3.26: on a host only
  'auth.solo_switch': () => fail(RUNTIME.server ? 'not_configured' : 'live_only'), // v3.26: a sold copy's two doors — on its host only
  // official connections of the subscriber's channels (WhatsApp Business, Instagram, Google Calendar…)
  'integrations.list': (p, c) => { needUser(c); return c.tenant ? store.get(`set:${c.tenant.id}:connections`, {}) : {}; },
  'integrations.connect': (p, c) => {
    needUser(c); needWritable(c); if (!['owner', 'admin', 'manager'].includes(c.user.role)) fail('forbidden'); const ch = R.CHANNELS.find(x => x.id === p.channel); if (!ch) fail('not_found');
    const key = `set:${c.tenant.id}:connections`; const conns = store.get(key, {}); conns[ch.id] = { status: 'pending', at: nowIso(), by: c.user.id }; store.set(key, conns);
    const job = queueJob(c, { service: 'integrations', action: 'connect', input: { channel: ch.id, kind: ch.kind } }); audit(c, { op: 'integrations.connect', path: ch.id }); return { queued: true, job };
  },
  'integrations.disconnect': (p, c) => {
    needUser(c); needWritable(c); if (!['owner', 'admin', 'manager'].includes(c.user.role)) fail('forbidden'); const key = `set:${c.tenant.id}:connections`; const conns = store.get(key, {}); if (!conns[p.channel]) fail('not_found');
    delete conns[p.channel]; store.set(key, conns); queueJob(c, { service: 'integrations', action: 'disconnect', input: { channel: p.channel } }); audit(c, { op: 'integrations.disconnect', path: p.channel }); return { ok: true };
  },
  // notices under the bell (per user: managers see office events, everyone sees his own results)
  'notices.list': (p, c) => {
    needUser(c); if (!c.tenant) return { items: [], unread: 0 }; const mgr = ['owner', 'admin', 'manager'].includes(c.user.role);
    const mine = rowsOf(c.tenant.id, 'notices').filter(n => n.to === 'all' || n.to === c.user.id || (n.to === 'managers' && mgr));
    return { items: mine.slice(0, Math.min(+p.limit || 50, 200)).map(({ read_by, ...n }) => ({ ...n, read: (read_by || []).includes(c.user.id) })), unread: mine.filter(n => !(n.read_by || []).includes(c.user.id)).length };
  },
  'notices.read': (p, c) => {
    needUser(c); if (!c.tenant) return { ok: true }; const list = rowsOf(c.tenant.id, 'notices'); const ids = Array.isArray(p.ids) ? p.ids : null;
    for (const n of list) if (!ids || ids.includes(n.id)) { n.read_by = [...new Set([...(n.read_by || []), c.user.id])].slice(-50); }
    saveRows(c.tenant.id, 'notices', list); return { ok: true };
  },
  // the automation side proves itself: which ops the server implements, and its health (generic, rendered as-is)
  'system.ops': (p, c) => { needDev(c); return { ops: [...new Set([...Object.keys(OPS), ...Object.keys(RUNTIME.ops || {})])].sort(), version: VERSION, server: RUNTIME.server }; },
  'system.health': (p, c) => {
    needPerm(c, 'monitoring'); const jobs = store.get('jobs', []); const n = s => jobs.filter(j => j.status === s).length;
    return { version: VERSION, mode: CFG.mode, server: RUNTIME.server, tenants: tenants().length, users: users().length, jobs: { waiting_link: n('waiting_link'), queued: n('queued'), running: n('running'), failed: n('failed') }, vault: RUNTIME.seal ? 'encrypted' : RUNTIME.server ? 'plain' : 'none', ...(RUNTIME.health ? RUNTIME.health() : {}) };
  },

  // ---- the assistants (v3.8: Dar Mind, assets/mind.js — the AI alone: no command reader, no rule-made answer, no ready list)
  // «one message», the pop-up, the developer's assistant and WhatsApp: words, look-ups, a checked plan, small safe changes
  // done at once with Undo; when no AI provider answers now, {pending} — the screen keeps the request and asks again
  'ai.command': (p, c) => { needUser(c); return mindTurn(p, c, p.channel === 'whatsapp' ? 'whatsapp' : c.user.app === 'developer' ? 'dev' : 'command'); },
  'ai.chat': (p, c) => { needUser(c); return mindTurn(p, c, MIND_SURF.includes(p.surface) ? p.surface : 'chat'); },
  // v3.7: the automation screen's assistant — every operation of the developer's assistant, of the automation engine, the
  // node library and the AI developer; nothing runs here (the dangerous steps wait for an explicit tick)
  'flow.assist': async (p, c) => { needPerm(c, 'automation'); const r = await mindTurn({ ...p, ctx: 'automation' }, c, 'flow'); return r.llm ? { ...r, by: 'ai' } : r; },
  'insight.run': (p, c) => {
    needUser(c); const map = { today: 'today', intel: 'intel_score', twin: 'digital_twin', partner: 'p_dashboard', builder: 'b_dashboard', provider: 'pr_dashboard', pulse: c.app === 'builders' ? 'b_dashboard' : 'today' }; // (v3.30: the business's pulse, on its home)
    const sid = map[p.name]; if (!sid) fail('not_found'); const svc = catalog(getP()).find(s => (s.id === sid || s.share === sid) && s.app === c.app) || catalog(getP()).find(s => s.id === sid);
    if (!svc || svc.app !== c.app || !roleAllows(c.app, c.user.role, svc, getP())) fail('forbidden'); const st = access(svc, accessCtx(c)); if (st !== 'ok') fail(st === 'plan' ? 'not_in_plan' : 'service_suspended');
    const ctx = computeCtx(c, p.input || {}); const fn = INSIGHTS[p.name]; const out = fn(ctx, p.id);
    // v3.2: the developer app names the office tools its own way (b_leads…); its "properties" are its units
    if (c.app === 'builders' && out && typeof out === 'object') { const m = x => x && x.svc ? { ...x, svc: x.svc === 'properties' ? 'b_units' : svcIn('builders', x.svc) } : x; if (Array.isArray(out.subs)) out.subs = out.subs.map(m); if (out.bottleneck) out.bottleneck = m(out.bottleneck); if (Array.isArray(out.steps)) out.steps = out.steps.map(m); }
    return out;
  },
  // ---- first-run questionnaire → menu + style (computed on the server from the answers)
  'onboarding.get': (p, c) => { needUser(c); const cfg = onboardingFor(c.app, getP()); return { cfg, state: c.tenant ? store.get(`set:${c.tenant.id}:onboarding`, null) : null }; },
  'onboarding.save': (p, c) => {
    needUser(c); needWritable(c); if (!['owner', 'admin', 'manager'].includes(c.user.role)) fail('forbidden');
    const cfg = onboardingFor(c.app, getP()); if (!cfg) fail('not_found');
    const answers = {}; const src = p.answers || {};
    for (const q of cfg.questions || []) { const picked = [].concat(src[q.id] || []).map(String).filter(id => (q.options || []).some(o => o.id === id)); answers[q.id] = q.type === 'single' ? picked.slice(0, 1) : picked; if (!p.skip && q.req && !answers[q.id].length) fail('validation', { [q.id]: 'required' }); }
    const { services, style, rec: sug } = p.skip ? { services: null, style: { ...DEFAULT_STYLE }, rec: [] } : computeMenu(cfg, answers);
    const known = id => catalog(getP()).some(s => s.id === id && s.app === c.app);
    const valid = services && services.filter(known);
    // v3.30 (the owner, 2026-10-16: «الخدمات … موجودة في واجهات المشتركين ولكنها غير موجودة في واجهات المشترين … تأكد انك فعلتها كلها»), and
    // v3.32.1 for the platform's subscribers too (2026-10-22: «لماذا خدمات المشتركين ناقص؟! مثل ربط واتسابهم بالمنصة من خلال QR وغيرها»):
    // every service stays in the menu whatever the answers — they set the assistant's style and focus, suggest, and put the services
    // they point to at the top (his pins, when he has none yet); only what he takes out of the menu himself («كل خدماتك») leaves it
    const prev = store.get(`set:${c.tenant.id}:onboarding`, null);
    const rec = { done: true, at: nowIso(), answers: p.skip ? {} : answers, services: null, top: (valid || []).slice(0, 60), hidden: Array.isArray(prev?.hidden) ? prev.hidden : [], rec: (sug || []).filter(known), style: { ...DEFAULT_STYLE, ...cleanStyle(style) }, by: c.user.id };
    if (valid && !p.skip) {
      const pk = `set:${c.tenant.id}:pins_${c.user.id}_${c.app}`; const always = new Set(cfg.always || []);
      const home = { app: 'today', builders: 'b_dashboard', providers: 'pr_dashboard' }[c.app];
      const top = valid.filter(id => !always.has(id) && id !== home).slice(0, 8);
      const had = store.get(pk, []); if (!(Array.isArray(had) && had.length) && top.length) store.set(pk, top);
    }
    store.set(`set:${c.tenant.id}:onboarding`, rec); audit(c, { op: 'onboarding', path: p.skip ? 'skip' : Object.keys(answers).join(','), after: { services: valid ? valid.length : 'all' } });
    if (c.app === 'providers' && answers.categories?.length) { const list = tenants(); const T = list.find(x => x.id === c.tenant.id); T.category = answers.categories[0]; T.categories = +planLimits(c).categories ? answers.categories.slice(0, +planLimits(c).categories) : answers.categories; saveTenants(list); }
    return rec;
  },
  'menu.set': (p, c) => {
    needUser(c); needWritable(c); if (!['owner', 'admin', 'manager'].includes(c.user.role)) fail('forbidden');
    const all = catalog(getP()).filter(s => s.app === c.app); const svc = all.find(s => s.id === p.service); if (!svc && !['reset', 'style'].includes(p.action)) fail('not_found');
    const key = `set:${c.tenant.id}:onboarding`; const rec = store.get(key, null) || { done: true, answers: {}, style: { ...DEFAULT_STYLE } };
    if (p.action === 'reset') { rec.services = null; rec.by_store = false; rec.hidden = []; }
    else if (p.action !== 'style') { const hid = new Set(Array.isArray(rec.hidden) ? rec.hidden : []); if (p.action === 'remove') hid.add(svc.id); else hid.delete(svc.id); rec.hidden = [...hid]; rec.services = null; rec.by_store = true; } // (v3.32.1: what he took out, and only that — a service added later is in his menu by itself)
    if (p.style && typeof p.style === 'object') rec.style = { ...DEFAULT_STYLE, ...(rec.style || {}), ...cleanStyle(p.style) };
    rec.done = true; store.set(key, rec); audit(c, { op: 'menu', path: (p.action || 'add') + ':' + (p.service || '') }); return rec;
  },
  // ---- translations the developer asks for (texts, services, landings, questions) → the AI translator fills missing languages after linking
  // v3.2: translations found on the developer's device (Dar's own texts, the browser's translator) — same paths, empty languages only
  'i18n.apply': (p, c) => { needDev(c); const items = (Array.isArray(p.items) ? p.items : []).slice(0, 500).filter(x => x && typeof x.path === 'string'); if (!items.length) fail('validation', { items: 'required' }); return OPS['platform.set']({ changes: items.map(x => ({ path: x.path, value: x.values ?? x.value })), label: p.label || 'translations' }, c); },
  'i18n.translate': (p, c) => { needDev(c); const items = (p.items || []).slice(0, 500); if (!items.length) fail('validation', { items: 'required' }); const job = queueJob(c, { service: 'd_texts', action: 'translate', input: { items } }); audit(c, { op: 'job', path: 'i18n.translate', rid: job.id }); return { queued: true, job }; },
  // v2.5.1: inbound WhatsApp — the automation forwards each Cloud API webhook body with the master key (see waInbound)
  'whatsapp.inbound': (p, c) => waInbound(p, c),
  'files.upload': (p) => { const s = String(p.data || ''); if (!s.startsWith('data:')) fail('bad_request'); if (s.length > 1.5e6) fail('file_too_big'); return { url: s }; },
  // v2.6.2: direct-to-storage upload. The contract checks the session and hands back a tenant-scoped object key;
  // the server signs a short-lived URL with its own secret (RUNTIME.signStorage), so the file never passes through
  // the server and no key reaches the browser. Without object storage (in-browser model, or a server with none),
  // it answers { enabled: false } and the caller falls back to files.upload (data URL).
  'files.sign': (p, c) => {
    needUser(c);
    if (!RUNTIME.signStorage) return { enabled: false };
    const kind = p.kind === 'get' ? 'get' : 'put';
    const scope = c.tenant?.id || 'platform';
    let key;
    if (kind === 'get') { key = String(p.key || '').replace(/^\/+/, '').slice(0, 200); }
    else { const ext = (String(p.name || '').match(/\.[A-Za-z0-9]{1,8}$/) || [''])[0].toLowerCase(); key = `${scope}/${nowIso().slice(0, 10)}/${uid('f')}${ext}`; }
    if (!key || !key.startsWith(scope + '/')) fail('forbidden'); // an office reads and writes only under its own prefix
    const r = RUNTIME.signStorage(key, { kind, contentType: String(p.content_type || '').slice(0, 100) });
    return { enabled: true, key, method: kind === 'get' ? 'GET' : 'PUT', upload_url: r.url, public_url: r.publicUrl };
  },
};

// v2.1 operations (team accounts, attendance clock, e-signature, uploads, portals, booking, inbox, workflows…)
const EXT = extOps({ rowsOf, saveRows, audit, fail, needUser, needWritable, getP, tenants, users, saveUsers, uid, nowIso, DAY, randomHex, hashPassword, issueToken, publicUser, queueJob, store, R, CFG, selfName, notify, tzOf, demoLocked, t, intlPhone, refAttr: (...a) => REF.attribute(...a) });
Object.assign(OPS, EXT.OPS);
// v3.30 (the owner, 2026-10-15, of the referral programme and the wallet: «أعدهما معدّلتين»): in a sold copy, the business's own —
// its clients bring it clients through their own links, and the rewards its owner sets wait in the wallet (assets/refer.js)
const cleanIdx = u => String(u).replace(/\/index\.html(?=[?#]|$)/, '/'); // (a link people share has no «index.html» in it)
const REF = referOps({ rowsOf, saveRows, audit, fail, needUser, needWritable, guard: (c, coll, w) => guardCollection(c, coll, w), uid, nowIso, randomHex, store, notify, t, tenants, demoLocked, OPS, officeCard, listingUrl: (T, id) => listingUrl(T, id),
  refUrl: code => cleanIdx(absUrl('site', { ref: code })), siteUrl: q => cleanIdx(absUrl('site', q)), pageUrl: (page, q) => cleanIdx(absUrl(page, q)), imgOk: u => IMG_OK.test(String(u || '')) && String(u).length < 400000, isEx: r => isStarterRow(r),
  link: (c, kind, params) => O32.snapshotLink(c, kind, params), runAuto: (...a) => EXT.runAutomations(...a) }); // (v3.30: and the marketers on commission — their page mk/?k=…)
Object.assign(OPS, REF.OPS);
{ const cat0 = OPS['public.catalog']; OPS['public.catalog'] = p => { const r = cat0(p); try { const mk = OPS['public.marketer.info']({ t: p.t }); if (mk.open) r.mk = { open: true, intro: mk.intro, rate: mk.rate, base: mk.base, builder: mk.builder, approval: mk.approval, terms: mk.terms }; } catch { /* no programme */ } return r; }; } // v3.30: the office page's link to join the marketers
{ const aw = EXT.afterWrite; EXT.afterWrite = (c, coll, rec, before) => { aw(c, coll, rec, before); try { REF.afterWrite(c, coll, rec, before); } catch (e) { console.warn('referral', e?.code || e); } }; } // (a reward never stops the change it follows)
// ---- v3.30 — the buyers' preview's example server (assets/exsrv.js).
// The owner (2026-10-16: «الخدمات ناقصة … موجودة في واجهات المشتركين ولكنها غير موجودة في واجهات المشترين … وتأكد انك فعلتها كلها»): the
// example administration's sections that work on an installed copy's own server — the self-check, backups, the code editor, the AI
// link, the automation engine, the growth engine, the knowledge library … — work in the example too. An example account's calls to the
// operations only a server answers are answered by the example server in the visitor's browser, from example data kept there: nothing
// of them reaches the real server, and nothing they do is done outside this browser. (Only a page of the preview ever loads it.)
export const EXN = Symbol('not an example operation');
let EXS = null;
export async function exampleCall(op, payload, app, token) {
  if (!SHOW || !token) return EXN;
  let c; try { c = ctxOf(app, token); } catch { return EXN; } if (!c.user?.demo) return EXN;
  EXS ||= import('./exsrv.js?v=3.34.0-d66b90ae').then(m => m.exampleServer({ rowsOf, saveRows, audit, fail, getP, tenants, users, uid, nowIso, DAY, randomHex, store, R, CFG, OPS }));
  const fn = await (await EXS).find(op); if (!fn) return EXN;
  return fn(payload || {}, c, token);
}
// ---- v2.5.2: server implementations of the password-reset link and the login code (model mode keeps live_only)
function needsLoginCode(u, app) {
  const mode = getP().security?.login_code || 'off';
  return mode === 'all' || (mode === 'developers' && app === 'developer') || (mode === 'managers' && (app === 'developer' || ['owner', 'admin', 'manager'].includes(u.role)));
}
async function startLoginCode(u, c, id0) {
  const code = String(100000 + (parseInt(randomHex(4), 16) % 900000)); const id = id0 || 'v' + randomHex(10); const now = Date.now();
  const vs = store.get('verifies', {}); for (const [k, v] of Object.entries(vs)) if (v.exp < now) delete vs[k];
  vs[id] = { uid: u.id, app: c.app, hash: await sha256(id + ':' + code), exp: now + 10 * 60e3, tries: 0, sent: now }; store.set('verifies', vs);
  const T = tenants().find(x => x.id === u.tenant);
  queueJob({ ...c, user: null, tenant: null }, { service: 'auth', action: 'login_code', input: { verify_id: id, code, email: u.email || '', phone: u.phone || '', country: T?.country || '', lang: knownLang(u.lang) ? u.lang : LANG.cur } });
  const m = String(u.email || ''); return { needs_verify: true, verify_id: id, sent_to: m ? m.replace(/^(.).*(@.*)$/, '$1***$2') : '***' + String(u.phone || '').slice(-3) };
}
const LIVE_ONLY_AUTH = { verify: OPS['auth.verify'], resend: OPS['auth.resend'], reset: OPS['auth.reset_confirm'] };
OPS['auth.reset_confirm'] = async (p, c) => {
  // v3.2: the same check with or without a server (the model's link is made in this browser)
  const tok = String(p.token || ''); const resets = store.get('resets', {}); const h = await sha256(tok); const r = resets[h];
  if (!tok || !r || r.exp < Date.now()) fail('validation', { token: 'expired' });
  if (String(p.password || '').length < pwMin()) fail('validation', { password: 'short' });
  const list = users(); const u = list.find(x => x.id === r.uid); if (!u) fail('not_found');
  u.salt = randomHex(12); u.hash = await hashPassword(String(p.password), u.salt); saveUsers(list);
  delete resets[h]; store.set('resets', resets);
  const tokens = store.get('tokens', {}); for (const [k, v] of Object.entries(tokens)) if (v.uid === u.id) delete tokens[k]; store.set('tokens', tokens); // every open session of that person ends
  audit({ ...c, user: u }, { op: 'auth.reset_confirm' }); return { ok: true };
};
OPS['auth.verify'] = async (p, c) => {
  if (!RUNTIME.server) return LIVE_ONLY_AUTH.verify(p, c);
  const id = String(p.verify_id || ''); const vs = store.get('verifies', {}); const v = vs[id];
  if (!v || v.exp < Date.now() || v.app !== c.app) fail('validation', { code: 'expired' });
  if (v.tries >= 5) { delete vs[id]; store.set('verifies', vs); fail('rate_limited'); }
  if (v.hash !== await sha256(id + ':' + latinDigits(String(p.code || '')).replace(/\D/g, ''))) { v.tries++; store.set('verifies', vs); fail('validation', { code: 'wrong' }); }
  delete vs[id]; store.set('verifies', vs);
  const u = users().find(x => x.id === v.uid); if (!u || u.status === 'inactive') fail('forbidden');
  const token = issueToken(u, c.app); audit({ ...c, user: u }, { op: 'auth.login', path: 'code' });
  return { token, user: publicUser(u), tenant: tenants().find(x => x.id === u.tenant) || null };
};
OPS['auth.resend'] = async (p, c) => {
  if (!RUNTIME.server) return LIVE_ONLY_AUTH.resend(p, c);
  const id = String(p.verify_id || ''); const v = store.get('verifies', {})[id];
  if (!v || v.exp < Date.now() || v.app !== c.app) fail('validation', { code: 'expired' });
  if (Date.now() - v.sent < 60e3) fail('rate_limited');
  const u = users().find(x => x.id === v.uid); if (!u) fail('not_found');
  await startLoginCode(u, c, id); return { ok: true };
};
// v2.2 operations (Universal Migration Agent, Market Radar → Dar Intelligence, secrets vault)
const EXT3 = extOps3({ hostedNet: p => (CFG.mode === 'hosted' && HOSTED.market ? HOSTED.market(p) : null), isHosted: () => CFG.mode === 'hosted' && !!HOSTED.call, rowsOf, saveRows, audit, fail, needUser, needWritable, needPerm, getP, tenants, uid, nowIso, DAY, queueJob, store, R, fieldsOf, cleanRow, guardCollection, planLimits, LIMIT_COLL, notify, isServer: () => RUNTIME.server, seal: v => (RUNTIME.seal ? RUNTIME.seal(v) : v), unseal: v => (RUNTIME.open ? RUNTIME.open(v) : v), catalog, access, accessCtx, roleAllows });
Object.assign(OPS, EXT3.OPS);
// v2.6 operations: the account's own AI memory and the privacy-preserving learning loop (assets/learn.js)
const LEARN = learnOps({ rowsOf, saveRows, audit, fail, needUser, needWritable, needPerm, devPerms, getP, tenants, users, uid, nowIso, DAY, store, notify, isAiJob: j => isAiJob(j), R });
Object.assign(OPS, LEARN.OPS);
// v3.1: cities and districts of every country (OpenStreetMap, fetched once and kept for everyone — assets/geo-ops.js)
const GEO = geoOps({ store, getP, fail, needUser, rowsOf, tenants, DAY, lang: () => LANG.cur, isServer: () => RUNTIME.server, countryOf: c => String(c?.tenant?.country || api.country || getP().default_country || '').toUpperCase(),
  server: (op, p) => (CFG.mode === 'hosted' && HOSTED.places ? HOSTED.places(op, p) : null), langsOf: cc => R.WORLD?.[cc]?.langs || [] }); // v3.17: the site's server answers the map's questions once for everyone
Object.assign(OPS, GEO.OPS);
// v3.1: the system learns each person's preferences from how they work, inside their own account (assets/behavior.js)
const langOfTenant = T => { const o = users().find(u => u.tenant === T.id && u.role === 'owner'); return knownLang(o?.lang) ? o.lang : knownLang(R.WORLD[T.country]?.lang) ? R.WORLD[T.country].lang : 'en'; };
const BEHAVIOR = behaviorOps({ store, getP, fail, needUser, rowsOf, saveRows, tenants, uid, nowIso, DAY, tzOf, langOf: langOfTenant, label: (f, v, l) => (OPTS[v] || [])[Math.max(0, ['ar', 'en', 'fr'].indexOf(l)) || (isBaseLang(l) ? 0 : 1)] || v, curOf: T => countryBy(T.country, rowsOf('platform', 'countries'), getP()).currency || R.WORLD[T.country]?.cur || '' });
Object.assign(OPS, BEHAVIOR.OPS);
// v3.28 — «موقعي»: its starting pages (assets/webtpl.js), and what is published of it — a copy of its pages, sections and settings
// at the moment he publishes, which the site's server shows at its own link (dar-web.php) with the account's live listings
const WEB_PAGE_F = ['id', 'title', 'path', 'page_kind', 'in_menu', 'sort', 'seo_title', 'seo_desc', 'seo_image', 'no_index']; // (v3.33.31: a share picture of its own, and hidden from search)
const WEB_SEC_F = ['id', 'page', 'block', 'sort', 'title', 'body', 'lines', 'image', 'button_label', 'button_link', 'style', 'filter', 'effect', 'layout', 'css_class', 'html', 'video']; // (v3.31: a video or 3D tour's link) // (v3.28: how it enters the view, its shape, his class and his own HTML)
const pickF = (r, F) => Object.fromEntries(F.filter(k => r[k] !== undefined && r[k] !== '').map(k => [k, r[k]]));
const needWebManager = c => { needUser(c); needWritable(c); if (!c.tenant || c.user.app === 'developer') fail('forbidden'); if (!MANAGER_ROLE.includes(roleOf(c))) fail('forbidden', { role: c.user.role }); };
Object.assign(OPS, {
  'website.get': (p, c) => { needUser(c); if (!c.tenant) fail('forbidden'); return { settings: webGet(c), pub: webPubInfo(c.tenant.id), pages: rowsOf(c.tenant.id, 'site_pages').length, sections: rowsOf(c.tenant.id, 'site_sections').length }; },
  // a whole starting website, written for this kind of business in his language — never over pages he already has unless he asks
  'website.start': (p, c) => {
    needWebManager(c); const T = c.tenant; const have = rowsOf(T.id, 'site_pages');
    if (have.length && p.replace !== true) fail('exists', { pages: have.length });
    const set = webRaw(c); const lang = knownLangCode(p.lang) ? p.lang : set.lang;
    const tpl = webTemplate(audienceOf(c.app) === 'builder' ? 'builder' : 'office', lang, { name: T.name || '', city: T.city || '' });
    if (p.replace === true) { saveRows(T.id, 'site_sections', []); saveRows(T.id, 'site_pages', []); }
    const now = nowIso(); const pages = tpl.pages.map(x => ({ id: uid('r'), created: now, updated: now, ...x }));
    const sections = tpl.sections.map(x => ({ id: uid('r'), created: now, updated: now, ...x, page: pages[x.page].id }));
    saveRows(T.id, 'site_pages', pages); saveRows(T.id, 'site_sections', sections);
    // (the ready designs are written in Arabic, English and French — in any other language the English one, and the site says so: its
    // visitors in his language read it translated by his AI, and his AI can write it in his own language from «أعد كتابة موقعي»)
    const eff = isBaseLang(lang) ? lang : 'en'; const cur = store.get(`set:${T.id}:website`, null);
    if (!cur || cur.lang !== eff) store.set(`set:${T.id}:website`, cleanWebsite({ ...set, lang: eff, slug: set.slug || '' }));
    audit(c, 'website.start', `${pages.length} pages`);
    return { pages: pages.length, sections: sections.length, lang: eff };
  },
  'website.publish': (p, c) => {
    needWebManager(c); const T = c.tenant; const set = webRaw(c); // (v3.31: what it leaves empty stays the business's own, read at every visit)
    if (!set.slug) fail('validation', { slug: 'required' });
    const pages = rowsOf(T.id, 'site_pages').filter(x => x.visible !== false); if (!pages.length) fail('validation', { pages: 'required' });
    const ids = new Set(pages.map(x => x.id)); const sections = rowsOf(T.id, 'site_sections').filter(x => ids.has(x.page) && x.visible !== false);
    const prev = store.get(`set:${T.id}:website_pub`, {}) || {}; const v = (+prev.v || 0) + 1;
    const pub = { v, at: nowIso(), by: String(c.user.name || '').slice(0, 80), settings: cleanWebsite(set), pages: pages.map(x => pickF(x, WEB_PAGE_F)), sections: sections.map(x => pickF(x, WEB_SEC_F)), off: false };
    if (JSON.stringify(pub).length > 3000000) fail('file_too_big');
    store.set(`set:${T.id}:website_pub`, pub); audit(c, 'website.publish', `v${v} · ${set.slug}`);
    return { v, at: pub.at, slug: set.slug, pages: pages.length, sections: sections.length };
  },
  'website.unpublish': (p, c) => { needWebManager(c); const k = `set:${c.tenant.id}:website_pub`; const prev = store.get(k, null); if (!prev?.v) fail('not_found'); store.set(k, { ...prev, off: true, at: nowIso() }); audit(c, 'website.unpublish', String(prev.v)); return { off: true, v: prev.v }; },
});
{ const forgetMem = OPS['memory.forget']; OPS['memory.forget'] = (p, c) => { const r = forgetMem(p, c); if (p?.all && c?.tenant) BEHAVIOR.forget(c.tenant.id); return r; }; } // «forget everything» includes the learned profile
export const geoTest = { setFetch: fn => GEO.setFetch(fn), setTiming: o => GEO.setTiming(o), settle: () => GEO.settle(), reset: () => GEO.reset() };
export const behaviorTest = { daily: (T, force) => BEHAVIOR.daily(T, force), compact: c => BEHAVIOR.compact(c) };
// v2.5.2 / v3.21: an account's erasure once its deletion is due — asked by its owner (30 days after), or by the billing cycle
// (60 days read-only, assets/billing.js). Business data, people, sessions, keys, jobs and the account's audit lines go; its
// invoices (binv:<id>) and payments stay, as the accounting laws want — v3.22: a partner's commissions and payouts too; a
// tombstone keeps id/app/country/plan/dates (and a partner's code).
function purgeTenant(id, c) {
  const list = tenants(); const T = list.find(x => x.id === id); if (!T) fail('not_found');
  if (T.status === 'deleted') return { ok: true, id: T.id, already: true };
  if (!T.deletion || !(new Date(T.deletion.after).getTime() <= Date.now())) fail('validation', { deletion: 'not_due' });
  const kept = new Set([`db:${T.id}:p_commissions`, `db:${T.id}:p_payouts`]); // (v3.22: a partner's commissions and payouts stay — a payout he asked for is still paid)
  for (const k of [...store.keys(`db:${T.id}:`), ...store.keys(`set:${T.id}:`), ...store.keys(`pstat:${T.id}`)]) if (!kept.has(k)) store.del(k);
  for (const k of store.keys('keyidx:')) { if (store.get(k, {})?.tenant === T.id) store.del(k); }
  const gone = users().filter(u => u.tenant === T.id).map(u => u.id); saveUsers(users().filter(u => u.tenant !== T.id));
  const tokens = store.get('tokens', {}); for (const [k, v] of Object.entries(tokens)) if (gone.includes(v.uid)) delete tokens[k]; store.set('tokens', tokens);
  store.set('jobs', store.get('jobs', []).filter(j => j.tenant !== T.id)); store.set('audit', store.get('audit', []).filter(a => a.tenant !== T.id));
  const keep = { id: T.id, app: T.app, audience: T.audience, country: T.country, plan: T.plan, created: T.created, attribution: T.attribution || '', ...(T.code ? { code: T.code } : {}) }; // (v3.22: a partner's code stays his)
  for (const k of Object.keys(T)) delete T[k]; Object.assign(T, keep, { name: '', status: 'deleted', deleted_at: nowIso(), deletion: { done: nowIso() } });
  saveTenants(list); audit(c, { op: 'tenants.purge', rid: T.id }); return { ok: true, id: T.id, removed_users: gone.length };
}
// v3.13.2: the money cycle without a card gateway — payments by transfer, the subscription's lifecycle, commissions on the money
// received (assets/billing.js; on a host the server runs the same, dar-billing.php)
const BILL = billingOps({ rowsOf, saveRows, audit, fail, needUser, needPerm, getP, tenants, saveTenants, users, uid, nowIso, DAY, store, R, notify, countryBy, billCur, fxOf, asSystem, isHosted: isHostedNow, listPrice, purge: id => purgeTenant(id, { app: 'developer', user: { id: 'billing', name: 'billing' }, tenant: null }) });
Object.assign(OPS, BILL.OPS);
export const billingTest = { tick: ms => BILL.tick(ms) };

// v3.2: every action that waited for a "link" runs now — from the office's own accounts and open standards (assets/acts32.js,
// assets/ops32.js, assets/deliver.js, assets/einvoice.js, assets/feeds.js, assets/agent.js, assets/relay.js)
extendBrain(ACTS32);
let FETCH32 = (...a) => globalThis.fetch(...a);
function absUrl(appId, q = {}) {
  const P = getP(); let base = publicUrl(appId, P);
  if (!base) { const rel = appLink(appId, P).replace(/#.*$/, ''); try { base = typeof location !== 'undefined' ? new URL(rel, location.href).href : rel; } catch { base = rel; } }
  const qs = Object.entries(q || {}).filter(([, v]) => v !== '' && v != null).map(([k, v]) => encodeURIComponent(k) + '=' + encodeURIComponent(v)).join('&');
  return base + (qs ? (base.includes('?') ? '&' : '?') + qs : '');
}
const officeOf = c => { const T = c?.tenant; if (!T) return {}; const prof = store.get(`set:${T.id}:profile`, {}); return { ...officeCard(T), email: /^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/.test(prof.email || '') ? prof.email : '', address: String(prof.address || '').slice(0, 160), brand: brandOf(T)?.color || '' }; };
O32 = ops32({ agentAI, rowsOf: (tid, coll) => coll === 'properties' && tid && tid !== 'platform' ? withOccupancy(tid, rowsOf(tid, coll)) : rowsOf(tid, coll), saveRows, audit, fail, needUser, needWritable, getP, tenants, uid, nowIso, DAY, store, R, notify, OPS, asSystem, intlOf: (c, ph) => intlPhone(ph, c?.tenant?.country), officeOf, isServer: () => RUNTIME.server, isLive: () => !!RUNTIME.server || CFG.mode === 'live', computeCtx: (c, i) => actCtx(c, i), appUrl: absUrl, catalog, access, accessCtx, roleAllows, sha256, lang: () => LANG.cur, fetch: (...a) => FETCH32(...a), hosted: HOSTED });
Object.assign(OPS, O32.OPS);
// the context the action executors receive: the usual computeCtx plus delivery helpers
function actCtx(c, input) {
  const ctx = computeCtx(c, input || {}); const T = c.tenant;
  ctx.listingUrl = id => listingUrl(T, id);
  ctx.intl = ph => intlPhone(ph, T?.country);
  ctx.office = officeOf(c);
  ctx.live = !!RUNTIME.server || CFG.mode === 'live';
  ctx.hosted = CFG.mode === 'hosted'; // v3.5: the site's own server (its mail sends an office's campaign)
  ctx.appUrl = (appId, q) => absUrl(appId, q);
  ctx.link = async (kind, params = {}) => { try { return await O32.snapshotLink(c, kind, params); } catch { return kind === 'listing' ? listingUrl(T, params.id) : absUrl('o', { t: T?.id }); } };
  ctx.geo = { amenities: (city, district) => GEO.amenities ? GEO.amenities(city, district, T?.country) : null };
  ctx.feedUrl = fmt => { const base = RUNTIME.publicUrl || RUNTIME.reqBase || CFG.apiBase; return RUNTIME.server && base && T ? `${base.replace(/\/$/, '')}/feed/${T.id}-${O32.relayToken(T.id)}/${fmt}.xml` : ''; }; // the server's own address (PUBLIC_URL)
  // v3.4: on a PHP host with Dar Sync the office's engine publishes each feed and the host serves it at the same kind of address
  ctx.hostedFeed = CFG.mode === 'hosted' && HOSTED.pub && T && ['app', 'builders'].includes(T.app) ? async fmts => {
    const out = []; for (const fmt of fmts) { const b = await O32.buildSnap(c, 'feed', { fmt }, true); if (!await HOSTED.pub('feed', { fmt }, b)) return []; let base = ''; try { base = new URL(CFG.root || './', typeof location !== 'undefined' ? location.href : 'https://dar.invalid/').href; } catch { base = ''; } out.push(`${base.replace(/\/$/, '')}/feed/${T.id}-${O32.relayToken(T.id)}/${fmt}.xml`); }
    return out;
  } : null;
  return ctx;
}
export const acts32Test = { setFetch: fn => { FETCH32 = fn; }, settleHooks: () => Promise.allSettled([...HOOKS_INFLIGHT]), actCtx: (c, i) => actCtx(c, i) };

const LOCAL_ACTS = {
  'maintenance.request_provider': (input, c) => { const rec = OPS['market.request']({ row: input }, c); return { kind: 'text', title: t('request_sent'), text: rec.title, note: t('request_sent_note') }; },
  // v3.2: the office's own domain — where its DNS points now (public DNS-over-HTTPS, no key) and what is left to do
  'white_label.dns_check': async (input, c) => {
    const w = store.get(`set:${c.tenant.id}:white_label`, {}); const host = cleanHost(input.host || w.custom_domain || c.tenant.domain || ''); if (!host) return { kind: 'empty', text: t('wl_no_domain') };
    const target = cleanHost(getP().cname_target || '') || (typeof location !== 'undefined' ? location.hostname : '');
    const ask = async type => { const r = await FETCH32(`https://cloudflare-dns.com/dns-query?name=${encodeURIComponent(host)}&type=${type}`, { headers: { accept: 'application/dns-json' } }); const j = await r.json(); return (j.Answer || []).map(x => ({ type, value: String(x.data || '').replace(/\.$/, '') })); };
    let rec = []; try { rec = [...await ask('CNAME'), ...await ask('A')]; } catch { return { kind: 'text', title: t('wl_domain'), text: t('dns_unreachable') }; }
    const ok = rec.some(r => r.type === 'CNAME' && cleanHost(r.value) === target);
    return { kind: 'multi', title: host, parts: [{ kind: 'table', cols: [{ key: 'type', label: ['النوع', 'Type', 'Type'] }, { key: 'value', label: ['القيمة', 'Value', 'Valeur'] }], rows: rec.length ? rec : [{ type: '—', value: t('dns_none') }] }, { kind: 'text', text: ok ? t('dns_ok', { host, target }) : t('dns_todo', { host, target: target || '—' }) }] };
  },
  'api_enterprise.accounting_export': (input, c) => accountingExport(actCtx(c, input)),
  // v3.5: a price estimate — own and tracked market listings first; on the hosted site, the Dar network's anonymous medians next
  'pricing_engine.estimate': async (input, c) => {
    // v3.33.1 (the owner — note 57: «محرك التسعير يجب أن يعمل بناءً على المعلومات الخارجية من شتى المواقع ومحركات البحث»): on the hosted
    // site the web is searched first (the listing portals and the search engines, through the AI that searches — dar-sync.php op_market_web);
    // what it found joins the account's own listings and its radar, and its sources are listed with their links
    let web = null;
    if (CFG.mode === 'hosted' && HOSTED.marketWeb && !SHOW && input?.city && input?.type) { try { web = await Promise.race([HOSTED.marketWeb({ city: input.city, district: input.district || '', type: input.type, purpose: input.purpose || 'sale', area: input.area || '', bedrooms: input.bedrooms || '' }), new Promise(r => setTimeout(() => r(null), 58000))]); /* (v3.33.17: a search of several pages takes 20–30 seconds — live, 2026-10-24) */ } catch { web = null; } }
    if (web?.listings?.length) input = { ...input, _web: web.listings };
    const ctx = computeCtx(c, input || {}); let res = compute('pricing_engine', 'estimate', ctx);
    if (web && res && typeof res === 'object') {
      const items = (web.sources || []).filter(x => /^https:\/\//.test(x.url)).slice(0, 12).map(x => ({ url: x.url, label: x.title || x.url }));
      const line = [`من الإنترنت الآن: ${web.listings?.length || 0} إعلانًا مشابهًا${web.summary ? ' — ' + web.summary : ''}`, `From the web now: ${web.listings?.length || 0} similar listings${web.summary ? ' — ' + web.summary : ''}`, `Sur le web à l’instant : ${web.listings?.length || 0} annonces similaires${web.summary ? ' — ' + web.summary : ''}`];
      const parts = [...(res.kind === 'multi' ? res.parts : [res]), ...(items.length ? [{ kind: 'links', title: ['مصادر السوق على الإنترنت', 'Market sources on the web', 'Sources du marché sur le web'], items }] : [])];
      res = { ...res, kind: 'multi', parts, note: [...(Array.isArray(res.note) ? res.note : res.note ? [res.note] : []), line] };
    }
    if (res?._market && CFG.mode === 'hosted' && HOSTED.market && !SOLO && !SHOW) { // (v3.26: a copy sold to one business has no network of offices)
      try {
        const r = await HOSTED.market({ segments: [{ city: input.city || '', district: input.district || '', type: input.type || '', purpose: input.purpose || '' }] });
        const x = r?.segs?.[0]; const use = x?.district || x?.city;
        if (use) res = estimateFrom(ctx, { area: +latinDigits(String(input.area)).replace(/[^\d.]/g, ''), ppmLow: use.low, ppmMid: use.ppm, ppmHigh: use.high, rows: [], kpiSuffix: [{ label: ['إعلانات الشبكة', 'Network listings', 'Annonces du réseau'], value: use.n }, { label: ['مكاتب مساهمة', 'Contributing offices', 'Agences contributrices'], value: use.contributors }], note: [`نطاق من أسعار شبكة دار المجمّعة بلا أسماء على مستوى ${x.district ? 'الحي' : 'المدينة'} (${use.n} إعلانًا من ${use.contributors} مكاتب).`, `Range from the Dar network’s anonymous prices at ${x.district ? 'district' : 'city'} level (${use.n} listings from ${use.contributors} offices).`, `Fourchette issue des prix anonymes du réseau Dar (${use.n} annonces, ${use.contributors} agences).`] });
        else if (r && !r.joined) res = { ...res, note: [res.note, ['انضم إلى شبكة دار من «رادار السوق» لتُحسب تقديراتك من أسعار السوق المجمعة بلا أسماء.', 'Join the Dar network from Market radar so estimates use the market’s anonymous prices.', 'Rejoignez le réseau Dar depuis le Radar pour estimer avec les prix anonymes du marché.']] };
      } catch { /* the message above stays */ }
    }
    if (res && typeof res === 'object') delete res._market; return res;
  },
};
// v3.2: a developer's construction updates and buyer statements carry buyer-portal links (a page snapshot on the static site)
for (const [k, fn] of Object.entries(BUILD32_ASYNC)) LOCAL_ACTS[k] = (input, c) => fn(actCtx(c, input));
Object.assign(LOCAL_ACTS, REF.LOCAL); // v3.30: the referral programme's and the wallet's steps, as their services' actions
// v3.30: a sold copy's marketer sends one of his prospects to the business (dar-mk.php «mk.refer»: the client lands in its clients, his)
// and the prospect's stage becomes «referred» on his own list
LOCAL_ACTS['p_leads.refer'] = async (input, c) => {
  needUser(c); if (!(SOLO || SHOW) || c.app !== 'partner') fail('not_available'); if (SOLO && !HOSTED.call) fail('not_available', { why: 'server' });
  const id = String(input?.prospect || ''); const rows = rowsOf(c.tenant.id, 'p_leads'); const l = rows.find(x => x.id === id); if (!l) fail('validation', { prospect: 'required' });
  const r = await api.call('mk.refer', { name: l.name || '', phone: l.phone || '', interest: l.interest || 'buy', note: [input?.note, l.notes].filter(Boolean).join('\n').slice(0, 500) }); // (on a host the business's server answers; in the buyers' preview, the example engine)
  l.stage = 'referred'; l.last_contact = nowIso(); l.updated = nowIso(); saveRows(c.tenant.id, 'p_leads', rows);
  return { kind: 'text', title: l.name || '', text: t(r?.known ? 'mki_refer_known' : 'mki_refer_ok') };
};
function summarize(r, only) { const o = {}; for (const k of Object.keys(only || r)) { if (['id', 'created', 'updated', 'by'].includes(k)) continue; const v = r[k]; o[k] = typeof v === 'string' && v.startsWith('data:') ? '[file]' : Array.isArray(v) ? `[${v.length}]` : v; } return o; }
// (v3.13.2: commissions are earned in assets/billing.js — on the money received, every payment, every kind of account)
// absolute link to a property's public page (QR codes on generated images point here)
function listingUrl(T, id) {
  const P = getP(); let base = publicUrl('l', P);
  if (!base) { const rel = appLink('l', P).replace(/#.*$/, ''); try { base = typeof location !== 'undefined' ? new URL(rel, location.href).href : rel; } catch { base = rel; } }
  return base + (base.includes('?') ? '&' : '?') + 't=' + encodeURIComponent(T?.id || '') + '&id=' + encodeURIComponent(id) + '&src=qr';
}
// what a job keeps of a result: generated images stay in the page (data URLs would fill the store), text is kept
function liteResult(r) {
  if (!r || typeof r !== 'object') return r ?? null;
  const strip = x => { if (!x || typeof x !== 'object') return x; if (x.kind === 'media') return { ...x, items: (x.items || []).map(it => /^data:/i.test(it?.url || '') ? { ...it, url: '', local_image: true } : it) }; if (x.kind === 'multi') return { ...x, parts: (x.parts || []).map(strip) }; if (x.kind === 'files') return { ...x, items: (x.items || []).map(({ data, ...it }) => ({ ...it, size: String(data || '').length })) }; if (x.kind === 'share') { const { image, ...rest } = x; return rest; } if (x.kind === 'qr') { const { svg, ...rest } = x; return rest; } return x; };
  try { const out = strip(r); return JSON.stringify(out).length <= 60000 ? out : { kind: 'text', text: String(out.title || ''), note: out.note || null }; } catch { return null; }
}
// v3.2 — a record whose PDF was read on the device carries its text (_text) for the assistant: search, summary, extraction
function withDocText(tk, coll, rows) {
  const dt = tk ? store.get(`set:${tk}:doctext`, null) : null; if (!dt || !Object.values(dt).some(v => v.coll === coll)) return rows;
  return rows.map(r => dt[r.id] ? { ...r, _text: dt[r.id].text } : r);
}
// v3.5: a property with a running lease or an active tenant reads «rented» in every computation, even before its own
// status was updated (older records); the stored status follows on the next write or scheduled duty
function withOccupancy(tid, rows) {
  const today = new Date().toISOString().slice(0, 10);
  const busy = new Set([...rowsOf(tid, 'leases').filter(l => l.status === 'active' && (!l.end || String(l.end) >= today)).map(l => l.property), ...rowsOf(tid, 'tenants').filter(x => (x.status || 'active') === 'active' && (!x.lease_end || String(x.lease_end) >= today)).map(x => x.property)].filter(Boolean));
  return busy.size ? rows.map(p => busy.has(p.id) && (!p.status || p.status === 'available') ? { ...p, status: 'rented' } : p) : rows;
}
// v3.22 — on a host a partner's browser holds no other account: his rank and counts come from the accounts the server lists in
// «مكاتبي المشتركة» (partner.clients), kept here in memory for the page (never in the browser's storage)
const REFERRED = new Map(); export const keepReferred = (tid, rows) => { if (tid) REFERRED.set(tid, Array.isArray(rows) ? rows : []); };
function computeCtx(c, input) {
  const P = getP(); const countries = rowsOf('platform', 'countries'); const country = countryBy(c.tenant?.country, countries, P);
  const cache = {};
  return {
    input, lang: LANG.cur, country, P, now: Date.now(), tenant: c.tenant, appUrl: (app, q) => absUrl(app, q), focus: c.tenant ? store.get(`set:${c.tenant.id}:onboarding`, {})?.style?.focus || 'both' : 'both',
    data: coll => (cache[coll] ||= (isPlatformColl(coll) ? rowsOf('platform', coll) : coll === 'properties' && c.tenant ? withOccupancy(c.tenant.id, withDocText(c.tenant.id, coll, rowsOf(c.tenant.id, coll))) : withDocText(c.tenant.id, coll, rowsOf(c.tenant.id, coll)))),
    settings: key => store.get(`set:${c.tenant?.id}:${key}`, {}),
    canColl: coll => { if (!c.user || ['owner', 'admin', 'manager'].includes(c.user.role)) return true; const P2 = getP(); return catalog(P2).some(s2 => s2.app === c.app && (s2.e || []).includes(coll) && roleAllows(c.app, c.user.role, s2, P2)); },
    jobs: () => store.get('jobs', []).filter(j => j.tenant === c.tenant?.id),
    audit: () => store.get('audit', []).filter(a => a.tenant === c.tenant?.id),
    services: catalog(P).filter(s => s.app === c.app && access(s, accessCtx(c)) === 'ok'),
    plan: rowsOf('platform', 'plans').find(x => x.code === c.tenant?.plan && x.audience === audienceOf(c.app)),
    partner: P.partner, tenants: () => { const mine = tenants().filter(x => x.attribution && x.attribution === c.tenant?.code); return mine.length || !isHostedNow() ? mine : REFERRED.get(c.tenant?.id) || []; },
    all: () => { const out = {}; for (const k of store.keys(`db:${c.tenant?.id}:`)) out[k.split(':').pop()] = store.get(k, []); out._settings = {}; for (const k of store.keys(`set:${c.tenant?.id}:`)) out._settings[k.split(':').pop()] = store.get(k, {}); return out; },
  };
}

// partner offers (pay/?o=ID): found across partner accounts; the discount is capped by the partner programme
function findOffer(id) {
  if (!id) return null;
  for (const T of tenants().filter(x => x.app === 'partner' && x.status !== 'suspended')) { const o = rowsOf(T.id, 'p_offers').find(x => x.id === id); if (o) return { offer: o, partner: { code: T.code, id: T.id }, expired: !!(o.expires && new Date(o.expires) < new Date()) || o.status === 'expired' }; }
  return null;
}
// AI operations count against the plan quota; payments, connections, migrations and translations do not
const NON_AI = ['checkout', 'password_reset', 'connect', 'disconnect', 'cancel', 'resume', 'api_pull', 'browser_session', 'extract', 'map_fields', 'feed_sync', 'account_session', 'translate'];
const isAiJob = j => !String(j.action || '').startsWith('webhook:') && !NON_AI.includes(j.action);
const MAINT_OK = ['platform.bootstrap', 'system.ping', 'public.status', 'monitor.log', 'auth.status'];

// ================================================================= v2.5.1 WHATSAPP (inbound, server)
// v3.5: values a setting can never take (a 150% partner commission, a domain with spaces, a colour that is not one)
const PCT_KEYS = ['commission_rate', 'max_discount'];
function checkSetting(parts, v) {
  const bad = k => fail('validation', { [k]: 'range' });
  if (parts[0] === 'partner') { const o = parts.length === 1 ? (v || {}) : { [parts[1]]: v }; for (const [k, x] of Object.entries(o)) { if (x === null || x === undefined || typeof x === 'boolean' || typeof x === 'object') continue; const n = +x; if (!isFinite(n) || n < 0 || (PCT_KEYS.includes(k) && n > 100)) bad(k); } }
  // v3.15: the growth engine's settings (dar-grow.php reads them; anything else is refused here first)
  if (parts[0] === 'i18n') { const o = parts.length === 1 ? (v || {}) : { [parts[1]]: v }; if (typeof o !== 'object' || Array.isArray(o)) fail('validation', { i18n: 'shape' }); for (const [k, x] of Object.entries(o)) { const okv = ['on', 'visit', 'dev', 'incomplete'].includes(k) ? typeof x === 'boolean' : k === 'pre' ? Array.isArray(x) && x.length <= 60 && x.every(l => knownLang(l) && !['ar', 'en', 'fr'].includes(l)) : false; if (!okv) fail('validation', { [k]: 'range' }); } } // v3.16: the translation engine's settings
  if (parts[0] === 'grow') { const o = parts.length === 1 ? (v || {}) : { [parts[1]]: v }; if (typeof o !== 'object' || Array.isArray(o)) fail('validation', { grow: 'shape' }); for (const [k, x] of Object.entries(o)) { const okv = ['on', 'indexnow'].includes(k) ? typeof x === 'boolean' : k === 'mode' ? ['auto', 'review'].includes(x) : k === 'ai_daily' ? Number.isInteger(x) && x >= 0 && x <= 20 : k === 'langs' ? Array.isArray(x) && x.length > 0 && x.length <= 40 && x.every(l => knownLang(l)) : k === 'auds' ? Array.isArray(x) && x.length > 0 && x.every(a => ['office', 'builder', 'provider', 'partner', 'buyer', 'renter', 'owner', 'investor', 'marketer'].includes(a)) /* (v3.30: and a sold copy's own readers — dar-grow.php grow_auds) */ : k === 'telegram' ? typeof x === 'string' && (x === '' || /^(@[A-Za-z0-9_]{5,32}|-?\d{5,20})$/.test(x)) : k === 'country' ? typeof x === 'string' && (x === '' || /^[A-Z]{2}$/.test(x)) : false; if (!okv) fail('validation', { [k]: 'range' }); } }
  // v3.17: the maps (dar-places.php and assets/maps.js read them): which tiles, an address search of his own, the services around
  if (parts[0] === 'maps') { const o = parts.length === 1 ? (v || {}) : { [parts[1]]: v }; if (typeof o !== 'object' || Array.isArray(o)) fail('validation', { maps: 'shape' });
    for (const [k, x] of Object.entries(o)) { const okv = ['on', 'nearby'].includes(k) ? typeof x === 'boolean' : k === 'tiles' ? ['osm', 'carto', 'custom'].includes(x) : k === 'precision' ? ['exact', 'approximate', 'hidden'].includes(x) : k === 'tile_url' ? x === '' || (typeof x === 'string' && x.length <= 300 && /^https:\/\/[^\s"'<>]+$/.test(x) && /\{z\}/.test(x) && /\{x\}/.test(x) && /\{y\}/.test(x)) : k === 'attribution' ? typeof x === 'string' && x.length <= 200 && !/[<>]/.test(x) : k === 'geocoder' ? x === '' || (typeof x === 'string' && /^https:\/\/[\w.-]+(\/[\w./-]*)?$/.test(x)) : k === 'overpass' ? Array.isArray(x) && x.length <= 4 && x.every(u => /^https:\/\/[\w.-]+\/[\w./-]*$/.test(u)) : false; if (!okv) fail('validation', { ['maps.' + k]: 'range' }); } }
  if (parts[0] === 'doctor') { const o = parts.length === 1 ? (v || {}) : { [parts[1]]: v }; if (typeof o !== 'object' || Array.isArray(o)) fail('validation', { doctor: 'shape' }); for (const [k, x] of Object.entries(o)) { if (['auto', 'ai', 'canary'].includes(k) ? typeof x !== 'boolean' : k === 'report' ? !['needs', 'daily', 'off'].includes(x) : true) fail('validation', { [k]: 'range' }); } }
  if (parts[0] === 'tracking') { const o = parts.length === 1 ? (v || {}) : { [parts[1]]: v }; if (typeof o !== 'object' || Array.isArray(o)) fail('validation', { tracking: 'shape' });
    for (const [k, x] of Object.entries(o)) { if (x === null || x === undefined || x === '') continue; const okv = k === 'consent' ? ['ask', 'none'].includes(x) : TRACK_RE[k] ? typeof x === 'string' && TRACK_RE[k].test(x) : false; if (!okv) fail('validation', { ['tracking.' + k]: 'format' }); } } // v3.18.3
  if (parts[0] === 'domain' && v && !/^(?=.{3,253}$)([a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z]{2,63}$/i.test(String(v))) fail('validation', { domain: 'domain' });
  if (parts[0] === 'theme' && parts.length === 2 && ['brand', 'accent'].includes(parts[1]) && v && !/^#[0-9a-f]{6}$/i.test(String(v))) fail('validation', { [parts[1]]: 'color' });
  if (['base_usd_rate'].includes(parts[0]) && v != null && !(+v > 0)) bad('base_usd_rate');
  if (parts[0] === 'base_currency' && v && !/^[A-Z]{3}$/.test(String(v))) fail('validation', { base_currency: 'currency' });
}
const WA_YES = /^(نعم|ايوه|أيوه|اي|أوافق|اوافق|موافق|yes|y|ok|okay|approve|oui|valider)$/i;
const WA_NO = /^(لا|رفض|ارفض|أرفض|الغاء|إلغاء|no|n|reject|cancel|non|refuser|annuler)$/i;
const WA_RANK = { owner: 5, admin: 4, manager: 3, accountant: 2, hr: 2, agent: 1, employee: 0 };
let WA_IDX = null, WA_AT = 0; // approved number → owner; rebuilt at most once a minute (and on a miss after 5 s)
function waIndex(force) {
  if (WA_IDX && !force && Date.now() - WA_AT < 60e3) return WA_IDX;
  const idx = new Map();
  for (const n of (getP().wa?.numbers || [])) { const d = intlPhone(n, ''); if (d) idx.set(d, { dev: true }); }
  for (const T of tenants()) { if (T.demo) continue; for (const r of rowsOf(T.id, 'wa_numbers')) { if (r.active === false) continue; const d = intlPhone(r.phone, T.country); if (d && !idx.has(d)) idx.set(d, { tenant: T.id, row: r.id }); } }
  WA_IDX = idx; WA_AT = Date.now(); return idx;
}
function waWho(from) {
  let hit = waIndex().get(from); if (!hit && Date.now() - WA_AT > 5e3) hit = waIndex(true).get(from);
  if (!hit) return null;
  if (hit.dev) { const u = users().find(x => x.app === 'developer' && x.role === 'owner' && x.status !== 'disabled'); return u ? { dev: true, user: u, T: null, row: null, scope: 'all' } : null; }
  const T = tenants().find(x => x.id === hit.tenant); const row = T && rowsOf(T.id, 'wa_numbers').find(r => r.id === hit.row); if (!T || !row || row.active === false) return null;
  const real = users().find(u => u.tenant === T.id && u.status !== 'disabled' && u.phone && intlPhone(u.phone, T.country) === from);
  const rr = row.role in WA_RANK ? row.role : 'employee';
  // the number's role never raises a person's own role; a number without a person acts at most as a manager
  const user = real ? { ...real, role: WA_RANK[rr] < (WA_RANK[real.role] ?? 0) ? rr : real.role } : { id: 'wa:' + row.id, app: T.app, tenant: T.id, role: WA_RANK[rr] > 3 ? 'manager' : rr, name: row.name || 'WhatsApp', status: 'active', lang: '' };
  return { dev: false, T, row, user, scope: ['all', 'read_only', 'approvals_only'].includes(row.commands) ? row.commands : 'all' };
}
function waMessage(p) {
  const v = p?.entry?.[0]?.changes?.[0]?.value; const raw = v?.messages?.[0]; if (v && !raw) return null; // delivery/read statuses carry no message
  const src = raw ? { from: raw.from, id: raw.id, type: raw.type, text: raw.text?.body ?? raw.button?.text ?? raw.interactive?.button_reply?.title ?? raw.interactive?.list_reply?.title ?? '', button: raw.interactive?.button_reply?.id || raw.button?.payload || '' } : p;
  const from = latinDigits(String(src?.from || '')).replace(/\D/g, ''); if (from.length < 8) return null;
  return { from, id: String(src.id || '').slice(0, 120), text: String(src.text || '').trim().slice(0, 2000), button: String(src.button || '').slice(0, 120), type: String(src.type || 'text').slice(0, 20) };
}
function waQuery(r, T) {
  const d = r.data || {}; const P = getP(); const cur = T ? countryBy(T.country, rowsOf('platform', 'countries'), P).currency : 'SAR'; const m$ = v => fmtMoney(+v || 0, cur);
  const tz = T ? (T.tz || tzOf(T.country)) : 'Asia/Riyadh'; const tm = s => { try { return new Intl.DateTimeFormat('en-GB', { hour: '2-digit', minute: '2-digit', timeZone: tz }).format(new Date(s)); } catch { return String(s || '').slice(11, 16); } };
  const dt = s => String(s || '').slice(0, 10); const lines = [];
  switch (r.query) {
    case 'attendance': lines.push(t('q_present', { n: d.present_today }), ...(d.present_list || []).map(x => `• ${x.employee} — ${tm(x.check_in)}${x.status === 'late' ? ' ⏰' : ''}`)); if ((d.on_leave || []).length) lines.push(t('q_on_leave', { list: d.on_leave.join(LSEP()) })); if (d.workday) lines.push(t('q_absent', { list: (d.absent_list || []).join(LSEP()) || '—' })); break;
    case 'leaves': lines.push(t('q_leaves', { n: d.leaves_pending }), ...(d.leaves_list || []).map(x => `• ${x.employee} — ${optLabel(x.leave_type)} ${dt(x.date_from)}→${dt(x.date_to)}`)); if (d.leaves_pending) lines.push(t('q_leaves_hint')); break;
    case 'overdue': lines.push(t('q_overdue', { v: m$(d.overdue) }), ...(d.overdue_list || []).map(x => `• ${x.number} · ${x.client || ''} — ${m$(x.amount)}`)); break;
    case 'appointments': lines.push(t('q_appts', { n: (d.appts_today || []).length }), ...(d.appts_today || []).map(x => `• ${tm(x.start)} ${x.title}`)); break;
    case 'obligations': lines.push(t('q_obligations', { n: (d.obligations_list || []).length }), ...(d.obligations_list || []).map(x => `• ${x.title} — ${m$(x.amount)} · ${dt(x.due)}`)); break;
    default: lines.push(t('q_new_leads', { n: d.leads_new_today }), t('q_open_leads', { n: d.leads_open }), t('q_appts', { n: (d.appts_today || []).length }), t('q_tasks', { n: d.tasks_due }), t('q_overdue', { v: m$(d.overdue) }), t('q_present', { n: d.present_today }), t('q_leaves', { n: d.leaves_pending }), t('q_obl7', { n: d.obligations_due }), t('q_sign', { n: d.signatures_pending }), ...(d.alerts || []).map(a => '⚠️ ' + a.text));
  }
  return `*${L(r.summary)}*\n` + lines.join('\n');
}
// v3.8: a step in plain words (WhatsApp and other text-only places)
const stepText = a => {
  const val = (k, v) => typeof v === 'string' && /^\$\d/.test(v) ? '…' : clip(Array.isArray(v) ? v.join(LSEP()) : fieldsOf(a.coll).find(f => f.key === k)?.type === 'sel' ? optLabel(v) : String(v), 40);
  switch (a.do) {
    case 'create': return t('pl_create', { c: collLabel(a.coll) }) + (a.row ? ' — ' + Object.entries(a.row).slice(0, 4).map(([k, v]) => `${fieldLabel(k, a.coll)}: ${val(k, v)}`).join(' · ') : '');
    case 'update': return t('pl_update', { c: collLabel(a.coll) }) + ' «' + (a.label || a.id) + '»' + (a.row ? ' — ' + Object.entries(a.row).slice(0, 3).map(([k, v]) => `${fieldLabel(k, a.coll)}: ${val(k, v)}`).join(' · ') : '');
    case 'delete': return t('pl_delete', { c: collLabel(a.coll) }) + ' «' + (a.label || a.id) + '»';
    case 'clock': return t(a.action === 'out' ? 'pl_clock_out' : 'pl_clock_in');
    // v3.13.1: an account's own steps
    case 'setting': return t('pl_setting', { k: t('pl_set_' + a.key) }) + ' — ' + Object.entries(a.set || {}).slice(0, 4).map(([k, v]) => `${fieldLabel(k)}: ${clip(Array.isArray(v) ? v.join(LSEP()) : String(v), 40)}`).join(' · ');
    case 'team': return a.action === 'invite' ? t('pl_team_invite', { name: a.name || a.email, email: a.email, role: optLabel(a.role) }) : a.action === 'role' ? t('pl_team_role', { name: a.label || a.id, role: optLabel(a.role) }) : t(a.action === 'deactivate' ? 'pl_team_off' : 'pl_team_on', { name: a.label || a.id });
    case 'message': return (a.conversation ? t('pl_msg_conv', { name: a.label || '' }) : t('pl_msg', { name: a.label || '', ch: t('ch_' + a.channel) })) + ': «' + clip(a.text, 120) + '»';
    case 'link': return t('pl_link_' + a.what, { name: a.label || '' }) + (a.send ? ' — ' + t('pl_link_and_send', { ch: t('ch_' + a.send.channel) }) : '');
    case 'approve': return t(a.decision === 'approve' ? 'pl_approve' : 'pl_reject', { what: a.label || a.id });
    default: return (a.label || [a.do, a.action || a.path || a.coll || ''].join(' ')).trim();
  }
};
// (v3.8: Dar Mind answers on WhatsApp too: what it did at once, and the steps that wait — «نعم» runs them)
const waText = (r, T) => r.pending ? '🕓 ' + t('wai_ai_wait') : r.budget ? '⚠️ ' + t('ai_off_budget') : r.job ? '🕓 ' + t('wai_working') : r.query ? waQuery(r, T)
  : r.llm ? [L(r.answer), ...(r.done || []).filter(d => d.ok).map(d => '✅ ' + stepText({ ...d.a, label: d.label || d.a.label })), ...(r.plan || []).map(a => '• ' + stepText(a)), (r.plan || []).length ? t(r.plan.every(a => ['create', 'update', 'delete', 'clock'].includes(a.do)) ? 'wai_reply_yes' : 'wai_plan_panel') : ''].filter(Boolean).join('\n')
  : r.answer ? L(r.answer) : '🕓 ' + t('cmd_unknown');
// v3.8: the steps a person confirmed on WhatsApp («نعم»): the records' own operations only (the rest from the panel)
async function waRunPlan(plan, cx) {
  const made = {}; const lines = [];
  for (const [i, a] of plan.entries()) {
    try {
      const row = withRefs(a.row, made);
      if (a.do === 'create') { const r = await OPS['data.create']({ coll: a.coll, row }, cx); made[a._n || i + 1] = r.id; lines.push('✅ ' + stepText({ ...a, row })); }
      else if (a.do === 'update') { await OPS['data.update']({ coll: a.coll, id: a.id, row }, cx); lines.push('✅ ' + stepText(a)); }
      else if (a.do === 'delete') { await OPS['data.delete']({ coll: a.coll, id: a.id }, cx); lines.push('✅ ' + stepText(a)); }
      else if (a.do === 'clock') { await OPS['hr.clock']({ action: a.action, method: 'whatsapp' }, cx); lines.push('✅ ' + stepText(a)); }
      // v3.13.1: an account's own steps from WhatsApp — its settings, its team, a reply in a conversation, an approval
      else if (a.do === 'setting') { await OPS['settings.patch']({ key: a.key, value: a.set }, cx); lines.push('✅ ' + stepText(a)); }
      else if (a.do === 'team' && a.action !== 'invite') { await OPS['team.update']({ id: a.id, ...(a.action === 'role' ? { role: a.role } : { status: a.action === 'deactivate' ? 'inactive' : 'active' }) }, cx); lines.push('✅ ' + stepText(a)); }
      else if (a.do === 'message' && a.conversation) { await OPS['inbox.send']({ conversation: a.conversation, body: a.text }, cx); lines.push('✅ ' + stepText(a)); }
      else if (a.do === 'approve') { await OPS['jobs.decide']({ id: a.id, decision: a.decision, note: a.note || 'WhatsApp' }, cx); lines.push('✅ ' + stepText(a)); }
      else lines.push('• ' + stepText(a) + ' — ' + t('wai_plan_panel'));
    } catch (e) { lines.push('⚠️ ' + stepText(a) + ' — ' + errText(e)); break; }
  }
  return lines.join('\n');
}
async function waDecide(cx, who, id, decision, out) {
  let j; try { j = await OPS['jobs.decide']({ id, decision, note: 'WhatsApp' }, cx); }
  catch (e) { if (e?.extra?.status === 'expired') return out('expired', t('wai_expired'), { job: id }); throw e; }
  const all = store.get('jobs', []); const jj = all.find(x => x.id === j.id); if (jj?.decision) { jj.decision.channel = 'whatsapp'; jj.decision.by_name = who.user.name || ''; store.set('jobs', all); j = jj; }
  return out(decision === 'approve' ? 'approved' : 'rejected', t(decision === 'approve' ? 'wai_approved' : 'wai_rejected', { what: L(j.proposal?.summary) || j.action }), { job: j.id });
}
async function waInbound(p, c) {
  if (c.api !== 'master') fail('forbidden');
  const m = waMessage(p); if (!m) return { ignored: true, reason: 'no_message' };
  if (m.id) { const seen = store.get('wa_seen', []); if (seen.includes(m.id)) return { ignored: true, reason: 'duplicate' }; seen.unshift(m.id); if (seen.length > 1000) seen.length = 1000; store.set('wa_seen', seen); }
  const who = waWho(m.from); if (!who) return { ignored: true, reason: 'unknown_number' }; // strangers get no answer (no spam, no probing)
  const { T, user } = who; const lg = [user.lang, T?.lang].find(x => knownLang(x)); if (lg) LANG.cur = lg;
  const cx = who.dev ? { app: 'developer', tenant: null, imp: null, user } : { app: T.app, tenant: T, imp: null, user };
  const out = (kind, reply, extra = {}) => ({ to: m.from, kind, reply, lang: LANG.cur, tenant: T?.id || 'platform', user: user.id, ...extra });
  if (T && T.status === 'suspended') return out('error', t('e_tenant_suspended'), { code: 'tenant_suspended' });
  const txt = normText(m.text).replace(/[.!؟?،,]+$/g, '').trim(); const yes = WA_YES.test(txt), no = WA_NO.test(txt);
  const pkey = 'wa_pending:' + m.from; const pend = store.get(pkey, null); const fresh = pend && Date.now() - new Date(pend.at).getTime() < 10 * 60e3;
  const latest = () => store.get('jobs', []).find(j => j.status === 'needs_approval' && (who.dev ? (!j.tenant || j.tenant === 'platform') : (j.tenant === T.id && (j.uid === user.id || ['owner', 'admin', 'manager'].includes(user.role))))) || null;
  const run = async text => {
    const ro = who.scope === 'read_only';
    const r = await OPS['ai.command']({ text, channel: 'whatsapp', lang: LANG.cur, autorun: !ro }, cx);
    if (r.llm && (r.plan || []).length) {
      if (ro) return out('denied', L(r.answer) + '\n' + t('wai_read_only')); // (v3.13.1: whatever the step — a setting, the team, a message… — a «read only» number changes nothing)
      // v3.13.1: an account whose owner gave its assistant a free hand («تعليماتي للمساعد»): the steps run now, no «نعم» needed
      if (!who.dev && T && acctAssist(T.id).confirm === 'none') {
        const wait = r.plan.filter(a => a.do === 'approve'); const ran = await waRunPlan(r.plan.filter(a => a.do !== 'approve'), cx); // (a decision his AI team waits for stays his own «نعم»)
        if (!wait.length) return out('done', [waText({ ...r, plan: null }, T), ran].filter(Boolean).join('\n'));
        store.set(pkey, { plan: wait, at: nowIso() }); return out('confirm', [ran, waText({ ...r, plan: wait }, T)].filter(Boolean).join('\n'));
      }
      store.set(pkey, { plan: r.plan, at: nowIso() });
    }
    return out(r.pending ? 'queued' : r.llm && (r.plan || []).length ? 'confirm' : r.understood ? 'done' : 'unknown', waText(r, T), r.job ? { job: r.job.id } : {});
  };
  try {
    const b = /^(approve|reject):([\w-]{3,40})$/.exec(m.button); if (b) return await waDecide(cx, who, b[2], b[1], out); // buttons on an approval request
    if (fresh && (yes || no)) { store.del(pkey); return no ? out('cancelled', t('wai_cancelled')) : out('done', await waRunPlan(pend.plan || [], cx)); } // «yes» to the steps that waited
    if (yes || no) { const j = latest(); return j ? await waDecide(cx, who, j.id, yes ? 'approve' : 'reject', out) : out('info', t('wai_no_pending')); } // «yes/no» to the latest approval request
    if (who.scope === 'approvals_only') return out('denied', t('wai_approvals_only'));
    if (!m.text) return out('unknown', '🕓 ' + t('cmd_unknown'));
    return await run(m.text);
  } catch (e) { return out('error', '⚠️ ' + errText(e), { code: e?.code || 'server_error' }); }
}

async function localCall(op, payload, app, token) {
  seedPlatform();
  // RUNTIME.ops: operations the automation server adds or replaces (payments, OAuth, OTP…) without touching this file
  const fn = RUNTIME.ops?.[op] || OPS[op]; if (!fn) fail('unknown_op');
  const c = ctxOf(app, token);
  // v3.33.8: the platform's team works through maintenance — an account opened from «الدخول كمشترك», or this browser has the
  // developer signed in (ui.js shows them the account with a notice); everyone else is still refused
  if (app !== 'developer' && getP().maintenance?.on && !MAINT_OK.includes(op) && !c.imp && !api.session('developer')?.token) fail('maintenance');
  if (token && c.user && c.user.app !== 'developer' && c.user.lang !== LANG.cur) { const all = users(); const u = all.find(x => x.id === c.user.id); if (u) { u.lang = LANG.cur; saveUsers(all); } } // notices and messages sent later use it
  const res = await fn(payload || {}, c, token);
  if (c.user && c.tenant) BEHAVIOR.observe(op, payload, c, res); // v3.1: preferences learned from how each person works (counts only)
  return res;
}

// Open Platform: a server call authenticated by an API key (header X-Dar-Key) instead of a session token.
// Office/console keys act inside their own account with their scope (read | write | full); the platform master key acts as
// the developer owner (automation workers). Account, billing, keys and platform operations are never reachable by key.
const KEY_DENY = /^(auth\.|team\.|keys\.|billing\.|platform\.|secrets\.|devusers\.|tenants\.|catalog\.|jobs\.(claim|complete|clear)|menu\.set|onboarding\.save|settings\.set|migration\.(connect|browser|rollback)|integrations\.|radar\.(connect|network)|partner\.payout)/; // v2.9: money moves only from a signed-in person, never from a key or the AI team
const KEY_READ = ['data.list', 'data.get', 'insight.summary', 'insight.run', 'radar.signals', 'radar.sources', 'jobs.list', 'notices.list', 'billing.usage', 'public.status', 'system.ping'];
export async function keyCall(op, payload, key, asTenant = null) {
  seedPlatform(); const k = String(key || '').trim(); if (!/^(?:dar|key)_(o|c|mk)_[0-9a-f]{20,64}$/.test(k)) fail('auth_required'); // (v3.30: a sold copy's keys begin key_)
  const h = await sha256(k); let c;
  if (k.startsWith('dar_mk_') || k.startsWith('key_mk_')) {
    const P = getP(); if (!P.master_key_hash || P.master_key_hash !== h) fail('auth_required');
    c = { app: 'developer', tenant: null, imp: null, api: 'master', user: { id: 'key:master', app: 'developer', tenant: 'platform', role: 'owner', name: 'Master key', status: 'active' } };
    if (asTenant) { // v2.5.1: the automation works inside one account as its AI team — never as a person, never on account/billing/team/keys
      const T = tenants().find(x => x.id === String(asTenant)); if (!T) fail('not_found', { tenant: 'unknown' });
      if (KEY_DENY.test(op) || /^(account\.|jobs\.|whatsapp\.|autonomy\.|ai\.fallback$)/.test(op)) fail('forbidden', { scope: 'as_tenant' });
      if (T.status === 'suspended' && !/^(data\.(list|get)|insight\.|notices\.list)$/.test(op)) fail('tenant_suspended');
      c = { app: T.app, tenant: T, imp: null, api: 'worker', user: { id: 'ai:worker', app: T.app, tenant: T.id, role: 'owner', name: 'AI · Dar', status: 'active', lang: T.lang || '' } };
    }
  } else {
    let idx = store.get('keyidx:' + h, null);
    if (!idx) for (const T0 of tenants()) for (const coll of ['api_keys', 'c_keys']) { const r0 = store.get(ckey(T0.id, coll), []).find(x => x.hash === h); if (r0) { idx = { tenant: T0.id, coll, id: r0.id }; store.set('keyidx:' + h, idx); } }
    if (!idx) fail('auth_required');
    const T = tenants().find(x => x.id === idx.tenant); const list = T ? store.get(ckey(T.id, idx.coll), []) : []; const rec = list.find(x => x.id === idx.id);
    if (!T || !rec || rec.status !== 'active' || rec.hash !== h) fail('auth_required');
    if (T.status === 'suspended') fail('tenant_suspended');
    if (KEY_DENY.test(op) || (rec.scope === 'read' && !KEY_READ.includes(op)) || (rec.scope !== 'full' && /\.(delete|rollback)$/.test(op))) fail('forbidden', { scope: rec.scope });
    c = { app: T.app, tenant: T, imp: null, api: rec.scope, user: { id: 'key:' + rec.id, app: T.app, tenant: T.id, role: 'owner', name: 'API · ' + rec.name, email: '', status: 'active' } };
    if (T.app === 'app') { const svc = catalog(getP()).find(s2 => s2.id === 'api_access'); if (svc && access(svc, accessCtx(c)) !== 'ok') fail('not_in_plan'); }
    if (!rec.last_used || Date.now() - new Date(rec.last_used) > 3600e3) { rec.last_used = nowIso(); store.set(ckey(T.id, idx.coll), list); }
  }
  const fn = RUNTIME.ops?.[op] || OPS[op]; if (!fn) fail('unknown_op');
  if (getP().maintenance?.on && c.app !== 'developer' && !MAINT_OK.includes(op)) fail('maintenance');
  return await fn(payload || {}, c, null);
}
// sandbox examples (demo_mode "sandbox" on a server) expire after a day; the server calls this every hour
export function cleanupDemos() {
  const now = Date.now(); const all = tenants(); const gone = all.filter(T => T.demo_sandbox && T.demo_expires && new Date(T.demo_expires).getTime() < now); if (!gone.length) return 0;
  for (const T of gone) for (const k of [...store.keys(`db:${T.id}:`), ...store.keys(`set:${T.id}:`), ...store.keys(`pstat:${T.id}`)]) store.del(k);
  const ids = new Set(gone.map(T => T.id)); saveTenants(all.filter(T => !ids.has(T.id))); saveUsers(users().filter(u => !ids.has(u.tenant))); return gone.length;
}
// v2.5.4: the contract's scheduled duties (spec → schedules); the server calls this every hour (SCHEDULES=off leaves them to system.sweep)
// v2.7: on a server, content jobs nobody claimed for `afterMin` minutes are completed by the local engine
// (the cloud team still gets every job first; external actions are never touched).
export async function localCatchUp({ afterMin = 10, limit = 20 } = {}) {
  seedPlatform(); const cut = Date.now() - Math.max(1, +afterMin || 10) * 60e3; const done = [];
  const sys = { app: 'developer', tenant: null, imp: null, user: { id: 'system:local', app: 'developer', tenant: 'platform', role: 'owner', name: 'Local engine', status: 'active' } };
  const due = store.get('jobs', []).filter(j => j.status === 'queued' && !j.claimed_at && new Date(j.at) < cut && j.tenant && j.tenant !== 'platform' && brainHandles(j.service, j.action) && !autoCapable(j.service, j.action)).slice(0, Math.min(100, +limit || 20));
  for (const j of due) { try { await OPS['ai.fallback']({ id: j.id, reason: 'no_worker' }, sys); done.push(j.id); } catch { /* left for the cloud team */ } }
  return { completed: done.length, ids: done };
}
export function runSweep(p = {}) { seedPlatform(); const r = withMemorySweep(EXT.sweep(p, OPS)); if (!p.tenant) { try { r.billing = BILL.tick(); } catch (e) { r.billing = { error: String(e?.message || e).slice(0, 120) }; } } integrityToMonitor(r); return r; }
// v3.2: every scheduled sweep also checks the records of every account and files what is wrong in the monitor (errors and
// warnings only; repeats fold within the hour) — the 24/7 watch over the system's data costs no automation execution
function integrityScan(p = {}, c = {}) {
  const dev = c.user?.app === 'developer' || c.system === true; if (!dev) { needUser(c); if (!['owner', 'admin', 'manager'].includes(c.user.role)) fail('forbidden'); } else if (c.user) needPerm(c, 'monitoring');
  const P = getP(); const countries = rowsOf('platform', 'countries'); const list = dev ? tenants().filter(T => !T.demo && T.status !== 'suspended').slice(0, 2000) : [c.tenant];
  const agg = {}; const per = [];
  for (const T of list) {
    if (!T) continue; let found = [];
    try { found = integrityIssues(coll => rowsOf(T.id, coll), { app: T.app, country: countryBy(T.country, countries, P) }); } catch { found = [{ code: 'scan_failed', level: 'error', coll: '', n: 1, sample: [] }]; }
    if (found.length) per.push({ tenant: T.id, name: T.name, app: T.app, n: found.reduce((a, x) => a + x.n, 0), codes: found.map(x => x.code) });
    for (const x of found) { const k = x.code + '|' + x.coll; const a = (agg[k] ||= { code: x.code, level: x.level, coll: x.coll, n: 0, tenants: 0, sample: [] }); a.n += x.n; a.tenants++; if (!dev && a.sample.length < 5) a.sample.push(...x.sample.slice(0, 5 - a.sample.length)); }
  }
  const queue = dev ? queueIssues(store.get('jobs', [])) : [];
  const rank = { error: 0, warn: 1, info: 2 };
  return { at: nowIso(), accounts: list.length, findings: Object.values(agg).sort((a, b) => rank[a.level] - rank[b.level] || b.n - a.n), queue, accounts_with_issues: per.sort((a, b) => b.n - a.n).slice(0, 20) };
}
function integrityToMonitor(r) {
  try {
    const sc = integrityScan({}, { system: true, app: 'server' }); const batch = [];
    for (const x of [...sc.findings, ...sc.queue]) if (x.level !== 'info') batch.push({ sev: x.level === 'error' ? 'error' : 'warn', msg: `${x.code}: ${x.n} ${x.coll || ''}${x.tenants ? ' · ' + x.tenants + ' accounts' : ''}`.trim(), where: 'integrity:' + x.code, app: 'server', count: 1 });
    if (batch.length) OPS['monitor.log']({ batch: batch.slice(0, 20) }, { app: 'server' });
    r.integrity = { findings: batch.length }; // a report, not a change: a second sweep with the same findings changes nothing
  } catch { r.errors = (+r.errors || 0) + 1; }
}
// v2.6: expired memories and old learning signals leave with the same hourly sweep
function withMemorySweep(r) { try { const m = LEARN.sweep(); if (m.memory) r.changes.memory_expired = m.memory; if (m.signals) r.changes.signals_expired = m.signals; } catch { r.errors = (+r.errors || 0) + 1; } try { const b = BEHAVIOR.sweep(); if (b) r.changes.behavior_notes = b; GEO.warm(); } catch { r.errors = (+r.errors || 0) + 1; } return r; }

// The same contract implementation, callable by a server: server/dar-server.mjs runs it over HTTP (POST /dar/v2) with a
// real store, so "model" and "live" behave identically and the automation side only adds integrations.
export const serverCall = localCall;
// v3.32: whether this browser's engine has an operation (an operation it lacks is the server's — assets/sync.js asks there)
export const localHas = op => !!(RUNTIME.ops?.[op] || OPS[op]);
export const RUNTIME = { server: false, geo: '', langs: null, geodb: false, solo: null }; // true when running inside server/dar-server.mjs: jobs wait for real workers ("queued")

// ================================================================= LIVE GATEWAY
async function liveCall(op, payload, app, token) {
  if (!CFG.apiBase) fail('no_api_base');
  const ctl = new AbortController(); const timer = setTimeout(() => ctl.abort(), CFG.timeout);
  try {
    const res = await fetch(CFG.apiBase.replace(/\/+$/, '') + '/' + CFG.endpoint.replace(/^\/+/, ''), {
      method: 'POST', headers: { 'Content-Type': 'application/json' }, signal: ctl.signal,
      body: JSON.stringify({ op, payload: payload || {}, token: token || null, app, lang: LANG.cur, country: api.country || null, v: VERSION }),
    });
    let j; try { j = await res.json(); } catch { fail('bad_response', { status: res.status }); }
    if (!j || j.ok !== true) fail(j?.error?.code || j?.error || 'server_error', j?.error?.extra || null);
    return j.data;
  } catch (e) { if (e instanceof DarError) throw e; fail(e?.name === 'AbortError' ? 'timeout' : 'network'); } finally { clearTimeout(timer); }
}

// ================================================================= PUBLIC API
const runner = () => CFG.mode === 'live' ? liveCall : CFG.mode === 'hosted' && HOSTED.call ? HOSTED.call : localCall;
// v3.13.1: an example account's session lives in this browser only — a server-only call it makes (refused for want of a server
// session) never signs the visitor out of the example
const localDemo = tok => { const tk = store.get('tokens', {})[tok]; if (!tk || tk.hosted) return false; return !!store.get('users', []).find(x => x.id === tk.uid)?.demo; };
export const api = {
  app: 'site', country: null, suffix: '',
  session(app = api.app) { return store.get('sess:' + app + api.suffix); },
  setSession(app, s) { const k = 'sess:' + app + api.suffix; if (s) store.set(k, s); else store.del(k); },
  onAuthExpired: null,
  async call(op, payload = {}) {
    const s = api.session(api.app);
    const run = runner();
    try { return await run(op, payload, api.app, s?.token); }
    catch (e) { if (e?.code === 'auth_required' && s?.token && typeof api.onAuthExpired === 'function' && !localDemo(s.token)) api.onAuthExpired(); throw e; }
  },
  async callAs(app, op, payload = {}) { const s = api.session(app); return runner()(op, payload, app, s?.token); },
  async callWith(app, token, op, payload = {}) { return runner()(op, payload, app, token); },
};

export async function loadConfig(root) {
  CFG.root = root; setPlacesRoot(root); // v3.17: lib/places/ is read from the site's root
  try { const r = await fetch(root + 'config.json', { cache: 'no-store' }); if (r.ok) Object.assign(CFG, await r.json()); } catch { /* model defaults */ }
  const o = store.get('cfg_override'); if (o && typeof o === 'object') Object.assign(CFG, o);
  CFG.mode = ['live', 'hosted'].includes(CFG.mode) ? CFG.mode : 'demo'; // v3.3: "hosted" = the engine here + Dar Sync (dar-sync.php) on the host
}
// Link to an interface: explicit index.html keeps links working on any static host and in previews.
// v3.27: the buyers' preview (dar-preview.php) — every link inside it stays inside it: the interface of the same edition at its private
// address, the page with the two editions for anything else (the platform's own pages are not part of what a buyer is shown)
// (v3.30: and the editions' marketers' interface and the programmers' portal — the developer edition's marketers have a page of their own)
export const PV_SLUG = { app: 'offices', builders: 'developers', providers: 'providers', developer: 'admin', partner: 'marketers', console: 'programmers' };
export function pvLink(appId, hash = '') {
  if (!PV) return null;
  const slug = appId === 'partner' && SHOW_KIND === 'builder' ? 'developermarketers' : PV_SLUG[appId];
  return (CFG.root || '/') + 'v/' + PV.token + (slug ? '/' + slug : '/') + (hash ? '#' + String(hash).replace(/^#/, '') : '');
}
export function appLink(appId, P, hash = '') {
  if (PV) return pvLink(appId, hash);
  const a = R.appById(appId);
  if (P?.domain && typeof location !== 'undefined' && location.hostname.endsWith(P.domain)) { const u = publicUrl(appId, P); if (u) return u + (hash ? '#' + hash.replace(/^#/, '') : ''); }
  const path = (P?.links?.[appId]?.path ?? a?.path ?? '');
  return CFG.root + path + (CFG.pretty ? '' : 'index.html') + (hash ? '#' + hash.replace(/^#/, '') : '');
}
// v3.23: a page the server draws itself (the legal texts, the prices, the contact page): readable without JavaScript and without
// signing in, as the provider's reviewers and the search engines read them, in the reader's language when it is one of the three; a
// site without its server (the static copy) keeps the pages drawn in the browser
export function pageLink(path, P) {
  if (PV) return pvLink('site'); // (v3.27: the preview has no legal pages of its own — the editions' pages are the sold copy's)
  if (CFG.mode !== 'hosted') { const m = /^legal\/(\w+)$/.exec(path); return appLink('site', P, m ? '/legal/' + m[1] : ''); }
  const lang = /^[a-z]{2,3}(-[A-Za-z]{2,4})?$/.test(LANG.cur || '') ? '?lang=' + LANG.cur : ''; // (v3.26: any language — the server answers in it when it can, else in English)
  return (publicUrl('site', P) || CFG.root) + path + lang;
}
export function publicUrl(appId, P) {
  const a = R.appById(appId); const sub = P?.links?.[appId]?.sub ?? a?.sub; const domain = P?.domain;
  if (!domain || !sub) return null;
  const host = (sub === 'www' ? '' : sub + '.') + domain;
  // v3.5.1: on a hosted site an interface takes its own sub-domain only once the server found it working there (the
  // developer panel's «افحص النطاقات»); until then every link keeps the site's own address, so nothing points to a
  // sub-domain that is not ready
  if (CFG.mode === 'hosted' && P?.links?.[appId]?.ok !== host) return null;
  return `https://${host}/`;
}
export { R };
