'use strict';
const $=id=>document.getElementById(id), NS='http://www.w3.org/2000/svg';
const esc=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const fold=s=>String(s).normalize('NFD').replace(/\p{M}/gu,'').toLowerCase();
const safeLink=url=>/^https?:\/\//.test(url)?esc(url):'#';
const state={scope:'all',selected:null,city:null};
let research,cities,layout,svg,places,initialView,view,cityGroups,measure;
const compact=()=>matchMedia('(max-width:600px)').matches;
const cityName=id=>cities.get(id)?.name||id;
const locatedIds=g=>g.cityIds.filter(id=>cities.get(id)?.coordinates);
const birth=t=>['city-birth','birth-city'].includes(t.locationType);
const deityWord=n=>n===1?'deity':'deities';
const claimNames={'birth-city':'Explicit city birth','city-birth':'Explicit city birth','city-conception':'Conception','conception-city':'Conception','city-birth-inference':'Inferred shrine birth','cosmic':'Cosmic origin','childhood-city':'Childhood setting','broad-regional-setting':'Broad regional setting','broad-coastal-setting':'Broad coastal setting'};
function claimKind(g,cid){const claims=g.originTraditions.filter(t=>t.cityId===cid);return claims.some(birth)?'birth':claims.some(t=>/conception/.test(t.locationType))?'conception':claims.some(t=>t.locationType==='city-birth-inference')?'inferred':'cult';}
function el(tag,attrs={},text){const n=document.createElementNS(NS,tag);for(const [k,v] of Object.entries(attrs))n.setAttribute(k,v);if(text!==undefined)n.textContent=text;return n;}
function merc(lat){return Math.log(Math.tan(Math.PI/4+lat*Math.PI/360));}
function project(coordinates){const [lon,lat]=coordinates,p=layout.projection;return [p.x0+p.scale*(lon-p.lon0)*Math.PI/180,p.y0+p.scale*(merc(p.lat0)-merc(lat))];}
function cite(c){return `<p class="meta"><a href="${safeLink(c.url)}" target="_blank" rel="noopener">${esc(c.work)}</a>, ${esc(c.passage)}<br>${esc(c.period)}</p>`;}
function matches(g){const q=fold($('search').value.trim()),type=$('evidence').value,cid=$('city').value;
 if(q&&!fold(JSON.stringify(g)+' '+g.cityIds.map(cityName).join(' ')).includes(q))return false;
 if(cid!=='all'&&!g.cityIds.includes(cid))return false;
 if(state.scope==='mapped'&&!locatedIds(g).length)return false;
 if(state.scope==='unlocated'&&locatedIds(g).length)return false;
 if(type==='origins'&&!g.originTraditions.length)return false;
 if(type==='birth'&&!g.originTraditions.some(birth))return false;
 if(type==='cosmic'&&!g.originTraditions.some(t=>!t.cityId))return false;
 if(type==='seats'&&!g.cityEvidence.length)return false;return true;
}
function listRow(g){const ids=locatedIds(g);const places=ids.length?ids.map(cityName).join(' · '):g.cityIds.length?g.cityIds.map(cityName).join(' · ')+' · unlocated':'Cosmic or unlocated origin';return `<button class="deity-row" data-deity="${esc(g.id)}"><span><strong>${esc(g.name)}</strong><small>${esc(places)}</small></span><span class="row-arrow" aria-hidden="true">↗</span></button>`;}
function renderBrowse(){state.selected=null;$('detail').hidden=true;$('browseView').hidden=false;
 const list=research.deities.filter(matches).sort((a,b)=>a.name.localeCompare(b.name));
 $('resultCount').textContent=`${list.length} ${list.length===1?'deity':'deities'}${state.city?' associated with '+cityName(state.city):' in this view'}`;
 $('cityIntro').innerHTML=state.city?`<div class="city-intro"><button class="text-button" id="clearCity">← All cities</button><h3>${esc(cityName(state.city))}</h3><p>Local associations and their sources. Birth and cult claims remain separate.</p></div>`:'';
 $('clearCity')?.addEventListener('click',clearFilters);
 $('results').innerHTML=list.length?list.map(listRow).join(''):'<p class="empty-state">No matching records. Try a different name or clear the filters.</p><button id="clearFilters" class="text-button">Clear filters</button>';
 $('clearFilters')?.addEventListener('click',clearFilters);
 renderPlaces(new Set(list.map(g=>g.id)));$('panelScroll').scrollTop=0;
}
function clearFilters(){state.city=null;state.scope='all';$('search').value='';$('evidence').value='all';$('city').value='all';setScopeTabs();history.replaceState(null,'',location.pathname+location.search);closePopover();renderBrowse();}
function setScopeTabs(){document.querySelectorAll('[data-scope]').forEach(b=>b.setAttribute('aria-pressed',String(b.dataset.scope===state.scope)));}
function refreshBrowse(){closePopover();history.replaceState(null,'',state.city&&cityGroups.has(state.city)?'#city='+encodeURIComponent(state.city):location.pathname+location.search);renderBrowse();}
function showDeity(id,{focus=true,mobile=true}={}){const g=research.deities.find(g=>g.id===id);if(!g)return;
 state.selected=id;closePopover();$('browseView').hidden=true;$('detail').hidden=false;
 const ids=locatedIds(g);
 const origin=g.originTraditions.map(t=>`<section class="claim"><div class="claim-type">${esc(claimNames[t.locationType]||t.locationType.replaceAll('-',' '))}${t.cityId?' · '+esc(cityName(t.cityId)):''}</div><p>${esc(t.summary)}</p>${!t.cityId||!cities.get(t.cityId)?.coordinates?'<p class="meta">No precise origin coordinate assigned.</p>':'<p class="meta">City anchor only; the exact event location is unknown.</p>'}${cite(t)}</section>`).join('');
 $('detail').innerHTML=`<button class="back-button" id="backToList">← ${state.city?'Back to '+esc(cityName(state.city)):'All deities'}</button><h2 tabindex="-1" id="deityTitle">${esc(g.name)}</h2><p class="domain">${esc(g.domains.join(' · '))}</p>${g.aliases.length?`<p class="aliases">Other names and spellings: ${esc(g.aliases.join(', '))}</p>`:''}${ids.length?`<div class="location-links" aria-label="Show associated cities on the map">${ids.map(cid=>`<button data-focus-city="${esc(cid)}">${esc(cityName(cid))} ↗</button>`).join('')}</div>`:'<p class="unlocated-note">No reliable coordinate for this record. Its cosmic or unlocated traditions are kept here without a map pin.</p>'}<h3>Birth, creation &amp; divine origins</h3>${origin||'<p>No birth or creation tradition established in the sources checked. The cult associations below do not establish a birthplace.</p>'}<h3>Cult seats &amp; patronage</h3>${g.cityEvidence.map(c=>`<section class="claim"><div class="claim-type">${esc(cityName(c.cityId))} · Cult association</div><p>${esc(c.summary)}</p>${cite(c)}</section>`).join('')||'<p>No securely located cult-city claim included in this catalogue.</p>'}<div class="identity-notes"><h3>Names &amp; interpretation</h3><p>${esc(g.nameNote)}</p>${g.notes.map(n=>`<p>${esc(n)}</p>`).join('')}</div><h3>Geographic anchors</h3>${g.cityIds.map(cid=>{const c=cities.get(cid);return `<p class="meta"><strong>${esc(cityName(cid))}</strong>: ${c?.coordinates?`${c.coordinates[1].toFixed(5)}° N, ${c.coordinates[0].toFixed(5)}° E. <a href="${safeLink(c.coordinateSource)}" target="_blank" rel="noopener">Pleiades site point</a>.`:esc(c?.note||'No reliable coordinate assigned.')}</p>`;}).join('')}`;
 $('backToList').onclick=()=>{history.replaceState(null,'',state.city?'#city='+encodeURIComponent(state.city):location.pathname+location.search);renderBrowse();};
 $('detail').querySelectorAll('[data-focus-city]').forEach(b=>b.onclick=()=>{focusCities([b.dataset.focusCity]);if(matchMedia('(max-width:980px)').matches)$('liveMap').scrollIntoView({block:'center',behavior:'auto'});});
 renderPlaces(new Set([id]));if(focus&&ids.length)focusCities(ids);else if(focus)setView(initialView);
 $('mapStatus').textContent=`${g.name} selected. ${ids.length?ids.map(cityName).join(', '):'No located map association.'}`;
 $('panelScroll').scrollTop=0;
 if(mobile&&matchMedia('(max-width:980px)').matches)$('browse').scrollIntoView({block:'start',behavior:'auto'});
}
function route(){const hash=location.hash.slice(1);if(hash.startsWith('deity='))showDeity(decodeURIComponent(hash.slice(6)));else if(hash.startsWith('city='))showCity(decodeURIComponent(hash.slice(5)));else if(hash==='composition')location.replace('poster.html#composition');else if(hash==='research'||hash==='browse'){$('browse').scrollIntoView({block:'start'});$('search').focus({preventScroll:true});}else if(research)renderBrowse();}
function chooseDeity(id){const g=research.deities.find(g=>g.id===id);if(state.city&&!g?.cityIds.includes(state.city)){state.city=null;$('city').value='all';}const hash='#deity='+encodeURIComponent(id);if(location.hash===hash)showDeity(id);else location.hash=hash;}
function showCity(cid){if(!cityGroups.has(cid))return;state.city=cid;state.scope='all';$('search').value='';$('evidence').value='all';$('city').value=cid;setScopeTabs();renderBrowse();focusCities([cid]);openPopover(cid);$('mapStatus').textContent=`${cityName(cid)} selected. ${cityGroups.get(cid).length} deity records.`;}
function chooseCity(cid){const hash='#city='+encodeURIComponent(cid);if(location.hash===hash)showCity(cid);else location.hash=hash;}
function marker(group,p,kind,cid){const count=cityGroups.get(cid).length,link=el('a',{href:'#city='+cid,'data-city':cid,class:'city-hotspot','aria-label':`${cityName(cid)}: explore ${count} ${deityWord(count)}`});
 link.append(el('circle',{cx:p[0],cy:p[1],r:40,class:'pin-halo'}));
 if(kind==='conception')link.append(el('path',{d:`M${p[0]},${p[1]-17}l17,17 -17,17 -17,-17Z`,fill:'#496c75',stroke:'#f5f0e4','stroke-width':3}));
 else{link.append(el('circle',{cx:p[0],cy:p[1],r:kind==='cult'?12:17,fill:kind==='birth'?'#e7b84e':'#f5f0e4',stroke:kind==='inferred'?'#a0523b':'#263d33','stroke-width':kind==='cult'?0:2.5}));if(kind!=='birth')link.append(el('circle',{cx:p[0],cy:p[1],r:kind==='cult'?7:5,fill:kind==='inferred'?'#a0523b':'#263d33'}));}
 group.append(link);
}
function renderPlaces(visible){if(!places)return;places.replaceChildren();
 for(const [cid,gs] of cityGroups){
  const config={...(layout.labels.find(l=>l.cityId===cid)||{x:190,y:1050,leader:{end:[820,1150],control:[1020,1320]}})};
  if(cid==='umma')config.y=2450;
  if(cid==='girsu')config.y+=50;
  if(compact()){const limit=cid==='girsu'||cid==='lagash'?950:cid==='nippur'||cid==='eridu'||cid==='uruk'?850:680;config.x=Math.max(850,Math.min(3150-limit,config.x));if(cid==='dilbat')config.y=2370;if(cid==='umma'){config.x=1550;config.y=2480;}if(cid==='isin')config.y=2730;if(cid==='marad'){config.x=800;config.y=2950;}if(cid==='zabalam')config.y=2820;if(cid==='lagash')config.y=3620;}
  const p=project(cities.get(cid).coordinates),active=state.selected?gs.some(g=>g.id===state.selected):state.city===cid;
  const matches=gs.filter(g=>visible.has(g.id));const group=el('g',{class:'map-place'+(active?' is-active':'')+(!matches.length?' is-muted':''),'data-place':cid});
  const leader=el('path',{class:'leader'});group.append(leader);
  const selectedGod=gs.find(g=>g.id===state.selected),kinds=(matches.length?matches:gs).map(g=>claimKind(g,cid)),kind=selectedGod?claimKind(selectedGod,cid):kinds.includes('birth')?'birth':kinds.includes('conception')?'conception':kinds.includes('inferred')?'inferred':'cult';marker(group,p,kind,cid);
  const cityLink=el('a',{href:'#city='+cid,'data-city':cid,'aria-label':`${cityName(cid)}: all ${gs.length} associated ${deityWord(gs.length)}`});cityLink.append(el('text',{x:config.x,y:config.y+38,class:'map-city-name'},cityName(cid)));group.append(cityLink);
  const preferred=config.deityIds||[];const ordered=[...gs].sort((u,v)=>{const priority=g=>(claimKind(g,cid)!=='cult'?-100:0)+(preferred.includes(g.id)?preferred.indexOf(g.id):50);return priority(u)-priority(v);});
  const nameLimit=cid==='umma'?1:2;
  let names=(matches.length?ordered.filter(g=>visible.has(g.id)):ordered).slice(0,nameLimit);let x=config.x,y=config.y+119;
  const maxWidth=cid==='girsu'||cid==='lagash'?950:cid==='nippur'||cid==='eridu'||cid==='uruk'?850:680;
  for(const g of names){const name=g.name.replace(' of Dilbat','');const w=measure.measureText(name).width;
   if(x>config.x&&x+w>config.x+maxWidth){x=config.x;y+=82;}
   const link=el('a',{href:'#deity='+g.id,'data-deity':g.id,'aria-label':`${g.name} — ${cityName(cid)}`,class:state.selected===g.id?'is-selected':''});
   link.append(el('text',{x,y,class:'map-deity-name claim-'+claimKind(g,cid)},name));group.append(link);x+=w+34;
  }
  const remaining=(matches.length?matches.length:gs.length)-names.length;
  if(remaining>0){const more=el('a',{href:'#city='+cid,'data-city':cid,'aria-label':`${cityName(cid)}: ${remaining} more ${deityWord(remaining)}`});more.append(el('text',{x:config.x,y:y+62,class:'map-more'},`+ ${remaining} more`));group.append(more);}
  places.append(group);
  const boxes=[...group.querySelectorAll('text')].map(t=>t.getBBox());
  const rect=[Math.min(...boxes.map(b=>b.x))-12,Math.min(...boxes.map(b=>b.y))-12,Math.max(...boxes.map(b=>b.x+b.width))+12,Math.max(...boxes.map(b=>b.y+b.height))+12];
  const end=[Math.max(rect[0],Math.min(rect[2],p[0])),Math.max(rect[1],Math.min(rect[3],p[1]))];
  const old=config.leader,control=[old.control[0]+(end[0]-old.end[0])*.5,old.control[1]+(end[1]-old.end[1])*.5];
  leader.setAttribute('d',`M${p.join(',')}Q${control.join(',')} ${end.join(',')}`);
 }
}
function setView(next){if(!svg)return;const w=Math.max(initialView[2]/5,Math.min(initialView[2],next[2])),h=w*initialView[3]/initialView[2];
 const center=[next[0]+next[2]/2,next[1]+next[3]/2];const margin=80;
 view=[Math.max(initialView[0]-margin,Math.min(initialView[0]+initialView[2]-w+margin,center[0]-w/2)),Math.max(initialView[1]-margin,Math.min(initialView[1]+initialView[3]-h+margin,center[1]-h/2)),w,h];
 svg.setAttribute('viewBox',view.join(' '));$('zoomIn').disabled=w<=initialView[2]/5+1;$('zoomOut').disabled=w>=initialView[2]-1;positionPopover();
}
function zoom(factor,at){const point=at||[view[0]+view[2]/2,view[1]+view[3]/2],w=Math.max(initialView[2]/5,Math.min(initialView[2],view[2]*factor)),scale=w/view[2];setView([point[0]-(point[0]-view[0])*scale,point[1]-(point[1]-view[1])*scale,w,view[3]*scale]);}
function focusCities(ids){const bounds=ids.map(id=>{const p=project(cities.get(id).coordinates),boxes=[...places.querySelectorAll(`[data-place="${id}"] text`)].map(t=>t.getBBox());return [Math.min(p[0],...boxes.map(b=>b.x))-170,Math.min(p[1],...boxes.map(b=>b.y))-190,Math.max(p[0],...boxes.map(b=>b.x+b.width))+170,Math.max(p[1],...boxes.map(b=>b.y+b.height))+190];});if(!bounds.length)return;
 const x=Math.min(...bounds.map(b=>b[0])),y=Math.min(...bounds.map(b=>b[1])),right=Math.max(...bounds.map(b=>b[2])),bottom=Math.max(...bounds.map(b=>b[3]));
 const w=Math.min(initialView[2],Math.max(1800,right-x,(bottom-y)*initialView[2]/initialView[3]));setView([(x+right)/2-w/2,(y+bottom)/2-w*initialView[3]/initialView[2]/2,w,w*initialView[3]/initialView[2]]);
}
function mapPoint(e){return new DOMPoint(e.clientX,e.clientY).matrixTransform(svg.getScreenCTM().inverse());}
function initGestures(){const pointers=new Map();let gesture;
 function begin(){const p=[...pointers.values()];gesture={view:[...view],points:p.map(p=>({...p}))};}
 svg.addEventListener('pointerdown',e=>{if(e.target.closest('a'))return;closePopover();pointers.set(e.pointerId,{x:e.clientX,y:e.clientY});svg.setPointerCapture(e.pointerId);svg.classList.add('is-dragging');begin();});
 svg.addEventListener('pointermove',e=>{if(!pointers.has(e.pointerId))return;pointers.set(e.pointerId,{x:e.clientX,y:e.clientY});const ps=[...pointers.values()];
  if(ps.length===2&&gesture.points.length===2){const dist=p=>Math.hypot(p[1].x-p[0].x,p[1].y-p[0].y);const factor=dist(gesture.points)/Math.max(1,dist(ps));const before={clientX:(gesture.points[0].x+gesture.points[1].x)/2,clientY:(gesture.points[0].y+gesture.points[1].y)/2};setView(gesture.view);const anchor=mapPoint(before);zoom(factor,[anchor.x,anchor.y]);}
  else if(ps.length===1){const matrix=svg.getScreenCTM(),start=gesture.points[0];const dx=(ps[0].x-start.x)/matrix.a,dy=(ps[0].y-start.y)/matrix.d;setView([gesture.view[0]-dx,gesture.view[1]-dy,gesture.view[2],gesture.view[3]]);}
 });
 const end=e=>{pointers.delete(e.pointerId);if(pointers.size)begin();else{gesture=null;svg.classList.remove('is-dragging');}};svg.addEventListener('pointerup',end);svg.addEventListener('pointercancel',end);
 svg.addEventListener('wheel',e=>{e.preventDefault();closePopover();const p=mapPoint(e);zoom(Math.exp(Math.max(-500,Math.min(500,e.deltaY))*.0015),[p.x,p.y]);},{passive:false});
 svg.addEventListener('keydown',e=>{if(e.target.closest('a'))return;const step=view[2]*.08;if(['ArrowLeft','ArrowRight','ArrowUp','ArrowDown'].includes(e.key)){e.preventDefault();setView([view[0]+(e.key==='ArrowRight'?step:e.key==='ArrowLeft'?-step:0),view[1]+(e.key==='ArrowDown'?step:e.key==='ArrowUp'?-step:0),view[2],view[3]]);}else if(e.key==='+'||e.key==='='){e.preventDefault();zoom(.75);}else if(e.key==='-'){e.preventDefault();zoom(1.333);}else if(e.key==='Home'){e.preventDefault();setView(initialView);}});
}
function closePopover(){const p=$('cityPopover');if(p){p.hidden=true;delete p.dataset.city;}}
function openPopover(cid){let p=$('cityPopover');if(!p){p=document.createElement('div');p.id='cityPopover';p.className='city-popover';$('liveMap').after(p);}p.dataset.city=cid;p.hidden=false;p.innerHTML=`<div><h3>${esc(cityName(cid))}</h3><button id="closePopover" aria-label="Close city popup">×</button></div><p>Select a deity to read its traditions.</p><div class="popover-names">${cityGroups.get(cid).map(g=>`<button data-deity="${esc(g.id)}">${esc(g.name)}</button>`).join('')}</div>`;$('closePopover').onclick=closePopover;positionPopover();}
function positionPopover(){const pop=$('cityPopover');if(!pop||pop.hidden||!svg)return;const p=project(cities.get(pop.dataset.city).coordinates),screen=new DOMPoint(...p).matrixTransform(svg.getScreenCTM()),frame=$('liveMap').getBoundingClientRect();pop.style.left=Math.max(16,Math.min(frame.width-286,screen.x-frame.x+22))+'px';pop.style.top=Math.max(58,Math.min(frame.height-300,screen.y-frame.y-40))+'px';}
function configureView(preserve=false){const old=view,oldHome=initialView;const [x1,y1,x2,y2]=layout.mapFrame,frame=$('liveMap').getBoundingClientRect(),aspect=frame.width/frame.height;
 const bw=x2-x1+110,bh=y2-y1+390,w=compact()?2400:Math.max(bw,bh*aspect),h=w/aspect,cx=(x1+x2)/2,cy=(y1+y2)/2-90;
 initialView=[cx-w/2,cy-h/2,w,h];
 if(preserve&&old&&oldHome&&old[2]<oldHome[2]*.98){const nextW=w*old[2]/oldHome[2],nextH=nextW/aspect;setView([old[0]+old[2]/2-nextW/2,old[1]+old[3]/2-nextH/2,nextW,nextH]);}else setView(initialView);
}
async function initMap(source){const parsed=new DOMParser().parseFromString(source,'image/svg+xml').documentElement;
 svg=el('svg',{id:'atlasSvg',xmlns:NS,role:'group','aria-label':'Map of Mesopotamian gods and city associations',tabindex:'0'});svg.append(parsed.querySelector('defs').cloneNode(true));
 svg.append(el('rect',{x:-1000,y:0,width:6500,height:6000,fill:'#f5f0e4'}));svg.append(parsed.querySelector('#geography').cloneNode(true));
 const geo=el('g',{'aria-hidden':'true'});
 for(const item of layout.geographicLabels){let {x,y}=item;if(compact()){if(item.text==='Persian Gulf')x=2680;else if(item.text.includes('suggested ancient')||item.text.includes('years ago'))x=2480;else if(item.text.includes('Mountains'))x=2600;else if(item.text.includes('Desert')){x=850;y=3740;}}const land=/Desert|Mountains|marshes/.test(item.text);geo.append(el('text',{x,y:y+item.size,class:'geo-name'+(land?' land':''),'font-size':item.size},item.text));}
 geo.append(el('text',{x:3670,y:1200,class:'map-caption'},'N ↑'));
 const length=layout.projection.scale*50000/(6371008.8*Math.cos(32*Math.PI/180)),scaleX=compact()?850:240;geo.append(el('path',{d:`M${scaleX},4200h${length}m0,-8v16M${scaleX},4192v16`,stroke:'#a3ae96','stroke-width':2,fill:'none'}));geo.append(el('text',{x:scaleX,y:4250,class:'map-caption'},'0'));geo.append(el('text',{x:scaleX+length-75,y:4250,class:'map-caption'},'50 km'));
 svg.append(geo);places=el('g',{id:'places'});svg.append(places);$('liveMap').replaceChildren(svg);$('liveMap').removeAttribute('role');$('liveMap').setAttribute('aria-label','Interactive map');
 configureView();initGestures();
 if(compact())$('mapHint').textContent='Tap a city or deity. Pinch or use + / − to explore.';
 svg.addEventListener('click',e=>{const a=e.target.closest('a');if(!a)return;e.preventDefault();if(a.dataset.deity)chooseDeity(a.dataset.deity);else if(a.dataset.city)chooseCity(a.dataset.city);});
 $('zoomIn').onclick=()=>zoom(.75);$('zoomOut').onclick=()=>zoom(1.3333);$('resetView').onclick=()=>{closePopover();setView(initialView);};
}
async function init(){try{
 const fetchJSON=async name=>{const r=await fetch(name);if(!r.ok)throw Error(name);return r.json();};
 const [r,c,l,source]=await Promise.all([fetchJSON('data/research.json'),fetchJSON('data/cities.json'),fetchJSON('data/poster-layout.json'),fetch('mesopotamian-gods.svg').then(r=>{if(!r.ok)throw Error('Map');return r.text();})]);research=r;cities=new Map(c.map(c=>[c.id,c]));layout=l;
 await Promise.all([document.fonts.load('700 84px Gentium'),document.fonts.load('700 60px SourceSans')]);measure=document.createElement('canvas').getContext('2d');measure.font='700 84px Gentium';
 cityGroups=new Map(c.filter(c=>c.coordinates&&r.deities.some(g=>g.cityIds.includes(c.id))).map(c=>[c.id,r.deities.filter(g=>g.cityIds.includes(c.id))]));
 const count=r.deities.filter(g=>locatedIds(g).length).length;$('allCount').textContent=r.deities.length;$('mappedCount').textContent=count;$('unlocatedCount').textContent=r.deities.length-count;$('rosterCount').textContent=`${cityGroups.size} cities`;$('totals').textContent=`${r.deities.length} deity records · ${r.deities.reduce((n,g)=>n+g.originTraditions.length,0)} origin claims.`;
 c.filter(c=>r.deities.some(g=>g.cityIds.includes(c.id))).sort((a,b)=>a.name.localeCompare(b.name)).forEach(c=>$('city').add(new Option(c.name+(c.coordinates?'':' · unlocated'),c.id)));
 await initMap(source);renderBrowse();
 $('search').oninput=refreshBrowse;$('evidence').onchange=refreshBrowse;$('city').onchange=()=>{state.city=$('city').value==='all'?null:$('city').value;refreshBrowse();if(state.city&&cityGroups.has(state.city))focusCities([state.city]);};
 document.querySelectorAll('[data-scope]').forEach(b=>b.onclick=()=>{state.scope=b.dataset.scope;state.city=null;$('city').value='all';setScopeTabs();refreshBrowse();});
 document.addEventListener('click',e=>{const b=e.target.closest('button[data-deity]');if(b)chooseDeity(b.dataset.deity);});
 $('helpToggle').onclick=()=>{const open=$('mapHelp').hidden;$('mapHelp').hidden=!open;$('helpToggle').setAttribute('aria-expanded',String(open));};
 $('browseLink').onclick=e=>{e.preventDefault();$('browse').scrollIntoView({block:'start',behavior:'auto'});$('search').focus({preventScroll:true});};
 document.addEventListener('keydown',e=>{if(e.key==='Escape'){closePopover();$('mapHelp').hidden=true;$('helpToggle').setAttribute('aria-expanded','false');}});
 addEventListener('hashchange',route);let resizing;addEventListener('resize',()=>{clearTimeout(resizing);resizing=setTimeout(()=>{configureView(true);renderPlaces(new Set(state.selected?[state.selected]:research.deities.filter(matches).map(g=>g.id)));positionPopover();},120);});if(location.hash)route();
 }catch(error){$('liveMap').innerHTML='<p class="loading">The interactive map could not load. <a href="poster.html">Open the poster</a>.</p>';$('resultCount').textContent='The catalogue could not load. Research JSON remains available on the sources page.';console.error(error);}}
init();
