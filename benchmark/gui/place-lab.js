const $ = id => document.getElementById(id);
const map = L.map('lab-canvas',{crs:L.CRS.Simple,minZoom:-6,maxZoom:5,zoomSnap:.25,attributionControl:false});
const layer = L.layerGroup().addTo(map);
I18n.mapControls(map);
let catalog, mid, data, selectedId, raster, bounds, busy=false, dirty=false, drawing=false;
let geometryType='point', points=[], undo=[], redo=[], refreshPending=false;
const statusNames={accepted:'已通过',ambiguous:'有歧义',unlocatable:'无法定位'};
function task(){return data?.tasks.find(t=>t.id===selectedId);}
function runs(){return [...new Map((data?.tasks||[]).flatMap(t=>t.predictions).map(p=>[p.job_id,p])).values()].sort((a,b)=>b.created_at.localeCompare(a.created_at));}
function prediction(t=task()){const id=$('lab-runs').value==='latest'?runs()[0]?.job_id:$('lab-runs').value;return t?.predictions.find(p=>p.job_id===id);}
function option(value,text,translate=true){const o=document.createElement('option');o.value=value;if(translate)I18n.text(o,text);else o.textContent=text;return o;}
function changed(){dirty=true;I18n.text($('lab-dirty'),'未保存');}
function clean(){dirty=false;I18n.text($('lab-dirty'),'');}
function fail(e){I18n.text($('lab-error'),e.message||String(e));}
async function api(path,body){return atlasJSON(path,body===undefined?{}:{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)});}
async function action(fn){if(busy)return;busy=true;availability();I18n.text($('lab-error'),'');try{await fn();}catch(e){fail(e);}finally{busy=false;availability();}}
function mayLeave(){
  if(!dirty&&!$('lab-name').value.trim())return Promise.resolve(true);
  return new Promise(resolve=>{const d=$('lab-confirm');$('lab-continue').onclick=()=>{d.close();resolve(true);};$('lab-cancel').onclick=()=>{d.close();resolve(false);};d.oncancel=()=>resolve(false);d.showModal();});
}
function availability(){
  $('lab-map').disabled=busy;$('lab-refresh').disabled=busy;
  $('lab-upload-open').disabled=busy;
  $('lab-input').disabled=busy||!(data?.tasks||[]).some(t=>t.gold);
  $('lab-import').disabled=busy||!data?.tasks.length;
  $('lab-add').disabled=busy||!data?.map;
  $('lab-save').disabled=busy||!task();
  $('lab-export').disabled=busy||!data?.tasks.length;
  ['lab-point','lab-polygon','lab-clear'].forEach(id=>$(id).disabled=busy||!task());
  $('lab-undo').disabled=busy||!undo.length;$('lab-redo').disabled=busy||!redo.length;
  $('lab-tolerance').disabled=geometryType!=='point';
  $('lab-annotation').hidden=!task();
}
function renderTasks(){
  $('lab-count').textContent=data?.tasks.length||0;
  $('lab-tasks').replaceChildren(...(data?.tasks||[]).map(t=>{
    const b=document.createElement('button');b.className='atlas-item'+(t.id===selectedId?' active':'');b.textContent=t.place_name;
    const p=prediction(t),label=!p?'未预测':p.status==='error'?'预测失败':p.geometry?'已定位':'未找到';
    const small=document.createElement('small');I18n.text(small,(statusNames[t.gold?.status]||'待标注')+' · '+label);b.append(small);
    b.onclick=()=>action(async()=>{if(await mayLeave()){selectedId=t.id;$('lab-name').value='';loadTask();}});return b;
  }));
}
function renderRuns(preferred){
  const prior=preferred||$('lab-runs').value,all=runs();
  $('lab-runs').replaceChildren(option('latest',all.length?'最新批次':'暂无预测'),...all.map(r=>option(r.job_id,
    `${r.created_at.slice(0,19).replace('T',' ')} · ${r.model} · ${r.coordinate_mode==='normalized_1000'?'相对':'像素'}`)));
  if(all.some(r=>r.job_id===prior))$('lab-runs').value=prior;
  $('lab-runs').disabled=!all.length;
}
function loadTask(){
  const t=task(),g=t?.gold;
  geometryType=g?.geometry?.type||'point';points=structuredClone(g?.geometry?.coordinates||[]);undo=[];redo=[];
  if(t)I18n.raw($('lab-title'),t.place_name);else I18n.text($('lab-title'),'选择或新增地名');
  $('lab-status').value=g?.status||'accepted';$('lab-confidence').value=g?.confidence??'';
  $('lab-tolerance').value=g?.tolerance_px??0;$('lab-evidence').value=g?.evidence||'';
  if(g)$('lab-annotator').value=g.annotator;
  clean();setMode(false);renderRuns();renderTasks();redraw();availability();
}
async function loadMap(id){
  const next=await api(`/api/atlas/${id}/places`);mid=id;data=next;selectedId=data.tasks[0]?.id;
  $('lab-map').value=mid;$('lab-name').value='';
  history.replaceState(null,'',workspaceURL('/place-lab.html?map='+encodeURIComponent(mid)));
  if(raster){map.removeLayer(raster);raster=null;}
  bounds=null;$('lab-empty').hidden=!!data.map;
  if(data.map){const a=data.map;bounds=[[-a.height,0],[0,a.width]];raster=L.imageOverlay(workspaceURL('/atlas-assets/'+a.version),bounds).addTo(map);map.fitBounds(bounds,{padding:[24,55]});}
  $('lab-dimensions').textContent=data.map?`${data.map.width} × ${data.map.height} px`:'';
  I18n.text($('lab-version'),data.map?`底图 ${data.map.version.slice(0,8)}`:'未设置底图');
  loadTask();
  renderJob();
}
function setMode(draw,type=geometryType){drawing=draw;geometryType=type;if(draw)map.dragging.disable();else map.dragging.enable();
  $('lab-hand').classList.toggle('active',!draw);$('lab-point').classList.toggle('active',draw&&type==='point');$('lab-polygon').classList.toggle('active',draw&&type==='polygon');
  $('lab-canvas').style.cursor=draw?'crosshair':'grab';}
function draw(geometry,color,dashed=false,name='',selected=false){
  if(!geometry?.coordinates.length)return;
  const coords=geometry.coordinates.map(([x,y])=>[-y,x]),style={color,weight:selected?3:2,fillOpacity:.08,interactive:true,dashArray:dashed?'6 4':null};
  const shape=geometry.type==='point'?L.circleMarker(coords[0],{...style,radius:selected?8:5,fillOpacity:.6}):coords.length>=3?L.polygon(coords,style):L.polyline(coords,style);
  shape.addTo(layer);
  const label=document.createElement('span');I18n.text(label,()=>name+' · '+I18n.t(dashed?'模型':'人工'));shape.bindTooltip(label,{direction:'top'});
  if(!dashed)coords.forEach(p=>L.circleMarker(p,{radius:3,color,weight:1,fillColor:'#fff',fillOpacity:1,interactive:false}).addTo(layer));
}
function redraw(){
  layer.clearLayers();
  let located=0,failed=0,abstained=0;
  for(const t of data?.tasks||[]){
    const selected=t.id===selectedId,p=prediction(t);
    if($('lab-show-gold').checked)draw(selected?{type:geometryType,coordinates:points}:t.gold?.geometry,'#cf3f49',false,t.place_name,selected);
    if($('lab-show-model').checked)draw(p?.geometry,'#287be0',true,t.place_name,selected);
    if(p?.status==='error')failed++;else if(p?.geometry)located++;else if(p)abstained++;
  }
  const saved=(data?.tasks||[]).filter(t=>t.gold).length;
  I18n.text($('lab-summary'),`已保存 ${saved}/${data?.tasks.length||0} · 已定位 ${located} · 未找到 ${abstained} · 失败 ${failed}`);
  const p=prediction();
  if(p?.model||runs()[0]?.model)I18n.raw($('lab-model'),p?.model||runs()[0]?.model);else I18n.text($('lab-model'),'暂无预测结果');
  I18n.text($('lab-result'),p?(p.status==='error'?'预测失败':p.geometry?`原图坐标：${p.geometry.coordinates[0].map(n=>n.toFixed(1)).join(', ')}`:'模型未能定位')+(p.imported?' · 导入结果':` · ${p.elapsed_seconds.toFixed(1)} s`)+(p.format_normalization?' · 单点格式已转换':''):'本批次无该地名结果');
  const g=task()?.gold;
  I18n.text($('lab-metric'),'');
  if(!dirty&&g?.status==='accepted'&&p?.comparison){
    const c=p.comparison;
    I18n.text($('lab-metric'),c.gold_type==='polygon'?(c.hit?'人工区域内':`距人工区域 ${c.distance_px.toFixed(1)} px`):`距人工点 ${c.distance_px.toFixed(1)} px · ${c.hit?'容差内':'容差外'}`);
  }
  availability();
}
function remember(){undo.push({type:geometryType,points:structuredClone(points)});redo=[];}
map.doubleClickZoom.disable();
map.on('mousemove',e=>{$('lab-cursor').textContent=`x ${Math.round(e.latlng.lng)} · y ${Math.round(-e.latlng.lat)}`;});
map.on('click',e=>{if(!drawing||busy||!task()||!data.map)return;
  const x=Math.round(e.latlng.lng),y=Math.round(-e.latlng.lat);if(x<0||y<0||x>=data.map.width||y>=data.map.height)return;
  remember();if(geometryType==='point')points=[[x,y]];else points.push([x,y]);changed();redraw();});
$('lab-hand').onclick=()=>setMode(false);
for(const type of ['point','polygon'])$('lab-'+type).onclick=()=>{if(type!==geometryType){remember();points=[];changed();}setMode(true,type);redraw();};
$('lab-undo').onclick=()=>{if(!undo.length)return;redo.push({type:geometryType,points:structuredClone(points)});const s=undo.pop();points=s.points;setMode(true,s.type);changed();redraw();};
$('lab-redo').onclick=()=>{if(!redo.length)return;undo.push({type:geometryType,points:structuredClone(points)});const s=redo.pop();points=s.points;setMode(true,s.type);changed();redraw();};
$('lab-clear').onclick=()=>{remember();points=[];changed();redraw();};
$('lab-fit').onclick=()=>bounds&&map.fitBounds(bounds,{padding:[24,55]});
['lab-show-gold','lab-show-model','lab-runs'].forEach(id=>$(id).onchange=()=>{renderTasks();redraw();});
['lab-status','lab-confidence','lab-tolerance','lab-evidence','lab-annotator'].forEach(id=>$(id).oninput=()=>{changed();redraw();});
$('lab-map').onchange=()=>action(async()=>{const id=$('lab-map').value;if(await mayLeave())await loadMap(id);else $('lab-map').value=mid;});
$('lab-refresh').onclick=()=>action(async()=>{if(await mayLeave()){await loadCatalog();if(mid)await loadMap(mid);}});
$('lab-add-form').onsubmit=e=>{e.preventDefault();action(async()=>{
  if(dirty)throw new Error('请先保存当前人工答案，或切换地名放弃草稿。');
  const result=await api(`/api/atlas/${mid}/places`,{map_version:data.map.version,place_name:$('lab-name').value});
  data=result;selectedId=result.task_id;$('lab-name').value='';loadTask();
});};
$('lab-save').onclick=()=>action(async()=>{
  data=await api(`/api/atlas/${mid}/place-gold`,{map_version:data.map.version,task_id:selectedId,base_revision:task().revision,
    geometry:points.length?{type:geometryType,coordinates:points}:null,status:$('lab-status').value,
    confidence:$('lab-confidence').value===''?null:Number($('lab-confidence').value),tolerance_px:Number($('lab-tolerance').value),
    evidence:$('lab-evidence').value,annotator:$('lab-annotator').value});loadTask();
});
function renderJob(){
  const jobs=(data?.jobs||[]).filter(j=>j.map_version===data.map?.version),running=jobs.find(j=>j.status==='running');
  const latest=running||jobs[0];
  I18n.text($('lab-job'),running?`批量预测中 · ${running.progress?.done||0}/${running.task_ids?.length||1}`:latest?.status==='completed'?'预测已完成':latest?.error||'');
}
async function refreshResults(){
  if(busy||!mid||refreshPending||document.hidden)return;
  refreshPending=true;const id=mid;
  try{
    const next=await api(`/api/atlas/${id}/places`);
    if(mid===id&&!busy){
      if(next.map?.version===data.map?.version){
        // Keep annotation edits made while the result request was in flight.
        data={...data,jobs:next.jobs,tasks:data.tasks.map(t=>{const n=next.tasks.find(r=>r.id===t.id);return n?{...t,predictions:n.predictions.map(p=>n.revision===t.revision?p:{...p,comparison:undefined})}:t;})};
        renderRuns();renderTasks();redraw();renderJob();
      }else I18n.text($('lab-job'),'底图版本已改变，请保存或放弃草稿后刷新。');
    }
  }catch(e){if(mid===id)I18n.text($('lab-job'),'结果同步暂不可用，稍后自动重试。');}
  finally{refreshPending=false;}
}
setInterval(refreshResults,3000);
$('lab-export').onclick=()=>{if(dirty){fail(new Error('请先保存人工答案。'));return;}
  const blob=new Blob([JSON.stringify({map:data.map,tasks:data.tasks},null,2)],{type:'application/json'}),url=URL.createObjectURL(blob),a=document.createElement('a');
  a.href=url;a.download=mid+'-place-experiment.json';a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);};
$('lab-home').onclick=async e=>{if(dirty||$('lab-name').value.trim()){e.preventDefault();if(await mayLeave()){clean();$('lab-name').value='';location.href=$('lab-home').href;}}};
$('lab-upload-open').onclick=async()=>{if(await mayLeave()){I18n.text($('lab-upload-error'),'');$('lab-upload-dialog').showModal();}};
$('lab-upload-cancel').onclick=()=>{if(!busy)$('lab-upload-dialog').close();};
$('lab-upload-dialog').addEventListener('cancel',e=>{if(busy)e.preventDefault();});
$('lab-map-file').onchange=()=>{if(!$('lab-map-title').value)$('lab-map-title').value=($('lab-map-file').files[0]?.name||'').replace(/\.[^.]+$/,'');};
$('lab-upload-form').onsubmit=event=>{event.preventDefault();action(async()=>{
  const file=$('lab-map-file').files[0];if(!file)return;
  $('lab-upload-submit').disabled=true;$('lab-upload-cancel').disabled=true;I18n.text($('lab-upload-error'),'');
  try{
    if(file.size>80*1024*1024)throw new Error('文件须小于 80 MB。');
    const source=await atlasJSON(`/api/atlas/upload?name=${encodeURIComponent(file.name)}&page=${Number($('lab-map-page').value)}`,{method:'POST',body:file});
    const result=await api('/api/place-maps',{source_id:source.id,title:$('lab-map-title').value});
    await loadCatalog();await loadMap(result.id);$('lab-upload-dialog').close();$('lab-upload-form').reset();
  }catch(e){I18n.text($('lab-upload-error'),e.message);}finally{$('lab-upload-submit').disabled=false;$('lab-upload-cancel').disabled=false;}
});};
$('lab-input').onclick=()=>action(async()=>{
  if(dirty)throw new Error('请先保存人工标注。');
  const r=await fetch(workspaceURL(`/api/atlas/${mid}/place-input?version=${data.map.version}`));
  if(!r.ok)throw new Error((await r.json()).error);
  const url=URL.createObjectURL(await r.blob()),a=document.createElement('a');a.href=url;a.download=mid+'-place-input.zip';a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);
});
$('lab-import').onclick=()=>action(async()=>{
  if(dirty)throw new Error('请先保存人工标注。');
  const file=$('lab-prediction-file').files[0];if(!file||file.size>200000)throw new Error('请选择小于 200 KB 的预测 JSON。');
  data=await api(`/api/atlas/${mid}/place-predictions`,JSON.parse(await file.text()));loadTask();
});
async function loadCatalog(){
  catalog=await api('/api/place-maps');$('lab-home').href=catalog.workspace?.events_url||'/';
  $('lab-map').replaceChildren(...catalog.maps.map(m=>option(m.id,m.active?.title||m.title||m.battle_name||m.id,false)));
  if(!catalog.maps.length)$('lab-map').append(option('','尚无实验地图'));
  if(mid&&!catalog.maps.some(m=>m.id===mid))mid=null;
  if(mid)$('lab-map').value=mid;
}
window.addEventListener('beforeunload',e=>{if(dirty||$('lab-name').value.trim()){e.preventDefault();e.returnValue='';}});
new ResizeObserver(()=>map.invalidateSize()).observe($('lab-canvas'));
lucide.createIcons();action(async()=>{
  await loadCatalog();
  const requested=new URLSearchParams(location.search).get('map');const first=catalog.maps.find(m=>m.id===requested)||catalog.maps[0];
  if(first)await loadMap(first.id);
  else {I18n.text($('lab-empty'),'尚未上传实验地图');loadTask();}
});
