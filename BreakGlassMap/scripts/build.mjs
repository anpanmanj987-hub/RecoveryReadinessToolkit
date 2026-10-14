/** Deterministic bundler for this repository's small, controlled ES module subset.
 * It is NOT a general-purpose JavaScript bundler. Rejects unsupported imports.
 */
import {readFileSync,writeFileSync,mkdirSync} from 'node:fs';
import {createHash} from 'node:crypto';
import {resolve} from 'node:path';
import {fileURLToPath} from 'node:url';
const root=fileURLToPath(new URL('..',import.meta.url));
const modules=['schema','fingerprint','engine','report','demo','ui'];
const emitted=new Set();
const chunks=['"use strict";const BGM=Object.create(null);'];
for(const name of modules) {
  let code=readFileSync(resolve(root,`src/${name}.mjs`),'utf8').replace(/\r\n?/g,'\n');
  code=code.replace(/^import\s+\{([^}]+)\}\s+from\s+['"]\.\/([\w-]+)\.mjs['"];?\s*$/gm,(_,bindings,dep)=>{
    if(!emitted.has(dep))throw new Error(`Out-of-order module ${dep}`);
    return `const {${bindings}} = BGM[${JSON.stringify(dep)}];`;
  });
  if(/^\s*import\s/m.test(code))throw new Error(`Unsupported import in ${name}`);
  const exports=[];
  code=code.replace(/\bexport\s+(function|class|const|let)\s+(\w+)/g,(_,type,id)=>{exports.push(id);return `${type} ${id}`;});
  if(/^\s*export\s/m.test(code))throw new Error(`Unsupported export in ${name}`);
  chunks.push(`BGM[${JSON.stringify(name)}]=(()=>{\n${code}\nreturn {${exports.join(',')}};\n})();`);emitted.add(name);
}
const js=chunks.join('\n').replace(/<\/script/gi,'<\\/script');
const css=readFileSync(resolve(root,'web/style.css'),'utf8').replace(/\r\n?/g,'\n');
const hash=x=>createHash('sha256').update(x).digest('base64');
const csp=`default-src 'none'; script-src 'sha256-${hash(js)}'; style-src 'sha256-${hash(css)}'; img-src data: blob:; connect-src 'none'; object-src 'none'; base-uri 'none'; form-action 'none'`;
const html=readFileSync(resolve(root,'web/template.html'),'utf8').replace(/\r\n?/g,'\n').replace('__CSP__',()=>csp).replace('__STYLE__',()=>css).replace('__SCRIPT__',()=>js);
mkdirSync(resolve(root,'dist'),{recursive:true});
writeFileSync(resolve(root,'dist/BreakGlassMap.html'),html);
console.log(`Built dist/BreakGlassMap.html (${Buffer.byteLength(html).toLocaleString()} bytes), no external assets.`);
