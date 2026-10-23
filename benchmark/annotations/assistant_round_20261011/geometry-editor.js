/* Edits are drafts in the human review journal; AI records remain immutable. */
(() => {
  const clone = value => value == null ? null : JSON.parse(JSON.stringify(value));
  const same = (a,b) => JSON.stringify(a) === JSON.stringify(b);
  const histories = new Map(), tools = [...document.querySelectorAll('[data-tool]')];
  let eventId=null, mode='pan', selected=-1, drawing=false, moving=null, preview=undefined;
  const minimum = g => g?.type==='polygon' ? 3 : g?.type==='line' ? 2 : 1;
  // A box is stored as an ordinary 4-vertex polygon, so saving, scoring and the server need nothing new.
  function box(a,b){const [x0,x1]=[a[0],b[0]].sort((m,n)=>m-n),[y0,y1]=[a[1],b[1]].sort((m,n)=>m-n);return {type:'polygon',coordinates:[[x0,y0],[x1,y0],[x1,y1],[x0,y1]]};}
  function isBox(g){
    if(g?.type!=='polygon'||g.coordinates.length!==4)return false;
    const c=g.coordinates;
    return [0,1,2,3].every(i=>{const a=c[i],b=c[(i+1)%4];return (a[0]===b[0])!==(a[1]===b[1]);});
  }
  function bbox(g){const xs=g.coordinates.map(p=>p[0]),ys=g.coordinates.map(p=>p[1]);return box([Math.min(...xs),Math.min(...ys)],[Math.max(...xs),Math.max(...ys)]);}
  // Dragging a box corner keeps it a box: the opposite corner stays, the two neighbours follow.
  function dragBoxCorner(g,i,p){
    const c=g.coordinates,o=c[(i+2)%4],j=(i+1)%4,k=(i+3)%4,sameX=c[j][0]===c[i][0];
    c[i]=p;c[j]=sameX?[p[0],o[1]]:[o[0],p[1]];c[k]=sameX?[o[0],p[1]]:[p[0],o[1]];
  }
  // Explicit null is a cleared human revision, never a fallback to the AI shape.
  function savedGeometry(){return window.reviewFeature ? window.reviewFeature.geometry() : current?.geometry || null;}
  function geom(){return preview !== undefined ? preview : savedGeometry();}
  function enabled(){return !!current && !!currentImage && !referenceMode && !!window.reviewFeature?.canEditGeometry();}
  function history(){if(!histories.has(eventId))histories.set(eventId,{undo:[],redo:[]});return histories.get(eventId);}
  function changed(next){
    if(!enabled() || same(savedGeometry(),next))return;
    const h=history();h.undo.push(clone(savedGeometry()));if(h.undo.length>100)h.undo.shift();h.redo=[];
    window.reviewFeature.editGeometry(clone(next));
    refresh();
  }
  function refresh(){
    if(eventId!==current?.event_id){eventId=current?.event_id;mode='pan';selected=-1;drawing=false;moving=null;preview=undefined;}
    if(referenceMode || !window.reviewFeature?.canEditGeometry()){mode='pan';drawing=false;moving=null;preview=undefined;}
    const on=enabled(), g=geom(), h=history();
    tools.forEach(b=>{b.disabled=b.dataset.tool!=='pan'&&!on;b.setAttribute('aria-pressed',String(mode===b.dataset.tool));});
    $('finish-geometry').disabled=!on || !drawing || !g || g.coordinates.length<minimum(g);
    $('undo-geometry').disabled=!on || !h.undo.length;
    $('redo-geometry').disabled=!on || !h.redo.length;
    $('delete-vertex').disabled=!on || selected<0 || !g || (g.type!=='point'&&g.coordinates.length<=minimum(g));
    $('clear-geometry').disabled=!on || !g;
    $('restore-candidate').disabled=!on || same(g,current?.geometry);
    $('to-box').disabled=!on || drawing || !g || g.type==='point' || g.coordinates.length<2 || isBox(g);
    $('show-human').disabled=referenceMode;
    if(current){
      $('focus').disabled=referenceMode||!g;$('coordinates').textContent=JSON.stringify(g);
      const changed=!same(g,current.geometry);
      $('geometry-type').textContent=`AI: ${current.geometry?.type||'none'}${changed?' / Human: '+(g?.type||'none'):''} · ${current.feature_type}`;
      if(!referenceMode && !current.geometry)$('map-note').textContent=`AI: ${statusLabel(current.status)} · ${g?pick('Human revision present','已有人工修订'):pick('No candidate geometry','没有候选几何')}`;
    }
    $('viewport').classList.toggle('editing',on&&mode!=='pan');
    $('editor-state').textContent=referenceMode ? t('Reference / 参考图') : g ? isBox(g) ? pick('box','矩形') : pick(`${g.type} · ${g.coordinates.length} ${g.coordinates.length===1?'vertex':'vertices'}`,`${{point:'点',line:'线',polygon:'区域'}[g.type]||g.type} · ${g.coordinates.length} 个顶点`) : t('No geometry / 无标注');
    drawOverlay();
  }
  function setMode(next){mode=next;selected=-1;drawing=false;preview=undefined;moving=null;if(next!=='pan')$('show-human').checked=true;refresh();}
  function point(e){const b=$('viewport').getBoundingClientRect();return [(e.clientX-b.left-tx)/scale,(e.clientY-b.top-ty)/scale];}
  function inside(p){return p[0]>=0&&p[1]>=0&&p[0]<current.annotation_image.width&&p[1]<current.annotation_image.height;}
  function bounded(p){return p.map((v,i)=>Math.round(Math.max(0,Math.min((i?current.annotation_image.height:current.annotation_image.width)-.01,v))*100)/100);}
  function nearest(p,g){let best=-1,d=13/scale;g?.coordinates.forEach((q,i)=>{const n=Math.hypot(q[0]-p[0],q[1]-p[1]);if(n<d){best=i;d=n;}});return best;}
  function edge(p,g){
    if(!g||g.type==='point')return null;
    const pts=g.coordinates, count=pts.length-(g.type==='polygon'?0:1);let best=null,d=10/scale;
    for(let i=0;i<count;i++){
      const a=pts[i],b=pts[(i+1)%pts.length],dx=b[0]-a[0],dy=b[1]-a[1],den=dx*dx+dy*dy;
      if(!den)continue;
      const t=Math.max(0,Math.min(1,((p[0]-a[0])*dx+(p[1]-a[1])*dy)/den));
      const q=[a[0]+t*dx,a[1]+t*dy],dist=Math.hypot(q[0]-p[0],q[1]-p[1]);
      if(t>.01&&t<.99&&dist<d){d=dist;best={index:i+1,point:bounded(q)};}
    }
    return best;
  }
  function paint(ctx,g,color,handles=false,dashed=false){
    if(!g||!g.coordinates.length)return;
    const pts=g.coordinates;ctx.save();ctx.lineJoin='round';ctx.lineCap='round';ctx.beginPath();
    if(g.type==='point')ctx.arc(...pts[0],7/scale,0,Math.PI*2);
    else{pts.forEach((p,i)=>i?ctx.lineTo(...p):ctx.moveTo(...p));if(g.type==='polygon'&&pts.length>=3){ctx.closePath();ctx.fillStyle=color+'20';ctx.fill();}}
    ctx.strokeStyle='white';ctx.lineWidth=5/scale;ctx.stroke();ctx.strokeStyle=color;ctx.lineWidth=2.5/scale;
    if(dashed)ctx.setLineDash([7/scale,5/scale]);ctx.stroke();ctx.setLineDash([]);
    if(handles)pts.forEach((p,i)=>{ctx.beginPath();ctx.arc(...p,(i===selected?6:4.5)/scale,0,Math.PI*2);ctx.fillStyle=i===selected?'#f8bd38':'white';ctx.fill();ctx.strokeStyle=color;ctx.lineWidth=2/scale;ctx.stroke();});
    ctx.restore();
  }
  function draw(ctx){
    if(!current||referenceMode)return;
    if($('show-overlay').checked)paint(ctx,current.geometry,current.status==='ambiguous'?'#a85500':'#cc0066',false,current.status==='ambiguous');
    const g=geom();
    if($('show-human').checked && (!same(g,current.geometry)||mode!=='pan'))paint(ctx,g,'#126eaa',mode!=='pan');
  }
  tools.forEach(b=>b.onclick=()=>setMode(b.dataset.tool));
  $('finish-geometry').onclick=()=>{const g=geom();if(g&&g.coordinates.length>=minimum(g))setMode('edit');};
  $('undo-geometry').onclick=()=>{if(!enabled()||!history().undo.length)return;const h=history();h.redo.push(clone(savedGeometry()));window.reviewFeature.editGeometry(h.undo.pop());setMode('edit');};
  $('redo-geometry').onclick=()=>{if(!enabled()||!history().redo.length)return;const h=history();h.undo.push(clone(savedGeometry()));window.reviewFeature.editGeometry(h.redo.pop());setMode('edit');};
  $('clear-geometry').onclick=()=>{changed(null);setMode('edit');};
  $('restore-candidate').onclick=()=>{changed(current.geometry);setMode('edit');};
  $('to-box').onclick=()=>{const g=savedGeometry();if(!g||g.type==='point')return;const b=bbox(g);if(isBox(b)){changed(b);setMode('edit');}};
  $('delete-vertex').onclick=()=>{const g=clone(savedGeometry());if(!g||selected<0)return;if(g.type==='point'){changed(null);}else if(g.coordinates.length>minimum(g)){g.coordinates.splice(selected,1);changed(g);}selected=-1;refresh();};
  $('viewport').addEventListener('pointerdown',e=>{
    if(!enabled()||mode==='pan'||e.button!==0)return;
    const p=point(e);if(!inside(p))return;e.preventDefault();
    if(mode==='edit'){
      const g=clone(savedGeometry());selected=nearest(p,g);
      if(selected>=0){moving={id:e.pointerId,before:g,box:isBox(g)};preview=clone(g);$('viewport').setPointerCapture(e.pointerId);}
      else if(!isBox(g)){const hit=edge(p,g);if(hit){g.coordinates.splice(hit.index,0,hit.point);selected=hit.index;changed(g);}}
    }else if(mode==='rect'){
      const q=bounded(p);moving={id:e.pointerId,start:q};preview=box(q,q);$('viewport').setPointerCapture(e.pointerId);
    }else if(mode==='point'){changed({type:'point',coordinates:[bounded(p)]});setMode('edit');selected=0;}
    else{
      const g=drawing?clone(savedGeometry()):{type:mode,coordinates:[]};
      const q=bounded(p);
      if(!g.coordinates.some(v=>Math.hypot(v[0]-q[0],v[1]-q[1])*scale<3)){g.coordinates.push(q);drawing=true;selected=g.coordinates.length-1;changed(g);}
    }
    refresh();
  });
  $('viewport').addEventListener('pointermove',e=>{
    if(!moving||moving.id!==e.pointerId)return;
    const q=bounded(point(e));
    if(moving.start)preview=box(moving.start,q);
    else if(moving.box)dragBoxCorner(preview,selected,q);
    else preview.coordinates[selected]=q;
    drawOverlay();
  });
  function end(e,cancel){
    if(!moving||moving.id!==e.pointerId)return;
    const next=preview,drag=moving;preview=undefined;moving=null;
    if(drag.start){
      // A click without a drag (or a box thinner than 3 screen pixels) draws nothing.
      const [a,,b]=next.coordinates;
      if(!cancel&&Math.abs(b[0]-a[0])*scale>=3&&Math.abs(b[1]-a[1])*scale>=3){changed(next);setMode('edit');return;}
    }else if(!cancel)changed(next);
    refresh();
  }
  $('viewport').addEventListener('pointerup',e=>end(e,false));
  $('viewport').addEventListener('pointercancel',e=>end(e,true));
  $('viewport').addEventListener('lostpointercapture',e=>end(e,true));
  window.addEventListener('keydown',e=>{
    if(/^(INPUT|TEXTAREA|SELECT)$/.test(e.target.tagName)||e.target.isContentEditable||!enabled())return;
    let button=null;
    if((e.ctrlKey||e.metaKey)&&e.key.toLowerCase()==='z')button=$(e.shiftKey?'redo-geometry':'undo-geometry');
    else if(e.key==='Delete'||e.key==='Backspace')button=$('delete-vertex');
    else if(e.key==='Enter')button=$('finish-geometry');
    else if(e.key==='Escape'){setMode('pan');e.preventDefault();}
    if(button&&!button.disabled){e.preventDefault();button.click();}
  });
  window.geometryEditor={geometry:geom,draw,refresh,active:()=>enabled()&&mode!=='pan',
    busy:()=>!!moving||drawing,reset:()=>{histories.clear();setMode('pan');}};
  refresh();
})();
