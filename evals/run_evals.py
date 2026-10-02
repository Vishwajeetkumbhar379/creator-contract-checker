"""Measure each rule's precision and recall on labelled clauses.

Disclosure, governing law, payment and usage-missing checks look at the whole
contract, so on single clauses they fire on almost everything; they are excluded
here and covered by the full-contract tests instead.
"""
import json
from collections import Counter
from pathlib import Path

from contract_checker.rules import check

DOC_LEVEL = {"disclosure", "law", "pay_missing", "pay_terms_missing", "usage_missing", "late_fee", "approval_sla"}

tp, fp, fn = Counter(), Counter(), Counter()
rows = [json.loads(l) for l in (Path(__file__).parent / "clauses.jsonl").read_text().splitlines() if l.strip()]
for row in rows:
    got = {f.rule for f in check(row["text"]).findings} - DOC_LEVEL
    want = set(row["expect"])
    for r in got & want:
        tp[r] += 1
    for r in got - want:
        fp[r] += 1
        print(f"FALSE ALARM {r}: {row['text']}")
    for r in want - got:
        fn[r] += 1
        print(f"MISSED      {r}: {row['text']}")

rules = sorted(set(tp) | set(fp) | set(fn))
print(f"\n{len(rows)} labelled clauses\n\n| Rule | Precision | Recall |\n|---|---:|---:|")
for r in rules:
    p = tp[r] / (tp[r] + fp[r]) if tp[r] + fp[r] else 0
    rc = tp[r] / (tp[r] + fn[r]) if tp[r] + fn[r] else 0
    print(f"| {r} | {p:.0%} | {rc:.0%} |")
T, F, N = sum(tp.values()), sum(fp.values()), sum(fn.values())
print(f"| **overall** | **{T / (T + F):.0%}** | **{T / (T + N):.0%}** |")
