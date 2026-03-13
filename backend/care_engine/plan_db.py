"""
Direct read-only queries against plan_fit_2026.db (8,081 MA plans, 2026).

No Django models or migrations needed — this file is queried via sqlite3.
"""

import os
import sqlite3

from django.conf import settings

# ── C-SNP condition keyword mapping ────────────────────────────────────────
CSNP_KEYWORDS = {
    'Heart & Vascular': ['heart', 'cardiac', 'cardio', 'chf', 'coronary'],
    'Diabetes':         ['diabet', 'glucose'],
    'ESRD':             ['esrd', 'renal', 'kidney', 'dialysis'],
    'Cancer':           ['cancer', 'oncol'],
    'Lung/COPD':        ['copd', 'breath', 'pulm', 'lung', 'respiratory'],
    'Dementia':         ['dementia', 'alzheimer', 'cognitive', 'memory', 'clarity'],
    'HIV/AIDS':         ['hiv', 'aids'],
    'Neurological':     ['neuro'],
}

PLAN_TYPE_LABELS = {
    '01': 'HMO',
    '02': 'HMO-POS',
    '04': 'PPO',
    '29': 'PDP',
}


def _get_db_path():
    return os.path.join(settings.BASE_DIR, '..', 'plan_fit_2026.db')


def _parse_csnp_condition(plan_name: str) -> str | None:
    """Return the chronic condition name if parseable from the plan name, else None."""
    if not plan_name:
        return None
    name_lower = plan_name.lower()
    for condition, keywords in CSNP_KEYWORDS.items():
        if any(kw in name_lower for kw in keywords):
            return condition
    return None


def search_plans(search_query: str, state_code: str | None = None, limit: int = 30) -> list[dict]:
    """
    Search plans by name/org. Optionally filter to a specific state.

    Returns a list of plan dicts for use in the typeahead UI.
    Excludes employer-only plans and PDP (Part D only) plans.

    If search_query is empty but state_code is provided, returns top plans for
    that state sorted by star rating (ZIP auto-load mode).
    """
    has_query = search_query and len(search_query.strip()) >= 2

    if not has_query and not state_code:
        return []

    if has_query:
        tokens = search_query.strip().split()
        name_conditions = ' AND '.join([f"p.plan_name LIKE ?" for _ in tokens])
        params = [f'%{t}%' for t in tokens]
    else:
        # State-only browse — no name filter
        name_conditions = '1=1'
        params = []

    # Optional state filter via service area
    state_clause = ''
    if state_code:
        state_clause = """
            AND EXISTS (
                SELECT 1 FROM plan_service_areas psa
                WHERE psa.contract_id = p.contract_id
                  AND psa.plan_id = p.plan_id
                  AND psa.state_code = ?
            )
        """
        params.append(state_code)

    params.append(limit)

    sql = f"""
        SELECT
            p.contract_id,
            p.plan_id,
            p.segment_id,
            p.plan_name,
            p.parent_org,
            pc.snp_type,
            pc.plan_type,
            co.monthly_premium,
            co.health_deductible,
            co.drug_deductible,
            co.moop_in_network,
            co.pcp_copay_max,
            co.specialist_copay_min,
            co.specialist_copay_max,
            co.inpatient_hospital_copay,
            sr.overall_star_rating
        FROM plans p
        JOIN plan_characteristics pc
            ON p.contract_id = pc.contract_id
           AND p.plan_id     = pc.plan_id
           AND p.segment_id  = pc.segment_id
        JOIN plan_costs co
            ON p.contract_id = co.contract_id
           AND p.plan_id     = co.plan_id
           AND p.segment_id  = co.segment_id
        LEFT JOIN contract_star_ratings sr
            ON p.contract_id = sr.contract_id
        WHERE {name_conditions}
          AND pc.employer_only_plan = '2'
          AND pc.plan_type != '29'
          {state_clause}
        ORDER BY sr.overall_star_rating DESC NULLS LAST, p.plan_name
        LIMIT ?
    """

    conn = sqlite3.connect(_get_db_path())
    conn.row_factory = sqlite3.Row
    try:
        cur = conn.execute(sql, params)
        rows = cur.fetchall()
    finally:
        conn.close()

    results = []
    for row in rows:
        snp_type = row['snp_type']
        csnp_condition = (
            _parse_csnp_condition(row['plan_name'])
            if snp_type == 'C-SNP' else None
        )
        results.append({
            'contract_id':       row['contract_id'],
            'plan_id':           row['plan_id'],
            'segment_id':        row['segment_id'],
            'plan_name':         row['plan_name'],
            'parent_org':        row['parent_org'],
            'snp_type':          snp_type,
            'csnp_condition':    csnp_condition,
            'plan_type':         row['plan_type'],
            'plan_type_label':   PLAN_TYPE_LABELS.get(row['plan_type'], row['plan_type'] or ''),
            'monthly_premium':   row['monthly_premium'],
            'health_deductible': row['health_deductible'],
            'drug_deductible':   row['drug_deductible'],
            'moop_in_network':   row['moop_in_network'],
            'pcp_copay_max':     row['pcp_copay_max'],
            'specialist_copay_min': row['specialist_copay_min'],
            'specialist_copay_max': row['specialist_copay_max'],
            'inpatient_hospital_copay': row['inpatient_hospital_copay'],
            'overall_star_rating': row['overall_star_rating'],
        })

    return results


def get_plan_by_id(contract_id: str, plan_id: str, segment_id: str) -> dict | None:
    """
    Fetch full plan attributes for a selected plan, including supplemental benefits.
    Used to build the LLM talking points prompt when a plan is selected.
    """
    sql = """
        SELECT
            p.contract_id,
            p.plan_id,
            p.segment_id,
            p.plan_name,
            p.parent_org,
            pc.snp_type,
            pc.plan_type,
            co.monthly_premium,
            co.health_deductible,
            co.drug_deductible,
            co.moop_in_network,
            co.pcp_copay_max,
            co.specialist_copay_min,
            co.specialist_copay_max,
            co.inpatient_hospital_copay,
            sb.has_vision,
            sb.has_dental,
            sb.has_hearing,
            sb.has_otc,
            sb.has_fitness,
            sb.has_transportation,
            sb.has_telehealth,
            sb.dental_amount,
            sb.vision_amount,
            sb.otc_amount,
            sr.overall_star_rating
        FROM plans p
        JOIN plan_characteristics pc
            ON p.contract_id = pc.contract_id
           AND p.plan_id     = pc.plan_id
           AND p.segment_id  = pc.segment_id
        JOIN plan_costs co
            ON p.contract_id = co.contract_id
           AND p.plan_id     = co.plan_id
           AND p.segment_id  = co.segment_id
        LEFT JOIN plan_supplemental_benefits sb
            ON p.contract_id = sb.contract_id
           AND p.plan_id     = sb.plan_id
           AND p.segment_id  = sb.segment_id
        LEFT JOIN contract_star_ratings sr
            ON p.contract_id = sr.contract_id
        WHERE p.contract_id = ?
          AND p.plan_id     = ?
          AND p.segment_id  = ?
        LIMIT 1
    """

    conn = sqlite3.connect(_get_db_path())
    conn.row_factory = sqlite3.Row
    try:
        cur = conn.execute(sql, [contract_id, plan_id, segment_id])
        row = cur.fetchone()
    finally:
        conn.close()

    if not row:
        return None

    snp_type = row['snp_type']
    csnp_condition = (
        _parse_csnp_condition(row['plan_name'])
        if snp_type == 'C-SNP' else None
    )

    # Collect supplemental benefits that are present
    supps = []
    if row['has_dental']:    supps.append(f"Dental (${row['dental_amount'] or '?'}/yr)" if row['dental_amount'] else 'Dental')
    if row['has_vision']:    supps.append(f"Vision (${row['vision_amount'] or '?'}/yr)" if row['vision_amount'] else 'Vision')
    if row['has_hearing']:   supps.append('Hearing')
    if row['has_otc']:       supps.append(f"OTC (${row['otc_amount'] or '?'}/period)" if row['otc_amount'] else 'OTC')
    if row['has_fitness']:   supps.append('Fitness')
    if row['has_transportation']: supps.append('Transportation')
    if row['has_telehealth']:     supps.append('Telehealth')

    return {
        'contract_id':       row['contract_id'],
        'plan_id':           row['plan_id'],
        'segment_id':        row['segment_id'],
        'plan_name':         row['plan_name'],
        'parent_org':        row['parent_org'],
        'snp_type':          snp_type,
        'csnp_condition':    csnp_condition,
        'plan_type_label':   PLAN_TYPE_LABELS.get(row['plan_type'], row['plan_type'] or ''),
        'monthly_premium':   row['monthly_premium'],
        'health_deductible': row['health_deductible'],
        'drug_deductible':   row['drug_deductible'],
        'moop_in_network':   row['moop_in_network'],
        'pcp_copay_max':     row['pcp_copay_max'],
        'specialist_copay_min': row['specialist_copay_min'],
        'specialist_copay_max': row['specialist_copay_max'],
        'inpatient_hospital_copay': row['inpatient_hospital_copay'],
        'overall_star_rating': row['overall_star_rating'],
        'supplemental_benefits': supps,
    }
