from __future__ import annotations

import ast
import hashlib
import json
import re
import tokenize
from pathlib import Path
from typing import Any

from pypdf import PdfReader

ROOT = Path(__file__).resolve().parents[2]
SNAPSHOT = ROOT / "data" / "snapshot" / "course-2026-10-17-v1"
OUT = ROOT / "data" / "normalized"


def lang_for(text: str) -> str:
    low = text.lower()
    cs = sum(low.count(x) for x in ("č", "ř", "ě", "š", "ž", "ý", "á", "í", "ů", " česk", " modelu"))
    pl = sum(low.count(x) for x in ("ł", "ą", "ę", "ś", "ź", "ż", "ć", "ń"))
    return "cs" if cs >= 2 else ("pl" if pl >= 2 else "en_or_mixed")


def source_id(rel: str, locator: str, text: str) -> str:
    raw = f"{rel}\0{locator}\0{text}".encode("utf-8", "replace")
    return hashlib.sha256(raw).hexdigest()[:20]


def add(records: list[dict[str, Any]], rel: str, locator: str, text: str, kind: str) -> None:
    text = text.replace("\x00", "").strip()
    if not text:
        return
    records.append({"id": source_id(rel, locator, text), "source_path": rel.replace("\\", "/"),
                    "locator": locator, "source_kind": kind, "language": lang_for(text), "text": text})


def extract_python(path: Path, rel: str, records: list[dict[str, Any]]) -> None:
    raw = path.read_text(encoding="utf-8", errors="replace")
    try:
        tree = ast.parse(raw)
    except SyntaxError:
        return
    seen: set[tuple[int, str]] = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef, ast.Module)):
            doc = ast.get_docstring(node, clean=True)
            if doc and len(doc.strip()) > 30:
                lineno = getattr(node, "lineno", 1)
                key = (lineno, doc)
                if key not in seen:
                    add(records, rel, f"line:{lineno}:docstring", doc, "python_docstring")
                    seen.add(key)
        if isinstance(node, ast.Call):
            fn = ast.unparse(node.func) if hasattr(ast, "unparse") else ""
            if fn.startswith("st.") and node.args and isinstance(node.args[0], ast.Constant) and isinstance(node.args[0].value, str):
                value = node.args[0].value
                if len(value.strip()) > 20:
                    key = (node.lineno, value)
                    if key not in seen:
                        add(records, rel, f"line:{node.lineno}:{fn}", value, "streamlit_literal")
                        seen.add(key)
    try:
        with path.open("rb") as f:
            for tok in tokenize.tokenize(f.readline):
                if tok.type == tokenize.COMMENT and len(tok.string.lstrip("# ")) > 35:
                    add(records, rel, f"line:{tok.start[0]}:comment", tok.string.lstrip("# "), "python_comment")
    except (tokenize.TokenError, UnicodeDecodeError):
        pass


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    records: list[dict[str, Any]] = []
    problems: list[dict[str, str]] = []
    for path in SNAPSHOT.rglob("*"):
        if not path.is_file():
            continue
        rel = path.relative_to(SNAPSHOT).as_posix()
        ext = path.suffix.lower()
        try:
            if ext == ".md" or ext == ".txt":
                add(records, rel, "document", path.read_text(encoding="utf-8", errors="replace"), ext[1:])
            elif ext == ".pdf":
                reader = PdfReader(str(path))
                for i, page in enumerate(reader.pages, 1):
                    text = page.extract_text() or ""
                    if text.strip():
                        add(records, rel, f"page:{i}", text, "pdf")
                    else:
                        problems.append({"source_path": rel, "locator": f"page:{i}", "issue": "no extractable text"})
            elif ext == ".ipynb":
                nb = json.loads(path.read_text(encoding="utf-8"))
                for i, cell in enumerate(nb.get("cells", [])):
                    src = "".join(cell.get("source", []))
                    if src.strip():
                        kind = "notebook_markdown" if cell.get("cell_type") == "markdown" else "notebook_code"
                        add(records, rel, f"cell:{i + 1}:{cell.get('cell_type', 'unknown')}", src, kind)
            elif ext == ".py" and "/views/" in f"/{rel}":
                extract_python(path, rel, records)
        except Exception as exc:
            problems.append({"source_path": rel, "locator": "file", "issue": f"{type(exc).__name__}: {exc}"})
    jsonl = OUT / "documents.jsonl"
    with jsonl.open("w", encoding="utf-8", newline="\n") as f:
        for item in records:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")
    report = {"snapshot": SNAPSHOT.name, "records": len(records), "unique_sources": len({r['source_path'] for r in records}),
              "by_kind": {}, "by_language": {}, "problems": problems}
    for r in records:
        report["by_kind"][r["source_kind"]] = report["by_kind"].get(r["source_kind"], 0) + 1
        report["by_language"][r["language"]] = report["by_language"].get(r["language"], 0) + 1
    (OUT / "extraction_report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({k: v for k, v in report.items() if k != "problems"}, ensure_ascii=False, indent=2))
    print(f"Problems: {len(problems)}; report: {OUT / 'extraction_report.json'}")


if __name__ == "__main__":
    main()
