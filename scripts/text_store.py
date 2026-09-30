#!/usr/bin/env python3
"""Resolve a source text by digest when its original path is gone.

Every rating, witness case and planting records the sha256 of the text it used, and the released bundle stores each
distinct text once as supplementary/checkpoint_inputs[_ext]/<sha256>.md. Those copies are tracked in the repository, so
a manifest path that pointed outside the repository (a scratch checkout, a machine that has been rebuilt) can always be
resolved back to byte-identical content. Resolution is digest-checked, so it cannot silently substitute a different text.

Usage as a library:
    from text_store import resolve, digest_for
    p = resolve(manifest_path, sha256=recorded_sha)     # -> pathlib.Path, or None if unresolvable

Usage as a command:
    python3 scripts/text_store.py            # report how many referenced texts resolve, and by which route
"""
import functools, hashlib, json, pathlib, sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
STORES = (ROOT / "supplementary" / "checkpoint_inputs", ROOT / "supplementary" / "checkpoint_inputs_ext")


def sha256_of(p) -> str:
    return hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()


@functools.lru_cache(maxsize=1)
def _index() -> dict:
    """path -> sha256, from every stored rating, witness case and planting record."""
    out = {}
    art = ROOT / "artifacts"
    for f in art.rglob("annotation.json"):
        try:
            d = json.load(open(f))
        except Exception:
            continue
        if d.get("path") and d.get("sha256"):
            out.setdefault(d["path"], d["sha256"])
    cases = art / "witness_discovery" / "cases.json"
    if cases.is_file():
        for c in json.load(open(cases)).get("cases", []):
            if c.get("path") and c.get("sha256"):
                out.setdefault(c["path"], c["sha256"])
    pl = art / "planted_defects" / "plantings.json"
    if pl.is_file():
        for o in json.load(open(pl)).get("originals", []):
            if o.get("path") and o.get("sha256"):
                out.setdefault(o["path"], o["sha256"])
    return out


@functools.lru_cache(maxsize=1)
def _by_digest() -> dict:
    out = {}
    for store in STORES:
        if store.is_dir():
            for p in store.glob("*.md"):
                out.setdefault(p.stem, p)
    for p in (ROOT / "artifacts" / "planted_defects" / "texts").rglob("*.md"):
        try:
            out.setdefault(sha256_of(p), p)
        except OSError:
            pass
    return out


@functools.lru_cache(maxsize=1)
def _by_prefix() -> dict:
    """Checkpoint files are named <label>-<first 12 hex of the digest>.md, so a stem suffix identifies the text."""
    out = {}
    for h in _by_digest():
        out.setdefault(h[:12], h)
    return out


def digest_for(path) -> str | None:
    h = _index().get(str(path))
    if h:
        return h
    stem = pathlib.Path(path).stem
    tail = stem.rsplit("-", 1)[-1].lower()
    if len(tail) >= 8 and all(c in "0123456789abcdef" for c in tail):
        cand = _by_prefix().get(tail[:12])
        if cand and cand.startswith(tail):
            return cand
    return None


@functools.lru_cache(maxsize=1)
def _anonymised() -> dict:
    """original sha256 -> released path, for the few texts the release scrubs (bundled bytes differ from the original)."""
    out = {}
    for store in STORES:
        mf = store / "manifest.json"
        if not mf.is_file():
            continue
        for r in json.load(open(mf)).get("records", []):
            o, b = r.get("original_sha256"), r.get("bundled_sha256")
            if o and b and o != b:
                q = store / f"{o}.md"
                if q.is_file():
                    out.setdefault(o, q)
    return out


def resolve(path, sha256: str | None = None, allow_anonymised: bool = True):
    """The original file when present, else the byte-identical tracked copy, else (optionally) the release's
    anonymised copy of the same text. Byte-identical results are digest-checked."""
    p = pathlib.Path(path)
    if p.exists():
        return p
    h = sha256 or digest_for(path)
    if not h:
        return None
    q = _by_digest().get(h)
    if q is not None and sha256_of(q) == h:
        return q
    if allow_anonymised:
        return _anonymised().get(h)
    return None


def provenance(path, sha256: str | None = None) -> str:
    """"original", "identical-copy", "anonymised-copy" or "unresolvable"."""
    if pathlib.Path(path).exists():
        return "original"
    h = sha256 or digest_for(path)
    if not h:
        return "unresolvable"
    q = _by_digest().get(h)
    if q is not None and sha256_of(q) == h:
        return "identical-copy"
    return "anonymised-copy" if h in _anonymised() else "unresolvable"


def read_bytes(path, sha256: str | None = None) -> bytes:
    q = resolve(path, sha256)
    if q is None:
        raise FileNotFoundError(f"{path} is absent and no digest-matching copy is stored")
    return q.read_bytes()


def main() -> int:
    refs = []
    art = ROOT / "artifacts"
    for f in sorted(art.glob("closure*checkpoints.json")):
        d = json.load(open(f))
        items = d if isinstance(d, list) else (d.get("checkpoints") or d.get("rows") or [])
        refs += [(f.name, x["path"], None) for x in items if isinstance(x, dict) and x.get("path")]
    cases = art / "witness_discovery" / "cases.json"
    if cases.is_file():
        refs += [("witness cases", c["path"], c.get("sha256")) for c in json.load(open(cases)).get("cases", [])]
    pl = art / "planted_defects" / "plantings.json"
    if pl.is_file():
        refs += [("planted originals", o["path"], o.get("sha256")) for o in json.load(open(pl)).get("originals", [])]
    tally = {}
    lost = []
    for s, p, h in refs:
        k = provenance(p, h)
        tally[k] = tally.get(k, 0) + 1
        if k == "unresolvable":
            lost.append((s, p))
    print(f"referenced source texts: {len(refs)}")
    print(f"  present at their recorded path:            {tally.get('original', 0)}")
    print(f"  byte-identical copy tracked in the repo:   {tally.get('identical-copy', 0)}")
    print(f"  release copy only, anonymised by design:   {tally.get('anonymised-copy', 0)}")
    print(f"  unresolvable:                              {len(lost)}")
    for s, p in lost[:10]:
        print("   ", s, p)
    return 1 if lost else 0


if __name__ == "__main__":
    sys.exit(main())
