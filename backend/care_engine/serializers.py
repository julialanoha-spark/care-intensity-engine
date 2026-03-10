from rest_framework import serializers
from care_engine.models import ChronicCondition, Provider, Medication


class ChronicConditionSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChronicCondition
        fields = ['id', 'name', 'tier', 'base_score', 'display_order']


class ProviderSerializer(serializers.ModelSerializer):
    class Meta:
        model = Provider
        fields = ['id', 'name', 'specialty', 'specialty_tier', 'specialty_score', 'npi']


class MedicationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Medication
        fields = ['id', 'name', 'dosage', 'category', 'is_specialty']


class ScoreRequestSerializer(serializers.Serializer):
    age_band = serializers.ChoiceField(
        choices=['under_65', '65_70', '70_75', '75_80', '80_plus', 'unknown'],
        required=False,
        default='unknown',
    )
    sex = serializers.ChoiceField(
        choices=['female', 'male', 'unknown'],
        required=False,
        default='unknown',
    )
    medicaid_dual = serializers.BooleanField(required=False, default=False)
    condition_ids = serializers.ListField(
        child=serializers.IntegerField(),
        required=False,
        default=list,
    )
    cancer_severity = serializers.ChoiceField(
        choices=['active', 'managed', 'unspecified'],
        required=False,
        default='unspecified',
    )
    provider_ids = serializers.ListField(
        child=serializers.IntegerField(),
        required=False,
        default=list,
    )
    medication_ids = serializers.ListField(
        child=serializers.IntegerField(),
        required=False,
        default=list,
    )
