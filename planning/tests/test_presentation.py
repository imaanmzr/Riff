"""Exports preserve narrative and stay offline, including hostile authored input."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from riff_core import records, presentation
from riff_core.diagnostic_runner import run

ROOT = Path(__file__).resolve().parents[2]
ASSETS = ROOT / 'distribution' / 'assets'

# Browser protocol test uses Node's built-in WebSocket; no npm/browser driver.
_BROWSER_CHECK = r"""
const fs = require('fs'), path = require('path'), cp = require('child_process');
const [browser, file, profile, screenshot] = process.argv.slice(1);
const launch = ['--headless=new', '--disable-gpu', '--disable-extensions',
  '--disable-background-networking', '--disable-component-update', '--disable-sync',
  '--no-first-run', '--no-default-browser-check', '--remote-debugging-port=0',
  '--user-data-dir=' + profile];
// GitHub-hosted Ubuntu rejects Chrome's sandbox and can omit DevToolsActivePort.
if (process.platform !== 'win32') launch.push('--no-sandbox', '--disable-dev-shm-usage');
launch.push('about:blank');
let browserLog = '';
const child = cp.spawn(browser, launch, {stdio:['ignore','ignore','pipe'], windowsHide:true});
child.stderr.on('data', chunk => { browserLog = (browserLog + chunk.toString()).slice(-4000); });
const sleep = ms => new Promise(resolve => setTimeout(resolve, ms));
let ws;
const timeout = setTimeout(() => { console.error('Browser check timed out'); cleanup(); process.exit(1); }, 60000);
function cleanup() {
  clearTimeout(timeout);
  if (ws) ws.close();
  if (child.exitCode === null) {
    if (process.platform === 'win32') cp.spawnSync('taskkill', ['/PID',String(child.pid),'/T','/F'],{stdio:'ignore',windowsHide:true});
    else child.kill('SIGTERM');
  }
}
(async () => {
  const portFile=path.join(profile, 'DevToolsActivePort');
  for(let i=0;i<400&&!fs.existsSync(portFile);i++) {
    if (child.exitCode !== null) break;
    await sleep(50);
  }
  if (!fs.existsSync(portFile)) throw new Error('Browser did not open a debugging port.\n' + browserLog);
  const port=fs.readFileSync(portFile,'utf8').split('\n')[0];
  const targets=await (await fetch('http://127.0.0.1:'+port+'/json')).json();
  const target=targets.find(t=>t.type==='page');
  ws=new WebSocket(target.webSocketDebuggerUrl);
  await new Promise((resolve,reject)=>{ws.onopen=resolve;ws.onerror=reject;});
  let sequence=0;const pending=new Map(), requests=[];
  ws.onmessage=event=>{
    const message=JSON.parse(event.data);
    if(message.id&&pending.has(message.id)) {
      const p=pending.get(message.id);pending.delete(message.id);
      if(message.error)p.reject(new Error(JSON.stringify(message.error)));else p.resolve(message.result);
    }
    if(message.method==='Network.requestWillBeSent')requests.push(message.params.request.url);
  };
  function call(method,params={}) {return new Promise((resolve,reject)=>{
    const id=++sequence;pending.set(id,{resolve,reject});ws.send(JSON.stringify({id,method,params}));
  });}
  async function evaluate(expression) {const r=await call('Runtime.evaluate',{expression,returnByValue:true});return r.result.value;}
  await call('Page.enable');await call('Network.enable');
  await call('Page.navigate',{url:require('url').pathToFileURL(file).href});
  let rendered;
  for(let i=0;i<300;i++){rendered=await evaluate('document.documentElement.dataset.riffRendered');if(rendered)break;await sleep(50);}
  const result=await evaluate(`({rendered:document.documentElement.dataset.riffRendered,
    errors:document.documentElement.dataset.riffDiagramErrors,
    svg:document.querySelectorAll('#riff-rendered .diagram svg').length,
    images:document.querySelectorAll('#riff-rendered img').length,
    pwned:window.RIFF_PWNED===true,
    fallbackHidden:document.getElementById('riff-fallback').hidden})`);
  result.remoteRequests=requests.filter(url=>/^https?:/i.test(url));
  if(screenshot){const shot=await call('Page.captureScreenshot',{format:'png',captureBeyondViewport:true});fs.writeFileSync(screenshot,Buffer.from(shot.data,'base64'));}
  await call('Emulation.setScriptExecutionDisabled',{value:true});
  await call('Page.reload');await sleep(500);
  // Page scripts stay disabled. The debugger can still read the parsed document.
  result.staticFallback=await evaluate(`(() => {
    const fallback=document.getElementById('riff-fallback');
    const rendered=document.getElementById('riff-rendered');
    return !!(fallback && fallback.hidden===false && rendered && rendered.hidden===true
      && document.documentElement.dataset.riffRendered===undefined);
  })()`);
  console.log(JSON.stringify(result));
  // Browser.close can terminate the debugger before it sends a response.
  ws.send(JSON.stringify({id:++sequence,method:'Browser.close'}));
  for(let i=0;i<50&&child.exitCode===null;i++)await sleep(50);
})().catch(error=>{console.error(error.stack);process.exitCode=1;}).finally(cleanup);
"""


class PresentationTests(unittest.TestCase):
    def plan(self):
        return dict(title='Readable plan', task_id='demo', revision=2, source_revision='abc',
                    route='standard', status='DRAFT', requirements=['R1'],
                    tasks=[dict(id='T1', objective='First change', dependencies=[], requirements=['R1']),
                           dict(id='T2', objective='Second change', dependencies=['T1'], requirements=['R1'])])

    def test_full_export_preserves_authored_text_and_exact_edges(self):
        plan = self.plan()
        authored = '## Contract\n\nNever retry an acknowledged action.\n'
        output = presentation.render_markdown(plan, authored, {})
        self.assertIn(authored, output)
        self.assertIn(records.generated_sections(plan)['graph'], output)
        self.assertIn('Proposed task dependencies', output)

    def test_concise_is_explicit_and_diagrams_can_be_disabled(self):
        output = presentation.render_markdown(self.plan(), 'Important details.', {}, detail='concise', diagrams='none')
        self.assertNotIn('```mermaid', output)
        self.assertNotIn('Important details.', output)
        self.assertIn('not an execution contract', output)
        self.assertIn('No structured outcome recorded', output)
        self.assertNotIn('specification below', output)
        full = presentation.render_markdown(self.plan(), '```mermaid\ngraph TD\nA-->B\n```', {}, diagrams='none')
        self.assertNotIn('```mermaid', full)
        self.assertIn('A-->B', full)
        for fence in ('```Mermaid', '~~~mermaid', '````mermaid', ' ``` mermaid', '> ```mermaid', '    ```mermaid'):
            with self.subTest(fence=fence):
                content = fence + '\ngraph TD\nA-->B\n' + fence.split('m')[0].split('M')[0]
                rendered = presentation.render_markdown(self.plan(), content, {}, diagrams='none')
                self.assertNotIn(fence, rendered)
        html = presentation.render_html('> ```mermaid\n> graph TD\n> A-->B\n> ```', 'No diagrams', ASSETS, diagrams='none')
        self.assertIn('"diagrams": "none"', html)
        self.assertIn("input.diagrams === 'none'", html)

    def test_generated_sections_are_verified_not_blindly_hidden(self):
        plan = self.plan()
        section = records.generated_sections(plan)['tasks']
        text = 'Narrative.\n<!-- riff:generated:tasks -->\n' + section + '\n<!-- /riff:generated:tasks -->\n'
        output = presentation.render_markdown(plan, text, {})
        self.assertIn('Narrative.', output)
        self.assertEqual(1, output.count(section))
        with self.assertRaises(ValueError):
            presentation.render_markdown(plan, text.replace('First change', 'Invented change'), {})

    def test_invalid_graph_is_not_drawn(self):
        plan = self.plan()
        plan['tasks'][0]['dependencies'] = ['missing']
        with self.assertRaises(ValueError):
            presentation.render_markdown(plan, 'Narrative', {})

    def test_assets_are_pinned_and_export_contains_fallback(self):
        text = '</script><img src="https://invalid.example/evil" onerror="alert(1)">'
        output = presentation.render_html(text, '<unsafe>', ASSETS)
        self.assertIn('&lt;unsafe&gt;', output)
        self.assertIn('\\u003c/script\\u003e', output)
        self.assertIn('id="riff-fallback"', output)
        self.assertIn("connect-src &#x27;none&#x27;", output)
        self.assertNotIn('<script src=', output)
        for item in json.loads((ASSETS / 'manifest.json').read_text()):
            self.assertEqual(item['sha256'], hashlib.sha256((ASSETS / item['file']).read_bytes()).hexdigest())

    def test_checksum_tampering_fails(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)
            for item in ASSETS.iterdir():
                if item.is_file():
                    (path / item.name).write_bytes(item.read_bytes())
            (path / 'mermaid.min.js').write_text('tampered')
            with self.assertRaisesRegex(ValueError, 'checksum'):
                presentation.render_html('# Text', 'Title', path)

    def test_offline_browser_and_hostile_input(self):
        browser = os.environ.get('RIFF_BROWSER')
        if not browser:
            browser = next((str(p) for p in [
                Path(r'C:\Program Files\Google\Chrome\Application\chrome.exe'),
                Path(r'C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe')]
                if p.is_file()), None)
        node = shutil.which('node')
        if not browser or not node:
            self.skipTest('Set RIFF_BROWSER to a Chromium browser and provide Node 22+')
        with tempfile.TemporaryDirectory(prefix='riff-browser-test-') as directory:
            root = Path(directory)
            page = root / 'plan.html'
            markdown = '''# Offline plan

```mermaid
flowchart LR
T1[Review] --> T2[Implement]
```

```mermaid
sequenceDiagram
User->>Riff: Show task
Riff-->>User: Explain status
```

<script>window.RIFF_PWNED=true</script>
![image](https://invalid.example/pixel)
[unsafe](javascript:alert(1))

```mermaid
%%{init: {'securityLevel':'loose'}}%%
graph TD
A-->B
```
'''
            page.write_text(presentation.render_html(markdown, 'Offline plan', ASSETS), encoding='utf-8')
            result = run([node, '-e', _BROWSER_CHECK, browser, str(page),
                          str(root / 'profile'), os.environ.get('RIFF_SCREENSHOT', '') or str(root / 'preview.png')],
                         root, command_timeout=75, total_timeout=75)
            self.assertFalse(result['timed_out'], result['stderr'])
            self.assertEqual(0, result['exit_code'], result['stderr'])
            observed = json.loads(result['stdout'])
            self.assertEqual('true', observed['rendered'])
            self.assertEqual('1', observed['errors'])
            self.assertEqual(2, observed['svg'])
            self.assertEqual([], observed['remoteRequests'])
            self.assertEqual(0, observed['images'])
            self.assertFalse(observed['pwned'])
            self.assertTrue(observed['fallbackHidden'])
            self.assertTrue(observed['staticFallback'])


if __name__ == '__main__':
    unittest.main()
