"""Explicit runtime bundle: no secrets, source originals, caches or training artifacts."""
import hashlib
import io
import json
import os
from pathlib import Path, PurePosixPath
import tempfile
import urllib.request
import zipfile

ROOT=Path(__file__).resolve().parents[2]
FIXED={'data/normalized/chunks_curated.jsonl','data/normalized/documents.jsonl','data/index/multilingual_e5_curated.json'}
MAX_BYTES=40*1024*1024


def sha(data):return hashlib.sha256(data).hexdigest()


def allowed(name):
    p=PurePosixPath(name)
    return name in FIXED or (str(p.parent)=='data/index' and p.name.startswith('multilingual_e5_curated_') and p.name.endswith('.npy') and ':' not in name and '..' not in p.parts)


def build(root=ROOT):
    index=json.loads((root/'data/index/multilingual_e5_curated.json').read_text(encoding='utf-8'))
    names=sorted(FIXED|{'data/index/'+index['index_file']})
    assert all(allowed(n) for n in names)
    blobs={n:(root/n).read_bytes() for n in names}
    manifest={n:sha(b) for n,b in blobs.items()}
    out=io.BytesIO()
    with zipfile.ZipFile(out,'w',zipfile.ZIP_DEFLATED) as z:
        for name,b in blobs.items():z.writestr(name,b)
        z.writestr('bundle_manifest.json',json.dumps(manifest,sort_keys=True))
    return out.getvalue()


def install(data,expected_sha,root=ROOT):
    if not isinstance(expected_sha,str) or len(expected_sha)!=64 or sha(data)!=expected_sha:
        raise ValueError('Runtime bundle SHA mismatch')
    with zipfile.ZipFile(io.BytesIO(data)) as z:
        names=z.namelist()
        if len(names)!=len(set(names)) or 'bundle_manifest.json' not in names:raise ValueError('Invalid bundle members')
        if sum(i.file_size for i in z.infolist())>MAX_BYTES:raise ValueError('Bundle exceeds size cap')
        manifest=json.loads(z.read('bundle_manifest.json'))
        if set(names)!=set(manifest)|{'bundle_manifest.json'} or not FIXED.issubset(manifest) or not all(allowed(n) for n in manifest):raise ValueError('Unsafe bundle member')
        blobs={n:z.read(n) for n in manifest}
        if any(sha(b)!=manifest[n] for n,b in blobs.items()):raise ValueError('Bundle member SHA mismatch')
        index=json.loads(blobs['data/index/multilingual_e5_curated.json'])
        if 'data/index/'+index['index_file'] not in blobs:raise ValueError('Index matrix missing')
        # Validate all members before mutation. No archive path is executed.
        for name,b in blobs.items():
            target=(root/name).resolve()
            if not target.is_relative_to(root.resolve()):raise ValueError('Bundle escapes root')
            target.parent.mkdir(parents=True,exist_ok=True)
            fd,tmp=tempfile.mkstemp(dir=target.parent)
            try:
                with os.fdopen(fd,'wb') as f:f.write(b)
                os.replace(tmp,target)
            finally:
                if os.path.exists(tmp):os.unlink(tmp)
    return manifest


def fetch(url,expected_sha,root=ROOT):
    if not url.startswith('https://'):raise ValueError('HTTPS bundle URL required')
    try:
        with urllib.request.urlopen(url,timeout=60) as r:data=r.read(MAX_BYTES+1)
        if len(data)>MAX_BYTES:raise ValueError('Bundle exceeds size cap')
        return install(data,expected_sha,root)
    except Exception:
        # A signed URL may contain credentials: never display underlying errors.
        raise ValueError('Runtime bundle unavailable or failed integrity validation') from None


DEVELOPMENT_FILES = [
    'eval/source_group_extension.local.json','eval/supervised_pair_training.local.json',
    'eval/supervised_pair.local.json','eval/supervised_pair_v2.local.json',
    'eval/supervised_pair_retrieval.local.json','eval/supervised_pair_test_notes.json']


def build_development(root=ROOT):
    blobs={name:(root/name).read_bytes() for name in DEVELOPMENT_FILES}
    out=io.BytesIO()
    with zipfile.ZipFile(out,'w',zipfile.ZIP_DEFLATED) as z:
        for name,b in blobs.items():z.writestr(name,b)
        z.writestr('bundle_manifest.json',json.dumps({n:sha(b) for n,b in blobs.items()},sort_keys=True))
    return out.getvalue()


if __name__=='__main__':
    import sys
    development='--development' in sys.argv
    data=build_development() if development else build()
    name='development' if development else 'runtime'
    out=ROOT/f'deployment/{name}.local.zip';out.parent.mkdir(exist_ok=True);out.write_bytes(data)
    meta={'sha256':sha(data),'bytes':len(data),'scope':'Explicit course/development data only; no originals, secrets or model weights'}
    (ROOT/f'deployment/{name}.local.json').write_text(json.dumps(meta,indent=2))
    print('Created',out.name,len(data),'bytes SHA256',sha(data))
