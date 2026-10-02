from pathlib import Path
from types import SimpleNamespace

from contract_checker.ai import review
from contract_checker.rules import _days, _months, check

EX = Path(__file__).parent.parent / "examples"


def rules_hit(text):
    return {f.rule for f in check(text).findings}


def test_bad_sample_is_flagged_everywhere():
    rep = check((EX / "sample_agreement.txt").read_text())
    hits = {f.rule for f in rep.findings}
    for rule in ["usage_perpetual", "paid_no_fee", "exclusivity", "pay_slow", "pay_trigger", "revisions",
                 "raw_files", "ip_transfer", "kill_fee", "morality_one_sided", "auto_renew", "disclosure", "law"]:
        assert rule in hits, rule
    assert rep.verdict == "negotiate before signing" and rep.score < 40


def test_fair_sample_passes():
    rep = check((EX / "fair_agreement.txt").read_text())
    assert [f.rule for f in rep.findings if f.severity != "low"] == []
    assert rep.verdict == "looks fair"
    assert rep.facts["usage period"] == "12 months" and rep.facts["payment terms"] == "30 days"


def test_number_parsing():
    assert _months("for six (6) months") == 6
    assert _months("usage for 2 years") == 24
    assert _days("payable net 45") == 45
    assert _days("within 14 days of invoice") == 14


def test_exclusivity_short_and_paid_is_fine():
    assert "exclusivity" not in rules_hit("Exclusivity for 1 month for named competitors, in consideration of the exclusivity fee. Fee paid net 30. Disclose with #ad. Governed by German law.")


def test_ai_review_drops_invented_clauses():
    rep = check((EX / "sample_agreement.txt").read_text())
    real = next(f.quote for f in rep.findings if f.rule == "ip_transfer")
    data = {"summary": "s", "negotiation_email": "e", "rewrites": [
        {"rule": "ip_transfer", "original": real, "proposed": "licence"},
        {"rule": "made_up", "original": "Clause that does not exist.", "proposed": "x"}]}
    fake = SimpleNamespace(messages=SimpleNamespace(create=lambda **kw: SimpleNamespace(
        content=[SimpleNamespace(type="tool_use", input=data)])))
    out = review(rep, client=fake)
    assert [r["rule"] for r in out["rewrites"]] == ["ip_transfer"]
