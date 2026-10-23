/* The overview routes every task into the same versioned annotation workspace. */
"use strict";
const $ = id => document.getElementById(id);
let catalog, atlas, europe, review = null;
function node(tag, cls, text) {
  const el=document.createElement(tag);if(cls)el.className=cls;
  if(text!==undefined)I18n.text(el,text);return el;
}
async function read(path) {
  const response=await fetch(workspaceURL(path));
  if(!response.ok)throw new Error('工作区加载失败');return response.json();
}
// The main workspace's battles open in the AI-candidate review site; its saved reviews drive the counts.
async function readReview() {
  const get=async path=>{const response=await fetch(path);if(!response.ok)throw new Error('审核数据加载失败');return response;};
  const [text,saved]=await Promise.all([get('/review/annotations.jsonl').then(r=>r.text()),get('/review/api/reviews/export').then(r=>r.json())]);
  const events=text.split('\n').filter(line=>line.trim()).map(line=>JSON.parse(line));
  const state=e=>{const r=saved.reviews[e.event_id];return !r?'pending':r.candidate_sha256!==saved.candidate_versions[e.event_id]?'stale':r.decision;};
  return {events:events.map(e=>({id:e.event_id,battle:e.source_record.battle_id,map:e.annotation_image.path,state:state(e)}))};
}
function reviewCounts(events) {
  return {total:events.length, reviewed:events.filter(e=>!['pending','stale'].includes(e.state)).length,
    accepted:events.filter(e=>['accepted','modified_accepted'].includes(e.state)).length};
}
function openBattle(id) {
  if(review) {
    const events=review.events.filter(e=>e.battle===id);if(!events.length)return;
    const next=events.find(e=>['pending','stale'].includes(e.state))||events[0];
    location.href='/review/review.html?battle='+encodeURIComponent(id)+'#'+encodeURIComponent(next.id);return;
  }
  const maps=atlas.maps.filter(m=>m.battle_id===id);
  if(!maps.length)return;
  const map=maps.find(m=>m.reviewed<m.total)||maps[0];
  location.href=workspaceURL('/atlas.html?map='+encodeURIComponent(map.id));
}
function resetEurope() {
  const points=catalog.battles.filter(b=>b.total>0).map(b=>[b.lat,b.lng]);
  europe.fitBounds([[36,-12],[60,31],...points],{padding:[30,35]});
}
function renderCatalog() {
  const workspace=catalog.workspace;
  for(const battle of catalog.battles) {
    if(review) {Object.assign(battle,reviewCounts(review.events.filter(e=>e.battle===battle.id)));continue;}
    const maps=atlas.maps.filter(m=>m.battle_id===battle.id);
    battle.reviewed=maps.reduce((n,m)=>n+m.reviewed,0);
    battle.accepted=maps.reduce((n,m)=>n+m.accepted,0);
  }
  const battles=catalog.battles.filter(b=>b.total>0);
  I18n.text($('workspace-name'),workspace.name);I18n.text(document.querySelector('title'),'HE · '+workspace.name);
  I18n.text($('overview-title'),workspace.kind==='main'?'战场地图':'实验地图');
  I18n.text($('item-label'),workspace.item_label);
  $('event-workspace-link').href=workspace.events_url;
  $('event-workspace-link').hidden=workspace.kind==='main';
  $('place-workspace-link').href=workspace.place_lab_url;
  const total=battles.reduce((n,b)=>n+b.total,0), reviewed=battles.reduce((n,b)=>n+b.reviewed,0);
  $('total-events').textContent=total;$('total-battles').textContent=review?new Set(review.events.map(e=>e.map)).size:atlas.maps.length;
  I18n.text($('global-progress'),reviewed+' / '+total+' 已审核');
  $('battle-list').replaceChildren(...battles.map(b=>{
    const button=node('button','battle-row');button.dataset.battle=b.id;
    const country=node('div','battle-country'),dot=node('b');dot.style.background=b.color;
    country.append(dot,node('span','',b.country));
    const progress=node('div','battle-progress');progress.append(node('span','',b.reviewed+' / '+b.total+' 已审核'),node('span','',b.accepted+' 已通过'));
    const track=node('div','progress-track'),fill=node('div','progress-fill');fill.style.width=(b.reviewed/b.total*100)+'%';track.append(fill);
    button.append(country,node('div','battle-name',b.name),node('div','battle-date',b.date),progress,track);
    button.onclick=()=>openBattle(b.id);return button;
  }));
  document.querySelector('.map-legend').replaceChildren(...Array.from(new Map(battles.map(b=>[b.country,b])).values()).map(b=>{
    const item=node('span'),dot=node('b');dot.style.background=b.color;item.append(dot,node('span','',b.country));return item;
  }));
}
async function initEurope() {
  europe=L.map('europe-map',{zoomControl:false,minZoom:3,maxZoom:10,attributionControl:true});
  L.control.zoom({position:'bottomright'}).addTo(europe);europe.attributionControl.setPrefix(false);
  I18n.mapControls(europe);
  europe.attributionControl.addAttribution('Natural Earth · <a href="https://www.naturalearthdata.com/" target="_blank" rel="noopener">公共领域边界</a>');
  I18n.text(document.querySelector('.leaflet-control-attribution a'),'公共领域边界');
  resetEurope();
  const geo=await read('/vendor/countries.geojson');
  L.geoJSON(geo,{style:f=>({color:'#b4c7c1',weight:.8,fillColor:['#f0f3ee','#e7eeea','#eef1ed','#e3ece6'][Math.abs((f.properties.ADMIN||'').charCodeAt(0)||0)%4],fillOpacity:1}),interactive:false}).addTo(europe);
  const countryLabels=[[46.5,2.2,'FRANCE'],[51,10.2,'GERMANY'],[42.8,12.4,'ITALY'],[40.2,-3.5,'SPAIN'],[54,-2.5,'UNITED KINGDOM'],[52.1,24,'POLAND'],[48,15,'AUSTRIA'],[46.5,8,'SWITZERLAND'],[58,13,'SWEDEN']];
  for(const [lat,lng,name] of countryLabels)L.tooltip({permanent:true,direction:'center',className:'country-label'}).setLatLng([lat,lng]).setContent(name).addTo(europe);
  const places=new Map();
  for(const b of catalog.battles.filter(b=>b.total>0)) {
    const key=b.lat+','+b.lng;if(!places.has(key))places.set(key,[]);places.get(key).push(b);
  }
  for(const battles of places.values()) {
    const b=battles[0],title=battles.map(x=>x.name).join(' / ');
    const pin=node('span','pin-wrap');pin.style.setProperty('--pin',b.color);pin.append(node('span','pin-dot'));
    const marker=L.marker([b.lat,b.lng],{icon:L.divIcon({className:'battle-marker',html:pin,iconSize:[22,22],iconAnchor:[11,11]}),keyboard:true,title}).addTo(europe);
    I18n.attr(marker.getElement(),()=>battles.map(x=>I18n.t(x.name)).join(' / '),'title');
    const tooltip=node('span');I18n.text(tooltip,()=>battles.map(x=>I18n.t(x.name)).join(' / '));marker.bindTooltip(tooltip);
    marker.on('click',()=>{
      if(battles.length===1){openBattle(b.id);return;}
      const popup=node('div');
      for(const item of battles){const btn=node('button','popup-battle',item.name);btn.onclick=()=>openBattle(item.id);popup.append(btn);}
      marker.bindPopup(popup).openPopup();
    });
  }
  new ResizeObserver(()=>europe.invalidateSize()).observe($('europe-map'));
}
async function boot() {
  lucide.createIcons();
  try {
    [catalog,atlas]=await Promise.all([read('/api/catalog'),read('/api/atlas')]);
    atlas.maps=atlas.maps.filter(m=>m.kind!=='place_lab');
    if(catalog.workspace.kind==='main')review=await readReview().catch(()=>null);
    renderCatalog();await initEurope();
    $('home').onclick=resetEurope;$('reset-europe').onclick=resetEurope;
  } catch(error) {I18n.text($('global-progress'),error.message);}
}
boot();
