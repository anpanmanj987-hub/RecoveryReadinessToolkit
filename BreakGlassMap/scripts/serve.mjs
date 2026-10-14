/** Read-only, loopback-only alternative when company browsers block file:// HTML. */
import http from 'node:http';
import {readFileSync} from 'node:fs';
import {fileURLToPath} from 'node:url';
import {resolve} from 'node:path';
const appFile=fileURLToPath(new URL('../dist/BreakGlassMap.html',import.meta.url));
export function createServer(){
  return http.createServer((req,res)=>{
    res.setHeader('X-Content-Type-Options','nosniff');
    res.setHeader('Cache-Control','no-store');
    res.setHeader('Referrer-Policy','no-referrer');
    res.setHeader('X-Frame-Options','DENY');
    res.setHeader('Content-Security-Policy',"frame-ancestors 'none'");
    const port=res.socket.localPort;
    if(![`127.0.0.1:${port}`,`localhost:${port}`].includes(req.headers.host)){res.writeHead(403);res.end('Forbidden host');return;}
    if(!['GET','HEAD'].includes(req.method)){res.setHeader('Allow','GET, HEAD');res.writeHead(405);res.end('Read-only');return;}
    let path;
    try{path=new URL(req.url,`http://127.0.0.1:${port}`).pathname;}
    catch{res.writeHead(400);res.end('Malformed request target');return;}
    if(path==='/favicon.ico'){res.writeHead(204);res.end();return;}
    if(!['/','/BreakGlassMap.html'].includes(path)){res.writeHead(404);res.end('Not found');return;}
    try{const html=readFileSync(appFile);res.setHeader('Content-Type','text/html; charset=utf-8');res.writeHead(200);res.end(req.method==='HEAD'?undefined:html);}
    catch{res.writeHead(503);res.end('Build the application first: npm run build');}
  });
}
if(process.argv[1]&&resolve(process.argv[1])===fileURLToPath(import.meta.url)){
  try{
    const args=process.argv.slice(2);
    if(args.length&&!(args.length===2&&args[0]==='--port'))throw new Error('Usage: node scripts/serve.mjs [--port 4173]');
    const port=args.length?Number(args[1]):4173;
    if(!Number.isInteger(port)||port<0||port>65535)throw new Error('Invalid port');
    const server=createServer();
    server.on('error',error=>{console.error(error.message);process.exitCode=1;});
    server.listen(port,'127.0.0.1',()=>console.log(`http://127.0.0.1:${server.address().port}`));
  }catch(error){console.error(error.message);process.exitCode=1;}
}
