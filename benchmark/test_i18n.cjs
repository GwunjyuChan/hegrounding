const test=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const vm=require('node:vm');
const script=fs.readFileSync(__dirname+'/gui/i18n.js','utf8');
function runtime(saved=null,blocked=false){
  const storage=new Map([['he-language',saved]]);
  const context={module:{exports:{}},localStorage:{getItem:k=>{if(blocked)throw Error();return storage.get(k);},setItem:(k,v)=>{if(blocked)throw Error();storage.set(k,v);}}};
  vm.runInNewContext(script,context);return {i18n:context.module.exports,storage};
}
function element(){return {textContent:'',value:'未保存的人工证据',attrs:{},setAttribute(k,v){this.attrs[k]=v;}};}
test('defaults to English and remembers explicit language preferences',()=>{
  const {i18n,storage}=runtime();assert.equal(i18n.t('事件标注'),'Event annotation');
  assert.equal(runtime('invalid').i18n.language,'en');
  assert.equal(runtime('zh').i18n.language,'zh');
  i18n.setLanguage('zh');assert.equal(storage.get('he-language'),'zh');
  i18n.setLanguage('en');assert.equal(storage.get('he-language'),'en');
  assert.equal(i18n.t('事件标注'),'Event annotation');assert.equal(runtime('en').i18n.language,'en');
  i18n.setLanguage('fr');assert.equal(i18n.language,'en');
});
test('dynamic labels, tooltips and controls switch both ways',()=>{
  const {i18n}=runtime(),el=element();i18n.text(el,'3 / 10 已审核');i18n.attr(el,'保存人工答案','title');
  i18n.setLanguage('en');assert.equal(el.textContent,'3 / 10 reviewed');assert.equal(el.attrs.title,'Save ground truth');
  assert.equal(el.value,'未保存的人工证据');i18n.setLanguage('zh');assert.equal(el.textContent,'3 / 10 已审核');
});
test('composite progress, model output and errors are fully translated',()=>{
  const {i18n}=runtime('en');
  assert.equal(i18n.t('原图坐标：100, 200 · 导入结果'),'Image coordinates: 100, 200 · Imported result');
  assert.equal(i18n.t('4 事件 · 待确认参考底图'),'4 events · Reference map not confirmed');
  assert.equal(i18n.t('已保存 2/4 · 已定位 1 · 未找到 1 · 失败 0'),'Saved 2/4 · Located 1 · Not found 1 · Failed 0');
  assert.equal(i18n.t('用户名或密码错误'),'Incorrect username or password');
});
test('raw research content and custom names are never localized',()=>{
  const {i18n}=runtime(),el=element();i18n.text(el,'选择或新增地名');
  i18n.raw(el,'区域');i18n.setLanguage('en');assert.equal(el.textContent,'区域');
  i18n.text(el,()=> '地图 · '+i18n.t('人工'));assert.equal(el.textContent,'地图 · Human');
  i18n.setLanguage('zh');assert.equal(el.textContent,'地图 · 人工');
});
test('storage unavailable still permits a live switch',()=>{
  const {i18n}=runtime('zh',true);assert.equal(i18n.language,'en');
  i18n.setLanguage('zh');assert.equal(i18n.t('取消'),'取消');
  i18n.setLanguage('en');assert.equal(i18n.t('取消'),'Cancel');
});
test('all UI pages load localization before their application scripts',()=>{
  for(const [html,app] of [['index.html','app.js'],['atlas.html','atlas.js'],['place-lab.html','place-lab.js'],['login.html','login.js']]){
    const source=fs.readFileSync(__dirname+'/gui/'+html,'utf8');
    assert.ok(source.indexOf('i18n.js')<source.indexOf('src="'+(html==='login.html'?'/':'')+app+'"'));
    assert.ok(source.includes('i18n.css'));
  }
});
