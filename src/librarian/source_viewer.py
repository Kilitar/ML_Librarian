"""Read static extracted context and hash-verified originals from the snapshot."""
import hashlib
import json
from pathlib import Path, PurePosixPath

ROOT=Path(__file__).resolve().parents[2]
DOCUMENTS=ROOT/'data/normalized/documents.jsonl'
SNAPSHOT=ROOT/'data/snapshot/course-2026-10-17-v1'
MANIFEST=ROOT/'data/snapshot/manifest.json'
MAX_DOWNLOAD=25*1024*1024


def relative_source(value):
    value=str(value).replace('\\','/')
    path=PurePosixPath(value)
    if not value or path.is_absolute() or any(p in ('.','..') or ':' in p or '\x00' in p for p in value.split('/')):
        raise ValueError('Invalid source path')
    return path.as_posix()


class SourceCatalog:
    def __init__(self, documents=DOCUMENTS):
        self.sources={}
        with Path(documents).open(encoding='utf-8') as source:
            for line in source:
                row=json.loads(line)
                key=relative_source(row['source_path'])
                self.sources.setdefault(key,[]).append(row)

    def parts(self, source_path):
        key=relative_source(source_path)
        if key not in self.sources:
            raise ValueError('Source is not in the extracted corpus')
        return tuple(self.sources[key])

    def original(self, source_path, *, snapshot=SNAPSHOT, manifest=MANIFEST):
        self.parts(source_path)  # Only a source already present in extracted data.
        key=relative_source(source_path)
        records={relative_source(r['path']):r for r in json.loads(Path(manifest).read_text(encoding='utf-8'))}
        if key not in records:
            raise ValueError('Source is not in the snapshot manifest')
        root=Path(snapshot).resolve(strict=True)
        if Path(snapshot)==SNAPSHOT and not root.is_relative_to(ROOT.resolve()):
            raise ValueError('Snapshot escapes workspace')
        target=(root/key).resolve(strict=True)
        if not target.is_relative_to(root) or not target.is_file():
            raise ValueError('Source escapes snapshot')
        if target.stat().st_size > MAX_DOWNLOAD:
            raise ValueError('Source exceeds download size limit')
        data=target.read_bytes()
        record=records[key]
        if len(data)!=record['bytes'] or hashlib.sha256(data).hexdigest()!=record['sha256'].lower():
            raise ValueError('Snapshot source hash mismatch')
        return data


def initial_part(parts, locator):
    return next((i for i,p in enumerate(parts) if p.get('locator')==locator),0)
