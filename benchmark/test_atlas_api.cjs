const {test} = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const path = require('node:path');
const source = fs.readFileSync(path.join(__dirname, 'gui/atlas-api.js'), 'utf8');
const urlSource = fs.readFileSync(path.join(__dirname, 'gui/workspace-url.js'), 'utf8');
const response = (status, data) => ({ok: status === 200, status, json: async () => data});
function client(queue, baseURI = 'http://localhost:8767/') {
  const calls = [];
  const context = vm.createContext({URL, document: {baseURI}, fetch: async (url, options) => {
    calls.push({url, options});
    assert.ok(queue.length, 'Unexpected request');
    const item = queue.shift();
    if (item instanceof Error) throw item;
    return item;
  }});
  vm.runInContext(urlSource + '\n' + source, context);
  return {request: context.atlasJSON, calls};
}

test('GET does not fetch a session separately', async () => {
  const c = client([response(200, {maps: []})]);
  assert.deepEqual(await c.request('/api/atlas'), {maps: []});
  assert.equal(c.calls.length, 1);
});

test('mounted workspace keeps session and writes in the same dataset', async () => {
  const c = client([response(200, {csrf: 'labels'}), response(200, {saved: true})],
    'https://experiment.chanlukaka.com/labels/');
  await c.request('/api/atlas/map/gold', {method: 'POST', body: 'draft'});
  assert.equal(c.calls[0].url, 'https://experiment.chanlukaka.com/labels/api/atlas');
  assert.equal(c.calls[1].url, 'https://experiment.chanlukaka.com/labels/api/atlas/map/gold');
});
test('save refreshes token while preserving submitted draft and revision', async () => {
  const c = client([response(200, {csrf: 'fresh'}), response(200, {saved: true})]);
  const body = JSON.stringify({base_revision: 'old-revision', evidence: 'unsaved edit'});
  const options = {method: 'POST', headers: {'Content-Type': 'application/json', 'X-CSRF-Token': 'old'}, body};
  await c.request('/api/atlas/map/gold', options);
  assert.equal(c.calls[0].options.cache, 'no-store');
  assert.equal(c.calls[1].options.headers['X-CSRF-Token'], 'fresh');
  assert.equal(c.calls[1].options.body, body);
  assert.equal(options.headers['X-CSRF-Token'], 'old');
});
test('one safe retry if server restarts between token fetch and POST', async () => {
  const c = client([response(200, {csrf: 'before'}), response(403, {error: 'Unauthorized local request'}),
    response(200, {csrf: 'after'}), response(200, {saved: true})]);
  await c.request('/api/atlas/map/gold', {method: 'POST', body: 'draft'});
  assert.equal(c.calls.length, 4);
  assert.equal(c.calls[3].options.headers['X-CSRF-Token'], 'after');
  assert.equal(c.calls[3].options.body, 'draft');
});
test('repeated unauthorized errors stop after one retry', async () => {
  const c = client([response(200, {csrf: 'one'}), response(403, {error: 'Unauthorized local request'}),
    response(200, {csrf: 'two'}), response(403, {error: 'Unauthorized local request'})]);
  await assert.rejects(c.request('/api/atlas/map/gold', {method: 'POST'}), /未保存的修改仍保留/);
  assert.equal(c.calls.length, 4);
});
for (const status of [400, 409, 500]) {
  test(`does not retry ${status} or replace the revision`, async () => {
    const c = client([response(200, {csrf: 'fresh'}), response(status, {error: 'failure'})]);
    await assert.rejects(c.request('/api/atlas/map/gold', {method: 'POST', body: 'draft'}), /failure/);
    assert.equal(c.calls.length, 2);
  });
}
test('does not retry network errors that might follow a successful write', async () => {
  const c = client([response(200, {csrf: 'fresh'}), new Error('Connection lost')]);
  await assert.rejects(c.request('/api/atlas/map/gold', {method: 'POST'}), /Connection lost/);
  assert.equal(c.calls.length, 2);
});
test('upload preserves binary body without forcing JSON content type', async () => {
  const body = new Uint8Array([1, 2, 3]);
  const c = client([response(200, {csrf: 'fresh'}), response(200, {id: 'source'})]);
  await c.request('/api/atlas/upload', {method: 'POST', body});
  assert.equal(c.calls[1].options.body, body);
  assert.equal(c.calls[1].options.headers['Content-Type'], undefined);
});
test('missing session token never sends the draft', async () => {
  const c = client([response(200, {})]);
  await assert.rejects(c.request('/api/atlas/map/gold', {method: 'POST'}), /无法获取保存凭证/);
  assert.equal(c.calls.length, 1);
});
