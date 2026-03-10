from django.db import models


class ChronicCondition(models.Model):
    TIER_HIGH = 'high'
    TIER_MEDIUM = 'medium'
    TIER_LOW = 'low'
    TIER_CHOICES = [
        (TIER_HIGH, 'High Complexity'),
        (TIER_MEDIUM, 'Medium Complexity'),
        (TIER_LOW, 'Low Complexity'),
    ]

    name = models.CharField(max_length=100, unique=True)
    tier = models.CharField(max_length=10, choices=TIER_CHOICES)
    base_score = models.IntegerField()
    display_order = models.IntegerField(default=0)

    class Meta:
        ordering = ['display_order', 'name']

    def __str__(self):
        return self.name


class Provider(models.Model):
    TIER_HIGH = 'high'
    TIER_MEDIUM = 'medium'
    TIER_LOW = 'low'
    TIER_BASE = 'base'
    TIER_CHOICES = [
        (TIER_HIGH, 'High Complexity Specialty'),
        (TIER_MEDIUM, 'Medium Complexity Specialty'),
        (TIER_LOW, 'Other Specialist'),
        (TIER_BASE, 'Primary Care'),
    ]

    name = models.CharField(max_length=150)
    specialty = models.CharField(max_length=100)
    specialty_tier = models.CharField(max_length=10, choices=TIER_CHOICES, default=TIER_LOW)
    specialty_score = models.IntegerField(default=2)
    npi = models.CharField(max_length=20, blank=True, default='')

    class Meta:
        ordering = ['specialty', 'name']

    def __str__(self):
        return f"{self.name} ({self.specialty})"


class Medication(models.Model):
    name = models.CharField(max_length=150)
    dosage = models.CharField(max_length=100, blank=True, default='')
    category = models.CharField(max_length=100, blank=True, default='')
    is_specialty = models.BooleanField(default=False)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return f"{self.name} {self.dosage}".strip()


class DemographicFactor(models.Model):
    AGE_UNDER_65 = 'under_65'
    AGE_65_70 = '65_70'
    AGE_70_75 = '70_75'
    AGE_75_80 = '75_80'
    AGE_80_PLUS = '80_plus'
    AGE_UNKNOWN = 'unknown'
    AGE_CHOICES = [
        (AGE_UNDER_65, 'Under 65'),
        (AGE_65_70, '65-70'),
        (AGE_70_75, '70-75'),
        (AGE_75_80, '75-80'),
        (AGE_80_PLUS, '80+'),
        (AGE_UNKNOWN, 'Unknown'),
    ]

    SEX_FEMALE = 'female'
    SEX_MALE = 'male'
    SEX_UNKNOWN = 'unknown'
    SEX_CHOICES = [
        (SEX_FEMALE, 'Female'),
        (SEX_MALE, 'Male'),
        (SEX_UNKNOWN, 'Unknown'),
    ]

    age_band = models.CharField(max_length=20, choices=AGE_CHOICES)
    sex = models.CharField(max_length=10, choices=SEX_CHOICES)
    base_score = models.IntegerField()

    class Meta:
        unique_together = ('age_band', 'sex')
        ordering = ['age_band', 'sex']

    def __str__(self):
        return f"{self.get_age_band_display()} / {self.get_sex_display()} → {self.base_score} pts"
