"""Check shared shell consistency, accessible IDs and source-only distribution."""
from pathlib import Path
from html.parser import HTMLParser
import subprocess,sys,json
root=Path(__file__).resolve().parents[1]
subprocess.run([sys.executable,str(root/'scripts/render-toy-pages.py'),'--check'],check=True)
class Page(HTMLParser):
    def __init__(self):super().__init__();self.ids=[];self.links=[];self.css=[]
    def handle_starttag(self,tag,attrs):
        a=dict(attrs)
        if 'id' in a:self.ids.append(a['id'])
        if tag=='a':self.links.append(a.get('href',''))
        if tag=='link' and a.get('rel')=='stylesheet':self.css.append(a['href'])
pages=json.loads((root/'templates/toys/pages.json').read_text(encoding='utf-8'))
for page in pages:
    slug=page['slug'];p=Page();s=(root/'web'/slug/'index.html').read_text(encoding='utf-8');p.feed(s)
    assert len(p.ids)==len(set(p.ids)),f'Duplicate IDs: {slug}'
    assert 'experience' in p.ids and 'source' in p.ids
    assert '/assets/toy-page.css?v=1' in p.css
    assert '#source' in p.links and '#experience' in p.links
    assert f'https://github.com/EehdrmsS/sangsangplum-toys/tree/main/{slug}' in p.links
    assert 'https://github.com/EehdrmsS/sangsangplum-toys#소스-내려받기와-실행' in p.links
    assert not any('/downloads/' in x for x in p.links)
    if slug=='usagi-rap':
        assert all(x in p.ids for x in ['free-tab','challenge-tab','typing-panel','challenge-target','challenge-progress'])
    for identity in (['try','inline','push','cat','close','sound','reset'] if slug=='clap-cat' else ['start','shorter','longer','duration','pause','reset','typing','pet','stage','fullscreen','exit-fullscreen']):
        assert identity in p.ids,f'Missing interaction ID {slug}/{identity}'
assert not list((root/'web').rglob('*.zip*')) and not list((root/'web').rglob('*.exe'))
print('PASS: shared styles, unique IDs, interaction hooks, source links and closed downloads')
