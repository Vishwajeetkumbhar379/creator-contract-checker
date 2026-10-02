# Creator Contract Checker

**Catch the clauses that cost creators and brands money, before anyone signs.**

In five years of creator deals I saw the same problems again and again: usage rights that never expire, exclusivity that wipes out a creator's income, payment 90 days after "campaign end", unlimited revisions, and no ad-disclosure clause at all. Most of them are easy to fix if someone spots them early. This tool spots them in seconds.

```
$ contract-check examples/sample_agreement.txt

0/100 · negotiate before signing · 14 findings
  high   Usage rights never expire
  high   Broad or long exclusivity without a fee
  high   Payment in 90 days
  high   Unlimited revisions
  high   Creator gives up ownership
  medium Paid ads use with no extra fee
  medium Payment clock starts late
  medium Raw footage must be handed over
  medium No kill fee
  medium Automatic renewal
  medium No ad-disclosure clause
  ...
```

Each finding quotes the exact sentence from the contract, explains why it matters and what to ask for instead. Full report: [`examples/sample_agreement_review.md`](examples/sample_agreement_review.md). A fair contract ([`examples/fair_agreement.txt`](examples/fair_agreement.txt)) scores 100/100.

## What it checks

| Area | Flags |
|---|---|
| Usage rights | Perpetual or irrevocable use · usage over 12 months · paid ads or whitelisting with no extra fee · usage scope not defined |
| Exclusivity | Whole-category blocks or more than 3 months without an exclusivity fee |
| Money | Payment terms over 30 or 60 days · payment clock that starts at "campaign end" or "approval" · no deadline · no late-payment consequence |
| Work | Unlimited revisions · no deadline for brand feedback · raw footage handover |
| Ownership | Assignment of all rights or "work made for hire" instead of a licence |
| Ending the deal | No kill fee · one-sided morality clause · automatic renewal |
| Compliance | No ad-disclosure clause (Germany expects "Werbung" or "Anzeige") · no governing law |

It's useful from both sides of the table: creators see what to push back on, and brand teams see what will slow down negotiations or create compliance risk.

## Measured, not guessed

[`evals/`](evals/) holds hand-labelled clauses, including fair versions of each risky clause, so the rules are tested for false alarms as well as misses. CI runs it on every push:

```
$ python evals/run_evals.py
24 labelled clauses
| Rule               | Precision | Recall |
| usage_perpetual    | 100%      | 100%   |
| exclusivity        | 100%      | 100%   |
| ...                |           |        |
| overall            | 100%      | 100%   |
```

It's a small set I wrote myself, so treat it as a regression test, not a benchmark. Add real clauses to `evals/clauses.jsonl` and the numbers will tell you where the rules need work.

## Claude as the explainer, not the judge (optional)

```bash
pip install -e ".[ai]"
export ANTHROPIC_API_KEY=sk-...
contract-check my_contract.txt --ai --side creator
```

The rules decide what is risky. Claude then writes a plain-language summary, proposes fairer wording for each flagged clause, and drafts a friendly negotiation email, all as **structured JSON via tool use**. Any rewrite that doesn't quote a real flagged clause is thrown away in code, so the model can't invent contract terms.

## Run it

```bash
git clone https://github.com/Vishwajeetkumbhar379/creator-contract-checker
cd creator-contract-checker
pip install -e ".[dev]"
contract-check examples/sample_agreement.txt
pytest && python evals/run_evals.py
```

Paste the contract text into a `.txt` file first (copy it out of the PDF).

---

**Not legal advice.** This is a commercial checklist based on common negotiation practice. Have a lawyer review high-value or unusual agreements. The sample contracts are fictional.

Built by [Vishwajeet Kumbhar](https://www.linkedin.com/in/vishwajeetkumbhar379) with Claude Code. MIT licence.
