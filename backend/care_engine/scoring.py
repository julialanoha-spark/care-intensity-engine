"""
Care Intensity Scoring Engine

Calculates a 0-100 Care Intensity Score from five components:
  1. Demographic base (age, sex, Medicaid dual status)
  2. Chronic condition score (HCC-aligned weights)
  3. Provider complexity (per unique specialty tier)
  4. Medication burden (polypharmacy + specialty drug flag)
  5. Comorbidity interaction bonuses

Reference: CMS-HCC Model V28 (CY 2024)
See context/SCORING_RATIONALE.md for full rationale and change log.
"""

from care_engine.models import ChronicCondition, Provider, Medication, DemographicFactor

# Cancer condition name — used for severity toggle logic
CANCER_CONDITION_NAME = 'Cancer'

# Cancer severity score overrides
CANCER_SEVERITY_SCORES = {
    'active': 14,       # Metastatic / active treatment (HCC 8, RAF ~2.65)
    'managed': 7,       # History / managed cancer (HCC 9-12, RAF ~0.18-1.00)
    'unspecified': 10,  # Default middle estimate
}

# Comorbidity interaction pairs: {frozenset({name_a, name_b}): bonus_pts}
# Modeled after CMS-HCC V28 interaction terms
INTERACTION_PAIRS = {
    frozenset({'Heart failure', 'Diabetes mellitus'}): 4,
    frozenset({'Heart failure', 'Chronic lung disorders'}): 5,
    frozenset({'End-stage renal disease', 'Cardiovascular disorders'}): 3,
    frozenset({'Diabetes mellitus', 'End-stage renal disease'}): 4,
}

MEDICAID_DUAL_BONUS = 3

# Score component caps
CAP_DEMOGRAPHIC = 15
CAP_CONDITIONS = 35
CAP_PROVIDERS = 25
CAP_MEDICATIONS = 25
CAP_INTERACTIONS = 10
CAP_TOTAL = 100


def calculate_score(
    age_band: str,
    sex: str,
    medicaid_dual: bool,
    condition_ids: list[int],
    cancer_severity: str,
    provider_ids: list[int],
    medication_ids: list[int],
) -> dict:
    """
    Returns a full scoring result dict including breakdown, flags, and
    all data needed for downstream discussion topic and narrative generation.
    """
    demographic_score, demographic_missing = _demographic_score(age_band, sex, medicaid_dual)
    condition_score, condition_names = _condition_score(condition_ids, cancer_severity)
    provider_score, specialty_tiers = _provider_score(provider_ids)
    medication_score, med_count, has_specialty_drug, medication_missing = _medication_score(medication_ids)
    interaction_score, interactions_triggered = _interaction_score(condition_names)

    raw_total = demographic_score + condition_score + provider_score + medication_score + interaction_score

    # --- Partial-data normalization ---
    # Determine which components have substantive data
    demo_has_data = not demographic_missing          # age AND sex are known
    conditions_have_data = len(condition_ids) > 0
    providers_have_data = len(provider_ids) > 0
    meds_have_data = len(medication_ids) > 0

    # At least one "primary" component (conditions or medications) must be present
    # to produce a meaningful score. Demographics alone aren't enough.
    primary_has_data = conditions_have_data or meds_have_data

    if primary_has_data:
        filled_max = 0
        if conditions_have_data:
            filled_max += CAP_CONDITIONS                          # 35
            if len(condition_ids) >= 2:
                filled_max += CAP_INTERACTIONS                    # +10 only if interactions can fire
        # Providers and medications are additive complexity signals — they increase
        # the numerator but do not expand the denominator when a condition
        # baseline exists (adding them should never lower the score).
        # Medications stay in the denominator only when serving as the sole
        # primary data source (no conditions), to prevent a zero denominator.
        if meds_have_data and not conditions_have_data:
            filled_max += CAP_MEDICATIONS                    # 25
        # Demographics included in filled_max only when primary data is present
        if demo_has_data:
            filled_max += CAP_DEMOGRAPHIC                    # 15
        total_score = min(round(raw_total / filled_max * 100), CAP_TOTAL)
    else:
        filled_max = 0
        total_score = 0

    completeness = {
        'demographics': demo_has_data,
        'conditions': conditions_have_data,
        'providers': providers_have_data,
        'medications': meds_have_data,
        'filled_max': filled_max,
    }

    return {
        'total_score': total_score,
        'intensity_level': _intensity_level(total_score),
        'breakdown': {
            'demographic_score': demographic_score,
            'condition_score': condition_score,
            'provider_score': provider_score,
            'medication_score': medication_score,
            'interaction_bonus': interaction_score,
        },
        'interactions_triggered': interactions_triggered,
        'flags': {
            'demographic_data_missing': demographic_missing,
            'medication_data_missing': medication_missing,
        },
        'completeness': completeness,
        # Pass through for discussion topics and LLM narrative
        '_condition_names': condition_names,
        '_cancer_severity': cancer_severity,
        '_specialty_tiers': specialty_tiers,
        '_med_count': med_count,
        '_has_specialty_drug': has_specialty_drug,
        '_medicaid_dual': medicaid_dual,
    }


def _demographic_score(age_band: str, sex: str, medicaid_dual: bool) -> tuple[int, bool]:
    missing = (not age_band or age_band == 'unknown') or (not sex or sex == 'unknown')

    try:
        factor = DemographicFactor.objects.get(age_band=age_band or 'unknown', sex=sex or 'unknown')
        base = factor.base_score
    except DemographicFactor.DoesNotExist:
        base = 0

    score = min(base + (MEDICAID_DUAL_BONUS if medicaid_dual else 0), CAP_DEMOGRAPHIC)
    return score, missing


def _condition_score(condition_ids: list[int], cancer_severity: str) -> tuple[int, list[str]]:
    if not condition_ids:
        return 0, []

    conditions = ChronicCondition.objects.filter(id__in=condition_ids)
    condition_names = list(conditions.values_list('name', flat=True))

    total = 0
    for condition in conditions:
        if condition.name == CANCER_CONDITION_NAME:
            score = CANCER_SEVERITY_SCORES.get(cancer_severity or 'unspecified', 10)
        else:
            score = condition.base_score
        total += score

    return min(total, CAP_CONDITIONS), condition_names


def _provider_score(provider_ids: list[int]) -> tuple[int, list[str]]:
    if not provider_ids:
        return 0, []

    providers = list(Provider.objects.filter(id__in=provider_ids))

    # Deduplicate by specialty — highest score wins per specialty
    specialty_best: dict[str, int] = {}
    for provider in providers:
        specialty_key = provider.specialty.lower().strip()
        current_best = specialty_best.get(specialty_key, 0)
        if provider.specialty_score > current_best:
            specialty_best[specialty_key] = provider.specialty_score

    total = sum(specialty_best.values())

    # Return ALL unique specialties for display (not just scored ones — base-tier
    # providers like primary care still deserve to appear in the breakdown)
    all_specialties = list(dict.fromkeys(
        p.specialty.lower().strip() for p in providers
    ))
    return min(total, CAP_PROVIDERS), all_specialties


def _medication_score(medication_ids: list[int]) -> tuple[int, int, bool, bool]:
    missing = not medication_ids

    if missing:
        return 0, 0, False, True

    medications = Medication.objects.filter(id__in=medication_ids)
    med_count = medications.count()
    has_specialty_drug = medications.filter(is_specialty=True).exists()

    if med_count == 0:
        polypharmacy_score = 0
    elif med_count <= 2:
        polypharmacy_score = 5
    elif med_count <= 5:
        polypharmacy_score = 10
    elif med_count <= 10:
        polypharmacy_score = 18
    else:
        polypharmacy_score = 22

    specialty_bonus = 3 if has_specialty_drug else 0
    total = min(polypharmacy_score + specialty_bonus, CAP_MEDICATIONS)
    return total, med_count, has_specialty_drug, False


def _interaction_score(condition_names: list[str]) -> tuple[int, list[str]]:
    if len(condition_names) < 2:
        return 0, []

    name_set = set(condition_names)
    total = 0
    triggered = []

    for pair, bonus in INTERACTION_PAIRS.items():
        if pair.issubset(name_set):
            total += bonus
            triggered.append(' + '.join(sorted(pair)))

    return min(total, CAP_INTERACTIONS), triggered


def _intensity_level(score: int) -> str:
    if score >= 75:
        return 'Very High'
    elif score >= 50:
        return 'High'
    elif score >= 25:
        return 'Moderate'
    return 'Low'
