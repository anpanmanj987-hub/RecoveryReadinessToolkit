#!/usr/bin/env node
import {readFileSync,statSync,writeFileSync} from 'node:fs';
import {parseModel,LIMITS} from '../src/schema.mjs';
import {analyze} from '../src/engine.mjs';
import {toCsv,toHtml,toText} from '../src/report.mjs';
const HELP=`BreakGlassMap 0.1.0-alpha.1 — local recovery-dependency analysis

Usage:
  node bin/breakglassmap.mjs validate MODEL.json
  node bin/breakglassmap.mjs analyze MODEL.json [options]

Options:
  --scenario ID       Named scenario (default: first in model)
  --as-of YYYY-MM-DD   Evidence evaluation date (default: UTC today)
  --format FORMAT     text | json | csv | html (default: text)
  --out PATH          Write a report instead of stdout; never overwrite by default
  --force             Explicitly allow overwriting --out
  --fail-on LEVEL     none | blocked | unknown | evidence (default: unknown)
  --help              Show help
  --version           Show version

Exit codes: 0 no selected gate failure; 1 input/I/O/usage error;
  2 blocked goal; 3 unknown goal; 4 non-current evidence.
Gates: unknown includes blocked; evidence includes both + EVERY modeled node's
  exercise record must be current and match the selected scenario.
A feasible model is NOT a successful recovery test. No systems are contacted.
`;
function main(args) {
  if(args.length===0||args.includes('--help')){process.stdout.write(HELP);return 0;}
  if(args.length===1&&args[0]==='--version'){console.log('0.1.0-alpha.1');return 0;}
  const [command,file,...rest]=args;
  if(!['validate','analyze'].includes(command))throw new Error('Expected validate or analyze. Use --help.');
  if(!file||file.startsWith('--'))throw new Error('A model file is required.');
  const options={format:'text','fail-on':'unknown'};
  const seen=new Set();
  for(let i=0;i<rest.length;i++) {
    const key=rest[i];
    if(!['--scenario','--as-of','--format','--out','--fail-on','--force'].includes(key))throw new Error(`Unknown option ${key}`);
    if(seen.has(key))throw new Error(`Duplicate option ${key}`);seen.add(key);
    if(key==='--force'){options.force=true;continue;}
    if(!rest[i+1]||rest[i+1].startsWith('--'))throw new Error(`Missing value for ${key}`);
    options[key.slice(2)]=rest[++i];
  }
  if(command==='validate'&&rest.length)throw new Error('validate does not accept analysis options.');
  if(!['text','json','csv','html'].includes(options.format))throw new Error('Invalid --format.');
  if(!['none','blocked','unknown','evidence'].includes(options['fail-on']))throw new Error('Invalid --fail-on.');
  if(options.force&&!options.out)throw new Error('--force requires --out.');
  if(statSync(file).size>LIMITS.bytes)throw new Error('Input exceeds 1 MiB limit.');
  const model=parseModel(readFileSync(file,'utf8'));
  if(command==='validate'){console.log(`Valid: ${model.nodes.length} nodes, ${model.scenarios.length} scenarios.`);return 0;}
  const result=analyze(model,options.scenario,{asOf:options['as-of']});
  const output=options.format==='json'?JSON.stringify(result,null,2)+'\n':({text:toText,csv:toCsv,html:toHtml}[options.format])(model,result);
  if(options.out)writeFileSync(options.out,output,{encoding:'utf8',flag:options.force?'w':'wx',mode:0o600});
  else process.stdout.write(output);
  const gate=options['fail-on'];
  if(gate==='none')return 0;
  if(result.summary.blocked)return 2;
  if(gate!=='blocked'&&result.summary.unknown)return 3;
  if(gate==='evidence'&&result.nodes.some(n=>n.evidenceStatus!=='current'))return 4;
  return 0;
}
try {process.exitCode=main(process.argv.slice(2));}
catch(error){process.stderr.write(`BreakGlassMap: ${error.message}\n`);process.exitCode=1;}
