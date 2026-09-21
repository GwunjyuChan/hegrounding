/* global L, lucide */
"use strict";
const $ = (id) => document.getElementById(id);
const statuses = {pending:"待标注", accepted:"已通过", ambiguous:"有歧义", unlocatable:"无法定位", rejected:"已剔除"};
const features = {bridge:"桥梁",ford:"浅滩渡口",river_bank:"河岸",river:"河流",road:"道路",junction:"路口",woodland:"林地",high_ground:"高地",open_ground:"开阔地",settlement:"聚落",building:"建筑",other:"其他"};
const state = {catalog:null, battle:null, current:null, mode:"point", points:[], undo:[], redo:[], dirty:false, busy:false, pan:false, source:false};
let europe, historic, overlay, drawing, imageBounds, toastTimer;
const iconify = () => lucide.createIcons();
function node(tag, cls, text) { const n=document.createElement(tag); if(cls)n.className=cls; if(text!==undefined)n.textContent=text; return n; }
function notify(message) { $("toast").textContent=message; $("toast").hidden=false; clearTimeout(toastTimer); toastTimer=setTimeout(()=>$("toast").hidden=true,4500); }
async function api(url, options={}) {
  const response=await fetch(url,options);
  const body=await response.json();
  if(!response.ok) throw new Error(body.error || `HTTP ${response.status}`);
  return body;
}
function setDirty(value=true) {state.dirty=value; $("save-indicator").textContent=value?"未保存":"已载入"; $("save-indicator").classList.toggle("dirty",value);}
async function leaveAllowed() {
  if(state.busy) return false;
  if(!state.dirty) return true;
  const dialog=$("discard-dialog");
  if(dialog.open) return false;
  return new Promise(resolve=>{
    const cleanup=(result)=>{dialog.close();$("stay").onclick=null;$("discard").onclick=null;dialog.oncancel=null;resolve(result);};
    $("stay").onclick=()=>cleanup(false); $("discard").onclick=()=>cleanup(true);
    dialog.oncancel=(event)=>{event.preventDefault();cleanup(false);}; dialog.showModal();
  });
}
function updateCatalog() {
  const all=state.catalog.battles;
  const total=all.reduce((s,b)=>s+b.total,0), reviewed=all.reduce((s,b)=>s+b.reviewed,0);
  $("global-progress").textContent=`${reviewed} / ${total} 已审核`;
  $("total-events").textContent=total;
  $("battle-list").replaceChildren();
  for(const battle of all) {
    const button=node("button","battle-row"); button.dataset.battle=battle.id;
    const country=node("div","battle-country");const dot=node("b");dot.style.background=battle.color;
    country.append(dot,document.createTextNode(battle.country));
    button.append(country,node("div","battle-name",battle.name),node("div","battle-date",battle.date));
    const progress=node("div","battle-progress");progress.append(node("span","",`${battle.reviewed} / ${battle.total} 已审核`),node("span","",`${battle.accepted} 已通过`));
    const track=node("div","progress-track"),fill=node("div","progress-fill");fill.style.width=`${battle.total?battle.reviewed/battle.total*100:0}%`;track.append(fill);
    button.append(progress,track);button.onclick=()=>openBattle(battle.id);$("battle-list").append(button);
  }
}
async function refreshCatalog() {state.catalog=await api("/api/catalog");updateCatalog();if(state.battle){state.battle=state.catalog.battles.find(b=>b.id===state.battle.id);renderEvents();}}
function resetEurope() {europe.fitBounds([[36,-12],[60,31]],{padding:[30,35]});}
function addPlace(battles) {
  const battle=battles[0],grouped=battles.length>1;
  const marker=L.marker([battle.lat,battle.lng],{icon:L.divIcon({className:"battle-marker",html:`<span class="pin-wrap" style="--pin:${battle.color}"><span class="pin-dot"></span></span>`,iconSize:[22,22],iconAnchor:[11,11]}),keyboard:true,title:grouped?"Wkra 河战区":battle.name}).addTo(europe);
  const label=node("div");label.append(document.createTextNode(grouped?"Wkra 河战区":battle.label),node("small","",`${grouped?"1806":battle.date.slice(0,4)} · ${battles.reduce((s,b)=>s+b.total,0)} 个事件`));
  const direction=grouped?"top":battle.id==="zurich_second_1799"?"right":"left";
  marker.bindTooltip(label,{permanent:true,direction,offset:grouped?[0,-14]:direction==="right"?[12,0]:[-12,0],className:"pin-label",interactive:true});
  const enter=()=>{
    if(!grouped){openBattle(battle.id);return;}
    const popup=node("div");
    for(const b of battles){const btn=node("button","popup-battle",b.name);btn.append(node("small","",`${b.total} 个事件 · ${b.date}`));btn.onclick=()=>openBattle(b.id);popup.append(btn);}
    marker.bindPopup(popup).openPopup();
  };
  marker.on("click",enter);marker.getTooltip().getElement()?.addEventListener("click",enter);
}
async function initEurope() {
  europe=L.map("europe-map",{zoomControl:false,minZoom:3,maxZoom:10,attributionControl:true});
  L.control.zoom({position:"bottomright"}).addTo(europe);
  europe.attributionControl.setPrefix(false);
  europe.attributionControl.addAttribution('Natural Earth · <a href="https://www.naturalearthdata.com/" target="_blank" rel="noopener">公共领域边界</a>');
  resetEurope();
  const response=await fetch("/vendor/countries.geojson");if(!response.ok)throw new Error("欧洲底图读取失败");
  const geo=await response.json();
  L.geoJSON(geo,{style:f=>({color:"#b4c7c1",weight:.8,fillColor:["#f0f3ee","#e7eeea","#eef1ed","#e3ece6"][Math.abs((f.properties.ADMIN||"").charCodeAt(0)||0)%4],fillOpacity:1}),interactive:false}).addTo(europe);
  const labels=[[46.5,2.2,"FRANCE"],[51,10.2,"GERMANY"],[42.8,12.4,"ITALY"],[40.2,-3.5,"SPAIN"],[54,-2.5,"UNITED KINGDOM"],[52.1,24,"POLAND"],[48,15,"AUSTRIA"],[46.5,8,"SWITZERLAND"],[58,13,"SWEDEN"]];
  for(const [lat,lng,name] of labels)L.tooltip({permanent:true,direction:"center",className:"country-label"}).setLatLng([lat,lng]).setContent(name).addTo(europe);
  for(const b of state.catalog.battles.filter(b=>b.country!=="波兰")) addPlace([b]);
  addPlace(state.catalog.battles.filter(b=>b.country==="波兰"));
  new ResizeObserver(()=>{europe.invalidateSize();}).observe($("europe-map"));
}
function renderEvents() {
  $("event-list").replaceChildren();
  const search=$("event-search").value.trim().toLowerCase(),filter=$("event-filter").value;
  const events=state.battle.events.filter(e=>(filter==="all"||e.status===filter)&&(`${e.id} ${e.question}`.toLowerCase().includes(search)));
  for(const event of events){
    const button=node("button",`event-row${state.current?.record.event_id===event.id?" selected":""}`);button.dataset.event=event.id;
    const head=node("div","event-row-head");head.append(node("span","mono",event.id),node("span",`status-dot ${event.status}`,statuses[event.status]||event.status));
    button.append(head,node("div","event-row-question",event.question));button.onclick=()=>openEvent(event.id);$("event-list").append(button);
  }
  if(!events.length)$("event-list").append(node("p","empty-list","没有匹配的事件"));
}
async function openBattle(id) {
  if(!await leaveAllowed())return;
  const battle=state.catalog.battles.find(b=>b.id===id);
  const event=battle.events.find(e=>e.status==="pending")||battle.events[0];
  if(!event){notify("此战场没有事件");return;}
  await openEvent(event.id, true);
}
async function openEvent(id, approved=false) {
  if(!approved && !await leaveAllowed())return;
  state.busy=true;
  try {
    const data=await api(`/api/event/${encodeURIComponent(id)}`);
    state.current=data;state.battle=state.catalog.battles.find(b=>b.id===data.record.battle_id);
    $("overview").hidden=true;$("editor").hidden=false;
    $("header-location").textContent=state.battle.label;$("battle-title").textContent=state.battle.name;
    $("battle-meta").textContent=`${state.battle.date} · ${state.battle.total} 个事件`;
    $("event-id").textContent=id;$("question").textContent=data.record.target_question||"Locate the event.";
    const url=data.record.article_url||"";$("article-link").hidden=!/^https?:\/\//.test(url);if(!$("article-link").hidden)$("article-link").href=url;
    $("source-section").textContent=data.record.source_section||"";$("caution").textContent=data.record.annotation_caution||"";
    document.querySelector(".annotation-scroll").scrollTop=0;
    $("source-tab").disabled=!data.record.source_text;state.source=false;renderPassage();
    $("history").replaceChildren();
    if(!data.history.length)$("history").append(new Option("尚无记录",""));
    data.history.forEach((ann,i)=>$("history").append(new Option(`${i===0?"最新 · ":""}${new Date(ann.updated_at).toLocaleString()} · ${ann.annotator||"anonymous"}`,String(i))));
    loadAnnotation(data.annotation);
    const index=state.battle.events.findIndex(e=>e.id===id);$("event-position").textContent=`${index+1} / ${state.battle.total}`;
    $("previous").disabled=index===0;$("next").disabled=index===state.battle.total-1;
    renderEvents();initHistoric();
    if(overlay)overlay.remove();drawing.clearLayers();
    const [width,height]=data.dimensions;imageBounds=L.latLngBounds([[-height,0],[0,width]]);
    overlay=L.imageOverlay(`/maps/${encodeURIComponent(id)}`,imageBounds,{interactive:false,alt:`${state.battle.name} 历史地图`});
    overlay.on("error",()=>notify("历史地图加载失败，请重新打开此事件。"));overlay.addTo(historic);
    historic.invalidateSize();historic.fitBounds(imageBounds,{padding:[30,55]});
    $("image-size").textContent=`${width} × ${height} px`;
    $("tolerance").max=Math.max(width,height);renderDrawing();setDirty(false);$("form-error").textContent="";
  } catch(error) {notify(error.message);} finally {state.busy=false;}
}
function loadAnnotation(ann) {
  state.mode=ann?.geometry?.type||state.current.record.suggested_geometry||"point";
  state.points=structuredClone(ann?.geometry?.coordinates||(ann?.geo_gold_px?[ann.geo_gold_px]:[]));
  const [w,h]=state.current.dimensions;
  if(ann && (ann.img_w!==w||ann.img_h!==h)){state.points=[];notify("旧标注尺寸与当前地图不同，几何未加载，请重新核对。");}
  $("status").value=ann?.status||"accepted";$("feature").value=features[ann?.geo_feature_type]?ann.geo_feature_type:(state.current.record.suggested_feature_type||"other");
  $("tolerance").value=ann?.tolerance_px??0;$("evidence").value=ann?.evidence||"";
  state.undo=[];state.redo=[];state.pan=false;
}
function renderPassage() {
  $("text-tab").setAttribute("aria-selected",String(!state.source));$("source-tab").setAttribute("aria-selected",String(state.source));
  $("passage").textContent=state.source?state.current.record.source_text:state.current.record.event_text;
  $("text-kind").textContent=state.source?"法文原文 · 1839 · Thiers":state.current.record.translation_review?"英文译文 · 待人工核对":"英文转述 · 非原文引文";
  $("passage").scrollTop=0;
}
function initHistoric() {
  if(historic)return;
  historic=L.map("historic-map",{crs:L.CRS.Simple,minZoom:-5,maxZoom:4,zoomControl:false,attributionControl:false,doubleClickZoom:false});
  drawing=L.layerGroup().addTo(historic);L.control.zoom({position:"bottomright"}).addTo(historic);
  historic.on("click",event=>{
    if(state.busy||state.pan)return;
    const [w,h]=state.current.dimensions,x=Math.round(event.latlng.lng),y=Math.round(-event.latlng.lat);
    if(x<0||y<0||x>=w||y>=h)return;
    pushUndo();if(state.mode==="point")state.points=[[x,y]];else state.points.push([x,y]);
    setDirty();renderDrawing();
  });
  historic.on("contextmenu",()=>undo());
  historic.on("mousemove",event=>{$("cursor-position").textContent=`x ${Math.round(event.latlng.lng)} · y ${Math.round(-event.latlng.lat)}`;});
  new ResizeObserver(()=>historic.invalidateSize()).observe($("historic-map"));
}
function snapshot(){return {mode:state.mode,points:structuredClone(state.points)};}
function pushUndo(){state.undo.push(snapshot());state.redo=[];}
function undo(){if(state.busy||!state.undo.length)return;state.redo.push(snapshot());Object.assign(state,state.undo.pop());setDirty();renderDrawing();}
function redo(){if(state.busy||!state.redo.length)return;state.undo.push(snapshot());Object.assign(state,state.redo.pop());setDirty();renderDrawing();}
function renderDrawing() {
  if(!drawing)return;drawing.clearLayers();
  const points=state.points.map(([x,y])=>[-y,x]),style={color:"#c23d65",weight:2,fillOpacity:.16,interactive:false};
  if(points.length>1){(state.mode==="polygon"&&points.length>=3?L.polygon(points,style):L.polyline(points,style)).addTo(drawing);}
  for(const p of points)L.circleMarker(p,{radius:4,color:"#fff",weight:1.5,fillColor:"#c23d65",fillOpacity:1,interactive:false}).addTo(drawing);
  document.querySelectorAll("[data-mode]").forEach(b=>{const selected=b.dataset.mode===state.mode&&!state.pan;b.classList.toggle("active",selected);b.setAttribute("aria-pressed",String(selected));});
  $("pan").classList.toggle("active",state.pan);$("pan").setAttribute("aria-pressed",String(state.pan));
  if(state.pan)historic.dragging.enable();else historic.dragging.disable();
  $("historic-map").classList.toggle("drawing",!state.pan);
  $("point-count").textContent=`${state.points.length} 顶点`;
  $("undo").disabled=!state.undo.length;$("redo").disabled=!state.redo.length;$("clear").disabled=!state.points.length;
  $("tolerance").disabled=state.mode==="polygon";
}
async function save(goNext=false) {
  if(!state.current||state.busy)return;
  $("form-error").textContent="";
  const evidence=$("evidence").value.trim();if(!evidence){$("form-error").textContent="请填写证据或审核理由。";$("evidence").focus();return;}
  if(!$("annotator").value.trim()){notify("请填写标注者姓名");$("annotator").focus();return;}
  const body={base_revision:state.current.revision,status:$("status").value,evidence,annotator:$("annotator").value.trim(),geo_feature_type:$("feature").value,tolerance_px:Number($("tolerance").value),geometry:state.points.length?{type:state.mode,coordinates:state.points}:null};
  state.busy=true;$("save").disabled=true;$("save-next").disabled=true;
  for(const id of ["annotator","status","feature","tolerance","evidence","history"])$(id).disabled=true;
  let success=false;
  try {
    const id=state.current.record.event_id;
    // Refresh the token without discarding a draft after a server restart.
    state.catalog.csrf=(await api("/api/catalog")).csrf;
    state.current=await api(`/api/event/${encodeURIComponent(id)}`,{method:"POST",headers:{"Content-Type":"application/json","X-CSRF-Token":state.catalog.csrf},body:JSON.stringify(body)});
    setDirty(false);success=true;notify(`${id} 已保存`);
    await refreshCatalog();
    $("history").replaceChildren();state.current.history.forEach((ann,i)=>$("history").append(new Option(`${i===0?"最新 · ":""}${new Date(ann.updated_at).toLocaleString()} · ${ann.annotator}`,String(i))));
    $("save-indicator").textContent="已保存";
  } catch(error) {$("form-error").textContent=error.message;}
  finally {state.busy=false;$("save").disabled=false;$("save-next").disabled=false;for(const id of ["annotator","status","feature","tolerance","evidence","history"])$(id).disabled=false;$("tolerance").disabled=state.mode==="polygon";}
  if(success&&goNext){const i=state.battle.events.findIndex(e=>e.id===state.current.record.event_id);if(i+1<state.battle.events.length)await openEvent(state.battle.events[i+1].id);else notify("本战场已到最后一条");}
}
async function navigate(delta){if(!state.current)return;const i=state.battle.events.findIndex(e=>e.id===state.current.record.event_id);const target=state.battle.events[i+delta];if(target)await openEvent(target.id);}
async function goHome(){if(!await leaveAllowed())return;setDirty(false);$("editor").hidden=true;$("overview").hidden=false;$("header-location").textContent="欧洲战场";europe.invalidateSize();await refreshCatalog();}
async function boot() {
  iconify();
  try{$("annotator").value=localStorage.getItem("he-annotator")||"eric";}catch{}
  $("annotator").addEventListener("input",()=>{try{localStorage.setItem("he-annotator",$("annotator").value);}catch{}if(state.current&&!$("editor").hidden)setDirty();});
  for(const [code,label] of Object.entries(features))$("feature").append(new Option(`${label} · ${code}`,code));
  $("home").onclick=goHome;$("back").onclick=goHome;$("reset-europe").onclick=resetEurope;
  $("event-filter").onchange=renderEvents;$("event-search").oninput=renderEvents;
  $("previous").onclick=()=>navigate(-1);$("next").onclick=()=>navigate(1);
  $("save").onclick=()=>save();$("save-next").onclick=()=>save(true);
  $("undo").onclick=undo;$("redo").onclick=redo;
  $("clear").onclick=()=>{if(state.busy)return;pushUndo();state.points=[];setDirty();renderDrawing();};
  $("pan").onclick=()=>{state.pan=!state.pan;renderDrawing();};
  $("fit-image").onclick=()=>historic.fitBounds(imageBounds,{padding:[30,55]});
  document.querySelectorAll("[data-mode]").forEach(button=>button.onclick=()=>{if(state.busy)return;const mode=button.dataset.mode;if(mode!==state.mode){pushUndo();state.mode=mode;state.points=[];setDirty();}state.pan=false;renderDrawing();});
  $("text-tab").onclick=()=>{state.source=false;renderPassage();};$("source-tab").onclick=()=>{state.source=true;renderPassage();};
  for(const id of ["status","feature","tolerance","evidence"])$(id).addEventListener("input",()=>setDirty());
  $("history").onchange=async()=>{const i=Number($("history").value);if(!state.current.history[i])return;if(!await leaveAllowed()){$("history").value="0";return;}loadAnnotation(state.current.history[i]);renderDrawing();setDirty();notify("已载入所选版本，保存后将追加为新版本");};
  window.addEventListener("beforeunload",e=>{if(state.dirty){e.preventDefault();e.returnValue="";}});
  window.addEventListener("keydown",e=>{if($("editor").hidden||e.target.matches("input,textarea,select"))return;if((e.metaKey||e.ctrlKey)&&e.key.toLowerCase()==="z"){e.preventDefault();e.shiftKey?redo():undo();}});
  try {await refreshCatalog();await initEurope();}catch(error){notify(error.message);$("global-progress").textContent="加载失败，请刷新";}
}
boot();
