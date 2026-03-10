from django.core.management.base import BaseCommand
from care_engine.models import DemographicFactor

# (age_band, sex, base_score)
# Derived from CMS-HCC V28 Community Non-Medicaid demographic factors
# Normalized from raw RAF range ~0.302–0.579 to 0–15 scale
# Source: CY 2024 AN_FINAL_20230131.pdf, Table II-6 (approx values)
DEMOGRAPHIC_DATA = [
    ('under_65', 'female', 4),
    ('under_65', 'male', 4),
    ('under_65', 'unknown', 0),
    ('65_70', 'female', 1),
    ('65_70', 'male', 1),
    ('65_70', 'unknown', 0),
    ('70_75', 'female', 2),
    ('70_75', 'male', 3),
    ('70_75', 'unknown', 0),
    ('75_80', 'female', 6),
    ('75_80', 'male', 7),
    ('75_80', 'unknown', 0),
    ('80_plus', 'female', 11),
    ('80_plus', 'male', 12),
    ('80_plus', 'unknown', 0),
    ('unknown', 'female', 0),
    ('unknown', 'male', 0),
    ('unknown', 'unknown', 0),
]


class Command(BaseCommand):
    help = 'Seed demographic base score factors from CMS-HCC V28'

    def handle(self, *args, **options):
        created_count = 0
        for age_band, sex, base_score in DEMOGRAPHIC_DATA:
            _, created = DemographicFactor.objects.get_or_create(
                age_band=age_band,
                sex=sex,
                defaults={'base_score': base_score},
            )
            if created:
                created_count += 1

        self.stdout.write(
            self.style.SUCCESS(
                f'Seeded demographics: {created_count} created, '
                f'{len(DEMOGRAPHIC_DATA) - created_count} already existed.'
            )
        )
