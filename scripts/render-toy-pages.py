"""Render shared toy shell; page-specific interaction markup stays in fragments."""
from pathlib import Path
from string import Template
import json,sys
root=Path(__file__).resolve().parents[1]
folder=root/'templates/toys'
pages=json.loads((folder/'pages.json').read_text(encoding='utf-8'))
template=Template((folder/'page.html').read_text(encoding='utf-8'))
check='--check' in sys.argv
for page in pages:
 data=dict(page)
 if not page.get('enabled',True):
  rendered=(folder/'unavailable.html').read_text(encoding='utf-8')
  target=root/'web'/page['slug']/'index.html'
  if check:assert target.read_text(encoding='utf-8')==rendered,'Disabled page drift: '+page['slug']
  else:target.write_text(rendered,encoding='utf-8')
  continue
 other=next(x for x in pages if x['slug']!=page['slug'])
 data.update(other_slug=other['slug'],other_name=other['name'])
 for part in ['experience','extra']:data[part]=(folder/page['slug']/(part+'.html')).read_text(encoding='utf-8').strip()
 data['steps']=''.join(f'<article><span>{i:02}</span><div><h3>{title}</h3><p>{body}</p></div></article>' for i,(title,body) in enumerate(page['steps'],1))
 rendered=template.substitute(data)
 target=root/'web'/page['slug']/'index.html'
 if check:
  assert target.read_text(encoding='utf-8')==rendered, 'Generated page drift: '+page['slug']
 else:target.write_text(rendered,encoding='utf-8')
print('PASS: toy page shells match the shared template' if check else 'Rendered toy pages')
