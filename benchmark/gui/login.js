const form=document.getElementById('login-form'),button=document.getElementById('submit'),error=document.getElementById('error');
const next=new URLSearchParams(location.search).get('next')||'/';
form.addEventListener('submit',async event=>{
  event.preventDefault();button.disabled=true;I18n.text(error,'');
  try{
    const response=await fetch('/auth/login',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({username:form.username.value,password:form.password.value,next})});
    const data=await response.json();if(!response.ok)throw new Error(data.error||'登录失败');
    form.password.value='';location.assign(data.next);
  }catch(e){I18n.text(error,e.message||'暂时无法连接，请稍后重试。');}finally{button.disabled=false;}
});
fetch('/auth/session').then(r=>r.json()).then(data=>{if(data.authenticated)document.getElementById('continue').hidden=false;}).catch(()=>{});
