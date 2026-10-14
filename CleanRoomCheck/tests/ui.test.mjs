// Execute the shipped app with deferred HTTP responses. Native DOM/downloads
// are covered separately by tools/browser_smoke.py.
import assert from 'node:assert/strict';
import test from 'node:test';
import fs from 'node:fs';
import vm from 'node:vm';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {execFileSync} from 'node:child_process';

const root = fileURLToPath(new URL('../', import.meta.url));
const fixture = JSON.parse(execFileSync('python', ['-c', `
import json
from datetime import date
from cleanroomcheck.catalog import field_catalog, RULES, load_sources
from cleanroomcheck.cli import TEMPLATES, example
from cleanroomcheck.engine import evaluate
from cleanroomcheck.report import render_html, questions_csv, verification_csv
examples = {name: example(name) for name in TEMPLATES}
examples['azure-risky']['project']['name'] = 'Initial'
examples['azure-improved']['project']['name'] = 'Template'
result = evaluate(examples['azure-risky'], date(2026, 10, 14))
print(json.dumps({'bootstrap': {'fields': field_catalog(), 'rules': RULES, 'sources': load_sources(), 'examples': examples, 'today': '2026-10-14', 'demo_date': '2026-10-14'}, 'output': {'result': result, 'html': render_html(result), 'questions_csv': questions_csv(result), 'verification_csv': verification_csv(result)}}))
`], {cwd: root, encoding: 'utf8', maxBuffer: 4 * 1024 * 1024}));

const app = fs.readFileSync(path.join(root, 'cleanroomcheck/web/app.js'), 'utf8');
const flush = () => new Promise(resolve => setImmediate(resolve));

function createHarness() {
  const nodes = new Map(), created = [], requests = [];
  class Element {
    constructor(tag = 'div') {
      this.tagName = tag;
      this.value = '';
      this.children = [];
      this.listeners = new Map();
      this.disabled = false;
      this.hidden = false;
      this.classList = {toggle() {}};
    }
    addEventListener(type, handler) {
      if (!this.listeners.has(type)) this.listeners.set(type, []);
      this.listeners.get(type).push(handler);
    }
    append(...children) {
      for (const child of children) {
        this.children.push(child);
        if (this.tagName === 'select' && this.children.length === 1) this.value = child.value;
      }
    }
    replaceChildren(...children) {
      this.children = [];
      if (this.tagName === 'select') this.value = '';
      this.append(...children);
    }
    setAttribute() {}
    scrollIntoView() {}
    remove() {}
    click() {}
  }
  const n = id => nodes.get(id) || created.find(node => node.id === id) || (() => {
    const node = new Element(['template', 'assessment', 'filterResults'].includes(id) ? 'select' : 'div');
    node.id = id;
    nodes.set(id, node);
    return node;
  })();
  const descendants = node => node.children.flatMap(child => [child, ...descendants(child)]);
  n('template').value = 'azure-improved';
  n('filterResults').value = 'issues';
  n('maxAge').value = '90';
  n('editor').hidden = true;
  n('results').hidden = true;

  const context = vm.createContext({
    document: {
      getElementById: n,
      querySelector: () => ({content: 'test-token'}),
      querySelectorAll: () => descendants(n('facts')).filter(node => ['input', 'select'].includes(node.tagName)),
      createElement: tag => {
        const node = new Element(tag);
        created.push(node);
        return node;
      },
      body: new Element('body')
    },
    window: {confirm: () => true},
    structuredClone, Blob, URL,
    setTimeout: () => {},
    fetch: (url, options) => new Promise(resolve => requests.push({
      url, body: options.body ? JSON.parse(options.body) : null, resolve
    }))
  });
  vm.runInContext(app, context);

  const emit = (id, type, event = {target: n(id)}) => Promise.all(
    (n(id).listeners.get(type) || []).map(handler => handler(event))
  );
  const request = url => {
    const index = requests.findIndex(item => item.url === url);
    assert.notEqual(index, -1, `Expected pending request ${url}`);
    return requests.splice(index, 1)[0];
  };
  const answer = (req, data) => req.resolve({ok: true, json: async () => structuredClone(data)});
  const model = name => {
    const data = structuredClone(fixture.bootstrap.examples['azure-risky']);
    data.project.name = name;
    return data;
  };
  const fillRaw = name => {
    n('rawModel').value = JSON.stringify(model(name));
    return emit('rawModel', 'input');
  };
  const beginImport = name => {
    const text = JSON.stringify(model(name));
    n('fileInput').files = [{size: Buffer.byteLength(text), text: async () => text}];
    return emit('fileInput', 'change');
  };
  return {n, emit, request, answer, model, fillRaw, beginImport};
}

async function mount() {
  const h = createHarness();
  h.answer(h.request('/api/bootstrap'), fixture.bootstrap);
  await flush();
  return h;
}
async function renderEvaluation(h) {
  const pending = h.emit('evaluate', 'click');
  h.answer(h.request('/api/evaluate'), fixture.output);
  await pending;
  assert.equal(h.n('results').hidden, false);
}
const rawName = h => JSON.parse(h.n('rawModel').value).project.name;
const validated = model => ({valid: true, model});

test('pending Apply preserves newer raw JSON edits', async () => {
  const h = await mount();
  await h.fillRaw('Older');
  const pending = h.emit('applyJson', 'click');
  const req = h.request('/api/validate');
  await h.fillRaw('Newer');
  h.answer(req, validated(h.model('Older')));
  await pending;
  assert.equal(rawName(h), 'Newer');
  assert.equal(h.n('evaluate').disabled, true);
});

test('pending Apply cannot overwrite a selected template', async () => {
  const h = await mount();
  await h.fillRaw('Older');
  const pending = h.emit('applyJson', 'click');
  const req = h.request('/api/validate');
  await h.emit('loadTemplate', 'click');
  h.answer(req, validated(h.model('Older')));
  await pending;
  assert.equal(rawName(h), 'Template');
});

test('Discard cancels an outstanding Apply', async () => {
  const h = await mount();
  await h.fillRaw('Discarded');
  const pending = h.emit('applyJson', 'click');
  const req = h.request('/api/validate');
  await h.emit('discardJson', 'click');
  h.answer(req, validated(h.model('Discarded')));
  await pending;
  assert.equal(rawName(h), 'Initial');
  assert.equal(h.n('evaluate').disabled, false);
});

for (const order of ['older-first', 'newer-first']) {
  test(`latest Apply wins when responses finish ${order}`, async () => {
    const h = await mount();
    await h.fillRaw('Older');
    const first = h.emit('applyJson', 'click');
    const older = h.request('/api/validate');
    await h.fillRaw('Newer');
    const second = h.emit('applyJson', 'click');
    const newer = h.request('/api/validate');
    if (order === 'older-first') {
      h.answer(older, validated(h.model('Older'))); await first;
      h.answer(newer, validated(h.model('Newer'))); await second;
    } else {
      h.answer(newer, validated(h.model('Newer'))); await second;
      h.answer(older, validated(h.model('Older'))); await first;
    }
    assert.equal(rawName(h), 'Newer');
  });

  test(`latest import wins when responses finish ${order}`, async () => {
    const h = await mount();
    const first = h.beginImport('Older'); await flush();
    const older = h.request('/api/validate');
    const second = h.beginImport('Newer'); await flush();
    const newer = h.request('/api/validate');
    if (order === 'older-first') {
      h.answer(older, validated(h.model('Older'))); await first;
      h.answer(newer, validated(h.model('Newer'))); await second;
    } else {
      h.answer(newer, validated(h.model('Newer'))); await second;
      h.answer(older, validated(h.model('Older'))); await first;
    }
    assert.equal(rawName(h), 'Newer');
  });
}

test('pending import preserves newer raw JSON edits', async () => {
  const h = await mount();
  const pending = h.beginImport('Imported'); await flush();
  const req = h.request('/api/validate');
  await h.fillRaw('Newer');
  h.answer(req, validated(h.model('Imported')));
  await pending;
  assert.equal(rawName(h), 'Newer');
  assert.equal(h.n('evaluate').disabled, true);
});

test('pending import cannot overwrite a selected template', async () => {
  const h = await mount();
  const pending = h.beginImport('Imported'); await flush();
  const req = h.request('/api/validate');
  await h.emit('loadTemplate', 'click');
  h.answer(req, validated(h.model('Imported')));
  await pending;
  assert.equal(rawName(h), 'Template');
});

test('projectName input invalidates rendered results before blur', async () => {
  const h = await mount();
  await renderEvaluation(h);
  h.n('projectName').value = 'Typed edit';
  await h.emit('projectName', 'input');
  assert.equal(h.n('results').hidden, true);
  assert.equal(rawName(h), 'Typed edit');
});

test('projectName input invalidates an in-flight evaluation before blur', async () => {
  const h = await mount();
  const pending = h.emit('evaluate', 'click');
  const req = h.request('/api/evaluate');
  h.n('projectName').value = 'Typed edit';
  await h.emit('projectName', 'input');
  h.answer(req, fixture.output);
  await pending;
  assert.equal(h.n('results').hidden, true);
  assert.equal(rawName(h), 'Typed edit');
});

for (const [id, value, field, expected] of [
  ['fact-rto_hours', '7', 'rto_hours', 7],
  ['fact-protection_until', '2027-02-01', 'protection_until', '2027-02-01'],
  ['proof-independent_identity', 'say', 'independent_identity', ['say']]
]) {
  test(`${id} input invalidates results before blur`, async () => {
    const h = await mount(); await renderEvaluation(h);
    h.n(id).value = value; await h.emit(id, 'input');
    assert.equal(h.n('results').hidden, true);
    const claim = JSON.parse(h.n('rawModel').value).assessments[0].facts[field];
    assert.deepEqual(id.startsWith('proof-') ? claim.evidence : claim.value, expected);
  });
}

test('evaluation date input invalidates results before blur', async () => {
  const h = await mount(); await renderEvaluation(h);
  h.n('asOf').value = '2026-10-15'; await h.emit('asOf', 'input');
  assert.equal(h.n('results').hidden, true);
});

test('template and import controls wait for bootstrap', async () => {
  const h = createHarness();
  assert.equal(h.n('loadTemplate').disabled, true);
  assert.equal(h.n('fileInput').disabled, true);
  h.answer(h.request('/api/bootstrap'), fixture.bootstrap); await flush();
  assert.equal(h.n('loadTemplate').disabled, false);
  assert.equal(h.n('fileInput').disabled, false);
});
