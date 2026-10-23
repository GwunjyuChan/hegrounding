"""Build an offline full-resolution viewer from existing, immutable results."""
import base64
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
sys.path.insert(0, str(ROOT / "benchmark"))
from run_atlas_vlm import read_package

TEMPLATE = r'''<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Zurich | 三模型高清对比</title><style>
*{box-sizing:border-box}body{margin:0;color:#20272d;background:#f6f7f8;font:14px system-ui,-apple-system,sans-serif;letter-spacing:0}
header{padding:12px 18px;border-bottom:1px solid #d4dae0;background:white;display:flex;align-items:center;justify-content:space-between;gap:12px;flex-wrap:wrap}
h1{font-size:18px;margin:0}a{color:#185caf;text-decoration:none}button,select,input{font:inherit}button,select{border:1px solid #c5cdd4;background:white;border-radius:4px;color:inherit;min-height:36px}button{display:inline-flex;align-items:center;justify-content:center;width:36px;flex:0 0 36px;cursor:pointer}button:hover{background:#eaf1f5}button:disabled{opacity:.35;cursor:default}button svg{width:18px;height:18px}button:focus-visible,select:focus-visible,input:focus-visible{outline:2px solid #1774cd;outline-offset:2px}select{max-width:100%;padding:5px 26px 5px 9px}
.toolbar{display:flex;align-items:center;gap:8px;padding:10px 18px;background:#fff;border-bottom:1px solid #d4dae0;flex-wrap:wrap}.group{display:flex;align-items:center;gap:6px;max-width:100%}.separator{height:24px;border-left:1px solid #d4dae0}.zoom{width:110px}.zoom-value{width:48px;font-variant-numeric:tabular-nums}.legend{display:flex;gap:12px;align-items:center;margin-left:auto;flex-wrap:wrap}label{display:flex;gap:5px;align-items:center;white-space:nowrap}.swatch{width:12px;height:12px;display:inline-block;background:#d42846}.muted{color:#596975;font-size:12px}
.context{padding:12px 18px;background:#fff;border-bottom:1px solid #cbd2d8}.question{margin:0;line-height:1.5;overflow-wrap:anywhere}.context details{margin-top:8px;max-width:1100px}.context summary{cursor:pointer;font-size:12px;color:#576571}.passage{line-height:1.65;white-space:pre-wrap;max-height:180px;overflow:auto;overflow-wrap:anywhere}.status{color:#8d451a;font-size:12px;margin:7px 0 0}.status:empty{display:none}
.panels{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:1px;background:#c7cfd7;height:calc(100dvh - 220px);min-height:400px}.panels.single{grid-template-columns:minmax(0,1fr)}.panel{min-width:0;background:#fff;display:flex;flex-direction:column;overflow:hidden}.panel[hidden]{display:none}.panel-header{height:64px;flex:0 0 64px;padding:10px 14px;border-bottom:1px solid #cbd2d8;display:flex;gap:8px;align-items:center;justify-content:space-between}.panel-name{font-weight:650;display:flex;align-items:center;gap:8px}.metric{font-size:12px;color:#566572;margin-top:5px;overflow-wrap:anywhere}.canvas-wrap{position:relative;flex:1;min-height:0;overflow:hidden;background:#e5e9ec}canvas{display:block;width:100%;height:100%;touch-action:none;cursor:grab}canvas:active{cursor:grabbing}.notice{position:absolute;bottom:14px;left:14px;right:14px;background:rgba(255,255,255,.95);padding:10px 12px;border-left:3px solid #a34a15;line-height:1.45;font-size:13px;pointer-events:none;overflow-wrap:anywhere}.notice:empty{display:none}footer{padding:9px 18px;font-size:12px;color:#5e6974;display:flex;justify-content:space-between;gap:10px;flex-wrap:wrap}
@media(max-width:700px){header,.toolbar,.context{padding-left:12px;padding-right:12px}.panels{height:65dvh;min-height:390px}.panels:not(.single){grid-template-columns:1fr;height:auto}.panels:not(.single) .panel{height:450px}.legend{margin-left:0}.separator{display:none}.zoom{width:85px}h1{font-size:16px}.panel-header{padding:8px 12px}}
</style></head><body>
<header><h1>苏黎世 · 三模型对比</h1><a href="RESULTS.md">实验报告</a></header>
<div class="toolbar">
<div class="group"><button id="prev" title="上一题" aria-label="上一题"><i data-lucide="chevron-left"></i></button><select id="event" aria-label="事件"></select><button id="next" title="下一题" aria-label="下一题"><i data-lucide="chevron-right"></i></button></div>
<span class="separator"></span><select id="view" aria-label="对比模型"><option value="all">三模型并排</option value="qwen_native">Qwen3-VL</option><option value="gpt5">GPT-5</option><option value="gpt6_astra">GPT-6 Astra</option></select>
<div class="group"><button id="zoom-out" title="缩小" aria-label="缩小"><i data-lucide="zoom-out"></i></button><input class="zoom" id="zoom" type="range" min="10" max="400" value="100" aria-label="缩放比例"><button id="zoom-in" title="放大" aria-label="放大"><i data-lucide="zoom-in"></i></button><output id="zoom-value" class="zoom-value">100%</output></div>
<div class="group"><button id="focus" title="聚焦人工标注和当前预测" aria-label="聚焦标注"><i data-lucide="focus"></i></button><button id="native" title="原始像素 1:1" aria-label="原始像素 1:1"><i data-lucide="scan"></i></button><button id="fit" title="查看整张地图" aria-label="查看整张地图"><i data-lucide="maximize"></i></button></div>
<div class="legend"><label><input id="gold" type="checkbox" checked><span class="swatch"></span>人工标注</label><label><input id="prediction" type="checkbox" checked>模型预测</label></div>
</div>
<section class="context"><p class="question" id="question"></p><p class="status" id="status"></p><details><summary>史料文本</summary><div class="passage" id="passage"></div></details></section>
<main class="panels" id="panels"></main>
<footer><span>冻结底图 · 1538 × 1754 px</span><span>2026-10-07 / 08 · 人工答案待复核</span></footer>
<script>__LUCIDE__</script><script id="data" type="application/json">__DATA__</script>
<script>
'use strict';
const DATA=JSON.parse(document.getElementById('data').textContent);
const models={qwen_native:{name:'Qwen3-VL · 原像素',color:'#087849'},gpt5:{name:'GPT-5',color:'#874bb1'},gpt6_astra:{name:'GPT-6 Astra',color:'#066ed4'}};
const $=id=>document.getElementById(id), panels=[], image=new Image();
let index=0,scale=1,cx=769,cy=877,ready=false,frame=0;
for(const task of DATA.tasks){const o=document.createElement('option');o.value=task.event_id;o.textContent=task.event_id;$('event').append(o)}
function iconButton(name,title){const b=document.createElement('button');b.title=title;b.setAttribute('aria-label',title);const i=document.createElement('i');i.dataset.lucide=name;b.append(i);return b}
for(const [key,model] of Object.entries(models)){
 const el=document.createElement('section');el.className='panel';el.dataset.model=key;
 const head=document.createElement('div');head.className='panel-header';
 const info=document.createElement('div'),name=document.createElement('div'),dot=document.createElement('span'),metric=document.createElement('div');
 name.className='panel-name';dot.className='swatch';dot.style.background=model.color;name.append(dot,document.createTextNode(model.name));metric.className='metric';info.append(name,metric);
 const download=iconButton('download','下载该模型原分辨率标注图');download.onclick=()=>exportImage(key);head.append(info,download);
 const wrap=document.createElement('div');wrap.className='canvas-wrap';const canvas=document.createElement('canvas');canvas.setAttribute('aria-label',model.name+' 地图');const notice=document.createElement('div');notice.className='notice';wrap.append(canvas,notice);el.append(head,wrap);$('panels').append(el);
 const p={key,el,canvas,metric,notice};panels.push(p);attachNavigation(p);
}
lucide.createIcons();
function activePanels(){return panels.filter(p=>!p.el.hidden)}
function current(){return DATA.tasks[index].event_id}
function row(key){return DATA.rows[key][current()]}
function metric(r){if(r.status==='error')return '输出错误 · '+r.error_type;if(r.status==='abstained')return '拒答';if(r.excluded_from_spatial_scoring)return '不计入主要空间评分';if(r.outside_map_abstention===false)return '目标在图外 · 仍给出位置';if(r.point_inside_gold===true)return '落入人工标注区域';if(r.distance_to_gold_px!==undefined)return (r.point_inside_gold===false?'距人工区域 ':'距人工点 ')+r.distance_to_gold_px.toFixed(1)+' px';return '几何类型不同 · 未评分'}
function redraw(){if(!frame)frame=requestAnimationFrame(()=>{frame=0;draw()})}
function geometry(ctx,g,color,transform,pointStyle){
 if(!g)return;const pts=g.coordinates.map(p=>transform(p));ctx.save();ctx.strokeStyle=color;ctx.fillStyle=color;ctx.lineWidth=2.5;
 if(g.type==='point'){const [x,y]=pts[0];ctx.beginPath();if(pointStyle==='cross'){ctx.moveTo(x-10,y);ctx.lineTo(x+10,y);ctx.moveTo(x,y-10);ctx.lineTo(x,y+10)}else{ctx.arc(x,y,7,0,Math.PI*2)}ctx.stroke();}
 else{ctx.beginPath();pts.forEach(([x,y],i)=>i?ctx.lineTo(x,y):ctx.moveTo(x,y));if(g.type==='polygon'){ctx.closePath();ctx.globalAlpha=.08;ctx.fill();ctx.globalAlpha=1}ctx.stroke()}
 ctx.restore();
}
function draw(){if(!ready)return;for(const p of activePanels()){
 const rect=p.canvas.getBoundingClientRect(),dpr=window.devicePixelRatio||1,w=rect.width,h=rect.height;if(!w||!h)continue;
 if(p.canvas.width!==Math.round(w*dpr)||p.canvas.height!==Math.round(h*dpr)){p.canvas.width=Math.round(w*dpr);p.canvas.height=Math.round(h*dpr)}
 const ctx=p.canvas.getContext('2d');ctx.setTransform(dpr,0,0,dpr,0,0);ctx.clearRect(0,0,w,h);ctx.imageSmoothingEnabled=true;ctx.imageSmoothingQuality='high';
 const x=w/2-cx*scale,y=h/2-cy*scale;ctx.drawImage(image,x,y,image.width*scale,image.height*scale);
 const t=([a,b])=>[x+a*scale,y+b*scale];if($('gold').checked)geometry(ctx,DATA.gold[current()].geometry,'#d42846',t,'cross');if($('prediction').checked)geometry(ctx,row(p.key).geometry,models[p.key].color,t,'circle');
 }$('zoom').value=scale*100;$('zoom-value').textContent=Math.round(scale*100)+'%'}
function setScale(value){scale=Math.max(.1,Math.min(4,value));redraw()}
function fitBounds(points){const visible=activePanels();if(!visible.length)return;const sizes=visible.map(p=>p.canvas.getBoundingClientRect());
 const xs=points.map(p=>p[0]),ys=points.map(p=>p[1]);const left=Math.min(...xs),right=Math.max(...xs),top=Math.min(...ys),bottom=Math.max(...ys);
 cx=(left+right)/2;cy=(top+bottom)/2;setScale(Math.min(2,Math.min(...sizes.map(r=>r.width-64))/Math.max(240,right-left+100),Math.min(...sizes.map(r=>r.height-100))/Math.max(240,bottom-top+100)));
 const hw=Math.max(...sizes.map(r=>r.width))/2/scale,hh=Math.max(...sizes.map(r=>r.height))/2/scale;
 cx=2*hw<image.width?Math.max(hw,Math.min(image.width-hw,cx)):image.width/2;
 cy=2*hh<image.height?Math.max(hh,Math.min(image.height-hh,cy)):image.height/2;}
function focus(){let pts=DATA.gold[current()].geometry?.coordinates.slice()||[];for(const p of activePanels())pts=pts.concat(row(p.key).geometry?.coordinates||[]);fitBounds(pts.length?pts:[[0,0],[image.width,image.height]])}
function update(){const task=DATA.tasks[index];$('event').value=task.event_id;$('prev').disabled=index===0;$('next').disabled=index===DATA.tasks.length-1;$('question').textContent=task.event_id+' · '+task.question;$('passage').textContent=task.text;
 $('status').textContent=DATA.excluded.includes(current())?'人工答案粒度待复核 · 已排除主要空间评分':DATA.gold[current()].status==='outside_map'?'该目标在冻结底图范围之外':'';
 for(const p of panels){const r=row(p.key);p.metric.textContent=metric(r);p.notice.textContent=r.status==='error'?(p.key==='gpt6_astra'&&current()==='Z0001'?'坐标数组格式错误；原始响应保留，未绘制预测。':'没有合法的预测几何。'):r.status==='abstained'?'模型返回拒答，未给出位置。':r.unscored_geometry_pair?'模型输出区域，人工答案为点；不计入点误差。':''}
 focus();
}
function setView(){for(const p of panels)p.el.hidden=$('view').value!=='all'&&$('view').value!==p.key;$('panels').classList.toggle('single',$('view').value!=='all');requestAnimationFrame(focus)}
function attachNavigation(p){let drag=null;p.canvas.addEventListener('pointerdown',e=>{if(e.button!==0)return;p.canvas.setPointerCapture(e.pointerId);drag={id:e.pointerId,x:e.clientX,y:e.clientY,cx,cy}});
 p.canvas.addEventListener('pointermove',e=>{if(!drag||drag.id!==e.pointerId)return;cx=drag.cx-(e.clientX-drag.x)/scale;cy=drag.cy-(e.clientY-drag.y)/scale;redraw()});for(const type of ['pointerup','pointercancel','lostpointercapture'])p.canvas.addEventListener(type,()=>drag=null);
 p.canvas.addEventListener('wheel',e=>{e.preventDefault();const r=p.canvas.getBoundingClientRect(),dx=e.clientX-r.left-r.width/2,dy=e.clientY-r.top-r.height/2,old=scale;setScale(scale*Math.exp(-e.deltaY*.002));cx+=dx/old-dx/scale;cy+=dy/old-dy/scale;redraw()},{passive:false});
}
function exportImage(key){const c=document.createElement('canvas');c.width=image.width;c.height=image.height;const ctx=c.getContext('2d');ctx.drawImage(image,0,0);if($('gold').checked)geometry(ctx,DATA.gold[current()].geometry,'#d42846',p=>p,'cross');if($('prediction').checked)geometry(ctx,row(key).geometry,models[key].color,p=>p,'circle');c.toBlob(blob=>{const url=URL.createObjectURL(blob),a=document.createElement('a');a.href=url;a.download=current()+'_'+key+'_1538x1754.png';a.click();setTimeout(()=>URL.revokeObjectURL(url),1000)},'image/png')}
$('prev').onclick=()=>{if(index>0){index--;update()}};$('next').onclick=()=>{if(index<DATA.tasks.length-1){index++;update()}};$('event').onchange=()=>{index=DATA.tasks.findIndex(t=>t.event_id===$('event').value);update()};$('view').onchange=setView;
$('zoom').oninput=()=>setScale(Number($('zoom').value)/100);$('zoom-in').onclick=()=>setScale(scale*1.25);$('zoom-out').onclick=()=>setScale(scale/1.25);$('native').onclick=()=>setScale(1);$('fit').onclick=()=>fitBounds([[0,0],[image.width,image.height]]);$('focus').onclick=focus;for(const id of ['gold','prediction'])$(id).onchange=redraw;
new ResizeObserver(redraw).observe($('panels'));for(const p of panels)new ResizeObserver(redraw).observe(p.canvas);
if(matchMedia('(max-width:700px)').matches)$('view').value='gpt6_astra';
image.onload=()=>{ready=true;setView();update()};image.onerror=()=>{$('status').textContent='地图加载失败'};image.src=DATA.image;
</script></body></html>'''


def main():
    report = json.loads((HERE / "review/diagnostics.json").read_text())
    gold = json.loads((HERE / "review/gold_snapshot.json").read_text())
    manifest, png, tasks, _ = read_package(HERE / "input.zip")
    assert manifest["image_sha256"] == report["map"]["image_sha256"] == gold["map"]["image_sha256"]
    data = {"tasks": tasks, "rows": report["rows"], "excluded": report["excluded"],
            "gold": {a["event_id"]: a for a in gold["annotations"]},
            "image": "data:image/png;base64," + base64.b64encode(png).decode()}
    icons = (ROOT / "benchmark/gui/vendor/lucide.js").read_text()
    html = TEMPLATE.replace("__LUCIDE__", icons).replace("__DATA__", json.dumps(data, ensure_ascii=False).replace("<", "\\u003c"))
    path = HERE / "review/comparison.html"
    path.write_text(html)
    print(path)


if __name__ == "__main__":
    main()
