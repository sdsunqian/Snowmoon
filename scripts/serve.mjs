import {createServer} from 'node:http';
import {readFile,stat} from 'node:fs/promises';
import {fileURLToPath} from 'node:url';
import {dirname,resolve,join,extname,sep} from 'node:path';
const ROOT=resolve(dirname(fileURLToPath(import.meta.url)),'../dist');
const PORT=Number(process.env.PORT||4321);
const TYPES={'.html':'text/html; charset=utf-8','.css':'text/css; charset=utf-8','.js':'text/javascript; charset=utf-8','.json':'application/json; charset=utf-8','.webp':'image/webp','.jpg':'image/jpeg','.svg':'image/svg+xml','.xml':'application/xml; charset=utf-8','.txt':'text/plain; charset=utf-8','.gz':'application/gzip'};
try{await stat(join(ROOT,'en/index.html'));}catch{console.error('Build the website first: npm run build');process.exit(1);}
createServer(async(req,res)=>{
  if(!['GET','HEAD'].includes(req.method)){res.writeHead(405);res.end();return;}
  try{
    const url=new URL(req.url,'http://localhost');
    if(url.pathname==='/'){res.writeHead(302,{Location:'/en/'});res.end();return;}
    let path=decodeURIComponent(url.pathname);
    let file=resolve(ROOT,'.'+path);
    if(!file.startsWith(ROOT+sep)){res.writeHead(403);res.end('Forbidden');return;}
    try{
      const info=await stat(file);
      if(info.isDirectory()){
        if(!path.endsWith('/')){res.writeHead(301,{Location:path+'/'+url.search});res.end();return;}
        file=join(file,'index.html');
      }
      const bytes=await readFile(file);
      res.writeHead(200,{'Content-Type':TYPES[extname(file)]||'application/octet-stream','Cache-Control':'no-cache','X-Content-Type-Options':'nosniff'});
      res.end(req.method==='HEAD'?undefined:bytes);
    }catch{
      res.writeHead(404,{'Content-Type':'text/html; charset=utf-8'});
      const body=await readFile(join(ROOT,'404.html'));
      res.end(req.method==='HEAD'?undefined:body);
    }
  }catch{res.writeHead(400);res.end('Bad request');}
}).listen(PORT,'127.0.0.1',()=>console.log(`Snowmoon preview: http://localhost:${PORT}/en/`));
