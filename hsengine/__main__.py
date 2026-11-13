"""CLI:  python -m hsengine data\\experiment3.json [--eval-schema] [--issues]"""
import argparse
import json
import sys

from .engine import analyze


def main() -> int:
    ap = argparse.ArgumentParser(prog="hsengine", description="Deterministic Haystack validator")
    ap.add_argument("file")
    ap.add_argument("--eval-schema", action="store_true", help="print ground truth in the Experiment 3 schema")
    ap.add_argument("--issues", action="store_true", help="print a short issue list instead of full JSON")
    ap.add_argument("--truthy-markers", action="store_true", help="treat JSON true as a marker")
    a = ap.parse_args()

    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    try:
        with open(a.file, encoding="utf-8-sig") as f:
            data = json.load(f)
        g = analyze(data, truthy_markers=a.truthy_markers)
    except Exception as ex:  # noqa: BLE001 - CLI boundary
        print(f"ERROR: {ex}", file=sys.stderr)
        return 2

    if a.issues:
        for i in g.issues:
            print(f"[{i.severity.upper():7}] {i.code:24} {i.entity:12} {i.message}")
        print(f"\n{len(g.entities)} entities, {sum(i.severity == 'error' for i in g.issues)} errors, "
              f"{sum(i.severity == 'warning' for i in g.issues)} warnings")
    else:
        out = g.to_eval_schema() if a.eval_schema else g.to_dict()
        print(json.dumps(out, indent=2, ensure_ascii=False))
    return 0 if g.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
