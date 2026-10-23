/* Refresh only the security token, never the editor's unsaved data. */
async function atlasJSON(url, options = {}) {
  url = workspaceURL(url);
  async function read(response) {
    if(response.status===401&&typeof window!=='undefined')window.dispatchEvent(new Event('he-session-expired'));
    const data = await response.json();
    if (!response.ok) throw new Error(data.error || '请求失败');
    return data;
  }
  if ((options.method || 'GET').toUpperCase() === 'GET') {
    return read(await fetch(url, options));
  }
  for (let attempt = 0; attempt < 2; attempt++) {
    const session = await read(await fetch(workspaceURL('/api/atlas'), {cache: 'no-store'}));
    if (typeof session.csrf !== 'string' || !session.csrf) {
      throw new Error('无法获取保存凭证；未保存的修改仍保留在页面中。');
    }
    const response = await fetch(url, {...options,
      headers: {...options.headers, 'X-CSRF-Token': session.csrf}});
    const data = await response.json();
    if (response.ok) return data;
    if(response.status===401&&typeof window!=='undefined')window.dispatchEvent(new Event('he-session-expired'));
    // This exact rejection happens before any write. Never retry conflicts or network errors.
    if (response.status === 403 && data.error === 'Unauthorized local request') {
      if (attempt === 0) continue;
      throw new Error('保存凭证已失效；未保存的修改仍保留在页面中，请稍后重试。');
    }
    throw new Error(data.error || '请求失败');
  }
}
