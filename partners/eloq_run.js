/* Eloquens listing automation for Dar Templates. Runs from the author's logged-in Eloquens page;
   each listing is created inside a same-origin iframe so one loop can publish many products. */
(function () {
  var SHOP = 'https://cdn.shopify.com/s/files/1/1007/1887/0832/files/';
  var S = window.__elq = window.__elq || { log: [], done: {} };
  S.log = S.log || []; S.done = S.done || {};
  function log(m) { S.log.push(new Date().toISOString().slice(11, 19) + ' ' + m); if (S.log.length > 300) S.log.shift(); S.last = m; }
  function sleep(ms) { return new Promise(function (r) { setTimeout(r, ms); }); }
  async function waitFor(fn, ms, label) {
    var t0 = Date.now();
    while (Date.now() - t0 < ms) { var v; try { v = fn(); } catch (e) { v = null; } if (v) return v; await sleep(700); }
    throw new Error('timeout: ' + label);
  }
  async function blob(u) {
    var r = await fetch(u);
    if (!r.ok) throw new Error('fetch ' + r.status + ' ' + u.slice(0, 90));
    return r.blob();
  }

  function Ctx(w) {
    var d = w.document;
    function vis(e) { return e && e.offsetParent !== null; }
    function q(sel) { return Array.prototype.slice.call(d.querySelectorAll(sel)); }
    function byText(sel, re) { return q(sel).filter(function (e) { return vis(e) && e.children.length < 3 && re.test((e.innerText || '').trim()); }); }
    function setv(el, v) { el.focus(); el.value = v; ['input', 'change', 'keyup', 'blur'].forEach(function (t) { el.dispatchEvent(new w.Event(t, { bubbles: true })); }); }
    return { w: w, d: d, q: q, vis: vis, byText: byText, setv: setv };
  }

  async function uploadFiles(c, files) {
    var z = c.w.Dropzone.instances.filter(function (x) { return x.element.id === 'formMediaUpload'; })[0] || c.w.Dropzone.instances[0];
    var done = 0, fail = 0;
    function ok() { done++; } function ko(f, m) { fail++; log('upload error ' + f.name + ' ' + (m && m.message || m)); }
    z.on('success', ok); z.on('error', ko);
    for (var i = 0; i < files.length; i++) {
      z.addFile(files[i]);
      if (i === 0 && files.length > 1) await waitFor(function () { return done + fail >= 1; }, 900000, 'first upload');
    }
    await waitFor(function () { return done + fail >= files.length; }, 3600000, 'uploads');
    z.off('success', ok); z.off('error', ko);
    if (fail) throw new Error('upload failures ' + fail);
  }
  async function addSelected(c, n) {
    var re = new RegExp('^ADD ' + n + ' (IMAGES?|ITEMS?)$', 'i');
    var b = await waitFor(function () { return c.byText('.btn, a, span, button', re)[0]; }, 180000, 'add button ' + n);
    b.click(); await sleep(3000);
  }
  function clickStep(c, re) {
    var b = c.byText('.btn, span, a, div', re)[0];
    if (!b) throw new Error('no step ' + re); b.click();
  }

  async function publish(item) {
    var k = item.k;
    log(k + ' start');
    var fr = document.getElementById('elqFrame');
    if (fr) fr.remove();
    fr = document.createElement('iframe'); fr.id = 'elqFrame';
    fr.style.cssText = 'position:fixed;left:0;top:0;width:1300px;height:900px;z-index:99999;background:#fff;border:3px solid #0f6b4f';
    fr.src = '/contributions/create/docs';
    document.body.appendChild(fr);
    await waitFor(function () { return fr.contentWindow.document.querySelector('input[name=title]') && fr.contentWindow.document.readyState === 'complete'; }, 90000, 'create page');
    await sleep(1500);
    var c = Ctx(fr.contentWindow);
    c.setv(c.d.querySelector('input[name=title]'), item.title);
    c.q('span.btnCheckCreation').filter(c.vis)[0].click();
    await waitFor(function () { return /edit-draft/.test(fr.contentWindow.location.href) && fr.contentWindow.document.readyState === 'complete' && fr.contentWindow.Dropzone; }, 90000, 'draft page');
    await sleep(2500);
    c = Ctx(fr.contentWindow);
    var draft = fr.contentWindow.location.pathname.split('/')[2];
    S.drafts = S.drafts || {}; S.drafts[k] = draft;
    log(k + ' draft ' + draft);

    var imgs = item.imgs;
    if (imgs === 'SHOPIFY') {
      var m = JSON.parse(localStorage.getItem('ELQ_IMG'));
      imgs = m[item.h].img.slice(0, 8).map(function (p) { return SHOP + p; });
    }
    var files = [];
    for (var i = 0; i < imgs.length; i++) {
      var b = await blob(imgs[i]);
      var ext = b.type.indexOf('png') >= 0 ? 'png' : 'jpg';
      files.push(new File([b], k + '-' + ('0' + (i + 1)).slice(-2) + '.' + ext, { type: b.type || 'image/jpeg' }));
    }
    log(k + ' images fetched ' + files.length);
    c.byText('.btn, span, a, div', /Add from library$/i)[0].click(); await sleep(2000);
    await uploadFiles(c, files); await addSelected(c, files.length); log(k + ' images added');

    var zf = [];
    for (var j = 0; j < item.zips.length; j++) {
      zf.push(new File([await blob(item.zips[j].u)], item.zips[j].n, { type: 'application/zip' }));
    }
    log(k + ' zips fetched ' + zf.map(function (f) { return Math.round(f.size / 1048576) + 'MB'; }).join(','));
    c.byText('.btn, span, a, div', /Add from library$/i)[1].click(); await sleep(2000);
    await uploadFiles(c, zf); await addSelected(c, zf.length); log(k + ' zips added');

    c.setv(c.d.getElementById('nvDescShort'), item.short);
    c.setv(c.d.getElementById('nvContents'), item.contents);
    c.setv(c.d.getElementById('pvFIObjectives'), 'Give the owner or manager one connected Excel system that shows what needs attention today and what really makes money, without a monthly subscription.');
    c.setv(c.d.getElementById('pvFIUseIf'), 'You run this kind of business and keep its records in notebooks, chats or scattered spreadsheets, and you want clear numbers and alerts in one place.');
    c.setv(c.d.getElementById('pvFIDontUseIf'), 'You need a multi-user cloud system with live bank or booking-platform integrations.');
    var s1 = c.d.querySelector('select[name=filter_completion]'); s1.value = 'duration_1'; s1.dispatchEvent(new c.w.Event('change', { bubbles: true }));
    var s2 = c.d.querySelector('select[name=filter_format]'); s2.value = 'models'; s2.dispatchEvent(new c.w.Event('change', { bubbles: true }));
    var ed = c.d.querySelector('.rte.countable'); ed.focus(); ed.innerHTML = item.long;
    ['input', 'keyup', 'change', 'blur'].forEach(function (t) { ed.dispatchEvent(new c.w.Event(t, { bubbles: true })); });
    var kw = c.d.getElementById('nvKeywords');
    function key(type) { var e = new c.w.KeyboardEvent(type, { key: 'Enter', code: 'Enter', bubbles: true, cancelable: true }); Object.defineProperty(e, 'keyCode', { get: function () { return 13; } }); Object.defineProperty(e, 'which', { get: function () { return 13; } }); kw.dispatchEvent(e); }
    for (var t = 0; t < item.tags.length; t++) { kw.focus(); kw.value = item.tags[t]; kw.dispatchEvent(new c.w.Event('input', { bubbles: true })); key('keydown'); key('keypress'); key('keyup'); await sleep(300); }
    log(k + ' tags ' + c.q('.tags-editor span.tag').length);
    await sleep(2000);
    clickStep(c, /^Next step$/i); await sleep(3000);
    clickStep(c, /^Next step$/i); await sleep(3000);
    c.setv(c.d.getElementById('pvLicenseBusiness'), String(item.price));
    var free = c.d.getElementById('chkFreeForAll');
    if (free.checked) { var lab = free.closest('label') || free.parentElement; lab.click(); await sleep(1000); }
    if (free.checked) { free.click(); await sleep(1000); }
    if (free.checked) throw new Error('free toggle still on');
    await sleep(1500);
    await confirmSubmit(c);
    S.done[k] = draft; log(k + ' SUBMITTED ' + draft);
  }

  async function confirmSubmit(c) {
    var b = c.byText('.btn, span, a, div', /^Confirm$/i)[0];
    if (b) b.click(); else { var li = c.q('li').filter(function (e) { return c.vis(e) && /^Confirm$/i.test(e.innerText.trim()); })[0]; if (!li) throw new Error('no confirm'); li.click(); }
    var page = await waitFor(function () { var t = c.d.querySelector('main').innerText; return /Everything seems good|there is a problem/i.test(t) ? t : null; }, 20000, 'confirm page');
    if (!/Everything seems good/i.test(page)) {
      var i0 = page.indexOf('problem');
      throw new Error('validation: ' + page.slice(i0, i0 + 300).replace(/\s+/g, ' '));
    }
    var ack = c.q('input[type=checkbox]').filter(function (x) { return /acknowledge/i.test((x.labels && x.labels[0] && x.labels[0].innerText) || ''); })[0];
    if (!ack.checked) { ack.labels[0].click(); await sleep(800); }
    c.byText('.btn, span, a, div', /^Submit for validation$/i)[0].click();
    await waitFor(function () { return /sent for validation/i.test(c.d.body.innerText); }, 30000, 'submit confirmation');
  }

  async function finishDraft(id) {
    var fr = document.getElementById('elqFrame'); if (fr) fr.remove();
    fr = document.createElement('iframe'); fr.id = 'elqFrame';
    fr.style.cssText = 'position:fixed;left:0;top:0;width:1300px;height:900px;z-index:99999;background:#fff;border:3px solid #0f6b4f';
    fr.src = '/contributions/' + id + '/edit-draft'; document.body.appendChild(fr);
    await waitFor(function () { return fr.contentWindow.document.readyState === 'complete' && fr.contentWindow.document.getElementById('pvLicenseBusiness'); }, 90000, 'draft ' + id);
    await sleep(3000);
    var c = Ctx(fr.contentWindow);
    var free = c.d.getElementById('chkFreeForAll');
    if (free.checked) { (free.closest('label') || free.parentElement).click(); await sleep(1000); }
    await confirmSubmit(c);
    log('draft ' + id + ' SUBMITTED');
  }

  window.ELQ = {
    finish: async function (ids) { for (var i = 0; i < ids.length; i++) { try { await finishDraft(ids[i]); S.done['d' + ids[i]] = ids[i]; } catch (e) { log('draft ' + ids[i] + ' ERR ' + e.message); } } var f = document.getElementById('elqFrame'); if (f) f.remove(); return 'finished'; },
    run: async function (keys) {
      if (S.running) return 'already running';
      S.running = true; S.errors = S.errors || {};
      try {
        var data = await fetch(window.__ELQ_DATA).then(function (r) { return r.json(); });
        for (var i = 0; i < keys.length; i++) {
          var it = data.filter(function (x) { return x.k === keys[i]; })[0];
          if (!it || S.done[it.k]) continue;
          S.current = it.k;
          try { await publish(it); delete S.errors[it.k]; }
          catch (e) { S.errors[it.k] = e.message; log(it.k + ' ERR ' + e.message); }
          try { localStorage.setItem('ELQ_STATE', JSON.stringify({ done: S.done, errors: S.errors })); } catch (e) { }
        }
      } finally { S.running = false; S.current = null; var f = document.getElementById('elqFrame'); if (f) f.remove(); log('run finished'); }
      return S.done;
    }
  };
  log('ELQ ready');
})();
