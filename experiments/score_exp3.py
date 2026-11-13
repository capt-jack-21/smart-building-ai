"""Score an LLM answer to Experiment 3 against the deterministic engine's ground truth.

Usage:  python experiments\\score_exp3.py out\\exp3_content.txt [data\\experiment3.json]
"""
from __future__ import annotations

import json
import os
import re
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from hsengine import analyze  # noqa: E402


def extract_json(text: str):
    """Tolerate <think> blocks and ```json fences. Returns (obj, error)."""
    text = re.sub(r"<think>.*?</think>", "", text, flags=re.S).strip()
    text = re.sub(r"^```(?:json)?\s*|\s*```$", "", text, flags=re.S).strip()
    try:
        return json.loads(text), None
    except json.JSONDecodeError:
        pass
    start, end = text.find("{"), text.rfind("}")
    if start >= 0 and end > start:
        try:
            return json.loads(text[start:end + 1]), None
        except json.JSONDecodeError as ex:
            return None, str(ex)
    return None, "no JSON object found"


def prf(pred: set, truth: set) -> dict:
    tp = len(pred & truth)
    p = tp / len(pred) if pred else (1.0 if not truth else 0.0)
    r = tp / len(truth) if truth else 1.0
    return {"precision": round(p, 3), "recall": round(r, 3), "false_positives": sorted(map(str, pred - truth)),
            "missed": sorted(map(str, truth - pred))}


def score(pred: dict, truth: dict) -> dict:
    res: dict = {"json_valid": True}
    p_ents = {e.get("id"): e for e in pred.get("entities", []) if isinstance(e, dict)}
    t_ents = {e["id"]: e for e in truth["entities"]}

    # entity kind
    kind_ok = sum(1 for i, e in t_ents.items() if p_ents.get(i, {}).get("kind") == e["kind"])
    res["entity_kind_accuracy"] = round(kind_ok / len(t_ents), 3)

    # tag classification: per truth tag, did the model put it in the right bucket?
    buckets = {"marker_tags": "marker", "value_tags": "value", "ref_tags": "ref"}
    total = correct = 0
    wrong: list[str] = []
    for i, t in t_ents.items():
        p = p_ents.get(i, {})
        pred_map = {}
        for key, label in buckets.items():
            for tag in p.get(key, []) or []:
                pred_map[tag] = label
        for key, label in buckets.items():
            for tag in t[key]:
                total += 1
                if pred_map.get(tag) == label:
                    correct += 1
                else:
                    wrong.append(f"{i}.{tag}: expected {label}, got {pred_map.get(tag, 'missing')}")
        extra = set(pred_map) - {x for k in buckets for x in t[k]}
        wrong += [f"{i}.{tag}: invented tag" for tag in sorted(extra)]
    res["tag_classification_accuracy"] = round(correct / total, 3) if total else 1.0
    res["tag_errors"] = wrong

    # relationships
    key = lambda r: (r.get("from"), r.get("tag"), r.get("to"), r.get("status"))
    p_rel = {key(r) for r in pred.get("relationships", []) if isinstance(r, dict)}
    t_rel = {key(r) for r in truth["relationships"]}
    res["relationships"] = prf(p_rel, t_rel)

    # invalid/unresolved reference detection
    t_bad = {r for r in t_rel if r[3] != "resolved"}
    p_bad = {r for r in p_rel if r[3] != "resolved"}
    res["invalid_ref_detection"] = prf(p_bad, t_bad)

    # missing relationships
    mk = lambda m: (m.get("entity"), m.get("expected_tag"))
    p_miss = {mk(m) for m in pred.get("missing_relationships", []) if isinstance(m, dict)}
    t_miss = {mk(m) for m in truth["missing_relationships"]}
    res["missing_relationship_detection"] = prf(p_miss, t_miss)

    # hallucination: predicted items with no counterpart in truth
    spurious = (len(p_rel - t_rel) + len(p_miss - t_miss) + len(set(p_ents) - set(t_ents)))
    predicted = len(p_rel) + len(p_miss) + len(p_ents)
    res["hallucination_rate"] = round(spurious / predicted, 3) if predicted else 0.0

    perfect = (res["entity_kind_accuracy"] == 1.0 and res["tag_classification_accuracy"] == 1.0
               and not res["relationships"]["false_positives"] and not res["relationships"]["missed"]
               and not res["missing_relationship_detection"]["false_positives"]
               and not res["missing_relationship_detection"]["missed"])
    res["perfect"] = perfect
    return res


def main() -> int:
    if len(sys.argv) < 2:
        print(__doc__)
        return 2
    data_path = sys.argv[2] if len(sys.argv) > 2 else os.path.join(os.path.dirname(__file__), "..", "data", "experiment3.json")
    try:
        with open(sys.argv[1], encoding="utf-8-sig") as f:
            text = f.read()
        with open(data_path, encoding="utf-8-sig") as f:
            truth = analyze(json.load(f)).to_eval_schema()
    except Exception as ex:  # noqa: BLE001
        print(f"ERROR: {ex}", file=sys.stderr)
        return 2

    pred, err = extract_json(text)
    if pred is None or not isinstance(pred, dict):
        print(json.dumps({"json_valid": False, "error": err}, indent=2))
        return 1
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    print(json.dumps(score(pred, truth), indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
