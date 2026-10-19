"""One-time, resumable source import and machine-assisted EN -> zh-CN translation.

Normal website builds use the checked-in translations and need only Node.js.
This optional refresh tool uses the public Google Translate endpoint (no secret).
It reports the provider honestly and never describes its output as human-reviewed.
"""
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from bs4 import BeautifulSoup, NavigableString, Comment
import requests
import hashlib
import json
import re
import time
import shutil
import sys

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parents[1]
PROJECT = ROOT.parent
CONTENT = ROOT / "content"
CACHE = ROOT / ".cache" / "translations"
CONTENT.mkdir(exist_ok=True)
CACHE.mkdir(parents=True, exist_ok=True)
(CONTENT / "original").mkdir(exist_ok=True)
(CONTENT / "zh").mkdir(exist_ok=True)
GLOSSARY = {
    "Zei Leimin": "泽伊·雷明", "Bai Jahen": "拜·贾亨", "Greater Plum Harbor": "大梅港",
    "Order of Steering": "掌舵会", "Arctic Empire": "北极帝国", "United Cities": "联合城邦",
    "Freetown Economics Institute": "自由城经济研究所", "Pafogai Du": "帕福盖城", "Sadzu Du": "萨祖城",
    "Elenar Forest": "埃莱纳森林", "Northglade": "北林", "Northshore": "北岸",
    "Gladias": "格拉迪亚斯", "Seila": "塞拉", "Delwart": "德尔沃特", "Zei": "泽伊", "Bai": "拜",
    "Fin": "芬", "Mu": "穆", "Den": "登", "Min": "敏", "Jahn": "贾恩", "Mov": "莫夫",
    "Pelae": "佩莱", "Alagael": "阿拉盖尔", "Febric": "费布里克", "Lily": "莉莉", "Zven": "兹文",
    "Vil": "维尔", "Daia": "达娅", "Hreda": "赫蕾达", "Verdow": "维尔多", "Utaku": "乌塔库",
    "Lektor": "莱克托尔", "Deluin": "德鲁因", "Telpo": "特尔波", "Vakaria": "瓦卡里亚",
    "Gallowar": "加洛瓦尔", "Ephelion": "埃菲利昂", "Emerald": "翡翠", "Veridia": "维里迪亚",
    "Meldan": "梅尔丹", "Dzego": "泽戈", "Freetown": "自由城", "Kalimar": "卡利马尔",
    "Redshire": "红郡", "Belpaki": "贝尔帕基", "Ondak": "翁达克", "Iptak": "伊普塔克",
    "Mantak": "曼塔克", "Thaldur": "萨尔杜尔", "Minpentai": "敏彭泰", "Dzegoban": "泽戈语",
    "Bansunpei": "班孙派", "Kungaupei": "昆高派", "zipcoins": "zip 币",
    "Snowmoon": "雪月", "Rainmoon": "雨月", "Windmoon": "风月", "Bloomtime": "花时",
    "Grasstime": "草时", "Harvestmoon": "收获月", "Firemoon": "火月", "Fruitmoon": "果月",
    "Grapetime": "葡萄时", "Mistime": "雾时", "Frostime": "霜时", "longhours": "长小时", "longhour": "长小时",
    "Graph Funding": "图谱资助", "Quadratic Funding": "二次方资助", "quadratic voting": "二次方投票",
    "zero-knowledge": "零知识", "Keepers": "守护者", "Keeper": "守护者", "Sentinels": "哨卫", "Sentinel": "哨卫",
    "Acolytes": "见习成员", "Acolyte": "见习成员", "rubrics": "评估准则", "rubric": "评估准则",
    "Arctics": "北极帝国一方", "Arctic": "北极帝国的", "Veridians": "维里迪亚人", "Veridian": "维里迪亚的",
    "Steering": "掌舵体系", "Emerald AI": "翡翠 AI", "anti-transmission foil": "反传输箔", "Bluewhale": "蓝鲸",
    "Silverchat": "银聊", "Helisport": "Helisport", "GPH": "大梅港"
}
pattern = re.compile(r"\b(" + "|".join(re.escape(k) for k in sorted(GLOSSARY, key=len, reverse=True)) + r")\b")
TOKENS = {key: f"ZXQ{i:03}QXZ" for i, key in enumerate(GLOSSARY)}
RESTORE = {token: GLOSSARY[key] for key, token in TOKENS.items()}
(CONTENT / "glossary.json").write_text(json.dumps(GLOSSARY, ensure_ascii=False, indent=2), encoding="utf-8")

def normalize(text):
    # Opaque proper-name tokens avoid the translation engine reinterpreting mixed
    # Chinese/English names; exact project spellings are restored afterward.
    return pattern.sub(lambda m: TOKENS[m.group()], text)

def restore(text):
    text = re.sub(r"[\u200b-\u200f\u202a-\u202e\u2060\ufeff]", "", text)
    text = re.sub(r"ZXQ\s*(\d{1,3})\s*QXZ", lambda m: RESTORE.get(f"ZXQ{int(m.group(1)):03}QXZ",m.group()), text, flags=re.I)
    if re.search(r"ZXQ|QXZ", text, re.I):
        raise ValueError("Unrestored terminology token: " + text[:180])
    return re.sub(r"(?<=[\u4e00-\u9fff])\s+(?=[\u4e00-\u9fff])", "", text)

def should_translate(node):
    text = str(node).strip()
    if not text or isinstance(node, Comment) or not re.search(r"[A-Za-z]{2}", text):
        return False
    if node.find_parent(["script", "style", "svg", "code"]):
        return False
    if re.fullmatch(r"[0-9a-f\s:]+", text) and len(text) > 40:
        return False
    # Preserve invented Dzegoban phonetic speech; its English gloss is translated separately.
    if len(text.split()) >= 4 and not re.search(r"[A-Z,.!?]", text) and all(len(t) <= 4 for t in text.split()):
        return False
    return True

def translate_batch(items):
    prepared = [(key, normalize(text)) for key, text in items]
    query = "\n\n".join(f"[{i:06}] {text}" for i, (_, text) in enumerate(prepared))
    cache_id = hashlib.sha256(query.encode()).hexdigest()
    cache_file = CACHE / f"{cache_id}.json"
    if cache_file.exists():
        saved = json.loads(cache_file.read_text(encoding="utf-8"))
        if len(saved) == len(items):
            return dict(zip((key for key, _ in items), saved.values()))
    for attempt in range(6):
        try:
            response = requests.get("https://translate.googleapis.com/translate_a/single", params={
                "client": "gtx", "sl": "en", "tl": "zh-CN", "dt": "t", "q": query
            }, timeout=55)
            response.raise_for_status()
            data = response.json()
            translated = "".join(part[0] or "" for part in data[0])
            matches = list(re.finditer(r"[\[［]\s*(\d{6})\s*[\]］]", translated))
            if len(matches) != len(items):
                raise ValueError(f"Marker mismatch: {len(matches)}/{len(items)}")
            result = {}
            for i, match in enumerate(matches):
                if int(match.group(1)) != i:
                    raise ValueError("Translation reordered source blocks")
                value = translated[match.end(): matches[i + 1].start() if i + 1 < len(matches) else None].strip()
                if not value:
                    raise ValueError("Empty translation")
                result[items[i][0]] = restore(value)
            cache_file.write_text(json.dumps(result, ensure_ascii=False), encoding="utf-8")
            return result
        except ValueError:
            # Translators occasionally swallow numeric separators. Split rather than
            # guess an alignment, so source paragraphs can never be silently merged.
            if len(items) > 1:
                middle = len(items) // 2
                result = {**translate_batch(items[:middle]), **translate_batch(items[middle:])}
                cache_file.write_text(json.dumps(result, ensure_ascii=False), encoding="utf-8")
                return result
            response = requests.get("https://translate.googleapis.com/translate_a/single", params={
                "client": "gtx", "sl": "en", "tl": "zh-CN", "dt": "t", "q": prepared[0][1]
            }, timeout=55)
            response.raise_for_status()
            result = {items[0][0]: restore("".join(part[0] or "" for part in response.json()[0]).strip())}
            if not result[items[0][0]]:
                raise RuntimeError("Empty individual translation")
            cache_file.write_text(json.dumps(result, ensure_ascii=False), encoding="utf-8")
            return result
        except Exception as exc:
            if attempt == 5:
                # A failed batch must fail the chapter; never silently omit source text.
                raise RuntimeError(f"Translation failed after retries: {exc}") from exc
            time.sleep(min(3 * (attempt + 1), 15))

def prepare_chapter(n):
    stored = CONTENT / "original" / f"chapter-{n:02}.html"
    source = stored if stored.exists() else PROJECT / "source" / f"chapter-{n:02}.html"
    copied = CONTENT / "original" / source.name
    if source.resolve() != copied.resolve():
        shutil.copy2(source, copied)
    soup = BeautifulSoup(source.read_text(encoding="utf-8"), "html.parser")
    article = soup.select_one(".document-page")
    if not article:
        raise ValueError(f"Chapter {n} has no article")
    for el in article.select("nav, script, style, h1"):
        el.decompose()
    for el in article.select("button"):
        el.name = "span"
        el["class"] = ["fictional-control"]
    # Translate complete paragraphs together so emphasis spans do not split sentences.
    block_tags = ["p", "li", "td", "th", "h2", "h3", "h4", "figcaption", "caption"]
    blocks = [el for el in article.find_all(block_tags)
              if not el.find_parent(block_tags + ["svg"]) and re.search(r"[A-Za-z]{2}", el.get_text())]
    nodes = [node for node in article.find_all(string=True)
             if not node.find_parent(block_tags) and should_translate(node)]
    targets = [(el, el.get_text(" ", strip=True)) for el in blocks] + [(el, str(el).strip()) for el in nodes]
    items = [(f"{n}:{i}", text) for i, (_, text) in enumerate(targets)]
    batches, batch, count = [], [], 0
    for key, text in items:
        size = len(normalize(text)) + 14
        if count + size > 3300 and batch:
            batches.append(batch)
            batch, count = [], 0
        batch.append((key, text))
        count += size
    if batch:
        batches.append(batch)
    translated = {}
    for batch in batches:
        translated.update(translate_batch(batch))
    for i, (node, _) in enumerate(targets):
        if isinstance(node, NavigableString):
            node.replace_with(NavigableString(translated[f"{n}:{i}"]))
        else:
            node.clear()
            node.append(NavigableString(translated[f"{n}:{i}"]))
    # Keep presentation classes and safe source diagrams, drop all event handlers and external dependencies.
    for el in article.find_all(True):
        for attr in list(el.attrs):
            if attr.lower().startswith("on") or attr in ("style", "id"):
                del el.attrs[attr]
        if el.name == "a":
            href = el.get("href", "")
            if href.startswith("javascript:"):
                del el.attrs["href"]
            elif href and not href.startswith(("https://", "#")):
                el["href"] = "https://vitalik.eth.limo/snowmoon/html/" + href
        if el.name == "svg":
            el["role"] = "img"
            el["aria-label"] = f"原作第 {n} 章示意图（图中文字保留原文）"
            if "viewbox" in el.attrs:
                el["viewBox"] = el.attrs.pop("viewbox")
        if el.name in ["rect", "clipPath", "text", "path"]:
            for lower, camel in [("clippathunits", "clipPathUnits"), ("textlength", "textLength"), ("lengthadjust", "lengthAdjust")]:
                if lower in el.attrs:
                    el[camel] = el.attrs.pop(lower)
    fragment = "".join(str(el) for el in article.contents)
    (CONTENT / "zh" / f"chapter-{n:02}.html").write_text(fragment, encoding="utf-8")
    record = {"chapter": n, "source": f"https://vitalik.eth.limo/snowmoon/html/chapter-{n}.html",
              "sourceSha256": hashlib.sha256(source.read_bytes()).hexdigest(),
              "sourceTranslatableNodes": len(targets), "translatedNodes": len(translated),
              "sourceParagraphs": len(article.find_all("p")), "outputParagraphs": len(BeautifulSoup(fragment, "html.parser").find_all("p")),
              "terminologyProtection": "opaque-tokens-v2",
              "provider": "Google Translate public endpoint; machine-assisted draft, not a certified translation",
              "humanReviewed": False, "omittedBlocks": 0}
    (CONTENT / "zh" / f"chapter-{n:02}.json").write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Chapter {n:02}: {len(targets)} text blocks, {len(batches)} batches, complete", flush=True)
    return record

if __name__ == "__main__":
    records = []
    failures = []
    with ThreadPoolExecutor(max_workers=4) as pool:
        futures = {pool.submit(prepare_chapter, n): n for n in range(1, 33)}
        for future in as_completed(futures):
            try:
                records.append(future.result())
            except Exception as exc:
                failures.append(futures[future])
                print(f"Chapter {futures[future]} ERROR: {exc}", flush=True)
    if failures:
        raise RuntimeError(f"Incomplete chapters: {failures}; existing results and caches retained")
    (CONTENT / "translation-report.json").write_text(json.dumps(sorted(records, key=lambda x:x['chapter']), ensure_ascii=False, indent=2), encoding="utf-8")
    print("All 32 complete Chinese chapter translations saved.", flush=True)
