# Correctness review of `output/risks.json` vs. the original document

Method: every extracted risk was checked against the raw page text (ingested
from `VestasAnnualReport2025.pdf`). For each item, three questions in order:

1. **Disclosure type** — did the company disclose this as a *risk* (financial-
   materiality "Risk" cell, or `Type of impact: Risk`), or as an *impact* /
   *opportunity*?
2. **Materiality** — was it scored immaterial / `N/A`, or is it a live disclosure?
3. **Discreteness** — is it a nameable principal risk, or is it narrative / process /
   an accounting footnote / a restatement?

This review covers the two verdicts that matter: the **golden set** (what the eval
scores) and the **full run** (what the extractor actually emitted).

## Golden set (`src/risk_pipeline/evaluation/golden.json`)

14 hand-adjudicated entries across the covered pages — 8 valid risks and 6 traps.
The set is page-complete for the pages it covers (`Risk management` p.50–51,
`Material impacts, risks, and opportunities` p.74, `Climate change` p.86).

| id | title | page | expected | reason |
|---|---|---|---|---|
| g01 | Geopolitics and regulatory framework | 51 | risk | one of the three Main risks columns |
| g02 | Project execution | 51 | risk | one of the three Main risks columns |
| g03 | Cyber attacks | 51 | risk | one of the three Main risks columns |
| g04 | Insufficient market conditions | 74 | risk | right-column financial risk |
| g05 | Cyber security risks | 74 | risk | right-column financial risk |
| g06 | Risk of corruption and bribery | 74 | risk | right-column financial risk |
| g07 | Climate transition investment and technology maturity risk | 86 | risk | significant investments + immature solutions stated as a risk |
| g08 | Dependence on political action | 86 | risk | business outlook depends on political action |
| n01 | Operational, Commercial, Macroeconomic, and Regulatory Challenges | 50 | trap | ERM overview sentence listing risk *categories* |
| n02 | Climate Change and Responsible Business Conduct Risks | 50 | trap | ERM review-cadence narrative, not a disclosure |
| n03 | Land-use restrictions during construction | 74 | trap | left-column impact; paired risks scored immaterial |
| n04 | Impacts on indigenous peoples' rights | 74 | trap | left-column impact; no paired financial risk |
| n05 | Uncertainties in Climate Scenario Analysis | 86 | trap | caveat about the analysis method |
| n06 | Physical climate risks (water stress and extreme rainfall) | 86 | trap | explicitly stated as not financially material |

## Full run verdict (15 entries)

| # | title | page | verdict | golden |
|---|---|---|---|---|
| 1 | Geopolitics and regulatory framework | 51 | CORRECT | g01 |
| 2 | Project execution | 51 | CORRECT | g02 |
| 3 | Cyber attacks | 51 | CORRECT | g03 |
| 4 | Carbon taxes and tariffs (materials) | 71 | CORRECT (out of scope) | — |
| 5 | Cost implication of injuries in own workforce | 73 | CORRECT (out of scope) | — |
| 6 | Cost implications of injuries to contractors | 73 | CORRECT (out of scope) | — |
| 7 | Fines related to forced or child labour | 73 | CORRECT (out of scope) | — |
| 8 | Insufficient market conditions for wind deployment | 74 | CORRECT | g04 |
| 9 | Cyber security risks | 74 | CORRECT | g05 |
| 10 | Risk of corruption and bribery | 74 | CORRECT | g06 |
| 11 | Carbon taxes and tariffs (transition) | 85 | CORRECT (out of scope) | — |
| 12 | Climate transition investment and technology maturity risk | 86 | CORRECT | g07 |
| 13 | Political and policy dependency risk | 86 | CORRECT | g08 |
| 14 | Increased costs from carbon taxes and tariffs on conventional steel | 87 | DUPLICATE | — |
| 15 | Cyber-Attacks and Power Outage Disruptions | 118 | CORRECT (out of scope) | — |

- **No false positives.** The traps (`n01`–`n06`) are all ignored.
- **14 of 15 are distinct correct principal risks.** #14 is a restatement of #11
  (carbon taxes/tariffs on steel) one page later in the same section; the no-merge
  design emits it, and it is counted as a duplicate rather than a golden entry.
- Entry #11 (Carbon taxes, p.85) and #14 (p.87) sit one page either side of g07 on
  p.86 — all three are the same transition theme disclosed separately.

## Eval result

```
risk-pipeline VestasAnnualReport2025.pdf --eval
```

```
predictions: 15 (7 out of scope)
golden: 8 valid + 6 traps
true positives: 8   false positives: 0   false negatives: 0
precision: 1.000  recall: 1.000  f1 score: 1.000
category accuracy: 1.000 (8 correct, 0 incorrect)
mitigation accuracy: 1.000 (8 correct, 0 missing, 0 hallucinated, 0 mismatch)
gates: passed
```

Category and mitigation are adjudicated against the source pages: the three p.51
Main risks state a "How we manage it" mitigation; the p.74 IRO table states no
mitigation (so a non-null mitigation there would be a hallucination); the two p.86
risks share one mitigation sentence.

The 7 out-of-scope predictions are legitimate risks on pages the golden set does
not sample (p.71, 73, 85, 87, 118); the evaluator ignores them by design so the
sample stays fair.

## How we got here

Earlier iterations had 11–16 entries and flipped between false positives and
misses. The fix was prompt-level, not eval-level:

- Replaced a document-specific prompt with a **generic** one that defines a
  principal risk and excludes impacts, opportunities, immaterial/`N/A` rows, ERM
  narrative, passing mentions, and accounting caveats.
- That reintroduced a p.50 regression (an "adverse effect" clause admitted the ERM
  overview). Sharpened the exclusions to name "a general statement that the company
  is exposed to risks" and "a passing mention inside actions, policies, targets, or
  metrics" specifically.
- Result: p.50 traps ignored, all 8 sampled valid risks recovered, no false
  positives. See `eval/README.md` for the harness.
