"""Directed, typed graph. Network/dependency/destructive edges never confer control."""
from __future__ import annotations
from collections import defaultdict, deque


def effective_edges(model: dict, scenario: dict) -> list[dict]:
    edges=[dict(e) for e in model['edges']]
    nodes={n['id']:n for n in model['nodes']}
    for tenant in sorted(scenario.get('azure_global_admin_tenants',[])):
        for node in sorted(model['nodes'],key=lambda n:n['id']):
            if node['provider']=='azure' and node['kind']=='subscription' and node.get('tenant')==tenant:
                groups=[nodes[tenant].get('evidence',[]),node.get('evidence',[])]
                edges.append({'id':f'inferred:{tenant}:{node["id"]}', 'source':tenant,
                              'target':node['id'],'relation':'controls',
                              'evidence':sorted({eid for group in groups for eid in group}),
                              'evidence_groups':groups,'inferred':'AZURE_GLOBAL_ADMIN',
                              'source_ids':['MS-AZURE-ELEVATE']})
    return sorted(edges,key=lambda e:(e['source'],e['target'],e['relation'],e['id']))


def _walk(edges: list[dict], roots: dict[str,list], relations: set[str]) -> dict[str,list]:
    adjacency=defaultdict(list)
    for edge in edges:
        if edge['relation'] in relations: adjacency[edge['source']].append(edge)
    paths={node:list(path) for node,path in roots.items()}; queue=deque(sorted(roots))
    while queue:
        node=queue.popleft()
        for edge in adjacency[node]:
            target=edge['target']
            if target not in paths:
                paths[target]=paths[node]+[edge]; queue.append(target)
    return paths


def control_paths(model: dict, scenario: dict) -> dict[str,list]:
    """One deterministic witness per controlled node, including roots with []."""
    return _walk(effective_edges(model,scenario),{n:[] for n in scenario['compromised']},{'controls'})


def effect_path(model: dict, control: dict[str,list], target: str, relations: set[str]):
    """Control path or one terminal destructive edge; None means no modeled path."""
    if target in control: return control[target]
    candidates=[]
    for edge in sorted(model['edges'],key=lambda e:e['id']):
        if edge['source'] in control and edge['target']==target and edge['relation'] in relations:
            candidates.append(control[edge['source']]+[edge])
    return min(candidates,key=lambda p:(len(p),[e['id'] for e in p])) if candidates else None


def network_paths(model: dict, control: dict[str,list]) -> dict[str,list]:
    """Network-reach edges from controlled nodes; no privilege transfer on the route."""
    # A zero-length control path is not a data-plane connection. At least one
    # network_reach edge must be present before a target appears in this result.
    adjacency=defaultdict(list)
    for edge in sorted(model['edges'],key=lambda e:e['id']):
        if edge['relation']=='network_reach': adjacency[edge['source']].append(edge)
    queue=deque((node,list(control[node])) for node in sorted(control))
    expanded=set(control); reached={}
    while queue:
        node,prefix=queue.popleft()
        for edge in adjacency[node]:
            target=edge['target']; path=prefix+[edge]
            if target not in reached: reached[target]=path
            if target not in expanded:
                expanded.add(target);queue.append((target,path))
    return reached
