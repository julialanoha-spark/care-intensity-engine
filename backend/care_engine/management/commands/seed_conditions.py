from django.core.management.base import BaseCommand
from care_engine.models import ChronicCondition

# (name, tier, base_score, display_order)
# Ordered to group high → medium → low, matching plan's HCC-aligned weights
CONDITION_DATA = [
    # Cancer is special: base_score=10 (unspecified default); severity toggle adjusts at score time
    ('Cancer', 'high', 10, 1),
    ('Heart failure', 'high', 12, 2),
    ('End-stage renal disease', 'high', 12, 3),
    ('Dementia', 'high', 11, 4),
    ('HIV/AIDS', 'high', 10, 5),
    ('Hematologic disorders', 'medium', 9, 6),
    ('Stroke', 'medium', 8, 7),
    ('Neurologic disorders', 'medium', 7, 8),
    ('Cardiovascular disorders', 'medium', 7, 9),
    ('Chronic lung disorders', 'medium', 7, 10),
    ('Autoimmune disorders', 'low', 5, 11),
    ('Mental health conditions', 'low', 5, 12),
    ('Diabetes mellitus', 'low', 4, 13),
]


class Command(BaseCommand):
    help = 'Seed the 13 chronic conditions with HCC-aligned scores'

    def handle(self, *args, **options):
        created_count = 0
        for name, tier, base_score, display_order in CONDITION_DATA:
            _, created = ChronicCondition.objects.get_or_create(
                name=name,
                defaults={
                    'tier': tier,
                    'base_score': base_score,
                    'display_order': display_order,
                },
            )
            if created:
                created_count += 1

        self.stdout.write(
            self.style.SUCCESS(
                f'Seeded conditions: {created_count} created, '
                f'{len(CONDITION_DATA) - created_count} already existed.'
            )
        )
