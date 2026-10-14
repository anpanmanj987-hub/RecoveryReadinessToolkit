"""CLI entry points. All commands are local; output directories are create-only."""
from __future__ import annotations
import argparse
import json
import sys
from datetime import date
from importlib.resources import files
from pathlib import Path
from . import __version__
from .catalog import RULES, field_catalog, load_sources
from .compare import compare_results, render_comparison
from .engine import evaluate
from .io import dump_json, export_csv_bundle, load_model, parse_json
from .model import ModelError, parse_date, validate_model
from .report import questions_csv, render_html, verification_csv

TEMPLATES=('blank','azure-risky','azure-improved','aws','m365')


def example(name: str) -> dict:
    if name not in TEMPLATES: raise ModelError('不明なテンプレートです')
    return validate_model(parse_json(files('cleanroomcheck').joinpath('data','examples',name+'.json').read_text(encoding='utf-8')))


def new_directory(path: Path) -> None:
    if path.exists() or path.is_symlink(): raise ModelError(f'出力先は新しいディレクトリを指定してください: {path}')
    path.mkdir(parents=True,exist_ok=False)


def write_reports(result: dict, output: Path) -> None:
    # Build all renderings before writing, to catch input/render errors first.
    content={'report.html':render_html(result),'report.json':dump_json(result),
             'questions.csv':questions_csv(result),'verification.csv':verification_csv(result)}
    new_directory(output)
    for name,text in content.items():
        (output/name).write_text(text,encoding='utf-8-sig' if name.endswith('.csv') else 'utf-8')


def _options(parser):
    parser.add_argument('--as-of',default=None,metavar='YYYY-MM-DD',help='評価基準日。省略時は実行端末の当日')
    parser.add_argument('--max-evidence-age-days',type=int,default=90,help='証跡許容期間（日）。既定90は変更可能な本OSS方針')


def build_parser():
    parser=argparse.ArgumentParser(prog='cleanroomcheck',description='クリーン環境の設計を、証跡メタデータと権限グラフからオフライン点検します。')
    parser.add_argument('--version',action='version',version='CleanRoomCheck '+__version__)
    sub=parser.add_subparsers(dest='command',required=True)
    p=sub.add_parser('validate',help='入力の型・参照・制限を検証'); p.add_argument('input',type=Path)
    p=sub.add_parser('check',help='点検しHTML/JSON/CSVレポートを生成'); p.add_argument('input',type=Path); p.add_argument('--out',required=True,type=Path); _options(p)
    p.add_argument('--fail-on',choices=['issues','failed','never'],default='issues',help='終了1の条件: issues=不成立/情報不足、failed=不成立のみ、never=常に0（入力エラーは2）')
    p=sub.add_parser('compare',help='同じ企業・同じ基準日の構成変更を比較'); p.add_argument('before',type=Path); p.add_argument('after',type=Path); p.add_argument('--out',required=True,type=Path); _options(p)
    p=sub.add_parser('init',help='入力テンプレートを新規作成'); p.add_argument('--template',choices=TEMPLATES,default='blank'); p.add_argument('--out',required=True,type=Path)
    p=sub.add_parser('csv-export',help='入力をstructure.json + facts.csvに変換'); p.add_argument('input',type=Path); p.add_argument('--out',required=True,type=Path)
    p=sub.add_parser('catalog',help='ルール・項目・一次資料カタログを出力'); p.add_argument('--out',required=True,type=Path)
    p=sub.add_parser('demo',help='架空Azureの不備/改善案と比較レポートを生成'); p.add_argument('--out',required=True,type=Path); p.add_argument('--as-of',default='2026-10-14',help='固定デモ基準日。既定2026-10-14')
    p=sub.add_parser('serve',help='ローカル入力画面を起動（127.0.0.1限定）'); p.add_argument('--port',type=int,default=8765); p.add_argument('--open-browser',action='store_true')
    return parser


def main(argv=None) -> int:
    args=build_parser().parse_args(argv)
    try:
        if args.command=='validate':
            model=load_model(args.input)
            print(f'VALID: {model["project"]["name"]} / {len(model["assessments"])}業務 / {len(model["scenarios"])}シナリオ')
        elif args.command=='check':
            result=evaluate(load_model(args.input),parse_date(args.as_of) if args.as_of else date.today(),args.max_evidence_age_days)
            write_reports(result,args.out)
            print(dump_json({'overall':result['overall'],**result['summary'],'report':str(args.out/'report.html')}),end='')
            if args.fail_on=='never': return 0
            if result['summary']['FAILED'] or (args.fail_on=='issues' and result['summary']['UNKNOWN']): return 1
        elif args.command=='compare':
            as_of=parse_date(args.as_of) if args.as_of else date.today()
            before=evaluate(load_model(args.before),as_of,args.max_evidence_age_days)
            after=evaluate(load_model(args.after),as_of,args.max_evidence_age_days)
            comparison=compare_results(before,after)
            html=render_comparison(comparison); new_directory(args.out)
            (args.out/'comparison.html').write_text(html,encoding='utf-8')
            (args.out/'comparison.json').write_text(dump_json(comparison),encoding='utf-8')
            write_reports(before,args.out/'before'); write_reports(after,args.out/'after')
            print(dump_json(comparison['summary']),end='')
        elif args.command=='init':
            model=example(args.template)
            # This deliberately uses exclusive creation, including for symlinks.
            args.out.parent.mkdir(parents=True,exist_ok=True)
            with args.out.open('x',encoding='utf-8') as f: f.write(dump_json(model))
            print(f'CREATED: {args.out}')
        elif args.command=='csv-export':
            export_csv_bundle(load_model(args.input),args.out); print(f'CREATED: {args.out}')
        elif args.command=='catalog':
            new_directory(args.out)
            for name,data in [('rules.json',RULES),('fields.json',field_catalog()),('sources.json',load_sources())]:
                (args.out/name).write_text(dump_json(data),encoding='utf-8')
            print(f'CREATED: {args.out}')
        elif args.command=='demo':
            as_of=parse_date(args.as_of)
            before=evaluate(example('azure-risky'),as_of); after=evaluate(example('azure-improved'),as_of)
            comparison=compare_results(before,after); html=render_comparison(comparison)
            new_directory(args.out)
            write_reports(before,args.out/'before'); write_reports(after,args.out/'after')
            (args.out/'comparison.html').write_text(html,encoding='utf-8')
            (args.out/'comparison.json').write_text(dump_json(comparison),encoding='utf-8')
            print('FICTIONAL DEMO: '+str(args.out/'comparison.html'))
        elif args.command=='serve':
            from .server import serve
            serve(args.port,args.open_browser)
        return 0
    except (ModelError,OSError,UnicodeError) as exc:
        print(f'ERROR: {exc}',file=sys.stderr); return 2
    except KeyboardInterrupt:
        print('\nSTOPPED',file=sys.stderr); return 130
