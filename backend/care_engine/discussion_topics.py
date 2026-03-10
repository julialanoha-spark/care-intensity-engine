"""
Rule-based plan discussion topic generator.

Produces a list of plan areas an agent should discuss based on the
beneficiary's condition profile, provider complexity, and score.

Topics are ordered by urgency (most critical first).
"""


def get_discussion_topics(scoring_result: dict) -> list[dict]:
    """
    Returns a list of discussion topic objects:
      { 'category': str, 'topic': str, 'reason': str }
    """
    condition_names = set(scoring_result.get('_condition_names', []))
    cancer_severity = scoring_result.get('_cancer_severity', 'unspecified')
    specialty_tiers = scoring_result.get('_specialty_tiers', [])
    med_count = scoring_result.get('_med_count', 0)
    has_specialty_drug = scoring_result.get('_has_specialty_drug', False)
    total_score = scoring_result.get('total_score', 0)
    medication_missing = scoring_result.get('flags', {}).get('medication_data_missing', False)

    topics = []

    # --- Condition-specific topics ---

    if 'Cancer' in condition_names:
        if cancer_severity == 'active':
            topics.append({
                'category': 'Prescription Drug Coverage',
                'topic': 'Oncology drug formulary and specialty tier costs',
                'reason': 'Active cancer treatment typically involves high-cost specialty drugs; verify formulary coverage and tier placement.',
            })
            topics.append({
                'category': 'Care Coordination',
                'topic': 'Care coordination and clinical trial access',
                'reason': 'Active cancer patients may benefit from integrated oncology care management programs and clinical trial coverage.',
            })
        else:
            topics.append({
                'category': 'Prescription Drug Coverage',
                'topic': 'Ongoing cancer medication coverage',
                'reason': 'Maintenance oncology medications may be on specialty tiers; review Part D formulary.',
            })

    if 'End-stage renal disease' in condition_names:
        topics.append({
            'category': 'Provider Network',
            'topic': 'Dialysis facility network coverage',
            'reason': 'ESRD patients typically require frequent dialysis; confirm preferred dialysis centers are in-network.',
        })
        topics.append({
            'category': 'Prescription Drug Coverage',
            'topic': 'ESRD-specific medication coverage (ESAs, phosphate binders)',
            'reason': 'Medications like erythropoietin agents and cinacalcet can be high-cost specialty drugs.',
        })

    if 'Heart failure' in condition_names:
        topics.append({
            'category': 'Care Management',
            'topic': 'Heart failure care management and home health benefits',
            'reason': 'Patients with heart failure benefit from care management programs and may need home health visits.',
        })

    if 'Dementia' in condition_names:
        topics.append({
            'category': 'Supplemental Benefits',
            'topic': 'Long-term care services and caregiver support',
            'reason': 'Dementia patients often require caregiver coordination; look for plans with memory care or respite benefits.',
        })

    if 'HIV/AIDS' in condition_names:
        topics.append({
            'category': 'Prescription Drug Coverage',
            'topic': 'HIV antiretroviral formulary coverage',
            'reason': 'ART regimens (bictegravir/emtricitabine combinations) are specialty-tier drugs; verify formulary position and cost sharing.',
        })

    if 'Mental health conditions' in condition_names:
        topics.append({
            'category': 'Provider Network',
            'topic': 'Behavioral health network and mental health parity',
            'reason': 'Verify in-network psychiatric providers and confirm mental health parity compliance for inpatient/outpatient coverage.',
        })

    if 'Diabetes mellitus' in condition_names:
        topics.append({
            'category': 'Prescription Drug Coverage',
            'topic': 'Insulin cost cap, CGM coverage, and diabetes supplies',
            'reason': 'IRA insulin cap applies; continuous glucose monitors may be covered under DME or Part D depending on plan.',
        })

    if 'Chronic lung disorders' in condition_names:
        topics.append({
            'category': 'Prescription Drug Coverage',
            'topic': 'Pulmonary medication coverage (inhalers, specialty biologics)',
            'reason': 'Maintenance inhalers and specialty pulmonary drugs (e.g., nintedanib) vary widely by formulary.',
        })

    if 'Stroke' in condition_names:
        topics.append({
            'category': 'Care Management',
            'topic': 'Post-stroke rehabilitation and home health benefits',
            'reason': 'Stroke recovery often requires ongoing physical, occupational, and speech therapy coverage.',
        })

    if 'Autoimmune disorders' in condition_names:
        topics.append({
            'category': 'Prescription Drug Coverage',
            'topic': 'Biologic and immunosuppressant drug coverage',
            'reason': 'Biologics like adalimumab are among the most expensive specialty drugs; prior authorization requirements vary.',
        })

    if 'Cardiovascular disorders' in condition_names:
        topics.append({
            'category': 'Care Management',
            'topic': 'Cardiac rehabilitation and preventive care benefits',
            'reason': 'Cardiac rehab programs may be covered; preventive screenings and lifestyle programs vary by plan.',
        })

    if 'Neurologic disorders' in condition_names:
        topics.append({
            'category': 'Provider Network',
            'topic': 'Neurology specialist access and continuity of care',
            'reason': 'Ongoing neurological management requires reliable in-network specialist access.',
        })

    if 'Hematologic disorders' in condition_names:
        topics.append({
            'category': 'Prescription Drug Coverage',
            'topic': 'Hematology specialty drug coverage',
            'reason': 'Drugs like ibrutinib, hydroxyurea, and rituximab are high-cost specialty tier; verify formulary and prior auth.',
        })

    # --- Medication-specific topics ---

    if medication_missing:
        topics.append({
            'category': 'Prescription Drug Coverage',
            'topic': 'Complete medication list needed for formulary review',
            'reason': 'No medications were recorded for this beneficiary. A full medication review is essential for accurate plan comparison.',
        })
    elif med_count >= 6:
        topics.append({
            'category': 'Prescription Drug Coverage',
            'topic': 'Formulary tier review and polypharmacy cost exposure',
            'reason': f'{med_count} medications increases Part D cost exposure; review tier placement, preferred pharmacy networks, and annual out-of-pocket projections.',
        })

    if has_specialty_drug:
        topics.append({
            'category': 'Prescription Drug Coverage',
            'topic': 'Specialty drug cost sharing and prior authorization',
            'reason': 'One or more specialty drugs are present; verify specialty tier cost sharing, prior authorization requirements, and step therapy rules.',
        })

    # --- Provider network topics ---

    high_specialty_count = sum(1 for t in specialty_tiers if 'oncolog' in t or 'nephrol' in t
                                or 'cardiol' in t or 'neurol' in t or 'hematol' in t
                                or 'infectious' in t)
    if high_specialty_count >= 2:
        topics.append({
            'category': 'Provider Network',
            'topic': 'Specialist network breadth and referral requirements',
            'reason': 'Multiple high-complexity specialists require verifying all are in-network and confirming whether referrals are required.',
        })

    # --- Score-based topics ---

    if total_score >= 50:
        topics.append({
            'category': 'Cost Protection',
            'topic': 'Out-of-pocket maximum and catastrophic coverage threshold',
            'reason': 'High care intensity increases annual cost exposure; compare MOOP limits and how quickly each plan hits catastrophic coverage.',
        })

    if total_score >= 75:
        topics.append({
            'category': 'Supplemental Benefits',
            'topic': 'Supplemental benefits: transportation, meal delivery, home support',
            'reason': 'Very high intensity beneficiaries often have non-clinical needs; identify plans with robust supplemental benefit packages.',
        })

    return topics
