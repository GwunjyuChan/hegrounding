/* Basemap raster assets and editable overlays deliberately use separate paths. */
const $ = id => document.getElementById(id);
const labels = {pending:'待审核',accepted:'已通过',ambiguous:'有歧义',unlocatable:'无法定位',outside_map:'范围外',rejected:'剔除'};
const featureNames = {bridge:'桥梁',ford:'浅滩',river_bank:'河岸',river:'河流',road:'道路',junction:'交叉口',woodland:'林地',high_ground:'高地',open_ground:'开阔地',settlement:'聚落',building:'建筑',other:'其他'};
const battleNames = {zurich_second_1799:'第二次苏黎世战役',san_sebastian_1813:'圣塞巴斯蒂安围城',bussaco_1810:'布萨科战役 · 内伊进攻',marengo_1800:'Marengo 战后部署',borkowo:'Borkowo',sochocin:'Sochocin',wavre:'Wavre'};
let catalog, detail, eventId, source, referenceDimensions, view='choose', mode='hand', dirty=false, busy=false;
let geometryType='point', points=[], undo=[], redo=[], cropStart=null, cropHover=null;
const modelVisibility=new Map();
let refImage, workImage, refBounds, workBounds, dimensions=[0,0];
const reference = L.map('reference-canvas',{crs:L.CRS.Simple,minZoom:-6,maxZoom:5,zoomSnap:.25,zoomDelta:.5,attributionControl:false});
const working = L.map('working-canvas',{crs:L.CRS.Simple,minZoom:-6,maxZoom:5,zoomSnap:.25,zoomDelta:.5,attributionControl:false});
const overlays=L.layerGroup().addTo(working);
I18n.mapControls(reference);I18n.mapControls(working);
const asLatLng = p => [-p[1],p[0]];
const imageBounds = (w,h) => [[-h,0],[0,w]];
function icons(){lucide.createIcons();}
function error(e){I18n.text($('atlas-error'),e.message||String(e));}
function changed(){dirty=true;I18n.text($('dirty'),'未保存修改');}
function clean(){dirty=false;I18n.text($('dirty'),'');}
function toast(msg){I18n.text($('toast'),msg);$('toast').hidden=false;setTimeout(()=>$('toast').hidden=true,3500);}
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
    I18n.attr(checkbox,()=>m.label+' '+I18n.t('模型预测'),'aria-label');
    checkbox.onchange=()=>{modelVisibility.set(m.id,checkbox.checked);redraw();};
    const swatch=document.createElement('span');swatch.className='model-swatch';swatch.style.backgroundColor=m.color;
    const name=document.createElement('span');I18n.text(name,m.label+(!prediction?' · 无结果':!prediction.geometry?' · 拒答':''));
    label.append(checkbox,swatch,name);return label;
  }));
}
async function request(url,body){
  const options=body===undefined?{}:{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)};
  const data=await atlasJSON(url,options);
  if(url==='/api/atlas')data.maps=data.maps.filter(m=>m.kind!=='place_lab');
  return data;
}
async function run(fn){
  if(busy)return;
  busy=true;I18n.text($('atlas-error'),'');
  document.querySelector('.atlas-layout').inert=true;
  document.querySelectorAll('.atlas-inspector button').forEach(b=>b.disabled=true);
  try{await fn();}catch(e){error(e);}finally{busy=false;document.querySelector('.atlas-layout').inert=false;document.querySelectorAll('.atlas-inspector button').forEach(b=>b.disabled=false);availability();}
}
function confirmAction(message,title='尚有未保存的修改'){
  I18n.text($('confirm-title'),title);I18n.text($('confirm-text'),message);
  return new Promise(resolve=>{
    const dialog=$('atlas-confirm');
    $('confirm-ok').onclick=()=>{dialog.close();resolve(true);};
    $('confirm-cancel').onclick=()=>{dialog.close();resolve(false);};
    dialog.oncancel=()=>resolve(false);dialog.showModal();
  });
}
async function mayLeave(){return !dirty||await confirmAction('离开会丢弃当前未保存的裁切或事件标注。');}
function option(value,text){const el=document.createElement('option');el.value=value;I18n.text(el,text);return el;}
function row(title,subtitle,active,onclick,translateSubtitle=true){const b=document.createElement('button');b.className='atlas-item'+(active?' active':'');const name=document.createElement('span');I18n.text(name,title);const s=document.createElement('small');if(translateSubtitle)I18n.text(s,subtitle);else s.textContent=subtitle;b.append(name,s);b.onclick=onclick;return b;}
function renderCatalog(){
  I18n.text($('atlas-count'),`${catalog.maps.length} 张参考地图`);
  const rows=catalog.maps.map(m=>row(
    m.battle_name||battleNames[m.battle_id]||m.battle_id,
    `${m.total} 事件 · ${m.active?m.reviewed+' 已审核':'待确认参考底图'}`,
    m.id===detail?.id,
    ()=>run(async()=>{if(await mayLeave())await openMap(m.id);})
  ));
  $('atlas-list').replaceChildren(...rows);
  $('source-select').replaceChildren(option('','选择已导入图像'),option('reference','当前战役参考地图'),...catalog.sources.map(s=>option(s.id,()=>s.name+(s.page?' · '+I18n.t('第 '+s.page+' 页'):''))));
  $('source-select').value=source?.id||'';
  if(!$('atlas-feature').options.length)$('atlas-feature').replaceChildren(...catalog.feature_types.map(f=>option(f,featureNames[f]||f)));
}
function renderEvents(){
  const filter=$('scope-filter').value;
  $('atlas-events').replaceChildren(...detail.events.filter(e=>filter==='all'||(e.gold?.status||'pending')===filter).map(e=>row(
    `${e.id} · ${labels[e.gold?.status||'pending']}`,e.question,e.id===eventId,()=>run(async()=>{
      if(!(await mayLeave()))return;
      eventId=e.id;view=detail.active?'annotate':'choose';fillMapFields();loadEvent();showView();
    }),false)));
}
async function openMap(mid,preferredEvent=null){
  detail=await request('/api/atlas/'+mid);
  eventId=detail.events.find(e=>e.id===preferredEvent)?.id||detail.events.find(e=>!e.gold||e.gold.status==='pending')?.id||detail.events[0]?.id;
  const ref=await request('/api/event/'+detail.reference_event);
  referenceDimensions=ref.dimensions;
  if(refImage)reference.removeLayer(refImage);
  refBounds=imageBounds(...ref.dimensions);
  refImage=L.imageOverlay(workspaceURL('/maps/'+detail.reference_event),refBounds).addTo(reference);
  reference.fitBounds(refBounds);clean();source=catalog.sources.find(s=>s.id===detail.active?.source_id)||null;
  view=detail.active?'annotate':'choose';
  $('show-reference').checked=false;
  fillMapFields();loadEvent();renderCatalog();renderEvents();showView();
}
function fillMapFields(){
  const a=detail.active;
  source=a?catalog.sources.find(s=>s.id===a.source_id)||null:null;
  $('source-select').value=source?.id||'';
  I18n.text($('map-title'),detail.battle_name||battleNames[detail.battle_id]||detail.battle_id);
  $('map-name').value=a?.title||`${detail.battle_name||battleNames[detail.battle_id]||detail.battle_id} · 标注底图`;
  $('provenance').value=a?.provenance||'';
  $('rotation').value=a?.rotation||0;$('max-side').value=a?.max_side??0;
  setCrop(a?.crop||(source?[0,0,source.width,source.height]:[0,0,0,0]));
  $('map-history').replaceChildren(...detail.history.map((a,i)=>option(a.version,`${i===0?'当前 · ':''}${a.version.slice(0,8)} · ${a.width}×${a.height} · ${a.created_at.slice(0,16)}`)));
  $('clean-download').hidden=!a;
  if(a){$('clean-download').href=workspaceURL('/atlas-assets/'+a.version);$('clean-download').download=`${detail.id}-${a.version}-basemap.png`;}
}
function setCrop(values){['crop-x0','crop-y0','crop-x1','crop-y1'].forEach((id,i)=>$(id).value=values[i]);}
function getCrop(){return ['crop-x0','crop-y0','crop-x1','crop-y1'].map(id=>Number($(id).value));}
function availability(){
  $('save-map').disabled=busy||!source;
  $('save-gold').disabled=busy||!detail?.active||!selected();
  $('restore-map').disabled=busy||!detail?.history.length;
  $('use-reference').disabled=busy||!detail;
  $('choose-upload').disabled=busy||!detail;
  $('edit-basemap').disabled=busy||!detail;
  ['export-input','export-gold','import-prediction'].forEach(id=>$(id).disabled=busy||!detail?.active);
  $('export-overlay').disabled=busy||!selected()?.gold?.geometry;
  $('export-prediction').disabled=busy||!selectedPrediction()?.geometry;
  const i=detail?.events.findIndex(e=>e.id===eventId)??-1;
  $('previous-event').disabled=i<=0;$('next-event').disabled=!detail||i>=detail.events.length-1;
}
function showView(){
  $('choose-fields').hidden=view!=='choose';
  $('prepare-fields').hidden=view!=='prepare';$('annotate-fields').hidden=view!=='annotate';
  I18n.text($('working-label'),view==='choose'?'参考地图':view==='prepare'?'编辑底图':'标注底图');
  $('edit-basemap').hidden=view==='prepare';
  $('step-map').setAttribute('aria-current',view==='annotate'?'false':'step');
  $('step-annotate').setAttribute('aria-current',view==='annotate'?'step':'false');
  $('reference-toggle').hidden=view==='choose';
  $('clean-download').hidden=view!=='annotate'||!detail.active;
  I18n.text($('map-role'),view==='choose'||(view==='annotate'&&detail.active?.base_map_role==='reference_map')?'参考底图 · 可能含作战部署':view==='prepare'?'底图草稿':'已选底图');
  $('crop-tool').hidden=view!=='prepare';
  document.querySelectorAll('[data-geometry]').forEach(b=>b.hidden=view!=='annotate');
  ['gold-toggle','prediction-toggle','undo-atlas','redo-atlas','clear-atlas'].forEach(id=>$(id).hidden=view!=='annotate');
  updateReferencePane();
  setMode('hand');showWorking();availability();
}
function updateReferencePane(){
  const visible=view!=='choose'&&$('show-reference').checked;
  $('reference-pane').hidden=!visible;
  document.querySelector('.atlas-canvases').classList.toggle('no-reference',!visible);
  working.invalidateSize();reference.invalidateSize();
}
function showWorking(){
  if(workImage)working.removeLayer(workImage);
  const a=view==='choose'?{width:referenceDimensions[0],height:referenceDimensions[1]}:view==='prepare'?source:detail.active;
  workImage=null;workBounds=null;
  $('map-empty').hidden=!!a;dimensions=a?[a.width,a.height]:[0,0];
  $('working-dimensions').textContent=a?`${a.width} × ${a.height} px`:'';
  I18n.text($('map-version'),view==='choose'?'参考图 · 待确认':detail.active?`底图 ${detail.active.version.slice(0,8)}`:'底图草稿');
  if(a){
    workBounds=imageBounds(a.width,a.height);
    const url=view==='choose'?'/maps/'+detail.reference_event:'/atlas-assets/'+(view==='prepare'?a.id:a.version);
    workImage=L.imageOverlay(workspaceURL(url),workBounds).addTo(working);
    workImage.on('error',()=>error(new Error('底图加载失败，请刷新重试。')));
    working.fitBounds(workBounds,{padding:[12,50]});
  }
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
  $('preview-event').textContent=e.id;$('preview-question').textContent=e.question;$('preview-passage').textContent=e.text;
  const url=new URL(location.href);url.searchParams.set('map',detail.id);url.searchParams.set('event',e.id);url.searchParams.delete('edit');history.replaceState(null,'',url);
  if(e.source_text)I18n.raw($('original-text'),e.source_text);else I18n.text($('original-text'),'无逐字原文');$('event-caution').textContent=e.caution;
  const safe=/^https?:\/\//i.test(e.article_url);$('source-link').hidden=!safe;if(safe)$('source-link').href=e.article_url;
  $('atlas-status').value=gold?.status||'accepted';$('atlas-feature').value=gold?.geo_feature_type||'other';
  $('atlas-evidence').value=gold?.evidence||'';$('atlas-tolerance').value=gold?.tolerance_px||0;
  $('atlas-confidence').value=gold?.confidence??'';
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
$('show-reference').onchange=updateReferencePane;
$('show-gold').onchange=redraw;$('prediction-model').onchange=availability;
$('scope-filter').onchange=renderEvents;
async function referenceSource(){
  const result=await request(`/api/atlas/${detail.id}/reference-source`,{base_revision:detail.revision});
  catalog=await request('/api/atlas');source=result;renderCatalog();
  $('provenance').value='战役参考地图 · 可能含作战部署';
  return result;
}
async function editBasemap(){
  if(!(await mayLeave()))return false;
  fillMapFields();loadEvent();
  if(!source){await referenceSource();setCrop([0,0,source.width,source.height]);}
  view='prepare';showView();return true;
}
async function finishSelection(result){
  detail=result;catalog=await request('/api/atlas');
  view='annotate';fillMapFields();loadEvent();renderCatalog();showView();
}
$('edit-basemap').onclick=()=>run(editBasemap);
$('choose-upload').onclick=()=>run(async()=>{if(await editBasemap())$('source-file').focus();});
$('cancel-map').onclick=()=>run(async()=>{if(!(await mayLeave()))return;view=detail.active?'annotate':'choose';fillMapFields();loadEvent();showView();});
$('use-reference').onclick=()=>run(async()=>{
  await finishSelection(await request(`/api/atlas/${detail.id}/use-reference`,{base_revision:detail.revision}));
  toast('参考底图已选定');
});
['crop-x0','crop-y0','crop-x1','crop-y1','map-name','rotation','max-side','provenance'].forEach(id=>$(id).oninput=()=>{changed();redraw();});
['atlas-status','atlas-feature','atlas-tolerance','atlas-evidence','atlas-annotator','atlas-confidence'].forEach(id=>$(id).oninput=changed);
$('source-select').onchange=()=>run(async()=>{
  const choice=$('source-select').value;
  if(!(await mayLeave())){$('source-select').value=source?.id||'';return;}
  if(choice==='reference')await referenceSource();else {source=catalog.sources.find(s=>s.id===choice)||null;$('provenance').value='';}
  $('rotation').value=0;$('max-side').value=0;setCrop(source?[0,0,source.width,source.height]:[0,0,0,0]);changed();showWorking();
});
$('upload-source').onclick=()=>run(async()=>{
  const file=$('source-file').files[0];if(!file)throw new Error('请选择 PDF 或图像。');if(file.size>512*1024*1024)throw new Error('文件须不超过 512 MiB。');
  if(!(await mayLeave()))return;
  I18n.text($('dirty'),'正在导入…');
  const data=await atlasJSON(`/api/atlas/upload?name=${encodeURIComponent(file.name)}&page=${Number($('pdf-page').value)}`,{method:'POST',body:file});
  source=data;$('max-side').value=0;catalog=await request('/api/atlas');renderCatalog();$('rotation').value=0;$('provenance').value='';setCrop([0,0,source.width,source.height]);showWorking();changed();toast('原图已导入');
});
$('save-map').onclick=()=>run(async()=>{
  if(detail.active&&!(await confirmAction('保存后所有事件切换到新底图版本；旧版标注保留，不自动迁移。','保存底图版本')))return;
  const result=await request(`/api/atlas/${detail.id}/map`,{base_revision:detail.revision,source_id:source.id,crop:getCrop(),rotation:Number($('rotation').value),max_side:Number($('max-side').value),title:$('map-name').value,provenance:$('provenance').value});
  await finishSelection(result);toast('底图已选定，可以标注事件');
});
$('restore-map').onclick=()=>run(async()=>{
  if(!(await confirmAction('恢复选定底图及其已有标注。当前未保存内容将丢弃。','恢复底图')))return;
  await request(`/api/atlas/${detail.id}/restore`,{base_revision:detail.revision,version:$('map-history').value});clean();await openMap(detail.id);
});
$('save-gold').onclick=()=>run(async()=>{
  detail=await request(`/api/atlas/${detail.id}/gold`,{event_id:eventId,map_version:detail.active.version,base_revision:selected().revision,status:$('atlas-status').value,
    confidence:$('atlas-confidence').value===''?null:Number($('atlas-confidence').value),
    geometry:points.length?{type:geometryType,coordinates:points}:null,geo_feature_type:$('atlas-feature').value,tolerance_px:Number($('atlas-tolerance').value),evidence:$('atlas-evidence').value,annotator:$('atlas-annotator').value});
  loadEvent();catalog=await request('/api/atlas');renderCatalog();toast('人工标注已保存；底图图像未改变');
});
async function moveEvent(step){if(!(await mayLeave()))return;const index=detail.events.findIndex(e=>e.id===eventId)+step;if(index<0||index>=detail.events.length)return;eventId=detail.events[index].id;loadEvent();setMode('hand');}
$('previous-event').onclick=()=>run(()=>moveEvent(-1));$('next-event').onclick=()=>run(()=>moveEvent(1));
async function download(url,name){const r=await fetch(workspaceURL(url));if(!r.ok)throw new Error((await r.json()).error);const urlBlob=URL.createObjectURL(await r.blob());const a=document.createElement('a');a.href=urlBlob;a.download=name;a.click();setTimeout(()=>URL.revokeObjectURL(urlBlob),1000);}
async function savedExport(kind){if(dirty)throw new Error('请先保存或放弃当前修改，再导出已保存结果。');await download(`/api/atlas/${detail.id}/${kind}?version=${detail.active.version}`,`${detail.id}-${detail.active.version}-${kind==='input'?'vlm-input.zip':'gold.json'}`);}
$('export-input').onclick=()=>run(()=>savedExport('input'));$('export-gold').onclick=()=>run(()=>savedExport('gold'));
$('export-overlay').onclick=()=>run(async()=>{if(dirty)throw new Error('请先保存人工标注。');await download(`/api/atlas/${detail.id}/overlay/${eventId}/gold?version=${detail.active.version}`,`${eventId}-gold.png`);});
$('export-prediction').onclick=()=>run(async()=>{
  const model=$('prediction-model').value;
  if(!selectedPrediction()?.geometry)throw new Error('该模型在此事件上没有可导出的几何。');
  await download(`/api/atlas/${detail.id}/overlay/${eventId}/predictions?version=${detail.active.version}&model=${encodeURIComponent(model)}`,`${eventId}-${model.replace(/[^a-zA-Z0-9._-]/g,'-')}-prediction.png`);
});
$('import-prediction').onclick=()=>run(async()=>{if(dirty)throw new Error('请先保存或放弃当前人工标注。');const file=$('prediction-file').files[0];if(!file)throw new Error('请选择预测 JSON。');if(file.size>200000)throw new Error('预测文件过大。');const data=JSON.parse(await file.text());detail=await request(`/api/atlas/${detail.id}/predictions`,data);loadEvent();toast('模型预测已单独保存');});
$('refresh-atlas').onclick=()=>run(async()=>{if(!(await mayLeave()))return;catalog=await request('/api/atlas');await openMap(detail.id,eventId);});
document.querySelector('.brand').onclick=async e=>{if(dirty){e.preventDefault();if(await mayLeave()){clean();location.href=e.currentTarget?.href||workspaceURL('/');}}};
window.addEventListener('beforeunload',e=>{if(dirty||busy){e.preventDefault();e.returnValue='';}});
new ResizeObserver(()=>{
  working.invalidateSize();reference.invalidateSize();
  if(workBounds)working.fitBounds(workBounds,{padding:[12,50]});
  if(refBounds)reference.fitBounds(refBounds);
}).observe(document.querySelector('.atlas-canvases'));
icons();run(async()=>{
  catalog=await request('/api/atlas');renderCatalog();
  const params=new URLSearchParams(location.search),requested=params.get('map');
  const first=requested?catalog.maps.find(m=>m.id===requested):catalog.maps[0];
  if(!first)throw new Error('未找到此战役，请返回战场地图重新选择。');
  await openMap(first.id,params.get('event'));
  if(params.get('edit')==='1')await editBasemap();
});
