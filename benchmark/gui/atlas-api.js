/* Refresh only the security token, never the editor's unsaved data. */
async function atlasJSON(url, options = {}) {
  async function read(response) {
    const data = await response.json();
    if (!response.ok) throw new Error(data.error || '请求失败');
    return data;
  }
  if ((options.method || 'GET').toUpperCase() === 'GET') {
    return read(await fetch(url, options));
  }
  for (let attempt = 0; attempt < 2; attempt++) {
    const session = await read(await fetch('/api/atlas', {cache: 'no-store'}));
    if (typeof session.csrf !== 'string' || !session.csrf) {
      throw new Error('无法获取保存凭证；未保存的修改仍保留在页面中。');
    }
    const response = await fetch(url, {...options,
      headers: {...options.headers, 'X-CSRF-Token': session.csrf}});
    const data = await response.json();
    if (response.ok) return data;
    // This exact rejection happens before any write. Never retry conflicts or network errors.
    if (response.status === 403 && data.error === 'Unauthorized local request') {
      if (attempt === 0) continue;
      throw new Error('保存凭证已失效；未保存的修改仍保留在页面中，请稍后重试。');
    }
    throw new Error(data.error || '请求失败');
  }
}
