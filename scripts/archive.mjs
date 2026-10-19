import { readdir, readFile } from 'node:fs/promises';
import { join, relative } from 'node:path';
import { gzipSync } from 'node:zlib';

// Small standards-based ustar archive: keeps the build dependency-free.
export async function sourceArchive(root) {
  const chunks = [];
  const skipped = new Set(['dist', 'node_modules', '.git', '.cache', '.qa', '__pycache__']);
  async function walk(directory) {
    for (const entry of (await readdir(directory, {withFileTypes:true})).sort((a,b)=>a.name.localeCompare(b.name))) {
      if (skipped.has(entry.name) || entry.name.startsWith('.env') || entry.name.endsWith('.log')) continue;
      const absolute = join(directory, entry.name);
      if (entry.isDirectory()) { await walk(absolute); continue; }
      if (!entry.isFile()) continue;
      const name = `snowmoon-website/${relative(root,absolute).replaceAll('\\','/')}`;
      if (Buffer.byteLength(name) > 100) throw new Error(`Archive path too long: ${name}`);
      const content = await readFile(absolute);
      const header = Buffer.alloc(512);
      header.write(name,0,100,'utf8');
      const octal = (value,width) => value.toString(8).padStart(width-1,'0')+'\0';
      header.write(octal(0o644,8),100,8);
      header.write(octal(0,8),108,8);
      header.write(octal(0,8),116,8);
      header.write(octal(content.length,12),124,12);
      header.write(octal(0,12),136,12);
      header.fill(32,148,156);
      header[156]=48;
      header.write('ustar\0',257,6);
      header.write('00',263,2);
      const sum = header.reduce((a,b)=>a+b,0);
      header.write(sum.toString(8).padStart(6,'0')+'\0 ',148,8);
      chunks.push(header,content,Buffer.alloc((512-content.length%512)%512));
    }
  }
  await walk(root);
  chunks.push(Buffer.alloc(1024));
  return gzipSync(Buffer.concat(chunks),{level:9});
}
