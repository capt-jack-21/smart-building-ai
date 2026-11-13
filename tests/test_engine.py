import json
import os
import sys
import unittest

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "experiments"))

from hsengine import analyze, classify_tag, normalize_id  # noqa: E402
from score_exp3 import extract_json, score  # noqa: E402


def load(name):
    with open(os.path.join(ROOT, "data", name), encoding="utf-8") as f:
        return json.load(f)


def codes(g):
    return sorted((i.code, i.entity) for i in g.issues)


class TagTests(unittest.TestCase):
    def test_marker_ref_value(self):
        self.assertEqual(classify_tag("sensor", "m:").kind, "marker")
        self.assertEqual(classify_tag("equipRef", "equip-001").kind, "ref")
        self.assertEqual(classify_tag("equipRef", "r:equip-001 AHU-01").kind, "ref")
        self.assertEqual(classify_tag("unit", "°C").kind, "value")
        self.assertEqual(classify_tag("curVal", "n:21.5 °C").value, {"value": 21.5, "unit": "°C"})
        self.assertEqual(classify_tag("ahu", {"_kind": "marker"}).kind, "marker")

    def test_true_is_value_unless_opted_in(self):
        self.assertEqual(classify_tag("ahu", True).kind, "value")
        self.assertEqual(classify_tag("ahu", True, truthy_markers=True).kind, "marker")

    def test_normalize_id(self):
        self.assertEqual(normalize_id("r:abc-1 Some Name"), "abc-1")
        self.assertEqual(normalize_id("@abc-1"), "abc-1")
        self.assertIsNone(normalize_id(""))
        self.assertIsNone(normalize_id(5))


class Experiment2(unittest.TestCase):
    def test_experiment2_records(self):
        g = analyze([
            {"id": "site-001", "dis": "London Office", "site": "m:", "geoCity": "London"},
            {"id": "equip-001", "dis": "AHU-01", "equip": "m:", "ahu": "m:", "siteRef": "site-001"},
            {"id": "point-001", "dis": "AHU-01 Supply Air Temperature", "point": "m:", "temp": "m:",
             "sensor": "m:", "air": "m:", "unit": "°C", "equipRef": "equip-001"},
        ])
        self.assertTrue(g.ok)
        self.assertEqual(g.issues, [])
        p = g.get("point-001")
        self.assertIn("sensor", p.markers)          # marker tag, NOT a "sensor type"
        self.assertNotIn("sensor", p.value_tags)
        self.assertEqual([r.tag for r in g.relationships], ["siteRef", "equipRef"])  # tags verbatim, no 'measures_via'
        self.assertEqual(g.site_of["point-001"], "site-001")        # derived through equipment
        self.assertEqual([e.id for e in g.points_of_equip("equip-001")], ["point-001"])


class Experiment3(unittest.TestCase):
    def setUp(self):
        self.g = analyze(load("experiment3.json"))

    def test_issues(self):
        self.assertEqual(codes(self.g), [("MISSING_EXPECTED_REF", "point-002"), ("UNRESOLVED_REF", "point-003")])
        self.assertFalse(self.g.ok)

    def test_relationships(self):
        got = {(r.source, r.tag, r.target, r.status) for r in self.g.relationships}
        self.assertEqual(got, {("equip-001", "siteRef", "site-001", "resolved"),
                               ("point-001", "equipRef", "equip-001", "resolved"),
                               ("point-003", "equipRef", "equip-999", "unresolved")})

    def test_hierarchy(self):
        h = self.g.hierarchy
        self.assertEqual([p["id"] for p in h["sites"][0]["equips"][0]["points"]], ["point-001"])
        self.assertEqual(sorted(h["unattached"]["points"]), ["point-002", "point-003"])


class Validation(unittest.TestCase):
    base = [{"id": "s", "site": "m:"}, {"id": "e", "equip": "m:", "siteRef": "s"}]

    def test_wrong_target_kind(self):
        g = analyze(self.base + [{"id": "p", "point": "m:", "sensor": "m:", "equipRef": "s"}])
        self.assertIn(("REF_WRONG_TARGET_KIND", "p"), codes(g))

    def test_duplicate_missing_id_and_no_kind(self):
        g = analyze([{"id": "a", "site": "m:"}, {"id": "a", "site": "m:"}, {"dis": "x"}, {"id": "b"}])
        self.assertEqual({c for c, _ in codes(g)}, {"DUPLICATE_ID", "MISSING_ID", "NO_ENTITY_KIND"})

    def test_marker_with_value(self):
        g = analyze([{"id": "p", "point": "m:", "sensor": "yes"}])
        self.assertIn(("KNOWN_MARKER_NOT_MARKER", "p"), codes(g))

    def test_ref_tag_not_ref(self):
        g = analyze(self.base + [{"id": "p", "point": "m:", "sensor": "m:", "equipRef": "m:"}])
        self.assertIn(("REF_TAG_NOT_REF", "p"), codes(g))

    def test_siteref_mismatch(self):
        g = analyze([{"id": "s1", "site": "m:"}, {"id": "s2", "site": "m:"},
                     {"id": "e", "equip": "m:", "siteRef": "s1"},
                     {"id": "p", "point": "m:", "sensor": "m:", "equipRef": "e", "siteRef": "s2"}])
        self.assertIn(("SITEREF_MISMATCH", "p"), codes(g))

    def test_nested_equip_inherits_site_and_cycle_detected(self):
        g = analyze(self.base + [{"id": "v", "equip": "m:", "equipRef": "e"}])
        self.assertEqual(g.site_of["v"], "s")
        self.assertEqual(g.hierarchy["sites"][0]["equips"][0]["children"][0]["id"], "v")
        c = analyze(self.base + [{"id": "x", "equip": "m:", "equipRef": "y"}, {"id": "y", "equip": "m:", "equipRef": "x"}])
        self.assertIn(("EQUIP_REF_CYCLE", "x"), codes(c))
        self.assertIn("x", c.hierarchy["unattached"]["equips"])

    def test_haystack_grid_input(self):
        g = analyze({"meta": {}, "cols": [], "rows": self.base})
        self.assertTrue(g.ok)


class Scorer(unittest.TestCase):
    def setUp(self):
        self.truth = analyze(load("experiment3.json")).to_eval_schema()

    def test_perfect_answer(self):
        r = score(json.loads(json.dumps(self.truth)), self.truth)
        self.assertTrue(r["perfect"])
        self.assertEqual(r["hallucination_rate"], 0.0)

    def test_experiment2_style_mistakes_are_penalised(self):
        bad = json.loads(json.dumps(self.truth))
        for e in bad["entities"]:
            if e["id"] == "point-001":                        # 'sensor' mislabelled as a value tag
                e["marker_tags"].remove("sensor"); e["value_tags"].append("sensor")
        bad["relationships"].append({"from": "point-002", "tag": "equipRef", "to": "equip-001", "status": "resolved"})  # invented
        bad["missing_relationships"] = []                      # missed the orphan
        r = score(bad, self.truth)
        self.assertFalse(r["perfect"])
        self.assertLess(r["tag_classification_accuracy"], 1.0)
        self.assertGreater(r["hallucination_rate"], 0.0)
        self.assertEqual(r["missing_relationship_detection"]["recall"], 0.0)

    def test_extract_json_handles_fences_and_think(self):
        obj, err = extract_json('<think>hmm</think>\n```json\n{"a": 1}\n```')
        self.assertEqual(obj, {"a": 1})
        self.assertIsNone(extract_json("not json")[0])


if __name__ == "__main__":
    unittest.main()
