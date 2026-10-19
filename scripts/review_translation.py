"""Apply source-indexed editorial corrections and audit preserved story structure.

These targeted, model-assisted checks are not a claim of complete human editing.
Works entirely from the self-contained checked-in source snapshots.
"""
from pathlib import Path
from bs4 import BeautifulSoup, NavigableString
import hashlib
import json
import re
import sys

sys.stdout.reconfigure(encoding='utf-8')
ROOT = Path(__file__).resolve().parents[1]
EDITS = json.loads((ROOT/'content/translation-edits.json').read_text(encoding='utf-8'))
records = []
for n in range(1,33):
    original_path = ROOT/'content/original'/f'chapter-{n:02}.html'
    original = BeautifulSoup(original_path.read_text(encoding='utf-8'),'html.parser').select_one('.document-page')
    output_path = ROOT/'content/zh'/f'chapter-{n:02}.html'
    output = BeautifulSoup(output_path.read_text(encoding='utf-8'),'html.parser')
    source_paragraphs = original.find_all('p')
    paragraphs = output.find_all('p')
    assert len(source_paragraphs)==len(paragraphs), f'Paragraph coverage mismatch: {n}'
    corrected = 0
    for index,(source,translated) in enumerate(zip(source_paragraphs,paragraphs)):
        key = f'{n}:{index}'
        text = source.get_text(' ',strip=True)
        words = re.findall(r'[a-z]+',text)
        invented = len(words)>=3 and not re.search(r'[A-Z]',text) and all(len(word)<=4 for word in words) and not re.search(r'[0-9]',text)
        if key in EDITS or invented:
            translated.clear()
            translated.append(EDITS.get(key,text))
            corrected += 1
    for source,translated in zip(original.select('button'), output.select('.fictional-control')):
        if source.get_text(strip=True)=='be':
            translated.clear(); translated.append('be')
    for node in list(output.find_all(string=True)):
        if node.find_parent(['svg','code']): continue
        text = re.sub(r'[\u200b-\u200f\u202a-\u202e\u2060\ufeff]','',str(node))
        text = text.replace('掌舵体系系统','掌舵体系').replace('维里迪亚的的','维里迪亚的').replace('北极帝国的的','北极帝国的').replace('维里迪亚的会','维里迪亚人会')
        if text!=str(node): node.replace_with(NavigableString(text))
    for control in output.select('input, select, textarea'):
        control['disabled']=''
        control['aria-label']='原作中的设备界面示意控件'
    assert len(original.select('table'))==len(output.select('table')),f'Missing table in chapter {n}'
    # Original navigation SVGs are not story diagrams.
    for nav in original.select('nav'): nav.decompose()
    assert len(original.select('svg'))==len(output.select('svg')),f'Missing diagram in chapter {n}'
    fragment = str(output)
    assert not re.search(r'ZXQ\d|QXZ',fragment),f'Terminology token left in chapter {n}'
    output_path.write_text(fragment,encoding='utf-8')
    record_path = ROOT/'content/zh'/f'chapter-{n:02}.json'
    record = json.loads(record_path.read_text(encoding='utf-8'))
    assert record['sourceSha256']==hashlib.sha256(original_path.read_bytes()).hexdigest()
    record.update({'targetedEditorialCorrections':corrected,'tablesPreserved':len(output.select('table')),
                   'storyDiagramsPreserved':len(output.select('svg')),'humanReviewed':False,
                   'translationFileSha256':hashlib.sha256(output_path.read_bytes()).hexdigest()})
    record_path.write_text(json.dumps(record,ensure_ascii=False,indent=2),encoding='utf-8')
    records.append(record)
(ROOT/'content/translation-report.json').write_text(json.dumps(records,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'chapters':len(records),'paragraphs':sum(r['outputParagraphs'] for r in records),
 'targetedCorrections':sum(r['targetedEditorialCorrections'] for r in records),
 'tables':sum(r['tablesPreserved'] for r in records),'storyDiagrams':sum(r['storyDiagramsPreserved'] for r in records)},ensure_ascii=False,indent=2))
