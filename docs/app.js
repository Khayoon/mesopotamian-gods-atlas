'use strict';
const $=id=>document.getElementById(id);
const esc=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
let research,cities,layout,selected,offsets={},svgRoot;
const cityName=id=>cities.find(c=>c.id===id)?.name||id;
const safeLink=url=>/^https?:\/\//.test(url)?esc(url):'#';
function cite(claim){return `<p class="meta"><a href="${safeLink(claim.url)}" target="_blank" rel="noopener">${esc(claim.work)}</a>, ${esc(claim.passage)}<br>${esc(claim.period)}</p>`;}
function show(id){selected=id;const g=research.deities.find(d=>d.id===id);if(!g)return;
 $('detail').innerHTML=`<h3>${esc(g.name)}</h3><p>${esc(g.domains.join(' · '))}</p>${g.aliases.length?`<p class="meta">Other names / spellings: ${esc(g.aliases.join(', '))}</p>`:''}<p>${esc(g.nameNote)}</p><h4>Birth, creation and divine origins</h4>${g.originTraditions.length?g.originTraditions.map(t=>`<div class="claim"><p>${esc(t.summary)}</p><p class="meta">Claim type: ${esc(t.locationType)}${t.cityId?' · '+esc(cityName(t.cityId)):''}. ${t.cityId&&cities.find(c=>c.id===t.cityId)?.coordinates?'City anchor only; not the exact event location.':'No precise origin coordinate assigned.'}</p>${cite(t)}</div>`).join(''):'<p>No birth or creation tradition established in the sources checked. Cult evidence below must not be substituted for one.</p>'}<h4>Cult seats, residence and patronage</h4>${g.cityEvidence.length?g.cityEvidence.map(e=>`<div class="claim"><p><strong>${esc(cityName(e.cityId))}</strong> — ${esc(e.summary)}</p>${cite(e)}</div>`).join(''):'<p>No securely located cult-city claim included in this catalogue.</p>'}<h4>Interpretation and identity</h4>${g.notes.map(n=>`<p>${esc(n)}</p>`).join('')}<h4>Geographic anchors</h4>${g.cityIds.map(id=>{const c=cities.find(c=>c.id===id);return `<p class="meta">${esc(cityName(id))}: ${c?.coordinates?`${c.coordinates[1].toFixed(5)}° N, ${c.coordinates[0].toFixed(5)}° E — <a href="${safeLink(c.coordinateSource)}">Pleiades representative site point</a>`:esc(c?.note||'Unlocated or broad setting; no coordinate assigned.')}</p>`;}).join('')}`;
 document.querySelectorAll('#results button').forEach(b=>b.setAttribute('aria-current',String(b.dataset.id===id)));
 const label=layout.labels.find(l=>l.deityIds.includes(id));if(label){$('label').value=label.cityId;syncControls();}
}
function filter(){const query=$('search').value.toLowerCase(),type=$('evidence').value,city=$('city').value;
const list=research.deities.filter(g=>{
 if(query&&!JSON.stringify(g).toLowerCase().includes(query)&&!g.cityIds.some(id=>cityName(id).toLowerCase().includes(query)))return false;
 if(city!=='all'&&!g.cultCityIds.includes(city))return false;
 if(type==='origins'&&!g.originTraditions.length)return false;
 if(type==='birth'&&!g.originTraditions.some(t=>t.locationType==='birth-city'||t.locationType==='city-birth'))return false;
 if(type==='cosmic'&&!g.originTraditions.some(t=>!t.cityId))return false;
 if(type==='seats'&&!g.cityEvidence.length)return false;return true;});
 $('resultCount').textContent=`${list.length} of ${research.deities.length} deity records`;
 $('results').innerHTML=list.map(g=>`<button role="listitem" data-id="${esc(g.id)}" aria-current="${g.id===selected}">${esc(g.name)}<small>${g.originTraditions.length} origin claims · ${g.cultCityIds.length} place associations</small></button>`).join('');
 $('results').querySelectorAll('button').forEach(b=>b.onclick=()=>show(b.dataset.id));
 if(list.length&&!list.some(g=>g.id===selected))show(list[0].id);else if(!list.length)$('detail').innerHTML='<p>No matching entries.</p>';
}
function syncControls(){const o=offsets[$('label').value]||{x:0,y:0};$('offsetX').value=o.x;$('offsetY').value=o.y;}
function applyOffset(id,x,y){offsets[id]={x,y};const group=svgRoot.querySelector(`#label-${id}`);group?.setAttribute('transform',`translate(${x} ${y})`);
 for(const selector of [`#leader-${id}`,`#leader-halo-${id}`]){const leader=svgRoot.querySelector(selector);if(leader){const orig=leader.dataset.original.split(' ').map(p=>p.split(',').map(Number));if(leader.dataset.curve==='quadratic'){const [a,c,b]=orig;leader.setAttribute('d',`M${a.join(',')}Q${c[0]+x*.5},${c[1]+y*.5} ${b[0]+x},${b[1]+y}`);}else{const next=orig.map((p,i)=>i?[p[0]+x,p[1]+y]:p);leader.setAttribute('points',next.map(p=>p.join(',')).join(' '));}}}
}
function download(blob,name){const a=document.createElement('a');a.href=URL.createObjectURL(blob);a.download=name;a.click();setTimeout(()=>URL.revokeObjectURL(a.href),1000);}
async function portableSVG(){const clone=svgRoot.cloneNode(true);for(const [filename,weight,family] of [['GentiumPlus-Regular.ttf',400,'Gentium'],['GentiumPlus-Bold.ttf',700,'Gentium'],['SourceSans3-Regular.ttf',400,'SourceSans'],['SourceSans3-Bold.ttf',700,'SourceSans']]){const data=new Uint8Array(await (await fetch('vendor/'+filename)).arrayBuffer());let b='';for(let i=0;i<data.length;i+=8192)b+=String.fromCharCode(...data.subarray(i,i+8192));const style=document.createElementNS('http://www.w3.org/2000/svg','style');style.textContent=`@font-face{font-family:${family};src:url(data:font/ttf;base64,${btoa(b)});font-weight:${weight}}`;clone.querySelector('defs').append(style);}return new XMLSerializer().serializeToString(clone);}
Promise.all([fetch('data/research.json').then(r=>r.json()),fetch('data/cities.json').then(r=>r.json()),fetch('data/poster-layout.json').then(r=>r.json()),fetch('mesopotamian-gods.svg').then(r=>r.text())]).then(([r,c,l,svg])=>{
 research=r;cities=c;layout=l;$('totals').textContent=`${r.deities.length} researched deity records; ${r.deities.reduce((n,g)=>n+g.originTraditions.length,0)} separately recorded origin claims. The poster is a geographic selection; cosmic, disputed and unlocated claims remain here with their sources.`;
 cities.filter(c=>research.deities.some(g=>g.cultCityIds.includes(c.id))).sort((a,b)=>a.name.localeCompare(b.name)).forEach(c=>$('city').add(new Option(c.name+(c.coordinates?'':' — unpinned'),c.id)));
 $('artboard').innerHTML=svg;svgRoot=$('artboard').querySelector('svg');
 layout.labels.forEach(l=>$('label').add(new Option(cityName(l.cityId),l.cityId)));
 ['search','city','evidence'].forEach(id=>$(id).addEventListener('input',filter));$('label').onchange=syncControls;
 ['offsetX','offsetY'].forEach(id=>$(id).oninput=()=>applyOffset($('label').value,Number($('offsetX').value),Number($('offsetY').value)));
 $('reset').onclick=()=>{layout.labels.forEach(l=>applyOffset(l.cityId,0,0));syncControls();};
 $('svgExport').onclick=async()=>download(new Blob([await portableSVG()],{type:'image/svg+xml'}),'mesopotamian-gods-edited.svg');
 $('jsonExport').onclick=()=>download(new Blob([JSON.stringify(offsets,null,2)],{type:'application/json'}),'poster-offsets.json');
 $('pngExport').onclick=async()=>{try{$('exportStatus').textContent='Rendering 4000 × 5000 PNG…';const blob=new Blob([await portableSVG()],{type:'image/svg+xml'});const url=URL.createObjectURL(blob);const img=new Image();await new Promise((ok,no)=>{img.onload=ok;img.onerror=no;img.src=url;});const canvas=document.createElement('canvas');canvas.width=4000;canvas.height=5000;canvas.getContext('2d').drawImage(img,0,0,4000,5000);URL.revokeObjectURL(url);canvas.toBlob(b=>{if(b){download(b,'mesopotamian-gods-edited.png');$('exportStatus').textContent='PNG exported. Inspect the edited labels at full resolution.';}else $('exportStatus').textContent='PNG export failed; the published PNG and editable SVG remain available.';},'image/png');}catch(e){$('exportStatus').textContent='PNG export could not complete; use the published PNG or export the SVG.';}};
 let drag;svgRoot.addEventListener('pointerdown',e=>{const g=e.target.closest('g[data-city]');if(!g)return;const id=g.dataset.city;const p=new DOMPoint(e.clientX,e.clientY).matrixTransform(svgRoot.getScreenCTM().inverse());drag={id,p,old:offsets[id]||{x:0,y:0}};svgRoot.setPointerCapture(e.pointerId);$('label').value=id;syncControls();});
 svgRoot.addEventListener('pointermove',e=>{if(!drag)return;const p=new DOMPoint(e.clientX,e.clientY).matrixTransform(svgRoot.getScreenCTM().inverse());applyOffset(drag.id,Math.round(drag.old.x+p.x-drag.p.x),Math.round(drag.old.y+p.y-drag.p.y));syncControls();});svgRoot.addEventListener('pointerup',()=>drag=null);svgRoot.addEventListener('pointercancel',()=>drag=null);
 filter();show('nanshe');
}).catch(()=>{$('resultCount').textContent='Research could not load. Download the JSON files directly, or serve this folder over HTTP.';});
