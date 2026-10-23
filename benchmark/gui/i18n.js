/* Only UI labels are bound. Inputs, research passages and saved data are never translated. */
const I18n = (() => {
  const en = {
    '历史地图实验平台':'Historical Map Lab','登录实验平台':'Sign in','用户名':'Username','密码':'Password','登录':'Sign in',
    '已登录，返回实验平台':'Already signed in. Open the lab','HE 平台首页':'HE home','历史事件与地名定位':'Event and place-name grounding',
    '重新登录':'Sign in again','退出':'Sign out','退出登录':'Sign out','返回平台首页':'Back to home',
    '返回工作区主页':'Back to workspace home','返回战场地图':'Back to battle overview','标注工作区':'Annotation workspace',
    '历史事件工作区':'Historical event workspace','地名实验工作区':'Place-name workspace','独立实验工作区':'Independent workspace',
    '欧洲战场':'European battlefields','标注工具':'Annotation tools','历史事件':'Historical events','历史事件标注':'Historical event annotation',
    '地名实验':'Place-name lab','战场地图':'Battle maps','实验地图':'Experiment maps','事件':'Events','图组':'Maps','地名样本':'Place names',
    '欧洲战场地图':'European battlefield map','欧洲全图':'Fit Europe','法国革命与拿破仑战争':'French Revolutionary and Napoleonic Wars',
    '公共领域边界':'Public-domain boundaries','事件标注':'Event annotation','刷新':'Refresh','参考地图':'Reference maps',
    '事件筛选':'Filter events','全部事件':'All events','待审核':'Pending','已通过':'Accepted','范围外':'Outside map','选择战役':'Select a battle',
    '标注进度':'Annotation workflow','1 选定底图':'1 Select basemap','2 事件标注':'2 Annotate events','编辑底图':'Edit basemap',
    '参考图全图':'Fit reference map','作战部署参考地图':'Reference deployment map','裁切原图':'Crop source image','底图全图':'Fit basemap',
    '标注底图画布':'Annotation map canvas','尚未导入底图':'No basemap imported','地图工具':'Map tools','平移':'Pan','框选裁切区域':'Crop region',
    '点':'Point','线':'Line','区域':'Polygon','撤销':'Undo','重做':'Redo','清空当前几何':'Clear geometry','对照参考图':'Show reference',
    '人工标注':'Human annotation','模型预测图层':'Model prediction layers','底图':'Basemap','选定标注底图':'Select an annotation map',
    '当前：战役参考地图':'Current: battle reference map','使用当前参考图并开始标注':'Use reference map and annotate',
    '上传其他底图':'Upload another map','编辑标注底图':'Edit annotation map','取消底图编辑':'Cancel map editing','底图来源':'Map source',
    '选择已导入图像':'Select an imported image','当前战役参考地图':'Current battle reference map','导入 PDF / 图像':'Import PDF / image',
    'PDF 页码（含封面）':'PDF page (including cover)','导入':'Import','底图名称':'Map name','左 x':'Left x','上 y':'Top y',
    '右 x':'Right x','下 y':'Bottom y','顺时针旋转':'Clockwise rotation','长边上限 px':'Max edge (px)',
    '来源 / 年代 / 范围备注':'Source / date / extent notes','确认底图并开始标注':'Confirm map and annotate','底图历史':'Map history',
    '恢复选定底图':'Restore selected map','选择事件':'Select an event','上一条':'Previous','下一条':'Next','原文与资料':'Source text and references',
    '原文网站':'Source website','审核状态':'Review status','通过':'Accepted','有歧义':'Ambiguous','无法定位':'Unlocatable','剔除':'Rejected',
    '要素类型':'Feature type','容差 px':'Tolerance (px)','人工标注置信度':'Annotation confidence','未审核':'Not reviewed',
    '1 · 非常不确定':'1 · Very uncertain','2 · 不确定':'2 · Uncertain','3 · 尚可':'3 · Moderate','4 · 较有把握':'4 · Confident','5 · 非常有把握':'5 · Very confident',
    '证据 / 审核理由':'Evidence / review notes','标注者':'Annotator','保存人工标注':'Save annotation','结果图模型':'Result model',
    'VLM 输入包':'VLM input package','人工答案':'Human ground truth','人工结果图':'Human overlay','模型结果图':'Model overlay',
    '模型预测 JSON':'Prediction JSON','导入模型预测':'Import predictions','尚有未保存的修改':'Unsaved changes','未保存的修改':'Unsaved changes',
    '取消':'Cancel','继续':'Continue','未保存修改':'Unsaved changes','未保存':'Unsaved','无结果':'No result','拒答':'Abstained',
    '暂无模型预测':'No model predictions','待确认参考底图':'Reference map not confirmed','标注底图':'Annotation map',
    '参考底图 · 可能含作战部署':'Reference map · may contain deployments','底图草稿':'Map draft','已选底图':'Selected map',
    '参考图 · 待确认':'Reference map · awaiting confirmation','无逐字原文':'No verbatim source text','正在导入…':'Importing…',
    '桥梁':'Bridge','浅滩':'Ford','河岸':'River bank','河流':'River','道路':'Road','交叉口':'Junction','林地':'Woodland','高地':'High ground',
    '开阔地':'Open ground','聚落':'Settlement','建筑':'Building','其他':'Other','地图':'Map','上传实验地图':'Upload experiment map',
    '选择地名':'Select a place name','全图':'Fit map','地名实验地图':'Place-name experiment map','未设置底图':'No map selected',
    '地名标注工具':'Place-name annotation tools','地名文字中心点':'Label center point','地名文字区域':'Label region',
    '清空人工几何':'Clear human geometry','模型预测':'Model predictions','地名文字定位':'Printed-label localization','地名':'Place names',
    '新增地名':'Add place name','置信度':'Confidence','点容差 px':'Point tolerance (px)','标注备注':'Annotation notes',
    '保存人工答案':'Save ground truth','预测结果':'Prediction results','预测批次':'Prediction batch','导出整图实验 JSON':'Export experiment JSON',
    '批量预测文件':'Batch prediction files','导出预测输入包':'Export model input','模型结果 JSON':'Model result JSON','导入预测结果':'Import results',
    '取消上传':'Cancel upload','地图名称':'Map name','地图文件':'Map file','上传并开始标注':'Upload and annotate','未预测':'Not predicted',
    '预测失败':'Prediction failed','已定位':'Located','未找到':'Not found','待标注':'Pending','最新批次':'Latest batch','暂无预测':'No predictions',
    '相对':'Normalized','像素':'Pixels','选择或新增地名':'Select or add a place name','模型':'Model','人工':'Human',
    'Qwen3-VL-8B · 本地':'Qwen3-VL-8B · Local',
    '暂无预测结果':'No prediction results','模型未能定位':'Model could not locate the label','导入结果':'Imported result',
    '单点格式已转换':'Point format normalized','本批次无该地名结果':'No result for this label in this batch',
    '人工区域内':'Inside human region','容差内':'Within tolerance','容差外':'Outside tolerance','预测已完成':'Prediction completed',
    '尚无实验地图':'No experiment maps','尚未上传实验地图':'No experiment map uploaded',
    '瑞士':'Switzerland','法国':'France','西班牙':'Spain','葡萄牙':'Portugal','意大利':'Italy','德国':'Germany','奥地利':'Austria',
    '比利时':'Belgium','荷兰':'Netherlands','捷克':'Czechia','波兰':'Poland','俄罗斯':'Russia','白俄罗斯':'Belarus',
    '第二次苏黎世战役':'Second Battle of Zurich','第一次苏黎世战役':'First Battle of Zurich','圣塞巴斯蒂安围城':'Siege of San Sebastian',
    '布萨科战役 · 内伊进攻':'Bussaco · Ney attack','Marengo 战后部署':'Marengo · post-battle deployment','Marengo · 上午部署':'Marengo · morning deployment',
    '布萨科 · 雷尼耶进攻':'Bussaco · Reynier attack','阿尔武埃拉 · 初始部署':'Albuera · initial deployment','奥尔泰兹战役':'Battle of Orthez',
    '图卢兹战役':'Battle of Toulouse','耶拿战役':'Battle of Jena','奥尔施泰特战役':'Battle of Auerstadt','埃伯斯贝格 · 上午部署':'Ebelsberg · morning deployment',
    '瓦格拉姆 · 战后夜间部署':'Wagram · post-battle night deployment','滑铁卢 · 开战部署':'Waterloo · opening deployment',
    '四臂村 · 东侧部署':'Quatre Bras · eastern deployment','弗利辛恩围城':'Siege of Flushing','贝亨奥普佐姆攻城':'Storming of Bergen op Zoom',
    '兹诺伊莫战役':'Battle of Znaim','库尔姆 · 次日部署':'Kulm · second-day deployment','普乌图斯克战役':'Battle of Pultusk',
    '海尔斯贝格 · 前卫战':'Heilsberg · advance-guard action','埃劳战役':'Battle of Eylau','弗里德兰 · 白天部署':'Friedland · daytime deployment',
    '第一次波洛茨克 · 次日':'First Polotsk · second day','别列津纳河渡河':'Crossing of the Berezina','Borkowo 战斗':'Battle of Borkowo',
    'Sochocin 战斗':'Battle of Sochocin','瓦夫尔战役':'Battle of Wavre','依原图标题':'as titled on the source map','夜间':'night','白天至17时':'daytime until 17:00',
    '工作区加载失败':'Could not load workspace','请求失败':'Request failed','登录失败':'Sign-in failed','暂时无法连接，请稍后重试。':'Unable to connect. Please try again.',
    '用户名或密码错误':'Incorrect username or password','请求来源无效':'Invalid request origin','登录请求格式无效':'Invalid login request',
    '用户名或密码格式无效':'Invalid username or password format','登录尝试过于频繁，请五分钟后重试。':'Too many attempts. Try again in five minutes.',
    '登录已过期，请在新标签页登录后重试；当前草稿仍保留。':'Session expired. Sign in in a new tab, then retry. Your draft is preserved.',
    '退出前请先保存当前修改。确认退出登录？':'Save your changes before signing out. Sign out now?',
    '离开会丢弃当前草稿。':'Leaving will discard this draft.','离开会丢弃当前未保存的裁切或事件标注。':'Leaving will discard unsaved crop or annotation changes.',
    '保存后所有事件切换到新底图版本；旧版标注保留，不自动迁移。':'All events will use the new map version. Previous annotations are retained, not transferred.',
    '保存底图版本':'Save map version','恢复底图':'Restore map','恢复选定底图及其已有标注。当前未保存内容将丢弃。':'Restore this map and its annotations? Unsaved changes will be discarded.',
    '底图加载失败，请刷新重试。':'Map failed to load. Refresh and try again.','参考底图已选定':'Reference map selected','原图已导入':'Source image imported',
    '底图已选定，可以标注事件':'Map selected. Ready to annotate.','人工标注已保存；底图图像未改变':'Annotation saved; basemap image unchanged.',
    '模型预测已单独保存':'Predictions saved separately','请选择 PDF 或图像。':'Select a PDF or image.','文件须小于 80 MB。':'File must be under 80 MB.',
    '文件必须小于 80 MB。':'File must be under 80 MB.','请选择预测 JSON。':'Select a prediction JSON file.','预测文件过大。':'Prediction file is too large.',
    '请选择小于 200 KB 的预测 JSON。':'Select a prediction JSON file under 200 KB.','请先保存人工标注。':'Save the annotation first.',
    '请先保存人工答案。':'Save the ground truth first.','请先保存或放弃当前人工标注。':'Save or discard your annotation first.',
    '请先保存或放弃当前修改，再导出已保存结果。':'Save or discard changes before exporting saved results.',
    '请先保存当前人工答案，或切换地名放弃草稿。':'Save the current ground truth, or switch labels to discard the draft.',
    '底图版本已改变，请保存或放弃草稿后刷新。':'Map version changed. Save or discard the draft, then refresh.',
    '结果同步暂不可用，稍后自动重试。':'Result sync unavailable. Retrying shortly.',
    '该模型在此事件上没有可导出的几何。':'No geometry available for this model and event.',
    '未找到此战役，请返回战场地图重新选择。':'Battle not found. Return to the overview and select again.',
    '实验地图宽高不得小于 32 像素。':'Map dimensions must be at least 32 pixels.','请先上传实验地图。':'Upload an experiment map first.',
    '预测文件格式无效。':'Invalid prediction file format.','预测数量无效。':'Invalid number of predictions.','未知或重复的地名 ID。':'Unknown or duplicate place ID.',
    '预测状态与几何不一致。':'Prediction status and geometry do not match.','地名预测须为单点。':'Place predictions must be single points.',
    '底图已改变，请重新打开地名实验。':'Map changed. Reopen the place-name experiment.','人工标注已更新，请刷新后重试。':'Annotation changed. Refresh and retry.',
    '请选择审核状态。':'Select a review status.','地名标注仅支持点或区域。':'Place annotations support points and polygons only.',
    '通过的地名必须有人工标注。':'Accepted labels require an annotation.','置信度须为 1–5 或未审核。':'Confidence must be 1–5 or unreviewed.',
    '像素容差无效。':'Invalid pixel tolerance.','底图校验失败。':'Map checksum verification failed.','未知坐标约定。':'Unknown coordinate convention.',
    '当前底图没有已保存人工标注的地名。':'No saved place annotations on this map.',
    '服务已重启；请检查运行记录后重新预测。':'Server restarted. Check the run history before retrying.',
    '服务正在关闭。':'Server is shutting down.','已有本地地名预测正在运行，请稍后再试。':'A local prediction job is running. Try again later.',
    '本地预测失败或超时；输入和日志已保留，可重新运行。':'Local inference failed or timed out. Inputs and logs are retained for retry.',
    'PDF 页码无效。':'Invalid PDF page.','导入 PDF 需要 Poppler（pdftoppm）；也可导入 PNG/JPEG。':'PDF import needs Poppler (pdftoppm). You can upload PNG/JPEG instead.',
    'PDF 页面读取失败，请检查页码或改用图片。':'Cannot read PDF page. Check the page number or upload an image.',
    '不支持的图像格式或尺寸超过 6000 万像素。':'Unsupported format or image larger than 60 million pixels.','无法读取此图像。':'Cannot read this image.',
    '底图已更新，请刷新地图集。':'Map changed. Refresh the workspace.','裁切框必须是四个整数 [left, top, right, bottom]。':'Crop must contain four integers: [left, top, right, bottom].',
    '裁切框越界或宽高不足 32 像素。':'Crop is outside the image or smaller than 32 pixels.','旋转角度须为 0、90、180、270。':'Rotation must be 0, 90, 180 or 270.',
    '输出长边须在 256–6000 像素之间。':'Maximum output edge must be 256–6000 pixels.','底图已更新，请刷新后再选择参考地图。':'Map changed. Refresh before selecting a reference map.',
    '无效几何类型。':'Invalid geometry type.','无效的几何类型。':'Invalid geometry type.','顶点数量无效。':'Invalid number of vertices.',
    '顶点必须是有限的像素坐标。':'Vertices must be finite pixel coordinates.','顶点必须为有限数值的像素坐标。':'Vertices must be finite pixel coordinates.',
    '底图版本已改变，请重新打开事件。':'Map version changed. Reopen the event.','标注已更新，请重新打开事件。':'Annotation changed. Reopen the event.',
    '置信度须为 1–5 的整数，或留空表示未审核。':'Confidence must be an integer from 1–5, or blank for unreviewed.',
    '要素类型不在统一词表中。':'Feature type is not in the vocabulary.','通过的事件必须有几何标注。':'Accepted events require geometry.',
    '通过的事件必须有地图标注。':'Accepted events require geometry.','范围外事件应清空几何标注。':'Clear geometry for outside-map events.',
    '无效像素容差。':'Invalid pixel tolerance.','底图已更新，请刷新。':'Map changed. Please refresh.','未知底图版本。':'Unknown map version.',
    '预测对应的底图版本不一致。':'Prediction map version does not match.','预测必须是对象。':'Predictions must be objects.',
    '未知事件。':'Unknown event.','预测事件重复。':'Duplicate event predictions.','请先保存标注底图。':'Save an annotation map first.',
    '当前底图没有已通过事件，无法导出评测输入。':'No accepted events on this map to export.','未知叠加层。':'Unknown overlay.','该事件没有可绘制的标注。':'No drawable annotation for this event.',
    '此事件已在其他窗口更新，请重新打开后再保存。':'Event updated in another window. Reopen it before saving.',
    '请选择有效审核状态。':'Select a valid review status.','请填写证据，且不超过 20000 字符。':'Enter evidence, up to 20,000 characters.',
    '请填写标注者姓名。':'Enter the annotator name.','请选择统一词表中的要素类型。':'Select a feature type from the vocabulary.',
    '容差必须是原图范围内的非负像素数。':'Tolerance must be a nonnegative pixel value within the image dimensions.',
    '底图已更新，请刷新后再导出。':'Map changed. Refresh before exporting.','读取本地数据失败，请查看终端。':'Cannot read data. Check the server logs.',
    '请求过大或为空。':'Request is too large or empty.','保存失败，请检查磁盘和文件权限。':'Save failed. Check disk space and permissions.',
    '无法获取保存凭证；未保存的修改仍保留在页面中。':'Cannot obtain a save token. Your draft remains on this page.',
    '保存凭证已失效；未保存的修改仍保留在页面中，请稍后重试。':'Save token expired. Your draft is preserved. Please retry.',
    '放大':'Zoom in','缩小':'Zoom out'
  };
  const patterns = [
    [/^(\d+) 张参考地图$/, '$1 reference maps'], [/^(\d+) \/ (\d+) 已审核$/, '$1 / $2 reviewed'],
    [/^(\d+) 已审核$/, '$1 reviewed'], [/^(\d+) 已通过$/, '$1 accepted'], [/^(\d+) 事件$/, '$1 events'],
    [/^底图 ([a-f0-9]+)$/, 'Map $1'], [/^当前$/, 'Current'], [/^第 (\d+) 页$/, 'Page $1'],
    [/^原图坐标：(.+)$/, 'Image coordinates: $1'], [/^距人工区域 ([\d.]+) px$/, '$1 px from human region'],
    [/^距人工点 ([\d.]+) px$/, '$1 px from human point'], [/^已保存 (\d+)\/(\d+)$/, 'Saved $1/$2'],
    [/^已定位 (\d+)$/, 'Located $1'], [/^未找到 (\d+)$/, 'Not found $1'], [/^失败 (\d+)$/, 'Failed $1'],
    [/^批量预测中$/, 'Batch inference running'], [/^([\d–]+)时$/, '$1 h'], [/^请填写有效的 (.+)。$/, 'Enter a valid $1.']
  ];
  let language='en';
  try {language=localStorage.getItem('he-language')==='zh'?'zh':'en';} catch {}
  const bindings=new WeakMap(), targets=new Set(), staticBindings=[];
  const translate=value=>{
    const source=String(value??'');if(language==='zh')return source;
    if(Object.hasOwn(en,source))return en[source];
    if(source.includes(' · '))return source.split(' · ').map(translate).join(' · ');
    for(const [pattern,replacement] of patterns)if(pattern.test(source))return source.replace(pattern,replacement);
    return source;
  };
  function bind(el,value,attribute=null){
    let fields=bindings.get(el);if(!fields){fields=new Map();bindings.set(el,fields);targets.add(new WeakRef(el));}
    fields.set(attribute,value);paint(el,value,attribute);return el;
  }
  function paint(el,value,attribute){
    const output=typeof value==='function'?value():translate(value);
    if(attribute)el.setAttribute(attribute,output);else el.textContent=output;
  }
  function capture(root){
    // Run once on HTML before application scripts insert any research content.
    const walker=document.createTreeWalker(root,NodeFilter.SHOW_TEXT);
    while(walker.nextNode()){
      const node=walker.currentNode,source=node.nodeValue;
      if(node.parentElement.closest('script,style,textarea,[data-no-i18n]')||!source.trim())continue;
      if(Object.hasOwn(en,source.trim())||source.trim().startsWith('HE · '))staticBindings.push([node,source]);
    }
    for(const el of root.querySelectorAll('[title],[aria-label],[placeholder]'))for(const key of ['title','aria-label','placeholder']){
      const value=el.getAttribute(key);if(value&&Object.hasOwn(en,value))bind(el,value,key);
    }
  }
  function apply(){
    if(typeof document!=='undefined')document.documentElement.lang=language==='en'?'en':'zh-CN';
    for(const [node,source] of staticBindings)if(node.isConnected)node.nodeValue=source.replace(source.trim(),translate(source.trim()));
    for(const ref of targets){const el=ref.deref();if(!el){targets.delete(ref);continue;}for(const [key,value] of bindings.get(el))paint(el,value,key);}
    const select=typeof document!=='undefined'&&document.getElementById('language-select');if(select)select.value=language;
  }
  function setLanguage(value){
    if(!['zh','en'].includes(value))return;
    language=value;try{localStorage.setItem('he-language',value);}catch{}
    apply();if(typeof window!=='undefined')window.dispatchEvent(new Event('he-language-change'));
  }
  if(typeof document!=='undefined'){
    capture(document.documentElement);
    const header=document.querySelector('.app-header,body>header');
    if(header){
      const select=document.createElement('select');select.id='language-select';select.className='language-select';
      select.setAttribute('aria-label','界面语言 / Interface language');select.title='界面语言 / Interface language';
      for(const [value,label] of [['zh','中文'],['en','English']]){const o=document.createElement('option');o.value=value;o.textContent=label;select.append(o);}
      select.onchange=()=>setLanguage(select.value);header.append(select);
    }
    apply();
    window.addEventListener('storage',event=>{if(event.key==='he-language'&&['zh','en'].includes(event.newValue)){language=event.newValue;apply();}});
  }
  function mapControls(map){for(const [selector,key] of [['.leaflet-control-zoom-in','放大'],['.leaflet-control-zoom-out','缩小']]){const el=map.getContainer().querySelector(selector);if(el){bind(el,key,'title');bind(el,key,'aria-label');}}}
  return {t:translate,text:(el,value)=>bind(el,value),raw:(el,value)=>{bindings.get(el)?.delete(null);el.textContent=value;},attr:bind,apply,setLanguage,mapControls,get language(){return language;},en};
})();
if(typeof module!=='undefined')module.exports=I18n;
