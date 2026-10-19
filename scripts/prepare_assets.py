"""Optional one-time import. Node-only builds use committed optimized assets."""
from pathlib import Path
from PIL import Image, ImageOps, ImageDraw, ImageFont
import json
import hashlib
import requests

ROOT = Path(__file__).resolve().parents[1]
PROJECT = ROOT.parent
ASSETS = ROOT / 'public' / 'assets'
ASSETS.mkdir(parents=True, exist_ok=True)
records = []

def find_prompt(data, key):
    if isinstance(data, dict):
        if data.get('id') == key or data.get('file', '').replace('.png','') == key or data.get('asset') == key:
            if data.get('actualPrompt') or data.get('prompt'):
                return data.get('actualPrompt') or data.get('prompt')
        for value in data.values():
            result = find_prompt(value, key)
            if result: return result
    if isinstance(data, list):
        for value in data:
            result = find_prompt(value, key)
            if result: return result
    return None

def convert(source, name, widths, portrait=False, chapter=None):
    image = Image.open(source).convert('RGB')
    # Character references include a printed label near the feet; portraits use an upper-body crop.
    if portrait:
        w,h=image.size
        image=image.crop((int(w*.13), int(h*.035), int(w*.87), int(h*.60)))
    outputs=[]
    for width in widths:
        height = round(width*5/6) if portrait else round(width*9/16)
        resized=ImageOps.fit(image, (width,height), Image.Resampling.LANCZOS, centering=(.5,.25) if portrait else (.5,.5))
        target=ASSETS/f'{name}-{width}.webp'
        resized.save(target,'WEBP',quality=76,method=6)
        outputs.append({'file':target.relative_to(ROOT).as_posix(),'bytes':target.stat().st_size,'width':width,'height':height})
    candidates=[]
    if portrait:
        candidates=[PROJECT/'concept-art'/'characters'/'prompts.json', PROJECT/'concept-art'/'prompts.json']
    elif chapter:
        prefix=f'chapter{chapter:02}'
        candidates=[PROJECT/'snowmoon-episode'/'pipeline'/f'{prefix}-final-prompts.json',PROJECT/'snowmoon-episode'/'pipeline'/f'{prefix}-prompts.json']
        if chapter==1: candidates.insert(0,PROJECT/'snowmoon-episode'/'pipeline'/'image-prompts.json')
    prompt=None
    for candidate in candidates:
        if candidate.exists():
            prompt=find_prompt(json.loads(candidate.read_text(encoding='utf-8')),source.stem)
            if prompt: break
    records.append({'name':name,'sourceFile':source.relative_to(PROJECT).as_posix(),'sourceSha256':hashlib.sha256(source.read_bytes()).hexdigest(),
                    'process':'Pillow crop/resize + WebP quality 76, method 6; no generative edits',
                    'artwork':'AI-assisted illustration from the Snowmoon motion-comic production',
                    'prompt':prompt,'outputs':outputs})

convert(PROJECT/'snowmoon-episode/public/episode-01/images/04-skybridge.png','hero',[640,960,1600],chapter=1)
episodes=json.loads((ROOT/'content/episodes.json').read_text(encoding='utf-8'))
for ep in episodes:
    n=ep['id']
    images=PROJECT/'snowmoon-episode'/'public'/f'episode-{n:02}'/'images'
    source=sorted(images.glob('*.png'))[0]
    convert(source,f'ep-{n:02}',[480,960],chapter=n)
    verification=PROJECT/'snowmoon-episode'/'output'/('verification-v3.json' if n==1 else f'verification-chapter{n:02}.json')
    data=json.loads(verification.read_text(encoding='utf-8'))
    ep['durationSeconds']=data.get('durationSeconds',0)
    if not ep['durationSeconds']:
        timeline=json.loads((images.parent/('timeline-multivoice.json' if n==1 else 'timeline.json')).read_text(encoding='utf-8'))
        ep['durationSeconds']=timeline['durationInFrames']/timeline['fps']
(ROOT/'content/episodes.json').write_text(json.dumps(episodes,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
characters=json.loads((ROOT/'content/characters.json').read_text(encoding='utf-8'))
for character in characters:
    convert(PROJECT/'concept-art/characters'/character['file'],character['slug'],[360,600],portrait=True)
# Social share image uses the same optimized master; fixed 1200x630 for Open Graph.
hero=Image.open(PROJECT/'snowmoon-episode/public/episode-01/images/04-skybridge.png').convert('RGB')
hero=ImageOps.fit(hero,(1200,630),Image.Resampling.LANCZOS)
shade=Image.new('RGBA',hero.size,(0,0,0,0)); draw=ImageDraw.Draw(shade)
for x in range(1200): draw.line((x,0,x,630),fill=(5,20,18,int(225*(1-x/1200)**1.2)))
hero=Image.alpha_composite(hero.convert('RGBA'),shade)
draw=ImageDraw.Draw(hero)
font_path=Path('C:/Windows/Fonts/arialbd.ttf')
font=ImageFont.truetype(str(font_path),82) if font_path.exists() else ImageFont.load_default(size=72)
small=ImageFont.truetype(str(font_path),24) if font_path.exists() else ImageFont.load_default(size=24)
draw.text((65,230),'SNOWMOON',font=font,fill='#f4f0e7')
draw.text((70,335),'32 CHAPTERS. ONE CHANGING WORLD.',font=small,fill='#9ee6ce')
draw.text((70,550),'snowmoon.cc',font=small,fill='#ffffff')
hero.convert('RGB').save(ASSETS/'social.jpg',quality=82,optimize=True)
(ROOT/'content/artwork-provenance.json').write_text(json.dumps(records,ensure_ascii=False,indent=2),encoding='utf-8')
(ROOT/'content/youtube.json').write_text(json.dumps({str(n):'' for n in range(1,33)},indent=2)+'\n',encoding='utf-8') if not (ROOT/'content/youtube.json').exists() else None
if not (ROOT/'LICENSE').exists():
    for url in ['https://www.gnu.org/licenses/gpl-3.0.txt','https://raw.githubusercontent.com/spdx/license-list-data/main/text/GPL-3.0-only.txt']:
        try:
            license_response=requests.get(url,timeout=25)
            license_response.raise_for_status()
            if 'GNU GENERAL PUBLIC LICENSE' not in license_response.text or len(license_response.text)<30000:
                raise ValueError('Unexpected license text')
            (ROOT/'LICENSE').write_text(license_response.text,encoding='utf-8')
            break
        except requests.RequestException:
            continue
    if not (ROOT/'LICENSE').exists(): raise RuntimeError('Could not retrieve full GPL v3 license text')
print(json.dumps({'images':len(list(ASSETS.glob('*'))),'totalBytes':sum(p.stat().st_size for p in ASSETS.glob('*')),'missingPrompts':[r['name'] for r in records if not r['prompt']]},ensure_ascii=False),flush=True)
