/* Session expiry never discards an annotation draft. */
document.addEventListener('DOMContentLoaded',()=>{
  if(location.protocol!=='https:')return;
  const header=document.querySelector('.app-header');if(!header)return;
  const login=document.createElement('a');I18n.text(login,'重新登录');login.href='/login.html';login.target='_blank';login.rel='noopener';login.hidden=true;login.id='session-login';
  const logout=document.createElement('button');logout.type='button';logout.className='secondary';I18n.text(logout,'退出');I18n.attr(logout,'退出登录','title');
  logout.onclick=async()=>{if(!confirm(I18n.t('退出前请先保存当前修改。确认退出登录？')))return;try{const r=await fetch('/auth/logout',{method:'POST',headers:{'Content-Type':'application/json'},body:'{}'});if(!r.ok)throw new Error();location.assign('/login.html');}catch{login.hidden=false;}};
  header.append(login,logout);
  window.addEventListener('he-session-expired',()=>{login.hidden=false;});
});
