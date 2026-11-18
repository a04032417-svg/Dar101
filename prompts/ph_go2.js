window.__phimg=async function(P){const st=window.__ph={step:'start'};try{
const f=document.querySelector('#addproduct');const E=n=>f.elements[n];
const setv=(n,v)=>{const e=E(n);e.value=v;e.dispatchEvent(new Event('input',{bubbles:true}));e.dispatchEvent(new Event('change',{bubbles:true}));};
setv('p_name',P.name);setv('p_price',P.price||'17');
const q=Quill.find(document.querySelector('.ql-editor').parentElement);q.setText('');q.clipboard.dangerouslyPasteHTML(0,P.html);E('p_desc').value=q.root.innerHTML;
document.querySelector('input[name=product_status][value=visible]').click();E('seo_description').value=P.seo;
const ins=[...document.querySelectorAll('input[type=file]')];st.step='imgs';
const imgs=[];for(let i=0;i<P.imgs.length;i++){const b=await (await fetch(P.imgs[i])).blob();imgs.push(new File([b],P.slug+'-'+(i+1)+'.jpg',{type:'image/jpeg'}));}
const dt=new DataTransfer();imgs.forEach(x=>dt.items.add(x));ins[1].files=dt.files;ins[1].dispatchEvent(new Event('change',{bubbles:true}));st.imgs=imgs.map(x=>x.size);st.step='imgs_uploading';
const zb=await (await fetch(P.zip)).blob();window.__zb=new File([zb],P.zipName,{type:'application/zip'});st.zip=zb.size;st.step='zip_ready';
}catch(e){st.err=String(e)}};
window.__zipput=function(){const ins=[...document.querySelectorAll('input[type=file]')];const dz=new DataTransfer();dz.items.add(window.__zb);ins[0].files=dz.files;ins[0].dispatchEvent(new Event('change',{bubbles:true}));window.__ph.step='zip_uploading';return 'ok'};
window.__go=async function(x,zip,commit){const P=await (await fetch('https://raw.githubusercontent.com/a04032417-svg/Dar101/'+commit+'/pub/payhip/'+x+'.json')).json();P.zip=zip;window.__P=P;__phimg(P)};
window.__auto=setInterval(()=>{try{const st=window.__ph||{};if(st.step!=='zip_ready')return;const busy=/Uploading|uploading/.test((document.querySelector('#imagelist, .product-images, #addproduct')||document.body).innerText);const sw=document.querySelector('.sweet-alert.visible, .swal2-popup');if(sw){const b=sw.querySelector('button.confirm, .swal2-confirm');if(b)b.click();return}if(!busy){__zipput();}}catch(e){}},20000);
window.__sub=setInterval(()=>{try{const st=window.__ph||{};if(st.step!=='zip_uploading')return;const fl=(document.querySelector('#filelist')||{}).innerText||'';if(/\.zip/i.test(fl)&&/Delete/i.test(fl)&&!/Uploading|%/.test(fl)){st.step='submitting';clearInterval(window.__auto);clearInterval(window.__sub);const b=[...document.querySelectorAll('button,input[type=submit]')].find(b=>/Add Product/i.test(b.innerText||b.value||''));b.click();}}catch(e){}},5000);
'runner ready';

window.__fx=async(u,ms)=>{for(let k=0;k<4;k++){try{const ac=new AbortController();const t=setTimeout(()=>ac.abort(),ms||25000);const r=await fetch(u,{signal:ac.signal,cache:'no-store'});const b=await r.blob();clearTimeout(t);if(r.ok)return b;}catch(e){}}throw new Error('fail '+u.slice(0,80))};
window.__go2=async function(x,zip,commit){const st=window.__ph={step:'start'};try{const P=await (await fetch('https://raw.githubusercontent.com/a04032417-svg/Dar101/'+commit+'/pub/payhip/'+x+'.json')).json();P.zip=zip;window.__P=P;
const f=document.querySelector('#addproduct');const E=n=>f.elements[n];const setv=(n,v)=>{const e=E(n);e.value=v;e.dispatchEvent(new Event('input',{bubbles:true}));e.dispatchEvent(new Event('change',{bubbles:true}));};
setv('p_name',P.name);setv('p_price',P.price||'29');const q=Quill.find(document.querySelector('.ql-editor').parentElement);q.setText('');q.clipboard.dangerouslyPasteHTML(0,P.html);E('p_desc').value=q.root.innerHTML;
document.querySelector('input[name=product_status][value=visible]').click();E('seo_description').value=P.seo;st.step='imgs';
const imgs=[];for(let i=0;i<P.imgs.length;i++){const b=await __fx(P.imgs[i]);imgs.push(new File([b],P.slug+'-'+(i+1)+'.jpg',{type:'image/jpeg'}));st.got=i+1;}
const ins=[...document.querySelectorAll('input[type=file]')];const dt=new DataTransfer();imgs.forEach(x=>dt.items.add(x));ins[1].files=dt.files;ins[1].dispatchEvent(new Event('change',{bubbles:true}));st.imgs=imgs.map(x=>x.size);st.step='imgs_uploading';
const zb=await __fx(P.zip,150000);window.__zb=new File([zb],P.zipName,{type:'application/zip'});st.zip=zb.size;st.step='zip_ready';}catch(e){st.err=String(e)}};
'go2 ready';
