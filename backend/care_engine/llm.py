"""
LLM narrative generation via Claude API.

Generates a 2-3 sentence agent talking points summary from the
scored beneficiary profile. Uses claude-haiku-4-5-20251001 for
cost efficiency and speed appropriate for live call support.
"""

from django.conf import settings


def generate_narrative(scoring_result: dict, discussion_topics: list[dict]) -> tuple[str, bool]:
    """
    Returns (narrative_text, narrative_available).

    narrative_available is False when ANTHROPIC_API_KEY is not configured.
    Falls back gracefully without raising an exception.
    """
    api_key = getattr(settings, 'ANTHROPIC_API_KEY', '')
    if not api_key:
        return '', False

    try:
        import anthropic
        client = anthropic.Anthropic(api_key=api_key)

        condition_names = scoring_result.get('_condition_names', [])
        cancer_severity = scoring_result.get('_cancer_severity', 'unspecified')
        specialty_tiers = scoring_result.get('_specialty_tiers', [])
        med_count = scoring_result.get('_med_count', 0)
        has_specialty_drug = scoring_result.get('_has_specialty_drug', False)
        total_score = scoring_result.get('total_score', 0)
        intensity_level = scoring_result.get('intensity_level', 'Unknown')
        interactions = scoring_result.get('interactions_triggered', [])
        flags = scoring_result.get('flags', {})

        # Build a compact profile summary for the prompt
        condition_summary = ', '.join(condition_names) if condition_names else 'none reported'
        if 'Cancer' in condition_names and cancer_severity != 'unspecified':
            condition_summary = condition_summary.replace('Cancer', f'Cancer ({cancer_severity})')

        specialty_summary = ', '.join(specialty_tiers) if specialty_tiers else 'none'
        med_summary = f'{med_count} medications' if not flags.get('medication_data_missing') else 'unknown (not recorded)'
        specialty_drug_note = ' including specialty drugs' if has_specialty_drug else ''
        interaction_note = f' Notable comorbidity interactions: {", ".join(interactions)}.' if interactions else ''

        topic_bullets = '\n'.join(
            f'- {t["category"]}: {t["topic"]}' for t in discussion_topics[:5]
        )

        prompt = f"""You are a decision support tool for Medicare insurance agents on live calls.

Beneficiary care intensity profile:
- Care Intensity Score: {total_score}/100 ({intensity_level})
- Chronic conditions: {condition_summary}
- Provider specialties: {specialty_summary}
- Medications: {med_summary}{specialty_drug_note}{interaction_note}

Key plan areas identified for discussion:
{topic_bullets}

Generate 2-3 concise, actionable talking points a Medicare insurance agent can use right now on a live call with this beneficiary. Focus on what matters most for their plan selection. Be direct and specific. Do not use bullet points — write in plain sentences. Do not explain the scoring methodology."""

        message = client.messages.create(
            model='claude-haiku-4-5-20251001',
            max_tokens=300,
            messages=[{'role': 'user', 'content': prompt}],
        )

        narrative = message.content[0].text.strip()
        return narrative, True

    except Exception:
        return '', False
