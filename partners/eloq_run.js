/* Eloquens listing automation for Dar Templates (runs in the logged-in author's page). */
(function () {
  var DATA_URL = 'https://raw.githubusercontent.com/a04032417-svg/Dar101/refs/heads/pipeline/partners/eloq_data.json';
  var SHOP = 'https://cdn.shopify.com/s/files/1/1007/1887/0832/files/';
  var S = window.__elq = window.__elq || { log: [] };
  function log(m) { S.log.push(new Date().toISOString().slice(11, 19) + ' ' + m); S.last = m; }
  function sleep(ms) { return new Promise(function (r) { setTimeout(r, ms); }); }
  function vis(e) { return e && e.offsetParent !== null; }
  function q(sel) { return Array.prototype.slice.call(document.querySelectorAll(sel)); }
  function byText(sel, re) { return q(sel).filter(function (e) { return vis(e) && re.test((e.innerText || '').trim()); }); }
  async function waitFor(fn, ms, label) {
    var t0 = Date.now();
    while (Date.now() - t0 < ms) { var v = fn(); if (v) return v; await sleep(500); }
    throw new Error('timeout: ' + label);
  }
  async function data() {
    if (S.data) return S.data;
    S.data = await fetch(DATA_URL + '?t=' + Date.now()).then(function (r) { return r.json(); });
    return S.data;
  }
  function item(d, k) { return d.filter(function (x) { return x.k === k; })[0]; }
  function setv(el, v) {
    el.focus(); el.value = v;
    ['input', 'change', 'keyup', 'blur'].forEach(function (t) { el.dispatchEvent(new Event(t, { bubbles: true })); });
  }
  async function blob(u) {
    var r = await fetch(u);
    if (!r.ok) throw new Error('fetch ' + r.status + ' ' + u);
    return r.blob();
  }
  function dz() { return Dropzone.instances.filter(function (d) { return d.element.id === 'formMediaUpload'; })[0] || Dropzone.instances[0]; }
  async function uploadFiles(files) {
    var z = dz(), done = 0, fail = 0;
    function ok() { done++; } function ko(f, m) { fail++; log('upload error ' + f.name + ' ' + (m && m.message || m)); }
    z.on('success', ok); z.on('error', ko);
    for (var i = 0; i < files.length; i++) {
      z.addFile(files[i]);
      if (i === 0 && files.length > 1) { await waitFor(function () { return done + fail >= 1; }, 600000, 'first upload'); }
    }
    await waitFor(function () { return done + fail >= files.length; }, 1800000, 'uploads');
    z.off('success', ok); z.off('error', ko);
    if (fail) throw new Error('upload failures ' + fail);
  }
  function openLibrary(n) {
    var b = byText('.btn, span, a, div', /^(attach_file|add_photo_alternate)?\s*Add from library$/i)
      .filter(function (e) { return e.children.length < 3; });
    b[n].click();
  }
  async function addSelected(expect) {
    var re = new RegExp('^ADD ' + expect + ' (IMAGES?|ITEMS?)$', 'i');
    var b = await waitFor(function () { return byText('.btn, a, span, button', re)[0]; }, 120000, 'add button ' + expect);
    b.click(); await sleep(2500);
  }
  function clickStep(re) { var b = byText('.btn, span, a, div', re).filter(function (e) { return e.children.length < 3; })[0]; if (!b) throw new Error('no step ' + re); b.click(); }

  window.ELQ = {
    create: async function (k) {
      var d = item(await data(), k); S.k = k; S.state = 'creating';
      var t = document.querySelector('input[name=title]'); setv(t, d.title);
      q('span.btnCheckCreation').filter(vis)[0].click();
      return d.title;
    },
    fill: async function (k) {
      S.k = k; S.state = 'filling'; S.log = [];
      try {
        var all = await data(), d = item(all, k);
        var imgs = d.imgs;
        if (imgs === 'SHOPIFY') {
          var m = JSON.parse(localStorage.getItem('ELQ_IMG'));
          imgs = m[d.h].img.slice(0, 8).map(function (p) { return SHOP + p; });
        }
        log('fetch images ' + imgs.length);
        var files = [];
        for (var i = 0; i < imgs.length; i++) {
          var b = await blob(imgs[i]);
          var ext = (b.type.indexOf('png') >= 0) ? 'png' : 'jpg';
          files.push(new File([b], ('0' + (i + 1)).slice(-2) + '-' + k + '.' + ext, { type: b.type || 'image/jpeg' }));
        }
        openLibrary(0); await sleep(1500);
        log('upload images'); await uploadFiles(files);
        await addSelected(files.length); log('images added');
        log('fetch zips ' + d.zips.length);
        var zf = [];
        for (var j = 0; j < d.zips.length; j++) { zf.push(new File([await blob(d.zips[j].u)], d.zips[j].n, { type: 'application/zip' })); }
        openLibrary(1); await sleep(1500);
        log('upload zips'); await uploadFiles(zf);
        await addSelected(zf.length); log('zips added');
        setv(document.getElementById('nvDescShort'), d.short);
        setv(document.getElementById('nvContents'), d.contents);
        setv(document.getElementById('pvFIObjectives'), 'Give ' + d.title.split(' in Excel')[0].replace(/ System| Template[s]?| Management/g, '').toLowerCase() + ' owners one connected Excel system that shows what needs attention and what really makes money, without a monthly subscription.');
        setv(document.getElementById('pvFIUseIf'), 'You run this kind of business and keep its records in notebooks, chats or scattered spreadsheets, and you want clear numbers and alerts in one place.');
        setv(document.getElementById('pvFIDontUseIf'), 'You need a multi-user cloud system with live bank or booking-platform integrations.');
        var s1 = document.querySelector('select[name=filter_completion]'); s1.value = 'duration_1'; s1.dispatchEvent(new Event('change', { bubbles: true }));
        var s2 = document.querySelector('select[name=filter_format]'); s2.value = 'models'; s2.dispatchEvent(new Event('change', { bubbles: true }));
        var ed = document.querySelector('.rte.countable'); ed.focus(); ed.innerHTML = d.long;
        ['input', 'keyup', 'change', 'blur'].forEach(function (t) { ed.dispatchEvent(new Event(t, { bubbles: true })); });
        var kw = jQuery('#nvKeywords');
        d.tags.forEach(function (tg) { kw.val(tg); kw.trigger(jQuery.Event('keydown', { which: 13, keyCode: 13 })); kw.trigger(jQuery.Event('keyup', { which: 13, keyCode: 13 })); });
        log('text set'); await sleep(2000);
        clickStep(/^Next step$/i); await sleep(2500);
        clickStep(/^Next step$/i); await sleep(2500);
        var price = document.getElementById('pvLicenseBusiness'); setv(price, String(d.price));
        var free = document.getElementById('chkFreeForAll');
        if (free.checked) { (free.closest('label') || free.parentElement).click(); await sleep(800); if (free.checked) { free.click(); } }
        await sleep(1500);
        if (free.checked) throw new Error('free still on');
        clickStep(/^Confirm$/i); await sleep(4000);
        var page = document.querySelector('main').innerText;
        if (!/Everything seems good/i.test(page)) { S.state = 'needs-fix'; log('validation: ' + page.slice(page.indexOf('CONFIRM'), page.indexOf('CONFIRM') + 400)); return S.state; }
        var ack = q('input[type=checkbox]').filter(function (c) { return /acknowledge/i.test((c.labels && c.labels[0] && c.labels[0].innerText) || ''); })[0];
        if (!ack.checked) { ack.labels[0].click(); await sleep(500); }
        clickStep(/^Submit for validation$/i); await sleep(5000);
        S.state = /sent for validation/i.test(document.body.innerText) ? 'submitted' : 'submit-unclear';
        log(S.state);
      } catch (e) { S.state = 'error'; log('ERR ' + e.message); }
      return S.state;
    }
  };
  log('ELQ ready');
})();
