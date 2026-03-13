from functools import reduce
from django.db.models import Q
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status

from care_engine.models import ChronicCondition, Provider, Medication
from care_engine.serializers import (
    ChronicConditionSerializer,
    ProviderSerializer,
    MedicationSerializer,
    ScoreRequestSerializer,
)
from care_engine.scoring import calculate_score
from care_engine.discussion_topics import get_discussion_topics
from care_engine.llm import generate_narrative


@api_view(['GET'])
def conditions_list(request):
    conditions = ChronicCondition.objects.all()
    return Response(ChronicConditionSerializer(conditions, many=True).data)


@api_view(['GET'])
def providers_list(request):
    q = request.query_params.get('search', '').strip()
    if not q or len(q) < 2:
        return Response([])
    words = q.split()
    name_filter = reduce(lambda a, b: a & b, [Q(name__icontains=w) for w in words])
    providers = (
        Provider.objects
        .filter(name_filter)
        .order_by('specialty_tier', 'name')[:60]
    )
    return Response(ProviderSerializer(providers, many=True).data)


@api_view(['GET'])
def medications_list(request):
    medications = Medication.objects.all()
    return Response(MedicationSerializer(medications, many=True).data)


@api_view(['GET'])
def plans_list(request):
    q = request.query_params.get('search', '').strip()
    zip_code = request.query_params.get('zip', '').strip()
    has_query = q and len(q) >= 2
    has_zip = zip_code and len(zip_code) == 5

    if not has_query and not has_zip:
        return Response([])

    state_code = None
    if has_zip:
        try:
            import zipcodes
            matches = zipcodes.matching(zip_code)
            if matches:
                state_code = matches[0].get('state')
        except Exception:
            pass

    from care_engine.plan_db import search_plans
    results = search_plans(q, state_code=state_code)
    return Response(results)


@api_view(['POST'])
def score(request):
    serializer = ScoreRequestSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    data = serializer.validated_data

    scoring_result = calculate_score(
        age_band=data['age_band'],
        sex=data['sex'],
        medicaid_dual=data['medicaid_dual'],
        condition_ids=data['condition_ids'],
        cancer_severity=data['cancer_severity'],
        provider_ids=data['provider_ids'],
        medication_ids=data['medication_ids'],
    )

    # Strip internal _keys before returning (no LLM call — fast path)
    response = {
        'total_score': scoring_result['total_score'],
        'intensity_level': scoring_result['intensity_level'],
        'breakdown': scoring_result['breakdown'],
        'interactions_triggered': scoring_result['interactions_triggered'],
        'flags': scoring_result['flags'],
        'completeness': scoring_result['completeness'],
        # Profile context for the score reasoning display
        'condition_names': scoring_result['_condition_names'],
        'specialty_tiers': scoring_result['_specialty_tiers'],
        'med_count': scoring_result['_med_count'],
        'has_specialty_drug': scoring_result['_has_specialty_drug'],
        'age_band': data['age_band'],
        'sex': data['sex'],
        'medicaid_dual': data['medicaid_dual'],
    }

    return Response(response)


@api_view(['POST'])
def reasoning(request):
    """
    LLM talking-point generation — called separately from score so the
    deterministic score returns immediately without waiting on OpenAI.
    Requires a fully-identified plan (contract_id, plan_id, segment_id).
    """
    serializer = ScoreRequestSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    data = serializer.validated_data

    plan_contract_id = data.get('plan_contract_id', '')
    plan_plan_id     = data.get('plan_plan_id', '')
    plan_segment_id  = data.get('plan_segment_id', '')

    if not (plan_contract_id and plan_plan_id and plan_segment_id):
        return Response({'talking_points': [], 'narrative_available': False})

    from care_engine.plan_db import get_plan_by_id
    plan_data = get_plan_by_id(plan_contract_id, plan_plan_id, plan_segment_id)

    scoring_result = calculate_score(
        age_band=data['age_band'],
        sex=data['sex'],
        medicaid_dual=data['medicaid_dual'],
        condition_ids=data['condition_ids'],
        cancer_severity=data['cancer_severity'],
        provider_ids=data['provider_ids'],
        medication_ids=data['medication_ids'],
    )

    discussion_topics = get_discussion_topics(scoring_result)
    talking_points, narrative_available = generate_narrative(
        scoring_result, discussion_topics, plan_data=plan_data
    )

    return Response({
        'talking_points': talking_points,
        'narrative_available': narrative_available,
    })
