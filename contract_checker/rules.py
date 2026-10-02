"""Clause rules for influencer / creator agreements.

Each rule finds the sentence that triggered it, so every flag can be checked
against the contract itself. The rules encode common negotiation practice,
not law. This is a checklist for a commercial review, not legal advice.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field

SEVERITY_POINTS = {"high": 18, "medium": 9, "low": 3}


@dataclass
class Finding:
    rule: str
    title: str
    severity: str  # high | medium | low
    hurts: str  # creator | brand | both
    why: str
    fix: str
    quote: str = ""


@dataclass
class Report:
    findings: list[Finding] = field(default_factory=list)
    facts: dict[str, str] = field(default_factory=dict)

    @property
    def score(self) -> int:
        """100 = no issues found. Each finding takes points off by severity."""
        return max(0, 100 - sum(SEVERITY_POINTS[f.severity] for f in self.findings))

    @property
    def verdict(self) -> str:
        if any(f.severity == "high" for f in self.findings) or self.score < 60:
            return "negotiate before signing"
        if self.score < 85:
            return "minor fixes"
        return "looks fair"


def sentences(text: str) -> list[str]:
    text = re.sub(r"\s+", " ", text)
    return [s.strip() for s in re.split(r"(?<=[.;:])\s+(?=[A-Z0-9(])", text) if s.strip()]


def _find(sents: list[str], pattern: str) -> str:
    rx = re.compile(pattern, re.I)
    hits = [s for s in sents if rx.search(s)]
    # prefer real clauses over numbered headings like "4. Exclusivity."
    return next((s for s in hits if len(s.split()) > 4), hits[0] if hits else "")


def _months(s: str) -> int | None:
    m = re.search(r"(\d+|one|two|three|six|twelve|eighteen|twenty-four)\s*(\(\d+\)\s*)?(month|year)s?", s, re.I)
    if not m:
        return None
    words = {"one": 1, "two": 2, "three": 3, "six": 6, "twelve": 12, "eighteen": 18, "twenty-four": 24}
    n = int(m.group(1)) if m.group(1).isdigit() else words[m.group(1).lower()]
    return n * 12 if m.group(3).lower().startswith("year") else n


def _days(s: str) -> int | None:
    m = re.search(r"net\s*(\d+)|within\s+(\d+)\s*(\(\d+\)\s*)?(business |calendar )?days", s, re.I)
    return int(m.group(1) or m.group(2)) if m else None


def check(text: str) -> Report:
    sents = sentences(text)
    r = Report()
    add = r.findings.append

    # Usage rights ------------------------------------------------------------
    perpetual = _find(sents, r"\b(in perpetuity|perpetual|irrevocabl\w*|without (any )?time limit)\b")
    usage = _find(sents, r"\b(usage|use|licen[cs]e)\b.*\b(month|year)s?\b")
    if perpetual:
        add(Finding("usage_perpetual", "Usage rights never expire", "high", "creator",
                    "The brand can use the content forever, which normally costs several times a standard fee.",
                    "Limit usage to 6-12 months, or price perpetual use as a separate line item.", perpetual))
    elif usage and (m := _months(usage)):
        r.facts["usage period"] = f"{m} months"
        if m > 12:
            add(Finding("usage_long", f"Long usage period ({m} months)", "medium", "creator",
                        "Usage beyond 12 months is usually charged extra.", "Add a usage fee for every month beyond 12.", usage))
    elif not usage:
        add(Finding("usage_missing", "Usage rights not defined", "medium", "both",
                    "Without a defined scope, both sides can end up in a dispute about where the content may run.",
                    "State the channels, the duration and the territory.", ""))

    paid = _find(sents, r"\b(paid (media|social|ads?|advertising)|whitelist\w*|spark ads?|dark posts?|boost\w*|partnership ads?)\b")
    if paid:
        r.facts["paid amplification"] = "yes"
        if not re.search(r"\b(additional|separate|usage) fee|paid separately|at an extra\b", text, re.I):
            add(Finding("paid_no_fee", "Paid ads use with no extra fee", "medium", "creator",
                        "Running the content as ads (whitelisting) is worth more than organic posting.",
                        "Add a paid-usage fee and cap the ad flight duration.", paid))

    # Exclusivity -------------------------------------------------------------
    excl = _find(sents, r"\bexclusiv\w*|shall not (promote|work with|endorse)")
    if excl:
        m = _months(excl) or 0
        r.facts["exclusivity"] = f"{m} months" if m else "yes"
        broad = re.search(r"\b(any|all)\b[^.;]{0,40}\b(brands?|compan(y|ies)|products?|competitors?)\b|\bentire (category|industry)\b", excl, re.I)
        paid_for = re.search(r"exclusivity fee|in consideration of (the )?exclusivity", text, re.I)
        if (broad or m > 3) and not paid_for:
            add(Finding("exclusivity", "Broad or long exclusivity without a fee", "high" if broad and m > 3 else "medium", "creator",
                        "Blocking a whole category or several months can cost the creator other income.",
                        "Name the direct competitors, keep it to the campaign plus 30-90 days, and pay an exclusivity fee.", excl))

    # Money -------------------------------------------------------------------
    pay = _find(sents, r"\b(pay|paid|payment|invoice|fee)\b.*\b(net\s*\d+|within\s+\d+)")
    if pay:
        d = _days(pay)
        r.facts["payment terms"] = f"{d} days"
        trigger_late = re.search(r"\b(after|following|upon) (the )?(end of the campaign|campaign end|final approval|brand'?s? approval|completion of the campaign)", pay, re.I)
        if d and d > 60:
            add(Finding("pay_slow", f"Payment in {d} days", "high", "creator", "Waiting more than two months strains a creator's cash flow.",
                        "Ask for net 30, or 50% upfront and 50% on posting.", pay))
        elif d and d > 30:
            add(Finding("pay_slow", f"Payment in {d} days", "medium", "creator", "Net 30 is the usual standard.", "Negotiate down to net 30.", pay))
        if trigger_late:
            add(Finding("pay_trigger", "Payment clock starts late", "medium", "creator",
                        "Starting the clock at campaign end or brand approval can add weeks of delay.",
                        "Start the payment clock on the posting date or on invoice receipt.", pay))
    elif not re.search(r"\b(fee|compensation|payment)\b", text, re.I):
        add(Finding("pay_missing", "No payment terms found", "high", "creator", "There's no amount or timeline to enforce.",
                    "State the fee, the currency, the invoice trigger and net days.", ""))
    else:
        add(Finding("pay_terms_missing", "Fee mentioned but no payment deadline", "medium", "creator",
                    "Without a deadline, payment can drift.", "Add 'payable within 30 days of invoice'.", _find(sents, r"\b(fee|compensation|payment)\b")))

    if not re.search(r"\b(late payment|interest|penalt)", text, re.I) and pay:
        add(Finding("late_fee", "No late-payment consequence", "low", "creator", "Nothing happens if the brand pays late.",
                    "Add statutory late-payment interest (for B2B in Germany, 9 points above the base rate).", ""))

    # Work and approvals ------------------------------------------------------
    rev = _find(sents, r"\b(unlimited|as many|any number of) (revision|change|edit)s?|revisions? (as|until) (requested|the brand is satisfied)")
    if rev:
        add(Finding("revisions", "Unlimited revisions", "high", "creator", "Open-ended revisions can turn one post into weeks of work.",
                    "Cap it at two rounds; extra rounds billed.", rev))
    appr = _find(sents, r"\bapprov\w*")
    if appr and not re.search(r"\bwithin\s+\d+\s*(business |working )?(days|hours)\b", appr, re.I):
        add(Finding("approval_sla", "No deadline for brand approval", "low", "both", "Slow approvals push posting dates and payment.",
                    "Brand gives feedback within 3 business days or the draft counts as approved.", appr))

    raw = _find(sents, r"\b(raw (footage|files)|unedited|source files)\b")
    if raw:
        add(Finding("raw_files", "Raw footage must be handed over", "medium", "creator", "Raw files let the brand cut new ads without paying for new content.",
                    "Deliver final edits only, or charge for raw files.", raw))

    ip = _find(sents, r"\b(assigns?|transfer\w*) (all|any|full) (right|title|intellectual|ownership)|work(s)? (made )?for hire|sole (and exclusive )?owner")
    if ip:
        add(Finding("ip_transfer", "Creator gives up ownership", "high", "creator", "Assigning ownership is far more than a licence: the creator loses control of their own content.",
                    "Grant a limited licence instead and keep ownership.", ip))

    # Ending the deal ---------------------------------------------------------
    term = _find(sents, r"\bterminat\w*|cancel\w*")
    if term and not re.search(r"\b(kill|cancellation) fee\b|paid (in full|pro rata) for (work|content)", text, re.I):
        add(Finding("kill_fee", "No kill fee", "medium", "creator", "If the brand cancels late, the creator may not be paid for work already done.",
                    "Add a cancellation fee, for example 50% after the brief is accepted and 100% after content is delivered.", term))
    moral = _find(sents, r"\b(moral(ity)?|reputation|disrepute)\b")
    if moral and not re.search(r"\b(mutual|either party|each party)\b", moral, re.I):
        add(Finding("morality_one_sided", "One-sided morality clause", "low", "creator", "Only the brand can walk away over reputation issues.",
                    "Make it mutual, so the creator can also exit if the brand faces a scandal.", moral))
    auto = _find(sents, r"\bautomatically (renew|extend)\w*")
    if auto:
        add(Finding("auto_renew", "Automatic renewal", "medium", "both", "The deal (and any exclusivity) can roll on without anyone deciding.",
                    "Require written agreement to renew.", auto))

    # Compliance --------------------------------------------------------------
    if not re.search(r"\b(disclos\w*|#ad\b|werbung|anzeige|sponsored|paid partnership|advertis\w* label|label\w* as (an )?ad)", text, re.I):
        add(Finding("disclosure", "No ad-disclosure clause", "medium", "both",
                    "Both sides carry risk if a sponsored post isn't labelled. Rules differ by country (Germany expects 'Werbung' or 'Anzeige').",
                    "Name the exact label and placement, and switch on the platform's paid-partnership tag.", ""))
    if not re.search(r"\b(governing law|jurisdiction|governed by)\b", text, re.I):
        add(Finding("law", "No governing law", "low", "both", "If something goes wrong, it's unclear which country's courts apply.",
                    "Add a governing-law and jurisdiction clause.", ""))
    return r
