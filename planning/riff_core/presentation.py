"""Readable exports. Rendering never edits task records or grants readiness."""
import base64
import hashlib
import html
import json
from pathlib import Path
import re

from . import records


def _plain(value):
    return str(value if value is not None else 'Unknown')


def _cell(value):
    return _plain(value).replace('|', '\\|').replace('\n', ' ')


def render_markdown(plan, authored, diagnostics, detail='full', diagrams='auto'):
    """Compose an export from facts and unmodified authored prose."""
    if detail not in ('concise', 'full') or diagrams not in ('auto', 'none'):
        raise ValueError('Invalid presentation detail or diagrams option')
    sections = records.generated_sections(plan)
    authored = records.authored_text(authored, plan)
    if diagrams == 'none':
        authored = re.sub(r'(?im)^([^\r\n]*?(?:`{3,}|~{3,}))[ \t]*mermaid[ \t]*$', r'\1text', authored)
    title = _plain(plan.get('title', plan.get('task_id', 'Riff plan')))
    outcome = plan.get('outcome') or ('See the authored specification below.' if detail == 'full'
                                      else 'No structured outcome recorded. Use `--detail full` to read the specification.')
    lines = [f'# {title}', '', '## At a glance', '',
             f'- **Outcome:** {_plain(outcome)}',
             f"- **Recorded status:** {_plain(diagnostics.get('recorded_status', plan.get('status')))}",
             f"- **Current evaluation:** {_plain(diagnostics.get('evaluated_status', 'unknown'))}",
             f"- **Route:** {_plain(plan.get('route'))}",
             f"- **Plan revision:** {_plain(plan.get('revision'))}",
             f"- **Source baseline:** `{_plain(plan.get('source_revision'))}`",
             f"- **Next action:** {_plain(diagnostics.get('next_action', plan.get('next_action', 'Inspect the plan and its evidence.')))}", '']
    if plan.get('scope'):
        lines += [f"**Scope:** {_plain(plan['scope'])}", '']
    issues = diagnostics.get('issues', [])
    if issues:
        shown = issues[:3] if detail == 'concise' else issues
        lines += ['## Questions and blockers', '', '| State | Finding | Next action |',
                  '| --- | --- | --- |']
        lines += [f"| {_cell(i.get('state'))} | {_cell(i.get('message'))} | {_cell(i.get('remedy'))} |" for i in shown]
        lines += ['']
        if len(shown) < len(issues):
            lines += [f'{len(issues) - len(shown)} more findings. Use `riff explain TASK` for the full evaluation.', '']
    if plan.get('tasks'):
        lines += ['## Delivery', '', sections['tasks'], '']
        if diagrams == 'auto':
            graph = sections['graph']
            if not graph.startswith('```'):
                graph = '```mermaid\n' + graph.rstrip() + '\n```'
            lines += ['### Proposed task dependencies', '',
                      f"Derived from structured tasks at plan revision {_plain(plan.get('revision'))}. "
                      'An arrow means the target depends on the source; it does not describe runtime messages.',
                      '', graph, '']
    if plan.get('decisions'):
        lines += ['## Decisions', '', '| ID | Decision | Status |', '| --- | --- | --- |']
        for decision in plan['decisions']:
            lines += [f"| {_cell(decision.get('id'))} | {_cell(decision.get('choice', decision.get('description', decision.get('title'))))} | {_cell(decision.get('status', 'proposed'))} |"]
        lines += ['']
    if detail == 'full':
        lines += ['## Authored specification and evidence', '', authored]
    else:
        lines += ['*Concise export: authored specifications and detailed evidence are omitted. '
                  'Export with `--detail full` to include them. This summary is not an execution contract.*', '']
    return '\n'.join(lines).rstrip() + '\n'


def _script(text):
    # HTML parsers terminate script elements even inside JS strings.
    return re.sub(r'</script', r'<\\/script', text, flags=re.I)


def _hash(text):
    return base64.b64encode(hashlib.sha256(text.encode('utf-8')).digest()).decode('ascii')


def _assets(assets_dir):
    directory = Path(assets_dir)
    manifest = json.loads((directory / 'manifest.json').read_text(encoding='utf-8'))
    entries = {entry['file']: entry for entry in manifest}
    result = {}
    for name in ('markdown-it.min.js', 'mermaid.min.js', 'markdown-it.LICENSE', 'mermaid.LICENSE'):
        data = (directory / name).read_bytes()
        if name not in entries or hashlib.sha256(data).hexdigest() != entries[name]['sha256']:
            raise ValueError('Rendering asset checksum mismatch: ' + name)
        result[name] = data.decode('utf-8')
    return result, manifest


_BOOTSTRAP = r"""
(async function () {
  'use strict';
  const input = JSON.parse(document.getElementById('riff-data').textContent);
  const md = window.markdownit({html: false, linkify: false, typographer: false});
  const escape = md.utils.escapeHtml;
  md.renderer.rules.image = (tokens, idx) => '<span class="image-description">[Image: ' + escape(tokens[idx].content) + ']</span>';
  md.renderer.rules.link_open = () => '<span class="link-text">';
  md.renderer.rules.link_close = () => '</span>';
  const defaultFence = md.renderer.rules.fence;
  const diagrams = [];
  md.renderer.rules.fence = function (tokens, idx, options, env, self) {
    const token = tokens[idx];
    if (input.diagrams === 'none' || token.info.trim().toLowerCase() !== 'mermaid') return defaultFence(tokens, idx, options, env, self);
    const source = token.content;
    const blocked = source.length > 50000 || /%%\s*\{|^\s*---|^\s*(?:click|links?)\b|(?:https?|ftp|file|data|javascript):|url\s*\(|@import/im.test(source);
    const id = 'riff-diagram-' + diagrams.length;
    diagrams.push({id, source, blocked});
    return '<figure><div id="' + id + '" class="diagram" aria-label="Mermaid diagram"></div>' +
      '<details open class="diagram-source"><summary>Diagram source / text fallback</summary><pre>' + escape(source) + '</pre></details></figure>';
  };
  const article = document.getElementById('riff-rendered');
  article.innerHTML = md.render(input.markdown);
  article.hidden = false;
  document.getElementById('riff-fallback').hidden = true;
  window.mermaid.initialize({startOnLoad: false, securityLevel: 'strict',
    theme: 'default', htmlLabels: false, flowchart: {htmlLabels: false},
    maxTextSize: 50000, maxEdges: 1000,
    secure: ['secure', 'securityLevel', 'startOnLoad', 'maxTextSize', 'maxEdges', 'htmlLabels', 'flowchart']});
  let errors = 0;
  for (const item of diagrams) {
    const container = document.getElementById(item.id);
    try {
      if (item.blocked) throw new Error('Diagram configuration, links, or oversized input is not allowed in offline exports.');
      const rendered = await window.mermaid.render(item.id + '-svg', item.source);
      // Mermaid strict mode sanitizes SVG; removing links also prevents accidental navigation.
      container.innerHTML = rendered.svg;
      for (const node of container.querySelectorAll('a, image, foreignObject, script')) {
        if (node.tagName.toLowerCase() === 'a') node.replaceWith(...node.childNodes);
        else node.remove();
      }
      for (const node of container.querySelectorAll('*')) {
        for (const attribute of [...node.attributes]) {
          if (/^on/i.test(attribute.name) || /^(?:href|xlink:href)$/i.test(attribute.name)) node.removeAttribute(attribute.name);
        }
      }
      container.parentElement.querySelector('details').open = false;
    } catch (error) {
      errors += 1;
      container.textContent = 'Diagram could not be rendered: ' + String(error.message || error);
      container.classList.add('diagram-error');
      const temporary = document.getElementById('d' + item.id + '-svg');
      if (temporary) temporary.remove();
    }
  }
  document.documentElement.dataset.riffRendered = 'true';
  document.documentElement.dataset.riffDiagramErrors = String(errors);
})().catch(function (error) {
  document.getElementById('riff-fallback').hidden = false;
  document.getElementById('riff-rendered').hidden = true;
  document.getElementById('riff-error').textContent = 'Rich rendering unavailable. The complete text is shown below.';
  document.documentElement.dataset.riffRendered = 'failed';
});
"""

_STYLE = """
body{font:16px/1.6 system-ui,sans-serif;color:#202938;background:#f7f8fa;margin:0}
main{max-width:1040px;margin:2rem auto;padding:2rem;background:white;border-radius:12px}
h1,h2,h3{line-height:1.25}h2{border-bottom:1px solid #dbe0e7;padding-bottom:.5rem;margin-top:2rem}
table{border-collapse:collapse;display:block;overflow:auto;width:100%}th,td{padding:.6rem;border:1px solid #dbe0e7;text-align:left}
pre{white-space:pre-wrap;overflow-wrap:anywhere;background:#f2f4f7;padding:1rem;border-radius:6px}code{font-family:ui-monospace,monospace}
svg{max-width:100%;height:auto}.diagram{overflow:auto}.diagram-error{color:#8a2d16}.link-text{text-decoration:underline}
details{margin:1rem 0}summary{cursor:pointer}.provenance{font-size:.8rem;color:#536174}
@media print{body,main{background:white;margin:0;padding:0}details{display:block}pre{white-space:pre-wrap}}
"""


def render_html(markdown, title, assets_dir, diagrams='auto'):
    """Self-contained, offline HTML; raw authored HTML and network resources disabled."""
    if diagrams not in ('auto', 'none'): raise ValueError('Invalid diagrams option')
    assets, manifest = _assets(assets_dir)
    scripts = [_script(assets['markdown-it.min.js']), _script(assets['mermaid.min.js']), _BOOTSTRAP]
    hashes = ' '.join("'sha256-" + _hash(script) + "'" for script in scripts)
    policy = ("default-src 'none'; script-src " + hashes + "; style-src 'unsafe-inline'; "
              "img-src 'none'; font-src 'none'; connect-src 'none'; object-src 'none'; "
              "base-uri 'none'; form-action 'none'; frame-src 'none'")
    payload = json.dumps({'markdown': markdown, 'diagrams': diagrams}, ensure_ascii=True).replace('<', '\\u003c').replace('>', '\\u003e').replace('&', '\\u0026')
    notices = '\n\n'.join(assets[n] for n in ('markdown-it.LICENSE', 'mermaid.LICENSE'))
    provenance = json.dumps(manifest, indent=2)
    return ('<!doctype html>\n<html lang="en"><head><meta charset="utf-8">'
            '<meta name="viewport" content="width=device-width, initial-scale=1">'
            f'<meta http-equiv="Content-Security-Policy" content="{html.escape(policy, quote=True)}">'
            f'<title>{html.escape(str(title))}</title><style>{_STYLE}</style></head><body><main>'
            '<p id="riff-error" role="status"></p><article id="riff-rendered" hidden></article>'
            f'<pre id="riff-fallback">{html.escape(markdown)}</pre>'
            '<details class="provenance"><summary>Rendering assets and licenses</summary>'
            f'<pre>{html.escape(provenance)}\n\n{html.escape(notices)}</pre></details></main>'
            f'<script id="riff-data" type="application/json">{payload}</script>'
            + ''.join('<script>' + script + '</script>' for script in scripts)
            + '</body></html>\n')
