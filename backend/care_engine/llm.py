"""
LLM talking point generation via OpenAI API.

Returns a structured list of plan-attribute talking points for a Medicare
insurance agent on a live call. Each point names a specific plan attribute
(plan type, deductibles, copays, Rx coverage) and explains why it matters
for this beneficiary's profile.

Uses GPT-4o with JSON mode for consistent, parseable output.
"""

import json
from django.conf import settings

# Conditions that may qualify a beneficiary for a Chronic Special Needs Plan (CSNP)
CSNP_CONDITIONS = {
    'Heart failure', 'Diabetes mellitus', 'End-stage renal disease',
    'Chronic lung disorders', 'Cardiovascular disorders', 'Cancer',
    'HIV/AIDS', 'Autoimmune disorders', 'Neurologic disorders', 'Dementia',
}


def generate_narrative(scoring_result: dict, discussion_topics: list[dict], plan_data: dict | None = None) -> tuple[list, bool]:
    """
    Returns (talking_points, narrative_available).

    talking_points is a list of {attribute: str, text: str} dicts.
    narrative_available is False when OPENAI_API_KEY is not configured.
    Falls back gracefully without raising an exception.
    """
    api_key = getattr(settings, 'OPENAI_API_KEY', '')
    if not api_key:
        return [], False

    try:
        from openai import OpenAI
        client = OpenAI(api_key=api_key)

        condition_names = scoring_result.get('_condition_names', [])
        cancer_severity = scoring_result.get('_cancer_severity', 'unspecified')
        specialty_tiers = scoring_result.get('_specialty_tiers', [])
        med_count = scoring_result.get('_med_count', 0)
        has_specialty_drug = scoring_result.get('_has_specialty_drug', False)
        medicaid_dual = scoring_result.get('_medicaid_dual', False)
        interactions = scoring_result.get('interactions_triggered', [])
        flags = scoring_result.get('flags', {})

        # Build profile summary
        condition_summary = ', '.join(condition_names) if condition_names else 'none reported'
        if 'Cancer' in condition_names and cancer_severity != 'unspecified':
            condition_summary = condition_summary.replace('Cancer', f'Cancer ({cancer_severity})')

        specialty_summary = ', '.join(specialty_tiers) if specialty_tiers else 'none'
        med_summary = (
            f'{med_count} medications'
            if not flags.get('medication_data_missing')
            else 'unknown'
        )
        specialty_drug_note = ', including specialty drugs' if has_specialty_drug else ''
        interaction_note = (
            f'\n- Comorbidity interactions: {", ".join(interactions)}'
            if interactions else ''
        )

        # Special needs plan eligibility hints
        csnp_qualifying = [c for c in condition_names if c in CSNP_CONDITIONS]
        plan_type_hints = ''
        if medicaid_dual:
            plan_type_hints += '\n- Medicaid dual eligible: YES (DSNP eligibility applies)'
        else:
            plan_type_hints += '\n- Medicaid dual eligible: NO'
        if csnp_qualifying:
            plan_type_hints += f'\n- CSNP qualifying conditions present: {", ".join(csnp_qualifying)}'

        # Flag D-SNP ineligibility mismatch when plan is already known (plan-specific mode)
        if plan_data and plan_data.get('snp_type') == 'D-SNP' and not medicaid_dual:
            plan_type_hints += (
                '\n- ⚠️ CRITICAL ELIGIBILITY CONCERN: This is a D-SNP plan, but the '
                'beneficiary is NOT Medicaid dual-eligible. D-SNP enrollment requires '
                'concurrent Medicare and Medicaid coverage. This beneficiary likely '
                'cannot enroll in this plan.'
            )

        # ── Build prompt — two modes: generic vs plan-specific ─────────────
        if plan_data:
            # Plan-specific mode: reason about fit/gaps for the selected plan
            supps = ', '.join(plan_data.get('supplemental_benefits', [])) or 'None listed'
            snp_label = plan_data.get('snp_type') or 'None'
            if plan_data.get('csnp_condition'):
                snp_label += f" ({plan_data['csnp_condition']})"

            def fmt(val):
                """Format a numeric value as dollar string or 'N/A'."""
                if val is None:
                    return 'N/A'
                try:
                    return f'${float(val):,.0f}'
                except (ValueError, TypeError):
                    return str(val)

            plan_block = f"""The agent has selected a specific plan to evaluate:

Plan: {plan_data['plan_name']} by {plan_data['parent_org']}
Type: {plan_data['plan_type_label']} | SNP: {snp_label}
Monthly Premium: {fmt(plan_data['monthly_premium'])}
Health Deductible: {fmt(plan_data['health_deductible'])} | Drug Deductible: {fmt(plan_data['drug_deductible'])}
Out-of-Pocket Maximum: {fmt(plan_data['moop_in_network'])}
PCP Copay: {fmt(plan_data['pcp_copay_max'])} | Specialist Copay: {fmt(plan_data['specialist_copay_min'])}–{fmt(plan_data['specialist_copay_max'])}
Inpatient Hospital Copay: {fmt(plan_data['inpatient_hospital_copay'])}
Star Rating: {plan_data['overall_star_rating'] or 'N/A'}/5
Supplemental Benefits: {supps}"""

            prompt = f"""You are a Medicare plan advisor helping an insurance agent on a live call.

Beneficiary profile:
- Chronic conditions: {condition_summary}
- Provider specialties: {specialty_summary}
- Medications: {med_summary}{specialty_drug_note}{interaction_note}{plan_type_hints}

{plan_block}

Generate exactly 3 talking points about this specific plan's fit for this beneficiary. Each talking point must name a specific plan attribute and explain whether it is a strength or a concern for this beneficiary given their conditions and medications.

Respond with JSON in this exact format:
{{
  "talking_points": [
    {{"attribute": "Specialist Copay", "text": "1-2 sentences explaining whether this plan attribute is a strength or concern for this beneficiary."}},
    {{"attribute": "Drug Deductible", "text": "..."}},
    {{"attribute": "Plan Type", "text": "..."}}
  ]
}}

Rules:
- Each text must be 1-2 sentences, direct and specific to this beneficiary's conditions or medications
- Do not reference the care intensity score
- IMPORTANT: If the plan is a D-SNP and the beneficiary is NOT Medicaid dual-eligible, the FIRST talking point must flag this as a critical enrollment eligibility concern — the beneficiary cannot enroll in a D-SNP without Medicaid coverage
- IMPORTANT: Do not mention drug formulary coverage (specific drugs covered or excluded) or provider network participation — these are not reflected in the plan data and must not be inferred"""

        else:
            # Generic mode: recommend what attributes to look for (no plan selected)
            prompt = f"""You are a Medicare plan advisor helping an insurance agent on a live call.

Beneficiary profile:
- Chronic conditions: {condition_summary}
- Provider specialties: {specialty_summary}
- Medications: {med_summary}{specialty_drug_note}{interaction_note}{plan_type_hints}

Generate exactly 3 talking points for the agent. Each talking point should focus on ONE specific plan attribute that is most relevant to this beneficiary's profile.

Choose attributes from: plan type (CSNP or DSNP), medical deductible, hospital inpatient coverage, monthly premium, primary care copay, specialist copay, Rx deductible, specialty drug tier cost sharing.

Respond with JSON in this exact format:
{{
  "talking_points": [
    {{"attribute": "Plan Type (CSNP)", "text": "1-2 sentences starting with Look for plans that... or Prioritize plans with... explaining why this attribute matters for this specific beneficiary."}},
    {{"attribute": "Specialist Copays", "text": "..."}},
    {{"attribute": "Rx Deductible", "text": "..."}}
  ]
}}

Rules:
- Each text must be 1-2 sentences, direct and specific to this beneficiary's conditions or medications
- Do not mention specific plan names or exact dollar amounts
- Do not reference the care intensity score
- IMPORTANT: Do not mention drug formulary coverage (specific drugs covered or excluded) or provider network participation — these are not reflected and must not be inferred"""

        response = client.chat.completions.create(
            model='gpt-4o',
            max_tokens=500,
            response_format={'type': 'json_object'},
            messages=[
                {'role': 'system', 'content': 'You are a concise Medicare plan advisor. Respond only with valid JSON.'},
                {'role': 'user', 'content': prompt},
            ],
        )

        data = json.loads(response.choices[0].message.content)
        talking_points = data.get('talking_points', [])

        # Validate structure
        talking_points = [
            p for p in talking_points
            if isinstance(p, dict) and 'attribute' in p and 'text' in p
        ]

        return talking_points, True

    except Exception:
        return [], False
