#!/usr/bin/env python3
"""Executable checks for the planted defects: runs every check function from parts/checks_*.py and writes checks.json.
Usage: python3 planted_checks.py --all      (standalone; only the parts modules and plantings.json in this directory are used)
A check returns (ok, detail): ok means the planted statement was confirmed false (F) or the display confirmed false and the
continuation confirmed correct (H). G plantings are deletions and have no executable check."""
import importlib.util, json, pathlib, sys, time

HERE = pathlib.Path(__file__).resolve().parent

def load_checks():
    checks = {}
    for mod in sorted((HERE / "parts").glob("checks_*.py")):
        spec = importlib.util.spec_from_file_location(mod.stem, mod); m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
        for name, fn in getattr(m, "CHECKS", {}).items():
            checks[name] = (mod.name, fn)
    return checks

def main():
    checks = load_checks()
    plantings = json.load(open(HERE / "plantings.json"))["plantings"] if (HERE / "plantings.json").exists() else []
    wanted = {e["check"]: e for e in plantings if not str(e.get("check", "")).startswith("none")}
    rows, n_ok = [], 0
    for name, (modname, fn) in sorted(checks.items()):
        try: ok, detail = fn()
        except Exception as exc: ok, detail = False, f"exception: {type(exc).__name__}: {exc}"
        e = wanted.get(name, {})
        rows.append({"check": name, "module": modname, "planting": e.get("id"), "type": e.get("type"), "ledger_statement": e.get("ledger_statement"), "ok": bool(ok), "detail": str(detail)[:600]})
        n_ok += bool(ok); print(f"{'PASS' if ok else 'FAIL'} {name:40s} {str(detail)[:140]}")
    missing = [n for n in wanted if n not in checks]
    for n in missing: print(f"MISSING {n} (planting {wanted[n]['id']})")
    print(f"{n_ok}/{len(rows)} PASS; {len(missing)} planting checks missing; {sum(1 for e in plantings if str(e.get('check','')).startswith('none'))} deletions without executable check")
    json.dump({"generated_utc": time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime()), "python": sys.version.split()[0], "checks": rows, "missing": missing}, open(HERE / "checks.json", "w"), indent=1)
    return 0 if (n_ok == len(rows) and not missing) else 1

if __name__ == "__main__": sys.exit(main())
