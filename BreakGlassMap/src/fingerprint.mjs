/** Non-cryptographic change detector, NOT a signature or evidence authenticity check.
 * FNV-1a-64 binds a self-reported exercise record to the model's structural inputs
 * and selected scenario. Metadata/evidence are excluded; all nodes are included.
 */
export function conditionFingerprint(model,scenario) {
  const normalized={
    version:1,
    nodes:model.nodes.map(n=>({id:n.id,kind:n.kind,...(n.kind==='resource'?{initial:n.initial??'unknown'}:{routes:(n.routes??[]).map(r=>({id:r.id,requires:r.requires})).sort((a,b)=>a.id.localeCompare(b.id,'en'))})})).sort((a,b)=>a.id.localeCompare(b.id,'en')),
    scenario:{id:scenario.id,unavailable:[...(scenario.unavailable??[])].sort(),unknown:[...(scenario.unknown??[])].sort()}
  };
  let hash=0xcbf29ce484222325n;
  for(const byte of new TextEncoder().encode(JSON.stringify(normalized))){hash^=BigInt(byte);hash=(hash*0x100000001b3n)&0xffffffffffffffffn;}
  return 'bgm1-'+hash.toString(16).padStart(16,'0');
}
