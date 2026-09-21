/* Clean raster assets and editable overlays deliberately use separate paths. */
const $ = id => document.getElementById(id);
const labels = {pending:'待审核',accepted:'已通过',ambiguous:'有歧义',unlocatable:'无法定位',outside_map:'范围外',rejected:'剔除'};
const featureNames = {bridge:'桥梁',ford:'浅滩',river_bank:'河岸',river:'河流',road:'道路',junction:'交叉口',woodland:'林地',high_ground:'高地',open_ground:'开阔地',settlement:'聚落',building:'建筑',other:'其他'};
const battleNames = {zurich_second_1799:'第二次苏黎世战役',borkowo:'Borkowo',sochocin:'Sochocin',wavre:'Wavre'};
let catalog, detail, eventId, source, view='prepare', mode='hand', dirty=false, busy=false;
let geometryType='point', points=[], undo=[], redo=[], cropStart=null, cropHover=null;
const modelVisibility=new Map();
let refImage, workImage, refBounds, workBounds, dimensions=[0,0];
const reference = L.map('reference-canvas',{crs:L.CRS.Simple,minZoom:-6,maxZoom:5,zoomSnap:.25,zoomDelta:.5,attributionControl:false});
const working = L.map('working-canvas',{crs:L.CRS.Simple,minZoom:-6,maxZoom:5,zoomSnap:.25,zoomDelta:.5,attributionControl:false});
const overlays=L.layerGroup().addTo(working);
const asLatLng = p => [-p[1],p[0]];
const imageBounds = (w,h) => [[-h,0],[0,w]];
function icons(){lucide.createIcons();}
function error(e){$('atlas-error').textContent=e.message||String(e);}
function changed(){dirty=true;$('dirty').textContent='未保存修改';}
function clean(){dirty=false;$('dirty').textContent='';}
function toast(msg){$('toast').textContent=msg;$('toast').hidden=false;setTimeout(()=>$('toast').hidden=true,3500);}
function selected(){return detail?.events.find(e=>e.id===eventId);}
function selectedPrediction(){return selected()?.predictions?.[$('prediction-model').value];}
function renderPredictionControls(){
  const models=detail?.prediction_models||[];
  const prior=$('prediction-model').value;
  $('prediction-model').replaceChildren(...models.map(m=>{
    const prediction=selected()?.predictions?.[m.id];
    const status=!prediction?' · 无结果':!prediction.geometry?' · 拒答':'';
    return option(m.id,m.label+status);
  }));
  if(!models.length)$('prediction-model').append(option('','暂无模型预测'));
  if(models.some(m=>m.id===prior))$('prediction-model').value=prior;
  $('prediction-model').disabled=!models.length;
  $('prediction-toggle').replaceChildren(...models.map(m=>{
    if(!modelVisibility.has(m.id))modelVisibility.set(m.id,true);
    const prediction=selected()?.predictions?.[m.id];
    const label=document.createElement('label');label.title=m.id;
    const checkbox=document.createElement('input');checkbox.type='checkbox';checkbox.checked=modelVisibility.get(m.id);
    checkbox.setAttribute('aria-label',m.label+' 预测');
    checkbox.onchange=()=>{modelVisibility.set(m.id,checkbox.checked);redraw();};
    const swatch=document.createElement('span');swatch.className='model-swatch';swatch.style.backgroundColor=m.color;
    const name=document.createElement('span');name.textContent=m.label+(!prediction?' · 无结果':!prediction.geometry?' · 拒答':'');
    label.append(checkbox,swatch,name);return label;
  }));
}
async function request(url,body){
  const options=body===undefined?{}:{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)};
  return atlasJSON(url,options);
}
async function run(fn){
  if(busy)return;
  busy=true;$('atlas-error').textContent='';
  document.querySelector('.atlas-layout').inert=true;
  document.querySelectorAll('.atlas-inspector button').forEach(b=>b.disabled=true);
  try{await fn();}catch(e){error(e);}finally{busy=false;document.querySelector('.atlas-layout').inert=false;document.querySelectorAll('.atlas-inspector button').forEach(b=>b.disabled=false);availability();}
}
function confirmAction(message,title='尚有未保存的修改'){
  $('confirm-title').textContent=title;$('confirm-text').textContent=message;
  return new Promise(resolve=>{
    const dialog=$('atlas-confirm');
    $('confirm-ok').onclick=()=>{dialog.close();resolve(true);};
    $('confirm-cancel').onclick=()=>{dialog.close();resolve(false);};
    dialog.oncancel=()=>resolve(false);dialog.showModal();
  });
}
async function mayLeave(){return !dirty||await confirmAction('离开会丢弃当前未保存的裁切或事件标注。');}
function option(value,text){const el=document.createElement('option');el.value=value;el.textContent=text;return el;}
function row(title,subtitle,active,onclick){const b=document.createElement('button');b.className='atlas-item'+(active?' active':'');b.textContent=title;const s=document.createElement('small');s.textContent=subtitle;b.append(s);b.onclick=onclick;return b;}
function renderCatalog(){
  $('atlas-count').textContent=`${catalog.maps.length} 张参考地图`;
  const rows=catalog.maps.map(m=>row(
    battleNames[m.battle_id]||m.battle_id,
    `${m.total} 事件 · ${m.active?m.reviewed+' 已审核':'未设置底图'}`,
    m.id===detail?.id,
    ()=>run(async()=>{if(await mayLeave())await openMap(m.id);})
  ));
  $('atlas-list').replaceChildren(...rows);
  $('source-select').replaceChildren(option('','选择已导入图像'),...catalog.sources.map(s=>option(s.id,`${s.name}${s.page?' · 第 '+s.page+' 页':''}`)));
  $('source-select').value=source?.id||'';
  if(!$('atlas-feature').options.length)$('atlas-feature').replaceChildren(...catalog.feature_types.map(f=>option(f,featureNames[f]||f)));
}
function renderEvents(){
  const filter=$('scope-filter').value;
  $('atlas-events').replaceChildren(...detail.events.filter(e=>filter==='all'||(e.gold?.status||'pending')===filter).map(e=>row(
    `${e.id} · ${labels[e.gold?.status||'pending']}`,e.question,e.id===eventId,()=>run(async()=>{
      if(!(await mayLeave()))return;
      if(!detail.active)throw new Error('请先在编辑底图中保存一个底图版本。');
      eventId=e.id;view='annotate';loadEvent();showView();
    }))));
}
async function openMap(mid){
  detail=await request('/api/atlas/'+mid);eventId=detail.events[0]?.id;
  const ref=await request('/api/event/'+detail.reference_event);
  if(refImage)reference.removeLayer(refImage);
  refBounds=imageBounds(...ref.dimensions);
  refImage=L.imageOverlay('/maps/'+detail.reference_event,refBounds).addTo(reference);
  reference.fitBounds(refBounds);clean();source=catalog.sources.find(s=>s.id===detail.active?.source_id)||null;
  if(!detail.active)view='prepare';
  fillMapFields();loadEvent();renderCatalog();renderEvents();showView();
}
function fillMapFields(){
  const a=detail.active;
  if(a){source=catalog.sources.find(s=>s.id===a.source_id)||null;$('source-select').value=source?.id||'';}
  $('map-title').textContent=battleNames[detail.battle_id]||detail.battle_id;
  $('map-name').value=a?.title||`${battleNames[detail.battle_id]||detail.battle_id} · 标注底图`;
  $('provenance').value=a?.provenance||'';
  $('rotation').value=a?.rotation||0;$('max-side').value=a?.max_side||3200;
  setCrop(a?.crop||(source?[0,0,source.width,source.height]:[0,0,0,0]));
  $('map-history').replaceChildren(...detail.history.map((a,i)=>option(a.version,`${i===0?'当前 · ':''}${a.version.slice(0,8)} · ${a.width}×${a.height} · ${a.created_at.slice(0,16)}`)));
  $('clean-download').hidden=!a;
  if(a){$('clean-download').href='/atlas-assets/'+a.version;$('clean-download').download=`${detail.id}-${a.version}-clean.png`;}
}
function setCrop(values){['crop-x0','crop-y0','crop-x1','crop-y1'].forEach((id,i)=>$(id).value=values[i]);}
function getCrop(){return ['crop-x0','crop-y0','crop-x1','crop-y1'].map(id=>Number($(id).value));}
function availability(){
  $('save-map').disabled=busy||!source;
  $('save-gold').disabled=busy||!detail?.active||!selected();
  $('restore-map').disabled=busy||!detail?.history.length;
  ['export-input','export-gold','import-prediction'].forEach(id=>$(id).disabled=busy||!detail?.active);
  $('export-overlay').disabled=busy||!selected()?.gold?.geometry;
  $('export-prediction').disabled=busy||!selectedPrediction()?.geometry;
  const i=detail?.events.findIndex(e=>e.id===eventId)??-1;
  $('previous-event').disabled=i<=0;$('next-event').disabled=!detail||i>=detail.events.length-1;
}
function showView(){
  $('prepare-fields').hidden=view!=='prepare';$('annotate-fields').hidden=view!=='annotate';
  $('working-label').textContent=view==='prepare'?'裁切原图':'标注底图';
  $('crop-tool').hidden=view!=='prepare';
  document.querySelectorAll('[data-geometry]').forEach(b=>b.hidden=view!=='annotate');
  ['gold-toggle','prediction-toggle','undo-atlas','redo-atlas','clear-atlas'].forEach(id=>$(id).hidden=view!=='annotate');
  document.querySelectorAll('[data-view]').forEach(b=>b.setAttribute('aria-selected',b.dataset.view===view));
  setMode('hand');showWorking();availability();
}
function showWorking(){
  if(workImage)working.removeLayer(workImage);
  const a=view==='prepare'?source:detail.active;
  $('map-empty').hidden=!!a;dimensions=a?[a.width,a.height]:[0,0];
  $('working-dimensions').textContent=a?`${a.width} × ${a.height} px`:'';
  $('map-version').textContent=detail.active?`底图 ${detail.active.version.slice(0,8)}`:'无底图版本';
  if(a){workBounds=imageBounds(a.width,a.height);workImage=L.imageOverlay('/atlas-assets/'+(view==='prepare'?a.id:a.version),workBounds).addTo(working);working.fitBounds(workBounds,{padding:[12,50]});}
  redraw();requestAnimationFrame(()=>{working.invalidateSize();reference.invalidateSize();});
}
function setMode(value){
  mode=value;cropStart=null;cropHover=null;
  if(mode==='hand')working.dragging.enable();else working.dragging.disable();
  working.doubleClickZoom.disable();
  $('working-canvas').style.cursor=mode==='hand'?'grab':'crosshair';
  $('hand-tool').classList.toggle('active',mode==='hand');$('crop-tool').classList.toggle('active',mode==='crop');
  document.querySelectorAll('[data-geometry]').forEach(b=>b.classList.toggle('active',view==='annotate'&&geometryType===b.dataset.geometry&&mode==='draw'));
}
function drawGeometry(geometry,color,dashed=false,label=''){
  if(!geometry?.coordinates.length)return;
  const coords=geometry.coordinates.map(asLatLng),style={color,weight:3,fillOpacity:.12,interactive:!!label,dashArray:dashed?'6 5':null};
  let layer;
  if(geometry.type==='point')layer=L.circleMarker(coords[0],{...style,radius:7,fillOpacity:.7}).addTo(overlays);
  else if(geometry.type==='polygon'&&coords.length>=3)layer=L.polygon(coords,style).addTo(overlays);
  else layer=L.polyline(coords,style).addTo(overlays);
  if(label){const name=document.createElement('span');name.textContent=label;layer.bindTooltip(name,{direction:'auto',className:'model-map-label'});}
  if(!dashed)coords.forEach(p=>L.circleMarker(p,{radius:3,color,fillColor:'#fff',fillOpacity:1,weight:1,interactive:false}).addTo(overlays));
}
function redraw(){
  overlays.clearLayers();
  if(view==='prepare'&&source){
    let [x0,y0,x1,y1]=getCrop();
    if(cropStart&&cropHover){[x0,x1]=[cropStart[0],cropHover[0]].sort((a,b)=>a-b);[y0,y1]=[cropStart[1],cropHover[1]].sort((a,b)=>a-b);}
    if(x1>x0&&y1>y0)L.rectangle([[-y0,x0],[-y1,x1]],{color:'#167b6a',weight:2,fillOpacity:.05,interactive:false}).addTo(overlays);
  }
  if(view==='annotate'){
    if($('show-gold').checked)drawGeometry({type:geometryType,coordinates:points},'#cf3f49');
    for(const model of detail.prediction_models||[]){
      if(modelVisibility.get(model.id))drawGeometry(selected()?.predictions?.[model.id]?.geometry,model.color,true,model.label);
    }
  }
  $('undo-atlas').disabled=!undo.length;$('redo-atlas').disabled=!redo.length;
  $('atlas-tolerance').disabled=geometryType==='polygon';
}
function snapshot(){return {type:geometryType,points:structuredClone(points)};}
function remember(){undo.push(snapshot());redo=[];}
function loadEvent(){
  const e=selected();if(!e)return;
  const gold=e.gold;geometryType=gold?.geometry?.type||'point';points=structuredClone(gold?.geometry?.coordinates||[]);undo=[];redo=[];
  $('selected-event').textContent=e.id;$('target-question').textContent=e.question;$('event-passage').textContent=e.text;
  $('original-text').textContent=e.source_text||'无逐字原文';$('event-caution').textContent=e.caution;
  const safe=/^https?:\/\//i.test(e.article_url);$('source-link').hidden=!safe;if(safe)$('source-link').href=e.article_url;
  $('atlas-status').value=gold?.status||'accepted';$('atlas-feature').value=gold?.geo_feature_type||'other';
  $('atlas-evidence').value=gold?.evidence||'';$('atlas-tolerance').value=gold?.tolerance_px||0;
  if(gold)$('atlas-annotator').value=gold.annotator;
  clean();renderEvents();renderPredictionControls();redraw();availability();
}
function pixel(e,edge=false){const [w,h]=dimensions;return [Math.max(0,Math.min(w-(edge?0:1),Math.round(e.latlng.lng))),Math.max(0,Math.min(h-(edge?0:1),Math.round(-e.latlng.lat)))];}
working.on('mousedown',e=>{if(mode==='crop'&&source){cropStart=pixel(e,true);cropHover=cropStart;}});
working.on('mousemove',e=>{const p=pixel(e,mode==='crop');$('cursor').textContent=`x ${p[0]} · y ${p[1]}`;if(cropStart){cropHover=p;redraw();}});
working.on('mouseup',e=>{
  if(mode==='crop'&&cropStart){const end=pixel(e,true);const xs=[cropStart[0],end[0]].sort((a,b)=>a-b),ys=[cropStart[1],end[1]].sort((a,b)=>a-b);
    if(xs[1]-xs[0]>=32&&ys[1]-ys[0]>=32){setCrop([xs[0],ys[0],xs[1],ys[1]]);changed();}
    cropStart=null;cropHover=null;redraw();}
});
document.addEventListener('mouseup',()=>{if(cropStart){cropStart=null;cropHover=null;redraw();}});
working.on('click',e=>{if(mode!=='draw'||view!=='annotate'||!detail.active)return;if(e.latlng.lng<0||e.latlng.lng>=dimensions[0]||-e.latlng.lat<0||-e.latlng.lat>=dimensions[1])return;
  remember();if(geometryType==='point')points=[pixel(e)];else points.push(pixel(e));$('show-gold').checked=true;changed();redraw();});
$('hand-tool').onclick=()=>setMode('hand');$('crop-tool').onclick=()=>setMode('crop');
document.querySelectorAll('[data-geometry]').forEach(b=>b.onclick=()=>{if(geometryType!==b.dataset.geometry){remember();geometryType=b.dataset.geometry;points=[];changed();}setMode('draw');redraw();});
$('undo-atlas').onclick=()=>{if(undo.length){redo.push(snapshot());const s=undo.pop();geometryType=s.type;points=s.points;changed();setMode('draw');redraw();}};
$('redo-atlas').onclick=()=>{if(redo.length){undo.push(snapshot());const s=redo.pop();geometryType=s.type;points=s.points;changed();setMode('draw');redraw();}};
$('clear-atlas').onclick=()=>{remember();points=[];changed();redraw();};
$('fit-working').onclick=()=>workBounds&&working.fitBounds(workBounds,{padding:[12,50]});$('fit-reference').onclick=()=>refBounds&&reference.fitBounds(refBounds);
$('show-reference').onchange=()=>{$('reference-pane').hidden=!$('show-reference').checked;document.querySelector('.atlas-canvases').classList.toggle('no-reference',!$('show-reference').checked);working.invalidateSize();reference.invalidateSize();};
$('show-gold').onchange=redraw;$('prediction-model').onchange=availability;
$('scope-filter').onchange=renderEvents;
document.querySelectorAll('[data-view]').forEach(b=>b.onclick=()=>run(async()=>{if(b.dataset.view===view)return;if(!(await mayLeave()))return;if(b.dataset.view==='annotate'&&!detail.active)throw new Error('请先保存底图。');view=b.dataset.view;fillMapFields();loadEvent();showView();}));
['crop-x0','crop-y0','crop-x1','crop-y1','map-name','rotation','max-side','provenance'].forEach(id=>$(id).oninput=()=>{changed();redraw();});
['atlas-status','atlas-feature','atlas-tolerance','atlas-evidence','atlas-annotator'].forEach(id=>$(id).oninput=changed);
$('source-select').onchange=()=>run(async()=>{if(!(await mayLeave())){$('source-select').value=source?.id||'';return;}source=catalog.sources.find(s=>s.id===$('source-select').value)||null;setCrop(source?[0,0,source.width,source.height]:[0,0,0,0]);changed();showWorking();});
$('upload-source').onclick=()=>run(async()=>{
  const file=$('source-file').files[0];if(!file)throw new Error('请选择 PDF 或图像。');if(file.size>80*1024*1024)throw new Error('文件须小于 80 MB。');
  if(!(await mayLeave()))return;
  $('dirty').textContent='正在导入…';
  const data=await atlasJSON(`/api/atlas/upload?name=${encodeURIComponent(file.name)}&page=${Number($('pdf-page').value)}`,{method:'POST',body:file});
  source=data;catalog=await request('/api/atlas');renderCatalog();setCrop([0,0,source.width,source.height]);showWorking();changed();toast('原图已导入');
});
$('save-map').onclick=()=>run(async()=>{
  if(detail.active&&!(await confirmAction('保存后所有事件切换到新底图版本；旧版标注保留，不自动迁移。','保存底图版本')))return;
  detail=await request(`/api/atlas/${detail.id}/map`,{base_revision:detail.revision,source_id:source.id,crop:getCrop(),rotation:Number($('rotation').value),max_side:Number($('max-side').value),title:$('map-name').value,provenance:$('provenance').value});
  clean();catalog=await request('/api/atlas');renderCatalog();fillMapFields();loadEvent();view='annotate';showView();toast('底图版本已保存；人工标注与图像分开存储');
});
$('restore-map').onclick=()=>run(async()=>{
  if(!(await confirmAction('恢复选定底图及其已有标注。当前未保存内容将丢弃。','恢复底图')))return;
  await request(`/api/atlas/${detail.id}/restore`,{base_revision:detail.revision,version:$('map-history').value});clean();await openMap(detail.id);
});
$('save-gold').onclick=()=>run(async()=>{
  detail=await request(`/api/atlas/${detail.id}/gold`,{event_id:eventId,map_version:detail.active.version,base_revision:selected().revision,status:$('atlas-status').value,
    geometry:points.length?{type:geometryType,coordinates:points}:null,geo_feature_type:$('atlas-feature').value,tolerance_px:Number($('atlas-tolerance').value),evidence:$('atlas-evidence').value,annotator:$('atlas-annotator').value});
  loadEvent();catalog=await request('/api/atlas');renderCatalog();toast('人工标注已保存；干净底图未改变');
});
async function moveEvent(step){if(!(await mayLeave()))return;const index=detail.events.findIndex(e=>e.id===eventId)+step;if(index<0||index>=detail.events.length)return;eventId=detail.events[index].id;loadEvent();setMode('hand');}
$('previous-event').onclick=()=>run(()=>moveEvent(-1));$('next-event').onclick=()=>run(()=>moveEvent(1));
async function download(url,name){const r=await fetch(url);if(!r.ok)throw new Error((await r.json()).error);const urlBlob=URL.createObjectURL(await r.blob());const a=document.createElement('a');a.href=urlBlob;a.download=name;a.click();setTimeout(()=>URL.revokeObjectURL(urlBlob),1000);}
async function savedExport(kind){if(dirty)throw new Error('请先保存或放弃当前修改，再导出已保存结果。');await download(`/api/atlas/${detail.id}/${kind}?version=${detail.active.version}`,`${detail.id}-${detail.active.version}-${kind==='input'?'vlm-input.zip':'gold.json'}`);}
$('export-input').onclick=()=>run(()=>savedExport('input'));$('export-gold').onclick=()=>run(()=>savedExport('gold'));
$('export-overlay').onclick=()=>run(async()=>{if(dirty)throw new Error('请先保存人工标注。');await download(`/api/atlas/${detail.id}/overlay/${eventId}/gold?version=${detail.active.version}`,`${eventId}-gold.png`);});
$('export-prediction').onclick=()=>run(async()=>{
  const model=$('prediction-model').value;
  if(!selectedPrediction()?.geometry)throw new Error('该模型在此事件上没有可导出的几何。');
  await download(`/api/atlas/${detail.id}/overlay/${eventId}/predictions?version=${detail.active.version}&model=${encodeURIComponent(model)}`,`${eventId}-${model.replace(/[^a-zA-Z0-9._-]/g,'-')}-prediction.png`);
});
$('import-prediction').onclick=()=>run(async()=>{if(dirty)throw new Error('请先保存或放弃当前人工标注。');const file=$('prediction-file').files[0];if(!file)throw new Error('请选择预测 JSON。');if(file.size>200000)throw new Error('预测文件过大。');const data=JSON.parse(await file.text());detail=await request(`/api/atlas/${detail.id}/predictions`,data);loadEvent();toast('模型预测已单独保存');});
$('refresh-atlas').onclick=()=>run(async()=>{if(!(await mayLeave()))return;catalog=await request('/api/atlas');await openMap(detail.id);});
window.addEventListener('beforeunload',e=>{if(dirty||busy){e.preventDefault();e.returnValue='';}});
new ResizeObserver(()=>{
  working.invalidateSize();reference.invalidateSize();
  if(workBounds)working.fitBounds(workBounds,{padding:[12,50]});
  if(refBounds)reference.fitBounds(refBounds);
}).observe(document.querySelector('.atlas-canvases'));
icons();run(async()=>{catalog=await request('/api/atlas');renderCatalog();const first=catalog.maps.find(m=>m.battle_id==='zurich_second_1799')||catalog.maps[0];if(first)await openMap(first.id);});
