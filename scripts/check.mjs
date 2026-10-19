import {readdir,readFile,stat} from 'node:fs/promises';
import {resolve,dirname,join,extname} from 'node:path';
import {fileURLToPath} from 'node:url';
import {createHash} from 'node:crypto';
import {gunzipSync} from 'node:zlib';
import assert from 'node:assert/strict';
const ROOT=resolve(dirname(fileURLToPath(import.meta.url)),'..');
const DIST=join(ROOT,'dist');
const files=[];
async function walk(directory){for(const entry of await readdir(directory,{withFileTypes:true})){const path=join(directory,entry.name);if(entry.isDirectory())await walk(path);else files.push(path);}}
await walk(DIST);
const htmlFiles=files.filter(file=>file.endsWith('.html'));
let links=0,schemas=0,chapterParagraphs=0;
for(const file of files) {
  const info=await stat(file);
  assert.ok(info.size<25*1024*1024,`Pages asset too large: ${file}`);
  assert.ok(!['.mp4','.wav','.mp3','.png'].includes(extname(file)),`Unexpected heavy media: ${file}`);
}
for(const file of htmlFiles) {
  const html=await readFile(file,'utf8');
  assert.equal((html.match(/<h1(?:\s|>)/g)||[]).length, file===join(DIST,'index.html')?0:1,`Expected one h1 in ${file}`);
  assert.ok(/<html lang="(?:en|zh-CN)">/.test(html),`Missing language: ${file}`);
  assert.ok(/<link rel="canonical" href="https:\/\/snowmoon\.cc\//.test(html),`Missing canonical: ${file}`);
  if(file!==join(DIST,'index.html')) {
    assert.ok(html.includes('name="description"'),`Missing description: ${file}`);
    assert.ok(html.includes('name="viewport"'),`Missing viewport: ${file}`);
  }
  assert.ok(!/<(?:iframe|object|embed)\b/i.test(html),`Unexpected third-party embed: ${file}`);
  for(const match of html.matchAll(/<script type="application\/ld\+json">([\s\S]*?)<\/script>/g)){
    const data=JSON.parse(match[1]);
    schemas+=data.length;
    assert.ok(!data.some(item=>item['@type']==='VideoObject'&&!item.uploadDate),'Fabricated video metadata');
  }
  for(const match of html.matchAll(/(?:href|src)="([^"#]+)(?:#[^"]*)?"/g)){
    const url=match[1].replaceAll('&amp;','&');
    if(!url.startsWith('/'))continue;
    const path=decodeURIComponent(url.split(/[?#]/)[0]);
    const target=join(DIST,path,path.endsWith('/')?'index.html':'');
    try{await stat(target);}catch{throw Error(`Broken local link ${url} in ${file}`);}
    links++;
  }
  for(const match of html.matchAll(/<img\b[^>]+>/g)) {
    assert.ok(match[0].includes('alt='),`Image missing alt in ${file}`);
    assert.ok(match[0].includes('width=')&&match[0].includes('height='),`Image missing dimensions in ${file}`);
  }
}
for(let n=1;n<=32;n++){
  const id=String(n).padStart(2,'0');
  const report=JSON.parse(await readFile(join(ROOT,'content/zh',`chapter-${id}.json`),'utf8'));
  const source=await readFile(join(ROOT,'content/original',`chapter-${id}.html`));
  const output=await readFile(join(DIST,'zh/read',`chapter-${n}/index.html`),'utf8');
  const translated=await readFile(join(ROOT,'content/zh',`chapter-${id}.html`));
  assert.equal(createHash('sha256').update(translated).digest('hex'),report.translationFileSha256,`Changed reviewed translation ${n}`);
  assert.equal((translated.toString().match(/<table(?:\s|>)/g)||[]).length,report.tablesPreserved,`Missing table ${n}`);
  assert.equal((translated.toString().match(/<svg(?:\s|>)/g)||[]).length,report.storyDiagramsPreserved,`Missing diagram ${n}`);
  assert.equal(createHash('sha256').update(source).digest('hex'),report.sourceSha256,`Changed original ${n}`);
  assert.equal(report.sourceTranslatableNodes,report.translatedNodes,`Missing translated blocks ${n}`);
  assert.equal(report.sourceParagraphs,report.outputParagraphs,`Missing paragraphs ${n}`);
  assert.equal(report.omittedBlocks,0,`Omitted source blocks ${n}`);
  assert.ok(output.includes(`https://vitalik.eth.limo/snowmoon/html/chapter-${n}.html`));
  assert.ok(output.includes('class="reader-content"'),'Text must be rendered in static HTML');
  assert.ok(!output.includes('hreflang="en" href="https://snowmoon.cc/en/episodes/'),'A summary is not an English translation equivalent of a full reading page');
  chapterParagraphs+=report.outputParagraphs;
}
const archive=gunzipSync(await readFile(join(DIST,'source/snowmoon-website-source.tar.gz')));
let offset=0,archiveFiles=0;
const archiveNames=[];
while(offset+512<=archive.length){
  const header=archive.subarray(offset,offset+512);
  const name=header.subarray(0,100).toString('utf8').replace(/\0.*$/,'');
  if(!name)break;
  assert.ok(!/\/(?:dist|\.cache|\.qa|node_modules|\.git)\//.test(name),`Excluded directory in source archive: ${name}`);
  const size=parseInt(header.subarray(124,136).toString().replace(/\0.*$/,''),8);
  assert.ok(Number.isFinite(size),'Invalid tar header');
  archiveNames.push(name);archiveFiles++;
  offset+=512+Math.ceil(size/512)*512;
}
for(const required of ['LICENSE','scripts/build.mjs','content/zh/chapter-32.html','content/youtube.json','public/assets/hero-1600.webp'])assert.ok(archiveNames.includes('snowmoon-website/'+required),`Archive missing ${required}`);
const sitemap=await readFile(join(DIST,'sitemap.xml'),'utf8');
for(const match of sitemap.matchAll(/<loc>([^<]+)<\/loc>/g)) {
  const url=new URL(match[1]);
  assert.equal(url.hostname,'snowmoon.cc');
  await stat(join(DIST,url.pathname,'index.html'));
}
assert.ok(files.length<20000,'Pages free-tier file count');
console.log(JSON.stringify({result:'passed',htmlPages:htmlFiles.length,checkedLocalLinks:links,structuredDataObjects:schemas,translatedChapters:32,translatedParagraphs:chapterParagraphs,sourceArchiveFiles:archiveFiles,files:files.length},null,2));
