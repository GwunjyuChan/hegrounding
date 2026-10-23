/* Human decisions are saved separately; this module never mutates candidate geometry. */
(() => {
  const key = `hegrounding-human-review:${data.manifest.annotation_decisions_sha256}`;
  const names = {pending:"Pending / 未审核",accepted:"Accepted / 已接受",modified_accepted:"Modified & accepted / 修改后接受",accepted_no_location:"No location on map / 确认图上没有",needs_changes:"Needs changes / 需修改",needs_evidence:"Needs evidence / 待补证据",rejected:"Rejected / 已剔除",stale:"Candidate changed / 待重审"};
  let reviews = {}, versions = {}, csrf = "", connected = false, saving = false, shownId = null;
  let drafts = {}, lastReviewer = "", message = "", messageKind = "";
  let geometryEditing=false;
  async function responseJSON(response) {
    if(response.redirected || response.status===401 || !response.headers.get("content-type")?.includes("application/json")) {
      throw Error("Session expired. Sign in in another tab, then reload reviews / 登录已过期，请在新标签页登录，再重新读取审核。");
    }
    return response.json();
  }
  const clone=value=>value==null?null:JSON.parse(JSON.stringify(value));
  try {drafts = JSON.parse(sessionStorage.getItem(key) || "{}");lastReviewer = localStorage.getItem("hegrounding-reviewer") || "";} catch {}
  const buttons = [...document.querySelectorAll("[data-decision]")];

  function persist() {
    try {sessionStorage.setItem(key, JSON.stringify(drafts));localStorage.setItem("hegrounding-reviewer", lastReviewer);} catch {}
  }
  function savedState(id) {
    const saved = reviews[id];
    return !saved ? "pending" : saved.candidate_sha256 !== versions[id] ? "stale" : saved.decision;
  }
  function defaultDraft(id) {
    const saved = reviews[id];
    const source=data.records.find(r=>r.event_id===id);
    // A stale review still starts from the reviewer's own geometry: the image and pixel frame are frozen for this round.
    const geometry=saved && Object.hasOwn(saved,"human_geometry") ? saved.human_geometry : source?.geometry;
    return {decision:savedState(id)==="stale" ? "pending" : saved?.decision || "pending", notes:saved?.notes || "", reviewer:saved?.reviewer || lastReviewer, revision:saved?.revision || 0, candidate_sha256:versions[id], human_geometry:clone(geometry), touched:false};
  }
  function draft(id) {return {...defaultDraft(id),...drafts[id]};}
  function geometry(){
    if(!current)return null;
    const d=draft(current.event_id);
    return d.candidate_sha256===versions[current.event_id] ? d.human_geometry : current.geometry;
  }
  function geometryChanged(){return current && JSON.stringify(geometry())!==JSON.stringify(current.geometry);}
  function canEditGeometry(){return connected&&geometryEditing&&!!current&&!saving&&draft(current.event_id).candidate_sha256===versions[current.event_id];}
  function stash() {
    if (!shownId || !connected || !drafts[shownId]) return;
    drafts[shownId].reviewer = $("reviewer").value;
    drafts[shownId].notes = $("review-notes").value;
    persist();
  }
  // Messages are kept untranslated ("English / 中文" or a function) so a language switch can repaint them.
  function paintMessage() {$("review-message").textContent=typeof message==="function" ? message() : t(message);$("review-message").dataset.kind=messageKind;}
  function showMessage(text, kind="") {message=text;messageKind=kind;paintMessage();}
  function controls() {
    const canEdit = connected && !!current && !saving;
    const d = current ? draft(current.event_id) : null;
    for (const button of buttons) {
      button.disabled = !canEdit || (button.dataset.decision==="accepted" && (!geometry() || geometryChanged())) ||
        (button.dataset.decision==="modified_accepted" && (!canEditGeometry() || !geometry() || !geometryChanged())) ||
        (button.dataset.decision==="accepted_no_location" && !!geometry());
      button.setAttribute("aria-pressed", String(d?.decision===button.dataset.decision));
    }
    for (const id of ["reviewer","review-notes","review-reset"]) $(id).disabled=!canEdit;
    $("review-save").disabled=!canEdit || !d?.touched;
    $("review-save-next").disabled=!canEdit || !d?.touched;
    $("review-reload").disabled=saving || location.protocol==="file:";
    // Saving binds a snapshot to one event; navigation is available again after it finishes.
    if (saving) for (const id of ["previous","next","event-select","map-filter","status-filter","review-filter"]) $(id).disabled=true;
    else {
      for (const id of ["map-filter","status-filter","review-filter"]) $(id).disabled=false;
      $("event-select").disabled=!current;
      const i=filtered.indexOf(current);$("previous").disabled=i<=0;$("next").disabled=i<0 || i===filtered.length-1;
    }
    const reviewed = data.records.filter(r => !["pending","stale"].includes(savedState(r.event_id))).length;
    $("review-progress").textContent=connected ? `${reviewed} / ${data.records.length}` : "";
    window.geometryEditor?.refresh();
  }
  function render() {
    if (!current) return;
    shownId=current.event_id;
    const d=draft(shownId);
    $("reviewer").value=d.reviewer || "";$("review-notes").value=d.notes || "";
    $("live-review-link").hash=shownId;
    if (location.protocol==="file:") {
      showMessage("Local file, read-only / 本地文件只读");$("live-review-link").classList.remove("hidden");
    } else if (!connected) showMessage(message || "Connecting… / 连接中…",messageKind);
    else if (d.touched) showMessage("Unsaved draft / 未保存草稿");
    else {
      const saved=reviews[shownId];
      const state=savedState(shownId);
      showMessage(saved ? () => `${t(names[state])} · ${new Date(saved.reviewed_at).toLocaleString(L10N.lang==="en"?"en-GB":"zh-CN")}` : names.pending, state==="stale" ? "error" : "");
    }
    const dt=[...$("coordinate-meta").querySelectorAll("dt")].find(n=>n.textContent==="Human review");
    if(dt)dt.nextElementSibling.textContent=t(names[savedState(shownId)]);
    controls();
  }
  function edit(change) {
    if(!current || !connected || saving)return;
    const id=current.event_id;
    drafts[id]={...draft(id),...change,touched:true};
    lastReviewer=drafts[id].reviewer;persist();controls();showMessage("Unsaved draft / 未保存草稿");
  }
  function checkCatalog(payload) {
    if(payload.round_id!==data.manifest.round_id || payload.decisions_sha256!==data.manifest.annotation_decisions_sha256) throw Error("Candidate version changed. Refresh this page / 候选版本已变化，请刷新页面。");
  }
  async function catalog() {
    const response=await fetch("api/reviews",{cache:"no-store"});
    const payload=await responseJSON(response);
    if(!response.ok)throw Error(payload.error || `HTTP ${response.status}`);
    checkCatalog(payload);return payload;
  }
  async function connect() {
    if(location.protocol==="file:"){render();return;}
    try {
      const payload=await catalog();
      reviews=payload.reviews;versions=payload.candidate_versions;csrf=payload.csrf;connected=true;geometryEditing=payload.geometry_editing===true;
      if(current && drafts[current.event_id]?.touched && drafts[current.event_id].candidate_sha256!==versions[current.event_id]) {
        showMessage("Draft belongs to another candidate version. Reset it before saving / 草稿版本不匹配，请重置后审核。","error");
      }
      render();
    } catch(error) {connected=false;showMessage(()=>pick(`Not connected: ${t(error.message)}`,`未连接：${t(error.message)}`),"error");controls();}
  }
  async function save(goNext) {
    if(!current || !connected || saving)return;
    stash();
    const id=current.event_id,d={...draft(id)},index=filtered.indexOf(current),nextId=filtered[index+1]?.event_id;
    if(window.geometryEditor?.busy()){showMessage("Finish drawing before saving / 请先完成绘制。","error");return;}
    if(!d.reviewer.trim()){showMessage("Enter your reviewer name / 请填写审核者。","error");$("reviewer").focus();return;}
    if((["modified_accepted","needs_changes","needs_evidence","rejected"].includes(d.decision) || (d.decision==="accepted" && current.status!=="proposed") || (d.decision==="accepted_no_location" && current.status!=="outside_map")) && !d.notes.trim()) {
      showMessage("Add a reason or required change / 请填写理由或修改要求。","error");$("review-notes").focus();return;
    }
    saving=true;controls();showMessage("Saving… / 保存中…");
    const body={event_id:id,decision:d.decision,notes:d.notes,reviewer:d.reviewer,revision:d.revision,candidate_sha256:d.candidate_sha256};
    if(geometryEditing){body.human_geometry=d.human_geometry;body.image_sha256=current.annotation_image.sha256;}
    async function post(){return fetch("api/reviews",{method:"POST",headers:{"Content-Type":"application/json","X-CSRF-Token":csrf},body:JSON.stringify(body)});}
    try {
      let response=await post();
      if(response.status===403){const payload=await catalog();csrf=payload.csrf;response=await post();}
      const payload=await responseJSON(response);
      if(!response.ok)throw Error(payload.error || `HTTP ${response.status}`);
      reviews[id]=payload.review;delete drafts[id];lastReviewer=d.reviewer;persist();
      saving=false;shownId=null;
      filterEvents(goNext && nextId ? nextId : id);
      showMessage("Saved to disk / 已保存到服务端文件", "success");
    } catch(error) {saving=false;showMessage(()=>pick(`Not saved: ${t(error.message)}`,`未保存：${t(error.message)}`),"error");}
    controls();
  }
  for(const button of buttons)button.onclick=()=>edit({decision:button.dataset.decision});
  $("reviewer").oninput=()=>edit({reviewer:$("reviewer").value});
  $("review-notes").oninput=()=>edit({notes:$("review-notes").value});
  $("review-reset").onclick=()=>{if(!current)return;drafts[current.event_id]={...defaultDraft(current.event_id),decision:"pending",notes:"",reviewer:$("reviewer").value,touched:true};persist();render();};
  $("review-save").onclick=()=>save(false);$("review-save-next").onclick=()=>save(true);
  $("review-filter").onchange=()=>filterEvents(current?.event_id);
  $("review-reload").onclick=async()=>{
    if(Object.values(drafts).some(d=>d.touched) && !confirm(t("Discard unsaved drafts and reload saved reviews? / 放弃未保存草稿并重新读取审核？")))return;
    drafts={};shownId=null;persist();window.geometryEditor?.reset();await connect();filterEvents(current?.event_id);
  };
  window.addEventListener("beforeunload",event=>{stash();if(Object.values(drafts).some(d=>d.touched)){event.preventDefault();event.returnValue="";}});
  window.reviewFeature={stash,render,geometry,canEditGeometry,
    // A changed shape selects 改后接受; the AI shape again, or no shape, clears the decision.
    editGeometry:g=>edit({human_geometry:clone(g),decision:g==null || JSON.stringify(g)===JSON.stringify(current?.geometry) ? "pending" : "modified_accepted"}),
    matches:r=>$("review-filter").value==="all" || savedState(r.event_id)===$("review-filter").value};
  L10N.onChange(paintMessage);
  render();connect();
})();
