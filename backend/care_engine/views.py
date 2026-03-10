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
    providers = Provider.objects.all()
    return Response(ProviderSerializer(providers, many=True).data)


@api_view(['GET'])
def medications_list(request):
    medications = Medication.objects.all()
    return Response(MedicationSerializer(medications, many=True).data)


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

    discussion_topics = get_discussion_topics(scoring_result)
    narrative, narrative_available = generate_narrative(scoring_result, discussion_topics)

    # Strip internal _keys before returning
    response = {
        'total_score': scoring_result['total_score'],
        'intensity_level': scoring_result['intensity_level'],
        'breakdown': scoring_result['breakdown'],
        'interactions_triggered': scoring_result['interactions_triggered'],
        'flags': scoring_result['flags'],
        'discussion_topics': discussion_topics,
        'narrative': narrative,
        'narrative_available': narrative_available,
    }

    return Response(response)
