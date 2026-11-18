import json
exec(open('/home/claude/work/partners/products.py').read())

CDN = "https://cdn.shopify.com/s/files/1/1007/1887/0832/files/"
data = [dict(k=p[0], h=p[1], plan=p[2], price=p[3], lang=p[4], aud=p[5], name=p[6], hook=p[7], tag=p[8], img=p[9]) for p in P]

CSS = r"""
#dp{--ink:#1d2433;--muted:#5b6475;--line:#e3e6ec;--brand:#0f6b4f;--brand2:#e8f4ef;--warn:#8a5a00;font-family:inherit;color:var(--ink);max-width:980px;margin:0 auto;direction:rtl;text-align:right;line-height:1.75}
#dp *{box-sizing:border-box}
#dp h2{font-size:1.45rem;margin:2.2rem 0 .6rem}
#dp h3{font-size:1.1rem;margin:1.2rem 0 .4rem}
#dp .hero{background:var(--brand);color:#fff;border-radius:14px;padding:28px 24px}
#dp .hero h1{color:#fff;font-size:1.9rem;margin:0 0 .4rem;line-height:1.35}
#dp .hero p{margin:.3rem 0;color:#eaf6f1}
#dp .stats{display:flex;flex-wrap:wrap;gap:10px;margin-top:14px}
#dp .stat{background:rgba(255,255,255,.12);border-radius:10px;padding:8px 14px;font-weight:700}
#dp .steps{counter-reset:s;list-style:none;padding:0;margin:0}
#dp .steps li{counter-increment:s;position:relative;padding:10px 46px 10px 0;border-bottom:1px solid var(--line)}
#dp .steps li:before{content:counter(s);position:absolute;right:0;top:10px;width:32px;height:32px;border-radius:50%;background:var(--brand2);color:var(--brand);font-weight:800;text-align:center;line-height:32px}
#dp .card{border:1px solid var(--line);border-radius:12px;padding:18px;margin:14px 0;background:#fff}
#dp label{display:block;font-weight:700;margin:10px 0 4px}
#dp input,#dp select,#dp textarea{width:100%;font:inherit;padding:10px 12px;border:1px solid #c9ced8;border-radius:8px;background:#fff;color:var(--ink)}
#dp textarea{min-height:120px;direction:auto;white-space:pre-wrap}
#dp .row{display:grid;grid-template-columns:1fr 1fr;gap:12px}
#dp .btn{display:inline-block;background:var(--brand);color:#fff;border:0;border-radius:8px;padding:10px 16px;font:inherit;font-weight:700;cursor:pointer;margin:6px 0 0 6px;text-decoration:none}
#dp .btn.alt{background:#fff;color:var(--brand);border:1px solid var(--brand)}
#dp .note{color:var(--muted);font-size:.92rem}
#dp .warn{background:#fff6e5;color:var(--warn);border-radius:8px;padding:8px 12px;font-size:.92rem}
#dp .out h3{display:flex;justify-content:space-between;align-items:center;gap:8px}
#dp .out h3 .btn{margin:0;padding:6px 12px;font-size:.85rem}
#dp .link{direction:ltr;text-align:left;font-family:ui-monospace,Menlo,monospace;font-size:.85rem;background:#f6f7f9;border-radius:8px;padding:8px 10px;word-break:break-all}
#dp .flyer{border:2px dashed var(--line);border-radius:12px;padding:22px;margin-top:10px;text-align:center}
#dp .flyer img.prod{max-width:100%;max-height:300px;border-radius:10px}
#dp .flyer .fh{font-size:1.5rem;font-weight:800;margin:.6rem 0 .2rem;line-height:1.4}
#dp .flyer .fp{font-size:1.1rem;margin:.2rem 0}
#dp .flyer .price{font-size:1.6rem;font-weight:800;color:var(--brand)}
#dp #dp-qr{display:inline-block;margin:10px auto;padding:8px;background:#fff}
#dp .ideas li{margin:.35rem 0}
#dp .en{direction:ltr;text-align:left}
#dp table{width:100%;border-collapse:collapse;font-size:.95rem}
#dp td,#dp th{border-bottom:1px solid var(--line);padding:8px 6px;text-align:inherit;vertical-align:top}
@media (max-width:640px){#dp .row{grid-template-columns:1fr}#dp .hero h1{font-size:1.5rem}}
@media print{body *{visibility:hidden!important}#dp-flyer,#dp-flyer *{visibility:visible!important}#dp-flyer{position:absolute;left:0;top:0;width:100%;border:0}#dp-flyer .noprint{display:none!important}}
"""

HTML = r"""
<div id="dp">
<div class="hero">
<h1>اربح 50% من كل بيعة: انضم إلى شركاء دار</h1>
<p>نبيع 36 نظام إكسل جاهزًا لأصحاب الأعمال (مكاتب عقار، مقاولات، محاسبة، صالونات، مطاعم وغيرها). أنت تنشر رابطك، ونحن نتولى البيع والتسليم والدعم، وتصلك عمولتك تلقائيًا.</p>
<div class="stats"><span class="stat">عمولة 50%</span><span class="stat">8.5$ عن كل نظام بـ17$</span><span class="stat">14.5$ عن كل نظام بـ29$</span><span class="stat">تتبع 30 يومًا</span><span class="stat">التسجيل مجاني</span></div>
</div>

<h2>كيف تبدأ في 3 دقائق</h2>
<ol class="steps">
<li><b>أنشئ حسابًا مجانيًا في Whop</b> (منصة الدفع التي نبيع عبرها، ومنها تُصرف عمولتك): <a href="https://whop.com/dar-94b4/" target="_blank" rel="noopener">افتح متجر دار في Whop</a> وسجّل الدخول.</li>
<li><b>انسخ اسم المستخدم</b> الخاص بك في Whop (يظهر في ملفك الشخصي).</li>
<li><b>اكتبه في المولّد بالأسفل</b> واختر الفئة التي تعرفها، فيجهز لك رابطك الخاص ورسائل جاهزة للنشر وملصقًا بباركود للزيارات الميدانية.</li>
<li><b>انشر وتابع</b>: كل من يشتري عبر رابطك خلال 30 يومًا تُسجّل عمولته لك تلقائيًا، وتراها في حسابك.</li>
</ol>
<p class="note">اشتريت منّا من قبل؟ أنت شريك أيضًا: رابطك يعمل بالطريقة نفسها وبالعمولة نفسها.</p>

<h2>مولّد حملتك الخاصة</h2>
<div class="card">
<div class="row">
<div><label for="dp-u">اسم المستخدم في Whop</label><input id="dp-u" placeholder="مثال: ahmed123" autocomplete="off" dir="ltr"></div>
<div><label for="dp-p">لمن ستسوّق؟</label><select id="dp-p"></select></div>
</div>
<div id="dp-warn" class="warn" style="margin-top:10px">اكتب اسم المستخدم أولًا حتى تُحسب العمولة لك. بدونه يكون الرابط عاديًا بلا عمولة.</div>
<button class="btn" id="dp-go" type="button">جهّز حملتي</button>
<button class="btn alt" id="dp-idea" type="button">ماذا أنشر الآن؟</button>
</div>

<div id="dp-out" class="out" style="display:none">
<div class="card">
<h3><span>رابطك الخاص لهذا النظام</span><button class="btn alt" type="button" data-copy="dp-link">نسخ</button></h3>
<div class="link" id="dp-link"></div>
<p class="note">رابط متجر دار كاملًا (لكل الأنظمة):</p>
<div class="link" id="dp-store"></div>
</div>
<div class="card"><h3><span>رسالة واتساب</span><button class="btn alt" type="button" data-copy="dp-wa">نسخ</button></h3><textarea id="dp-wa" readonly></textarea>
<a class="btn" id="dp-wa-open" target="_blank" rel="noopener">افتح في واتساب</a></div>
<div class="card"><h3><span>منشور X</span><button class="btn alt" type="button" data-copy="dp-x">نسخ</button></h3><textarea id="dp-x" readonly></textarea>
<a class="btn" id="dp-x-open" target="_blank" rel="noopener">انشر الآن</a></div>
<div class="card"><h3><span>نص الستوري أو الحالة</span><button class="btn alt" type="button" data-copy="dp-st">نسخ</button></h3><textarea id="dp-st" readonly></textarea></div>
<div class="card"><h3><span>رسالة متابعة بعد يومين</span><button class="btn alt" type="button" data-copy="dp-fu">نسخ</button></h3><textarea id="dp-fu" readonly></textarea></div>
<div class="card"><h3><span>للزيارة الميدانية</span></h3>
<p id="dp-field"></p>
<div class="flyer" id="dp-flyer">
<img class="prod" id="dp-img" alt="">
<div class="fh" id="dp-fh"></div>
<div class="fp" id="dp-fp"></div>
<div class="price" id="dp-price"></div>
<div id="dp-qr"></div>
<div class="note" id="dp-fn"></div>
<div class="noprint"><button class="btn" type="button" id="dp-print">اطبع الملصق</button><button class="btn alt" type="button" id="dp-dl">حمّل الباركود</button></div>
</div>
</div>
</div>

<h2>أفكار تبيع أكثر</h2>
<ul class="ideas">
<li><b>ابدأ بمن تعرفهم</b>: صاحب مكتب عقار أو صالون أو مطعم في حيّك. رسالة واتساب شخصية واحدة أقوى من عشرة منشورات عامة.</li>
<li><b>المقارنة بالاشتراك الشهري</b>: أغلب برامج الإدارة باشتراك شهري يتكرر. نظامنا يُدفع مرة واحدة ويبقى للعميل.</li>
<li><b>اعرض لا تشرح</b>: أرسل صورة لوحة التحكم من صفحة المنتج مع رابطك. البيانات التجريبية داخل الملف تجعل العميل يرى النتيجة في دقائق.</li>
<li><b>المجموعات المهنية</b>: مجموعات الوسطاء العقاريين والمقاولين والمحاسبين، بشرط احترام قوانين كل مجموعة وعدم الإزعاج.</li>
<li><b>الزيارة الميدانية</b>: اطبع الملصق، واترك نسخة عند الاستقبال، والباركود يفتح رابطك مباشرة.</li>
<li><b>عميل يحيل عميلًا</b>: بعد أي بيعة، اطلب من العميل أن يرشحك لزميل في المجال نفسه.</li>
</ul>

<h2>قواعد بسيطة</h2>
<ul class="ideas">
<li>لا رسائل عشوائية ولا إزعاج، ولا تنشر في مكان يمنع الإعلانات.</li>
<li>لا وعود غير موجودة في صفحة المنتج، ولا تنتحل صفة الشركة.</li>
<li>تريد كود خصم باسمك لجمهورك؟ راسلنا على <a href="mailto:service@dar.ink">service@dar.ink</a> واذكر اسم المستخدم في Whop.</li>
</ul>

<div class="en">
<h2>Earn 50% on every sale (English)</h2>
<p>We sell 36 ready-made Excel business systems. Create a free Whop account, open <a href="https://whop.com/dar-94b4/" target="_blank" rel="noopener">the Dar store on Whop</a>, copy your Whop username, type it in the generator above and pick an audience: you get your personal link, ready-to-post texts and a printable flyer with a QR code. Anyone who buys through your link within 30 days earns you 50% of the sale, credited automatically. Questions or a personal discount code for your audience: <a href="mailto:service@dar.ink">service@dar.ink</a>.</p>
</div>
</div>
"""

JS = r"""
(function(){
var D=__DATA__;
var STORE='https://darjob.myshopify.com/products/';
function $(i){return document.getElementById(i)}
var sel=$('dp-p');
var gA=document.createElement('optgroup');gA.label='بالعربي';
var gE=document.createElement('optgroup');gE.label='English';
D.forEach(function(p,i){var o=document.createElement('option');o.value=i;o.textContent=(p.lang=='ar'?p.aud+' — '+p.name:p.name+' ('+p.aud+')')+' • '+p.price+'$';(p.lang=='ar'?gA:gE).appendChild(o)});
sel.appendChild(gA);sel.appendChild(gE);
try{var s=localStorage.getItem('dp_u');if(s)$('dp-u').value=s}catch(e){}
function user(){return ($('dp-u').value||'').trim().replace(/^@/,'').replace(/[^A-Za-z0-9_.-]/g,'')}
function link(p,u){return u?'https://whop.com/checkout/'+p.plan+'?a='+encodeURIComponent(u):STORE+p.h}
function texts(p,L){
 if(p.lang=='ar'){
  return {
  wa:'السلام عليكم 👋\nرسالة تهم '+p.aud+': '+p.hook+'.\n\n'+p.name+': ملف إكسل جاهز بالعربي، تدفع '+p.price+'$ مرة واحدة بدون اشتراك شهري، وفيه بيانات تجريبية تشوف بها كل شيء قبل ما تبدأ.\nضمان استرجاع المبلغ خلال 14 يومًا.\n\n'+L,
  x:p.hook+'.\n\n'+p.name+': ملف إكسل بالعربي بـ'+p.price+'$ مرة واحدة، بلا اشتراك.\n'+L+'\n#'+p.tag+' #إكسل',
  st:'إلى '+p.aud+' 👇\n'+p.hook+'\n'+p.price+'$ مرة واحدة • بالعربي • ضمان 14 يومًا\n'+L,
  fu:'أهلًا، هل لحقت تشوف '+p.name+'؟ أول ما تحمّله تلاقي فيه بيانات تجريبية، فتعرف خلال دقائق إذا يناسبك، وإذا ما ناسبك يرجع لك المبلغ خلال 14 يومًا.\n'+L,
  field:'عرّف بنفسك واسأل سؤالًا واحدًا: «كيف تتابعون هذا الشغل حاليًا: دفتر، ملفات متفرقة، أو برنامج باشتراك شهري؟». اعرض صورة لوحة التحكم من جوالك، ثم اترك الملصق أو أرسل الرابط في واتساب أمامه.',
  fh:p.name, fp:p.hook, price:p.price+'$ مرة واحدة • بلا اشتراك', fn:'امسح الباركود للتفاصيل والشراء • ضمان استرجاع 14 يومًا'};
 }
 var apps=p.price>=29?'Excel and Google Sheets':'Excel';
 return {
  wa:'Hi! If you work with '+p.aud+', this may help: '+p.hook+'.\n\n'+p.name+' is a ready-made '+apps+' system. '+p.price+' dollars once, no subscription, with sample data inside so you see every dashboard before you type a row. 14-day money-back guarantee.\n\n'+L,
  x:p.hook.charAt(0).toUpperCase()+p.hook.slice(1)+'.\n\n'+p.name+': '+p.price+' dollars once, no monthly fee.\n'+L+'\n#'+p.tag+' #excel',
  st:'For '+p.aud+':\n'+p.hook+'\n'+p.price+' dollars once • 14-day guarantee\n'+L,
  fu:'Hi again, did you get a chance to look at '+p.name+'? It opens with sample data, so you can tell in five minutes whether it fits. If it does not, you get a refund within 14 days.\n'+L,
  field:'Introduce yourself and ask one question: how do you track this today, on paper, in scattered files, or with a monthly subscription? Show the dashboard picture on your phone, then leave the flyer or send the link on the spot.',
  fh:p.name, fp:p.hook.charAt(0).toUpperCase()+p.hook.slice(1), price:p.price+' dollars once • no subscription', fn:'Scan for details • 14-day money-back guarantee'};
}
var qr=null;
function go(){
 var u=user(); try{localStorage.setItem('dp_u',u)}catch(e){}
 $('dp-warn').style.display=u?'none':'block';
 var p=D[+sel.value], L=link(p,u), t=texts(p,L);
 $('dp-link').textContent=L;
 $('dp-store').textContent=u?'https://whop.com/dar-94b4/?a='+encodeURIComponent(u):'https://whop.com/dar-94b4/';
 $('dp-wa').value=t.wa;$('dp-x').value=t.x;$('dp-st').value=t.st;$('dp-fu').value=t.fu;$('dp-field').textContent=t.field;
 $('dp-wa-open').href='https://wa.me/?text='+encodeURIComponent(t.wa);
 $('dp-x-open').href='https://x.com/intent/post?text='+encodeURIComponent(t.x);
 $('dp-img').src='https://cdn.shopify.com/s/files/1/1007/1887/0832/files/'+p.img;$('dp-img').alt=p.name;$('dp-fh').textContent=t.fh;$('dp-fp').textContent=t.fp;$('dp-price').textContent=t.price;$('dp-fn').textContent=t.fn;
 var box=$('dp-qr');box.innerHTML='';
 if(window.QRCode){qr=new QRCode(box,{text:L,width:180,height:180,correctLevel:QRCode.CorrectLevel.M})}
 else{box.textContent=L}
 $('dp-out').style.display='block';
 $('dp-out').scrollIntoView({behavior:'smooth',block:'start'});
}
$('dp-go').onclick=go;
$('dp-idea').onclick=function(){sel.value=Math.floor(Math.random()*D.length);go()};
document.querySelectorAll('#dp [data-copy]').forEach(function(b){b.onclick=function(){var el=$(b.getAttribute('data-copy'));var v=el.value!==undefined&&el.tagName=='TEXTAREA'?el.value:el.textContent;
 (navigator.clipboard?navigator.clipboard.writeText(v):Promise.reject()).then(function(){b.textContent='تم النسخ ✓';setTimeout(function(){b.textContent='نسخ'},1500)},function(){if(el.select){el.select()}})}});
$('dp-print').onclick=function(){window.print()};
$('dp-dl').onclick=function(){var c=$('dp-qr').querySelector('canvas'),i=$('dp-qr').querySelector('img');var src=c?c.toDataURL('image/png'):(i?i.src:'');if(!src)return;var a=document.createElement('a');a.href=src;a.download='dar-qr.png';document.body.appendChild(a);a.click();a.remove()};
var m=location.search.match(/[?&]a=([A-Za-z0-9_.-]+)/);if(m){$('dp-u').value=m[1]}
})();
"""

page = ("<style>" + CSS + "</style>" + HTML +
        '<script src="https://cdnjs.cloudflare.com/ajax/libs/qrcodejs/1.0.0/qrcode.min.js"></script>'
        "<script>" + JS.replace("__DATA__", json.dumps(data, ensure_ascii=False)) + "</script>")
open('/home/claude/work/partners/partners_page.html', 'w').write(page)
print(len(page))
