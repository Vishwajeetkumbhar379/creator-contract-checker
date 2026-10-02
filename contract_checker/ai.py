"""Optional Claude layer: explain the findings in plain language and redraft the riskiest clauses.

Claude never decides what is risky; the rules do. Claude only explains and proposes
wording for clauses the rules already flagged, returned as structured JSON.
"""
from __future__ import annotations

import os

from .rules import Report

MODEL = os.environ.get("CONTRACT_MODEL", "claude-sonnet-4-5")
TOOL = {
    "name": "record_review",
    "description": "Record a plain-language summary and proposed clause rewrites.",
    "input_schema": {
        "type": "object",
        "properties": {
            "summary": {"type": "string", "description": "3-4 sentences a creator or brand manager can act on."},
            "rewrites": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {"rule": {"type": "string"}, "original": {"type": "string"}, "proposed": {"type": "string"}},
                    "required": ["rule", "original", "proposed"],
                },
            },
            "negotiation_email": {"type": "string", "description": "A short, friendly email asking for the changes. Under 150 words."},
        },
        "required": ["summary", "rewrites", "negotiation_email"],
    },
}
SYSTEM = (
    "You help creators and brand partnership managers review influencer contracts. "
    "You only rewrite clauses that appear in the flagged findings, quoting the original exactly. "
    "Keep proposals fair to both sides and commercially realistic. You are not a lawyer and do not give legal advice."
)


def review(report: Report, side: str = "creator", client=None) -> dict:
    if client is None:
        import anthropic

        client = anthropic.Anthropic()
    flagged = [
        {"rule": f.rule, "issue": f.title, "severity": f.severity, "quote": f.quote, "suggested_direction": f.fix}
        for f in report.findings if f.quote
    ]
    msg = client.messages.create(
        model=MODEL, max_tokens=1500, system=SYSTEM, tools=[TOOL],
        tool_choice={"type": "tool", "name": "record_review"},
        messages=[{"role": "user", "content": f"I am the {side}. Flagged clauses:\n{flagged}\nKnown terms: {report.facts}"}],
    )
    out = dict(next(b for b in msg.content if getattr(b, "type", "") == "tool_use").input)
    quotes = {f.quote for f in report.findings}
    out["rewrites"] = [rw for rw in out.get("rewrites", []) if rw.get("original") in quotes]  # no invented clauses
    return out
