# Care Intensity Engine — Scoring Rationale

**Last Updated:** 2026-03-10
**Model Version:** MVP v1.0
**Status:** Initial weights — pending clinical review and empirical calibration

Reference: CMS-HCC Model V28 (CY 2024)
Source document: `CY 2024 AN_FINAL_20230131.pdf`

> **Note on V28 coefficients**: The coefficient values below are approximate, derived
> from training data (knowledge cutoff Aug 2025). Before treating these as final, verify
> against the source document Table V-1 (condition factors) and Table II-6 (demographic
> factors). Run `brew install poppler` to enable PDF reading in Claude sessions.

---

## Score Architecture

```
Total Score (0–100) = normalize(Component 1 + Component 2 + Component 3 + Component 4 + Component 5)

Components:
  Demographic Base      (0-15)
  Chronic Conditions    (0-35)
  Provider Complexity   (0-25)
  Medication Burden     (0-25)
  Comorbidity Interactions (0-10)

Theoretical max: 110
```

### Partial-Data Normalization

When only some components have data, the raw sum is normalized to the maximum
achievable from the filled components:

```
filled_max = sum of caps for components with data
total_score = min(round(raw_total / filled_max × 100), 100)
```

**Inclusion rules:**
- Conditions + Interactions (max 45): included if any condition is selected
- Providers (max 25): included if any provider is selected
- Medications (max 25): included if any medication is selected
- Demographics (max 15): included only when a primary component (conditions or meds)
  is also present AND age+sex are known

**Rationale**: Scoring relative to what's been assessed prevents artificially low scores
from depressing the intensity level before the call profile is complete. A beneficiary
with Heart Failure (12 pts) alone scores 27/100 (Moderate) rather than 12/100 (Low).
As more components are filled, the score converges toward the true absolute value.

**Note on score drift (resolved 2026-03-13)**: Providers and medications no longer
expand the `filled_max` denominator when a condition baseline is present. Both act
as pure additive bonuses — adding more care data can only increase or maintain the
score. Medications remain in the denominator only when they are the sole primary
data source (no conditions entered), to avoid a zero denominator.

### Intensity Thresholds

| Score | Level | Clinical Interpretation |
|---|---|---|
| 0–24 | Low | Standard MA coverage likely sufficient |
| 25–49 | Moderate | Enhanced coverage features worth discussing |
| 50–74 | High | Complex care needs; specialist access and drug coverage critical |
| 75–100 | Very High | High utilization expected; full plan comparison essential |

---

## Component 1: Demographic Base Score (0–15 pts)

**Rationale**: Age and sex predict baseline utilization independent of diagnosed conditions.
Derived from CMS-HCC V28 Community Non-Medicaid demographic RAF factors, normalized to 0–15.

Normalization: raw RAF range ~0.302–0.579 → linear scale to 0–15.

| Age Band | Female | Male |
|---|---|---|
| Under 65 (disabled) | 4 | 4 |
| 65–70 | 1 | 1 |
| 70–75 | 2 | 3 |
| 75–80 | 6 | 7 |
| 80+ | 11 | 12 |
| Unknown | 0 + flag | 0 + flag |

**Medicaid Dual Status Bonus**: +3 pts
Rationale: Medicaid dually eligible beneficiaries have higher predicted utilization
(V28 Medicaid demographic factor adds ~0.07–0.08 RAF).

**Missing data handling**: When age/sex is unknown, score 0 pts and set
`demographic_data_missing: true` in the response.

---

## Component 2: Chronic Condition Score (0–35 pts)

**Rationale**: Conditions are the primary driver of care intensity. Weights are
conceptually aligned with CMS-HCC V28 condition factors (Table V-1).

### Cancer Severity Toggle

Cancer's RAF varies enormously by stage/type:
- Metastatic/acute leukemia (HCC 8): RAF ~2.65 → **14 pts**
- Lung/other severe cancers (HCC 9): RAF ~1.00
- Lymphoma (HCC 10): RAF ~0.68  → History/managed average: **7 pts**
- Colorectal/bladder (HCC 11): RAF ~0.34
- Breast/prostate (HCC 12): RAF ~0.18

When "Cancer" is selected in the UI, a severity toggle appears:
- **Active / Metastatic** → 14 pts
- **History / Managed** → 7 pts
- **Unspecified** → 10 pts (default middle estimate)

### Condition Weight Table

| Condition | HCC Reference | V28 RAF (approx) | Score Pts |
|---|---|---|---|
| Cancer (active/metastatic) | HCC 8 | ~2.65 | **14** |
| Cancer (history/managed) | HCC 9–12 | ~0.18–1.00 | **7** |
| Heart failure | HCC 85 | ~0.323 | **12** |
| End-stage renal disease | HCC 134–138 | ~0.289–0.617 | **12** |
| Dementia | HCC 51–52 | ~0.246–0.369 | **11** |
| HIV/AIDS | HCC 1 | ~0.344 | **10** |
| Hematologic disorders | HCC 46–48 | ~0.260–0.913 | **9** |
| Stroke | HCC 100–103 | ~0.274 | **8** |
| Neurologic disorders | HCC 72–78 | ~0.249–0.427 | **7** |
| Cardiovascular disorders | HCC 86–111 | ~0.149–0.461 | **7** |
| Chronic lung disorders | HCC 161–162 | ~0.170–0.273 | **7** |
| Autoimmune disorders | HCC 40 | ~0.421 | **5** |
| Mental health conditions | HCC 186–188 | ~0.395–0.422 | **5** |
| Diabetes mellitus | HCC 17–19 | ~0.118–0.302 | **4** |

**Cap**: Sum of condition points capped at 35.

---

## Component 3: Provider Complexity Score (0–25 pts)

**Rationale**: Specialist presence signals both care complexity and plan network sensitivity.
Multiple providers in the same specialty count once (deduplication by specialty).

| Tier | Specialties | Pts per unique specialty |
|---|---|---|
| High | Oncology, Nephrology, Cardiology, Neurology, Hematology, Infectious Disease | 7 |
| Medium | Endocrinology, Pulmonology, Psychiatry, Rheumatology, Transplant | 5 |
| Low | All other specialists | 2 |
| Base | Primary Care Physician | 0 |

**Cap**: 25 pts.

**Specialty tier mapping** is defined in `care_engine/management/commands/load_providers.py`
as a Python dict. Update this dict to change how free-text specialty names map to tiers.

---

## Component 4: Medication Burden Score (0–25 pts)

**Rationale**: Polypharmacy is strongly correlated with care complexity and adherence risk.
Bucket thresholds are aligned with observed distribution in Spark platform data
(n=20,126 beneficiaries with known medication counts, analysis date: 2026-03-10).

| Bucket | Observed % of known | Score Pts |
|---|---|---|
| 0 medications | 51.8% | 0 |
| 1–2 medications | 18.7% | 5 |
| 3–5 medications | 13.2% | 10 |
| 5–10 medications | 13.9% | 18 |
| 10+ medications | 2.4% | 22 |
| + any specialty drug | — | +3 |

**Cap**: 25 pts.

**Unknown medication count** (~31.4% of all Spark records had no medication data):
Score 0 pts and set `medication_data_missing: true`. Never impute a default.

---

## Component 5: Comorbidity Interaction Bonuses (0–10 pts)

**Rationale**: CMS-HCC V28 includes interaction terms for condition pairs where
comorbidity creates additional utilization beyond each condition's individual factor.

| Condition Pair | V28 Interaction Factor | Bonus Pts |
|---|---|---|
| Heart failure + Diabetes | ~0.121 | 4 |
| Heart failure + Chronic lung disorders | ~0.164 | 5 |
| ESRD + Cardiovascular disorders | ~0.068 | 3 |
| Diabetes + ESRD | ~0.122 | 4 |

**Cap**: Total interaction bonus capped at 10 pts.
Multiple pairs can trigger simultaneously and stack up to the cap.

---

## Open Questions

1. **Interaction pair completeness**: V28 has more interaction terms than the 4 we've
   implemented (e.g., CHF + Renal, Diabetes + Renal NEC). Should we add more? Requires
   verifying against Table V-2 in the source document.

2. **Cancer severity default**: Should the default be "unspecified" (10 pts) or
   "active" (14 pts) to avoid undercounting high-risk beneficiaries?

3. **Unknown medication handling**: Should a missing medication count surface an
   explicit warning/prompt to the agent in the UI, rather than silently scoring 0?

4. **Provider specialty matching**: The current mapping is exact-string match against
   a predefined dict. Should we implement fuzzy matching for CSV uploads with non-standard
   specialty names?

5. **Institutional beneficiaries**: CMS uses different demographic factors for
   nursing home / long-term institutional beneficiaries. Currently we assume all
   beneficiaries are community-dwelling. Should we add an institutional flag?

---

## Change Log

| Date | Change | Rationale |
|---|---|---|
| 2026-03-13 | Removed providers and medications (when conditions present) from `filled_max` denominator in `scoring.py` | Adding low-scoring providers (PCPs, low-tier specialists) or generic medications was causing the normalized score to drop due to denominator expansion exceeding numerator contribution. Providers and medications are now treated as additive complexity signals — they can only increase the score, never decrease it. |
| 2026-03-10 | Added filled_max normalization for partial data | Score reflects complexity relative to assessed components; prevents artificial Low ratings when profile is incomplete |
| 2026-03-10 | Initial weights set for MVP | Based on CMS-HCC V28 conceptual alignment |
| 2026-03-10 | Medication buckets calibrated to Spark data | n=29,347 distribution analysis |
| 2026-03-10 | Added demographic component (age+sex+Medicaid) | CMS-HCC V28 demographic factors |
| 2026-03-10 | Added comorbidity interaction bonuses | CMS-HCC V28 Table V-2 interaction terms |
| 2026-03-10 | Added Cancer severity toggle | RAF range 0.18–2.65 too wide for single score |
| 2026-03-10 | Provider scoring changed to per-unique-specialty | Prevent double-counting same specialty |

---

## Conversation Template

When saving a new conversation to `context/conversations/`, use this format:

```markdown
# [Topic] — YYYY-MM-DD

**Date:** YYYY-MM-DD
**Topic:** One-line description

## Context
Why this conversation happened and what was being decided.

## Decisions Made
- Decision 1 (reasoning)
- Decision 2 (reasoning)

## Open Questions
- Question 1

## Next Steps
- [ ] Action item

## Score Impact
Describe any changes made to scoring weights or logic.
```
