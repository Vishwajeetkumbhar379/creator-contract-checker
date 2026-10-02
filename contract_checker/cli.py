"""contract-check examples/sample_agreement.txt [--ai] [--side creator|brand]"""
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

from .rules import check

ICON = {"high": "🔴", "medium": "🟠", "low": "🟡"}


def to_markdown(name: str, rep, ai: dict | None = None) -> str:
    lines = [f"# Contract check · {name}", "", f"**Score:** {rep.score}/100 · **Verdict:** {rep.verdict}", ""]
    if rep.facts:
        lines += ["| Term | Found |", "|---|---|", *[f"| {k} | {v} |" for k, v in rep.facts.items()], ""]
    order = {"high": 0, "medium": 1, "low": 2}
    for f in sorted(rep.findings, key=lambda f: order[f.severity]):
        lines += [f"### {ICON[f.severity]} {f.title}", f"*{f.severity} · affects the {f.hurts}*", "", f.why, ""]
        if f.quote:
            lines += [f"> {f.quote}", ""]
        lines += [f"**Ask for:** {f.fix}", ""]
    if ai:
        lines += ["## AI summary", "", ai["summary"], ""]
        for rw in ai["rewrites"]:
            lines += [f"**{rw['rule']}**", "", f"> {rw['original']}", "", f"Proposed: {rw['proposed']}", ""]
        lines += ["## Negotiation email", "", ai["negotiation_email"], ""]
    lines += ["<sub>A commercial checklist, not legal advice. Have a lawyer review high-value or unusual agreements.</sub>"]
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="contract-check", description="Flag risky clauses in an influencer agreement.")
    ap.add_argument("file", type=Path, help="Contract as .txt or .md (copy the text out of a PDF first)")
    ap.add_argument("--out", type=Path)
    ap.add_argument("--ai", action="store_true", help="Add a Claude summary, clause rewrites and a negotiation email")
    ap.add_argument("--side", choices=["creator", "brand"], default="creator")
    a = ap.parse_args(argv)
    rep = check(a.file.read_text(encoding="utf-8"))
    ai = None
    if a.ai:
        if os.environ.get("ANTHROPIC_API_KEY"):
            from .ai import review

            ai = review(rep, a.side)
        else:
            print("Set ANTHROPIC_API_KEY to use --ai.", file=sys.stderr)
    md = to_markdown(a.file.stem.replace("_", " "), rep, ai)
    out = a.out or a.file.with_name(a.file.stem + "_review.md")
    out.write_text(md, encoding="utf-8")
    print(f"{rep.score}/100 · {rep.verdict} · {len(rep.findings)} findings")
    for f in rep.findings:
        print(f"  {f.severity:<6} {f.title}")
    print(f"Report: {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
