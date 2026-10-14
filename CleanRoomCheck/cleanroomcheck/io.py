"""Bounded local inputs. CSV bundle = structure.json + typed facts.csv."""
from __future__ import annotations
import csv
import io
import json
from copy import deepcopy
from pathlib import Path
from .model import MAX_BYTES, MAX_DEPTH, ModelError, check_budget, validate_model


def _unique(pairs):
    result={}
    for key,value in pairs:
        # Validate before including a duplicate key in an error response.
        check_budget(key)
        if key in result: raise ModelError(f'重複したキー: {key}')
        result[key]=value
    return result


def _bad_constant(value):
    raise ModelError(f'非有限数は使用できません: {value}')


def _bounded_integer(raw: str) -> int:
    # Independent of interpreter-specific int-decoder limits; real model numbers
    # are bounded much more tightly by the schema.
    if len(raw.lstrip('-')) > 100:
        raise ModelError('JSONの整数は100桁以下にしてください')
    return int(raw)


def parse_json(text: str):
    try:
        if len(text.encode('utf-8')) > MAX_BYTES: raise ModelError('入力は2MiB以下にしてください')
        data=json.loads(text,object_pairs_hook=_unique,parse_constant=_bad_constant,parse_int=_bounded_integer)
        check_budget(data)
        return data
    except ModelError:
        raise
    except (ValueError, RecursionError, UnicodeError) as exc:
        raise ModelError(f'JSONを読み込めません: {str(exc)[:180]}') from exc


def read_text(path: Path) -> str:
    try:
        with path.open('rb') as fh: raw=fh.read(MAX_BYTES+1)
        if len(raw)>MAX_BYTES: raise ModelError('各入力ファイルは2MiB以下にしてください')
        return raw.decode('utf-8-sig')
    except (OSError, UnicodeError) as exc:
        raise ModelError(f'UTF-8ファイルを読み込めません: {path.name}: {exc}') from exc


def parse_yaml(text: str):
    try: import yaml
    except ImportError as exc:
        raise ModelError('YAML入力には任意依存PyYAMLが必要です: pip install "cleanroomcheck[yaml]"') from exc
    try:
        depth=0
        for token in yaml.scan(text):
            if isinstance(token,(yaml.tokens.AliasToken,yaml.tokens.AnchorToken)):
                raise ModelError('YAMLのanchor/aliasは初版では使用できません')
            if isinstance(token,(yaml.tokens.BlockMappingStartToken,yaml.tokens.BlockSequenceStartToken,yaml.tokens.FlowMappingStartToken,yaml.tokens.FlowSequenceStartToken)):
                depth+=1
                if depth>MAX_DEPTH: raise ModelError('YAMLの深さが制限を超えています')
            elif isinstance(token,(yaml.tokens.BlockEndToken,yaml.tokens.FlowMappingEndToken,yaml.tokens.FlowSequenceEndToken)):
                depth-=1
        class UniqueLoader(yaml.SafeLoader): pass
        UniqueLoader.yaml_implicit_resolvers={key:[(tag,pattern) for tag,pattern in vals if tag!='tag:yaml.org,2002:timestamp'] for key,vals in yaml.SafeLoader.yaml_implicit_resolvers.items()}
        def mapping(loader,node,deep=False):
            result={}
            for key_node,value_node in node.value:
                key=loader.construct_object(key_node,deep=deep)
                if not isinstance(key,str): raise ModelError('YAMLのキーは文字列で指定してください')
                if key in result: raise ModelError(f'YAMLの重複キー: {key}')
                result[key]=loader.construct_object(value_node,deep=deep)
            return result
        UniqueLoader.add_constructor(yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG,mapping)
        data=yaml.load(text,Loader=UniqueLoader); check_budget(data); return data
    except (yaml.YAMLError, RecursionError) as exc:
        raise ModelError(f'安全なYAMLを読み込めません: {str(exc)[:180]}') from exc


def load_model(path: Path | str) -> dict:
    path=Path(path)
    if path.is_dir(): return _load_bundle(path)
    text=read_text(path)
    if path.suffix.lower() in {'.yaml','.yml'}: data=parse_yaml(text)
    elif path.suffix.lower()=='.json': data=parse_json(text)
    else: raise ModelError('入力は.json/.yaml/.yml、またはCSV bundleディレクトリです')
    return validate_model(data)


def _load_bundle(path: Path) -> dict:
    data=validate_model(parse_json(read_text(path/'structure.json')))
    assessments={a['id']:a for a in data['assessments']}
    if any(a['facts'] for a in assessments.values()):
        raise ModelError('CSV bundleのstructure.jsonのfactsは空にしてください')
    raw=read_text(path/'facts.csv')
    try:
        reader=csv.DictReader(io.StringIO(raw))
        if reader.fieldnames!=['assessment_id','field','value_json','evidence_ids']:
            raise ModelError('facts.csvの列はassessment_id,field,value_json,evidence_idsです')
        seen=set()
        for row in reader:
            if None in row or any(v is None for v in row.values()): raise ModelError('facts.csvの列数が不正です')
            aid,field=row['assessment_id'],row['field']; key=(aid,field)
            if aid not in assessments: raise ModelError(f'facts.csv: 存在しないassessment {aid}')
            if key in seen: raise ModelError(f'facts.csv: 重複したfact {aid}/{field}')
            seen.add(key)
            value=parse_json(row['value_json'])
            evidence=row['evidence_ids'].split(';') if row['evidence_ids'] else []
            assessments[aid]['facts'][field]={'value':value,'evidence':evidence}
    except csv.Error as exc: raise ModelError(f'CSVを読み込めません: {exc}') from exc
    return validate_model(data)


def dump_json(data) -> str:
    return json.dumps(data,ensure_ascii=False,indent=2,allow_nan=False)+'\n'


def export_csv_bundle(model: dict, directory: Path | str) -> None:
    validate_model(model)
    directory=Path(directory)
    if directory.exists(): raise ModelError('CSV出力先は存在しないディレクトリを指定してください')
    data=deepcopy(model); rows=[]
    for assessment in data['assessments']:
        for field,claim in sorted(assessment['facts'].items()):
            rows.append([assessment['id'],field,json.dumps(claim['value'],ensure_ascii=False),';'.join(claim.get('evidence',[]))])
        assessment['facts']={}
    directory.mkdir(parents=True)
    (directory/'structure.json').write_text(dump_json(data),encoding='utf-8')
    with (directory/'facts.csv').open('w',encoding='utf-8-sig',newline='') as fh:
        writer=csv.writer(fh); writer.writerow(['assessment_id','field','value_json','evidence_ids']); writer.writerows(rows)
