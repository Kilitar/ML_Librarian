"""Versioned source export with an optional verified course runtime release."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
ROOT=Path(__file__).resolve().parents[2]


def export(course, *, include_runtime=False):
    course=course.resolve(strict=True)
    if not (course/'app.py').is_file() or not (course/'views').is_dir():raise ValueError('Expected course checkout')
    dest=course/'components/ml_librarian'
    if not dest.resolve().is_relative_to(course):raise ValueError('Export escapes course')
    files=[ROOT/'app.py',ROOT/'embedded.py',ROOT/'dock.py',ROOT/'requirements-librarian.txt']
    files += list((ROOT/'src/librarian').glob('*.py'))+list((ROOT/'src/librarian').glob('*.json'))
    files += list((ROOT/'config').glob('*.json'))+list((ROOT/'docs').glob('*.md'))
    files += list((ROOT/'docs/lecturer').glob('*'))+list((ROOT/'notebooks').glob('*.ipynb'))
    files += list((ROOT/'eval').glob('*_summary.json'))
    files += [ROOT/'eval/domain_probe_training.json']
    for name in ['artifacts.json']:
        files.append(ROOT/'deployment'/name)
    logo=ROOT/'data/Icons/codesrlab_logo_square.png'
    if logo.exists():files.append(logo)
    if include_runtime:
        files.append(ROOT/'deployment/runtime.local.zip')
    old=dest/'export_manifest.json'
    if old.exists():
        for name,digest in json.loads(old.read_text())['files'].items():
            target=dest/name
            if not target.is_file() or hashlib.sha256(target.read_bytes().replace(b'\r\n',b'\n') if json.loads(old.read_text()).get('normalization')=='text-lf' and target.suffix not in ('.png','.zip') else target.read_bytes()).hexdigest()!=digest:
                raise ValueError('Course module modified locally: '+name)
    manifest={}
    for path in files:
        if not path.is_file() or not path.resolve().is_relative_to(ROOT):raise ValueError('Invalid export source')
        name=path.relative_to(ROOT).as_posix()
        if name=='deployment/runtime.local.zip':
            expected=json.loads((ROOT/'deployment/artifacts.json').read_text())['runtime.local.zip']['sha256']
            if hashlib.sha256(path.read_bytes()).hexdigest()!=expected:raise ValueError('Runtime release SHA mismatch')
            name='deployment/runtime.zip'
        target=dest/name
        if not target.resolve().is_relative_to(dest.resolve()):raise ValueError('Unsafe export target')
        target.parent.mkdir(parents=True,exist_ok=True)
        data=path.read_bytes()
        if path.suffix not in ('.png','.zip'):data=data.replace(b'\r\n',b'\n')
        target.write_bytes(data);manifest[name]=hashlib.sha256(data).hexdigest()
    revision=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
    old.write_text(json.dumps({'source_repository':'https://github.com/Kilitar/ML_Librarian',
        'normalization':'text-lf','base_commit':revision,'source_worktree_modified':bool(subprocess.check_output(['git','status','--porcelain','--']+[p.relative_to(ROOT).as_posix() for p in files],cwd=ROOT,text=True)),
        'files':manifest},indent=2)+'\n',encoding='utf-8')
    print('Exported',len(manifest),'files to',dest)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--course-root',type=Path,required=True)
    p.add_argument('--include-runtime',action='store_true')
    args=p.parse_args();export(args.course_root,include_runtime=args.include_runtime)
